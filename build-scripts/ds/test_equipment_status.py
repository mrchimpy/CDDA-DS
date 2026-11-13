"""Equipment overlay guards and host transport tests; not Android/engine acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apply_activity_status as activity
import apply_body_status as body
import apply_core_status as core
import apply_environment_status as environment
import apply_equipment_status as equipment

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "equipment-status/host-fixtures"
WIDGET_FILES = {
    "wield": ("2c45a1069c521d092f5a0c29ed0aea2d78bd416c", "wielding_desc", "wielding_text"),
    "ma_style": ("88da6ee149bbf0c137e739a952d99e93b5821c22", "style_desc", "style_text"),
    "power": ("ec009ad36ee11b5b646fb4ca220b88df5ab770f9", "power_desc", "power_text"),
    "sound": ("8bb06f1d93bf33dac8b4ecb4ca968004f0ef5130", "sound_num", "sound"),
    "morale": ("99ba0e965a8f2501fe142f51bb5249a9d6892f49", "mood_desc_label", "mood_text"),
}


def run(command: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise AssertionError(f"{command[0]} failed:\n{result.stdout}\n{result.stderr}")
    return result


class EquipmentStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources = {
            "src/game.cpp": body.INCLUDE + body.PANEL + "    (void)force_draw;\n}\n",
            "src/main.cpp": body.INCLUDE + "void loop() {\n" + body.SESSION + "}\n",
            body.JAVA: "class CataclysmDDA {\n    private NativeUI nativeUI = null;\n"
                + body.RESUME + "    }\n" + body.FOCUS + "}\n}\n",
        }
        for path, text in self.sources.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        self.guard = patch.dict(equipment.EXPECTED_BLOBS, {
            p: body.blob_sha(t.encode()) for p, t in self.sources.items()
        }, clear=True)
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def assert_originals(self):
        for path, text in self.sources.items():
            self.assertEqual((self.root / path).read_text(), text)
        self.assertFalse((self.root / "src/ds_hud.h").exists())

    def generated(self):
        directory = self.root / "generated"
        directory.mkdir(exist_ok=True)
        for path, text in equipment.render_templates().items():
            (directory / Path(path).name).write_text(text)
        return directory

    def test_pinned_widgets_and_append_order(self):
        ids = []
        for name, (digest, wid, variable) in WIDGET_FILES.items():
            raw = (HERE.parent.parent / f"data/json/ui/{name}.json").read_bytes()
            self.assertEqual(body.blob_sha(raw), digest)
            definition = next(w for w in json.loads(raw) if w["id"] == wid)
            self.assertEqual(definition["var"], variable)
            ids.append(wid)
        self.assertEqual(equipment.WIDGET_IDS[:12], environment.WIDGET_IDS)
        self.assertEqual(equipment.WIDGET_IDS[12:], tuple(ids))
        self.assertEqual(len(set(equipment.WIDGET_IDS)), 17)

    def test_existing_templates_scripts_and_parent_rendering_unchanged(self):
        paths = list(environment.TEMPLATE_BLOBS) + [
            "apply_body_status.py", "apply_core_status.py", "apply_activity_status.py",
            "apply_environment_status.py"]
        before = {p: (HERE / p).read_bytes() for p in paths}
        rendered_before = environment.render_templates()
        equipment.apply(self.root, self.root / "dist")
        self.assertEqual(environment.render_templates(), rendered_before)
        for p, data in before.items():
            self.assertEqual((HERE / p).read_bytes(), data)

    def test_core_decoder_and_native_logic_reused(self):
        old, new = environment.render_templates(), equipment.render_templates()
        path = activity.JAVA_DIR + "CoreHudSnapshot.java"
        self.assertEqual(new[path], old[path])
        self.assertEqual(new["src/ds_hud.cpp"], old["src/ds_hud.cpp"].replace(
            "Object[] { long[36], byte[13][] }", "Object[] { long[41], byte[18][] }"))
        self.assertIn("activity_field_count = 17;", new["src/ds_hud.h"])
        self.assertIn("STATUS_COUNT = 17;", new[activity.JAVA_DIR + "ActivityHudSnapshot.java"])

    def test_overlay_eight_targets_and_provenance(self):
        report = equipment.apply(self.root, self.root / "dist")
        self.assertEqual(report["experiment"], "equipment_status")
        self.assertEqual(len(report["paths"]), 8)
        self.assertFalse(report["game_actions"])
        self.assertTrue(report["original_sidebar_retained"])
        self.assertEqual(report["widget_ids"], list(equipment.WIDGET_IDS))
        for p, digest in report["paths"].items():
            self.assertEqual(hashlib.sha256((self.root / p).read_bytes()).hexdigest(), digest)
        self.assertEqual(json.loads((self.root / "dist/EQUIPMENT-STATUS.json").read_text()), report)
        self.assertIn('"wielding_desc"', (self.root / "dist/EQUIPMENT-STATUS.patch").read_text())

    def test_capture_only_changes_widget_declaration(self):
        original = environment.patch_text("src/game.cpp", self.sources["src/game.cpp"])
        new = equipment.patch_text("src/game.cpp", self.sources["src/game.cpp"])
        self.assertEqual(new, original.replace(equipment.declaration(environment.WIDGET_IDS),
                                              equipment.declaration(equipment.WIDGET_IDS), 1))
        self.assertIn("widget view = id.obj();", new)
        self.assertIn("remove_color_tags( view.show( u, 80 ) )", new)
        self.assertIn("if( ds_hud::read().active )", new)
        self.assertEqual(new.count("ds_hud::publish("), 1)
        for wid in equipment.WIDGET_IDS:
            self.assertEqual(new.count('"' + wid + '"'), 1)

    def test_lifecycle_and_input_hooks_unchanged(self):
        for path in ("src/main.cpp", body.JAVA):
            self.assertEqual(equipment.patch_text(path, self.sources[path]),
                             environment.patch_text(path, self.sources[path]))
        ui_path = activity.JAVA_DIR + "DualScreenHud.java"
        old, new = environment.render_templates()[ui_path], equipment.render_templates()[ui_path]
        self.assertEqual(new, old.replace('"CDDA-DS / ENVIRONMENT STATUS"',
                                         '"CDDA-DS / EQUIPMENT STATUS"'))
        for marker in ("FLAG_NOT_FOCUSABLE", "FOCUS_BLOCK_DESCENDANTS", "handler.postDelayed(this, 250)"):
            self.assertIn(marker, new)

    def test_layout_wrapping_and_clear_loop_are_retained(self):
        java = equipment.render_templates()[activity.JAVA_DIR + "DualScreenHud.java"]
        self.assertIn("for (int i = 5; i < activityValues.length; i++)", java)
        self.assertIn('activityValues[i] = text("", 16)', java)
        self.assertIn('for (TextView field : activityValues) field.setText("")', java)
        for forbidden in ("setMaxLines", "setEllipsize", "TabLayout", "dispatchKeyEvent"):
            self.assertNotIn(forbidden, java)

    def test_original_source_hash_guards_unchanged(self):
        self.assertEqual(environment.EXPECTED_BLOBS, body.EXPECTED_BLOBS)
        self.assertEqual(body.EXPECTED_BLOBS["src/game.cpp"], "9c5ac1c44ab7079852eebdad1bb92b77c5c3d5c5")

    def test_bad_hash_stops_before_writes(self):
        (self.root / "src/main.cpp").write_text("changed")
        with self.assertRaises(ValueError): equipment.apply(self.root, self.root / "dist")
        self.assertEqual((self.root / "src/game.cpp").read_text(), self.sources["src/game.cpp"])
        self.assertFalse((self.root / "src/ds_hud.h").exists())

    def test_existing_destination_stops_before_writes(self):
        (self.root / "src/ds_hud.cpp").write_text("existing")
        with self.assertRaises(ValueError): equipment.apply(self.root, self.root / "dist")
        self.assert_originals()

    def test_source_symlink_rejected(self):
        p = self.root / "src/game.cpp"
        p.rename(self.root / "original")
        p.symlink_to(self.root / "original")
        with self.assertRaises(ValueError): equipment.apply(self.root, self.root / "dist")
        self.assert_originals()

    def test_destination_symlink_rejected(self):
        (self.root / "src/ds_hud.cpp").symlink_to(self.root / "missing")
        with self.assertRaises(ValueError): equipment.apply(self.root, self.root / "dist")
        self.assert_originals()

    def test_parent_path_escape_rejected(self):
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): core.safe_target(self.root, "escape/file")

    def test_changed_template_stops_before_writes(self):
        templates = self.root / "templates"
        for path in environment.TEMPLATE_BLOBS:
            dst = templates / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((HERE / path).read_bytes())
        (templates / "activity-status/ds_hud.h").write_text("changed")
        with self.assertRaises(ValueError): equipment.apply(self.root, self.root / "dist", templates)
        self.assert_originals()

    def test_missing_template_stops_before_writes(self):
        templates = self.root / "empty"
        templates.mkdir()
        with self.assertRaises(FileNotFoundError): equipment.apply(self.root, self.root / "dist", templates)
        self.assert_originals()

    def test_duplicate_anchor_rejected(self):
        with self.assertRaises(ValueError):
            equipment.patch_text("src/game.cpp", self.sources["src/game.cpp"] + body.PANEL)

    def test_repeat_application_rejected(self):
        equipment.apply(self.root, self.root / "dist")
        with self.assertRaises(ValueError): equipment.apply(self.root, self.root / "dist")

    def test_native_coherence_copy_and_session_clearing(self):
        d = self.generated()
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        exe = self.root / "native"
        run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread", "-I", str(d),
             str(d / "ds_hud.cpp"), str(FIXTURES / "test_native.cpp"), "-o", str(exe)])
        run([str(exe)])

    def test_real_jni_and_decoder(self):
        d = self.generated()
        compiler = shutil.which("g++") or shutil.which("clang++")
        javac, java = shutil.which("javac"), shutil.which("java")
        self.assertIsNotNone(compiler)
        self.assertIsNotNone(javac)
        self.assertIsNotNone(java)
        inc = Path(javac).resolve().parent.parent / "include"
        lib = self.root / "libequipment.so"
        run([compiler, "-std=c++17", "-shared", "-fPIC", "-pthread", "-D__ANDROID__",
             "-Wall", "-Wextra", "-Werror", "-I", str(inc), "-I", str(inc / "linux"), "-I", str(d),
             str(d / "ds_hud.cpp"), str(FIXTURES / "test_native.cpp"), "-o", str(lib)])
        stub = d / "DualScreenHud.java"
        stub.write_text("package com.cleverraven.cataclysmdda;\n"
                        "final class DualScreenHud { static native Object[] nativeSnapshot(); }\n")
        classes = self.root / "classes"
        classes.mkdir()
        run([javac, "--release", "8", "-Xlint:all,-options", "-Werror", "-d", str(classes),
             str(d / "CoreHudSnapshot.java"), str(d / "ActivityHudSnapshot.java"), str(stub),
             str(FIXTURES / "EquipmentHudSnapshotTest.java")])
        result = run([java, "-Xcheck:jni", "-cp", str(classes),
                      "com.cleverraven.cataclysmdda.EquipmentHudSnapshotTest", str(lib)])
        self.assertIn("equipment real JNI round-trip passed", result.stdout)
        self.assertNotIn("WARNING", result.stdout + result.stderr)

    def test_compiled_capture_fixture_and_no_stale_equipment(self):
        d = self.generated()
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        (d / "game.h").write_text(r'''#pragma once
#include <string>
struct bodypart_id { explicit bodypart_id(const char *) {} };
struct mode { std::string name() const { return "walk"; } char panel_letter() const { return 'W'; } };
struct avatar {
    mode movement;
    int get_part_hp_cur(const bodypart_id &) const { return 20; }
    int get_part_hp_max(const bodypart_id &) const { return 80; }
    int get_stamina() const { return 25; } int get_stamina_max() const { return 100; }
    int get_str() const { return 5; } int get_dex() const { return 3; }
    int get_int() const { return 4; } int get_per() const { return 2; }
    int get_speed() const { return 75; } int get_focus() const { return 137; }
    const mode *current_movement_mode() const { return &movement; }
};
struct game { avatar u; void draw_panels(bool force_draw); };
''')
        (d / "move_mode.h").write_text('#include "game.h"\n')
        (d / "widget.h").write_text(r'''#pragma once
#include "game.h"
#include <cassert>
#include <map>
inline int total_calls = 0;
struct widget {
    std::string value;
    int calls = 0;
    std::string show(const avatar &, int width) {
        assert(width == 80); ++calls; ++total_calls; return value;
    }
};
inline std::map<std::string, widget> definitions;
struct widget_id {
    std::string id;
    explicit widget_id(const char *p): id(p) {}
    bool is_valid() const { return definitions.count(id) != 0; }
    const widget &obj() const { return definitions.at(id); }
};
inline std::string remove_color_tags(const std::string &s) { return s; }
''')
        (d / "capture.cpp").write_text(equipment.patch_text("src/game.cpp", self.sources["src/game.cpp"]))
        ids = ', '.join(json.dumps(wid) for wid in equipment.WIDGET_IDS)
        (d / "caller.cpp").write_text(r'''#include "widget.h"
#include "ds_hud.h"
int main() {
    const char *ids[] = { IDS };
    for (const char *id : ids) definitions[id].value = id;
    game g;
    g.draw_panels(true);
    assert(!ds_hud::read().ready && total_calls == 0);
    {
        ds_hud::session_scope session;
        g.draw_panels(true);
        auto s = ds_hud::read();
        assert(s.ready && s.current == 25 && s.core.focus == 137 && total_calls == 17);
        for (int i = 0; i < 17; i++) {
            assert(s.activity.available[i] && s.activity.text[i] == ids[i]);
            assert(definitions.at(ids[i]).calls == 0);
        }
        definitions.at("wielding_desc").value = "long spear";
        definitions.at("style_desc").value = "No style";
        definitions.at("power_desc").value = "--";
        definitions.at("sound_num").value = "0";
        definitions.at("mood_desc_label").value = ":|";
        g.draw_panels(true);
        assert(ds_hud::read().activity.text[12] == "long spear");
        definitions.at("wielding_desc").value = "fists";
        definitions.at("style_desc").value.clear();
        definitions.erase("power_desc");
        g.draw_panels(true);
        s = ds_hud::read();
        assert(s.activity.text[12] == "fists");
        assert(s.activity.available[13] && s.activity.text[13].empty());
        assert(!s.activity.available[14] && s.activity.text[14].empty());
        assert(s.activity.text[15] == "0" && s.activity.text[16] == ":|");
        assert(s.activity.text[6] == "time_desc_label");
    }
    assert(!ds_hud::read().ready && ds_hud::read().activity.text[12].empty());
}
'''.replace("IDS", ids))
        obj = self.root / "capture.o"
        run([compiler, "-std=c++17", "-D__ANDROID__", "-Wall", "-Wextra", "-Werror", "-I", str(d),
             "-c", str(d / "capture.cpp"), "-o", str(obj)])
        exe = self.root / "capture-test"
        run([compiler, "-std=c++17", "-pthread", "-I", str(d), str(d / "caller.cpp"),
             str(d / "ds_hud.cpp"), str(obj), "-o", str(exe)])
        run([str(exe)])


if __name__ == "__main__":
    unittest.main()
