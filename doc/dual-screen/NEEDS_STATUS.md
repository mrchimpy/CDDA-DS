# Experiment 9: basic needs and lower-screen deduplication

Status: accepted for build 13 based on the owner's Thor report on 2026-11-13.
All five reported categories pass, including eating/drinking/sleeping transitions,
blank/dash handling, deduplication, retained readings and presentation/input/lifecycle.
Widget ordering remains deferred. See [Checkpoint 10](CHECKPOINT_10.md) for the
observations and coverage limits; this is not exhaustive widget or release acceptance.

Tested source: `35ef6dd4e21983d71637c7d26275bcb57438b976`.
Source checkpoint branch: `checkpoint/needs-status-13`.
Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43477256421
The preceding build review confirmed all 191 host/fixture tests, Android compilation
and package checks passed. Recording acceptance makes no implementation changes
and does not require another build or installation.

Base: build 12 (`hud_presentation`), source
`a88a3e25efff14d0afdb08441fd540566c68d8d4`. The owner reported PASS for black
background, expected font diagnostic, readability, scrolling, previous readings,
simultaneous input and lifecycle. Font-size tuning was explicitly deferred.
Those are owner observations, not assistant-operated device tests. This increment
preserves that presentation and does not revisit the upper-sidebar allocation.

## Approved scope

Append three active-game readouts, with permanent labels:

| Lower label | Native widget | Meaning |
|---|---|---|
| Hunger | `hunger_desc_label` | Native descriptive hunger state, not a raw counter. |
| Thirst | `thirst_desc_label` | Native descriptive thirst state, including the game's instant-thirst rules. |
| Rest | `sleepiness_desc_label` | Native descriptive sleepiness, separate from Weariness. |

The existing game-thread capture calls the selected widget's `show(u, 80)` on a
local copy and strips color tags, as before. No new thresholds, nutrition model,
raw-counter readout, positive/rested placeholder, or gameplay change is introduced.
For valid empty/whitespace output the label remains with the established dash
(U+2014). A missing widget remains `Unavailable`, never silently a neutral state.

Remove exactly these nine LOWER view rows: Time, Date, Place, Wield, Style,
Weather, Lighting, Wind and environmental Temperature. This is a presentation
change only. Native definitions, the upper sidebar, and the original values in
our copied snapshot remain intact. Environmental Temperature is not Body comfort;
Wield/Style are not the six worn-clothing summaries. The latter remain displayed.

All other readouts remain, including body health, stamina, current attributes,
speed, movement mode, focus, activity/weariness/transition/malus, pain, oxygen,
body comfort/trend, worn clothing, bionic power, Sound and Mood.

## Temporary layout and unchanged behavior

The first five widget rows retain their paired/full-width arrangement. The nine
removed rows have no TextViews and no placeholder space. Remaining full-width
rows keep their order; Hunger, Thirst and Rest are appended after Worn feet.
There are 20 displayed widget readouts instead of 26, and 36 total attached
TextViews instead of 42. This is six fewer rows, before actual text wrapping.

Black backgrounds, shared Terminus/Unifont typeface resolution, text sizes,
progress bars, spacing, scrolling, focus flags, 250 ms polling and session handling
are unchanged. Rendering and clearing skip only the absent view slots. No tabs,
font-size tuning, state-color overhaul, vehicle work, maps, compass, interactive
controls, anatomy refactor or upper-sidebar configuration write is included.

The owner's current upper-screen panel choices (including both small maps, Env,
compass/legend, vehicle and log) are not changed. Needs was enabled upstairs for
comparison. With the reported needs checks passed, the owner can disable that
panel for normal play using the native configurator and re-enable it for future
comparisons. This does not itself establish a separate Needs-disabled refresh or
configuration-persistence test. Earlier experiments, including `hud_presentation`,
remain unchanged and selectable.

## Integration and transport

The new manual selector is `needs_status`, applied in this order:

1. Existing `apply_body_details.py`.
2. Existing `apply_hud_presentation.py`.
3. New `apply_needs_status.py`.

The new stage validates all five generated source input hashes, the unchanged
core decoder/font helper, the three pinned JSON definitions, and unique anchors
before any source write. Unsafe paths and symlinks are refused; repeat application
fails. No original upstream source/data files are committed as modified files.

