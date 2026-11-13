# Experiment 13: native colors and a paired comfort row

Status: implemented; 38 new local tests pass. Full Android compilation and Thor
acceptance are pending. This increment does not include a prebuilt APK.

Base: build 16 (`hud_polish`), source
`6434ddf99a5dce572e460d7cd8ee45ee5c082220`. The owner subsequently confirmed all
build-16 input/lifecycle checks passed as well as the reported layout/readings.
Those are owner-operated device tests, not assistant-operated hardware tests.

## Approved scope

Pair Body comfort on the left with Comfort trend on the right. Fixed probes are
`Body comfort: Comfortable` and `Comfort trend: (Falling!!)`. Keep the current font
sizes, width-only stacking fallback, black canvas, stamina percentage and long bar,
three paired health rows, all other reading order, nine-field deduplication,
clothing summaries, upper sidebar, input/focus/polling and lifecycle behavior.
Oxygen follows the comfort pair and still precedes Bionic Power. No new headings,
blank spacer rows or font-size reduction are added. One row is saved when paired.

Restore native color information throughout retained gameplay readings. This is
not an Android-only layout patch: the copied-state bridge now carries resolved
colors as well as values. No gameplay rules, thresholds, JSON definitions, source
palette, original widgets, or game-input machinery are changed.

## Color authority and inventory

The engine remains the authority. Copies of native number widgets evaluate their
own `set_default_var_range`, `get_var_value`, and `value_color` methods. Descriptive
widgets are rendered once using the already-selected widget's `show()` output.
The existing plain text is retained, while the native markup is parsed into colored
runs. No threshold/description-to-color table is implemented in Java.

| Lower reading | Native source |
|---|---|
| Stamina fill and percentage | `stamina_graph_classic` native value color |
| Six HP fills | Corresponding `hp_*_graph_no_label` widgets |
| Six full body-part names | First visible glyph style from corresponding `bodypart_*_status_text` |
| Strength, Dexterity, Intelligence, Perception | `str_num`, `dex_num`, `int_num`, `per_num` |
| Speed and Focus | `speed_num`, `focus_num` |
| Movement name and letter | `move_mode_letter` style; existing name/letter text retained |
| Weariness, Activity | `weariness_desc`, `activity_desc` styled output |
| Transition, Weary Malus | `weariness_transition_graph`, `weary_malus_desc` |
| Pain | `pain_desc_label` |
| Thirst, Hunger, Rest | `thirst_desc_label`, `hunger_desc_label`, `sleepiness_desc_label` |
| Mood | `mood_desc_label` |
| Body comfort and Comfort trend | `body_temp_desc_label`, `body_temp_delta_desc_label` |
| Oxygen | `oxygen_graph_classic`, with unchanged native full-oxygen suppression |
| Bionic Power | `power_desc` |
| Sound | `sound_num`; no invented dynamic loudness coloring |
| Six worn summaries | Existing `bp_armor_outer_*_text` output, including multiple colored runs |

The selected compact native widgets are the comparison target, not arbitrary
custom sidebar layouts. Labels added by this HUD are neutral native light gray;
values receive native styling. Body-part labels are the exception because the
label itself communicates a condition. Their condition color/background is
independent of the bar's HP color. Full English names and left alignment remain.
Native background highlights are retained, not collapsed into one foreground.

RGB comes from the running game's resolved `nc_color`, `colorpairs` and
`windowsPalette`, using the same foreground/background bright-index rules as
`catacurses::wattron`. Configured native remappings/base palette values therefore
travel with the frame. Android generic green/red colors and smooth gradients are
not substituted. The target is the same native color decisions and RGB values,
not pixel-identical rendering between two different screens/renderers.

HP and stamina use the engine's actual five-color mapping, including the native
12.5/37.5/62.5/87.5-percent boundaries for these pinned positive-maximum widgets.
The underlying value, not the rounded stamina percentage, selects the color.
Numeric attribute colors remain base-relative; Speed and Focus retain their
separate native rules. The tests cover boundaries of the actual pinned evaluator.

Bar fill and geometry remain proportional. At exactly zero, the empty track uses
the native graph foreground color so the warning remains visible, analogous to
native colored empty graph glyphs; progress remains zero, never a fabricated sliver.
Nonempty tracks use native dark gray. Device acceptance must judge this zero-state
adaptation of a text graph into a graphical bar.

Valid blank descriptions retain the accepted neutral dash. Missing widgets retain
neutral `Unavailable`. No positive status or severity is inferred from a blank.
Malformed/unsupported color information preserves valid plain readings, resets
styling to neutral, and adds a diagnostic warning rather than retaining stale colors.

## Data and integration boundaries

