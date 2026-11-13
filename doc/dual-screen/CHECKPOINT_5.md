# Checkpoint 5: core-status HUD passes with a movement-refresh exception

Status: qualified functional checkpoint for continued development. Build 7 passed
Android CI/package checks and the owner-reported categories below, except that
movement-mode refresh is PARTIAL. This is not an all-pass acceptance, full
Milestone 1 completion, or an exhaustive stability assessment.

Owner report: November 12, 2026 (America/Los_Angeles).

## Tested build

- Build: 7; experiment: `core_status`; signing: `persistent`.
- Tested source: `8382d31744c2c138afd5130f3f7862e9322f01d9`.
- Source checkpoint branch: `checkpoint/core-status-7` at that exact commit.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43379254462
- Artifact: `CDDA-DS-arm64-test-7`, ID `14015414795`.
- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Application ID: `io.github.mrchimpy.cddads.experimental`.

The preceding CI/log-and-package review reported all 51 host/fixture tests passed,
the seven-target overlay applied to pinned source, Android Java/native compilation
completed, and signing/package checks passed. Device findings below come from the
owner, not from automated tests or assistant-operated hardware.

## Owner-reported results

| Category | Result | Observation |
|---|---|---|
| Layout | PASS | All readouts are readable, with no clipped labels or values. No scrolling is necessary at default Thor text size and DPI. |
| Current values | PASS | All bottom-screen attributes/meters match the upper sidebar. Damage-related stat penalties are reflected in sync with the sidebar. |
| Movement mode | PARTIAL | Selecting a movement mode immediately changes the upper sidebar without another turn. The lower label retains the previous mode until a turn passes, then updates. |
| Health, stamina and focus handling | PASS | Owner reported this combined checklist category as passed. No additional per-subtest detail was supplied in this report. |
| Session clearing | PASS | Owner reported the menu/reload clearing category as passed. |

The accompanying device photo shows the core-status layout, health/stamina, and
current values together. It supports static visibility, not the timing or lifecycle
claims. The photo stays in the project conversation and has not been published in
the repository.

## Open finding: movement-mode freshness without turn advancement

Tracking label: `CORE-REFRESH-01` (documentation identifier, not a GitHub issue number).
Status: open; owner explicitly deferred an immediate fix. Other readouts' behavior
after changes that do not consume a turn remains untested; the owner plans to check
after the next build. Do not generalize the movement result to all metrics.

Reproduction from the owner's report:

1. Load a disposable character and note the current movement mode on both displays.
2. Select another available mode through the ordinary game controls.
3. Do not move or take another turn-consuming action: the upper sidebar changes,
   while the lower mode label still shows the previous selection.
4. Advance a turn: the lower mode label updates.

Expected eventual behavior: once the engine accepts the new mode, the lower display
must reflect it during its normal refresh cycle without requiring an extra turn.
A rejected mode change must not display a mode the engine has not selected.

The current implementation captures state in `game::draw_panels` and the Android
UI polls a copied snapshot. A capture/publication or redraw-path timing gap is a
working hypothesis, not a diagnosed cause. The immediately updating upper sidebar
is evidence that the game can expose the new mode before another turn; this should
not be dismissed as an unavoidable turn-based-engine limitation. No code trace or
reproduction by the assistant establishes the exact missed refresh path yet.

For the next timing test, note the lower Snapshot number and its age immediately
before and after selection while leaving the turn unadvanced. An unchanged number
would indicate no new snapshot was published; a changed number with an old label
would require checking publication order/content and the UI consumer. Waiting or
opening a non-turn-consuming menu may help distinguish delayed publication from a
missed event, but no such additional experiment is claimed as completed here.

This finding is non-blocking for the owner's next incremental metric work while
the original sidebar stays visible. Freshness after no-turn state changes remains
a required completeness check before the lower HUD replaces the upper sidebar.
Do not force a turn, inject gameplay actions, or read live game objects on Android's
UI thread as a workaround. No polling-rate or gameplay change is made here.

## Retained scope and limits

- Preserve working health/stamina/core readings and the original upper sidebar.
- Fresh installs remain the development choice; retain persistent signing and app ID.
  Back up wanted test data before uninstalling only the test app.
- In-place update/data migration remains unresolved.
- Variable anatomy and upstream display semantics remain required completeness/layout
  work after incremental metric coverage and before final show/hide/sidebar removal.
- Both maps, entity compass, messages, and remaining status/environment information
  are still part of the unfinished full HUD milestone.
- Default Thor layout fit does not establish large-font, alternate-DPI, or all-device fit.
- The report does not independently establish every mode, rejected mode selection,
  all non-turn-changing metrics, or extended gameplay stability.

This checkpoint records observations only. The documentation revision is separate
from the tested source above and introduces no game, HUD, input, signing, or workflow
changes. No rebuild or reinstall is required for this documentation update.
