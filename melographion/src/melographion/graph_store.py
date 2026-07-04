from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Settings
from .models import AudioFeatureSet, GraphChange, MelographionSession, ReflectionSession, SongProfile
from .storage import read_json, write_json


def empty_graph() -> dict[str, Any]:
    return {"nodes": [], "edges": []}


def load_graph(settings: Settings) -> dict[str, Any]:
    return read_json(settings.graph_path, empty_graph())


def preview_graph_update(
    settings: Settings,
    *,
    profile: SongProfile | None = None,
    session: MelographionSession | ReflectionSession | None = None,
    audio_features: AudioFeatureSet | None = None,
) -> GraphChange:
    graph = load_graph(settings)
    return _apply_to_graph(graph, profile=profile, session=session, audio_features=audio_features, mutate=False)


def update_graph(
    settings: Settings,
    *,
    profile: SongProfile | None = None,
    session: MelographionSession | ReflectionSession | None = None,
    audio_features: AudioFeatureSet | None = None,
    dry_run: bool = False,
) -> GraphChange:
    graph = load_graph(settings)
    changes = _apply_to_graph(
        graph, profile=profile, session=session, audio_features=audio_features, mutate=True
    )
    if not dry_run and changes.has_changes:
        write_json(settings.graph_path, graph)
    return changes


def _apply_to_graph(
    graph: dict[str, Any],
    *,
    profile: SongProfile | None,
    session: MelographionSession | ReflectionSession | None,
    audio_features: AudioFeatureSet | None,
    mutate: bool,
) -> GraphChange:
    nodes_by_id = {node["id"]: node for node in graph.get("nodes", [])}
    edge_keys = {
        (edge["source"], edge["target"], edge["type"]): edge for edge in graph.get("edges", [])
    }
    changes = GraphChange()

    def add_node(node_id: str, node_type: str, label: str, **attrs) -> None:
        payload = {"id": node_id, "type": node_type, "label": label, **attrs}
        if node_id not in nodes_by_id:
            changes.nodes_added.append(payload)
            nodes_by_id[node_id] = payload
            if mutate:
                graph.setdefault("nodes", []).append(payload)
        else:
            current = nodes_by_id[node_id]
            updates = {key: value for key, value in payload.items() if current.get(key) != value}
            if updates:
                changes.nodes_updated.append({"id": node_id, **updates})
                if mutate:
                    current.update(updates)

    def add_edge(source: str, target: str, edge_type: str, **attrs) -> None:
        key = (source, target, edge_type)
        payload = {"source": source, "target": target, "type": edge_type, **attrs}
        if key not in edge_keys:
            changes.edges_added.append(payload)
            edge_keys[key] = payload
            if mutate:
                graph.setdefault("edges", []).append(payload)
        else:
            current = edge_keys[key]
            updates = {name: value for name, value in payload.items() if current.get(name) != value}
            if updates:
                changes.edges_updated.append({"source": source, "target": target, "type": edge_type, **updates})
                if mutate:
                    current.update(updates)

    if profile:
        song_node = f"song:{profile.track_id}"
        add_node(song_node, "song", profile.track_name, spotify_url=profile.spotify_url)
        for artist in profile.artist_names:
            artist_node = f"artist:{artist.casefold()}"
            add_node(artist_node, "artist", artist)
            add_edge(song_node, artist_node, "by")
        for tag in profile.tags:
            tag_node = f"tag:{tag.casefold()}"
            add_node(tag_node, "tag", tag)
            add_edge(song_node, tag_node, "tagged")

    if session:
        canonical = session.to_session() if isinstance(session, ReflectionSession) else session
        session_node = f"session:{canonical.session_id}"
        add_node(
            session_node,
            "session",
            canonical.title or canonical.session_id,
            status=canonical.status,
            started_at=canonical.started_at,
        )
        for theme in canonical.session_themes:
            theme_node = f"theme:{theme.casefold()}"
            add_node(theme_node, "theme", theme)
            add_edge(session_node, theme_node, "develops")
        for symbol in canonical.session_symbols:
            symbol_node = f"symbol:{symbol.casefold()}"
            add_node(symbol_node, "symbol", symbol)
            add_edge(session_node, symbol_node, "evokes")
        for event in canonical.events:
            event_node = f"event:{canonical.session_id}:{event.sequence}"
            add_node(
                event_node,
                "session_event",
                f"Event {event.sequence}",
                status=event.status,
                sequence=event.sequence,
            )
            add_edge(session_node, event_node, "contains")
            add_edge(event_node, f"song:{event.song_id}", "uses_song")
            observations = event.reviewed_observations or event.inferred_observations
            if observations:
                analysis_status = observations.analysis_status
                for symbol in observations.extracted_symbols:
                    symbol_node = f"symbol:{symbol.casefold()}"
                    add_node(symbol_node, "symbol", symbol)
                    add_edge(event_node, symbol_node, "evokes", analysis_status=analysis_status)
                for emotion in observations.emotional_tags:
                    emotion_node = f"emotion:{emotion.casefold()}"
                    add_node(emotion_node, "emotion", emotion)
                    add_edge(event_node, emotion_node, "evokes", analysis_status=analysis_status)
                for body in observations.body_response:
                    body_node = f"body:{body.casefold()}"
                    add_node(body_node, "body_response", body)
                    add_edge(event_node, body_node, "lands_in", analysis_status=analysis_status)
                for memory in observations.memories:
                    memory_node = f"memory:{memory[:80].casefold()}"
                    add_node(memory_node, "memory", memory)
                    add_edge(event_node, memory_node, "recalls", analysis_status=analysis_status)
            if event.next_song_id:
                add_edge(event_node, f"song:{event.next_song_id}", "suggests_next")
        if canonical.created_note_path:
            note_node = f"vault_note:{canonical.created_note_path}"
            add_node(note_node, "vault_note", Path(canonical.created_note_path).stem)
            add_edge(session_node, note_node, "links_to")

    if audio_features:
        audio_node = f"audio:{audio_features.audio_id}"
        add_node(audio_node, "audio_features", audio_features.audio_id, analyzer=audio_features.analyzer)
        if audio_features.song_id:
            add_edge(audio_node, f"song:{audio_features.song_id}", "analyzes")

    return changes
