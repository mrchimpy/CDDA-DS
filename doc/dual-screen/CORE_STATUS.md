# Experiment 3: current core status, body health, and stamina

Status: build 7 passed Android CI/package checks. Owner-reported Thor results pass
layout, current values including damage penalties, health/stamina/focus handling,
and session clearing. Movement-mode refresh is PARTIAL: the lower label updates
after the next turn rather than immediately with the upper sidebar. See
[Checkpoint 5](CHECKPOINT_5.md) and open finding `CORE-REFRESH-01`. This is a qualified
checkpoint for continued development, not an all-pass acceptance.

This builds on the accepted build 6 health/stamina display. It adds the requested
Strength, Dexterity, Intelligence, Perception, Speed, Movement mode, and Focus.
The upper sidebar and viewport remain unchanged. No gameplay actions, controller
remapping, signing changes, extra permissions, or second APK are introduced.

## Build

PR #2 has merged and build 7 already exists; no rebuild is needed merely to record
its test results. For a subsequent requested build, start a NEW **CDDA-DS Android
test** run:

| Input | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `core_status` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

The workflow is still manual-only and gated to `ds-dev`; `baseline` remains the
safe default. `stamina_probe` and `body_status` remain available unchanged. The
accepted body-status source is preserved as `checkpoint/body-status-6` at
`643eabbf2f406cc69a99798cef3a073d9b1f3301`. The tested core-status source is
`checkpoint/core-status-7` at `8382d31744c2c138afd5130f3f7862e9322f01d9`, with the
movement-refresh exception documented in Checkpoint 5.

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
is a safety net for large fonts, long mode names or smaller displays. The owner
reported no scrolling or clipping at default Thor text size and DPI in build 7;
other configurations remain unverified. Scrolling only views the read-only panel;
it does not send input to CDDA. Existing non-focusable Presentation, 250 ms polling,
lifecycle hooks, and intact-upper-sidebar fallback are retained.

## Host/CI validation and limits

The new host/fixture suite checks seven-file overlay planning, fail-before-write
hash/path guards, current getters, unchanged lifecycle hooks, copied-state isolation,
concurrent coherent reads, session clearing and a compiled capture-hook fixture.
It also compiles the production JNI implementation into a host shared library and
calls it from Java under `-Xcheck:jni`. Tests cover field order, changed/zero/negative
values, focus above 100, UTF-8 including supplementary characters, long/empty movement
labels, malformed payloads, reader-copy independence, and session transitions.

The host JVM is NOT an Android device. Those tests do not exercise the Android
Presentation or actual game event/redraw timing. The local overlay uses a small
source fixture with matching integration anchors, not a full engine build. Build 7
subsequently passed all 51 host/fixture tests in CI, applied the seven-target overlay
to the real pinned source, and completed Android Java/native compilation and the
signing/package checks. The owner supplied the device observations below; CI success
did not establish refresh behavior after a no-turn mode selection.

## Device acceptance (build 7: qualified, movement refresh PARTIAL)

| Category | Owner-reported result |
|---|---|
| Layout | PASS: readable with no clipped labels/values and no scrolling at default Thor text size/DPI. |
| Current values | PASS: all shown attributes/meters match the upper sidebar, including penalties from incoming damage. |
| Movement mode | PARTIAL: the upper sidebar changes immediately after selection; the lower label changes only after the next turn. |
| Health, stamina and focus handling | PASS: combined checklist category reported passed. |
| Session clearing | PASS: menu/reload clearing category reported passed. |

`CORE-REFRESH-01` remains open. The owner explicitly deferred an immediate fix and
plans to test other readouts' no-turn refresh behavior after the next build. That
cross-metric timing test is pending; do not claim all metrics share the delay.
The capture/publication path is a working hypothesis, not a confirmed root cause.
See Checkpoint 5 for reproduction and the snapshot-number/age diagnostic.

## Future regression and closure checks

1. Preserve default Thor fit and correct current values, including penalties/bonuses.
2. Change movement through ordinary controls without advancing a turn; the lower
   name/letter must eventually follow accepted selections in its normal refresh
   cycle, while rejected switches must not invent a change. Currently PARTIAL.
3. Check other legitimately no-turn state changes against both displays; record
   snapshot number/age to help distinguish capture from rendering. Currently pending.
4. Repeat health/stamina changes, lower-touch/controller focus, sleep/resume, app
   switching, menu clearing and reload checks after future implementation changes.

## Deferred deliberately

Six standard body parts remain the prototype assumption. Variable anatomy and
which parts warrant health bars are required completeness/layout checks before
final layout and coordinated show/hide/sidebar removal, not part of this increment.
Upstream color rules, complete translation of fixed HUD labels, other metrics,
both maps, compass, message log, interactive actions, and visibility controls are
not implemented here. Sampling remains tied to the current sidebar hook. The known
no-turn movement refresh gap must be addressed before the lower HUD replaces the
upper sidebar; keeping the last snapshot in an idle menu is not blanket acceptance
of stale values when the original sidebar already shows a change. This is not full
Milestone 1.
