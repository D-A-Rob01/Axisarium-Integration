# Astrerium 0.4.0

The native Android interface presents a focused card against an obsidian lake, with painterly plasma light, sparse elemental marks, and wavelength contours. All 78 cards have distinct illustrated cells. Android draws card names and orientation labels as text, separate from artwork.

## Reading flow

Encounter retains the existing seven spread contracts and eight protocols. Committing a draw saves its complete snapshot before displaying it. Journal entries use unique IDs; new inquiries never overwrite earlier readings. Notice captures first impressions, Relate pairs two spread positions, and Revisit records later reflections. Dated annotations append around the immutable snapshot. Unfinished drafts persist separately, keyed by reading and position or pair.

The Journal reopens saved readings. Deck browses all five collections and their original reference terms. Quiet view hides the writing panels. Android's share sheet exports Markdown and optional JSON with the original audit fields plus dated human annotations. No network permission, cloud synchronization, or automatic interpretation is added. Backup is disabled; uninstalling removes local readings and drafts, so users should export readings they wish to retain.

## Artwork provenance

Artwork was generated with OpenAI's built-in image-generation tool under David's art direction. Source imagery remains unaltered in the atlas PNGs. Runtime source rectangles follow visually inspected tile seams; native text and elemental seals overlay the paintings. This is an original visual interpretation of the existing Rider-Waite-Smith card identities; quantum and plasma motifs are visual metaphors.

The production prompt set requested independent 3-by-3 full-bleed portrait tiles, impressionist impasto, refracted geometric facets, obsidian/violet/cyan/champagne light, sparse elemental marks, subtle wavelength filaments, and no generated labels. Individual compositions followed each named card's established scene and differentiated silhouettes. Number labels are authoritative native text; symbolic object counts in the generated paintings may be stylized.

Atlas order, left-to-right then top-to-bottom:

- major-0: Fool through Strength.
- major-1: Hermit through Star.
- major-2: Moon, Sun, Judgement, World, Ace of Wands, Ace of Cups, Ace of Swords, Ace of Pentacles, unused back motif.
- Each suit atlas: Two through Ten.
- courts-0: Page, Knight, Queen, King of Wands; Page, Knight, Queen, King of Cups; unused motif.
- courts-1: Page, Knight, Queen, King of Swords; Page, Knight, Queen, King of Pentacles; unused motif.

`build_astrerium_index.py` reconstructs the 78-card map and SHA-256 manifest. `verifyAstreriumArtwork` checks deck identity, distinct cells, atlas hashes and image decoding before every build. Startup rechecks IDs, coordinates and hashes. The original v3 assets and contract checks remain intact.

## Validation and delivery

Run `testDebugUnitTest assembleDebug assembleDebugAndroidTest`; run `AstreriumFlowTest` on a clean emulator installation. It exercises draft retention, immutable snapshot restoration, and all three annotation modes. Release builds use the existing signing workflow and key; never substitute a new release key. Handset/Obsidian acceptance remains separate from emulator validation as documented in RELEASE.md.

On Windows, `KYBERNION_BUILD_DIR=build-astrerium` selects an isolated local build folder. The default CI output path remains `app/build`.
