#!/usr/bin/env python3
"""Append body comfort, conditional oxygen and native worn-armor summaries."""
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
import apply_equipment_status as equipment

EXPECTED_BLOBS = dict(equipment.EXPECTED_BLOBS)
# Append only; do not reinterpret the accepted core numbers or 17 widget slots.
BODY_WIDGETS = (
    ("body_temp_desc_label", "Body comfort"),
    ("body_temp_delta_desc_label", "Comfort trend"),
    ("oxygen_graph_classic", "Oxygen"),
    ("bp_armor_outer_head_text", "Worn head"),
    ("bp_armor_outer_torso_text", "Worn torso"),
    ("bp_armor_outer_arms_text", "Worn arms"),
    ("bp_armor_outer_hands_text", "Worn hands"),
    ("bp_armor_outer_legs_text", "Worn legs"),
    ("bp_armor_outer_feet_text", "Worn feet"),
)
WIDGET_IDS = equipment.WIDGET_IDS + tuple(wid for wid, _ in BODY_WIDGETS)
OLD_COUNT = equipment.STATUS_COUNT
STATUS_COUNT = len(WIDGET_IDS)
OXYGEN_INDEX = WIDGET_IDS.index("oxygen_graph_classic")
OXYGEN_LAYOUT = "oxygen_classic_layout"


def patch_text(path: str, text: str) -> str:
    result = equipment.patch_text(path, text)
    if path == "src/game.cpp":
        result = body.replace_once(result, equipment.declaration(equipment.WIDGET_IDS),
                                   equipment.declaration(WIDGET_IDS))
        # Read the game's conditional child selection without calling layout(),
        # which writes shared widget height bookkeeping even on a local copy.
        anchor = '            if( id.is_valid() ) {\n'
        gate = (
            f'                if( i == {OXYGEN_INDEX} ) {{\n'
            f'                    const widget_id gate_id( "{OXYGEN_LAYOUT}" );\n'
            '                    if( !gate_id.is_valid() ) {\n'
            '                        continue;\n'
            '                    }\n'
            '                    widget gate = gate_id.obj();\n'
            '                    const auto children = gate.widgets( true );\n'
            '                    if( children.empty() ) {\n'
            '                        // Native full-oxygen suppression: valid blank, not missing.\n'
            '                        activity.available[i] = true;\n'
            '                        continue;\n'
            '                    }\n'
            '                    if( children.size() != 1 || children.front() != id ) {\n'
            '                        // Do not invent output for an unsupported custom layout.\n'
            '                        continue;\n'
            '                    }\n'
            '                }\n'
        )
        result = body.replace_once(result, anchor, anchor + gate)
    return result


def render_templates(template_root: Path | None = None) -> dict[str, str]:
    """Derive only this experiment; preserve accepted templates and transports."""
    rendered = equipment.render_templates(template_root)
    h = body.replace_once(rendered["src/ds_hud.h"],
        f"activity_field_count = {OLD_COUNT};", f"activity_field_count = {STATUS_COUNT};")
    h = body.replace_once(h,
        "// Original 24 numeric fields, then seventeen widget-availability flags.",
        "// Original 24 numeric fields, then 26 widget-availability flags.")
    h = body.replace_once(h,
        "// UTF-8 arrays: movement, five activity, seven environment, five equipment/status fields.",
        "// UTF-8 arrays: movement, 17 previous widgets, then nine body-detail widgets.")
    rendered["src/ds_hud.h"] = h
    rendered["src/ds_hud.cpp"] = body.replace_once(rendered["src/ds_hud.cpp"],
        "Object[] { long[41], byte[18][] }", "Object[] { long[50], byte[27][] }")
    path = activity.JAVA_DIR + "ActivityHudSnapshot.java"
    decoder = body.replace_once(rendered[path],
        "copy of seventeen game-rendered activity/environment/equipment widgets.",
        "copy of 26 game-rendered status widgets, including body details.")
    decoder = body.replace_once(decoder, f"STATUS_COUNT = {OLD_COUNT};",
                                         f"STATUS_COUNT = {STATUS_COUNT};")
    decoder = body.replace_once(decoder, "    static final int TRANSITION = 2;",
        "    static final int TRANSITION = 2;\n"
        f"    static final int OXYGEN = {OXYGEN_INDEX};")
    previous_labels = ', '.join(json.dumps(label) for _, label in equipment.EQUIPMENT_WIDGETS)
    decoder = body.replace_once(decoder, previous_labels, previous_labels + ',\n        '
        + ', '.join(json.dumps(label) for _, label in BODY_WIDGETS))
    rendered[path] = decoder
    path = activity.JAVA_DIR + "DualScreenHud.java"
    ui = body.replace_once(rendered[path], '"CDDA-DS / EQUIPMENT STATUS"',
                                          '"CDDA-DS / BODY DETAILS"')
    ui = body.replace_once(ui,
        '                activityValues[i] = text("", 16);\n'
        '                activityStatus.addView(activityValues[i]);',
        '                activityValues[i] = text("", 16);\n'
        '                if (i == ActivityHudSnapshot.OXYGEN) {\n'
        '                    activityValues[i].setTypeface(Typeface.MONOSPACE);\n'
        '                }\n'
        '                activityStatus.addView(activityValues[i]);')
    rendered[path] = ui
    return rendered


def apply(root: Path, output: Path, template_root: Path | None = None) -> dict:
    root = root.resolve()
    pending: dict[str, tuple[str, str]] = {}
    # Plan and validate everything before modifying any game-source file.
    for relative, expected in EXPECTED_BLOBS.items():
        data = core.safe_target(root, relative).read_bytes()
        if body.blob_sha(data) != expected:
            raise ValueError(f"Body details expects pinned original source: {relative}")
        before = data.decode("utf-8")
        pending[relative] = (before, patch_text(relative, before))
    for relative, after in render_templates(template_root).items():
        if core.safe_target(root, relative).exists():
            raise ValueError(f"Body details destination already exists: {relative}")
        pending[relative] = ("", after)
    diff = "".join("".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + path if before else "/dev/null", tofile="b/" + path))
        for path, (before, after) in pending.items())
    report = {
        "experiment": "body_details",
        "architecture": "same APK; copied-state mailbox; Android Presentation",
        "game_actions": False,
        "original_sidebar_retained": True,
        "widget_ids": list(WIDGET_IDS),
        "conditional_widget_layouts": {"oxygen_graph_classic": OXYGEN_LAYOUT},
        "derived_from_template_blobs": dict(environment.TEMPLATE_BLOBS),
        "patch_file": "BODY-DETAILS.patch",
        "paths": {path: hashlib.sha256(after.encode("utf-8")).hexdigest()
                  for path, (_, after) in pending.items()},
    }
    for relative, (_, after) in pending.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "BODY-DETAILS.patch").write_text(diff, encoding="utf-8")
    (output / "BODY-DETAILS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
