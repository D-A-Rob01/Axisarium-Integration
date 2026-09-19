# Kybernion Mobile Helm

Kybernion 0.3.4 (Android version code 7) is a local-first handheld symbolic inquiry and reading capture app.

Open this `android-app/` folder in Android Studio, allow Gradle to resolve the Android and Compose dependencies, then run the `app` configuration on an emulator or physical device.

The app loads the Python package's existing deck and spread JSON directly as a Gradle asset tree. The source checkout must therefore retain:

```text
../src/cartomancy_engine/data/
```

The first screen supports Kybernion's field-capture workflow:

- question and context capture
- Three Card, The Constellation, The Fork, The Aperture, The Crucible, The Interface, and The Vector formations
- interpretation protocol selection
- optional confidence
- reversals enabled or disabled
- one immutable draw per active screen session
- first-impression capture
- Android share export of Markdown and optional JSON
- an interactive, stage-aware field cue in place of permanent onboarding copy

## Version 0.3 release

Version 0.3 integrates the complete set of 78 high-resolution Kybernion Tarot
v3 SVGs. Every card is mapped to the canonical Rider-Waite-Smith record by ID,
verified by SHA-256 at import and build time, and rendered from the bundled
vector without a network dependency.

The reading surface now has two complementary modes:

- an adaptive spread overview using complete 3:5 card vectors
- a full-screen, swipeable card detail viewer with readable position,
  orientation, keywords, and prompt metadata

Portrait and landscape layouts preserve the full artwork with `Fit` scaling.
Reversed cards rotate the artwork only, leaving all labels legible. The column
count adapts from compact phones through larger displays, while the detail
viewer changes from stacked to side-by-side presentation. Changing orientation
or recreating the activity preserves the active reading; starting a new reading
still requires the explicit refresh control.

## Artwork source and validation

Import or verify the source package from the repository root:

```powershell
python .\scripts\import_tarot_v3.py --source <path-to-tarot-sigil-drafts-v3>
python .\scripts\import_tarot_v3.py --source <path-to-tarot-sigil-drafts-v3> --check
.\gradlew.bat verifyTarotAssets
```

`verifyTarotAssets` is also attached to `preBuild`; a missing, duplicate, or
modified SVG fails the build instead of silently substituting another card.

This is a personal release, not a published Play Store app. It does
not write directly to an Obsidian vault, perform AI interpretation, sync to the
cloud, or support Galaxy Watch. The package/application id remains
`com.aletheion.cartomancy` as a technical compatibility name.

## Spread Grammar 0.3.4

See [the spread guide](../docs/spread-grammar.md) and [change record](../docs/changes-0.3.4.md). The Constellation, icon, draw engine, reading state, and export renderers are preserved. Run `./gradlew verifyTarotAssets verifyStartupContracts verifyDeckArtworkContract testDebugUnitTest assembleDebug assembleRelease` from this folder. Signed APKs are produced by the Kybernion Android workflow with `release=true`; signing material must never enter source bundles.
