# Experiment 3: current core status, body health, and stamina

Status: implemented with local host/fixture checks. Full Android compilation and
Thor acceptance are still pending. No new APK or hardware acceptance is implied.

This builds on the accepted build 6 health/stamina display. It adds the requested
Strength, Dexterity, Intelligence, Perception, Speed, Movement mode, and Focus.
The upper sidebar and viewport remain unchanged. No gameplay actions, controller
remapping, signing changes, extra permissions, or second APK are introduced.

## Build

After merging this change into `ds-dev`, start a NEW **CDDA-DS Android test** run:

| Input | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `core_status` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

The workflow is still manual-only and gated to `ds-dev`; `baseline` remains the
safe default. `stamina_probe` and `body_status` remain available unchanged. The
accepted source is preserved as `checkpoint/body-status-6` at
`643eabbf2f406cc69a99798cef3a073d9b1f3301`.

Use the owner's fresh-install development process after backing up wanted test
data. Remove only CDDA-DS (test), not official CDDA. Keep the persistent signing
secrets unchanged. In-place update/data migration remains unresolved.

## Where values come from

All captures run on the game thread during the existing `game::draw_panels` hook.
These are current/effective values, not the character's starting/base attributes.

| Readout | Pinned upstream source |
|---|---|
| Strength | `u.get_str()` |
| Dexterity | `u.get_dex()` |
| Intelligence | `u.get_int()` |
| Perception | `u.get_per()` |
| Speed | `u.get_speed()` (character speed, not terrain movement cost or vehicle velocity) |
| Focus | `u.get_focus()` (raw displayed value, not a percentage; no 100-point clamp) |
| Movement mode | `u.current_movement_mode()->name()` plus `panel_letter()` |

The six numeric getters match `widget::get_var_value` in the pinned `src/widget.cpp`.
Movement uses the same mode object/letter as `display::move_mode_letter_color` in
`src/display.cpp`; its full name comes from `src/move_mode.h`. Names are supplied
by CDDA, rather than a second hard-coded walk/run/crouch/prone map in Java.

Pinned source references:
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/widget.cpp
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/display.cpp
- https://github.com/mrchimpy/CDDA-DS/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/move_mode.h

## Data and layout

One mutex-protected snapshot contains stamina, all six health pairs, all six numeric
core readings, and a copied UTF-8 movement label. JNI reads the mailbox once and
returns `Object[] { long[24], byte[] }`: the original 18 numeric fields followed by
Strength, Dexterity, Intelligence, Perception, Speed, Focus; the byte array contains
the movement label from the SAME copy. The label is transported as ordinary UTF-8
bytes, not passed to `NewStringUTF` as modified UTF-8. No game object is accessed
from Android's UI thread. The decoder clones numeric data and clears all readouts
for inactive/unready states. No snapshot or label persists into the next session.

The accepted health/stamina section remains. Three paired rows add the attributes,
speed and focus; one wrapping row shows movement. A non-focusable scroll container
is a safety net for large fonts, long mode names or smaller displays. Normal Thor
fit still requires testing. Scrolling only views the read-only panel; it does not
send input to CDDA. Existing non-focusable Presentation, 250 ms polling, lifecycle
hooks, and intact-upper-sidebar fallback are retained.

## Local validation and limits

The new host/fixture suite checks seven-file overlay planning, fail-before-write
hash/path guards, current getters, unchanged lifecycle hooks, copied-state isolation,
concurrent coherent reads, session clearing and a compiled capture-hook fixture.
It also compiles the production JNI implementation into a host shared library and
calls it from Java under `-Xcheck:jni`. Tests cover field order, changed/zero/negative
values, focus above 100, UTF-8 including supplementary characters, long/empty movement
labels, malformed payloads, reader-copy independence, and session transitions.

The host JVM is NOT an Android device. The Android Presentation itself is not built
or exercised by that host JNI test. Full Android Java/native build and physical
layout/focus/lifecycle testing remain required. The local overlay uses a small source
fixture with matching integration anchors, not a full engine build; CI retains the
original pinned-source hashes and must apply the real overlay before compilation.

## Device acceptance (pending)

1. All seven new readouts fit and remain legible with health/stamina; no clipped
   labels or values. Report whether scrolling is necessary at normal Thor settings.
2. Compare all four current attributes, Speed and Focus with the upper sidebar.
   Include a character/state with penalties or bonuses, not only starting values.
3. Change movement using the ordinary game controls. Verify full name and letter
   match each mode that can be selected; a rejected switch must not invent a change.
4. Confirm values change on redraw without advancing turns merely to refresh the HUD.
   Confirm stamina depletion/recovery and damage/healing still work.
5. Repeat lower-touch/controller-focus, sleep/resume, app switching, menu clearing
   and reload checks. No previous character's mode or core readings should survive.

## Deferred deliberately

Six standard body parts remain the prototype assumption. Variable anatomy and
which parts warrant health bars are required completeness/layout checks before
final layout and coordinated show/hide/sidebar removal, not part of this increment.
Upstream color rules, complete translation of fixed HUD labels, other metrics,
both maps, compass, message log, interactive actions, and visibility controls are
not implemented here. Sampling remains tied to sidebar redraws. Menus/idle turns
can retain the last snapshot; its age is still displayed. This is not full Milestone 1.
