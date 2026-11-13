#!/usr/bin/env python3
"""Apply the approved label/stamina/reading-order polish AFTER hud_refinement."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

JAVA_DIR = "android/app/src/main/java/com/cleverraven/cataclysmdda/"
UI = JAVA_DIR + "DualScreenHud.java"
PARENT_UI_SHA256 = "c2ed2ac1359a7c45dcc15b20fd89ceee30f7a9d62aaefad2b58702061609b137"
UNCHANGED_SHA256 = {
    "src/ds_hud.h": "8c47d4b841ca6ebe8ce27855b600ac56f6a200d6d8868197e87a8b0a02d75b56",
    "src/ds_hud.cpp": "f1413b8d07c549fbe57fe9da81c7bb0d44f40f6f84c8c2ecc39d128803697f5d",
    JAVA_DIR + "CoreHudSnapshot.java": "d95a69c314a4419b2baa915ec3d10724135414a5c086001079aa5816954c7070",
    JAVA_DIR + "ActivityHudSnapshot.java": "560cb0c6edfa2c946b7e74e3a705af844b55a4ddaa686882df648032c395edf1",
    JAVA_DIR + "HudTypeface.java": "093fb83d6b3377b2bae49ca46e68bb9147c8896039c2ef0efcb323dcfcfd2642",
}
WIDGET_BLOBS = {"data/json/move_modes.json": "3d192121f0f26c7c8ab3efee9e3c8367ddbbfe98"}
OVERLAY_ORDER = ["BODY-DETAILS.patch", "HUD-PRESENTATION.patch", "NEEDS-STATUS.patch",
                 "HUD-LAYOUT.patch", "HUD-REFINEMENT.patch", "HUD-POLISH.patch"]
LABEL_ALIGNMENT = "                bodyLabels[i].setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);\n"
OLD_MOVEMENT = '''            pair(details, widget(19), widget(15), padding,
                "Oxygen: Unavailable", "Sound: -2147483648");
            movement = text("", 16);
            full(details, movement);
'''
NEW_MOVEMENT = '''            movement = text("", 16);
            pair(details, movement, widget(15), padding,
                "Movement mode: crouch (C)", "Sound: -2147483648");
'''
OXYGEN_ANCHOR = "            full(details, widget(18)); // Comfort trend.\n"
OXYGEN_ROW = "            full(details, widget(19)); // Oxygen: retained, below comfort and above power.\n"
OLD_STAMINA = '''            value.setText(String.format(Locale.ROOT, "Stamina: %.1f%%  (%d / %d)",
                                       percent, state.current, state.maximum));'''
NEW_STAMINA = '''            value.setText(String.format(Locale.ROOT, "Stamina: %.1f%%", percent));'''


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def safe_target(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe polish path: {relative}")
    path = root
    for part in rel.parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"Symlink polish path: {relative}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Escaping polish path: {relative}")
    return path


def replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"Expected one polish anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_ui(text: str) -> str:
    text = replace_once(text, '"CDDA-DS / HUD REFINEMENT"', '"CDDA-DS / HUD POLISH"')
    text = replace_once(text, LABEL_ALIGNMENT, "")
    text = replace_once(text, OLD_MOVEMENT, NEW_MOVEMENT)
    text = replace_once(text, OXYGEN_ANCHOR, OXYGEN_ANCHOR + OXYGEN_ROW)
    return replace_once(text, OLD_STAMINA, NEW_STAMINA)


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    source = safe_target(root, UI)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_UI_SHA256:
        raise ValueError("Polish expects the unchanged build-15 hud_refinement UI")
    for relative, expected in UNCHANGED_SHA256.items():
        if hashlib.sha256(safe_target(root, relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Unexpected build-15 polish dependency: {relative}")
    for relative, expected in WIDGET_BLOBS.items():
        if blob_sha(safe_target(root, relative).read_bytes()) != expected:
            raise ValueError(f"Unexpected movement definition: {relative}")
    before = raw.decode("utf-8")
    after = patch_ui(before)
    diff = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                      fromfile="a/" + UI, tofile="b/" + UI))
    report = {
        "experiment": "hud_polish", "base_experiment": "hud_refinement", "presentation_only": True,
        "overlay_order": OVERLAY_ORDER, "game_actions": False, "original_sidebar_retained": True,
        "displayed_widget_count": 20, "health_label_alignment": "original left alignment; no literal spaces",
        "health_spacing_deferred": "Different trailing whitespace is accepted temporarily; revisit later.",
        "stamina_display": "one-decimal percentage and unchanged full-width bar; raw values retained internally",
        "movement_pair": ["Movement mode", "Sound"],
        "movement_width_probes": ["Movement mode: crouch (C)", "Sound: -2147483648"],
        "oxygen_position": "full-width row after Comfort trend and before Bionic Power",
        "needs_pair": ["Thirst", "Hunger"], "font_sizes_unchanged": True,
        "pair_fallback": "Unchanged width-only StablePairRow; no value-dependent rearrangement.",
        "input_ui_sha256": PARENT_UI_SHA256, "unchanged_sha256": dict(UNCHANGED_SHA256),
        "widget_git_blobs": dict(WIDGET_BLOBS), "patch_file": "HUD-POLISH.patch",
        "paths": {UI: hashlib.sha256(after.encode("utf-8")).hexdigest()},
    }
    # All input identities and edit anchors are checked before the source write.
    source.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "HUD-POLISH.patch").write_text(diff, encoding="utf-8")
    (output / "HUD-POLISH.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
