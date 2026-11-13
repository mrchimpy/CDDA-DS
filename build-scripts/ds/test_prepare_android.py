"""Offline tests for the packaging helper; these are not APK/device tests."""
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

import prepare_android as build


class PrepareTests(unittest.TestCase):
    def make_archive(self, extra=None, omit=None):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            for prefix in build.RESOURCE_ROOTS:
                if prefix != omit:
                    archive.writestr("assets/" + prefix + "sample.txt", b"fixture")
            archive.writestr("classes.dex", b"must not copy")
            archive.writestr("lib/arm64-v8a/libmain.so", b"must not copy")
            archive.writestr("assets/data/json/gameplay.json", b"must not overwrite")
            if extra:
                archive.writestr(*extra)
        data.seek(0)
        return zipfile.ZipFile(data)

    def test_replacement_is_idempotent(self):
        self.assertEqual(build.verified_replacement("abc", "abc", "xyz"), "xyz")
        self.assertEqual(build.verified_replacement("xyz", "abc", "xyz"), "xyz")

    def test_replacement_rejects_ambiguous_or_missing_source(self):
        for value in ("abc abc", "unknown", "abc xyz"):
            with self.assertRaises(ValueError):
                build.verified_replacement(value, "abc", "xyz")

    def test_identity_overlay_preserves_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, edits in build.IDENTITY_EDITS.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('\n'.join(before for before, _ in edits) + '\n', encoding="utf-8")
            gradle = root / "android/app/build.gradle"
            gradle.write_text('namespace "com.cleverraven.cataclysmdda"\n' + gradle.read_text(), encoding="utf-8")
            pending = build.identity_changes(root)
            self.assertIn('namespace "com.cleverraven.cataclysmdda"', pending[gradle])
            self.assertIn('applicationId "io.github.mrchimpy.cddads"', pending[gradle])
            self.assertIn('applicationId "com.cleverraven.cataclysmdda"', gradle.read_text())

    def test_allowlist_excludes_executables_and_gameplay(self):
        with tempfile.TemporaryDirectory() as directory, self.make_archive() as archive:
            plan, counts = build.resource_plan(archive, Path(directory))
            self.assertEqual(len(plan), 4)
            self.assertEqual(set(counts.values()), {1})

    def test_missing_resource_category_fails(self):
        with tempfile.TemporaryDirectory() as directory, self.make_archive(omit="gfx/") as archive:
            with self.assertRaises(ValueError):
                build.resource_plan(archive, Path(directory))

    def test_path_traversal_fails(self):
        with tempfile.TemporaryDirectory() as directory, self.make_archive(("assets/gfx/../../escape", "bad")) as archive:
            with self.assertRaises(ValueError):
                build.resource_plan(archive, Path(directory))

    def test_executable_in_resource_directory_fails(self):
        with tempfile.TemporaryDirectory() as directory, self.make_archive(("assets/gfx/evil.so", "bad")) as archive:
            with self.assertRaises(ValueError):
                build.resource_plan(archive, Path(directory))

    def test_symlink_fails(self):
        info = zipfile.ZipInfo("assets/gfx/link")
        info.create_system = 3
        info.external_attr = (0o120777 << 16)
        with tempfile.TemporaryDirectory() as directory, self.make_archive((info, "target")) as archive:
            with self.assertRaises(ValueError):
                build.resource_plan(archive, Path(directory))

    def test_wrong_hash_fails_before_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / "wrong.apk"
            apk.write_bytes(b"not the upstream APK")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                build.prepare(root, apk)
            self.assertEqual(list(root.iterdir()), [apk])


if __name__ == "__main__":
    unittest.main()
