# Checkpoint 6: activity-status HUD passes Thor functional acceptance

Status: accepted for this bounded increment based on the owner's build 8 device
report. All five reported acceptance categories pass. This does not establish full
sidebar migration, exhaustive state coverage, or extended gameplay stability.

## Tested build

- Build: 8; experiment: `activity_status`; signing: `persistent`.
- Tested source: `346e0bdc3a49efd83ff329a02cc55bef948a8285`.
- Source checkpoint: `checkpoint/activity-status-8` at that exact revision.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43387170510
- Artifact: `CDDA-DS-arm64-test-8`, ID `14018934153`.
- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Application ID: `io.github.mrchimpy.cddads.experimental`.

The preceding CI/log-and-package review reported 69 host/fixture tests passed,
eight overlay integration targets applied to pinned source, successful Android
Java/native compilation, and successful signing/package checks. Device observations
below are owner-reported, not assistant-operated tests or conclusions from CI.

## Owner-reported device results

| Category | Result | Observation |
|---|---|---|
| Layout and scrolling | PASS | All previous and new readings remain legible; all rows are accessible without clipping. The owner reports reaching the limit before scrolling becomes necessary. |
| Activity and weariness | PASS | Weariness, Activity, Transition symbols and Weary Malus match the upper sidebar; all were observed changing downstairs in sync with upstairs. |
| Pain | PASS | A dash appears when the owner observes no pain. Descriptions change in sync with the upper sidebar, using the correct text formatting. |
| Previous readings and controller focus | PASS | Owner reports no change from the previously passing behavior. |
| Lifecycle and clearing | PASS | Owner reports no change from the previously passing behavior. |

The owner supplied `IMG_20261112_235137.jpg`, showing both screens and the expanded
activity-status panel, with part of the creature-name list circled on the upper
sidebar. The photo supports static layout/readability and the illustrated state;
the dynamic changes and lifecycle results come from the owner's report. The photo
remains in the conversation and has not been published in the repository.

The exact weariness/activity states exercised were not enumerated. Do not turn this
report into a claim that all thresholds, missing-widget cases, alternate DPI/font
settings, or extended scrolling interactions have been tested. Upstream color
reproduction remains deferred: the current activity overlay strips color markup.
Pain's dash continues to mean valid blank widget output, not an independently
measured zero pain value. No missing-widget `Unavailable` case was reported.

## Layout sequencing retained

- The current presentation is at the owner's reported no-scroll space limit.
- Continue incremental information coverage before revising the final layout.
- Keep readings legible and reachable through the existing scroll fallback as
  necessary; reaching that fallback is not by itself a reason to shrink text.
- The owner has a minimap/layout idea but explicitly wishes to present it only
  after seeing all data brought over. No details or design decision are inferred.
- Both the small text/symbol map and separate pixel minimap remain in scope.
- Variable anatomy, layout completeness and coordinated lower-HUD show/hide and
  upper-sidebar removal remain deferred in the agreed order.

## Creature-name list: inclusion/presentation undecided

The owner highlighted the nearby NPC/monster name list and is ambivalent about
migrating it, because the directional compass already provides nearby-creature
awareness. The owner notes that the compass alone loses names/labels. This is a
note for later evaluation, not an instruction to remove the list from scope or to
implement a new layout/control now.

In the pinned `data/json/ui/compass.json`, the compass directions and the
`compass_legend_text` / `compass_legend_text_alt` widgets are distinct definitions;
the combined layouts include both. This provides a source-level separation for
later investigation, not proof that an optional/collapsible lower-screen UI already
exists. The circled list supplies explicit names and counts in the photograph;
the directional display and readable identification are related but not identical
information.

Keep the original migration scope as the reference while recording this open
decision. Do not silently discard creature-name/count information, assume permanent
visibility is required, or treat optional display as already approved. Revisit the
tradeoff when the data coverage and eventual layout can be evaluated together.
No compass/legend implementation or visibility controls are added by this record.

## Retained constraints and verification limits

- Read-only HUD; original upper sidebar and viewport retained.
- Preserve the corrected build 7 observation: both displays share the observed
  next-turn movement-mode refresh. No lower-only refresh defect is reopened here.
- Keep persistent signing and application identity unchanged; use the owner's
  fresh-install development process after backing up wanted test data.
- In-place updating/data migration remains unresolved; fresh installs do not test it.
- Standard six-part anatomy, complete colors and display semantics, remaining
  metrics, both maps, compass/legend decision and message log are not completed by
  this acceptance. No interactive gameplay controls or sidebar removal are added.

This is a documentation checkpoint. Its commit is distinct from the tested source
above. No game, HUD, controller, signing or workflow code changes are needed to
record these findings; no rebuild or reinstall is required.
