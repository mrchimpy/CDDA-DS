# Experiment 2: body health and stamina

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
test data first; signing and application identity remain unchanged.

## Device acceptance (pending)

- Compare all six bars with the upper sidebar on a disposable character.
- After damage/healing, verify that the appropriate body-part bar updates.
- Verify labels and all six rows fit the lower display with no clipping.
- Repeat focus, app-switch, sleep/resume, title-menu clearing, and reload checks.
- Check stamina remains accurate.

Full Android CI and device validation are required before treating this increment
as accepted. Maps, compass, messages, environmental status, and sidebar removal
remain later work within the full HUD milestone.
