"""Tests generate disposable LOCAL fixture keys; no project signing secret is used."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from configure_signing import configure, property_value, private_write, KEY_SECRET, PASSWORD_SECRET


class SigningFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "repo"
        (self.root / "android").mkdir(parents=True)
        self.temporary = Path(self.directory.name) / "temp"


class SigningValidationTests(SigningFixture):
    def test_missing_secrets_fail_before_creating_key(self):
        with self.assertRaisesRegex(ValueError, "requires repository secrets"):
            configure(self.root, self.temporary, "persistent", {})
        self.assertFalse(self.temporary.exists())

    def test_partial_secrets_do_not_fall_back_to_disposable(self):
        with self.assertRaises(ValueError):
            configure(self.root, self.temporary, "persistent", {PASSWORD_SECRET: "not-a-real-password"})
        self.assertFalse(self.temporary.exists())

    def test_invalid_base64_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Base64"):
            configure(self.root, self.temporary, "persistent", {KEY_SECRET: "%%%", PASSWORD_SECRET: "unused"})
        self.assertFalse(self.temporary.exists())

    def test_oversized_base64_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "size"):
            configure(self.root, self.temporary, "persistent", {KEY_SECRET: "A" * 50000, PASSWORD_SECRET: "unused"})

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            configure(self.root, self.temporary, "auto", {})

    def test_properties_escape_special_characters(self):
        self.assertEqual(property_value(" a=b:c#!\\\n\r\t"), "\\ a\\=b\\:c\\#\\!\\\\\\n\\r\\t")
        with self.assertRaises(ValueError):
            property_value("bad\0value")

    def test_private_write_is_exclusive(self):
        path = self.root / "private"
        private_write(path, b"original")
        with self.assertRaises(FileExistsError):
            private_write(path, b"replacement")
        self.assertEqual(path.read_bytes(), b"original")
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_private_write_rejects_symlink(self):
        target = self.root / "target"
        target.write_bytes(b"unchanged")
        path = self.root / "link"
        path.symlink_to(target)
        with self.assertRaises(FileExistsError):
            private_write(path, b"replacement")
        self.assertEqual(target.read_bytes(), b"unchanged")


@unittest.skipUnless(shutil.which("keytool"), "JDK keytool not installed")
class SigningKeytoolTests(SigningFixture):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.fixture.cleanup)
        cls.password = "Fixture-only-$=\\ Password!"
        path = Path(cls.fixture.name) / "fixture.p12"
        env = dict(os.environ, DS_TEST_STORE_PASSWORD=cls.password)
        subprocess.run(["keytool", "-genkeypair", "-noprompt", "-storetype", "PKCS12",
                        "-keystore", str(path), "-alias", "cdda-ds-test", "-keyalg", "RSA",
                        "-keysize", "2048", "-validity", "1", "-dname", "CN=LOCAL TEST ONLY",
                        "-storepass:env", PASSWORD_SECRET, "-keypass:env", PASSWORD_SECRET],
                       env=env, capture_output=True, check=True, timeout=60)
        cls.encoded = base64.b64encode(path.read_bytes()).decode("ascii")

    def environment(self, password=None):
        return dict(os.environ, DS_TEST_KEYSTORE_BASE64=self.encoded,
                    DS_TEST_STORE_PASSWORD=self.password if password is None else password)

    def test_persistent_cert_is_stable_across_clean_runs(self):
        first = configure(self.root, self.temporary, "persistent", self.environment())
        (self.root / "android/keystore.properties").unlink()
        (self.temporary / "cdda-ds-test.p12").unlink()
        second = configure(self.root, self.temporary, "persistent", self.environment())
        self.assertEqual(first["certificate_sha256"], second["certificate_sha256"])
        self.assertEqual(first["mode"], "persistent")
        self.assertNotIn(self.password, json.dumps(first))
        self.assertNotIn(self.encoded, json.dumps(first))
        self.assertEqual((self.temporary / "cdda-ds-test.p12").stat().st_mode & 0o777, 0o600)

    def test_wrong_password_removes_private_material(self):
        with self.assertRaisesRegex(ValueError, "validation failed"):
            configure(self.root, self.temporary, "persistent", self.environment("WRONG-FIXTURE-PASSWORD"))
        self.assertFalse((self.temporary / "cdda-ds-test.p12").exists())
        self.assertFalse((self.root / "android/keystore.properties").exists())

    def test_invalid_keystore_removes_private_material(self):
        env = self.environment()
        env[KEY_SECRET] = base64.b64encode(b"not a keystore").decode("ascii")
        with self.assertRaises(ValueError):
            configure(self.root, self.temporary, "persistent", env)
        self.assertFalse((self.temporary / "cdda-ds-test.p12").exists())

    def test_existing_properties_are_not_overwritten(self):
        path = self.root / "android/keystore.properties"
        path.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            configure(self.root, self.temporary, "persistent", self.environment())
        self.assertEqual(path.read_text(), "keep")

    def test_disposable_mode_is_explicit_and_reported(self):
        report = configure(self.root, self.temporary, "disposable", dict(os.environ))
        self.assertEqual(report["mode"], "disposable")
        self.assertEqual(len(report["certificate_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
