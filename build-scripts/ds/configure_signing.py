#!/usr/bin/env python3
"""Prepare Android test signing without printing, caching, or publishing a private key."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import subprocess

ALIAS = "cdda-ds-test"
KEY_SECRET = "DS_TEST_KEYSTORE_BASE64"
PASSWORD_SECRET = "DS_TEST_STORE_PASSWORD"
MAX_ENCODED_BYTES = 48 * 1024


def property_value(value: str) -> str:
    """Escape a value for java.util.Properties.load(Reader)."""
    escapes = {"\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t",
               "\f": "\\f", " ": "\\ ", "=": "\\=", ":": "\\:",
               "#": "\\#", "!": "\\!"}
    if "\0" in value:
        raise ValueError("NUL characters are not supported in signing properties")
    return "".join(escapes.get(char, char) for char in value)


def private_write(path: Path, payload: bytes) -> None:
    # Never replace an existing file or follow a symlink at the destination.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(payload)


def keytool(arguments: list[str], environment: dict[str, str]) -> bytes:
    result = subprocess.run(
        ["keytool", "-J-Duser.language=en", "-J-Duser.country=US", *arguments],
        env=environment, capture_output=True, check=False, timeout=60,
    )
    if result.returncode:
        # Do not echo input, command arguments, or diagnostic output containing secrets.
        raise ValueError("Signing keystore validation failed; check its password, PKCS12 format, and cdda-ds-test alias")
    return result.stdout


def configure(root: Path, temporary: Path, mode: str, environment: dict[str, str]) -> dict:
    root, temporary = root.resolve(), temporary.resolve()
    if mode not in {"persistent", "disposable"}:
        raise ValueError("Choose persistent or disposable signing explicitly")
    encoded = environment.get(KEY_SECRET, "")
    password = environment.get(PASSWORD_SECRET, "")
    if mode == "persistent":
        if not encoded or not password:
            raise ValueError("Persistent signing requires repository secrets DS_TEST_KEYSTORE_BASE64 and DS_TEST_STORE_PASSWORD; see doc/dual-screen/SIGNING.md")
        if len(encoded) > MAX_ENCODED_BYTES:
            raise ValueError("The encoded keystore exceeds the supported GitHub secret size")
        try:
            payload = base64.b64decode(encoded.strip(), validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("The keystore secret is not valid single-line Base64") from exc
        if not payload:
            raise ValueError("The keystore secret is empty")
    else:
        password, payload = "android", b""
    # Validate property encoding before creating private files.
    escaped_password = property_value(password)
    temporary.mkdir(parents=True, exist_ok=True)
    keystore = temporary / "cdda-ds-test.p12"
    properties = root / "android/keystore.properties"
    if keystore.exists() or keystore.is_symlink() or properties.exists() or properties.is_symlink():
        raise FileExistsError("Refusing to replace existing signing files")
    if not properties.parent.is_dir():
        raise ValueError("Android project directory is missing")
    key_environment = dict(environment)
    key_environment.pop(KEY_SECRET, None)
    key_environment[PASSWORD_SECRET] = password
    shared = ["-keystore", str(keystore), "-storetype", "PKCS12",
              "-storepass:env", PASSWORD_SECRET, "-alias", ALIAS]
    created_key = created_properties = False
    try:
        if mode == "persistent":
            private_write(keystore, payload)
            created_key = True
        else:
            # This location is a private runner temporary directory, not a cached path.
            created_key = True
            keytool(["-genkeypair", "-noprompt", *shared,
                     "-keypass:env", PASSWORD_SECRET, "-keyalg", "RSA", "-keysize", "2048",
                     "-validity", "3650", "-dname", "CN=CDDA-DS Disposable Test,O=CDDA-DS,C=US"],
                    key_environment)
            keystore.chmod(0o600)
        listing = keytool(["-list", "-v", *shared], key_environment)
        if b"PrivateKeyEntry" not in listing:
            raise ValueError("The signing alias must contain a private key, not just a certificate")
        certificate = keytool(["-exportcert", *shared], key_environment)
        fingerprint = hashlib.sha256(certificate).hexdigest()
        text = (f"storeFile={property_value(str(keystore))}\n"
                f"storePassword={escaped_password}\nkeyAlias={ALIAS}\n"
                f"keyPassword={escaped_password}\n")
        private_write(properties, text.encode("utf-8"))
        created_properties = True
        return {"mode": mode, "alias": ALIAS, "certificate_sha256": fingerprint,
                "note": "In-place updates require the same signing certificate and compatible versioning"}
    except Exception:
        if created_key:
            keystore.unlink(missing_ok=True)
        if created_properties:
            properties.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("persistent", "disposable"), required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--temporary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = configure(args.root, args.temporary, args.mode, dict(os.environ))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"Signing setup stopped: {exc}\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))  # Public certificate fingerprint only.


if __name__ == "__main__":
    main()
