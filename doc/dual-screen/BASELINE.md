# CDDA-DS: pinned baseline and build checkpoint

Status: the first source-built APK succeeded and the owner reported a brief successful Thor smoke test. Full acceptance testing remains incomplete. See [CHECKPOINT_1.md](CHECKPOINT_1.md) for the exact source, run, artifact, and limitations.

## Source of truth

- Upstream: https://github.com/CleverRaven/Cataclysm-DDA
- Release tag: `cdda-experimental-2026-10-19-0834`
- Baseline commit: `bb52239dee96df602da097f113382fe5c9a9c115`
- Working branch: `ds-dev`
- Official comparison APK: `cdda-android-x64-2026-10-19-0834.apk` (ARM64 despite its filename).
- Comparison APK SHA-256: `f2f04a347728664cc0a240f50630d6e278f1e88f04101c1d811404af54749bab`.
- Release: https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/cdda-experimental-2026-10-19-0834

The owner has verified that the official build's controller scheme works on their Ayn Thor. The additional brief smoke test of our own APK is not a claim that every save/load, sleep/resume, or gameplay test has passed.

## Completed build checkpoint and immediate follow-up

One manually requested ARM64 Android test APK was produced from the pinned game source. Its separate application ID, document-provider authority, and visible label are intended to coexist with the official installation. No dual-screen interface is implemented yet.

Next, validate persistent test signing and conservative build caching without changing gameplay, controller logic, rendering, or the HUD. See [ANDROID_BUILD.md](ANDROID_BUILD.md) and [SIGNING.md](SIGNING.md). A protected owner-held signing key must not be committed, cached, published, or pasted into chat.

The build reuses the exact comparison APK's packaged graphics, sounds, translations, and shader artifacts after verifying its hash. The native game library and Android application are compiled from source, not repackaged from the official executable. This is not a completely source-only or bit-for-bit reproducible release build.

Use disposable saves. Continue installation, launch, controller direction selection/commit, ordinary-menu, save/reload, and sleep/resume testing on the Thor. A successful CI build is not a complete device acceptance pass.

## Milestone 1 remains unchanged

Read-only live sidebar on the lower screen; reclaim the upper sidebar's map space at the existing tile scale; preserve gameplay and controller behavior; retain a single-screen fallback.

Required information includes body/core/activity status; equipment, environment, and time; the small text/symbol map; eight-direction NPC/monster compass; message log; and the separate graphical pixel minimap. Both maps are required. Inventory interaction, new control mappings, the bottom-left touch shortcut strip, and Android system bars are outside Milestone 1.

## Change discipline

- No automatic synchronization with upstream Experimental.
- Keep packaging/build changes separate from later interface changes.
- Keep the baseline commit recorded even after `ds-dev` advances.
- Preserve upstream licenses and attribution. This unofficial fork is not endorsed by the CDDA project or AYN.
- Treat architecture choices as unvalidated until a minimal on-device experiment succeeds.
