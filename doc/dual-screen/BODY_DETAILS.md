# Experiment 7: body comfort, oxygen and worn clothing/armor summaries

Status: implemented with 24 new local host/fixture tests passing. Full Android
compilation, actual engine evaluation and Thor acceptance remain pending. No new
APK is created by this PR. Do not mark these fields accepted before device results.

Builds on build 10 (`equipment_status`, tested source
`50474b61fd018ed46db61cfc6b253210ea3d1a7a`) and its documentation checkpoint
`2dbf3d871f6fa73adf4b74d4cc5846e522b16015`. Keep the rollback source
`checkpoint/equipment-status-10`. Its untested bionic-power behavior and long-item
wrapping are still open verification items, not silently resolved by this PR.

The owner explicitly requested the three groups in one iteration. Preserve all
previous health, stamina, core, activity, environment and equipment readings, and
the original upper sidebar/viewport. This remains an incremental read-only HUD.

## New information

Nine appended rows implement the three requested groups:

| Readout | Pinned game widget | Boundary |
|---|---|---|
| Body comfort | `body_temp_desc_label` | Native descriptive body-heat category, not environmental temperature. |
| Comfort trend | `body_temp_delta_desc_label` | Native rising/falling description; valid blank becomes a dash. |
| Oxygen | `oxygen_graph_classic` | Native five-character meter, subject to `oxygen_classic_layout` selection. |
| Worn head | `bp_armor_outer_head_text` | Existing Head outer-armor summary. |
| Worn torso | `bp_armor_outer_torso_text` | Existing Torso outer-armor summary. |
| Worn arms | `bp_armor_outer_arms_text` | Existing Arms summary; native definition uses `arm_r`. |
| Worn hands | `bp_armor_outer_hands_text` | Existing Hands summary; native definition uses `hand_r`. |
| Worn legs | `bp_armor_outer_legs_text` | Existing Legs summary; native definition uses `leg_r`. |
| Worn feet | `bp_armor_outer_feet_text` | Existing Feet summary; native definition uses `foot_r`. |

Definitions are in pinned `data/json/ui/{body_temp,oxygen,bodypart_armor}.json`
at `bb52239dee96df602da097f113382fe5c9a9c115`. The six clothing widgets bind to
`bp_armor_outer_text`; `src/widget.cpp` routes this to
`ava.worn.get_armor_display(only_bp())`. The HUD copies the resulting game-provided
text, including whatever item names, condition symbols or count summaries it
supplies. It does not enumerate a new inventory, calculate protection ratings,
aggregate left/right coverage, or claim that all worn layers are listed separately.
The grouped right-side representatives are inherited from the game, not a new
claim that both sides are identical. Variable anatomy remains deferred.

Body comfort and trend use the native JSON clauses, not independently maintained
thresholds. Existing environmental Temperature retains its separate meaning and
character-knowledge restrictions. Colors are stripped as in earlier experiments;
colored condition information is not yet reproduced by this text-only increment.

## Conditional oxygen without changing the original sidebar

The pinned `oxygen_classic_layout` selects its graph only when
`u_oxygen_max() != u_oxygen()`. Capture reads that layout's conditional child list
through `widgets(true)` on a local copy, then renders a local copy of the graph
with the existing `show(u, 80)` path. It does NOT call the layout renderer, which
updates shared height bookkeeping, or reimplement an oxygen threshold/formula.

- No selected child: oxygen is available but its text is blank. The temporary lower
  row stays present with a dash, while the upper sidebar may omit the oxygen panel.
  This is deliberate temporary row presentation, not an unknown reading or an error.
- The expected graph selected: display its native five-character meter in monospace.
- Missing graph/gating definition, or an unsupported custom child selection:
  `Unavailable`, rather than silently displaying invented or stale information.

This is data capture for an existing native condition, not the deferred coordinated
HUD show/hide feature. No gameplay action, turn advancement, forced refresh or
controller routing change is added. Sampling still follows the existing sidebar
hook. Shared next-turn movement-mode refresh remains the previously accepted
behavior, not a reopened lower-only defect.

## Transport and temporary layout

`apply_body_details.py` derives this experiment's workspace files in memory from
`apply_equipment_status.py`. The accepted hash-locked activity/core templates and
all earlier experiment scripts are unchanged. All source hashes, unique anchors,
template inputs and destinations are validated before the first game-source write.
The overlay still changes/adds eight integration targets in the build workspace.

