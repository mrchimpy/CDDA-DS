# Experiment 5: date, time and surroundings

Status: implemented with 20 new local host/fixture tests passing. Full Android build,
real-engine integration and Thor acceptance are pending. No new APK exists yet.

Builds on accepted build 8 (`activity_status`, tested source
`346e0bdc3a49efd83ff329a02cc55bef948a8285`) and its acceptance record at
`a84383a53c9c59624e7c21d9232490aa6e8f1cb4`. All prior health, stamina, current core
and activity readings remain. The upper sidebar and original viewport stay intact.

## Added information

| Readout | Pinned named widget | Interpretation |
|---|---|---|
| Date | `date_desc_label` | Game calendar display, not the device date. |
| Time | `time_desc_label` | The game's exact, approximate or unknown time text. |
| Place | `place_desc` | The current location description from the game. |
| Weather | `weather_desc` | The game's weather description. |
| Lighting | `lighting_desc` | The existing JSON widget's descriptive conditions. |
| Wind | `wind_desc` | Game-provided wind description/direction text. |
| Temperature | `env_temp_desc` | Environmental temperature, not body comfort. |

The existing game-thread widget capture renders local copies with `show(u, 80)`
and strips color markup, just as in the accepted activity experiment. There are no
new weather calculations, light thresholds, clock readers or temperature conversions.
In the pinned `src/display.cpp`, `time_string` gives exact time with a watch,
approximate time when the character can see the sky, and `???` otherwise. `get_temp`
returns a reading only with the relevant thermometer access/flag, otherwise `-`.
Using those widgets preserves these knowledge restrictions rather than exposing raw
engine state. Temperature uses the game's configured units. Actual runtime parity
and changes of equipment/visibility still require device tests.

The seven named definitions are in `data/json/ui/{date,time,place,weather,lighting,
wind,env_temp}.json` at pinned upstream `bb52239dee96df602da097f113382fe5c9a9c115`.
Time means the standard textual widget, not a graphical sundial or every custom
sidebar variant. This does not add body temperature/comfort, equipment, maps, compass,
creature names, messages, or remaining status fields.

## Implementation and preservation

`apply_environment_status.py` derives its build-workspace files from the accepted
activity templates, rather than committing another full copy of the HUD stack.
It validates those templates against explicit Git blob hashes, applies exact unique
replacement anchors in memory, and checks all source/destination guards before any
source write. A future template change must be deliberately reviewed, not silently
absorbed. The original activity/core/body/stamina scripts and templates are untouched.

The existing 24 numeric core fields are unchanged. The coherent snapshot extends
widget availability to 12 flags and widget text to 12 strings; JNI returns
`Object[] { long[36], byte[13][] }`. Text order is movement first, the original five
activity widgets, then Date, Time, Place, Weather, Lighting, Wind, Temperature.
All fields come from one copied snapshot. The native bridge implementation and core
Java decoder are reused without behavioral changes; the selected activity decoder
is generated with the expanded count and labels. UTF-8 is carried as bytes.

Blank widget text still produces a dash; a missing widget produces `Unavailable`.
Literal `???`, `-`, units, wind symbols and other game-provided text are preserved.
Inactive/unready sessions clear all fields. No live game object is accessed by the
Android UI thread; no game actions, extra permissions or forced redraws are added.
The accepted session hooks, non-focusable Presentation, display selection and 250 ms
polling remain. Shared next-turn movement refresh is unchanged, not a reopened bug.

## Temporary layout, not a redesign

The first five activity readouts retain their existing paired rows/full-width pain
row. Seven full-width wrapping rows are appended beneath them, using the existing
font size. Given the owner's build 8 space-limit report, expect to use the existing
scroll fallback; actual fit and swipe/controller-focus behavior remain untested.
No information is removed or text shrunk to force a no-scroll fit.

The owner's bottom-edge tabs and context-themed pages remain IDEATION ONLY. Repeated
readouts across pages, a possible engagement view, and map/legend groupings are not
approved design direction. No tabs, automatic switching, new gameplay controls or
visibility controls are introduced. The creature-name/count legend decision remains
open; both maps remain in the migration scope. Anatomy, final layout/colors and
coordinated show/hide/sidebar removal stay in the later completeness pass.

## Validation actually performed

- 20 new host/fixture tests passed, including eight-target overlay/provenance,
  source/template hash guards, symlink/existing-file/duplicate-anchor refusal,
  unchanged older templates/hooks and pinned widget-definition hashes.
- A compiled capture fixture checks all 12 widget slots, copied definitions,
  inactive-session suppression, missing widgets and unknown readings. It uses small
  substitute game/widget types, NOT the actual CDDA widget renderer.
- Generated production JNI code and decoder passed a real host-JVM round-trip under
  `-Xcheck:jni`: field order, prior core values, focus above 100, signed/zero values,
  missing/blank/unknown strings, long text, Unicode/supplementary characters,
  embedded NUL, invalid payloads, independent copies and session clearing.
- Native coherent-copy/concurrency/session tests passed AddressSanitizer and
  UndefinedBehaviorSanitizer. Workflow YAML and all ten Bash blocks passed syntax
  checks; the only workflow additions are the selector and dispatch case.

The existing 69 tests were not rerun locally. CI must run all tests (89 expected),
apply this overlay to actual pinned source and compile the Android native/Java app.
No Android Presentation compilation, emulator execution, complete engine integration,
or hardware acceptance is claimed by these host checks.

## Build and acceptance

After review/merge into `ds-dev`, start a NEW manual **CDDA-DS Android test** run:

| Setting | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `environment_status` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

The default is still `baseline`, and the workflow remains gated to `ds-dev`.
Continue the owner's fresh-install process after backing up wanted test data;
remove only CDDA-DS (test), not official CDDA. Signing secrets and app identity stay
unchanged. In-place update/data migration remains unresolved.

For the device test:
1. Scroll through all old/new rows at default Thor settings. Check wrapping, no
   clipped/inaccessible content, and controller focus after lower-screen swipes.
2. Compare all seven readings with the upper sidebar at the same game redraw.
   Exercise location changes and lighting/weather/wind changes that are practical;
   record conditions not reached as not exercised.
3. Check Time with/without a watch and with/without sky visibility where practical.
   Approximate/unknown output must remain consistent with the game's display.
4. Check Temperature with/without thermometer access and the current unit setting.
   A legitimate `-` differs from `Unavailable`. Do not assume all unknown cases passed
   just because a character possessing every instrument shows numeric readings.
5. Recheck health/stamina/core/activity values, sleep/resume, app switching,
   main-menu clearing and reload. The HUD must not advance a turn by itself.
