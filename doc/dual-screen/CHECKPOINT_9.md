# Checkpoint 9: body-details HUD passes exercised Thor checks

Status: accepted as a checkpoint for continued incremental development based on
the owner's build 11 report. All five categories pass for the cases exercised;
no defects were reported. The explicit coverage limits below remain open. This
is not exhaustive field acceptance, aesthetic fidelity or full sidebar migration.

## Tested build

- Build: 11; experiment: `body_details`; signing: `persistent`.
- Tested source: `f7e2d5700b7504a35d754a5b243036396521aeaa`.
- Source checkpoint: `checkpoint/body-details-11` at that exact revision.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43408109422
- Artifact: `CDDA-DS-arm64-test-11`, ID `14028098151`.
- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Application ID: `io.github.mrchimpy.cddads.experimental`.

The preceding CI/log-and-package review reported all 133 host/fixture tests passed,
eight integration targets applied to pinned source, successful Android Java/native
compilation and successful signing/package checks. Device results below are the
owner's observations, not assistant-operated hardware tests or inferences from CI.
This documentation update does not rerun or independently revalidate that build.

## Owner-reported results

| Category | Result | Observation |
|---|---|---|
| Layout and scrolling | PASS for exercised content | All previous and new rows are reachable and legible, including Worn feet. Simultaneous lower-screen swiping and upper-screen joystick input remain good. Longer clothing descriptions were unavailable for testing. |
| Body comfort and trend | PASS for observed states | Comfort matches and is synchronized with the sidebar; a blank trend appears as a dash. Clothing-driven comfort changes were explicitly untested, despite the owner's high confidence. No nonblank rising/falling trend or particular temperature-category transition was enumerated. |
| Oxygen | PASS for reduced/recovering state | The owner reports that the character started with limited oxygen and attributes this to game RNG. Recovery on the lower display stayed synchronized with the upper sidebar. The report does not explicitly confirm the final full-capacity meter-to-dash transition. |
| Worn clothing/armor | PASS for wear/remove/swap | Wearing, removing and swapping worn clothing/armor updated the lower summaries in sync with the upper sidebar. Layering on the same body part and an uncovered category were explicitly not tested. |
| Previous readings and lifecycle | PASS | Owner reports the combined category passed, with no additional notes. |

The reported reason for the character's initial oxygen state is not an independently
verified engine finding. The demonstrated result is correct observed recovery
parity, not a diagnosis of how the starting state arose.

## Open verification items, not reported defects

- Long clothing descriptions: on-device wrapping remains NOT TESTED. Long wielded-
  item-name wrapping from build 10 also remains open; host long-string transport
  tests do not establish on-device visual presentation.
- Clothing-driven comfort changes: NOT TESTED. High confidence is not a completed
  observation. Nonblank rising/falling trends and specific category transitions
  were not separately established by this report.
- Oxygen at final full capacity: the return from the symbolic meter to a dash is
  NOT EXPLICITLY CONFIRMED. Do not infer it from the recovery pass. No need to
  reopen the demonstrated reduced/recovering-state agreement.
- Layered clothing on one body part and uncovered-category output: NOT TESTED.
  Removing an item alone does not establish the resulting category was uncovered.
- Bionic-power behavior from build 10 remains NOT TESTED. This report does not
  close it or other earlier untested knowledge/unit cases.
- Previous readings/lifecycle passed as a combined category. No additional stress
  runs, timings, controller-binding coverage or detailed sequences are inferred.
- All clothing combinations, independent bilateral coverage, variable anatomy,
  every comfort/oxygen state, alternate DPI/fonts and long-play stability are not
  established by this report.

These are test-coverage limits, not evidence of defects or reasons to invent a
repair. Carry them into the completeness pass and future practical testing before
claiming full replacement of the original sidebar.

## Retained scope and sequencing

- Continue incremental read-only coverage; retain the upper sidebar and viewport.
- Preserve readable text and the temporary scrolling layout. No tab implementation,
  automatic page switching, gameplay controls or visibility changes are authorized
  by this acceptance report.
- Both maps, directional compass, messages and remaining metrics are unfinished.
  Creature-name/count legend inclusion/presentation remains an open decision.
- Context-themed pages and repeated readouts remain layout ideas, not a committed
  page design. The minimalist font, state-color and functional-framing preference
  stays with the later presentation pass; no decorative assets are introduced.
- Anatomy and full display semantics remain completeness work before final layout,
  coordinated show/hide and upper-sidebar removal.
- The corrected shared movement-mode refresh behavior remains unchanged; no
  companion-only timing defect is reopened here.
- Keep persistent signing and app identity. Continue fresh installs after backing
  up wanted test data; in-place update/data migration remains unresolved.

Documentation only. The tested source is distinct from the documentation revision.
No game, HUD, input, workflow or signing changes; no new APK, rebuild or reinstall.
