# Checkpoint 5: core-status HUD passes reported sidebar-parity tests

Status: accepted for this bounded increment based on the owner's corrected device
report. Build 7 passed Android CI/package checks and the reported functional
categories below. Movement mode matches the original sidebar's refresh behavior;
immediate no-turn refresh is not established. This is not full Milestone 1 completion
or an exhaustive stability assessment.

Owner report and subsequent correction: November 12, 2026 (America/Los_Angeles).

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

## Owner-reported results (corrected)

| Category | Result | Observation |
|---|---|---|
| Layout | PASS | All readouts are readable, with no clipped labels or values. No scrolling is necessary at default Thor text size and DPI. |
| Current values | PASS | All bottom-screen attributes/meters match the upper sidebar. Damage-related stat penalties are reflected in sync with the sidebar. |
| Movement mode | PASS for sidebar parity | The owner corrected the initial report: neither the upper sidebar nor the lower label reflects the selected mode until the sidebar refreshes next turn. No lower-versus-upper timing mismatch is reported. |
| Health, stamina and focus handling | PASS | Owner reported this combined checklist category as passed. No additional per-subtest detail was supplied in this report. |
| Session clearing | PASS | Owner reported the menu/reload clearing category as passed. |

The accompanying device photo shows the core-status layout, health/stamina, and
current values together. It supports static visibility, not the timing or lifecycle
claims. The photo stays in the project conversation and has not been published in
the repository.

## Corrected finding: shared movement-mode refresh behavior

Tracking label: `CORE-REFRESH-01` (documentation identifier, not a GitHub issue number).
Status: CLOSED / SUPERSEDED as a lower-HUD mismatch, following the owner's correction.
No implementation fix was applied or needed to close that reported mismatch.

The initial report said the upper sidebar changed immediately while only the lower
label waited for a turn. The owner subsequently explicitly retracted that comparison:
the sidebar behaves like the lower screen, and both wait until the next-turn sidebar
refresh. The earlier documentation commit `48f79f688f14b057c936579992cc166c43ca23d5`
preserves the original report in history; its mismatch conclusion and corresponding
capture-path hypothesis must not be treated as current evidence.

Corrected observed sequence:

1. Load a disposable character and note the movement mode on both displays.
2. Select another available mode through the ordinary game controls.
3. Without advancing a turn, both displayed mode readings remain unchanged.
4. At the sidebar's next-turn refresh, both reflect the selected movement mode.

The owner suggests that mode selection does not consume a turn and therefore may
not trigger an immediate base-game sidebar refresh. This is a plausible explanation,
not a source-verified cause or a statement of upstream design intent. There has been
no separate unmodified-baseline reproduction or source trace in this correction.
Matching behavior in the two displays establishes parity in this tested scenario;
it does not prove an inherent engine limitation or an inability to redraw without
advancing simulation time.

Immediate feedback could be evaluated later as a separate UX enhancement. It is not
currently a companion-specific repair or a blocker to the next metric increment.
Do not force a turn, inject gameplay actions, or read live game objects from the
Android UI thread to change display timing. No polling-rate or gameplay change is
made here.

Other readouts' timing after no-turn changes remains untested; the owner's planned
cross-metric observations after the next build remain useful, without presuming a
fault or the same behavior for all metrics. General freshness/parity remains part
of the completeness pass before sidebar removal. The specific requirement to fix
a lower-only movement lag is withdrawn because its factual premise was corrected.

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
