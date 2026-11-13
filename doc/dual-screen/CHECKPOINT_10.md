# Checkpoint 10: build 13 needs and deduplication pass Thor checks

Recorded: 2026-11-13.

Status: accepted for continued incremental development based on the owner's
build 13 report. All five reported categories pass; no defects were reported.
Widget order remains a deferred layout concern, not a failed acceptance item.
This is acceptance of the bounded needs/deduplication increment, not a claim of
exhaustive widget coverage, final layout, or a release-ready application.

## Tested build

- Build: 13; experiment: `needs_status`; signing: `persistent`.
- Tested source: `35ef6dd4e21983d71637c7d26275bcb57438b976`.
- Source checkpoint branch: `checkpoint/needs-status-13` at that exact revision.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43477256421
- Artifact: `CDDA-DS-arm64-test-13`, ID `14064351408`.
- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Application ID: `io.github.mrchimpy.cddads.experimental`.

The preceding CI/log-and-package review reported all 191 host/fixture tests
passed, the three overlays applied in order, successful Android Java/native
compilation, and successful package/signing checks. That review also reported
local artifact-integrity, certificate-identity, packaged-asset, and generated-source
hash checks. Full signature verification was performed in CI; the local certificate
extraction checked identity, not the whole signature. This documentation update
does not rerun or independently repeat those build/package checks.

The device results below are the owner's observations, not assistant-operated
hardware tests or conclusions inferred from CI.

## Owner-reported results

| Category | Result | Observation |
|---|---|---|
| Needs descriptions | PASS | Hunger, Thirst and Rest refresh in sync with the upper Needs panel. Eating, drinking and sleeping changed the descriptions on both displays in sync. |
| Blank-state handling | PASS | The lower display uses a dash for blank upper descriptions. Transitions between descriptive text and blank/dash states work properly. |
| Deduplication and layout | PASS for the approved scope | The owner reports the needed widgets are represented across the two screens without duplication, aside from the current widget-order concern. This accepts the requested nine-row display deduplication; it is not an audit of every possible game widget. |
| Retained readings | PASS | Other readings continue updating correctly. Body comfort/trend, oxygen and worn clothing remain visible on the lower screen. |
| Presentation, input and lifecycle | PASS | Owner reports the combined category passed with no additional notes. No new timing measurements, stress testing or extra controller-binding coverage are inferred. |

The new needs readings were exercised through real eating, drinking and sleeping,
not merely checked at character load. The report does not enumerate every severity
category, mutation-dependent needs rule or possible transition, so none is claimed.
Rest remains the native sleepiness description, separate from Weariness.

## What this checkpoint accepts

- Three persistent active-game labels: Hunger, Thirst and Rest. Native descriptive
  values update, valid blanks become labeled dashes, and state transitions match
  the upper panel in the exercised cases.
- Removal from the lower view of exactly Time, Date, Place, Wield, Style, Weather,
  Lighting, Wind and environmental Temperature. Their native upper widgets and
  existing captured values were not deleted or redefined.
- Body comfort and Comfort trend remain distinct from removed environmental
  Temperature. The six worn summaries remain distinct from removed Wield/Style.
- The inherited black background, game-derived font, readable scrolling and
  existing input/lifecycle behavior pass the owner's regression category.

## Working screen allocation and deferred decisions

The owner used CDDA's built-in panel configurator, without another compile, to
retain both small maps, Env (including its Wield/Style fields), the directional
compass and name/count legend, vehicle panel and log upstairs. The owner reported
that the resulting log capacity is satisfactory in the observed on-foot layout.
Vehicle-layout evaluation is explicitly deferred; no estimate of its additional
height is treated as a measured result.

The current lower HUD remains the character/status view. Needs can now be disabled
upstairs through the same native configurator for normal play, with temporary
re-enabling retained as a comparison aid. This documentation does not change or
save any upper-sidebar configuration, and does not establish a separate
Needs-disabled refresh/persistence test unless the owner reports one.

Widget order, possible tabs, font-size tuning, state-dependent colors and later
interactive/full-overmap work remain separate discussions. Both small maps and
the compass/legend remain upstairs in this working arrangement; lower-screen
copies are not prerequisites for this configuration. No new feature or layout
implementation is authorized by this acceptance report.

## Coverage limits carried forward

Earlier untested cases remain open unless specifically exercised and reported:
bionic-power behavior, long on-device clothing names, layering/uncovered clothing,
clothing-driven comfort changes and nonblank trends, the final full-oxygen
meter-to-dash transition, alternate knowledge/unit cases, and variable anatomy.
Wielded-item-name wrapping is historical coverage for earlier experiments; Wield
is intentionally absent from this lower view. No repair is inferred from any of
these coverage limits, and no complete/sidebar-equivalent semantics are claimed.

Persistent signing and the chosen fresh-install development workflow remain.
Back up wanted test data and settings; preserve official CDDA and signing secrets.
In-place update/data migration remains unresolved.

Documentation only. The tested source is distinct from this documentation revision.
No game, HUD, input, workflow, signing, widget-order or upper-configuration changes.
No new APK, rebuild or reinstall is required for recording this checkpoint.
