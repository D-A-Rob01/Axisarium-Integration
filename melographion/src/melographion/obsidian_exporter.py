from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .backup import build_backup_manifest, create_backup
from .config import Settings
from .graph_store import preview_graph_update, update_graph
from .models import (
    AudioFeatureSet,
    MelographionSession,
    ObservationSet,
    PlannedWrite,
    ReflectionSession,
    SessionEvent,
    SongProfile,
    VaultWritePreview,
)
from .vault_paths import AxisariumPaths, assert_safe_vault_path, date_prefix


def yaml_frontmatter(payload: dict[str, Any]) -> str:
    try:
        import yaml

        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).strip()
    except ModuleNotFoundError:
        lines: list[str] = []
        for key, value in payload.items():
            lines.extend(_yaml_lines(key, value))
        return "\n".join(lines)


def _yaml_lines(key: str, value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if value is None:
        return [f"{prefix}{key}:"]
    if isinstance(value, dict):
        if not value:
            return [f"{prefix}{key}: {{}}"]
        lines = [f"{prefix}{key}:"]
        for child_key, child_value in value.items():
            lines.extend(_yaml_lines(str(child_key), child_value, indent + 2))
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{prefix}{key}: []"]
        lines = [f"{prefix}{key}:"]
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}  -")
                for child_key, child_value in item.items():
                    lines.extend(_yaml_lines(str(child_key), child_value, indent + 4))
            else:
                lines.append(f"{prefix}  - {item}")
        return lines
    return [f"{prefix}{key}: {value}"]


def render_session_note(
    session: MelographionSession,
    profiles: dict[str, SongProfile],
    audio_features_by_event: dict[str, AudioFeatureSet] | None = None,
) -> str:
    audio_features_by_event = audio_features_by_event or {}
    session.refresh_rollups()
    first_profile = _profile_for_event(session.events[0], profiles) if session.events else None
    frontmatter = {
        "type": "melographion-session",
        "system": "Melographion",
        "project": "Iridescentia",
        "origin": {
            "system": "Melographion",
            "version": "0.2",
        },
        "review": {
            "reviewed": _session_reviewed(session),
            "interpretation": _session_interpretation_state(session),
        },
        "confidence": {
            "symbolic": _symbolic_confidence(session),
        },
        "session": {
            "id": session.session_id,
            "role": "melographion-session",
            "event_count": len(session.events),
            "primary_artifact": True,
        },
        "playlist": first_profile.playlist_name if first_profile else "",
        "songs": [_profile_for_event(event, profiles).track_name for event in session.events],
        "date": date_prefix(session.started_at),
        "mode": session.mode,
        "emotional_tags": _session_emotional_tags(session),
        "sonic_tags": _session_sonic_tags(audio_features_by_event),
        "symbolic_tags": session.session_symbols,
        "body_response": list(session.body_map.keys()),
        "linked_themes": session.session_themes,
        "linked_notes": ["Melographion", "Song Collage Analysis II", "Iridescentia"],
        "status": "capture",
        "melographion_status": "raw",
        "analysis_status": _session_interpretation_state(session),
    }
    events = "\n\n".join(
        render_event_block(
            event,
            _profile_for_event(event, profiles),
            audio_features_by_event.get(event.event_id),
        )
        for event in session.events
    )
    summary_block = render_session_summary(session)
    return f"""---
{yaml_frontmatter(frontmatter)}
---

# Melographion Session - {date_prefix(session.started_at)} - {_session_title(session, profiles)}

## Session Frame

{_session_frame(session)}

{events}

## Session-Level Inferences

- Themes: {_inline_list(session.session_themes)}
- Symbols: {_inline_list(session.session_symbols)}
- Body map: {_inline_list(list(session.body_map.keys()))}
- Emotional arc: {_inline_list(session.emotional_arc)}

## Session Summary

{summary_block}

## Connections

- [[Melographion]]
- [[Aletheion]]
- [[08 Iridescentia/Protocols/Mnemosynthesizer Protocol|Mnemosynthesizer Protocol]]
- [[Song Collage Analysis II]]
- [[Iridescentia]]
"""


