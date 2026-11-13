# Checkpoint 3: stamina probe passes Thor functional tests

Build 5, source `8a904007bd4104e1165f00fbb21966251f7c8309`.
Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43370344308

CI passed 29 tests, Android compilation, overlay application, APK signature and
package checks. Owner-reported device tests on November 12, 2026 passed:

- Lower-screen stamina panel appears with the original upper sidebar retained.
- Stamina changes with turns, matches the upper bar, and recovers while resting.
- Sleep/resume restores both displays.
- Lower-screen touch leaves the upper screen as the controller input target.
- Switching apps and returning shows no perceived issues.
- Returning to the main menu shows "No active game"; loading restores correct stamina.

This validates the one-value proof of concept, not complete sidebar migration or
extended gameplay stability. Individual controller bindings were not separately
reported in these results.

An update produced a stale-data diagnostic for `mods/Backrooms/modinfo.json`.
Update/data migration remains unresolved. The owner explicitly chose fresh installs
for further iterations, retaining the existing persistent signing key and app ID.
Back up any wanted test data before uninstalling. Earlier instructions to require an
in-place update for each iteration are superseded by this owner decision.

The next optional experiment is `body_status`; `stamina_probe` remains available
unchanged for comparison and rollback. See BODY_STATUS.md.
