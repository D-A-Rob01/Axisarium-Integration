# Kybernion Mobile Helm Release Procedure

## Preconditions

- Complete a fresh debug build and the full unit-test suite.
- Run `verifyTarotAssets`; it must validate exactly 78 indexed SVG files.
- Test on the target Lexarcanum handset: create a reading, rotate the display,
  open card detail, export Markdown and JSON, and save both to the Axisarium
  readings destination.

## Signing

The release build signs itself only when all four `KYBERNION_*` signing values
are supplied as environment variables or in an untracked `keystore.properties`
file. Use the included example as the shape, never as a storage location for
credentials. A partial signing configuration is rejected rather than silently
producing an unsigned package.

```powershell
./gradlew.bat verifyTarotAssets testDebugUnitTest assembleRelease
```

When signing is configured, the usable artifact is:

```text
app/build/outputs/apk/release/app-release.apk
```

Record its SHA-256 alongside the version number. The signing key must be kept
securely and retained for every future update to this application id.

## GitHub Actions release

Ordinary pull-request and branch runs perform artwork validation, unit tests,
and unsigned debug/release builds. They intentionally do not publish an APK.

The explicit `Kybernion Android` workflow-dispatch release and any
`kybernion-v*` tag require all four repository Actions secrets:

- `KYBERNION_KEYSTORE_B64`
- `KYBERNION_STORE_PASSWORD`
- `KYBERNION_KEY_ALIAS`
- `KYBERNION_KEY_PASSWORD`

The release job fails with the names of any missing secrets. With complete
credentials, it signs the release, verifies the APK certificate, records a
SHA-256 file, and retains both files in the
`Kybernion-Mobile-Helm-0.3.0-signed` workflow artifact for 30 days.

## Lexarcanum acceptance gate

The release is ready only after the APK installs on Lexarcanum, launches, and
the exported Markdown note opens from the intended `Axisarium/03 Readings/Tarot`
location in Obsidian.
