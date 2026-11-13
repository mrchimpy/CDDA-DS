# CDDA-DS: first Android build checkpoint

**This builds the ordinary single-screen game, not the dual-screen HUD.**
**Use a disposable world. The initial workflow signs with a new temporary key on every run.**
No successful CI build or Thor acceptance test is implied by the presence of this file.

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
The gate must be revised explicitly when we begin actual interface development.

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
and checksum checks in upstream Gradle are retained. The asset reuse avoids silently
pulling newer graphics or sounds from moving upstream repositories.

This is a fixed-source/fixed-resource build recipe, not a promise of bit-for-bit
reproducibility or a wholly source-only build. Its temporary signing key, runner image,
and external build-tool repositories are additional inputs. If the baseline APK is
unavailable or its hash differs, stop and investigate; do not substitute a newer APK.

## Enable and run

1. Keep Actions disabled until this workflow has been reviewed and placed on `ds-dev`.
2. Make `ds-dev` the repository default branch. GitHub requires the manual workflow
   to be present on the default branch to expose its Run workflow control.
3. Enable repository Actions, but leave inherited upstream workflows individually
   disabled. Enable only **CDDA-DS Android test**. Do not trigger Experimental Release,
   translation synchronization, or other upstream automation.
4. Open Actions, select **CDDA-DS Android test**, choose **Run workflow**, confirm
   `ds-dev`, and run it. No signing secrets or upstream release credentials are required.
5. On a successful run, download `CDDA-DS-arm64-test-<run number>` from Artifacts,
   unzip it, and install the APK on the Thor. The separate build-log artifact is
   for diagnostics; it does not contain an APK.

The new workflow has only a manual trigger, read-only repository-content permission,
no publication step, and no automatic upstream synchronization. It does not itself
change repository settings or enable/disable the inherited workflows.

## Signing and save safety

This first checkpoint uses a fresh temporary key, intentionally not uploaded or cached.
Android will reject an in-place upgrade signed by a different key. Before testing a
second run, export/back up any test-app data you care about, then remove ONLY
**CDDA-DS (test)** if necessary. Removing an app can remove its saves. Never remove
the official CDDA installation to resolve a test-build signing error.

Do not use these disposable builds for a long-running character. Before normal
iteration or public distribution, introduce a persistent owner-controlled signing key
stored as GitHub Actions secrets, with an offline backup. Never commit or paste that
private key into chat, source code, logs, or release artifacts.

## Acceptance on the Thor

Check side-by-side installation, launch, initial asset installation, eight-direction
selection and R2 movement commitment, ordinary menus, save/reload, sleep/resume, and
app switching with the top-screen focus lock. Compare against the official baseline.
A green build only proves that the workflow's build/package checks passed; it does
not establish device behavior, controller reliability, or gameplay correctness.

## Records and notices

The artifact contains the source/run identifiers, resource preparation report, exact
packaging patch, APK metadata, signature fingerprint, SHA-256 checksum, this guide,
and inherited top-level license notices. Resource-tree notices are retained with the
resources. This is an unofficial modified test build, not endorsed by CDDA or AYN.
No new license replaces upstream terms. A complete third-party binary notice/source
obligation review remains a separate gate before a public release.

References:

- https://github.com/CleverRaven/Cataclysm-DDA/releases/tag/cdda-experimental-2026-10-19-0834
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://developer.android.com/build/manage-manifests
- https://developer.android.com/studio/publish/app-signing
