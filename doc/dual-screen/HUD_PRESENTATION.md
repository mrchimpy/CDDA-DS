# Experiment 8: black background and consistent bundled game typography

Status: implemented; 29 new local host tests pass. Android compilation and Thor
visual/functional acceptance remain pending. No new APK is produced by this PR.
This is a presentation-only increment, not the compass or final layout pass.

Based on documentation checkpoint `0c712da74aeadf6c23308bc1ff5543d9e67ee9d7`.
The accepted build-11 source remains `checkpoint/body-details-11` at
`f7e2d5700b7504a35d754a5b243036396521aeaa`. Selecting `body_details` still produces
the unchanged earlier presentation. All previous coverage gaps remain open.

## Approved change

- Use opaque black (`#000000`) for the lower Presentation window background,
  ScrollView viewport and content layout, including waiting/menu/error states.
- Use one resolved typeface throughout the lower HUD: title, stamina, body labels,
  core values, movement, all 26 widget rows (including Transition and Oxygen), and
  the diagnostic footer. No per-meter Android-monospace override remains.
- Preserve existing text sizes, padding, row grouping, white text, health/stamina
  progress bars, data decoding, refresh timing, controller routing and lifecycle.
  The gray rails of progress bars are unchanged; they are not the background.

No external artwork, icons or fonts, new metrics, tabs, visibility controls,
state-dependent color migration, or upper-sidebar removal are included.

## Font source and fallback

The pinned `data/fontdata.json` selects `data/font/Terminus.ttf` followed by
`data/font/unifont.ttf` for its default interface font. Both files already ship in
the APK assets. Load them from the APK AssetManager, not from a newly downloaded
font or a potentially uninitialized/extracted user-data directory. No font binary
or license text is modified, copied into a new source location, or added to Git.
The existing packaged fonts and license notices remain unchanged.

`HudTypeface` is resolved once per Presentation creation, not on every snapshot.
All TextViews receive the same resulting Typeface object. Letter spacing is zero;
ligature/contextual-ligature/kerning features are disabled for consistent symbol
sequences. This does not yet implement a character-cell map renderer.

On Android API 29 and above, the native custom-fallback API builds this order:
**Terminus -> Unifont -> system monospace fallback**. Font style comes from the
Terminus asset. If Unifont fails, keep Terminus with system glyph fallback. If the
custom chain cannot be created, retry ordinary Terminus asset loading. Android
API 24-28 uses that legacy loading path directly and system glyph fallback.
If Terminus cannot load at all, keep the HUD readable with Android monospace.
Failures are logged, not turned into gameplay actions or focus-requesting dialogs.

The footer identifies the chosen path in active, waiting, menu and error states:

- `Font: Terminus + Unifont` for the normal API-29+ chain.
- `Font: Terminus (system glyph fallback)` for the legacy/degraded chain.
- `Font: Android monospace (font fallback)` when Terminus could not load.

These identify the configured chain, not which font drew every individual glyph.
Fallback glyphs, particularly wide characters, need not have Terminus's cell width.
There is no claim of pixel-identical SDL/Android rendering or complete Unicode
coverage. CDDA requests Bitmap hinting; Android text sizing/rasterization can look
different even with identical font bytes. User-selected/custom upper-game fonts
are NOT tracked: this experiment matches the pinned default assets only.

Android API references used:
- https://developer.android.com/reference/android/graphics/Typeface
- https://developer.android.com/reference/android/graphics/Typeface.CustomFallbackBuilder
- https://developer.android.com/reference/android/graphics/fonts/Font.Builder
- https://developer.android.com/reference/android/graphics/fonts/FontFamily.Builder

## Build integration and provenance

New explicit selector: `hud_presentation`. The workflow applies the unchanged
`body_details` overlay first, then `apply_hud_presentation.py`. That second stage
checks the exact build-11 generated Java SHA-256, the helper template hash, bundled
font/config Git blob hashes, unique text anchors and safe destination paths before
writing either changed/new Android source file. Native source, transport fields,
Java decoders and all previous experiment scripts/templates are untouched.

Provenance is sequential: apply `BODY-DETAILS.patch`, then
`HUD-PRESENTATION.patch`. `BODY-DETAILS.json` describes the first stage;
`HUD-PRESENTATION.json` supersedes its DualScreenHud.java hash and adds the
HudTypeface.java hash. The base report's other seven integration hashes remain
valid. Do not compare the base UI hash to the final UI without the second report.

A conditional verification step opens the finished APK and checks the byte identity
of Terminus, Unifont and fontdata.json at their actual `assets/data/...` paths.
It writes `HUD-FONT-ASSETS.json`; this proves packaged asset identity, not rendering.
The workflow adds ten lines total: selector, two-stage dispatch and asset check.
Manual dispatch, default baseline, ds-dev gate, permissions, signing and caches are
unchanged. No new dependencies or Android minimum-version change are introduced.

## Validation actually completed

All 29 new host tests passed. They cover two-target overlay provenance, pinned
font/config/template/source guards, missing/changed assets, symlink/path checks,
repeat-application rejection, unchanged data/decoders, and packaged-font checking.

The generated production HUD Java, production font helper and unchanged decoders
compiled with `javac --release 8 -Xlint:all,-options -Werror` against small Android
API substitutes. Seven executed host scenarios check normal custom font selection,
missing Unifont, primary-font failure, custom/legacy builder failure, API gating,
and explicit emergency fallback. They walk all 42 TextViews through initial,
active, menu and invalid-snapshot states, checking a shared font, black background
calls, preserved sizes/white text, all rows/clearing, focus flags and no font reload
on repeated renders. These are API-call/logic tests, NOT Android rendering, genuine
font loading, scrolling or input-focus tests.

Local parent sources were reconstructed from the downloaded build-11 patch and
checked against its recorded SHA-256 hashes. The local test command explicitly
used `DS_PRESENTATION_PARENT_FIXTURE` for those generated files. CI without that
override uses the actual existing `apply_body_details.render_templates()` generator.
The expected parent UI hash must match in either path. The earlier 133 tests were
not rerun locally; the next CI run should discover 162 total.

Workflow YAML and all ten Bash blocks passed syntax checks. Actual Android SDK
compilation, native/Java integration and Thor visual/functional results are pending.
Host checks do not establish exact font appearance, glyph alignment or legibility.

## Build and device test

After review/merge into ds-dev, start a NEW CDDA-DS Android test run:

| Setting | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `hud_presentation` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

Keep persistent signing and the existing fresh-install process after backing up
wanted test data. Preserve official CDDA. Update/data migration is still unresolved,
as recorded in the original development handoff and later checkpoints.

1. Confirm a black background across all lower-screen areas while active, at the
   main menu, and after sleep/resume. Distinguish intentionally unchanged progress
   bar tracks from the background. Check viewport margins while scrolling.
2. Record the footer's font diagnostic. Compare the default game's typeface with
   the lower title, body labels, numbers, long text, footer and symbolic meters.
   Report tofu/missing glyphs, strange widths or excessive blur; do not assume a
   successful font load establishes visual acceptance.
3. Reach every row, including Worn feet. Test wrapping and two-column rows at
   normal Thor font size/DPI. Additional wrapping is possible; no automatic font
   shrinking has been added to hide it.
4. Recheck simultaneous lower swipe/upper joystick, earlier readings, sleep/resume,
   app switching, title-menu clearing and reload. Confirm no gameplay input change.

Do not mark this experiment accepted until the owner reports device results. Maps,
compass, themed pages, exact fixed-cell rendering, complete fonts/colors, anatomy,
remaining untested states and coordinated show/hide remain separate later work.
