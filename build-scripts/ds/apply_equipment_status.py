#!/usr/bin/env python3
"""Append five equipment/status widgets to the accepted environment HUD."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

import apply_activity_status as activity
import apply_body_status as body
import apply_core_status as core
import apply_environment_status as environment

EXPECTED_BLOBS = dict(environment.EXPECTED_BLOBS)
# Append only: the accepted twelve widget slots keep their positions and meaning.
EQUIPMENT_WIDGETS = (
    ("wielding_desc", "Wield"),
    ("style_desc", "Style"),
    ("power_desc", "Bionic Power"),
    ("sound_num", "Sound"),
    ("mood_desc_label", "Mood"),
)
WIDGET_IDS = environment.WIDGET_IDS + tuple(wid for wid, _ in EQUIPMENT_WIDGETS)
OLD_COUNT = environment.STATUS_COUNT
STATUS_COUNT = len(WIDGET_IDS)


def declaration(ids: tuple[str, ...]) -> str:
    return 'const char *const widget_ids[] = { ' + ', '.join(
        json.dumps(value) for value in ids) + ' };'


def patch_text(path: str, text: str) -> str:
    result = environment.patch_text(path, text)
    if path == "src/game.cpp":
        result = body.replace_once(result, declaration(environment.WIDGET_IDS),
                                   declaration(WIDGET_IDS))
    return result


def render_templates(template_root: Path | None = None) -> dict[str, str]:
    """Extend hash-validated templates in memory; never rewrite accepted experiments."""
    rendered = environment.render_templates(template_root)
    h = body.replace_once(rendered["src/ds_hud.h"],
        f"activity_field_count = {OLD_COUNT};", f"activity_field_count = {STATUS_COUNT};")
    h = body.replace_once(h, "// Original 24 numeric fields, then twelve widget-availability flags.",
                            "// Original 24 numeric fields, then seventeen widget-availability flags.")
    h = body.replace_once(h,
        "// UTF-8 arrays: movement, five activity fields, then seven environment fields.",
        "// UTF-8 arrays: movement, five activity, seven environment, five equipment/status fields.")
    rendered["src/ds_hud.h"] = h
    rendered["src/ds_hud.cpp"] = body.replace_once(rendered["src/ds_hud.cpp"],
        "Object[] { long[36], byte[13][] }", "Object[] { long[41], byte[18][] }")
    path = activity.JAVA_DIR + "ActivityHudSnapshot.java"
    decoder = body.replace_once(rendered[path],
        "copy of twelve game-rendered activity/environment widgets.",
        "copy of seventeen game-rendered activity/environment/equipment widgets.")
    decoder = body.replace_once(decoder, f"STATUS_COUNT = {OLD_COUNT};",
                                         f"STATUS_COUNT = {STATUS_COUNT};")
    previous_labels = ', '.join(json.dumps(label) for _, label in environment.ENVIRONMENT_WIDGETS)
    decoder = body.replace_once(decoder, previous_labels, previous_labels + ',\n        '
        + ', '.join(json.dumps(label) for _, label in EQUIPMENT_WIDGETS))
    rendered[path] = decoder
    path = activity.JAVA_DIR + "DualScreenHud.java"
    # Existing full-width loop is array-sized, so new rows inherit wrapping/clearing.
    rendered[path] = body.replace_once(rendered[path], '"CDDA-DS / ENVIRONMENT STATUS"',
                                                       '"CDDA-DS / EQUIPMENT STATUS"')
    return rendered


def apply(root: Path, output: Path, template_root: Path | None = None) -> dict:
    root = root.resolve()
    pending: dict[str, tuple[str, str]] = {}
    # Check every hash, anchor, template and destination before source writes.
    for relative, expected in EXPECTED_BLOBS.items():
        data = core.safe_target(root, relative).read_bytes()
        if body.blob_sha(data) != expected:
            raise ValueError(f"Equipment status expects pinned original source: {relative}")
        before = data.decode("utf-8")
        pending[relative] = (before, patch_text(relative, before))
    for relative, after in render_templates(template_root).items():
        if core.safe_target(root, relative).exists():
            raise ValueError(f"Equipment status destination already exists: {relative}")
        pending[relative] = ("", after)
    diff = "".join("".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + path if before else "/dev/null", tofile="b/" + path))
        for path, (before, after) in pending.items())
    report = {
        "experiment": "equipment_status",
        "architecture": "same APK; copied-state mailbox; Android Presentation",
        "game_actions": False,
        "original_sidebar_retained": True,
        "widget_ids": list(WIDGET_IDS),
        "derived_from_template_blobs": dict(environment.TEMPLATE_BLOBS),
        "patch_file": "EQUIPMENT-STATUS.patch",
        "paths": {path: hashlib.sha256(after.encode("utf-8")).hexdigest()
                  for path, (_, after) in pending.items()},
    }
    for relative, (_, after) in pending.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "EQUIPMENT-STATUS.patch").write_text(diff, encoding="utf-8")
    (output / "EQUIPMENT-STATUS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