def render_reflection_note(
    session: ReflectionSession,
    profile: SongProfile,
    audio_features: AudioFeatureSet | None = None,
) -> str:
    canonical = session.to_session()
    event = canonical.latest_event()
    audio_map = {event.event_id: audio_features} if audio_features else {}
    return render_session_note(canonical, {profile.track_id: profile}, audio_map)


def render_event_block(
    event: SessionEvent,
    profile: SongProfile,
    audio_features: AudioFeatureSet | None = None,
) -> str:
    inferred = event.inferred_observations
    reviewed = event.reviewed_observations
    return f"""## Song Event {event.sequence}

- Status: {event.status}
- Song: {profile.track_name}
- Artist: {profile.display_artist}
- Playlist: {profile.playlist_name or "none recorded"}

### Prompt

{event.prompt}

### Verbatim Response

{event.user_response_verbatim or "No response captured yet."}

### Reviewed Observations

{render_observation_block(reviewed) if reviewed else "No reviewed observations yet."}

### Inferred Observations

These observations are rule-based and provisional until reviewed.

{render_observation_block(inferred)}

### Sonic

{render_audio_block(audio_features)}

### Lyrical

- Lyric reference: {event.lyric_reference or profile.lyric_reference or "none supplied"}
- Inferred lyric fields: {_inline_list(list(profile.lyric_vector.keys()))}

### Next Song Hypothesis

{event.next_song_reasoning_public or "No next-song hypothesis recorded yet."}
"""


def render_observation_block(observations: ObservationSet | None) -> str:
    if observations is None:
        return "No observations recorded yet."
    return "\n".join(
        [
            f"- Interpretation state: {observations.analysis_status}",
            f"- Valence: {observations.emotional_valence}",
            f"- Tags: {_inline_list(observations.emotional_tags)}",
            f"- Intensity score: {observations.intensity_score}",
            f"- Symbols: {_inline_list(observations.extracted_symbols)}",
            f"- Themes: {_inline_list(observations.extracted_themes)}",
            f"- Body response: {_inline_list(observations.body_response)}",
            "- Memory cues:",
            _bullet_list(observations.memories),
        ]
    )


def render_session_summary(session: MelographionSession) -> str:
    if not session.can_have_arc_summary:
        return "A one-song session may have a frame, but Melographion does not generate a full arc summary until at least two events exist."
    return session.session_summary or "Session arc summary has not been written yet."


def render_audio_block(audio_features: AudioFeatureSet | None) -> str:
    if audio_features is None:
        return "- No local audio feature set linked to this session event."
    return "\n".join(
        [
            f"- Analyzer: {audio_features.analyzer}",
            f"- Duration seconds: {audio_features.duration_seconds}",
            f"- Estimated tempo: {audio_features.estimated_tempo}",
            f"- RMS energy mean: {audio_features.rms_energy_mean}",
            f"- Silence ratio: {audio_features.silence_ratio}",
            f"- Zero-crossing rate mean: {audio_features.zero_crossing_rate_mean}",
            f"- Section-change estimates: {_inline_list([str(value) for value in audio_features.section_change_estimates])}",
        ]
    )


