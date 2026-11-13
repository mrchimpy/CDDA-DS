# Experiment 2: body health and stamina

Status: build 6 passed Android CI/package checks and all six owner-reported Thor
functional acceptance categories. See [Checkpoint 4](CHECKPOINT_4.md) for the exact
tested revision, observations, and remaining limits.

Select `body_status` with persistent signing in the manual Android test workflow.
This adds six health bars (head, torso, left/right arms and legs) alongside stamina.
The original upper sidebar remains intact. No viewport or controller changes.

Implementation uses the same copied-state mailbox and Presentation lifecycle as
build 5. All six current/max HP pairs are copied with stamina under one mutex;
Android reads only that snapshot. Menu/session transitions clear all values.
This first body-health view assumes the standard six human body parts; it does not
represent extra/mutated limbs, effects, limb temperature, or full sidebar semantics.
Health is displayed as proportional bars without exposing numeric HP.

Use a fresh installation for development per the owner's preference. Back up wanted
test data first; signing and application identity remain unchanged. In-place update
and data migration remain unresolved.

## Device acceptance (build 6: owner-reported PASS)

- Layout: all six bars and labels fit without clipping or text overlap; stamina is visible.
- Body-part mapping: matches the upper sidebar, including left/right checks.
- Damage and healing: appropriate body-part bars update.
- Stamina regression: updates remain correct as in the previous build.
- Focus/lifecycle: lower touches preserve upper controller focus; sleep/resume,
  app switching, and foreground/background transitions restore both displays.
- Session clearing: main menu clears character data; loading restores health and stamina.

These checks accept the bounded body-status experiment, not full sidebar migration
or exhaustive stability. Maps, compass, messages, environmental status, and sidebar
removal remain later work within the full HUD milestone.
