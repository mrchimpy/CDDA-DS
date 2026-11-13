#!/usr/bin/env python3
"""Append native needs and omit nine duplicate lower rows AFTER hud_presentation."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

JAVA_DIR = "android/app/src/main/java/com/cleverraven/cataclysmdda/"
UI = JAVA_DIR + "DualScreenHud.java"
DECODER = JAVA_DIR + "ActivityHudSnapshot.java"
# Exact generated build-12 inputs, after BODY-DETAILS then HUD-PRESENTATION.
PARENT_SHA256 = {
    "src/game.cpp": "f7c41242f48f0787afdb0f6c4cb7c61a8ec2738914f6121ca2ea10ebf07036b4",
    "src/ds_hud.h": "53d991406a0b69c119d4757be4912e4c73859c54b651005b895c35df74466b06",
    "src/ds_hud.cpp": "3a351bed4abd9b1b74c38dfaaf2c664df75dea1610f62a68a85ee062eee781f5",
    DECODER: "d4d106bf9acfbebb4a9ad287381d23a82c55f7c58a0f117fc969cd4516b1def8",
    UI: "afacc72579e67adef1485c57ede6cb724b169f698e6218f7548f033f2fcedd6d",
}
UNCHANGED_SHA256 = {
    JAVA_DIR + "CoreHudSnapshot.java": "d95a69c314a4419b2baa915ec3d10724135414a5c086001079aa5816954c7070",
    JAVA_DIR + "HudTypeface.java": "093fb83d6b3377b2bae49ca46e68bb9147c8896039c2ef0efcb323dcfcfd2642",
}
WIDGET_BLOBS = {
    "data/json/ui/hunger.json": "0ff6803cd0199ce99bde23efd4f79566ec204efb",
    "data/json/ui/thirst.json": "de6038aef54385d037082567e59c493f808fa395",
    "data/json/ui/sleepiness.json": "c1a8c2f018d4e26937a77f7c199f8bd71fcb8b49",
}
NEEDS_WIDGETS = (
    ("hunger_desc_label", "Hunger"),
    ("thirst_desc_label", "Thirst"),
    ("sleepiness_desc_label", "Rest"),
)
# Stable wire slots 5..13, omitted from the view tree, not removed from capture.
HIDDEN_LABELS = ("Date", "Time", "Place", "Weather", "Lighting", "Wind", "Temperature", "Wield", "Style")
OLD_COUNT = 26
STATUS_COUNT = OLD_COUNT + len(NEEDS_WIDGETS)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def safe_target(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe needs path: {relative}")
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"Symlink needs path: {relative}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Escaping needs path: {relative}")
    return path


def replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"Expected one needs anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_text(path: str, text: str) -> str:
    if path == "src/game.cpp":
        return replace_once(text, '"bp_armor_outer_feet_text" };',
            '"bp_armor_outer_feet_text", ' + ', '.join(json.dumps(wid) for wid, _ in NEEDS_WIDGETS) + ' };')
    if path == "src/ds_hud.h":
        text = replace_once(text, "activity_field_count = 26;", "activity_field_count = 29;")
        text = replace_once(text, "then 26 widget-availability flags.", "then 29 widget-availability flags.")
        return replace_once(text, "movement, 17 previous widgets, then nine body-detail widgets.",
            "movement, 26 previous widgets, then Hunger, Thirst and Rest.")
    if path == "src/ds_hud.cpp":
        # Only the explanatory wire-shape comment changes; transport loops are unchanged.
        return replace_once(text, "Object[] { long[50], byte[27][] }", "Object[] { long[53], byte[30][] }")
    if path == DECODER:
        text = replace_once(text, "copy of 26 game-rendered status widgets, including body details.",
            "copy of 29 game-rendered status widgets, including basic needs.")
        text = replace_once(text, "STATUS_COUNT = 26;", "STATUS_COUNT = 29;")
        return replace_once(text, '"Worn legs", "Worn feet"\n',
            '"Worn legs", "Worn feet",\n        "Hunger", "Thirst", "Rest"\n')
    if path == UI:
        text = replace_once(text, '"CDDA-DS / HUD PRESENTATION"', '"CDDA-DS / NEEDS STATUS"')
        text = replace_once(text, "Object[] { long[29], byte[6][] UTF-8 movement/status text }.",
            "Object[] { long[53], byte[30][] UTF-8 movement/status text }.")
        text = replace_once(text,
            "            // Temporary full-width, wrapping rows; no tabs or smaller fonts.\n"
            "            for (int i = 5; i < activityValues.length; i++) {\n",
            "            // Slots 5..13 (Date through Style) remain on the wire, not in the view tree.\n"
            "            // Retain Bionic Power onward, then append Hunger, Thirst and Rest.\n"
            "            for (int i = 14; i < activityValues.length; i++) {\n")
        text = replace_once(text, '            for (TextView field : activityValues) field.setText("");',
            '            for (TextView field : activityValues) {\n'
            '                if (field != null) field.setText("");\n'
            '            }')
        return replace_once(text,
            "                activityValues[i].setText(activity.label(i));",
            "                if (activityValues[i] != null) activityValues[i].setText(activity.label(i));")
    raise ValueError(f"Unexpected needs target: {path}")


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    pending = {}
    # Validate every input, definition and anchor before the first source write.
    for relative, expected in {**PARENT_SHA256, **UNCHANGED_SHA256}.items():
        raw = safe_target(root, relative).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Needs expects the unchanged build-12 generated source: {relative}")
        if relative in PARENT_SHA256:
            before = raw.decode("utf-8")
            pending[relative] = (before, patch_text(relative, before))
    for relative, expected in WIDGET_BLOBS.items():
        if blob_sha(safe_target(root, relative).read_bytes()) != expected:
            raise ValueError(f"Unexpected needs widget definition: {relative}")
    diff = "".join("".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + path, tofile="b/" + path))
        for path, (before, after) in pending.items())
    report = {
        "experiment": "needs_status", "base_experiment": "hud_presentation",
        "overlay_order": ["BODY-DETAILS.patch", "HUD-PRESENTATION.patch", "NEEDS-STATUS.patch"],
        "game_actions": False, "original_sidebar_retained": True,
        "added_widgets": [wid for wid, _ in NEEDS_WIDGETS],
        "removed_lower_labels": list(HIDDEN_LABELS), "removed_from_capture": False,
        "widget_count": STATUS_COUNT, "displayed_widget_count": 20,
        "wire_shape": {"numeric": 53, "text": 30},
        "input_sha256": dict(PARENT_SHA256), "unchanged_sha256": dict(UNCHANGED_SHA256),
        "widget_git_blobs": dict(WIDGET_BLOBS), "patch_file": "NEEDS-STATUS.patch",
        "paths": {p: hashlib.sha256(after.encode("utf-8")).hexdigest()
                  for p, (_, after) in pending.items()},
    }
    for relative, (_, after) in pending.items():
        (root / relative).write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "NEEDS-STATUS.patch").write_text(diff, encoding="utf-8")
    (output / "NEEDS-STATUS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
