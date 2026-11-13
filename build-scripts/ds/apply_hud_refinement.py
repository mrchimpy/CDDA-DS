#!/usr/bin/env python3
"""Right-align health labels and pair Thirst/Hunger AFTER the hud_layout overlay."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

JAVA_DIR = "android/app/src/main/java/com/cleverraven/cataclysmdda/"
UI = JAVA_DIR + "DualScreenHud.java"
PARENT_UI_SHA256 = "7aae6ef8f6778bf00d8dd2ea50d9bd5111bfa6a45965475c496b1b2ff479e80a"
UNCHANGED_SHA256 = {
    "src/ds_hud.h": "8c47d4b841ca6ebe8ce27855b600ac56f6a200d6d8868197e87a8b0a02d75b56",
    "src/ds_hud.cpp": "f1413b8d07c549fbe57fe9da81c7bb0d44f40f6f84c8c2ecc39d128803697f5d",
    JAVA_DIR + "CoreHudSnapshot.java": "d95a69c314a4419b2baa915ec3d10724135414a5c086001079aa5816954c7070",
    JAVA_DIR + "ActivityHudSnapshot.java": "560cb0c6edfa2c946b7e74e3a705af844b55a4ddaa686882df648032c395edf1",
    JAVA_DIR + "HudTypeface.java": "093fb83d6b3377b2bae49ca46e68bb9147c8896039c2ef0efcb323dcfcfd2642",
}
WIDGET_BLOBS = {
    "data/json/ui/hunger.json": "0ff6803cd0199ce99bde23efd4f79566ec204efb",
    "data/json/ui/thirst.json": "de6038aef54385d037082567e59c493f808fa395",
}
OLD_NEEDS = '''            // Needs are ahead of equipment; longer hunger/thirst descriptions keep full width.
            full(details, widget(26));
            full(details, widget(27));
'''
NEW_NEEDS = '''            // Fixed probes cover the pinned English descriptions, blanks and Unavailable.
            // Thirst left, Hunger right; never rearrange in response to changing values.
            pair(details, widget(27), widget(26), padding,
                "Thirst: Very thirsty", "Hunger: Near starving");
'''
LABEL_ANCHOR = '                bodyLabels[i] = text(labels[i], 16);\n'
LABEL_ALIGNMENT = '                bodyLabels[i].setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);\n'


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def safe_target(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe refinement path: {relative}")
    path = root
    for part in rel.parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"Symlink refinement path: {relative}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Escaping refinement path: {relative}")
    return path


def replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"Expected one refinement anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_ui(text: str) -> str:
    text = replace_once(text, '"CDDA-DS / HUD LAYOUT"', '"CDDA-DS / HUD REFINEMENT"')
    text = replace_once(text, LABEL_ANCHOR, LABEL_ANCHOR + LABEL_ALIGNMENT)
    return replace_once(text, OLD_NEEDS, NEW_NEEDS)


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    source = safe_target(root, UI)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_UI_SHA256:
        raise ValueError("Refinement expects the unchanged build-14 hud_layout UI")
    for relative, expected in UNCHANGED_SHA256.items():
        if hashlib.sha256(safe_target(root, relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Unexpected build-14 refinement dependency: {relative}")
    for relative, expected in WIDGET_BLOBS.items():
        if blob_sha(safe_target(root, relative).read_bytes()) != expected:
            raise ValueError(f"Unexpected refinement needs definition: {relative}")
    before = raw.decode("utf-8")
    after = patch_ui(before)
    diff = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                      fromfile="a/" + UI, tofile="b/" + UI))
    report = {
        "experiment": "hud_refinement", "base_experiment": "hud_layout", "presentation_only": True,
        "overlay_order": ["BODY-DETAILS.patch", "HUD-PRESENTATION.patch", "NEEDS-STATUS.patch",
                          "HUD-LAYOUT.patch", "HUD-REFINEMENT.patch"],
        "game_actions": False, "original_sidebar_retained": True, "displayed_widget_count": 20,
        "health_label_alignment": "right; fixed label widths and bar geometry unchanged",
        "needs_pair": ["Thirst", "Hunger"],
        "needs_width_probes": ["Thirst: Very thirsty", "Hunger: Near starving"],
        "stamina_full_width": True, "font_sizes_unchanged": True,
        "pair_fallback": "Unchanged width-only StablePairRow; never depends on current values.",
        "input_ui_sha256": PARENT_UI_SHA256, "unchanged_sha256": dict(UNCHANGED_SHA256),
        "widget_git_blobs": dict(WIDGET_BLOBS), "patch_file": "HUD-REFINEMENT.patch",
        "paths": {UI: hashlib.sha256(after.encode("utf-8")).hexdigest()},
    }
    # Validate all inputs and anchors before the single production source write.
    source.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "HUD-REFINEMENT.patch").write_text(diff, encoding="utf-8")
    (output / "HUD-REFINEMENT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
