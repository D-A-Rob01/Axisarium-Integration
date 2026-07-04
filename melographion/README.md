# Melographion

Melographion is a local resonance-session engine. It connects Spotify playlist metadata, optional local audio files, David's verbatim reflection responses, rule-based inferred observations, and Obsidian-ready Axisarium notes.

Phase 2 prioritizes session-atomic capture:

- Spotify playlist loading and song profiles
- canonical sessions with ordered song events
- explicit event statuses from `pending_prompt` through `complete`
- manual audio-file import from WAV, MP3, or M4A paths
- local audio feature extraction, using `librosa` when available
- verbatim reflection capture before interpretation
- separate inferred and reviewed observations
- JSON graph persistence
- session-first vault export with `--dry-run` previews and timestamped backups on real writes

## Setup

```powershell
cd "C:\Users\david\OneDrive\Documents\Axisarium Integration\melographion"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Fill in Spotify credentials in `.env` if you want Spotify access.

## Core Commands

```powershell
melographion init --dry-run
melographion spotify-auth
melographion playlist list
melographion playlist load "Iridescentia Animae"
melographion session start --song-id <id>
melographion session capture-response --session-id <id> --sequence 1
melographion session infer --session-id <id> --sequence 1
melographion session review-inference --session-id <id> --sequence 1
melographion session next-song --session-id <id> --sequence 1
melographion session add-song --session-id <id> --song-id <id>
melographion session export --session-id <id> --dry-run
melographion song suggest --mode random
melographion song reflect --song-id <id>
melographion audio import "C:\path\to\song.wav" --song-id <id>
melographion song analyze-audio "C:\path\to\song.wav" --song-id <id>
melographion export-note --dry-run
melographion graph update --dry-run
melographion index rebuild --dry-run
```

## cobalt.tools Path

cobalt is optional and never required for core use.

- v0.1: use cobalt manually, download a supported public link, then pass the local file to Melographion.
- v0.2: scan `inbox/audio/` for new files and ask which song/reflection each belongs to.
- v0.3: optionally call a local/private cobalt instance through `COBALT_API_URL`.

Melographion does not call public cobalt.tools in v0.1.

## Vault Safety

The live vault defaults to:

```text
C:\Users\david\OneDrive\Apps\remotely-save\Axisarium
```

Every live vault write has a dry-run mode. Real writes create a timestamped backup manifest under:

```text
C:\Users\david\OneDrive\Documents\Axisarium Integration\scratch\backups\melographion
```

Melographion never modifies `.obsidian` or sync internals.

