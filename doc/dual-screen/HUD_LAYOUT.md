# Experiment 10: compact body health and mixed-width reading order

Status: implemented; 28 new host tests pass. Actual Android compilation and Thor
visual/functional acceptance remain pending. No APK is produced by this PR.

Base: accepted build 13 (`needs_status`), source
`35ef6dd4e21983d71637c7d26275bcb57438b976`, documented at checkpoint 10.
This increment branches from documentation revision
`b0125838c9e0f2c7442c1d605c87b6bd3a76fbee`. The original `needs_status`
experiment and all prior stages remain unchanged and selectable.

## Approved layout

Keep the full-width stamina text and long progress bar exactly as before. Keep
the current font sizes, black background, shared Terminus/Unifont resolution,
white text, bar style/thickness, and a single continuous scrolling viewport.

The body section becomes three rows, each containing two label/bar cells:

| Left | Right |
|---|---|
| Head | Torso |
| Left arm | Right arm |
| Left leg | Right leg |

The six original health indices, proportional calculations and progress scales
are unchanged. Labels remain on the same line as their bars, with complete names.
All health labels use one measured width; bars take the remaining cell width.
Each column receives equal space with the established 12-dp inter-column gutter.
There is a 4-dp label/bar gap and a 64-dp minimum useful bar-width target before
switching a pair to vertically stacked cells on a narrow display. No numerical HP
or new body parts are exposed, and left/right are never mirrored.

Below body health, the approved order is:

| Order | Arrangement |
|---|---|
| 1 | Pain, full width |
| 2 | Oxygen / Sound |
| 3 | Movement mode, full width |
| 4 | Speed / Focus |
| 5 | Strength / Dexterity |
| 6 | Intelligence / Perception |
| 7 | Hunger, full width |
| 8 | Thirst, full width |
| 9 | Rest / Mood |
| 10 | Weariness / Activity |
| 11 | Transition / Weary Malus |
| 12 | Body comfort, full width |
| 13 | Comfort trend, full width |
| 14 | Bionic Power, full width |
| 15-20 | Worn head, torso, arms, hands, legs and feet, all full width |
| Last | Existing snapshot/font diagnostic footer |

These descriptions are documentation, not new on-screen section headings or blank
spacer rows. At widths that support the pairs, body health saves three rows and
the Oxygen/Sound and Rest/Mood pairs save another two. Five fewer single-line rows
is not a guarantee that all content fits without scrolling; wrapping, fallback,
font rendering, and real device geometry determine the final footprint.

## Width handling and readability boundaries

`StablePairRow`, a private UI-only helper, uses equal-weight cells when there is
room. The text probes are measured through the actual TextView Paint after the
shared font and existing sp size have been assigned. Complete fixed labels and
conservative sample values are used, including `Unavailable` for the added status
pairs. The width requirement is fixed for that Presentation, not recalculated from
changing gameplay values. This avoids shifting fields when a dash becomes text.

A constrained width below the pair requirement stacks its two cells left first,
then right, at full width. Returning to sufficient width restores the pair.
Existing attribute/exertion pairs use the same width-only safety fallback. There
is no automatic font shrinking, single-line enforcement, ellipsis, horizontal
scrolling, or value-dependent hiding. Long descriptions (including clothing,
Hunger and Thirst) are always full width and may wrap vertically as before.

The probes are layout budgets, NOT game thresholds or a proof that every future
modded/localized string fits one line. Unexpectedly long paired text may still
wrap rather than be truncated. Current normal and fallback-font appearance must
be judged on the Thor. Host modeled widths cannot establish real glyph geometry.
No general fixed-cell map renderer, tab system or interactive controls are added.

Android APIs used:
- https://developer.android.com/reference/android/graphics/Paint#measureText(java.lang.String)
- https://developer.android.com/reference/android/widget/LinearLayout.LayoutParams

## Scope and provenance

Explicit selector: `hud_layout`. The workflow applies the unchanged body-details,
presentation and needs stages, then `apply_hud_layout.py`. That final stage changes
only generated `DualScreenHud.java`, guarded by its exact accepted build-13 hash
plus five unchanged native/decoder/font-helper hashes. Unsafe/symlinked paths,
ambiguous/missing anchors and repeat application are rejected before source writes.
There is no production fixture or hash-bypass setting.

