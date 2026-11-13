# Checkpoint 2: persistent signing and initial persistence test

## Build under test

- Source: `2ad3ee39aa7b5db2b811f847edde170d4466b570`.
- Preserved branch: `checkpoint/persistent-baseline-4`.
- Run: https://github.com/mrchimpy/CDDA-DS/actions/runs/43365008254
- Artifact: `CDDA-DS-arm64-test-4`; APK `CDDA-DS-arm64-test-4.apk`.
- Signing: persistent; application ID `io.github.mrchimpy.cddads.experimental`.
- Public certificate SHA-256: `430f49596dcbb05ad014f48cdc26fce1c74d82a57859da231cd2f0129a121ae3`.
- Upstream game baseline remains `bb52239dee96df602da097f113382fe5c9a9c115`.

## Evidence and limits

The build completed successfully, including 22 preparation/signing tests and the
final certificate match. Compiler cache statistics reported 501 misses and no hits;
this run populated, rather than demonstrated reuse of, the native cache.

The owner reports an in-game test: the save file works, and the audio-volume setting
persists across app launch/close cycles. Record these as user-reported smoke-test
results, not exhaustive gameplay validation. A persistent-to-persistent APK update,
second-screen output, extended play, and full sleep/resume acceptance have not yet
been verified. Restart persistence is not the same test as update persistence.

## Next isolated experiment

See [STAMINA_PROBE.md](STAMINA_PROBE.md). Keep the original sidebar, map dimensions,
controller mappings, gameplay, and ordinary menus. Add one read-only stamina display
below. This does not implement full sidebar migration or interactive inventory.

Keep the owner-controlled signing key and application ID unchanged. Do not remove
build 4 just to install the next persistent-signed APK: the intended test is an
in-place update that retains the disposable save and changed volume setting.
Back up anything worth keeping first. Stop and report an unexpected install error
rather than hiding an update failure by uninstalling.
