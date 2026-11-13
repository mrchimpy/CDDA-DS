#!/usr/bin/env python3
"""Apply the optional, hash-locked core-status HUD without changing older experiments."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

import apply_body_status as body

JAVA = body.JAVA
EXPECTED_BLOBS = dict(body.EXPECTED_BLOBS)
TEMPLATES = dict(body.TEMPLATES)
TEMPLATES["CoreHudSnapshot.java"] = (
    "android/app/src/main/java/com/cleverraven/cataclysmdda/CoreHudSnapshot.java"
)


def patch_text(path: str, text: str) -> str:
    # Reuse the accepted session/activity hooks, without changing their implementation.
    result = body.patch_text(path, text)
    if path == "src/game.cpp":
        result = body.replace_once(result, '#include "ds_hud.h"\n',
                                   '#include "ds_hud.h"\n#include "move_mode.h"\n')
        result = body.replace_once(result,
            '    ds_hud::publish( u.get_stamina(), u.get_stamina_max(), health );\n',
            '    ds_hud::core_status core;\n'
            '    core.strength = u.get_str();\n'
            '    core.dexterity = u.get_dex();\n'
            '    core.intelligence = u.get_int();\n'
            '    core.perception = u.get_per();\n'
            '    core.speed = u.get_speed();\n'
            '    core.focus = u.get_focus();\n'
            '    core.movement_mode = u.current_movement_mode()->name() + " (" +\n'
            '                         std::string( 1, u.current_movement_mode()->panel_letter() ) + ")";\n'
            '    ds_hud::publish( u.get_stamina(), u.get_stamina_max(), health, core );\n')
    return result


def safe_target(root: Path, relative: str) -> Path:
    target = root / relative
    if target.is_symlink() or not target.resolve().is_relative_to(root):
        raise ValueError(f"Unsafe overlay path: {relative}")
    return target


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    pending: dict[str, tuple[str, str]] = {}
    # Plan and validate all source hashes and new destinations before writing.
    for relative, expected in EXPECTED_BLOBS.items():
        data = safe_target(root, relative).read_bytes()
        if body.blob_sha(data) != expected:
            raise ValueError(f"Core status expects pinned original source: {relative}")
        before = data.decode("utf-8")
        pending[relative] = (before, patch_text(relative, before))
    templates = Path(__file__).resolve().parent / "core-status"
    for template, relative in TEMPLATES.items():
        if safe_target(root, relative).exists():
            raise ValueError(f"Core status destination already exists: {relative}")
        pending[relative] = ("", (templates / template).read_text(encoding="utf-8"))
    patch = "".join("".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + relative if before else "/dev/null", tofile="b/" + relative))
        for relative, (before, after) in pending.items())
    report = {
        "experiment": "core_status",
        "architecture": "same APK; native copied-state mailbox; Android Presentation",
        "game_actions": False,
        "original_sidebar_retained": True,
        "patch_file": "CORE-STATUS.patch",
        "paths": {path: hashlib.sha256(after.encode("utf-8")).hexdigest()
                  for path, (_, after) in pending.items()},
    }
    for relative, (_, after) in pending.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "CORE-STATUS.patch").write_text(patch, encoding="utf-8")
    (output / "CORE-STATUS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
