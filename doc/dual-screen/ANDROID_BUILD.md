# CDDA-DS: Android baseline test builds

**This builds the ordinary single-screen game, not the dual-screen HUD.**
Build 2 compiled successfully and received a brief owner-reported Thor smoke test;
see [CHECKPOINT_1.md](CHECKPOINT_1.md). The revised signing/cache workflow still needs
its first CI run and device verification. Keep using disposable worlds.

## What is being built

- Source baseline: `bb52239dee96df602da097f113382fe5c9a9c115`.
- Upstream tag: `cdda-experimental-2026-10-19-0834`.
- Target: ARM64 (`arm64-v8a`), optimized Experimental Release configuration.
- Test application ID: `io.github.mrchimpy.cddads.experimental`.
- Launcher label: **CDDA-DS (test)**.
- Document provider: `io.github.mrchimpy.cddads.experimental.documents`.
- File-picker label: **CDDA-DS Test Data**.

The first build gate rejects changes in `src`, `data`, `gfx`, `lang`, or `android`
relative to the baseline. The preparation script then applies a recorded packaging
overlay to the build workspace only: application identity, launcher label,
document-provider authority, and file-picker label. The Java namespace and JNI
names stay unchanged. No gameplay, HUD, or controller behavior is intentionally changed.
The gate must be revised explicitly when actual interface development begins.

## Fixed assets, newly compiled executable

The helper downloads the exact official Android comparison APK, verifies SHA-256
`f2f04a347728664cc0a240f50630d6e278f1e88f04101c1d811404af54749bab`, and extracts only:

- `assets/gfx/`
- `assets/data/sound/`
- `assets/data/shaders/`
- `assets/lang/mo/`

Game JSON and source come from the pinned repository. Native libraries, Java bytecode,
and the official manifest are NOT copied from that APK. The Android application and
native game executable are compiled by Gradle/CMake. Existing SDL dependency versions
and checksum checks in upstream Gradle are retained. Asset reuse avoids silently pulling
newer graphics or sounds from moving upstream repositories.

This is a fixed-source/fixed-resource recipe, not a promise of bit-for-bit reproducibility
or a wholly source-only build. Signing material, runner images, and external build-tool
repositories are additional inputs. Stop if the baseline APK is unavailable or its hash
differs; do not substitute a newer APK.

## Enable and run

1. Use `ds-dev` as the repository default and selected workflow branch.
2. Enable repository Actions and **CDDA-DS Android test** only. Keep inherited workflows
   individually disabled. Allow the pinned GitHub-owned `actions/*` dependencies.
3. Complete [SIGNING.md](SIGNING.md) once, adding the two owner-controlled signing secrets.
4. Open Actions, select **CDDA-DS Android test**, and choose **Run workflow** on `ds-dev`.
   Keep `signing_mode = persistent` for ordinary iteration. Missing/invalid secrets fail
   early; there is no automatic fallback. `disposable` is for deliberate troubleshooting.
5. Leave `use_cache` checked to reuse dependency/compiler results. Uncheck it for a clean
   comparison build; this disables cache restore/save and the compiler cache.
6. After success, download `CDDA-DS-arm64-test-<run number>` from Artifacts, unzip it,
   and install the APK. The separate build-log artifact does not contain an APK.

The workflow has only a manual trigger, read-only repository-content permission,
no publication step, and no automatic upstream synchronization. It does not change
repository settings or enable/disable inherited workflows.

## Signing and save safety

Build 2's signing key was deliberately destroyed. The first persistent-key build cannot
update it in place. Back up test data first; remove ONLY **CDDA-DS (test)** when its
replacement APK is ready. Never remove official CDDA to fix test signing. Future builds
using the same certificate, application identity, and compatible versioning can update
one another; validate this on the Thor before relying on it for important saves.

The owner keeps the PKCS12 key and password securely backed up and stores them in GitHub
Actions secrets. No private key is committed, cached, or uploaded as an artifact. The
workflow checks the final APK certificate against the selected key and records only
its public fingerprint. Choosing disposable mode creates a new key intentionally.

## Build caches

Cache only Gradle wrapper downloads, Maven dependency files, and C/C++ compilation
results. Do not cache the whole Gradle home, Android build tree, APKs, signing properties,
private keys, or saves. Native compiler-cache entries are limited to 2 GB and restored
within a toolchain/build-configuration-specific prefix. Source/header changes are checked
by ccache. Cache failures are non-blocking; a missed cache causes ordinary compilation.

The first cached run must populate the cache. Speedup is not yet measured. Inspect
`CCACHE-STATS.txt` and job durations rather than assuming a hit or predicting a runtime.
A full uncached build remains available through `use_cache = false`.

## Acceptance on the Thor

Check side-by-side installation, launch, initial assets, eight-direction selection and
R2 movement commitment, ordinary menus, save/reload, sleep/resume, and app switching
with top-screen focus locked. Compare against official CDDA and the saved build-2 APK.
A green build is not proof of correct gameplay or device lifecycle behavior.

## Records and notices

The artifact contains source/run identifiers, resource preparation report, packaging
patch, APK metadata, signing mode/public fingerprint, SHA-256 checksum, cache statistics,
this guide, and inherited top-level license notices. Resource-tree notices are retained.
This unofficial test build is not endorsed by CDDA or AYN. Upstream license terms are
unchanged; a full third-party binary notice/source review remains a public-release gate.

References:

- https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/cdda-experimental-2026-10-19-0834
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://developer.android.com/studio/publish/app-signing
- https://ccache.dev/manual/latest.html
