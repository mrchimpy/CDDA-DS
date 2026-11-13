#!/usr/bin/env python3
"""Prepare an isolated CDDA-DS test build; never copy executable code from an APK."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

BASELINE_SHA = "bb52239dee96df602da097f113382fe5c9a9c115"
BASELINE_TAG = "cdda-experimental-2026-10-19-0834"
APK_SHA256 = "f2f04a347728664cc0a240f50630d6e278f1e88f04101c1d811404af54749bab"
APPLICATION_ID = "io.github.mrchimpy.cddads.experimental"
RESOURCE_ROOTS = ("gfx/", "data/sound/", "data/shaders/", "lang/mo/")
MAX_RESOURCE_BYTES = 4 * 1024**3

# Keep the Java namespace and JNI class names unchanged. Only installation identity
# and visible labels change. Validate every edit before writing any of the files.
IDENTITY_EDITS = {
    "android/app/build.gradle": (
        ('applicationId "com.cleverraven.cataclysmdda"',
         'applicationId "io.github.mrchimpy.cddads"'),
        ('resValue "string", "app_name", "Cataclysm DDA (experimental)"',
         'resValue "string", "app_name", "CDDA-DS (test)"'),
    ),
    "android/app/src/main/AndroidManifest.xml": (
        ('android:authorities="com.cleverraven.cataclysmdda.documents"',
         'android:authorities="${applicationId}.documents"'),
    ),
    "android/app/src/main/java/com/cleverraven/cataclysmdda/CDDADocumentsProvider.java": (
        ('rowValues[i] = "CDDA Game Data";',
         'rowValues[i] = "CDDA-DS Test Data";'),
    ),
}


def verified_replacement(text: str, before: str, after: str) -> str:
    """Apply once, allow an already-applied edit, and reject ambiguous source."""
    old_count, new_count = text.count(before), text.count(after)
    if old_count == 1 and new_count == 0:
        return text.replace(before, after, 1)
    if old_count == 0 and new_count == 1:
        return text
    raise ValueError(f"Unexpected source near {before!r}: old={old_count}, new={new_count}")


def identity_changes(root: Path) -> dict[Path, str]:
    pending = {}
    for relative, edits in IDENTITY_EDITS.items():
        path = root / relative
        text = path.read_text(encoding="utf-8")
        for before, after in edits:
            text = verified_replacement(text, before, after)
        pending[path] = text
    return pending


def verify_apk(apk: Path) -> None:
    with apk.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != APK_SHA256:
        raise ValueError(f"Baseline APK SHA-256 mismatch: expected {APK_SHA256}, got {actual}")


def resource_plan(archive: zipfile.ZipFile, root: Path) -> tuple[list, dict[str, int]]:
    """Plan an allowlisted extraction, rejecting traversal, symlinks and duplicates."""
    root = root.resolve()
    plan, seen = [], set()
    counts = dict.fromkeys(RESOURCE_ROOTS, 0)
    total_bytes = 0
    for info in archive.infolist():
        if info.is_dir() or not info.filename.startswith("assets/"):
            continue
        relative = info.filename[len("assets/"):]
        category = next((prefix for prefix in RESOURCE_ROOTS if relative.startswith(prefix)), None)
        if category is None:
            continue
        parts = PurePosixPath(relative).parts
        if ".." in parts or "\\" in relative or relative.startswith("/"):
            raise ValueError(f"Unsafe resource path: {relative}")
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError(f"Symlink resource rejected: {relative}")
        destination = (root / relative).resolve()
        category_root = (root / category).resolve()
        if not category_root.is_relative_to(root) or not destination.is_relative_to(category_root):
            raise ValueError(f"Resource escapes its allowed directory: {relative}")
        if destination in seen:
            raise ValueError(f"Duplicate resource: {relative}")
        if destination.suffix.lower() in {".so", ".dex", ".jar", ".apk"}:
            raise ValueError(f"Executable resource rejected: {relative}")
        seen.add(destination)
        total_bytes += info.file_size
        if total_bytes > MAX_RESOURCE_BYTES:
            raise ValueError("Resource archive exceeds the allowed extracted size")
        counts[category] += 1
        plan.append((info, destination))
    missing = [prefix for prefix, count in counts.items() if count == 0]
    if missing:
        raise ValueError(f"Expected baseline resource directories missing: {missing}")
    return plan, counts


def prepare(root: Path, apk: Path) -> dict:
    verify_apk(apk)  # No extraction or source writes before verification succeeds.
    pending = identity_changes(root)
    with zipfile.ZipFile(apk) as archive:
        plan, counts = resource_plan(archive, root)
        for info, destination in plan:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
    for path, text in pending.items():
        path.write_text(text, encoding="utf-8")
    return {
        "baseline_tag": BASELINE_TAG,
        "baseline_commit": BASELINE_SHA,
        "resource_apk_sha256": APK_SHA256,
        "application_id": APPLICATION_ID,
        "provider_authority": APPLICATION_ID + ".documents",
        "label": "CDDA-DS (test)",
        "resource_file_counts": counts,
        "packaging_overlay_paths": list(IDENTITY_EDITS),
        "executable_source": "compiled from the checked-out repository, not the baseline APK",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.root.resolve(), args.apk.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