def render_system_note() -> str:
    created = _today()
    return f"""---
type: constellation
status: active
created: {created}
updated:
aliases:
  - Song Collage Reflection System
  - Resonance Engine
tags:
  - constellation
  - iridescentia
---

# Melographion

## Essence

Melographion is a conversation engine that uses songs as thresholds. Its true object is not music analysis but the lived pattern that appears when sound, memory, body, image, and language begin answering one another.

## Why It Exists

Axisarium preserves more than information; it preserves the shape of attention over time. Melographion exists because some truths become available only through resonance: a lyric that opens a memory, a rhythm that locates feeling in the body, a sequence of songs that reveals a symbolic path. It gives those moments a durable form without mistaking inference for certainty.

## Governing Premise

Songs are events within reflective sessions; the session is the primary artifact.

## Primary Functions

- Conduct guided listening sessions.
- Preserve David's verbatim responses before interpretation.
- Mark symbolic, emotional, bodily, lyrical, and sonic observations as inferred until reviewed.
- Build a symbolic constellation of sessions, songs, motifs, body responses, and emerging themes.
- Export reviewable Axisarium notes with provenance, confidence, and review state.

## Relationship To

### Aletheion

Aletheion reads symbolic weather from time and sky. Melographion reads symbolic weather from resonance, listening, and response. Both systems separate observation from interpretation.

### Mnemosynthesizer

Melographion nominates possible memories, themes, and motifs. [[08 Iridescentia/Protocols/Mnemosynthesizer Protocol|Mnemosynthesizer]] keeps them provisional until David reviews, confirms, revises, or promotes them.

### The Axis

Melographion serves [[The Axis]] when it turns intensity into form: a session, a question, a response, an observation, and a next movement.

## Current Orbit Structure

Initial orbit structure is empty.

## Future Capacities

Initial future capacities are empty.
"""


def render_project_note() -> str:
    created = _today()
    return f"""---
type: project
status: active
created: {created}
deadline:
next_action: Run `melographion init --dry-run`, then inspect the generated vault preview.
---

# Melographion

## Desired outcome

A local Python CLI that runs Melographion as a session-centered conversation engine: songs become events, questions shape the path, responses are preserved verbatim, and inferred observations become reviewable Axisarium material.

## Current state

- v0.1 emphasizes reliable session capture, manual audio import, local analysis, dry-run previews, and constellation persistence.
- cobalt is optional and not called directly in v0.1.

## Next action

- Configure Spotify credentials in the local `.env` file.

## Materials

- [[Melographion]]
- [[Song Collage Analysis II]]
- [[08 Iridescentia/Protocols/Mnemosynthesizer Protocol|Mnemosynthesizer Protocol]]

## Questions

- Which playlist should become the first active resonance field?

## Links

- [[Iridescentia]]
- [[Aletheion]]
"""


def render_song_collage_index() -> str:
    return render_resonance_index()


def render_resonance_index() -> str:
    created = _today()
    return f"""---
type: index
status: active
created: {created}
tags:
  - index
  - iridescentia
---

# Resonance Index

## Purpose

Track Melographion sessions, song events, recurring inferred motifs, and the symbolic constellation that forms through resonance.

## Active Notes

- [[Melographion]]

## Reference Notes

- [[Song Collage Analysis II]]
- [[08 Iridescentia/Protocols/Mnemosynthesizer Protocol|Mnemosynthesizer Protocol]]

## Session Fields

- Sessions:
- Song events:
- Emerging themes:
- New orbits:

## Maintenance

- Last reviewed:
- Next review:
"""


def plan_init(settings: Settings, dry_run: bool = True) -> VaultWritePreview:
    paths = AxisariumPaths(settings.vault_path)
    writes = [
        PlannedWrite(
            target_path=str(paths.system_note),
            content=render_system_note(),
            kind="constellation",
            existed_before=paths.system_note.exists(),
        ),
        PlannedWrite(
            target_path=str(paths.project_note),
            content=render_project_note(),
            kind="project",
            existed_before=paths.project_note.exists(),
        ),
        PlannedWrite(
            target_path=str(paths.song_collage_index),
            content=render_song_collage_index(),
            kind="index",
            existed_before=paths.song_collage_index.exists(),
        ),
    ]
    index_writes, index_changes = plan_constellation_index_update(settings)
    writes.extend(index_writes)
    manifest = build_backup_manifest(
        vault_path=settings.vault_path,
        target_paths=[Path(write.target_path) for write in writes],
        backup_root=settings.backup_root,
        dry_run=dry_run,
    )
    return VaultWritePreview(writes=writes, backup_manifest=manifest, index_changes=index_changes)


