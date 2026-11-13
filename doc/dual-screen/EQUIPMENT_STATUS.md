# Experiment 6: wielded item, martial-arts style and small status readouts

Status: build 10 passed Android CI/package checks and the owner's exercised Thor
checks. Accepted as a checkpoint for continued incremental development, with
bionic-power behavior and long wielded-item-name wrapping explicitly NOT TESTED.
See [Checkpoint 8](CHECKPOINT_8.md). No defects were reported in the exercised paths;
this is not an unconditional all-fields acceptance or full Milestone 1 completion.

Builds on accepted build 9 (`environment_status`, tested source
`5067a4cdba6cb1fdeab19ed899237568cd66f80d`) and its acceptance record
`6c73453a675bc1ba1a1c95ac651e2f6b33bd60c4`. That rollback source remains
`checkpoint/environment-status-9`. The build 10 tested source is preserved as
`checkpoint/equipment-status-10` at `50474b61fd018ed46db61cfc6b253210ea3d1a7a`.
Preserve every earlier health, stamina, core, activity and environmental readout,
the original upper sidebar and viewport.

## Added information

| Readout | Pinned widget | Meaning and boundary |
|---|---|---|
| Wield | `wielding_desc` | Game-formatted wielded-item text (`wielding_text`), not a new item-name calculation. |
| Style | `style_desc` | The game's martial-arts style text (`style_text`). |
| Bionic Power | `power_desc` | The game's bionic power text, not Thor battery or arbitrary equipment charge. |
| Sound | `sound_num` | The sidebar's numeric Sound widget, not device volume or a new detection-range estimate. |
| Mood | `mood_desc_label` | The game's mood-face/text widget, not a separately exposed raw morale value. |

The definitions are in pinned `data/json/ui/{wield,ma_style,power,sound,morale}.json`
at `bb52239dee96df602da097f113382fe5c9a9c115`. Tests check those files' Git blob hashes,
selected widget IDs and bound variables. The script appends these five named widgets
to the accepted capture list; it does not enumerate arbitrary custom sidebar layouts.

Capture still makes local copies of the game widgets and calls `show(u, 80)` on the
game thread. Keep text, punctuation and any units/details supplied by those widgets;
strip color markup as before. Native widget formatting and its existing width limit
still apply, so this is not a promise of unlimited item-name display or exact visual
parity across all sidebar widths. Android rows wrap the text they receive; long
wielded-item-name wrapping was not exercised in the owner's build 10 device report.

Empty valid output retains the existing dash placeholder; a missing definition is
`Unavailable`. A literal `--`, `0` or game-provided no-style/unarmed description is
not replaced with an invented interpretation. Host test examples exercise transport,
not a claim that every example is the renderer's output for every game state.

## Implementation and preservation

`apply_equipment_status.py` derives files in memory from the accepted environment
renderer, which validates the original activity/core templates against explicit
blob hashes. Earlier scripts/templates are untouched; no additional full copy of
the HUD implementation is committed. All source hashes, anchors, templates and
new destinations are checked before writing any game source in the build workspace.

The 24 numeric core slots are unchanged. The first twelve widget slots retain their
indices and meaning. Append Wield, Style, Bionic Power, Sound and Mood at indices
12-16. The coherent native snapshot now transports `Object[] { long[41], byte[18][] }`:
24 core numbers plus 17 availability flags, with movement text followed by 17 widget
texts. All arrays derive from the same locked snapshot copy. The production native
bridge logic and core Java decoder are reused; no live game object is accessed by
the Android UI thread. The inherited `ActivityHudSnapshot` class name remains for
this derived experiment; its count/labels expand, not its decoding behavior.

The Android layout implementation is identical to the accepted environment layout
apart from the title. Its array-sized loop adds five more full-width wrapping rows
after Temperature, at the same text size. Existing clearing/render loops include all
new fields. Non-focusable Presentation, display selection, session/Activity hooks,
250 ms polling and sidebar-driven publication are unchanged. No game actions, new
permissions, controller mapping, forced redraws or turn advancement are added.

Only five workflow lines were added: one selector option and a four-line dispatch
case. Default `baseline`, manual dispatch, the `ds-dev` gate, repository read
permission, signing and dependency/compiler caches remain unchanged.

## Host/CI validation and limits

- All 20 new host/fixture tests passed locally, covering eight-target overlay
  provenance, pinned widget hashes/variables, append order, source/template/destination
  guards, old-template preservation, unchanged lifecycle/input hooks and clearing loops.
