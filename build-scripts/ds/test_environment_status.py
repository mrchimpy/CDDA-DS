"""Checks for derived environment HUD templates; host fixtures are not the game engine."""
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
import apply_environment_status as env

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "environment-status/host-fixtures"
WIDGET_FILES = {
    "date": "013fcc2b8eef492e6ed3969351d6b6b71db29c9e",
    "time": "f00ef8b84eabd779f0643191c23c67e891e60941",
    "place": "fe8517e073f1db44f686543b23ab335adf7bece7",
    "weather": "0eb052a8de70bd936e53c22d05bab203ba95d803",
    "lighting": "7f28860f218fca72ade7964b0d6c15737389951a",
    "wind": "b4643f47f13ec253e5a93931931ddd37ea9c48db",
    "env_temp": "503d9ebb54fff9b75cd1f7d49ef49e1787f8cbd9",
}


def run(command: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise AssertionError(f"{command[0]} failed:\n{result.stdout}\n{result.stderr}")
    return result


class EnvironmentStatusTests(unittest.TestCase):
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
        self.guard = patch.dict(env.EXPECTED_BLOBS, {
            p: body.blob_sha(t.encode()) for p, t in self.sources.items()
        }, clear=True)
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def assert_originals(self):
        for p, t in self.sources.items():
            self.assertEqual((self.root / p).read_text(), t)
        self.assertFalse((self.root / "src/ds_hud.h").exists())

    def generated(self):
        directory = self.root / "generated"
        directory.mkdir(exist_ok=True)
        for path, text in env.render_templates().items():
            (directory / Path(path).name).write_text(text)
        return directory

    def test_widget_definitions_and_order(self):
        ids = []
        for name, expected in WIDGET_FILES.items():
            raw = (HERE.parent.parent / f"data/json/ui/{name}.json").read_bytes()
            self.assertEqual(body.blob_sha(raw), expected)
            ids.append(json.loads(raw)[0]["id"])
        self.assertEqual(tuple(ids), env.WIDGET_IDS[5:])
        self.assertEqual(env.WIDGET_IDS[:5], activity.WIDGET_IDS)
        self.assertEqual(len(set(env.WIDGET_IDS)), 12)

    def test_templates_and_core_decoder_reused(self):
        rendered = env.render_templates()
        self.assertEqual(rendered[activity.JAVA_DIR + "CoreHudSnapshot.java"],
                         (HERE / "core-status/CoreHudSnapshot.java").read_text())
        expected_cpp = (HERE / "activity-status/ds_hud.cpp").read_text().replace(
            "Object[] { long[29], byte[6][] }", "Object[] { long[36], byte[13][] }")
        self.assertEqual(rendered["src/ds_hud.cpp"], expected_cpp)
        self.assertIn("activity_field_count = 12;", rendered["src/ds_hud.h"])
        self.assertIn("STATUS_COUNT = 12;", rendered[activity.JAVA_DIR + "ActivityHudSnapshot.java"])

    def test_old_sources_not_mutated(self):
        before = {p: (HERE / p).read_bytes() for p in env.TEMPLATE_BLOBS}
        ids_before = activity.WIDGET_IDS
        env.apply(self.root, self.root / "dist")
        self.assertEqual(activity.WIDGET_IDS, ids_before)
        for p, data in before.items():
            self.assertEqual((HERE / p).read_bytes(), data)

    def test_overlay_all_eight_targets_and_provenance(self):
        report = env.apply(self.root, self.root / "dist")
        self.assertEqual(report["experiment"], "environment_status")
        self.assertEqual(len(report["paths"]), 8)
        self.assertFalse(report["game_actions"])
        self.assertTrue(report["original_sidebar_retained"])
        for p, digest in report["paths"].items():
            self.assertEqual(hashlib.sha256((self.root / p).read_bytes()).hexdigest(), digest)
        self.assertEqual(json.loads((self.root / "dist/ENVIRONMENT-STATUS.json").read_text()), report)
        self.assertIn('"time_desc_label"', (self.root / "dist/ENVIRONMENT-STATUS.patch").read_text())

    def test_session_and_activity_hooks_unchanged(self):
        for p in ("src/main.cpp", body.JAVA):
            self.assertEqual(env.patch_text(p, self.sources[p]), activity.patch_text(p, self.sources[p]))
        java = env.render_templates()[activity.JAVA_DIR + "DualScreenHud.java"]
        original = (HERE / "activity-status/DualScreenHud.java").read_text()
        boundary = "    private static final class HudPresentation"
        self.assertEqual(java.split(boundary)[0], original.split(boundary)[0])
        self.assertIn("handler.postDelayed(this, 250)", java)
        self.assertIn("FLAG_NOT_FOCUSABLE", java)
        self.assertIn("FOCUS_BLOCK_DESCENDANTS", java)

    def test_read_only_capture_and_no_hidden_time_temperature(self):
        text = env.patch_text("src/game.cpp", self.sources["src/game.cpp"])
        for wid in env.WIDGET_IDS:
            self.assertEqual(text.count('"' + wid + '"'), 1)
        self.assertIn("widget view = id.obj();", text)
        self.assertIn("remove_color_tags( view.show( u, 80 ) )", text)
        self.assertIn("if( ds_hud::read().active )", text)
        for forbidden in ("calendar::turn", "get_temperature(", "get_weather(",
                          "dispatchKeyEvent", "invalidate_main_ui", "u.moves"):
            self.assertNotIn(forbidden, text)
        self.assertEqual(text.count("ds_hud::publish("), 1)

    def test_layout_retains_prior_rows_and_clears_new_values(self):
        java = env.render_templates()[activity.JAVA_DIR + "DualScreenHud.java"]
        self.assertIn("for (int i = 0; i < 5; i += 2)", java)
        self.assertIn("column < 2 && i + column < 5", java)
        self.assertIn("for (int i = 5; i < activityValues.length; i++)", java)
        self.assertIn('activityValues[i] = text("", 16)', java)
        self.assertIn('for (TextView field : activityValues) field.setText("")', java)
        for forbidden in ("TabLayout", "setMaxLines", "setEllipsize", "setTextSize(12)"):
            self.assertNotIn(forbidden, java)

    def test_pinned_source_guards_unchanged(self):
        self.assertEqual(body.EXPECTED_BLOBS, activity.EXPECTED_BLOBS)
        self.assertEqual(body.EXPECTED_BLOBS["src/game.cpp"], "9c5ac1c44ab7079852eebdad1bb92b77c5c3d5c5")

    def test_bad_hash_fails_before_writes(self):
        (self.root / "src/main.cpp").write_text("changed")
        with self.assertRaises(ValueError): env.apply(self.root, self.root / "dist")
        self.assertEqual((self.root / "src/game.cpp").read_text(), self.sources["src/game.cpp"])
        self.assertFalse((self.root / "src/ds_hud.h").exists())

    def test_existing_destination_fails_before_writes(self):
        (self.root / "src/ds_hud.cpp").write_text("existing")
        with self.assertRaises(ValueError): env.apply(self.root, self.root / "dist")
        self.assert_originals()

    def test_destination_symlink_is_rejected(self):
        (self.root / "src/ds_hud.cpp").symlink_to(self.root / "missing")
        with self.assertRaises(ValueError): env.apply(self.root, self.root / "dist")
        self.assert_originals()

    def test_source_symlink_is_rejected(self):
        p = self.root / "src/game.cpp"
        p.rename(self.root / "original")
        p.symlink_to(self.root / "original")
        with self.assertRaises(ValueError): env.apply(self.root, self.root / "dist")
        self.assert_originals()

    def test_parent_escape_is_rejected(self):
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): core.safe_target(self.root, "escape/file")

    def test_template_mutation_fails_before_writes(self):
        templates = self.root / "templates"
        for p in env.TEMPLATE_BLOBS:
            dst = templates / p
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((HERE / p).read_bytes())
        (templates / "activity-status/ds_hud.h").write_text("changed")
        with self.assertRaises(ValueError): env.apply(self.root, self.root / "dist", templates)
        self.assert_originals()

    def test_missing_template_fails_before_writes(self):
        templates = self.root / "empty"
        templates.mkdir()
        with self.assertRaises(FileNotFoundError): env.apply(self.root, self.root / "dist", templates)
        self.assert_originals()

    def test_duplicate_anchor_is_rejected(self):
        with self.assertRaises(ValueError):
            env.patch_text("src/game.cpp", self.sources["src/game.cpp"] + body.PANEL)

    def test_repeat_application_is_rejected(self):
        env.apply(self.root, self.root / "dist")
        with self.assertRaises(ValueError): env.apply(self.root, self.root / "dist")

    def test_native_coherence_copy_and_session_clearing(self):
        d = self.generated()
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        exe = self.root / "native"
        run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread", "-I", str(d),
             str(d / "ds_hud.cpp"), str(FIXTURES / "test_native.cpp"), "-o", str(exe)])
        run([str(exe)])

    def test_real_jni_roundtrip_and_decoder(self):
        d = self.generated()
        compiler = shutil.which("g++") or shutil.which("clang++")
        javac, java = shutil.which("javac"), shutil.which("java")
        self.assertIsNotNone(compiler)
        self.assertIsNotNone(javac)
        self.assertIsNotNone(java)
        inc = Path(javac).resolve().parent.parent / "include"
        lib = self.root / "libenvironment.so"
        run([compiler, "-std=c++17", "-shared", "-fPIC", "-pthread", "-D__ANDROID__",
             "-Wall", "-Wextra", "-Werror", "-I", str(inc), "-I", str(inc / "linux"), "-I", str(d),
             str(d / "ds_hud.cpp"), str(FIXTURES / "test_native.cpp"), "-o", str(lib)])
        classes = self.root / "classes"
        classes.mkdir()
        run([javac, "--release", "8", "-Xlint:all,-options", "-Werror", "-d", str(classes),
             str(d / "CoreHudSnapshot.java"), str(d / "ActivityHudSnapshot.java"),
             str(FIXTURES / "DualScreenHud.java"), str(FIXTURES / "EnvironmentHudSnapshotTest.java")])
        result = run([java, "-Xcheck:jni", "-cp", str(classes),
                      "com.cleverraven.cataclysmdda.EnvironmentHudSnapshotTest", str(lib)])
        self.assertIn("environment real JNI round-trip passed", result.stdout)
        self.assertNotIn("WARNING", result.stdout + result.stderr)


    def test_compiled_capture_fixture_all_fields_and_inactive_guard(self):
        d = self.generated()
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        (d / "game.h").write_text(r"""#pragma once
#include <string>
struct bodypart_id { explicit bodypart_id(const char *) {} };
struct mode { std::string name() const { return "walk"; } char panel_letter() const { return 'W'; } };
struct avatar {
    mode movement;
    int get_part_hp_cur(const bodypart_id &) const { return 20; }
    int get_part_hp_max(const bodypart_id &) const { return 80; }
    int get_stamina() const { return 25; }
    int get_stamina_max() const { return 100; }
    int get_str() const { return 5; } int get_dex() const { return 3; }
    int get_int() const { return 4; } int get_per() const { return 2; }
    int get_speed() const { return 75; } int get_focus() const { return 137; }
    const mode *current_movement_mode() const { return &movement; }
};
struct game { avatar u; void draw_panels(bool force_draw); };
""")
        (d / "move_mode.h").write_text('#include "game.h"\n')
        (d / "widget.h").write_text(r"""#pragma once
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
""")
        (d / "capture.cpp").write_text(env.patch_text("src/game.cpp", self.sources["src/game.cpp"]))
        ids = ', '.join(json.dumps(i) for i in env.WIDGET_IDS)
        (d / "caller.cpp").write_text(r"""#include "widget.h"
#include "ds_hud.h"
int main() {
    const char *ids[] = { IDS };
    for (const char *id : ids) definitions[id].value = id;
    game g;
    g.draw_panels(true);
    assert(!ds_hud::read().ready && total_calls == 0);
    ds_hud::session_scope session;
    g.draw_panels(true);
    auto s = ds_hud::read();
    assert(s.ready && s.current == 25 && s.core.focus == 137 && total_calls == 12);
    for (int i = 0; i < 12; i++) {
        assert(s.activity.available[i] && s.activity.text[i] == ids[i]);
        assert(definitions.at(ids[i]).calls == 0);
    }
    definitions.erase("weather_desc");
    definitions.at("time_desc_label").value = "???";
    definitions.at("env_temp_desc").value = "-";
    g.draw_panels(true);
    s = ds_hud::read();
    assert(!s.activity.available[8] && s.activity.text[8].empty());
    assert(s.activity.text[6] == "???" && s.activity.text[11] == "-");
}
""".replace("IDS", ids))
        obj, exe = self.root / "capture.o", self.root / "capture-test"
        run([compiler, "-std=c++17", "-D__ANDROID__", "-Wall", "-Wextra", "-Werror",
             "-I", str(d), "-c", str(d / "capture.cpp"), "-o", str(obj)])
        run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread", "-I", str(d),
             str(d / "caller.cpp"), str(d / "ds_hud.cpp"), str(obj), "-o", str(exe)])
        run([str(exe)])


if __name__ == "__main__":
    unittest.main()