The first 24 numeric fields and 17 text-widget slots retain their positions.
New widget slots 17-25 are comfort, trend, oxygen, head, torso, arms, hands, legs,
feet, in that order. One mutex-protected copied snapshot is transported as
`Object[] { long[50], byte[27][] }`: 24 core fields plus 26 availability flags;
movement text followed by 26 UTF-8 widget strings. Native transport logic and the
core decoder are unchanged. Live game objects are never read by Android's UI thread.

The existing array-sized loops append nine full-width wrapping rows after Mood and
clear all fields on session transitions. UI changes are limited to the experiment
title and monospace for the oxygen meter. Text size, scroll container, display
selection, non-focusable Presentation, 250 ms polling, and lifecycle hooks remain.
No font shrinking, tab buttons, decorative art or upper-sidebar removal is added.
The inherited 80-column game-widget rendering width still applies; wrapping cannot
recover content the upstream formatter already omitted.

## Validation actually performed

- All 24 new host/fixture tests passed. They check pinned definitions and native
  grouping/oxygen conditions, appended field order, eight-target provenance,
  hash/path/destination/duplicate-anchor guards, unchanged older sources and hooks,
  and parent output hashes against accepted build 10 provenance.
- A compiled capture fixture tests changed comfort/clothing, blank and missing
  summaries, oxygen full/reduced/suppressed/restored cases, missing gate/graph,
  unsupported custom child selections, inactive sessions and copied definitions.
  It substitutes small game/widget classes: it is NOT the real CDDA renderer,
  oxygen simulation, clothing system, or clause-expression evaluator.
- Generated production JNI code and Java decoders passed a host-JVM round-trip
  under `-Xcheck:jni`: 50 numeric/27 text slots, prior values, signed/zero stats,
  focus above 100, long text, Unicode/supplementary characters, embedded NUL,
  changed/blank/missing values, malformed payloads, copy isolation and clearing.
- Native mailbox copy/concurrency/session tests passed AddressSanitizer and
  UndefinedBehaviorSanitizer. This is not a race-detector or Android-device test.
- Workflow YAML and all ten Bash blocks passed syntax checks. The workflow changes
  are exactly five added lines: the new selector option and dispatch case.

The existing 109 tests were not rerun locally. CI should discover 133 tests, apply
the overlay to the actual pinned source, and compile Android native/Java code.
No full-engine build, Android Presentation compilation/execution, emulator test or
Thor acceptance is established by the local host checks.

## Next build

After review and merge into `ds-dev`, start a NEW manual **CDDA-DS Android test** run:

| Setting | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `body_details` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

Default `baseline`, manual dispatch, the branch gate, read-only repository
permissions, signing and caches are unchanged. Use the owner's fresh-install
process after backing up wanted data. Remove only CDDA-DS (test); leave official
CDDA and signing secrets unchanged. In-place update/data migration remains unresolved.

## Device acceptance (pending)

1. Reach all old/new rows by scrolling; check labels and wrapping, and repeat
   simultaneous lower swipe/upper joystick. Long equipment/clothing names remain a
   useful explicit test when available, not an assumed pass.
2. Compare body comfort with the sidebar. Exercise practical clothing/environment
   changes and compare trend text where shown. Mark unreached categories untested.
3. Compare oxygen when reduced and recovering on a disposable character. At the
   native full-capacity suppression state, expect the lower Oxygen row to show a
   dash. Confirm the previous meter does not remain stale after suppression.
4. Change worn items (wear/remove/swap), not merely the wielded item. Compare all
   six summaries with the matching sidebar widgets. Include an uncovered category
   and multiple worn items where practical; report native placeholders as observed.
   Do not treat these summaries as a new detailed armor-stat screen.
5. Confirm prior readings, lower-touch/controller focus, sleep/resume, app switching,
   main-menu clearing and reload. Compare both screens at the same game refresh.

## Deferred deliberately

Both maps, compass/legend, messages and remaining metrics are unfinished. Variable
anatomy, complete state/color semantics and final layout precede coordinated
show/hide and sidebar removal. Context-themed pages, repeated readings across tabs,
map grouping and the creature-legend decision remain later discussion. The owner's
minimalist font/color/framing preferences do not authorize a redesign in this PR.
This increment adds no interaction controls and is not full Milestone 1 completion.
