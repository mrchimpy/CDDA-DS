# Experiment 4: activity, weariness and pain

Status: implementation and 18 new local host/fixture tests completed. Full Android
compilation, real-engine overlay application and Thor acceptance remain pending.
This is an incremental read-only HUD, not full Milestone 1 completion.

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

After review and merge into `ds-dev`, start a NEW manual **CDDA-DS Android test** run:

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
row. Existing fields are not removed or reduced. The existing scroll fallback remains
for content that exceeds the display. Fit at default Thor DPI/fonts, scroll behavior
and controller focus after swipes need actual hardware testing. This is not the
final compact layout or the coordinated show/hide design.

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
blocks passed syntax checks; this is not a GitHub runner execution.

The existing 51-test suite was not rerun locally. The next CI run must discover both
old and new tests (69 expected), apply the actual pinned-engine overlay and compile
the Android UI/native app. No Android Presentation compilation, emulator execution,
Thor testing or new APK is claimed by these local checks.

## Device acceptance (pending)

1. Check all five added readouts plus prior health/core values. Note whether scrolling
   is needed at default Thor text size/DPI; verify no clipping or inaccessible rows.
2. Compare weariness, activity, transition glyphs and malus text with the upper sidebar.
   Exercise activity/rest and any weariness change available in a disposable test;
   report unchanged/unexercised states rather than assuming they passed.
3. Compare the pain description during damage/recovery and when the sidebar suppresses
   pain text. A blank result should display a dash; `Unavailable` is a different state
   to report, not a substitute for "No pain".
4. Check prior health/stamina/current attributes, movement and focus. Compare both
   displays at the same game refresh; no extra turn should be injected by the HUD.
5. Touch/scroll the lower screen, then verify upper-controller focus, sleep/resume,
   app switching, foreground/background transitions, menu clearing and reload.

Variable anatomy, final colors/layout, remaining metrics, both maps, entity compass,
message log and coordinated show/hide/sidebar removal remain later work. The original
upper sidebar stays intact throughout this experiment.
