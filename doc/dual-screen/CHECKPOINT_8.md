# Checkpoint 8: equipment-status HUD passes exercised Thor checks

Status: accepted as a checkpoint for continued incremental development, with the
explicit coverage gaps below. The owner reports no defects in the exercised paths.
Bionic-power behavior and long wielded-item-name wrapping remain NOT TESTED; this
is not an unconditional all-fields acceptance or full sidebar migration.

## Tested build

- Build: 10; experiment: `equipment_status`; signing: `persistent`.
- Tested source: `50474b61fd018ed46db61cfc6b253210ea3d1a7a`.
- Source checkpoint: `checkpoint/equipment-status-10` at that exact revision.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43401644695
- Artifact: `CDDA-DS-arm64-test-10`, ID `14025686664`.
- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Application ID: `io.github.mrchimpy.cddads.experimental`.

The preceding CI/log-and-package review reported all 109 host/fixture tests passed,
eight integration targets applied to pinned source, successful Android Java/native
compilation and successful signing/package checks. The device results below are
owner-reported, not assistant-operated hardware tests or inferences from CI. This
documentation update does not rerun or independently revalidate that build.

## Owner-reported results

| Category | Result | Observation |
|---|---|---|
| Layout and scrolling | PASS for exercised content | All rows are visible and reachable. Simultaneous lower-screen swiping and upper-screen joystick input remain good. The owner did not have a long-named item to exercise wrapping. |
| Wield | PASS | Repeated changes back and forth between wielded items update immediately/in sync with the upper sidebar. Unequipping produces `fist`, using the owner's reported wording. |
| Style | PASS | Changing to brawling updates the lower screen in sync with the sidebar. No additional notes or enumerated style combinations were supplied. |
| Sound and Mood | PASS | Reported updating in sync with the upper sidebar. Exact values, mood levels and transitions were not enumerated. |
| Bionic Power | NOT TESTED | The owner explicitly says bionics were not checked. The combined category's PASS is not evidence of functional bionic-power testing. |
| Previous readings and lifecycle | PASS | Owner reports the combined category passed, with no additional notes. |

The user's combined heading was "Bionic Power, Sound, and Mood: Pass" followed by
"I did not check bionics." This record separates those claims rather than assigning
a pass to an unexercised field. No bionic placeholder, charge level, capacity,
charging/draining behavior or related transition is established by this report.

The unarmed wording above preserves the report; it is not a newly hard-coded label
or a claim about every upstream character, language or widget configuration.

## Open verification items, not reported defects

- Long wielded-item-name wrapping on the Thor: not exercised. Ordinary row access
  and legibility pass; host long-string transport tests do not establish on-device
  rendering. Inherited game-widget width limits remain a separate consideration.
- Bionic Power: no functional acceptance claimed. Test relevant capacity and changing
  charge states against the upper sidebar when practical; do not infer a pass from
  compilation, tests with substitute widgets or Sound/Mood agreement.
- Other martial-arts styles, all mood levels, unusual equipment descriptions,
  alternate DPI/fonts, other devices and long-play behavior are not established.
- Previous readings/lifecycle were reported as passing; no extra stress runs,
  timings, controller-binding coverage or specific knowledge-rule retests are inferred.

These coverage gaps do not require a repair on the evidence supplied. Keep them
visible during continued incremental additions and revisit before claiming complete
coverage or replacing the original upper sidebar.

## Retained scope and sequencing

- Read-only HUD with original upper sidebar and viewport retained for comparison.
- Keep the temporary scrolling layout and readable text. Do not introduce tabs,
  automatic page switching, interaction controls or a visual redesign here.
- Context-themed pages, repeated readings across pages and map/legend organization
  remain later layout discussion; no implementation decision is made by this report.
- Typography, state-dependent colors and functional framing remain later presentation
  work. This functional checkpoint does not establish aesthetic fidelity.
- Clothing summaries, body comfort, oxygen, remaining metrics, both maps, compass,
  creature-legend inclusion/presentation, messages and variable anatomy remain later
  work under the existing scope. Do not remove the upper sidebar prematurely.
- Shared sidebar refresh behavior remains unchanged; the earlier corrected movement
  observation is not reopened as a lower-only defect.
- Keep persistent signing and app identity; use the owner's fresh-install process
  after backing up wanted test data. In-place update/data migration remains unresolved.

This is a documentation checkpoint only. The tested source above is distinct from
the documentation commit. No game, HUD, input, workflow or signing code changes,
new APK, rebuild or reinstall are required.
