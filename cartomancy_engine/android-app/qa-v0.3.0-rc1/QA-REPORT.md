# Kybernion Mobile Helm v0.3.0-rc1 QA

Date: 2026-08-02

Device: Android API 35 emulator, 1080 x 1920 portrait / 1920 x 1080 landscape

Package: `com.aletheion.cartomancy`

## Result

PASS — no crash or ANR signatures observed.

## Verified

- all 78 canonical v3 SVGs are present, uniquely mapped, and SHA-256 checked
- Three Card overview renders complete 3:5 vectors without cropping
- The Constellation renders all seven positions in the adaptive grid
- reversed cards rotate artwork only; interface text remains upright
- full-screen detail opens from a spread card and pages from 1/3 to 2/3
- detail layout preserves the complete vector in portrait and landscape
- the active draw survives rotation and background process recreation
- the Field Cue replaces permanent onboarding copy and cycles 1/4 to 2/4
- 200% system text retains the formation value and vertically scrolls
- export invokes Android Sharesheet with Markdown and JSON (`Sharing 2 files`)
- debug APK installs and launches on API 35
- minified release APK assembles and passes release lint-vital checks

## Automated checks

```text
python -m pytest -q
44 passed

gradlew verifyTarotAssets testDebugUnitTest assembleDebug assembleRelease
BUILD SUCCESSFUL
```

## Build note

Windows temporarily held the original generated `app/build` cache open. It was
moved intact to `app/build-stale-20260802`, after which a fresh output tree
completed all 88 Gradle tasks successfully. The stale cache is ignored and is
not part of the release artifacts.

## Artifacts

- Debug APK SHA-256: `E58991A846EDEC3F45C197FB7CCA9DAC01028763D45B20B1468CECA4DC0D71E6`
- Unsigned release APK SHA-256: `1C0E085883439513C7895C6861FB1F86AEDBAE678CEE1767C61AED456160C9CD`