All 20 currently displayed widget readings and all 36 TextViews are preserved.
Snapshot shape, indices, native capture/JNI and decoder logic are unchanged.
Date, Time, Place, Weather, Lighting, Wind, environmental Temperature, Wield and
Style remain absent downstairs. Body comfort/trend and the six worn summaries
remain present. The upper sidebar/configuration is untouched.

The reordered mixed readings share a `details` container, so waiting/menu/error
states clear their values and hide them together. Only container visibility names
change in render/clear code; the reading/bar update expressions are byte-identical.
Display selection, 250-ms polling, touch handling, focus flags and lifecycle code
are unchanged. Signing, app identity, caches and workflow permissions remain intact.

Apply provenance in order: `BODY-DETAILS.patch`, `HUD-PRESENTATION.patch`,
`NEEDS-STATUS.patch`, `HUD-LAYOUT.patch`. The last JSON report supersedes ONLY the
final HUD Java hash; the needs/native/decoder reports and font-helper hash remain
valid. The existing packaged-font check also runs for this selector.

## Validation actually performed

All 28 new host tests passed. They cover exact build-13 parent identities,
single-target output/provenance, rejection guards, unchanged native/decoder/font
files, unchanged stamina setup, unchanged rendering/clearing expressions, and
unchanged outer polling/lifecycle/display routing.

Production HUD Java, its decoders and font helper compile with
`javac --release 8 -Xlint:all,-options -Werror` against host Android substitutes.
Seven executed scenarios cover normal, blank, unavailable, long descriptions,
changing readings, larger modeled glyph widths and emergency font fallback.
They verify the complete visual order, 36 text elements, seven bars, all six health
mappings using deliberately different values, fixed label widths, full-width long
fields, exact hidden slots, pair-width boundaries/recovery/padding, equal weights,
no repeated layout mutation, no value-driven rearrangement, preserved font sizes,
black backgrounds, and inactive/unready/invalid/reloaded states.

The new fixture privately extends a copy of the earlier Android substitutes;
the accepted fixture is unchanged and its Git blob is checked. These checks are
API-call and layout-policy tests, NOT genuine Android measurement/rendering,
font loading, scrolling, controller routing or hardware lifecycle tests.

Local input files were reconstructed from the build-13 artifact patches and
matched every required production SHA-256. Tests explicitly selected them with
`DS_LAYOUT_PARENT_FIXTURE`; no hashes were overridden. Without that setting,
CI derives those same six inputs from the existing overlay generators. The earlier
191 tests were not rerun locally. CI should discover 219 tests total.
Workflow YAML, all ten Bash blocks and Python syntax passed local checks.

## Build and Thor acceptance

After review/merge into ds-dev, start a NEW CDDA-DS Android test run:

| Setting | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `hud_layout` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

Preserve signing secrets and official CDDA. Continue fresh test-app installs after
backing up wanted saves/settings, including the tuned upper-sidebar configuration.
In-place update/data migration remains unresolved.

1. Stamina retains its full-width bar, percentage/current/max text and size.
2. Head/Torso, left/right arms and left/right legs form three rows at normal Thor
   settings. Check complete labels, column gutter and useful bar lengths. Damage
   distinct parts on a disposable character and confirm the matching bar updates.
3. Verify the exact order above and every retained reading. Check longer Rest,
   Oxygen and Mood states where practical; Hunger/Thirst, Pain, Movement mode,
   comfort/power and clothing retain full-width space and can wrap without clipping.
4. Confirm the nine deduplicated fields remain absent, no empty rows/extra headings
   appear, and every row/footer is reachable. Do not require a no-scroll fit.
5. Repeat blank-state transitions, sidebar parity, simultaneous lower swiping/upper
   joystick input, sleep/resume, app switching, menu clearing and reload. The
   expected font diagnostic remains `Font: Terminus + Unifont`.
6. Narrow-width/larger-text fallback is an additional check, not a requirement to
   change preferred device settings permanently. Record unexercised cases honestly.

Vehicle tests, anatomy, state-dependent color fidelity, additional coverage gaps,
buttons/tabs and the full lower overmap remain deferred. No acceptance is inferred
from compilation or host checks; owner device results are required.
