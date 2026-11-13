# Checkpoint 1: built baseline, initial Thor smoke test

## What is recorded

- Upstream baseline: `bb52239dee96df602da097f113382fe5c9a9c115`
  (`cdda-experimental-2026-10-19-0834`).
- First successful CDDA-DS build source: `2d3c4e0145a6512acbdd733991162e3f529a4c49`.
- Reference branch: `checkpoint/baseline-smoke-1`, created at that exact source commit.
  This is an ordinary reference branch, not a protected/immutable tag.
- Successful run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43358193411
- Build number: 2. GitHub job duration: 23 minutes 33 seconds; Gradle: 22 minutes 28 seconds.
- Artifact: `CDDA-DS-arm64-test-2` (APK and provenance).
- Artifact ZIP SHA-256: `00edbb196be3638cbf6696ca681cda2907c17d9fb791fc20255cd85c9936f178`.
- Owner's report: "very short test, but all looks good."

This records an initial smoke test only. It does not assert that every controller,
save/load, lifecycle, or long-session test has been individually completed. No secondary
screen, HUD migration, or interactive companion is implemented in this checkpoint.

The game/Android source equality gate, nine preparation tests, compilation, signature
checks, separate identity/ARM64 checks, and artifact upload passed in run 2. Known
non-blocking warnings included compiler and Java/Gradle/Node deprecations. Keep them
separate from gameplay changes.

## What this reference preserves

The source branch lets us compare future changes with the source that produced the
working test APK. It does NOT preserve the destroyed signing key or permanently retain
the binary: GitHub build artifacts expire. Keep a local copy of the downloaded ZIP for
comparison. Do not rerun the old disposable workflow expecting the same certificate.

## Next checkpoints

1. Validate persistent owner-controlled test signing and conservative build caching.
   These changes must leave game code unchanged; see `SIGNING.md`.
2. Choose display plumbing based on actual Android/source inspection and implement one
   live value on the lower screen while retaining the original sidebar for comparison.
3. Expand coverage to the agreed sidebar content before reclaiming the upper map space.

No architecture has been selected or proven by the successful baseline build.
