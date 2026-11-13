# Experiment 4: activity, weariness and pain

Status: build 8 passed Android CI/package checks and all five owner-reported Thor
functional acceptance categories. See [Checkpoint 6](CHECKPOINT_6.md) for the exact
tested source, observations, layout capacity note and open creature-legend decision.
This accepts the bounded read-only increment, not full Milestone 1 completion.

Builds on accepted build 7 (`core_status`, source
`8382d31744c2c138afd5130f3f7862e9322f01d9`). The corrected movement observation in
Checkpoint 5 is retained: both displays wait for the sidebar's next-turn refresh;
there is no established lower-only timing defect and no timing fix in this change.

## Added readouts and source semantics

| Readout | Game widget used |
|---|---|
| Weariness | `weariness_desc` |
| Activity | `activity_desc` |
| Transition | `weariness_transition_graph` |
| Weary Malus | `weary_malus_desc` |
| Pain | `pain_desc_label` |

These are the pinned game's named widgets, not independently reimplemented thresholds
or formulas. During the existing game-thread sidebar hook, valid definitions are
copied locally and rendered with `widget::show(u, 80)`. Color markup is removed from
the copied result; text and graph glyphs travel as UTF-8 to the lower display.
The five new widgets are evaluated only while a real game session is active.

The transition readout retains the game's five-character symbolic meter, shown in
a monospace font. It is NOT relabeled as a recovery or progress percentage. Activity
uses the JSON widget's conditions, not an assumed second mapping of activity levels.
Pain uses the descriptive widget; the companion does not independently read and
expose raw perceived-pain numbers. Any text/numbers that the widget itself legitimately
returns are preserved. Blank game output is shown as a dash; it is not asserted to be
numeric zero or necessarily "No pain". A missing widget is separately shown as
`Unavailable`, not confused with a valid blank reading.

This covers the five named standard widgets. It does not discover every selected
sidebar layout, reproduce arbitrary custom widgets, or implement all upstream colors.
Existing health bars, stamina, current attributes, speed, focus and movement remain.

Pinned source references:
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/data/json/ui/weariness.json
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/data/json/ui/activity.json
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/data/json/ui/pain.json
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/widget.h
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/widget.cpp
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/display.cpp

## Build and installation

PR #3 has merged and build 8 already exists. No rebuild is required merely to record
its acceptance. Tested source `346e0bdc3a49efd83ff329a02cc55bef948a8285` is preserved
as `checkpoint/activity-status-8`. For a subsequent requested activity-status build,
start a NEW manual **CDDA-DS Android test** run:

| Setting | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `activity_status` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

The default remains `baseline`. The workflow remains manual, read-only in repository
permissions, and gated to `ds-dev`. Existing `stamina_probe`, `body_status` and
`core_status` scripts/templates are unchanged. No new permissions, separate app,
Shizuku integration, input remapping, or signing changes are introduced.

Continue the owner's fresh-install development process after backing up wanted test
data. Uninstall only CDDA-DS (test), keep official CDDA and signing secrets unchanged.
In-place update/data migration remains unresolved, not validated by fresh installs.

## Snapshot, lifecycle and layout

One mutex protects a copied snapshot containing health, stamina, core values, movement
text and the five new widget texts/availability flags. JNI reads it once, returning
`Object[] { long[29], byte[6][] }`. The first 24 numbers are the accepted core protocol;
the last five are widget availability flags. The six byte arrays contain movement,
weariness, activity, transition, malus and pain, in that order. UTF-8 bytes avoid
modified-UTF-8 string conversion. The existing CoreHudSnapshot decoder is reused
verbatim for the numeric/core portion; ActivityHudSnapshot validates and copies the
new fields. Inactive/unready sessions clear all readings and text.

No live game object is read from Android's UI thread. The accepted non-focusable
Presentation, session/Activity hooks, display selection and 250 ms polling are
preserved. No forced redraw, turn advancement, controller injection, or viewport
change is added. Captures still follow the existing sidebar hook.

Two paired rows show weariness/activity and transition/malus; pain has a full-width
row. Existing fields are not removed or reduced. The owner reports that all readings
fit legibly without clipping, at the limit before scrolling becomes necessary.
The existing scroll fallback remains for subsequent content that exceeds the display.
The owner explicitly defers layout changes until the data has been brought over and
will share a minimap idea later. Do not infer its design or request it prematurely.
This is not the final compact layout or the coordinated show/hide design.

## Validation completed and limits

All 18 new host/fixture tests passed locally. Coverage includes eight integration
targets, pinned hash/destination guards, unchanged lifecycle hooks, current getters,
exact pinned widget-definition hashes, missing/blank fields, copy isolation,
concurrent coherent reads, and normal/exception session clearing. A compiled capture
fixture checks widget order, local definition copies, missing widget handling and
inactive-session suppression. That fixture substitutes small game/widget types;
it does NOT run CDDA's real widget renderer or full engine.

The production JNI code was compiled into a host library and called from Java under
`-Xcheck:jni`. Tests cover all numeric fields and new text slots, signed/zero values,
focus above 100, embedded NUL, Unicode/supplementary characters, long text, malformed
payloads, copy independence and session transitions. The native mailbox also passed
AddressSanitizer and UndefinedBehaviorSanitizer. Workflow YAML and all ten Bash
blocks passed syntax checks; these local checks alone were not a GitHub runner execution.

The existing 51-test suite was not rerun in that local implementation pass. Build 8
subsequently ran all 69 tests successfully in GitHub CI, applied the eight-target
overlay to the real pinned source and completed Android Java/native compilation
and signing/package checks. The owner then reported the hardware results below.
These results do not extend the substitute-widget tests into exhaustive real-engine
coverage or establish every possible activity/weariness state.

## Device acceptance (build 8: owner-reported PASS)

| Category | Result |
|---|---|
| Layout and scrolling | PASS: all readings legible and rows accessible without clipping; at the limit before scrolling becomes necessary. |
| Activity and weariness | PASS: Weariness, Activity, Transition glyphs and Weary Malus match the upper sidebar and were observed changing in sync. |
| Pain | PASS: visible dash when not in pain; descriptions and formatting update in sync with the upper sidebar. |
| Previous readings and controller focus | PASS: no change from previously passing behavior reported. |
| Lifecycle and clearing | PASS: no change from previously passing behavior reported. |

Dynamic/lifecycle results are the owner's observations, not inferred from the photo.
Exact categories/thresholds exercised were not enumerated; missing-widget behavior,
alternate font/DPI settings and exhaustive scrolling or extended-play coverage are
not claimed. Color fidelity remains deferred despite correct text/glyph behavior.

## Subsequent regression and design work

Preserve comparison of all five readings with the upper sidebar during activity/rest
and pain changes, as well as prior health/core readings, controller focus, sleep/resume,
app switching and menu/reload clearing. Compare both screens at the same game refresh;
the accepted shared movement-mode refresh behavior is unchanged.

The owner highlighted the nearby-creature name/count list and is undecided whether it
needs migrating alongside the directional compass. Record that as an open inclusion/
presentation decision, not a scope deletion or an approved always-visible layout.
The pinned compass JSON defines the directional widgets and a separate name legend;
see Checkpoint 6. No legend, optional control or visibility feature is implemented here.

Variable anatomy, final colors/layout, remaining metrics, both maps, entity compass,
message log and coordinated show/hide/sidebar removal remain later work. The original
upper sidebar stays intact throughout this experiment.
