# Experiment 1: one real value on the second display

Status: implementation prepared; full Android compilation and Thor behavior still
require validation. This is NOT Milestone 1 completion.

## Select the experiment

Run **CDDA-DS Android test** on `ds-dev` with:

| Input | Value |
|---|---|
| `experiment` | `stamina_probe` |
| `signing_mode` | `persistent` |
| `use_cache` | enabled |

`baseline` remains the default experiment and builds the ordinary single-screen
version. No private key changes, new permissions, separate APK, Shizuku integration,
or controller remapping are required by the probe. The pipeline remains manual-only.

After CI/package validation, install the new persistent-signed APK over build 4,
without uninstalling. Back up any test data worth retaining first. Its application
ID and key must remain unchanged, and its version code must advance. Report an
unexpected installation failure rather than uninstalling to conceal it.

## Expected behavior to test (not yet verified on Thor)

Top: original map, original sidebar, ordinary menus and controller behavior.
Bottom: a simple read-only stamina panel with current/maximum, percentage, a bar,
a snapshot number, and age since the game last redrew the sidebar.

Launch the game on the upper display with the Thor's existing top-screen focus lock.
The probe looks for exactly one other eligible Android presentation display. It does
not hard-code display 1 or assume screen resolution. On the title screen it should
show "No active game"; after loading a game it should report actual stamina.

The display is intentionally diagnostic, not a proposed final HUD layout.

## Architecture

One APK. The game thread copies two integers during `game::draw_panels`. A scoped
session starts only after the opening menu enters a real game and clears the snapshot
on return to the menu or exception unwinding. A mutex protects the small native
mailbox. Android reads a copied snapshot through JNI every 250 ms, never touches
live Character/game objects, and never calls gameplay actions or advances turns.

A Java `Presentation` draws native views on the secondary display. Its window does
not request keyboard/gamepad focus. Touches in the read-only panel are consumed;
no commands are injected. Activity pause/destroy dismiss the panel and stop callbacks;
resume redetects the display. Display selection and failure details are written to
Android log tag `CDDA-DS-HUD` and `files/ds-hud-probe.txt` under CDDA-DS Test Data.
No extra keep-awake flag is set by the HUD.

If there is no suitable display, multiple candidates, or a presentation-window error,
the original sidebar remains. The probe does not alter viewport sizing or remove any
upper-screen information. OEM focus/lifecycle behavior remains a hardware test.

## Deliberately bounded limitations

- Samples follow sidebar redraws, not every internal simulation update. Menus or
  waiting for a turn may leave the last snapshot unchanged; its displayed age makes
  that explicit. This is not yet the final HUD's freshness guarantee.
- Only presentation-category displays are supported. Other devices and an unexpected
  Thor display configuration produce diagnostics, not a permission-bypassing fallback.
- No maps, entity compass, message log, full body/status HUD, or inventory actions yet.
- No runtime enable/disable settings menu yet. Build a new `baseline` APK to remove
  this experimental integration while retaining application identity and signing.
- Cache reuse, update persistence, and sleep/resume are tests, not promises.

## Temporary, explicit build overlay

The repository's original `src` and `android` trees remain pinned. Selecting this
experiment applies a checked-in overlay in the CI workspace only. Before touching
anything, `apply_stamina_probe.py` verifies exact Git blob hashes for `game.cpp`,
`main.cpp`, and `CataclysmDDA.java` and checks unique integration anchors. It adds
`ds_hud.h`, `ds_hud.cpp`, and `DualScreenHud.java`. CMake's existing source glob picks
up the added native file. All six changed/new paths and their contents are recorded
in `STAMINA-PROBE.patch` and SHA-256 values in `STAMINA-PROBE.json` in the artifact.
The usual installation-identity overlay remains separate.

This explicit overlay keeps the baseline/probe switch reversible during exploration;
it is not a commitment to maintaining production UI changes this way. Once the
architecture is validated, normal source edits and broader tests are preferable.
Never apply the script to a checkout with uncommitted game/Android modifications.

## Device acceptance checklist

1. Install as an update over build 4. Confirm the disposable save and volume setting
   remain. Do not change signing secrets or uninstall to work around a failure.
2. With CDDA on top, confirm the panel appears only below and the full original
   upper sidebar remains. A missing lower panel calls for its diagnostic file.
3. Load a disposable game. Use normal stamina-consuming actions, then recover stamina.
   Compare the lower numeric/bar display with the original upper stamina indicator.
4. Check eight-way selection and R2 commitment, ordinary menus, and touching below.
   No lower-screen touch should move the character, advance a turn, or take controller focus.
5. Save and return to the title menu: no previous character's stamina should remain.
   Load again and confirm a fresh snapshot.
6. Switch apps and return, then sleep/wake. Check game, controls, panel, and freshness.

A passing result establishes one-value plumbing only. Full sidebar migration retains
its existing scope, including both maps and the eight-way entity compass.

## Validation performed before first CI run

Seven new host/fixture tests cover anchor rejection, preflight/no-write failures,
recorded overlay coverage, activity hooks, and native session/concurrent-read behavior.
The native mailbox test compiles with C++17 and warnings-as-errors on the host. The
JNI code path also passed a host compilation using JDK JNI headers. These do not
substitute for an NDK build or Android device execution. Android Java compilation
and the hash-locked patch against the complete pinned source are checked in CI.
Workflow YAML, its job-level context use, and ten Bash blocks were checked locally.

## References and attribution

Original experimental integration for CDDA-DS; no implementation code was copied
from the reference projects. Keep upstream CDDA notices and license terms intact.
The Stardew Thor project is an architectural reference, not an imported dependency.

- CDDA pinned sidebar redraw: https://github.com/CleverRaven/Cataclysm-DDA/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/game.cpp
- Game-session loop: https://github.com/CleverRaven/Cataclysm-DDA/blob/bb52239dee96df602da097f113382fe5c9a9c115/src/main.cpp
- Android Presentation: https://developer.android.com/reference/android/app/Presentation
- Display selection: https://developer.android.com/reference/android/hardware/display/DisplayManager
- Window focus flag: https://developer.android.com/reference/android/view/WindowManager.LayoutParams#FLAG_NOT_FOCUSABLE
- Thor presentation precedent: https://github.com/hung-eggie-do-covergo/stardew-thor-dual-screen/blob/main/README.md
