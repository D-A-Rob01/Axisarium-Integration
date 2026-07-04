# Melographion Architecture

## Core Philosophy

Melographion is a conversation engine that happens to use songs.

Its primary artifact is the reflective session: a guided sequence where a song becomes an event, a prompt opens a response, and the response produces observations that can be reviewed over time. The system may analyze music, lyrics, metadata, and audio features, but those analyses are supporting instruments. They are never the center of gravity.

The architectural rule is simple:

> Preserve the response before assigning meaning.

Raw capture is canonical. Interpretation is provisional. Any symbolic, emotional, bodily, lyrical, or sonic claim produced by Melographion must remain marked as inferred until David reviews it.

## System Shape

Melographion has four layers:

1. Capture: load songs, ask questions, preserve verbatim responses, import optional local audio.
2. Observation: extract rule-based inferred signals and local audio features.
3. Constellation: persist relationships among sessions, songs, motifs, body responses, and notes.
4. Export: render reviewable Axisarium notes through dry-run previews and backup-protected writes.

The CLI coordinates these layers. It should stay thin: parse intent, call the correct subsystem, and print clear results. Domain behavior belongs in modules, not in command handlers.

## Module Boundaries

### `models.py`

Owns the shared data contracts: song profiles, Melographion sessions, session events, observation sets, legacy reflection wrappers, audio feature sets, symbolic nodes, backup manifests, write previews, and constellation changes.

Must never:
- Read or write files directly.
- Call Spotify, cobalt, or vault APIs.
- Hide interpretation inside computed properties.

### `config.py`

Owns local settings, environment loading, project paths, and required local directories.

Must never:
- Create or mutate live vault files.
- Treat missing Spotify or cobalt settings as fatal for core use.
- Store secrets in code or generated notes.

### `spotify_client.py`

Owns Spotify authentication, playlist listing, playlist loading, and conversion of Spotify track payloads into `SongProfile` records.

Must never:
- Claim Spotify provides raw audio.
- Download audio.
- Write Obsidian notes.
- Treat Spotify metadata as personal meaning.

### `song_selector.py`

Owns song suggestion modes. In v0.1, non-random modes are heuristics over existing local data.

Must never:
- Pretend heuristic ranking is psychological certainty.
- Invent a personal memory or definitive symbolic interpretation.
- Require Spotify access after local song profiles already exist.

### `prompt_engine.py`

Owns reflection prompts.

Must never:
- Diagnose.
- Lead David toward a predetermined interpretation.
- Collapse the session into song review or taste judgment.

### `response_analyzer.py`

Owns rule-based extraction from David's response: themes, symbols, body responses, memory cues, valence, emotional tags, and intensity.

Must never:
- Modify the verbatim response.
- Present extracted signals as definitive.
- Infer memories that David did not actually state.
- Turn reflection into diagnosis.

Its output belongs in `SessionEvent.inferred_observations`, never in `user_response_verbatim` or `reviewed_observations`.

### `lyric_ingest.py`

Owns user-provided lyric text and lyric references.

Must never:
- Scrape lyrics by default.
- Automatically store full copyrighted lyrics from public sources.
- Treat lyric analysis as more authoritative than David's response.

### `audio_features.py`

Owns local audio feature extraction from user-provided files.

Must never:
- Download audio.
- Call cobalt.
- Pretend unavailable features were measured.
- Treat sonic features as emotional truth.

### `audio_ingest/`

Owns optional audio ingress pathways.

- `manual_file.py`: implemented in v0.1; copies a local audio file into the audio inbox and analyzes it.
- `cobalt_watch_folder.py`: v0.2 scaffold; scans the local inbox for files to associate with sessions.
- `cobalt_api_client.py`: v0.3 scaffold; reserved for a local/private cobalt endpoint.

Must never:
- Make cobalt required for core use.
- Call public cobalt.tools.
- Download or process a file without David providing or configuring the ingress path.

### `graph_store.py`

Owns the local symbolic constellation persisted as JSON. It tracks nodes and edges for sessions, songs, artists, symbols, emotions, body responses, memories, audio features, and vault notes.

Must never:
- Write to the live vault.
- Replace review state in Obsidian.
- Treat graph presence as confirmation of meaning.

The graph is a working constellation, not a court record.

### `vault_paths.py`

Owns Axisarium path mapping and path safety.

Must never:
- Resolve targets outside the configured vault.
- Permit writes into `.obsidian` or sync-internal folders.
- Reintroduce retired `Prima Midgardia` production paths.

### `backup.py`

Owns backup manifests and backup zip creation before live vault writes.

Must never:
- Skip backup creation for real live-vault writes.
- Back up or write paths outside the vault boundary.
- Treat dry-run as permission to mutate files.

### `obsidian_exporter.py`

Owns note rendering, dry-run previews, init scaffolding, index rebuild plans, and backup-protected vault writes.

Must never:
- Put inferred observations before verbatim response.
- Write to the vault without a previewable plan.
- Mutate `.obsidian`.
- Bypass `backup.py`.

### `storage.py`

Owns local JSON persistence for cache, profiles, sessions, audio features, and graph-related artifacts.

Must never:
- Write live vault notes.
- Store secrets.
- Rewrite user-authored vault content.

### `cli.py`

Owns user-facing command routing.

Must never:
- Contain the core business logic.
- Hide live vault writes behind commands that do not expose `--dry-run`.
- Treat a failed optional dependency as failure of the whole system.

