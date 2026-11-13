#!/usr/bin/env python3
"""Apply optional activity/weariness/pain widgets beside the accepted core HUD."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

import apply_body_status as body
import apply_core_status as core

EXPECTED_BLOBS = dict(core.EXPECTED_BLOBS)
JAVA_DIR = "android/app/src/main/java/com/cleverraven/cataclysmdda/"
# Reuse the accepted core decoder verbatim. Older experiments are never modified.
TEMPLATES = {
    "activity-status/ds_hud.h": "src/ds_hud.h",
    "activity-status/ds_hud.cpp": "src/ds_hud.cpp",
    "activity-status/DualScreenHud.java": JAVA_DIR + "DualScreenHud.java",
    "core-status/CoreHudSnapshot.java": JAVA_DIR + "CoreHudSnapshot.java",
    "activity-status/ActivityHudSnapshot.java": JAVA_DIR + "ActivityHudSnapshot.java",
}
WIDGET_IDS = (
    "weariness_desc", "activity_desc", "weariness_transition_graph",
    "weary_malus_desc", "pain_desc_label",
)


def patch_text(path: str, text: str) -> str:
    result = core.patch_text(path, text)
    if path == "src/game.cpp":
        result = body.replace_once(result, '#include "ds_hud.h"\n',
                                   '#include "ds_hud.h"\n#include "widget.h"\n')
        ids = ", ".join('"' + value + '"' for value in WIDGET_IDS)
        capture = (
            '    ds_hud::activity_status activity;\n'
            f'    const char *const widget_ids[] = {{ {ids} }};\n'
            '    static_assert( sizeof( widget_ids ) / sizeof( widget_ids[0] ) ==\n'
            '                   ds_hud::activity_field_count, "Activity widget order/size" );\n'
            '    if( ds_hud::read().active ) {\n'
            '        for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {\n'
            '            const widget_id id( widget_ids[i] );\n'
            '            if( id.is_valid() ) {\n'
            '                // A local copy keeps display bookkeeping off the shared widget.\n'
            '                // Use the game\'s descriptions/graph, not hidden raw pain or a new formula.\n'
            '                widget view = id.obj();\n'
            '                activity.text[i] = remove_color_tags( view.show( u, 80 ) );\n'
            '                activity.available[i] = true;\n'
            '            }\n'
            '        }\n'
            '    }\n'
            '    ds_hud::publish( u.get_stamina(), u.get_stamina_max(), health, core, activity );\n'
        )
        result = body.replace_once(result,
            '    ds_hud::publish( u.get_stamina(), u.get_stamina_max(), health, core );\n', capture)
    return result


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    pending: dict[str, tuple[str, str]] = {}
    # Validate all hashes, anchors and destinations before the first source write.
    for relative, expected in EXPECTED_BLOBS.items():
        data = core.safe_target(root, relative).read_bytes()
        if body.blob_sha(data) != expected:
            raise ValueError(f"Activity status expects pinned original source: {relative}")
        before = data.decode("utf-8")
        pending[relative] = (before, patch_text(relative, before))
    for template, relative in TEMPLATES.items():
        if core.safe_target(root, relative).exists():
            raise ValueError(f"Activity status destination already exists: {relative}")
        pending[relative] = ("", (Path(__file__).resolve().parent / template).read_text(encoding="utf-8"))
    diff = "".join("".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + path if before else "/dev/null", tofile="b/" + path))
        for path, (before, after) in pending.items())
    report = {
        "experiment": "activity_status",
        "architecture": "same APK; copied-state mailbox; Android Presentation",
        "game_actions": False,
        "original_sidebar_retained": True,
        "widget_ids": list(WIDGET_IDS),
        "patch_file": "ACTIVITY-STATUS.patch",
        "paths": {path: hashlib.sha256(after.encode("utf-8")).hexdigest()
                  for path, (_, after) in pending.items()},
    }
    for relative, (_, after) in pending.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "ACTIVITY-STATUS.patch").write_text(diff, encoding="utf-8")
    (output / "ACTIVITY-STATUS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