The unchanged `long[53]` numeric fields and `byte[30][]` plain UTF-8 text arrays
remain the first two members of the JNI result. A third `long[]` carries versioned
`DSC1` color metadata: snapshot sequence, readiness/completeness, neutral/track colors,
20 scalar foreground/background pairs and colored runs for 29 native widget slots.
Only the existing 20 widget slots remain visible. Colors and readings are published
and copied together under the existing mutex; Android never reads live game objects.

Native runs use UTF-8 byte offsets; the Java decoder validates them and converts to
UTF-16 offsets, including supplementary characters. Lengths, color alpha/ranges,
run continuity, code-point boundaries, version, sequence and trailing data are checked.
Nested tags are resolved by the native tag parser. Malformed tags do not become
rendered styling instructions; capture verifies plain-text equivalence. Safety
limits are 64 KiB of marked text, 4096 runs per widget and 256 nested scopes.

The final overlay modifies generated `src/game.cpp`, `src/ds_hud.h`, `src/ds_hud.cpp`
and `DualScreenHud.java`, and adds `ds_hud_colors.h`, `ds_hud_color_capture.h` and
`NativeHudColors.java`. Core/status value decoders and the font helper stay unchanged.
No upstream source is committed directly: the manual build applies guarded overlays.
Exact parent inputs, 28 definition/source identities, template bytes and unique
anchors are checked before writes. Earlier experiments and their tests are unchanged.

Select `native_colors`: body_details -> hud_presentation -> needs_status ->
hud_layout -> hud_refinement -> hud_polish -> native_colors. Provenance ends with
`NATIVE-COLORS.patch` and `NATIVE-COLORS.json`; later reports supersede affected
source hashes, not unrelated earlier hashes. The manual workflow adds only the
selector/case and packaged-font check; signing, permissions, caching and ds-dev gate
remain unchanged. No merge or build dispatch is performed by this increment.

## Validation performed and limitations

All 38 new local tests passed. Production HUD/decoder/font-helper Java compiles
with `--release 8 -Xlint:all,-options -Werror` against host Android API substitutes.
Production native mailbox/JNI code compiles as a host shared library and is called
from Java. Native color-capture helpers compile against substitute game objects.
The exact pinned `widget::value_color` function is extracted, hash-checked and
compiled, with colors inherited from the packaged widget definitions.

Tests cover full UI inventory/order, comfort widths and fallback, independent HP
and condition styling, native scalar boundaries, unrounded stamina color selection,
mixed text colors/backgrounds, UTF-8/UTF-16 handling, custom resolved RGB, direct
recovery, blanks/missing states, menu/waiting clearing, immutable copies, concurrent
mailbox coherence, malformed extension fallback, zero bars, and font fallback.
Overlay guards, seven changed integration targets and patch forward/reverse roundtrip
pass. Four native scenarios also pass AddressSanitizer/UndefinedBehaviorSanitizer.
Workflow YAML, all ten Bash command blocks, Python syntax and whitespace pass.

Local parent fixtures reconstruct six exact generated sources from build-16 artifact
patches plus a focused game-hook fragment; all six production hashes match. Synthetic
apply() unit fixtures mock only their own expected identities. There is no production
hash bypass. In CI the parent is generated through the unchanged earlier stages and
all nine production parent hashes are checked. Native JSON expressions/full gameplay,
real Android rendering, physical color matching, actual touch/controller focus, and
hardware lifecycle are not simulated by these fixtures. The previous 265 tests were
not rerun locally; GitHub should discover 303 tests total. Full Android compilation,
package/signature review and subsequent Thor acceptance remain pending.

## Device comparison and deferred work

After review/merge, manually build `native_colors` on `ds-dev` with persistent
signing and caches enabled. Continue the established fresh test-app installation
process after backing up wanted saves/settings and upper-sidebar configuration.
Leave official CDDA and signing secrets unchanged; in-place data migration remains
unresolved. Temporarily enable matching native upper panels for color comparisons.

Compare penalties/bonuses and recovery, independently damaged limbs, limb condition
foreground/background, stamina depletion/recovery including zero, descriptive needs,
activity/weariness, comfort/trend, oxygen, mood/power and multicolored worn items as
practical. Do not force dangerous/extreme states just to finish a checklist; record
unexercised states as untested. Check the comfort pair's longest available descriptions,
all retained rows, scrolling, simultaneous lower swipe/upper joystick, sleep/resume,
app switching, menu clearing and reload. A native-color warning in the footer is a
reportable degraded state, not a successful native-color match.

Body-label/bar spacing and Oxygen's final placement remain provisional. Font/footer
cleanup near alpha, variable anatomy, interactive tabs/buttons, full lower overmap,
and vehicle migration remain deferred. No new design work is bundled into this pass.
