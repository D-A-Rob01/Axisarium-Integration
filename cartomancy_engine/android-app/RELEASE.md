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
credentials.

```powershell
./gradlew.bat verifyTarotAssets testDebugUnitTest assembleRelease
```

When signing is configured, the usable artifact is:

```text
app/build/outputs/apk/release/app-release.apk
```

Record its SHA-256 alongside the version number. The signing key must be kept
securely and retained for every future update to this application id.

## Lexarcanum acceptance gate

The release is ready only after the APK installs on Lexarcanum, launches, and
the exported Markdown note opens from the intended `Axisarium/03 Readings/Tarot`
location in Obsidian.
