# Checkpoint 4: body-status HUD passes Thor functional acceptance

Status: accepted for this bounded increment, based on owner-reported tests on the
AYN Thor on November 12, 2026 (America/Los_Angeles). This is not full Milestone 1
completion or an exhaustive stability assessment.

## Tested build

- Build: 6; experiment: `body_status`; signing: `persistent`.
- Tested source: `643eabbf2f406cc69a99798cef3a073d9b1f3301`.
- Source checkpoint branch: `checkpoint/body-status-6` at that exact commit.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43373711241
- Artifact: `CDDA-DS-arm64-test-6`, ID `14013387441`.
- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Application ID: `io.github.mrchimpy.cddads.experimental`.

Build 6's CI/log-and-package review preceded these device tests. All 36 host/fixture
tests, Android compilation, and the workflow's signing/package checks passed.
The following acceptance results are the owner's hardware observations, not tests
performed by the assistant or inferred from CI success.

## Owner-reported results

| Test | Result | Observation |
|---|---|---|
| Layout | PASS | All six bars fit without clipping or overlapping their text labels. Stamina remains visible and refreshes properly. |
| Body-part mapping | PASS | All bars correspond to the upper-sidebar meters. Left/right mapping checked and passed. |
| Damage and healing | PASS | Damage and healing update the appropriate values/bars. |
| Stamina regression | PASS | The lower-screen stamina display continues working as in the previous build. |
| Focus and lifecycle | PASS | Upper display remains the controller input target after lower-display touches. Sleep/resume, app switching, and foreground/background transitions restore both displays. |
| Session clearing | PASS | Returning to the main menu clears character information. Loading restores correct health and stamina. |

The accompanying device photo shows all six labeled body-health bars and stamina
visible together, with differing injury levels and the original upper sidebar still
present. The photo supports the layout observation; the dynamic/lifecycle results
come from the owner's test report. The photo remains in the project conversation;
it has not been copied into this repository.

## Scope and remaining limits

- The accepted increment is six standard human body-health bars alongside stamina.
- Bars are proportional, without numeric body HP; they are not a complete reproduction
  of upstream health-display semantics, extra anatomy, or body-part effects.
- Sampling remains tied to sidebar redraws.
- The upper sidebar and original viewport are retained.
- Full lower-screen HUD content, including the small text/symbol map, eight-way
  entity compass, message log, and separate pixel minimap, remains unfinished.
- Extended play and all possible controller bindings are not claimed as tested.
- Fresh installs remain the chosen development process. Back up wanted test data
  before uninstalling only the test app; retain the same signing key and app ID.
- In-place update/data migration remains unresolved. These passes do not establish
  upgrade compatibility or resolve the earlier stale-data warning.

The documentation commit recording these results is separate from the tested source
above. No game, display, controller, signing, or workflow changes are needed to record
this checkpoint.