def plan_index_rebuild(settings: Settings, dry_run: bool = True) -> VaultWritePreview:
    paths = AxisariumPaths(settings.vault_path)
    writes = [
        PlannedWrite(
            target_path=str(paths.song_collage_index),
            content=render_song_collage_index(),
            kind="index",
            existed_before=paths.song_collage_index.exists(),
        )
    ]
    index_writes, index_changes = plan_constellation_index_update(settings)
    writes.extend(index_writes)
    manifest = build_backup_manifest(
        vault_path=settings.vault_path,
        target_paths=[Path(write.target_path) for write in writes],
        backup_root=settings.backup_root,
        dry_run=dry_run,
    )
    return VaultWritePreview(writes=writes, backup_manifest=manifest, index_changes=index_changes)


def plan_session_export(
    settings: Settings,
    session: MelographionSession,
    profiles: dict[str, SongProfile],
    audio_features_by_event: dict[str, AudioFeatureSet] | None = None,
    dry_run: bool = True,
) -> VaultWritePreview:
    paths = AxisariumPaths(settings.vault_path)
    title = _session_title(session, profiles)
    target = paths.reflection_note_path(date_prefix(session.started_at), title, session.session_id[:8])
    graph_changes = preview_graph_update(settings, session=session)
    manifest = build_backup_manifest(
        vault_path=settings.vault_path,
        target_paths=[target],
        backup_root=settings.backup_root,
        dry_run=dry_run,
    )
    return VaultWritePreview(
        writes=[
            PlannedWrite(
                target_path=str(target),
                content=render_session_note(session, profiles, audio_features_by_event),
                kind="melographion-session",
                existed_before=target.exists(),
            )
        ],
        backup_manifest=manifest,
        graph_changes=graph_changes,
    )


def plan_reflection_export(
    settings: Settings,
    session: ReflectionSession,
    profile: SongProfile,
    audio_features: AudioFeatureSet | None = None,
    dry_run: bool = True,
) -> VaultWritePreview:
    canonical = session.to_session()
    event = canonical.latest_event()
    audio_map = {event.event_id: audio_features} if audio_features else {}
    return plan_session_export(
        settings,
        canonical,
        {profile.track_id: profile},
        audio_features_by_event=audio_map,
        dry_run=dry_run,
    )


