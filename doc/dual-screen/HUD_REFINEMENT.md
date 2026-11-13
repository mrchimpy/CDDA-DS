# Experiment 11: uniform health-label gaps and paired basic needs

Status: implemented; 21 new local host tests pass. Full Android compilation and
Thor acceptance are pending. No new APK is produced by this PR.

Base: build 14 (`hud_layout`), source
`2e447e538c00266e3f02754f7603497f82216839`.

## Owner feedback and approved scope

The owner reported build-14 passes for stamina, metric order and stable columns,
long descriptions/scrolling, retained readings/deduplication, and presentation,
input and lifecycle. The supplied photos show the three health pairs fitting and
the footer remaining accessible. The owner flagged unequal visible gaps between
health-label text and progress bars, especially left versus right limb names.
A separate build-14 damage/healing mapping test was not explicitly reported.
These are owner observations, not assistant-operated hardware tests.

Only two gameplay-presentation changes are approved:

1. Right-align the six body-part labels inside their existing common-width boxes.
   Keep those box widths, bar widths/starts, 4-dp label/bar margin, paired-row
   gutter, progress scales, label text and font sizes unchanged. Short names such
   as Head start farther right, an explicitly accepted tradeoff. Other text keeps
   its existing alignment. This fixes trailing alignment, not by shortening names
   or moving individual bars. Exact visual appearance still requires a Thor check.
2. Put **Thirst on the left and Hunger on the right** of one paired row in their
   existing needs section, before Rest/Mood. This saves one additional row when
   there is room, without moving any other reading or changing any value.

The diagnostic title becomes `CDDA-DS / HUD REFINEMENT` to identify the experiment.
All 20 displayed widget readings, 36 TextViews and seven progress bars remain.
The nine previously deduplicated fields remain absent. Stamina retains its long,
full-width bar and percentage/current/max text. Clothing and the other previously
full-width descriptions remain full width, except the expressly approved needs
pair. No section headings or empty spacer rows are introduced.

## Width policy

The unchanged `StablePairRow` measures the fixed probes `Thirst: Very thirsty` and
`Hunger: Near starving` with the resolved font and existing size. These are the
longest complete English label/description combinations in the pinned definitions
(20 and 21 characters). `Unavailable` and the blank-state dash are shorter. Both
JSON definitions are hash-checked before application; tests enumerate their
native descriptions rather than looking only at neutral/dash values.

The existing width-only stacking fallback remains: Thirst first, Hunger second
when narrow, then equal-width columns when sufficient width returns. Changing
needs descriptions does not trigger rearrangement. There is no shrinking,
ellipsis, single-line enforcement or new value-dependent layout policy.
Unanticipated long text can wrap; alternate fonts, translations, modified widget
content and real display geometry are not guaranteed by modeled host widths.

Right alignment uses `TextView.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL)`
only on the six existing English body labels. This does not introduce a generalized
RTL/localization redesign. API reference:
https://developer.android.com/reference/android/widget/TextView#setGravity(int)

## Integration and provenance

Explicit selector: `hud_refinement`. Apply the unchanged stages in order:
`body_details`, `hud_presentation`, `needs_status`, `hud_layout`, then the new
`apply_hud_refinement.py`. Earlier selectors and their files stay unchanged.

Only the generated `DualScreenHud.java` changes in the final stage. Its exact
build-14 hash, five unchanged native/decoder/font-helper hashes, two needs JSON
blob hashes and unique edit anchors are checked before the source write. Unsafe
paths, symlinks, wrong/missing inputs and repeat application are rejected.
No production fixture override or hash bypass is added.

`HUD-REFINEMENT.patch` follows `BODY-DETAILS.patch`, `HUD-PRESENTATION.patch`,
`NEEDS-STATUS.patch` and `HUD-LAYOUT.patch`. `HUD-REFINEMENT.json` supersedes only
the final HUD Java hash. Capture, JNI, snapshot shape, decoding, font loading,
refresh, display routing, input and lifecycle code remain unchanged.

The workflow adds the selector/case and extends existing packaged-font checking.
Manual-only dispatch, ds-dev restriction, baseline default, permissions, toolchain,
signing and caching are unchanged. Upper-sidebar settings are not modified.

## Validation actually completed

All 21 new host tests passed. The production Java HUD, decoders and font helper
compile with `--release 8 -Xlint:all,-options -Werror` against Android API substitutes.
Seven executed scenarios cover normal, blank, missing, long, changing, larger
modeled text and fallback-font cases. They check all retained/absent readings,
full visual order, independent health mapping, all six right-alignment calls,
unchanged non-health alignment, fixed label widths and bar margins, and the new
needs pair including all combinations of pinned descriptions and the unavailable
width case. Width-boundary/stacking/recovery, no value-driven rearrangement,
menu/unready/error clearing and reload are also exercised.

The new tests extend temporary copies of the earlier layout harness and emitted
Android substitutes; all three earlier support files are byte-identical and
hash-checked. Static checks prove the only production differences are the two
approved edits and diagnostic title. Rejection guards and single-target staged
provenance are tested. Workflow YAML and all ten Bash blocks pass syntax checks.

Local parent inputs were reconstructed from the build-14 artifact patches and
matched every required production SHA-256. `DS_REFINEMENT_PARENT_FIXTURE` selects
these exact files in local tests, without overriding hashes. CI otherwise derives
the same parent from the existing generators. These tests are API-call and
layout-policy checks, not genuine Android rendering, glyph-edge measurement,
scrolling, device focus/lifecycle tests or a full needs simulation.

The prior 219 tests were not rerun locally. CI should discover 240 tests total.
Full Android compilation and Thor visual/functional acceptance remain pending.

## Build and acceptance

After review and merge, start a NEW CDDA-DS Android test run:

| Setting | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `hud_refinement` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

Continue fresh test-app installs after backing up wanted saves and settings,
including the tuned upper sidebar. Preserve official CDDA and signing secrets.
In-place update/data migration remains unresolved.

Check the six visible label-to-bar gaps, retained aligned bar starts/lengths,
full stamina bar and unchanged font. Check Thirst left/Hunger right at normal Thor
settings, longer descriptions when available, dash/text transitions and absence
of value-driven column changes. Confirm all rows/footer remain reachable and
repeat retained-readout, simultaneous swipe/joystick and lifecycle checks.
Record unexercised extreme descriptions, narrow/large-font behavior and separate
health damage/healing coverage as untested rather than inferring them from photos.

Vehicle, variable anatomy, state-dependent colors, tabs/buttons, full overmap and
earlier untested semantic cases remain outside this refinement.
