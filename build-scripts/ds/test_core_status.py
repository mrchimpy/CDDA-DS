"""Host checks for the optional core-status overlay, native mailbox and JNI decoder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apply_body_status as body
import apply_core_status as core

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "core-status"
FIXTURES = TEMPLATES / "host-fixtures"


def run(command: list[str], timeout: int = 45) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise AssertionError(f"{command[0]} failed:\n{result.stdout}\n{result.stderr}")
    return result


class CoreStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources = {
            "src/game.cpp": body.INCLUDE + body.PANEL + "    (void)force_draw;\n}\n",
            "src/main.cpp": body.INCLUDE + "void loop() {\n" + body.SESSION + "}\n",
            body.JAVA: "class CataclysmDDA {\n    private NativeUI nativeUI = null;\n"
                + body.RESUME + "    }\n" + body.FOCUS + "}\n}\n",
        }
        for path, content in self.sources.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        expected = {path: body.blob_sha(content.encode()) for path, content in self.sources.items()}
        self.guard = patch.dict(core.EXPECTED_BLOBS, expected, clear=True)
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def assert_originals(self) -> None:
        for path, content in self.sources.items():
            self.assertEqual((self.root / path).read_text(), content)

    def test_overlay_applies_all_seven_targets(self):
        result = core.apply(self.root, self.root / "dist")
        self.assertEqual(result["experiment"], "core_status")
        self.assertEqual(len(result["paths"]), 7)
        self.assertFalse(result["game_actions"])
        self.assertTrue(result["original_sidebar_retained"])
        for path, digest in result["paths"].items():
            self.assertEqual(hashlib.sha256((self.root / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(json.loads((self.root / "dist/CORE-STATUS.json").read_text()), result)
        self.assertIn("core.strength = u.get_str();", (self.root / "dist/CORE-STATUS.patch").read_text())

    def test_uses_current_sidebar_getters_not_base_values(self):
        text = core.patch_text("src/game.cpp", self.sources["src/game.cpp"])
        for getter in ("get_str", "get_dex", "get_int", "get_per", "get_speed", "get_focus"):
            self.assertIn(f"u.{getter}()", text)
            self.assertNotIn(f"u.{getter}_base()", text)
        self.assertIn('u.current_movement_mode()->name()', text)
        self.assertIn('u.current_movement_mode()->panel_letter()', text)
        self.assertIn('#include "move_mode.h"', text)
        self.assertEqual(text.count("ds_hud::publish("), 1)

    def test_session_and_activity_hooks_are_the_accepted_hooks(self):
        for path in ("src/main.cpp", body.JAVA):
            self.assertEqual(core.patch_text(path, self.sources[path]),
                             body.patch_text(path, self.sources[path]))

    def test_production_hash_guard_is_unchanged(self):
        self.assertEqual(body.EXPECTED_BLOBS["src/game.cpp"], "9c5ac1c44ab7079852eebdad1bb92b77c5c3d5c5")
        self.assertEqual(body.EXPECTED_BLOBS["src/main.cpp"], "a5f96b997377eaea9b8aee2aa07e98bf45e5988e")
        self.assertEqual(body.EXPECTED_BLOBS[body.JAVA], "ce06c3d4438175eabfca4043742169c25e680220")

    def test_bad_hash_fails_before_other_writes(self):
        path = self.root / "src/main.cpp"
        path.write_text("unexpected")
        with self.assertRaises(ValueError): core.apply(self.root, self.root / "dist")
        self.assertEqual((self.root / "src/game.cpp").read_text(), self.sources["src/game.cpp"])
        self.assertFalse((self.root / "src/ds_hud.h").exists())

    def test_existing_destination_fails_before_writes(self):
        path = self.root / core.TEMPLATES["CoreHudSnapshot.java"]
        path.write_text("existing")
        with self.assertRaises(ValueError): core.apply(self.root, self.root / "dist")
        self.assert_originals()
        self.assertEqual(path.read_text(), "existing")

    def test_source_symlink_is_rejected(self):
        path = self.root / "src/game.cpp"
        actual = self.root / "original-game.cpp"
        path.rename(actual)
        path.symlink_to(actual)
        with self.assertRaises(ValueError): core.apply(self.root, self.root / "dist")
        self.assertEqual(actual.read_text(), self.sources["src/game.cpp"])

    def test_destination_symlink_is_rejected(self):
        path = self.root / "src/ds_hud.cpp"
        path.symlink_to(self.root / "missing")
        with self.assertRaises(ValueError): core.apply(self.root, self.root / "dist")
        self.assert_originals()

    def test_parent_escape_is_rejected(self):
        (self.root / "outside").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): core.safe_target(self.root, "outside/test.cpp")

    def test_duplicate_anchor_fails(self):
        with self.assertRaises(ValueError):
            core.patch_text("src/game.cpp", self.sources["src/game.cpp"] + body.PANEL)

    def test_repeat_overlay_refused(self):
        core.apply(self.root, self.root / "dist")
        with self.assertRaises(ValueError): core.apply(self.root, self.root / "dist")

    def test_scope_no_input_or_viewport_changes(self):
        java = (TEMPLATES / "DualScreenHud.java").read_text()
        self.assertIn("FLAG_NOT_FOCUSABLE", java)
        self.assertIn("FOCUS_BLOCK_DESCENDANTS", java)
        self.assertIn("core.setVisibility(View.GONE)", java)
        self.assertIn('movement.setText("")', java)
        for forbidden in ("dispatchKeyEvent", "performClick", "nativeKeyDown", "TERRAIN_WINDOW_WIDTH", "get_width_right"):
            self.assertNotIn(forbidden, java + core.patch_text("src/game.cpp", self.sources["src/game.cpp"]))

    def test_native_mailbox_coherence_lifecycle_and_copy(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler, "C++17 compiler required")
        output = self.root / "mailbox"
        run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
             "-I", str(TEMPLATES), str(TEMPLATES / "ds_hud.cpp"),
             str(TEMPLATES / "test_mailbox.cpp"), "-o", str(output)])
        run([str(output)])

    def test_capture_hook_compiles_and_reads_current_values(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        include = self.root / "include"
        include.mkdir()
        (include / "game.h").write_text(r'''#pragma once
#include <string>
struct bodypart_id { explicit bodypart_id(const char *) {} };
struct movement {
    std::string name() const { return "crouch"; }
    char panel_letter() const { return 'C'; }
};
struct avatar {
    movement mode;
    int get_part_hp_cur(const bodypart_id &) const { return 30; }
    int get_part_hp_max(const bodypart_id &) const { return 80; }
    int get_stamina() const { return 25; }
    int get_stamina_max() const { return 100; }
    int get_str() const { return 6; }
    int get_dex() const { return 3; }
    int get_int() const { return 11; }
    int get_per() const { return 4; }
    int get_speed() const { return 82; }
    int get_focus() const { return 137; }
    const movement *current_movement_mode() const { return &mode; }
};
struct game { avatar u; void draw_panels(bool force_draw); };
''')
        (include / "move_mode.h").write_text('#pragma once\n#include "game.h"\n')
        capture = self.root / "capture.cpp"
        capture.write_text(core.patch_text("src/game.cpp", self.sources["src/game.cpp"]))
        caller = self.root / "caller.cpp"
        caller.write_text(r'''#include "game.h"
#include "ds_hud.h"
#include <cassert>
int main() {
    ds_hud::session_scope scope;
    game g;
    g.draw_panels(true);
    const auto s = ds_hud::read();
    assert(s.ready && s.current == 25 && s.health.current[0] == 30);
    assert(s.core.strength == 6 && s.core.dexterity == 3);
    assert(s.core.intelligence == 11 && s.core.perception == 4);
    assert(s.core.speed == 82 && s.core.focus == 137);
    assert(s.core.movement_mode == "crouch (C)");
}
''')
        obj = self.root / "capture.o"
        run([compiler, "-std=c++17", "-D__ANDROID__", "-Wall", "-Wextra", "-Werror",
             "-I", str(include), "-I", str(TEMPLATES), "-c", str(capture), "-o", str(obj)])
        exe = self.root / "capture-test"
        run([compiler, "-std=c++17", "-pthread", "-I", str(include), "-I", str(TEMPLATES),
             str(caller), str(TEMPLATES / "ds_hud.cpp"), str(obj), "-o", str(exe)])
        run([str(exe)])

    def test_real_jni_transport_and_java_decoder(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        javac = shutil.which("javac")
        java = shutil.which("java")
        self.assertIsNotNone(compiler, "C++17 compiler required")
        self.assertIsNotNone(javac, "Java JDK required; CI sets up Java 17 first")
        self.assertIsNotNone(java)
        home = Path(javac).resolve().parent.parent
        includes = home / "include"
        self.assertTrue((includes / "jni.h").exists(), "JDK JNI headers required")
        library = self.root / "libcore_hud_host.so"
        run([compiler, "-std=c++17", "-shared", "-fPIC", "-pthread", "-D__ANDROID__",
             "-Wall", "-Wextra", "-Werror", "-I", str(includes), "-I", str(includes / "linux"),
             "-I", str(TEMPLATES), str(TEMPLATES / "ds_hud.cpp"),
             str(FIXTURES / "test_jni.cpp"), "-o", str(library)])
        classes = self.root / "classes"
        classes.mkdir()
        run([javac, "--release", "8", "-Xlint:all,-options", "-Werror", "-d", str(classes),
             str(TEMPLATES / "CoreHudSnapshot.java"), str(FIXTURES / "DualScreenHud.java"),
             str(FIXTURES / "CoreHudSnapshotTest.java")])
        result = run([java, "-Xcheck:jni", "-cp", str(classes),
                      "com.cleverraven.cataclysmdda.CoreHudSnapshotTest", str(library)])
        self.assertIn("real JNI round-trip passed", result.stdout)
        self.assertNotIn("WARNING", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