def write_preview(settings: Settings, preview: VaultWritePreview) -> None:
    create_backup(preview.backup_manifest, settings.vault_path)
    for write in preview.writes:
        target = Path(write.target_path)
        assert_safe_vault_path(settings.vault_path, target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(write.content, encoding="utf-8")


def write_reflection_export(
    settings: Settings,
    session: ReflectionSession,
    profile: SongProfile,
    audio_features: AudioFeatureSet | None = None,
) -> tuple[VaultWritePreview, ReflectionSession]:
    preview = plan_reflection_export(settings, session, profile, audio_features, dry_run=False)
    write_preview(settings, preview)
    session.created_note_path = preview.writes[0].target_path
    update_graph(settings, profile=profile, session=session, audio_features=audio_features, dry_run=False)
    return preview, session


def write_session_export(
    settings: Settings,
    session: MelographionSession,
    profiles: dict[str, SongProfile],
    audio_features_by_event: dict[str, AudioFeatureSet] | None = None,
) -> tuple[VaultWritePreview, MelographionSession]:
    preview = plan_session_export(
        settings,
        session,
        profiles,
        audio_features_by_event=audio_features_by_event,
        dry_run=False,
    )
    write_preview(settings, preview)
    session.created_note_path = preview.writes[0].target_path
    update_graph(settings, session=session, dry_run=False)
    return preview, session


def plan_constellation_index_update(settings: Settings) -> tuple[list[PlannedWrite], list[str]]:
    paths = AxisariumPaths(settings.vault_path)
    target = paths.constellation_index
    if not target.exists():
        return [], [f"Constellation index not found: {target}"]
    content = target.read_text(encoding="utf-8")
    if "[[Melographion]]" in content:
        return [], ["Constellation Index already contains [[Melographion]]."]
    row = "| [[Melographion]] | Session-centered resonance engine for guided listening, verbatim capture, and inferred symbolic observation | active |"
    marker = "\n## Constellation Rules"
    if marker in content:
        updated = content.replace(marker, f"{row}\n{marker}", 1)
    else:
        updated = content.rstrip() + "\n" + row + "\n"
    return [PlannedWrite(target_path=str(target), content=updated, kind="index", existed_before=True)], [row]


def _profile_for_event(event: SessionEvent, profiles: dict[str, SongProfile]) -> SongProfile:
    return profiles.get(event.song_id) or SongProfile(
        track_id=event.song_id,
        track_name=event.song_id,
        artist_names=[],
        metadata_source="manual",
    )


def _session_title(session: MelographionSession, profiles: dict[str, SongProfile]) -> str:
    if session.title:
        return session.title
    if not session.events:
        return "Untitled Session"
    first = _profile_for_event(session.events[0], profiles)
    if len(session.events) == 1:
        return first.track_name
    return f"{first.track_name} + {len(session.events) - 1} more"


def _session_frame(session: MelographionSession) -> str:
    if session.can_have_arc_summary:
        return "This session contains multiple song events. Melographion may summarize the arc only after the ordered responses exist."
    return "This one-song session has a frame, but not a full arc summary. Melographion needs at least two events before it names a session arc."


def _session_reviewed(session: MelographionSession) -> bool:
    return bool(session.events) and all(
        event.reviewed_observations is not None for event in session.events
    )


def _session_interpretation_state(session: MelographionSession) -> str:
    if _session_reviewed(session):
        return "reviewed"
    if any(event.inferred_observations is not None for event in session.events):
        return "inferred"
    return "none"


def _session_emotional_tags(session: MelographionSession) -> list[str]:
    tags: list[str] = []
    for event in session.events:
        observations = event.reviewed_observations or event.inferred_observations
        if observations:
            tags.extend(observations.emotional_tags)
    return _unique(tags)


def _session_sonic_tags(audio_features_by_event: dict[str, AudioFeatureSet]) -> list[str]:
    tags: list[str] = []
    for features in audio_features_by_event.values():
        tags.extend(_sonic_tags(features))
    return _unique(tags)


def _sonic_tags(features: AudioFeatureSet | None) -> list[str]:
    if not features:
        return []
    tags = []
    if features.estimated_tempo and features.estimated_tempo >= 120:
        tags.append("kinetic")
    if features.rms_energy_mean and features.rms_energy_mean > 0.08:
        tags.append("high-energy")
    if features.silence_ratio and features.silence_ratio > 0.25:
        tags.append("spacious")
    return tags


def _symbolic_confidence(session: MelographionSession) -> float:
    signal_count = 0
    for event in session.events:
        observations = event.reviewed_observations or event.inferred_observations
        if not observations:
            continue
        signal_count += (
            len(observations.extracted_symbols)
            + len(observations.extracted_themes)
            + len(observations.emotional_tags)
            + len(observations.body_response)
        )
    if not signal_count:
        return 0.0
    return round(min(0.7, 0.25 + signal_count * 0.06), 2)


def _today() -> str:
    return date.today().isoformat()


def _inline_list(values: list[str]) -> str:
    return ", ".join(values) if values else "none inferred"


def _bullet_list(values: list[str]) -> str:
    if not values:
        return "- none inferred"
    return "\n".join(f"- {value}" for value in values)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