## Data Flow

### Initialization

```text
CLI
-> config loads settings
-> obsidian_exporter plans vault scaffold
-> backup builds dry-run manifest
-> preview prints target notes, backup manifest, constellation changes, and index changes
-> real write creates backup first, then writes notes
```

### Playlist Loading

```text
CLI
-> spotify_client authenticates
-> Spotify playlist metadata becomes SongProfile records
-> storage writes local JSON profiles and playlist cache
```

Spotify metadata is identity context, not interpretation.

### Single-Song v0.1 Session

```text
CLI
-> storage loads SongProfile
-> prompt_engine generates question
-> CLI captures David's verbatim response
-> response_analyzer extracts inferred observations
-> storage writes MelographionSession with one SessionEvent
-> graph_store updates local constellation
```

The compatibility `song reflect` command is still song-addressed because Spotify tracks are convenient handles. The saved artifact is a canonical session with one event.

### Multi-Event Session

```text
session start
-> SessionEvent status: pending_prompt
session capture-response
-> stores user_response_verbatim and sets response_captured
session infer
-> stores inferred_observations and sets inference_pending
session review-inference
-> stores reviewed_observations and sets inference_reviewed
session next-song
-> records next song candidate and sets next_song_suggested
session add-song
-> appends next pending_prompt event
```

The event lifecycle is explicit:

- `pending_prompt`
- `response_captured`
- `inference_pending`
- `inference_reviewed`
- `next_song_suggested`
- `complete`

`user_response_verbatim` is immutable after capture. Inference is not final until moved into `reviewed_observations`.

### Audio Import

```text
CLI
-> audio_ingest.manual_file copies local file to inbox/audio
-> audio_features analyzes local file
-> storage writes AudioFeatureSet
-> graph_store links audio features to song/session context
```

Audio files enter Melographion only through local user-provided paths in v0.1.

### Vault Export

```text
CLI
-> storage loads MelographionSession and SongProfile records
-> obsidian_exporter renders session note with ordered events
-> backup builds manifest
-> dry-run prints everything
-> real write creates backup, writes note, and persists constellation changes
```

Session summaries are generated only after at least two events exist. A one-song session may have a frame, but not a full arc summary.

Every vault-writing command must support `--dry-run`.

## Subsystem Ownership

Capture owns:
- prompt text
- immutable verbatim response
- session identifiers
- event identifiers and statuses
- song event order
- local source references

Observation owns:
- rule-based inferred themes
- rule-based inferred symbols
- body response extraction
- memory cue extraction
- reviewed observations after David accepts, revises, or defers inference
- audio features
- lyric features from user-provided text

Constellation owns:
- local graph nodes
- local graph edges
- emerging motifs
- provisional relationships

Export owns:
- Axisarium note shape
- frontmatter
- backlinks
- provenance metadata
- review metadata
- confidence metadata
- dry-run rendering
- backup-protected writes

## Metadata Policy

Generated session notes should carry provenance and review state:

```yaml
origin:
  system: Melographion
  version: 0.2

review:
  reviewed: false
  interpretation: inferred

confidence:
  symbolic: 0.43
```

Confidence values are local heuristics. They express how much inferred material was available, not how true the interpretation is.

## Live Vault Safety

The live Axisarium vault is not a scratchpad.

Rules:
- Dry-run first.
- Show target paths.
- Show full note content.
- Show backup manifest.
- Show constellation changes.
- Back up existing target files before real writes.
- Never modify `.obsidian`.
- Never write sync-internal paths.

## Future Multi-System Communication

Melographion should communicate with future systems through explicit artifacts, not hidden coupling.

Preferred shared interfaces:
- Markdown notes in Axisarium.
- Local JSON records with stable model fields.
- Constellation nodes and edges.
- Frontmatter provenance blocks.
- Review states.

Systems should read each other's outputs as evidence or context, never as commands.

### Argos

Argos may eventually observe patterns across systems.

Melographion should expose:
- session summaries
- emerging themes
- review states
- constellation changes

Argos must not rewrite Melographion sessions directly. It may nominate patterns for review.

### Aurelius

Aurelius may eventually translate private insight into public-facing rhetoric, essays, teaching material, or client-safe language.

Melographion should expose only reviewed or explicitly selected material to Aurelius. Raw responses, memory cues, and private inferred observations should remain private unless David promotes them.

### Aletheion

Aletheion contributes symbolic weather. Melographion contributes resonance weather.

Communication should happen through linked notes, dated context, and reviewed motifs. Neither system should treat the other's interpretation as authority.

### Mnemosynthesizer

Mnemosynthesizer is the review and promotion gate.

Melographion may nominate candidate memories and motifs. Mnemosynthesizer decides whether they remain raw, become reviewed, become confirmed, or get promoted into an Orbit, Protocol, Project, Fragment, or Constellation.

### Future Systems

Any future system should integrate by asking:

- What artifact am I allowed to read?
- Is the material raw, inferred, reviewed, or confirmed?
- Am I observing, nominating, transforming, or publishing?
- What must remain private?
- Where does David review the result?

## Architectural North Star

Melographion should become better at holding a session, not louder at explaining a song.

When uncertain, prefer:
- more faithful capture
- clearer provenance
- better review states
- safer exports
- fewer claims
- stronger session continuity

The system succeeds when David can return months later and see not only what a song was, but what kind of conversation it opened.
