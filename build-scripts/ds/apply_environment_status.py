#!/usr/bin/env python3
"""Add seven environment/time widgets using the hash-locked activity HUD templates."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

import apply_activity_status as activity
import apply_body_status as body
import apply_core_status as core

EXPECTED_BLOBS = dict(activity.EXPECTED_BLOBS)
TEMPLATE_BLOBS = {
    "activity-status/ds_hud.h": "f6b2e846fa5b13db33333fd84a47622cbdb8eeed",
    "activity-status/ds_hud.cpp": "7bb30813c8d6dd42a747d2f53a2f5eec3bba5ae0",
    "activity-status/DualScreenHud.java": "de1a0c2e6cf502ef01a19d286a9c90d88768dc93",
    "core-status/CoreHudSnapshot.java": "847763b9654a6d112c67e7458d98da9b16cc9f11",
    "activity-status/ActivityHudSnapshot.java": "cacb16ab291cabc9597404435444681bc8b67a1e",
}
# Append only: original five fields keep their indices, labels and layout.
ENVIRONMENT_WIDGETS = (
    ("date_desc_label", "Date"),
    ("time_desc_label", "Time"),
    ("place_desc", "Place"),
    ("weather_desc", "Weather"),
    ("lighting_desc", "Lighting"),
    ("wind_desc", "Wind"),
    ("env_temp_desc", "Temperature"),
)
WIDGET_IDS = activity.WIDGET_IDS + tuple(item[0] for item in ENVIRONMENT_WIDGETS)
OLD_COUNT = len(activity.WIDGET_IDS)
STATUS_COUNT = len(WIDGET_IDS)


def patch_text(path: str, text: str) -> str:
    result = activity.patch_text(path, text)
    if path == "src/game.cpp":
        def declaration(ids: tuple[str, ...]) -> str:
            return 'const char *const widget_ids[] = { ' + ', '.join(
                json.dumps(value) for value in ids) + ' };'
        result = body.replace_once(result, declaration(activity.WIDGET_IDS),
                                   declaration(WIDGET_IDS))
    return result


def render_templates(template_root: Path | None = None) -> dict[str, str]:
    """Derive build-workspace files in memory; never modify accepted experiments."""
    template_root = (template_root or Path(__file__).resolve().parent).resolve()
    source = {}
    for path, expected in TEMPLATE_BLOBS.items():
        data = core.safe_target(template_root, path).read_bytes()
        if body.blob_sha(data) != expected:
            raise ValueError(f"Accepted template changed; review derivation first: {path}")
        source[path] = data.decode("utf-8")
    rendered = {target: source[path] for path, target in activity.TEMPLATES.items()}
    h = rendered["src/ds_hud.h"]
    h = body.replace_once(h, f"activity_field_count = {OLD_COUNT};",
                           f"activity_field_count = {STATUS_COUNT};")
    h = body.replace_once(h, "// Original 24 numeric fields, then five widget-availability flags.",
                           "// Original 24 numeric fields, then twelve widget-availability flags.")
    h = body.replace_once(h, "// UTF-8 byte arrays carry movement, weariness, activity, transition, malus, pain.",
                           "// UTF-8 arrays: movement, five activity fields, then seven environment fields.")
    rendered["src/ds_hud.h"] = h
    rendered["src/ds_hud.cpp"] = body.replace_once(rendered["src/ds_hud.cpp"],
        "Object[] { long[29], byte[6][] }", "Object[] { long[36], byte[13][] }")
    decoder_path = activity.JAVA_DIR + "ActivityHudSnapshot.java"
    decoder = body.replace_once(rendered[decoder_path],
        "copy of the five game-rendered status widgets.",
        "copy of twelve game-rendered activity/environment widgets.")
    decoder = body.replace_once(decoder, f"STATUS_COUNT = {OLD_COUNT};",
                                         f"STATUS_COUNT = {STATUS_COUNT};")
    decoder = body.replace_once(decoder,
        '"Weariness", "Activity", "Transition", "Weary Malus", "Pain"',
        '"Weariness", "Activity", "Transition", "Weary Malus", "Pain",\n        '
        + ', '.join(json.dumps(label) for _, label in ENVIRONMENT_WIDGETS))
    rendered[decoder_path] = decoder
    ui_path = activity.JAVA_DIR + "DualScreenHud.java"
    ui = body.replace_once(rendered[ui_path], '"CDDA-DS / ACTIVITY STATUS"',
                                             '"CDDA-DS / ENVIRONMENT STATUS"')
    ui = body.replace_once(ui,
        "for (int i = 0; i < ActivityHudSnapshot.STATUS_COUNT; i += 2)",
        f"for (int i = 0; i < {OLD_COUNT}; i += 2)")
    ui = body.replace_once(ui, "column < 2 && i + column < activityValues.length",
                              f"column < 2 && i + column < {OLD_COUNT}")
    ui = body.replace_once(ui, "column == 0 && i + 1 < activityValues.length",
                              f"column == 0 && i + 1 < {OLD_COUNT}")
    ui = body.replace_once(ui, "            activityStatus.setVisibility(View.GONE);\n"
        "            layout.addView(activityStatus);\n",
        "            // Temporary full-width, wrapping rows; no tabs or smaller fonts.\n"
        f"            for (int i = {OLD_COUNT}; i < activityValues.length; i++) {{\n"
        '                activityValues[i] = text("", 16);\n'
        "                activityStatus.addView(activityValues[i]);\n"
        "            }\n"
        "            activityStatus.setVisibility(View.GONE);\n"
        "            layout.addView(activityStatus);\n")
    rendered[ui_path] = ui
    return rendered


def apply(root: Path, output: Path, template_root: Path | None = None) -> dict:
    root = root.resolve()
    pending: dict[str, tuple[str, str]] = {}
    # Plan all changes, including derived templates, before the first source write.
    for relative, expected in EXPECTED_BLOBS.items():
        data = core.safe_target(root, relative).read_bytes()
        if body.blob_sha(data) != expected:
            raise ValueError(f"Environment status expects pinned original source: {relative}")
        before = data.decode("utf-8")
        pending[relative] = (before, patch_text(relative, before))
    for relative, after in render_templates(template_root).items():
        if core.safe_target(root, relative).exists():
            raise ValueError(f"Environment status destination already exists: {relative}")
        pending[relative] = ("", after)
    diff = "".join("".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + path if before else "/dev/null", tofile="b/" + path))
        for path, (before, after) in pending.items())
    report = {
        "experiment": "environment_status",
        "architecture": "same APK; copied-state mailbox; Android Presentation",
        "game_actions": False,
        "original_sidebar_retained": True,
        "widget_ids": list(WIDGET_IDS),
        "derived_from_template_blobs": dict(TEMPLATE_BLOBS),
        "patch_file": "ENVIRONMENT-STATUS.patch",
        "paths": {path: hashlib.sha256(after.encode("utf-8")).hexdigest()
                  for path, (_, after) in pending.items()},
    }
    for relative, (_, after) in pending.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "ENVIRONMENT-STATUS.patch").write_text(diff, encoding="utf-8")
    (output / "ENVIRONMENT-STATUS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
