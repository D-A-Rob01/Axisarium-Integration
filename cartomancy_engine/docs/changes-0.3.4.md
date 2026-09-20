# Kybernion 0.3.4 — Spread Grammar

Android version name **0.3.4**, version code **7**. Baseline: `3dbe692` (0.3.3).

## Changes

- Added The Fork, The Aperture, The Crucible, The Interface, and The Vector as
  shared seven-position JSON contracts and Android formation choices.
- Added all five to the Android startup build checks. Added draw/export coverage
  across the seven Android formations, including optional reversals, position
  metadata, unique cards, first-impression edits, and Markdown/JSON audit fields.
- Corrected the stale Python test expecting a Major-Arcana-only deck to check
  the already-shipped 78-card deck (22 major, 56 minor).
- Updated engine, Android, and root documentation; added the spread guide and
  comprehensive project brief. Updated the signed workflow artifact name.
- Python distribution version remains independently at 0.1.0; Android is 0.3.4.

## Preserved

The Constellation JSON, existing spread contracts, draw engine, reading models,
saved reading state, Markdown/JSON renderers, Android sharing, application ID,
icon, card artwork, and UI rendering are unchanged from the baseline. The
formation list is the only runtime Kotlin change. No schema migration or
automatic spread recommendation is introduced. Existing production worktrees
and private readings were not changed.

## Verified locally, 2026-09-19

- Python: `python -m pytest cartomancy_engine/tests -q` — **34 passed**.
- Android: `verifyTarotAssets verifyStartupContracts verifyDeckArtworkContract
  testDebugUnitTest assembleDebug assembleRelease` — **BUILD SUCCESSFUL**.
- Existing reading/export/state/UI/icon/Constellation paths: no diff versus
  `3dbe692`.
- Debug APK and unsigned release APK built. Signed delivery uses the existing
  GitHub workflow with `release=true`; see the run and artifact for signing status.
- GitHub Actions signed release: [run 35468247811](https://github.com/D-A-Rob01/Axisarium-Integration/actions/runs/35468247811) completed successfully for commit `3e8255d`. The workflow verified the APK signature and retained `Kybernion-Mobile-Helm-0.3.4-signed`, containing the signed APK and SHA-256 checksum, for 30 days.

## Acceptance limits

No Android device or emulator was attached at verification time, so physical
launch, rotation, and share-sheet acceptance for 0.3.4 are not claimed. Existing
AGP 8.5.2 reports a compileSdk 35 compatibility warning; builds pass and a platform
upgrade is outside this change. The Grok import is a selected source snapshot,
not live repository synchronization; it excludes private readings and secrets.
