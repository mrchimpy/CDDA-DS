# Checkpoint 7: environment-status HUD passes Thor functional acceptance

Status: accepted for this bounded increment based on the owner's build 9 device
report. All five reported acceptance categories pass. This does not establish full
sidebar migration, every knowledge/visibility condition, or exhaustive stability.

## Tested build

- Build: 9; experiment: `environment_status`; signing: `persistent`.
- Tested source: `5067a4cdba6cb1fdeab19ed899237568cd66f80d`.
- Source checkpoint: `checkpoint/environment-status-9` at that exact revision.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43395962054
- Artifact: `CDDA-DS-arm64-test-9`, ID `14022807525`.
- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Application ID: `io.github.mrchimpy.cddads.experimental`.

The preceding CI/log-and-package review reported 89 host/fixture tests passed,
eight integration targets applied to the pinned source, successful Android
Java/native compilation, and successful signing/package checks. The device results
below are owner-reported, not assistant-operated hardware tests or conclusions
from compilation. No build revalidation or new code execution is claimed here.

## Owner-reported device results

| Category | Result | Observation |
|---|---|---|
| Layout and scrolling | PASS | Wrapping, legibility and scrolling access to bottommost content work. Lower-screen swipes do not change upper-screen controller focus. The owner additionally swiped the lower screen while rotating the joystick; both screens behaved as intended simultaneously. |
| New readings | PASS | All new lower-screen metrics update in sync with the base game's upper sidebar. The exact location/weather/lighting/wind states exercised were not enumerated. |
| Time and character knowledge | PASS | With a smartphone and smartwatch in inventory, the clock showed exact time. Dropping both changed `8:02am` to `Morning`, matching the sidebar. |
| Temperature | PASS | Dropping the same two items changed `50F` to `-`, matching the reduced information available in the sidebar. |
| Previous readings and lifecycle | PASS | Owner reported the combined previous-readings/lifecycle category as all good. No additional per-subtest details were supplied in this report. |

The simultaneous swipe/joystick observation is useful evidence beyond a sequential
"touch below, then try the controller" check. It establishes that tested interaction
on this Thor; it is not a guarantee for future buttons, every controller binding,
all devices, or arbitrary concurrent interactions.

The item-removal tests establish observed parity when precise information becomes
unavailable, not only when instruments are present. Both devices were dropped
together: the report does not identify which item individually supplies each
capability, test every instrument type, or establish the pickup/restoration path.

## Remaining verification limits

- No explicit no-watch/no-sky `???` case was reported. The exact-to-approximate test
  passes; that separate unknown-time case remains untested by this report.
- The reported temperature case uses Fahrenheit. Alternate units, every thermometer
  capability and every equipment combination are not claimed as tested.
- No missing-widget `Unavailable` case was reported. The observed temperature `-`
  is legitimate restricted information, not evidence of a missing widget.
- Not all environmental states, custom sidebar variants, alternate fonts/DPI or
  long-play conditions were enumerated or established.
- General lifecycle and previous readings were reported as passed; do not invent
  additional timings, stress runs, binding coverage or detailed test sequences.
- This device report concerns build 9, not any later documentation revision.

## Retained scope and sequencing

- Continue incremental read-only information coverage. The original upper sidebar
  and viewport remain the comparison reference and are not removed.
- Scrolling is now owner-tested for the expanded stack, including access to its
  bottommost content. Keep text readable; do not shrink it to force a no-scroll fit.
- Bottom-edge tabs, context-themed pages and repeated readouts across pages remain
  ideation only. No page grouping, automatic page switching or gameplay controls
  have been approved or implemented by this acceptance.
- Preserve both maps in scope. Creature-name/count legend inclusion/presentation
  remains an open decision, not a silent deletion or an approved permanent panel.
- Variable anatomy, upstream color/display semantics and final layout completeness
  precede coordinated show/hide and upper-sidebar removal, in the agreed order.
- Preserve the corrected movement-mode observation: both displays share the
  observed next-turn refresh; no lower-only timing defect is reopened here.
- Fresh installs remain the owner's development process. Keep persistent signing
  and app identity unchanged; back up wanted test data before uninstalling only
  the test app. In-place update/data migration remains unresolved.

This is a documentation checkpoint only. It introduces no game, HUD, input,
workflow or signing changes. No new APK, rebuild or reinstall is required.
