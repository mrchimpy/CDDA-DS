# Persistent test signing: owner setup

The owner generates and keeps this key. Never send its contents or password to chat,
commit it to GitHub, publish it as an artifact, or place it in a build cache.
This is an unofficial development key, not an upstream CDDA key or a public-release
signing policy. Only the public certificate fingerprint is safe to share.

## Why this is a one-time transition

Build 2 used a throwaway key that was intentionally destroyed. A new key cannot update
that installation in place. Back up any test saves first. When the first persistent-key
APK is ready, remove ONLY **CDDA-DS (test)** and install the new test APK. Keep official
CDDA installed. Later builds using this same key and application identity can update
one another; installation/update behavior must still be tested on the Thor.
Keep using disposable worlds until save compatibility and the prototype are validated.

## Generate the key on your Windows PC

Download `build-scripts/ds/New-CDDA-DSTestKey.ps1` and review it. It requires an installed
JDK's `keytool`; it checks PATH, JAVA_HOME, and common Temurin/Android Studio locations.
It does not install software, upload anything, or show private values in its output.
If keytool is missing, install a Java 17 JDK (for example Eclipse Temurin 17) and reopen
PowerShell. There is no need to install the Android SDK or a full development IDE.

Run from the folder where you saved the helper:

```powershell
.\New-CDDA-DSTestKey.ps1
```

If Windows blocked the downloaded script, review it first and unblock only that file:

```powershell
Unblock-File .\New-CDDA-DSTestKey.ps1
.\New-CDDA-DSTestKey.ps1
```

No system-wide execution-policy change is required by this guide. An organization
policy may still prevent scripts; do not bypass an organization's restrictions.

The default output directory is `%USERPROFILE%\CDDA-DS-private`, outside the repository.
The helper refuses to overwrite an existing output folder and restricts the new folder's
Windows permissions to the current user. Keep a secure backup of the PKCS12 key and
password. Base64 is encoding, NOT encryption. Both secret text files are sensitive.

Required key format: PKCS12, alias `cdda-ds-test`, with the same password for the store
and private key. The helper generates a random password and uses RSA-3072. A custom
keystore must meet these requirements; only the fixed alias is supported at this stage.

## Add two repository secrets

In `mrchimpy/CDDA-DS`, open **Settings > Secrets and variables > Actions > Secrets**.
Use **New repository secret**, NOT the repository Variables tab and NOT Add file.

| Secret name | Value |
|---|---|
| `DS_TEST_KEYSTORE_BASE64` | Entire contents of `DS_TEST_KEYSTORE_BASE64.txt` |
| `DS_TEST_STORE_PASSWORD` | Entire contents of `DS_TEST_STORE_PASSWORD.txt` |

Paste the values only into GitHub's secret-entry fields, without quotes or added lines.
Do not share screenshots showing the values. The GitHub connector used for this project
does not provide secret-management access; the owner performs these two entries.

## Build and verify

Run **CDDA-DS Android test** on `ds-dev`, with `signing_mode = persistent`. Missing or
invalid secrets stop the job before toolchain installation and compilation. There is
no silent fallback to a new key. `disposable` remains an explicit troubleshooting option
and does not produce an upgrade-compatible APK.

The build records the selected public certificate fingerprint in `SIGNING.json`, then
checks that the final APK has that same fingerprint. Compare it to your locally generated
`CERTIFICATE-SHA256.txt` on the first persistent run. Subsequent persistent builds should
have the same fingerprint. Never replace secrets merely to make a build error disappear.

## Caches and limits

The new caches include only Gradle wrapper downloads, Maven dependency files, and C/C++
compiler results. They exclude keystores, signing properties, APKs, saves, and the complete
Gradle/Android build directories. GitHub caches are not secret storage. Cache hits and
elapsed time must be measured; no speedup has yet been validated for this workflow.

The workflow is manual-only, restricted to `ds-dev`, and does not publish releases.
Review future workflow changes before running them with signing secrets. Repository
write access permits modifying code that executes during such builds.

## References

- Android app-signing and update identity: https://developer.android.com/studio/publish/app-signing
- GitHub repository secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
- JDK distribution: https://adoptium.net/installation/
- Ccache design and limitations: https://ccache.dev/manual/latest.html

Local validation covered the Python signing helper with disposable fixture keys. The
Windows helper has been reviewed but not executed on Windows in this development session.
The revised GitHub workflow still needs its first CI run and an on-device update test.
