# CDDA-DS: pinned baseline and build checkpoint

Status: build setup in progress; no CDDA-DS APK has been built or device-tested yet.

## Source of truth

- Upstream: https://github.com/CleverRaven/Cataclysm-DDA
- Release tag: `cdda-experimental-2026-10-19-0834`
- Baseline commit: `bb52239dee96df602da097f113382fe5c9a9c115`
- Working branch: `ds-dev`
- Official comparison APK: `cdda-android-x64-2026-10-19-0834.apk` (ARM64 despite its filename).
- Comparison APK SHA-256: `f2f04a347728664cc0a240f50630d6e278f1e88f04101c1d811404af54749bab`.
- Release: https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/cdda-experimental-2026-10-19-0834

The owner has verified that the official build's controller scheme works on their Ayn Thor. This is not a claim that save/load, sleep/resume, every gameplay system, or our future build has passed acceptance testing.

## Current checkpoint: build the baseline ourselves

Produce one manually requested ARM64 Android test APK from the pinned game source. Do not change gameplay, controller logic, rendering, or the HUD at this checkpoint. Give the test installation a separate application ID, document-provider authority, and visible label so it does not replace the official installation.

The initial build may reuse the exact comparison APK's packaged graphics, sounds, translations, and shader artifacts. It must verify the APK hash first and must compile the native game library and Android application from source, not repackage the official executable. Record this asset dependency explicitly; this is not a completely source-only or bit-for-bit reproducible release build.

Use disposable saves. Test installation, launch, controller direction selection/commit, ordinary menus, save/reload, and sleep/resume on the Thor. A successful CI build is not a device acceptance pass.

## Milestone 1 remains unchanged

Read-only live sidebar on the lower screen; reclaim the upper sidebar's map space at the existing tile scale; preserve gameplay and controller behavior; retain a single-screen fallback.

Required information includes body/core/activity status; equipment, environment, and time; the small text/symbol map; eight-direction NPC/monster compass; message log; and the separate graphical pixel minimap. Both maps are required. Inventory interaction, new control mappings, the bottom-left touch shortcut strip, and Android system bars are outside Milestone 1.

## Change discipline

- No automatic synchronization with upstream Experimental.
- Keep packaging/build changes separate from later interface changes.
- Keep the baseline commit recorded even after `ds-dev` advances.
- Preserve upstream licenses and attribution. This unofficial fork is not endorsed by the CDDA project or AYN.
- Treat architecture choices as unvalidated until a minimal on-device experiment succeeds.
