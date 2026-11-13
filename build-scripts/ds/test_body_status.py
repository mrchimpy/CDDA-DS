"""Host/fixture tests; these do not claim Android or Thor runtime validation."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apply_body_status as probe

FIXTURES = {
    "src/game.cpp": probe.INCLUDE + probe.PANEL + "    static int previous_turn = -1;\n}\n",
    "src/main.cpp": probe.INCLUDE + "void run_game_loop() {\n" + probe.SESSION + "}\n",
    probe.JAVA: "class CataclysmDDA {\n    private NativeUI nativeUI = null;\n"
        + probe.RESUME + "    }\n" + probe.FOCUS + "\n    }\n}\n",
}


class ProbeTests(unittest.TestCase):
    def test_unique_anchor_required(self):
        for source in ("", "xx"):
            with self.assertRaises(ValueError):
                probe.replace_once(source, "x", "y")
        self.assertEqual(probe.replace_once("axb", "x", "y"), "ayb")

    def test_hooks_are_observation_only(self):
        game = probe.patch_text("src/game.cpp", FIXTURES["src/game.cpp"])
        main = probe.patch_text("src/main.cpp", FIXTURES["src/main.cpp"])
        self.assertIn("ds_hud::publish( u.get_stamina(), u.get_stamina_max(), health );", game)
        self.assertIn("const ds_hud::session_scope ds_hud_session;", main)
        self.assertIn("static int previous_turn = -1;", game)
        self.assertNotIn("set_stamina", game)

    def test_activity_hooks_release_resources(self):
        text = probe.patch_text(probe.JAVA, FIXTURES[probe.JAVA])
        self.assertEqual(text.count("dualScreenHud.start();"), 1)
        self.assertEqual(text.count("dualScreenHud.stop();"), 2)
        self.assertIn("super.onPause();", text)
        self.assertIn("super.onDestroy();", text)

    def test_unexpected_source_fails_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "src/game.cpp"
            path.parent.mkdir()
            path.write_text("wrong baseline")
            with self.assertRaises(ValueError):
                probe.apply(root, root / "dist")
            self.assertEqual(path.read_text(), "wrong baseline")
            self.assertFalse((root / "dist").exists())
            self.assertFalse((root / "src/ds_hud.cpp").exists())

    def test_plan_applies_and_records_all_six_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, content in FIXTURES.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            hashes = {name: probe.blob_sha(content.encode()) for name, content in FIXTURES.items()}
            with patch.object(probe, "EXPECTED_BLOBS", hashes):
                report = probe.apply(root, root / "dist")
                self.assertEqual(len(report["paths"]), 6)
                self.assertIn("/dev/null", (root / "dist/BODY-STATUS.patch").read_text())
                with self.assertRaises(ValueError):
                    probe.apply(root, root / "dist")

    def test_existing_destination_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, content in FIXTURES.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            (root / "src/ds_hud.h").write_text("existing")
            hashes = {name: probe.blob_sha(content.encode()) for name, content in FIXTURES.items()}
            with patch.object(probe, "EXPECTED_BLOBS", hashes):
                with self.assertRaises(ValueError):
                    probe.apply(root, root / "dist")
            self.assertEqual((root / "src/game.cpp").read_text(), FIXTURES["src/game.cpp"])

    @unittest.skipUnless(shutil.which("g++"), "host C++ compiler not available")
    def test_native_mailbox_lifecycle_and_concurrent_reads(self):
        source = Path(__file__).parent / "body-status"
        with tempfile.TemporaryDirectory() as temp:
            binary = str(Path(temp) / "test-mailbox")
            subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
                str(source / "ds_hud.cpp"), str(source / "test_mailbox.cpp"), "-o", binary], check=True)
            subprocess.run([binary], check=True, timeout=10)


if __name__ == "__main__":
    unittest.main()
