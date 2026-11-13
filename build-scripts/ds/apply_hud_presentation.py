#!/usr/bin/env python3
"""Apply black backgrounds and bundled game fonts AFTER the body_details overlay."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

JAVA_DIR = "android/app/src/main/java/com/cleverraven/cataclysmdda/"
JAVA = JAVA_DIR + "DualScreenHud.java"
HELPER = JAVA_DIR + "HudTypeface.java"
PARENT_UI_SHA256 = "ba8a2440d5b5a76748c52b8e26e06f7ceddf61621bdea777c4eec84381c4c313"
FONT_BLOBS = {
    "data/font/Terminus.ttf": "9e3af633ccbb154ea18d9abf737f22f8cb920c7a",
    "data/font/unifont.ttf": "605357ee9e1e876ffdd8bca1c976e4deafdf9e23",
    "data/fontdata.json": "d86d5291b4cf1d4f0ff87a2ee5370b11f6b76b7f",
}
TEMPLATE = Path(__file__).resolve().parent / "hud-presentation/HudTypeface.java"
# Updated only with an intentional, reviewed change to this helper.
TEMPLATE_SHA256 = '093fb83d6b3377b2bae49ca46e68bb9147c8896039c2ef0efcb323dcfcfd2642'


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def safe_target(root: Path, relative: str) -> Path:
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError(f"Unsafe presentation path: {relative}")
    return path


def replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"Expected one presentation anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_ui(text: str) -> str:
    text = replace_once(text, "import android.graphics.Typeface;\n",
                             "import android.graphics.drawable.ColorDrawable;\n")
    text = replace_once(text, "        private TextView value;\n",
                             "        private HudTypeface hudFont;\n        private TextView value;\n")
    text = replace_once(text,
        "                window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);\n",
        "                window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);\n"
        "                window.setBackgroundDrawable(new ColorDrawable(Color.BLACK));\n")
    text = replace_once(text, "            super.onCreate(state);\n",
        "            super.onCreate(state);\n"
        "            hudFont = HudTypeface.load(getContext());\n"
        "            Log.i(TAG, \"Lower HUD font: \" + hudFont.description);\n")
    text = replace_once(text, "layout.setBackgroundColor(Color.rgb(18, 22, 27));",
                             "layout.setBackgroundColor(Color.BLACK);")
    text = replace_once(text, '"CDDA-DS / BODY DETAILS"', '"CDDA-DS / HUD PRESENTATION"')
    # Remove BOTH per-widget overrides: every readout uses the single resolved face.
    text = replace_once(text,
        "                    if (field == ActivityHudSnapshot.TRANSITION) {\n"
        "                        activityValues[field].setTypeface(Typeface.MONOSPACE);\n"
        "                    }\n", "")
    text = replace_once(text,
        "                if (i == ActivityHudSnapshot.OXYGEN) {\n"
        "                    activityValues[i].setTypeface(Typeface.MONOSPACE);\n"
        "                }\n", "")
    text = replace_once(text, "            scroll.setFillViewport(true);\n",
        "            scroll.setFillViewport(true);\n"
        "            scroll.setBackgroundColor(Color.BLACK);\n")
    text = replace_once(text, "            view.setTextSize(size);\n",
        "            view.setTextSize(size);\n"
        "            view.setTypeface(hudFont.typeface);\n"
        "            view.setLetterSpacing(0.0f);\n"
        "            view.setFontFeatureSettings(\"'liga' 0, 'clig' 0, 'kern' 0\");\n")
    text = replace_once(text,
        'status = text("Read-only. The original sidebar remains above.", 12);',
        'status = text("Read-only. The original sidebar remains above.\\nFont: "\n'
        '                + hudFont.description, 12);')
    text = replace_once(text,
        'status.setText("Read-only diagnostic; original game interface is unchanged.");',
        'status.setText("Read-only diagnostic; original game interface is unchanged.\\nFont: "\n'
        '                + hudFont.description);')
    text = replace_once(text,
        '                state.sequence, state.ageMs / 1000.0));',
        '                state.sequence, state.ageMs / 1000.0) + "\\nFont: " + hudFont.description);')
    return text


def verify_font_data(reader) -> dict[str, str]:
    observed = {}
    for relative, expected in FONT_BLOBS.items():
        observed[relative] = blob_sha(reader(relative))
        if observed[relative] != expected:
            raise ValueError(f"Unexpected bundled font/config: {relative}")
    return observed


def verify_apk(apk: Path, output: Path) -> dict:
    """Verify the actual packaged assets, not just repository font availability."""
    with ZipFile(apk) as archive:
        observed = verify_font_data(lambda path: archive.read("assets/" + path))
    report = {"experiment": "hud_presentation", "apk": apk.name,
              "asset_git_blobs": observed,
              "note": "Byte identity only; not Android font rendering or device acceptance."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def apply(root: Path, output: Path, template: Path | None = None) -> dict:
    root = root.resolve()
    source = safe_target(root, JAVA)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_UI_SHA256:
        raise ValueError("Presentation expects the unchanged build-11 body_details UI")
    destination = safe_target(root, HELPER)
    if destination.exists():
        raise ValueError("Presentation helper destination already exists")
    font_blobs = verify_font_data(lambda path: safe_target(root, path).read_bytes())
    helper = (template or TEMPLATE).read_bytes()
    if hashlib.sha256(helper).hexdigest() != TEMPLATE_SHA256:
        raise ValueError("Unexpected presentation helper template")
    before = raw.decode("utf-8")
    after = patch_ui(before)
    pending = {JAVA: (before, after), HELPER: ("", helper.decode("utf-8"))}
    diff = "".join("".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile="a/" + path if old else "/dev/null", tofile="b/" + path))
        for path, (old, new) in pending.items())
    report = {
        "experiment": "hud_presentation", "base_experiment": "body_details",
        "base_overlay_report": "BODY-DETAILS.json",
        "presentation_only": True, "game_actions": False,
        "original_sidebar_retained": True, "background": "#000000",
        "font_asset_git_blobs": font_blobs, "helper_sha256": TEMPLATE_SHA256,
        "input_ui_sha256": PARENT_UI_SHA256,
        "patch_file": "HUD-PRESENTATION.patch",
        "note": "Apply after BODY-DETAILS.patch. This report supersedes its UI hash only.",
        "paths": {p: hashlib.sha256(new.encode("utf-8")).hexdigest()
                  for p, (_, new) in pending.items()},
    }
    # All validation is complete before either Android source is written.
    for path, (_, new) in pending.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "HUD-PRESENTATION.patch").write_text(diff, encoding="utf-8")
    (output / "HUD-PRESENTATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-apk", type=Path)
    args = parser.parse_args()
    result = verify_apk(args.verify_apk, args.output) if args.verify_apk else apply(args.root, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