New text slots 26, 27 and 28 are Hunger, Thirst and Rest. All original 24 core
numbers and 26 widget positions retain their meanings, including hidden slots
5..13. The array-sized native transport and Java decoder grow to
`Object[] { long[53], byte[30][] }`: 24 core fields plus 29 availability flags,
and the movement label plus 29 UTF-8 widget strings. No raw game objects cross
threads; no transport redesign or reordering is performed.

`NEEDS-STATUS.json` and `NEEDS-STATUS.patch` describe the five targets superseded
by this final stage. Apply patches sequentially; do not compare the earlier UI
hash to the final source without the later report. The unchanged font-asset check
also runs for this selector, so `HUD-FONT-ASSETS.json` continues to identify the
inherited presentation layer. Signing, permissions, baseline default, ds-dev gate,
caches and manual-only dispatch remain unchanged.

## Original implementation validation and limits

All 29 new host/fixture tests passed locally. They cover pinned widget definitions,
append-only field ordering, parent-source identity, five-target provenance,
hash/anchor/path guards, unchanged native transport logic, and omitted UI rows.
A compiled capture fixture exercises changed/blank/missing needs, copied widget
isolation, session clearing and coherent concurrent reads. Native AddressSanitizer
and UndefinedBehaviorSanitizer checks also passed (not a race-detector test).

Generated production native JNI, Java decoders, HUD and the unchanged font helper
were compiled and exercised together under a host JVM with `-Xcheck:jni`.
Java compiled with `--release 8 -Xlint:all,-options -Werror`. Nine scenarios cover
ordinary/changed/blank/whitespace/missing/Unicode/long/NUL values, independent
copies, malformed payloads and preserved font fallback. Each walks the actual
production UI calls through active, inactive, unready, invalid and reloaded states,
checking 36 attached text elements, nine absent slots and all retained readings.
Android API substitutes are reused unchanged from the presentation tests.

Local generated inputs were reconstructed from the build-12 artifact patches and
verified against recorded hashes. The explicit `DS_NEEDS_PARENT_FIXTURE` setting
selected these files locally; its game.cpp is a hook-only substitute. Fixture apply
tests override expected source hashes only inside unittest mocks. The production
script has no fixture bypass. On CI without that setting, the tests derive the
full parent game.cpp and generated files from the existing overlay generators and
verify their actual production hashes. The pinned needs JSON bytes were also
checked against build-12 APK assets locally.

Those host checks were not full-engine needs simulations or real Android
rendering/input tests. At implementation time, the earlier 162 tests were not rerun
locally; workflow YAML and all ten Bash blocks passed local syntax checks.
Subsequently, build 13 passed all 191 tests and compiled against the real pinned
source and Android SDK. The owner then reported the separate device results in
Checkpoint 10. This documentation update does not rerun those tests or builds.

## Rebuilding and regression checklist

For a future manual build of this experiment on `ds-dev`, use:

| Input | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `needs_status` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

The checkpoint branch and tested commit above identify the exact accepted source;
future `ds-dev` commits may contain additional work. No rebuild is required merely
to record this acceptance. Keep the established fresh-install process after backing
up wanted test data and settings. Leave official CDDA and signing secrets unchanged.
In-place data migration remains unresolved.

The following remains a reusable checklist for future regressions; the exercised
build-13 cases have passed as recorded in Checkpoint 10:

1. Compare Hunger, Thirst and Rest with the native Needs panel at the same game
   refresh. Exercise practical eating/drinking/rest or state changes; record cases
   not reached as untested. Weariness is not a substitute for Rest.
2. Check valid blank results become a labeled dash and nonblank descriptions return
   correctly. Report `Unavailable` as a missing-widget result, not a neutral state.
3. Verify all nine requested lower rows are absent, with no empty spacer rows.
   Body comfort/trend and all six worn rows must still appear. Reach the new final
   Rest row and footer; no clipping or inaccessible content.
4. Recheck retained readings, black background and expected font diagnostic,
   simultaneous lower swipe/upper joystick, sleep/resume, app switching, main-menu
   clearing and reload. Upper-panel behavior/configuration must remain unchanged.

Earlier untested cases (bionics, long on-device names, layering/uncovered clothing,
comfort transitions, oxygen's final suppression state, variable anatomy and other
coverage gaps) are not closed by these host tests or this general regression pass.
The needs report does not enumerate every severity state or special anatomy rule.
Vehicle evaluation, widget ordering, future tabs and full-overmap interaction remain
deferred; no additional implementation is authorized by recording these results.
