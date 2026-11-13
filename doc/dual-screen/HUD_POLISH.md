# Experiment 12: left health labels, percentage-only stamina and reading placement

Status: implemented; 25 new local host tests pass. Full Android compilation and
Thor acceptance remain pending. No APK is produced by this PR.

Base: build 15 (`hud_refinement`), source
`4a85d5947eb058bb7651c6378f54108bb68e3e6c`.

## Owner feedback and approved scope

Build 15 passed the owner's Thirst/Hunger layout, description-transition,
blank/dash, no-clipping and stable-column checks. Other readings, deduplication,
font identification, input and lifecycle passed in the reported exercised cases.
Health-label alignment was functional but visually disliked; stamina was working
but its displayed current/maximum suffix was no longer wanted. These are user
reports, not assistant-operated hardware tests. No unreported extreme-state or
fresh damage/healing coverage is inferred from the photograph.

Four presentation changes are approved:

1. Restore the original left-aligned six body-part labels in their existing
   equal-width boxes. Keep full names, bar geometry, labels beside bars, shared
   label widths, inter-column gutter and 4-dp label/bar margin. Do not add literal
   spaces. The six names/indices and the three health pairs are unchanged.
2. Show stamina as `Stamina: 100.0%` (example) plus the unchanged long full-width
   bar. Remove only the `(current / maximum)` text. Preserve one-decimal rounding,
   raw captured values, percentage calculation, progress calculation and font size.
3. Pair **Movement mode on the left / Sound on the right** immediately after Pain.
   Remove the former Oxygen/Sound row without leaving a spacer.
4. Move **Oxygen** to a full-width row immediately after Comfort trend and before
   Bionic Power. Keep its existing values, symbolic presentation and blank rules.

The diagnostic heading changes to `CDDA-DS / HUD POLISH`. All 20 displayed widget
readings, 36 TextViews and seven bars remain. The nine previously deduplicated
readings remain absent. The successful Thirst-left/Hunger-right row is unchanged.
No font sizing, color, spacing, input, capture or upper-sidebar redesign is added.

## Explicit deferred item: body-part label/bar spacing

The user explicitly requested that this may be revisited later. Restoring left
alignment prioritizes consistent text starts and aligned bar starts; shorter
labels necessarily leave more visible trailing whitespace in equal-width boxes.
This tradeoff is accepted temporarily, NOT a claim that uniform visible gaps
have been solved. No literal space-padding workaround is introduced. Revisit the
body-label/bar spacing as a separate future layout decision.

## Reading order

Stamina text and its full-width bar remain first, followed by Head/Torso,
Left arm/Right arm and Left leg/Right leg in three paired health rows.

| Order | Arrangement |
|---|---|
| 1 | Pain, full width |
| 2 | Movement mode / Sound |
| 3 | Speed / Focus |
| 4 | Strength / Dexterity |
| 5 | Intelligence / Perception |
| 6 | Thirst / Hunger |
| 7 | Rest / Mood |
| 8 | Weariness / Activity |
| 9 | Transition / Weary Malus |
| 10 | Body comfort, full width |
| 11 | Comfort trend, full width |
| 12 | Oxygen, full width |
| 13 | Bionic Power, full width |
| 14-19 | Worn head, torso, arms, hands, legs and feet, all full width |
| Last | Existing snapshot/font diagnostic footer |

These are documentation groups, not additional visible headings or spacer rows.
Moving Oxygen down and pairing Movement/Sound shifts the intervening readings up
one row but does not itself reduce the total row count. Existing scrolling stays.

## Width policy and scope

Movement/Sound uses the unchanged width-only `StablePairRow`. Fixed probes are
`Movement mode: crouch (C)` and `Sound: -2147483648`, measured using the existing
font and size. The pinned movement definition includes walk, run, crouch and prone;
its Git blob is checked before source mutation. Empty movement text is still
rendered as Unknown by the unchanged decoder. Current English mode strings and
Unknown fit the modeled budget. No value-driven rearrangement, font shrinking,
ellipsis or truncation is added. Unexpected longer text can wrap. Narrow widths
stack Movement first, Sound second; actual Thor fit still requires a device test.

Explicit selector: `hud_polish`. Apply the unchanged body_details,
hud_presentation, needs_status, hud_layout and hud_refinement stages, then
`apply_hud_polish.py`. Earlier experiments and their tests stay unchanged.
Only generated `DualScreenHud.java` changes in this final overlay. Its exact
build-15 hash, five native/decoder/font-helper hashes, movement JSON identity and
unique anchors are validated before writing. Wrong/missing files, ambiguous
anchors, unsafe paths, symlinks and repeat application are rejected.

Provenance order ends `HUD-LAYOUT.patch`, `HUD-REFINEMENT.patch`, `HUD-POLISH.patch`.
`HUD-POLISH.json` supersedes only the final HUD Java hash. Capture/JNI, raw values,
snapshot shape, decoders, fonts, polling, focus and lifecycle remain unchanged.
The workflow only adds the selector/case and extends packaged-font verification;
manual dispatch, ds-dev gate, baseline default, permissions, signing and caches stay.

## Validation performed and limits

All 25 new local host tests passed. Production HUD/decoder/font-helper Java compiled
with `--release 8 -Xlint:all,-options -Werror` against Android API substitutes.
Eight executed scenarios cover normal, blank, missing, long text, changing values,
larger modeled text, emergency font fallback and stamina boundaries. Checks include
complete reading order and mapping, no padding/shortened names, equal health label
boxes/bar margins, independent HP mapping, percentage-only stamina with unchanged
raw values/math/rounding, Oxygen placement, movement/Sound pairing, all pinned mode
strings plus Unknown, width boundaries/stacking/recovery, retained Thirst/Hunger,
no value-driven rearrangement, no missing/duplicate readings, menu/error clearing
and restoration. Static reversal limits production changes to the four approved
edits and title. Patch application/reversal and input rejection tests passed.
Workflow YAML and all ten Bash blocks passed syntax checks.

Tests reuse the unchanged layout/presentation substitute files, checking their
Git blob identities. Only a temporary emitted TextView substitute receives an
alignment-call spy. Local build-15 inputs were reconstructed from artifact patches
and matched all six production hashes. `DS_POLISH_PARENT_FIXTURE` selects those
inputs for tests only; CI normally renders the parent using unchanged generators.
No production hash bypass is added. The previous 240 tests were not rerun locally;
CI should discover 265 tests total. These are API-call/layout-policy tests, NOT
Android rendering, precise glyph geometry, real needs simulation or hardware
input/lifecycle tests. Full Android compilation and Thor acceptance are pending.

## Next build and device checks

After review and merge, run CDDA-DS Android test on `ds-dev` with
`experiment=hud_polish`, `signing_mode=persistent`, and caches enabled.
Continue the established fresh test-app install after backing up wanted saves and
settings, including the tuned upper sidebar. Keep official CDDA and signing
secrets unchanged; in-place update/data migration remains unresolved.

Check left-aligned full health labels and aligned bars (variable trailing gaps are
expected); percentage-only stamina with unchanged long bar; Movement-left/Sound-right
through supported movement changes; Oxygen below Comfort trend and above power;
unchanged Thirst/Hunger, remaining readings and deduplication; footer reachability;
simultaneous swipe/joystick input, sleep/resume, app switch, menu clearing and reload.
Record unexercised cases as untested. Vehicle, variable anatomy, state colors,
tabs/buttons and the full lower overmap remain outside this increment.
