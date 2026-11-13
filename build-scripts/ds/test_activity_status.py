"""Host/fixture checks for the optional activity-status HUD (not Android acceptance)."""
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
import apply_activity_status as activity

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "activity-status"
FIXTURES = TEMPLATES / "host-fixtures"


def run(command: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise AssertionError(f"{command[0]} failed:\n{result.stdout}\n{result.stderr}")
    return result


class ActivityStatusTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
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
        expected = {p: body.blob_sha(s.encode()) for p, s in self.sources.items()}
        guard = patch.dict(activity.EXPECTED_BLOBS, expected, clear=True)
        guard.start()
        self.addCleanup(guard.stop)

    def originals_unchanged(self):
        for p, s in self.sources.items():
            self.assertEqual((self.root / p).read_text(), s)

    def test_overlay_records_all_eight_targets(self):
        result = activity.apply(self.root, self.root / "dist")
        self.assertEqual(result["experiment"], "activity_status")
        self.assertEqual(len(result["paths"]), 8)
        self.assertEqual(result["widget_ids"], list(activity.WIDGET_IDS))
        self.assertFalse(result["game_actions"])
        self.assertTrue(result["original_sidebar_retained"])
        for p, digest in result["paths"].items():
            self.assertEqual(hashlib.sha256((self.root / p).read_bytes()).hexdigest(), digest)
        self.assertEqual(json.loads((self.root / "dist/ACTIVITY-STATUS.json").read_text()), result)
        self.assertIn("view.show( u, 80 )", (self.root / "dist/ACTIVITY-STATUS.patch").read_text())

    def test_pinned_production_source_guard(self):
        self.assertEqual(core.EXPECTED_BLOBS, body.EXPECTED_BLOBS)
        self.assertEqual(body.EXPECTED_BLOBS["src/game.cpp"], "9c5ac1c44ab7079852eebdad1bb92b77c5c3d5c5")
        self.assertEqual(body.EXPECTED_BLOBS["src/main.cpp"], "a5f96b997377eaea9b8aee2aa07e98bf45e5988e")
        self.assertEqual(body.EXPECTED_BLOBS[body.JAVA], "ce06c3d4438175eabfca4043742169c25e680220")

    def test_bad_hash_fails_before_any_source_write(self):
        (self.root / "src/main.cpp").write_text("unexpected")
        with self.assertRaises(ValueError): activity.apply(self.root, self.root / "dist")
        self.assertEqual((self.root / "src/game.cpp").read_text(), self.sources["src/game.cpp"])
        self.assertFalse((self.root / "src/ds_hud.h").exists())

    def test_existing_destination_fails_before_writes(self):
        dest = self.root / activity.TEMPLATES["activity-status/ActivityHudSnapshot.java"]
        dest.write_text("existing")
        with self.assertRaises(ValueError): activity.apply(self.root, self.root / "dist")
        self.originals_unchanged()
        self.assertEqual(dest.read_text(), "existing")

    def test_source_symlink_is_rejected(self):
        src = self.root / "src/game.cpp"
        saved = self.root / "original.cpp"
        src.rename(saved)
        src.symlink_to(saved)
        with self.assertRaises(ValueError): activity.apply(self.root, self.root / "dist")
        self.assertEqual(saved.read_text(), self.sources["src/game.cpp"])

    def test_destination_symlink_is_rejected(self):
        (self.root / "src/ds_hud.h").symlink_to(self.root / "missing")
        with self.assertRaises(ValueError): activity.apply(self.root, self.root / "dist")
        self.originals_unchanged()

    def test_parent_escape_is_rejected(self):
        (self.root / "outside").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): core.safe_target(self.root, "outside/test.cpp")

    def test_duplicate_anchor_is_rejected(self):
        with self.assertRaises(ValueError):
            activity.patch_text("src/game.cpp", self.sources["src/game.cpp"] + body.PANEL)

    def test_missing_template_fails_before_writes(self):
        with patch.dict(activity.TEMPLATES, {"missing.template": "src/extra.h"}):
            with self.assertRaises(FileNotFoundError): activity.apply(self.root, self.root / "dist")
        self.originals_unchanged()
        self.assertFalse((self.root / "src/ds_hud.cpp").exists())

    def test_second_overlay_is_rejected(self):
        activity.apply(self.root, self.root / "dist")
        with self.assertRaises(ValueError): activity.apply(self.root, self.root / "dist")

    def test_session_and_activity_hooks_unchanged(self):
        for path in ("src/main.cpp", body.JAVA):
            self.assertEqual(activity.patch_text(path, self.sources[path]),
                             core.patch_text(path, self.sources[path]))
        accepted = (HERE / "core-status/DualScreenHud.java").read_text()
        updated = (TEMPLATES / "DualScreenHud.java").read_text()
        # UI construction differs, but display/focus/poll/lifecycle logic does not.
        old_prefix = accepted.split("    private static final class HudPresentation")[0]
        new_prefix = updated.split("    private static final class HudPresentation")[0]
        normalize = lambda s: "\n".join(x for x in s.splitlines()
            if not x.startswith(("import ", "/**", "    //", "        StringBuilder details")))
        self.assertEqual(normalize(old_prefix), normalize(new_prefix))

    def test_current_values_and_widget_capture_only(self):
        capture = activity.patch_text("src/game.cpp", self.sources["src/game.cpp"])
        for getter in ("get_str", "get_dex", "get_int", "get_per", "get_speed", "get_focus"):
            self.assertIn(f"u.{getter}()", capture)
        for wid in activity.WIDGET_IDS: self.assertIn('"' + wid + '"', capture)
        for code in ("id.is_valid()", "widget view = id.obj();", "remove_color_tags( view.show( u, 80 ) )"):
            self.assertIn(code, capture)
        for forbidden in ("get_perceived_pain", "mod_moves", "set_movement", "do_turn(", "get_width_right", "TERRAIN_WINDOW_WIDTH"):
            self.assertNotIn(forbidden, capture)
        self.assertEqual(capture.count("ds_hud::publish("), 1)

    def test_ui_scope_and_clearing(self):
        java = (TEMPLATES / "DualScreenHud.java").read_text()
        for expected in ("FLAG_NOT_FOCUSABLE", "FOCUS_BLOCK_DESCENDANTS", "ScrollView",
                         "activityStatus.setVisibility(View.GONE)", 'field.setText("")', "Typeface.MONOSPACE"):
            self.assertIn(expected, java)
        for forbidden in ("dispatchKeyEvent", "nativeKeyDown", "performClick", "setTextIsSelectable"):
            self.assertNotIn(forbidden, java)

    def test_accepted_core_decoder_is_reused_verbatim(self):
        self.assertEqual(activity.TEMPLATES["core-status/CoreHudSnapshot.java"],
                         core.TEMPLATES["CoreHudSnapshot.java"])
        self.assertEqual(body.blob_sha((HERE / "core-status/CoreHudSnapshot.java").read_bytes()),
                         "847763b9654a6d112c67e7458d98da9b16cc9f11")

    def test_named_widget_definitions_are_the_pinned_ones(self):
        repo = HERE.parent.parent
        expected = {"activity.json": "19c8755996ea166eaeb9fd1f3175f53511863a2c",
                    "weariness.json": "a18c11eefad568bc9acfd423c4768e2f15f49c70",
                    "pain.json": "8cfa52b17b98821682fba545c11cd9592f5988fe"}
        widgets = {}
        for name, digest in expected.items():
            data = (repo / "data/json/ui" / name).read_bytes()
            self.assertEqual(body.blob_sha(data), digest)
            widgets.update({item["id"]: item for item in json.loads(data)})
        self.assertEqual(set(activity.WIDGET_IDS) - set(widgets), set())
        self.assertEqual(widgets["weariness_transition_graph"]["width"], 5)
        self.assertEqual(widgets["pain_desc_label"]["var"], "pain_text")
        self.assertIn("clauses", widgets["activity_desc"])

    def test_native_mailbox_coherence_and_session_clearing(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        exe = self.root / "mailbox"
        run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread", "-I", str(TEMPLATES),
             str(TEMPLATES / "ds_hud.cpp"), str(TEMPLATES / "test_mailbox.cpp"), "-o", str(exe)])
        run([str(exe)])

    def test_capture_hook_calls_widgets_and_keeps_definitions_unchanged(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        self.assertIsNotNone(compiler)
        inc = self.root / "include"
        inc.mkdir()
        shutil.copyfile(FIXTURES / "capture_game.h", inc / "game.h")
        shutil.copyfile(FIXTURES / "capture_widget.h", inc / "widget.h")
        (inc / "move_mode.h").write_text('#pragma once\n#include "game.h"\n')
        capture = self.root / "capture.cpp"
        capture.write_text(activity.patch_text("src/game.cpp", self.sources["src/game.cpp"]))
        obj = self.root / "capture.o"
        run([compiler, "-std=c++17", "-D__ANDROID__", "-Wall", "-Wextra", "-Werror",
             "-I", str(inc), "-I", str(TEMPLATES), "-c", str(capture), "-o", str(obj)])
        exe = self.root / "capture-test"
        run([compiler, "-std=c++17", "-pthread", "-I", str(inc), "-I", str(TEMPLATES),
             str(FIXTURES / "test_capture.cpp"), str(TEMPLATES / "ds_hud.cpp"), str(obj), "-o", str(exe)])
        run([str(exe)])

    def test_real_jni_transport_and_java_decoder(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        javac, java = shutil.which("javac"), shutil.which("java")
        self.assertIsNotNone(compiler)
        self.assertIsNotNone(javac)
        self.assertIsNotNone(java)
        headers = Path(javac).resolve().parent.parent / "include"
        library = self.root / "libactivity_hud_host.so"
        run([compiler, "-std=c++17", "-shared", "-fPIC", "-pthread", "-D__ANDROID__",
             "-Wall", "-Wextra", "-Werror", "-I", str(headers), "-I", str(headers / "linux"),
             "-I", str(TEMPLATES), str(TEMPLATES / "ds_hud.cpp"), str(FIXTURES / "test_jni.cpp"), "-o", str(library)])
        classes = self.root / "classes"
        classes.mkdir()
        run([javac, "--release", "8", "-Xlint:all,-options", "-Werror", "-d", str(classes),
             str(HERE / "core-status/CoreHudSnapshot.java"), str(TEMPLATES / "ActivityHudSnapshot.java"),
             str(FIXTURES / "DualScreenHud.java"), str(FIXTURES / "ActivityHudSnapshotTest.java")])
        result = run([java, "-Xcheck:jni", "-cp", str(classes),
                      "com.cleverraven.cataclysmdda.ActivityHudSnapshotTest", str(library)])
        self.assertIn("activity real JNI round-trip passed", result.stdout)
        self.assertNotIn("WARNING", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