- A compiled capture fixture exercises all 17 widget slots, inactive-session
  suppression, local widget copies, changed/cleared/missing equipment and session
  cleanup. It substitutes small game/widget classes; it does not evaluate the real
  CDDA renderer, item system, bionics, martial arts or sound/mood calculations.
- The generated production JNI implementation and Java decoders passed a real host
  JVM round-trip under `-Xcheck:jni`: 41 numeric/18 text slots, previous values,
  signed/zero values and focus above 100, changed equipment, long/Unicode text,
  supplementary characters, embedded NUL, blank/missing text, malformed payloads,
  copy independence and inactive/unready-session clearing.
- Native copied-state/concurrent-read/session tests passed AddressSanitizer and
  UndefinedBehaviorSanitizer. Workflow YAML and all ten Bash blocks passed syntax
  checks; exact comparison confirmed only the five intended workflow lines differ.

The existing 89 tests were not rerun in that local implementation check. Build 10
subsequently ran all 109 host/fixture tests successfully in CI, applied the eight-target
overlay to the actual pinned source, compiled Android Java/native code and passed
the pipeline's signing/package checks. The preceding artifact review checked download
integrity and extracted the signing certificate for identity comparison; full signature
verification was performed by the pipeline. Device observations are separately
owner-reported below. CI and host long-text tests do not establish unexercised device
behavior such as bionic power or long-name wrapping.

## Build and installation

PR #5 is merged and build 10 already exists. No rebuild is needed to record its
acceptance results. For a subsequent requested build, start a NEW manual
**CDDA-DS Android test** run:

| Setting | Value |
|---|---|
| Branch | `ds-dev` |
| Experiment | `equipment_status` |
| Signing mode | `persistent` |
| Use dependency/compiler caches | enabled |

Continue the owner's fresh-install process after backing up wanted data. Uninstall
only CDDA-DS (test); retain official CDDA, application identity and signing secrets.
In-place update/data migration remains unresolved, not validated by fresh installs.

## Device acceptance (build 10: exercised paths pass, coverage gaps retained)

| Category | Owner-reported result |
|---|---|
| Layout and scrolling | PASS for exercised content: all rows visible/reachable; simultaneous lower swipe/upper joystick remains good. No long-named item was available for the wrapping check. |
| Wield | PASS: repeated item changes update immediately/in sync with the sidebar; unequipping shows `fist` in the owner's wording. |
| Style | PASS: switching to brawling updates in sync with the sidebar. |
| Sound and Mood | PASS: reported updating in sync with the sidebar; exact values/states not enumerated. |
| Bionic Power | NOT TESTED: explicitly excluded by the owner despite the combined category's PASS heading. |
| Previous readings and lifecycle | PASS: no additional notes supplied. |

See Checkpoint 8 for coverage boundaries. No bionic charge, capacity, placeholder or
charging/draining transition is established by this report. The ordinary layout
pass does not establish long wield/style-text wrapping on the device. These are
unexercised cases, not diagnosed defects and not a reason to invent a repair.

## Future regression and coverage checks

1. Preserve complete row access and simultaneous lower-swipe/upper-controller focus.
   Check long wield/style text when a suitable item/style is available; distinguish
   upstream widget width limits from actual Android clipping or missing content.
2. Repeat held-item changes and unarmed transitions against the sidebar; preserve
   game-supplied descriptions rather than substituting a hard-coded unarmed label.
3. Exercise other available style transitions and Sound/Mood states without assuming
   one Brawling change establishes every martial-arts or equipment combination.
4. Test Bionic Power in relevant capacity and changing-charge states when practical.
   Record the actual output; leave charging/draining untested until exercised.
5. Recheck previous health/core/activity/environment readings, knowledge restrictions,
   sleep/resume, app switching, title-menu clearing and reload after future changes.
   Compare both screens at the same sidebar refresh; no extra turn is required by
   the test protocol merely to make the companion update independently.

## Deliberately deferred

Clothing/armor summaries, body comfort, oxygen, remaining metrics, both maps, entity
compass/legend, message log, variable anatomy and final colors/layout remain later
work. Bottom-edge tabs, context-themed pages and repeated readouts across pages stay
ideation only. Typography, semantic color fidelity and functional framing belong to
the later presentation pass, not this functional acceptance update. No automatic
page switching, new gameplay controls, coordinated show/hide or upper-sidebar removal
is included. This is not full Milestone 1.
