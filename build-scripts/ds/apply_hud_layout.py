#!/usr/bin/env python3
"""Apply the approved mixed-width layout AFTER the unchanged needs_status stages."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

JAVA_DIR = "android/app/src/main/java/com/cleverraven/cataclysmdda/"
UI = JAVA_DIR + "DualScreenHud.java"
PARENT_UI_SHA256 = "e3cdd3a342fc7e7cecc558995e3b5533e2f7785b724518c637f892147ada0660"
UNCHANGED_SHA256 = {
    "src/ds_hud.h": "8c47d4b841ca6ebe8ce27855b600ac56f6a200d6d8868197e87a8b0a02d75b56",
    "src/ds_hud.cpp": "f1413b8d07c549fbe57fe9da81c7bb0d44f40f6f84c8c2ecc39d128803697f5d",
    JAVA_DIR + "CoreHudSnapshot.java": "d95a69c314a4419b2baa915ec3d10724135414a5c086001079aa5816954c7070",
    JAVA_DIR + "ActivityHudSnapshot.java": "560cb0c6edfa2c946b7e74e3a705af844b55a4ddaa686882df648032c395edf1",
    JAVA_DIR + "HudTypeface.java": "093fb83d6b3377b2bae49ca46e68bb9147c8896039c2ef0efcb323dcfcfd2642",
}

# The arrays and snapshot indices are unchanged. Only their view arrangement changes.
LAYOUT = '''            body = new LinearLayout(getContext());
            body.setOrientation(LinearLayout.VERTICAL);
            String[] labels = {"Head", "Torso", "Left arm", "Right arm", "Left leg", "Right leg"};
            TextView[] bodyLabels = new TextView[labels.length];
            int labelWidth = 0;
            for (int i = 0; i < labels.length; i++) {
                bodyLabels[i] = text(labels[i], 16);
                labelWidth = Math.max(labelWidth, textWidth(bodyLabels[i], labels[i]));
            }
            int barGap = Math.round(4 * getContext().getResources().getDisplayMetrics().density);
            int minimumBar = Math.round(64 * getContext().getResources().getDisplayMetrics().density);
            for (int i = 0; i < labels.length; i += 2) {
                LinearLayout[] cells = new LinearLayout[2];
                for (int column = 0; column < 2; column++) {
                    int part = i + column;
                    cells[column] = new LinearLayout(getContext());
                    cells[column].setGravity(Gravity.CENTER_VERTICAL);
                    cells[column].addView(bodyLabels[part], new LinearLayout.LayoutParams(
                        labelWidth, LinearLayout.LayoutParams.WRAP_CONTENT));
                    healthBars[part] = new ProgressBar(getContext(), null,
                        android.R.attr.progressBarStyleHorizontal);
                    healthBars[part].setMax(1000);
                    LinearLayout.LayoutParams track = new LinearLayout.LayoutParams(0,
                        LinearLayout.LayoutParams.WRAP_CONTENT, 1);
                    track.leftMargin = barGap;
                    cells[column].addView(healthBars[part], track);
                }
                int cellMinimum = labelWidth + barGap + minimumBar;
                body.addView(new StablePairRow(getContext(), cells[0], cells[1], padding,
                    cellMinimum, cellMinimum));
            }
            body.setVisibility(View.GONE);
            layout.addView(body);
            details = new LinearLayout(getContext());
            details.setOrientation(LinearLayout.VERTICAL);
            // Immediate condition. Native slot numbers retain their build-13 meanings.
            full(details, widget(4)); // Pain: descriptive, full width.
            pair(details, widget(19), widget(15), padding,
                "Oxygen: Unavailable", "Sound: -2147483648");
            movement = text("", 16);
            full(details, movement);
            // Speed/focus first, then the two established attribute pairs.
            int[][] coreOrder = {{4, 5}, {0, 1}, {2, 3}};
            String[] coreProbes = {"Strength: -999", "Dexterity: -999", "Intelligence: -999",
                "Perception: -999", "Speed: -9999", "Focus: -999"};
            for (int[] fields : coreOrder) {
                for (int field : fields) coreValues[field] = text("", 16);
                pair(details, coreValues[fields[0]], coreValues[fields[1]], padding,
                    coreProbes[fields[0]], coreProbes[fields[1]]);
            }
            // Needs are ahead of equipment; longer hunger/thirst descriptions keep full width.
            full(details, widget(26));
            full(details, widget(27));
            pair(details, widget(28), widget(16), padding,
                "Rest: Unavailable", "Mood: Unavailable");
            // Preserve the familiar exertion pairs, not raw counters or new interpretations.
            pair(details, widget(0), widget(1), padding,
                "Weariness: Extremely weary", "Activity: Unavailable");
            pair(details, widget(2), widget(3), padding,
                "Transition: Unavailable", "Weary Malus: Unavailable");
            full(details, widget(17)); // Body comfort, NOT environmental Temperature.
            full(details, widget(18)); // Comfort trend.
            full(details, widget(14)); // Bionic Power retains room for formatted units.
            for (int i = 20; i <= 25; i++) full(details, widget(i)); // All six worn summaries.
            // Hidden slots 5..13 stay absent, not allocated as empty spacer rows.
            details.setVisibility(View.GONE);
            layout.addView(details);
'''

HELPERS = '''        private TextView widget(int field) {
            if (activityValues[field] != null) throw new IllegalStateException("Duplicate HUD field");
            activityValues[field] = text("", 16);
            return activityValues[field];
        }

        private static void full(LinearLayout parent, View child) {
            parent.addView(child, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        }

        private static int textWidth(TextView view, String probe) {
            // Measure with the actual resolved face and unchanged text size. Two pixels
            // of rounding reserve; no font-size changes, single-line limits or ellipses.
            return (int) Math.ceil(view.getPaint().measureText(probe)) + 2
                + view.getPaddingLeft() + view.getPaddingRight();
        }

        private void pair(LinearLayout parent, TextView left, TextView right, int gap,
                String leftProbe, String rightProbe) {
            full(parent, new StablePairRow(getContext(), left, right, gap,
                textWidth(left, leftProbe), textWidth(right, rightProbe)));
        }

        /** Width-only fallback: changing game values never rearranges this row. */
        private static final class StablePairRow extends LinearLayout {
            private final View left;
            private final View right;
            private final int gap;
            private final int pairWidth;
            private int chosenOrientation = -1;

            StablePairRow(Context context, View left, View right, int gap,
                    int leftMinimum, int rightMinimum) {
                super(context);
                this.left = left;
                this.right = right;
                this.gap = gap;
                pairWidth = 2 * Math.max(leftMinimum, rightMinimum) + gap;
                setFocusable(false);
                setDescendantFocusability(ViewGroup.FOCUS_BLOCK_DESCENDANTS);
                setGravity(Gravity.CENTER_VERTICAL);
                addView(left);
                addView(right);
                arrange(HORIZONTAL);
            }

            private void arrange(int orientation) {
                if (chosenOrientation == orientation) return;
                chosenOrientation = orientation;
                setOrientation(orientation);
                boolean paired = orientation == HORIZONTAL;
                LinearLayout.LayoutParams a = new LinearLayout.LayoutParams(
                    paired ? 0 : LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT, paired ? 1 : 0);
                LinearLayout.LayoutParams b = new LinearLayout.LayoutParams(
                    paired ? 0 : LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT, paired ? 1 : 0);
                a.rightMargin = paired ? gap : 0;
                left.setLayoutParams(a);
                right.setLayoutParams(b);
            }

            @Override protected void onMeasure(int widthSpec, int heightSpec) {
                int available = View.MeasureSpec.getSize(widthSpec) - getPaddingLeft() - getPaddingRight();
                boolean bounded = View.MeasureSpec.getMode(widthSpec) != View.MeasureSpec.UNSPECIFIED;
                arrange(bounded && available < pairWidth ? VERTICAL : HORIZONTAL);
                super.onMeasure(widthSpec, heightSpec);
            }
        }

'''


def safe_target(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe layout path: {relative}")
    path = root
    for part in rel.parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"Symlink layout path: {relative}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Escaping layout path: {relative}")
    return path


def replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"Expected one layout anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_ui(text: str) -> str:
    text = replace_once(text, '"CDDA-DS / NEEDS STATUS"', '"CDDA-DS / HUD LAYOUT"')
    text = replace_once(text, "        private LinearLayout core;\n", "        private LinearLayout details;\n")
    text = replace_once(text, "        private LinearLayout activityStatus;\n", "")
    start = "            body = new LinearLayout(getContext());\n"
    end = "            layout.addView(status);\n"
    if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
        raise ValueError("Expected one ordered body/details layout block")
    text = text[:text.index(start)] + LAYOUT + text[text.index(end):]
    text = replace_once(text, "        private TextView text(String content, int size) {\n",
                        HELPERS + "        private TextView text(String content, int size) {\n")
    for state in ("GONE", "VISIBLE"):
        text = replace_once(text,
            f"            core.setVisibility(View.{state});\n            activityStatus.setVisibility(View.{state});\n",
            f"            details.setVisibility(View.{state});\n")
    return text


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    source = safe_target(root, UI)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_UI_SHA256:
        raise ValueError("Layout expects the unchanged build-13 needs_status UI")
    for relative, expected in UNCHANGED_SHA256.items():
        if hashlib.sha256(safe_target(root, relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Unexpected build-13 layout dependency: {relative}")
    before = raw.decode("utf-8")
    after = patch_ui(before)
    diff = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                      fromfile="a/" + UI, tofile="b/" + UI))
    report = {
        "experiment": "hud_layout", "base_experiment": "needs_status", "presentation_only": True,
        "overlay_order": ["BODY-DETAILS.patch", "HUD-PRESENTATION.patch", "NEEDS-STATUS.patch", "HUD-LAYOUT.patch"],
        "game_actions": False, "original_sidebar_retained": True, "displayed_widget_count": 20,
        "health_pairs": [["Head", "Torso"], ["Left arm", "Right arm"], ["Left leg", "Right leg"]],
        "stamina_full_width": True, "font_sizes_unchanged": True,
        "pair_fallback": "Fixed-probe measured widths, not changing game values; stack on narrow viewports.",
        "input_ui_sha256": PARENT_UI_SHA256, "unchanged_sha256": dict(UNCHANGED_SHA256),
        "patch_file": "HUD-LAYOUT.patch", "paths": {UI: hashlib.sha256(after.encode("utf-8")).hexdigest()},
    }
    # All source guards/anchors are checked before the single production source write.
    source.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "HUD-LAYOUT.patch").write_text(diff, encoding="utf-8")
    (output / "HUD-LAYOUT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
