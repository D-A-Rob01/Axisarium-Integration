from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utcish_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class SongProfile(BaseModel):
    track_id: str
    track_name: str
    artist_names: list[str] = Field(default_factory=list)
    album: str = ""
    duration_ms: int | None = None
    spotify_url: str = ""
    playlist_name: str = ""
    date_added: str | None = None
    metadata_source: str = "spotify"
    tags: list[str] = Field(default_factory=list)
    emotional_vector: dict[str, float] = Field(default_factory=dict)
    sonic_vector: dict[str, float] = Field(default_factory=dict)
    lyric_vector: dict[str, Any] = Field(default_factory=dict)
    symbolic_vector: dict[str, float] = Field(default_factory=dict)
    lyric_reference: str | None = None
    audio_feature_path: str | None = None
    created_at: str = Field(default_factory=utcish_now)
    updated_at: str = Field(default_factory=utcish_now)

    @property
    def display_artist(self) -> str:
        return ", ".join(self.artist_names) if self.artist_names else "Unknown Artist"


EventStatus = Literal[
    "pending_prompt",
    "response_captured",
    "inference_pending",
    "inference_reviewed",
    "next_song_suggested",
    "complete",
]


class ObservationSet(BaseModel):
    extracted_themes: list[str] = Field(default_factory=list)
    extracted_symbols: list[str] = Field(default_factory=list)
    body_response: list[str] = Field(default_factory=list)
    memories: list[str] = Field(default_factory=list)
    emotional_valence: str = "unclear"
    emotional_tags: list[str] = Field(default_factory=list)
    intensity_score: float = 0.0
    analysis_status: Literal["inferred", "reviewed"] = "inferred"
    review_note: str = ""

    @classmethod
    def from_analyzer(cls, payload: dict[str, object]) -> "ObservationSet":
        return cls.model_validate({**payload, "analysis_status": "inferred"})


class SessionEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    sequence: int
    song_id: str
    prompt: str
    status: EventStatus = "pending_prompt"
    user_response_verbatim: str = ""
    inferred_observations: ObservationSet | None = None
    reviewed_observations: ObservationSet | None = None
    audio_feature_path: str | None = None
    lyric_reference: str | None = None
    next_song_id: str | None = None
    next_song_reasoning_private: str = ""
    next_song_reasoning_public: str = ""
    created_at: str = Field(default_factory=utcish_now)
    updated_at: str = Field(default_factory=utcish_now)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "user_response_verbatim":
            existing = getattr(self, "user_response_verbatim", "")
            if existing and value != existing:
                raise ValueError("user_response_verbatim is immutable once captured.")
        super().__setattr__(name, value)

    def capture_response(self, response: str) -> None:
        if self.user_response_verbatim and response != self.user_response_verbatim:
            raise ValueError("Refusing to overwrite user_response_verbatim.")
        self.user_response_verbatim = response
        self.status = "response_captured"
        self.updated_at = utcish_now()

    def set_inferred_observations(self, observations: ObservationSet) -> None:
        self.inferred_observations = observations
        self.status = "inference_pending"
        self.updated_at = utcish_now()

    def review_observations(self, observations: ObservationSet) -> None:
        self.reviewed_observations = observations.model_copy(update={"analysis_status": "reviewed"})
        self.status = "inference_reviewed"
        self.updated_at = utcish_now()

    def suggest_next_song(
        self,
        *,
        song_id: str,
        reasoning_public: str,
        reasoning_private: str = "",
    ) -> None:
        self.next_song_id = song_id
        self.next_song_reasoning_public = reasoning_public
        self.next_song_reasoning_private = reasoning_private
        self.status = "next_song_suggested"
        self.updated_at = utcish_now()

    def complete(self) -> None:
        if not self.user_response_verbatim:
            raise ValueError("Cannot complete an event without a verbatim response.")
        if self.reviewed_observations is None:
            raise ValueError("Cannot complete an event until observations are reviewed or explicitly deferred.")
        self.status = "complete"
        self.updated_at = utcish_now()


class MelographionSession(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    started_at: str = Field(default_factory=utcish_now)
    updated_at: str = Field(default_factory=utcish_now)
    status: Literal["active", "complete", "archived"] = "active"
    mode: str = "manual"
    title: str = ""
    events: list[SessionEvent] = Field(default_factory=list)
    session_summary: str = ""
    session_themes: list[str] = Field(default_factory=list)
    session_symbols: list[str] = Field(default_factory=list)
    body_map: dict[str, list[str]] = Field(default_factory=dict)
    emotional_arc: list[str] = Field(default_factory=list)
    created_note_path: str | None = None

    def add_event(self, song_id: str, prompt: str) -> SessionEvent:
        event = SessionEvent(sequence=len(self.events) + 1, song_id=song_id, prompt=prompt)
        self.events.append(event)
        self.updated_at = utcish_now()
        return event

    def get_event(self, event_id: str | None = None, sequence: int | None = None) -> SessionEvent:
        if event_id:
            for event in self.events:
                if event.event_id == event_id:
                    return event
        if sequence is not None:
            for event in self.events:
                if event.sequence == sequence:
                    return event
        raise ValueError("Session event not found.")

    def latest_event(self) -> SessionEvent:
        if not self.events:
            raise ValueError("Session has no events.")
        return self.events[-1]

    @property
    def can_have_arc_summary(self) -> bool:
        return len(self.events) >= 2

    def refresh_rollups(self) -> None:
        themes: list[str] = []
        symbols: list[str] = []
        emotional_arc: list[str] = []
        body_map: dict[str, list[str]] = {}
        for event in self.events:
            observations = event.reviewed_observations or event.inferred_observations
            if observations is None:
                continue
            themes.extend(observations.extracted_themes)
            symbols.extend(observations.extracted_symbols)
            if observations.emotional_valence != "unclear":
                emotional_arc.append(observations.emotional_valence)
            for body in observations.body_response:
                body_map.setdefault(body, []).append(event.event_id)
        self.session_themes = _unique(themes)
        self.session_symbols = _unique(symbols)
        self.body_map = body_map
        self.emotional_arc = emotional_arc
        self.updated_at = utcish_now()

    @classmethod
    def from_reflection(cls, reflection: "ReflectionSession") -> "MelographionSession":
        event = SessionEvent(
            event_id=reflection.session_id,
            sequence=1,
            song_id=reflection.song_id,
            prompt=reflection.prompt,
            status="inference_pending",
            user_response_verbatim=reflection.user_response,
            inferred_observations=ObservationSet(
                extracted_themes=reflection.extracted_themes,
                extracted_symbols=reflection.extracted_symbols,
                body_response=reflection.body_response,
                memories=reflection.memories,
                emotional_valence=reflection.emotional_valence,
                emotional_tags=reflection.emotional_tags,
                intensity_score=reflection.intensity_score,
                analysis_status="inferred",
            ),
            audio_feature_path=reflection.audio_feature_path,
            next_song_reasoning_private=reflection.next_song_reasoning_private,
            next_song_reasoning_public=reflection.next_song_reasoning_public,
        )
        session = cls(
            session_id=reflection.session_id,
            started_at=reflection.date,
            updated_at=reflection.date,
            mode=reflection.mode,
            events=[event],
            created_note_path=reflection.created_note_path,
        )
        session.refresh_rollups()
        return session


class ReflectionSession(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    date: str = Field(default_factory=utcish_now)
    song_id: str
    prompt: str
    user_response: str
    mode: str = "manual"
    extracted_themes: list[str] = Field(default_factory=list)
    extracted_symbols: list[str] = Field(default_factory=list)
    body_response: list[str] = Field(default_factory=list)
    memories: list[str] = Field(default_factory=list)
    emotional_valence: str = "unclear"
    emotional_tags: list[str] = Field(default_factory=list)
    intensity_score: float = 0.0
    analysis_status: Literal["inferred"] = "inferred"
    next_song_reasoning_private: str = ""
    next_song_reasoning_public: str = ""
    created_note_path: str | None = None
    audio_feature_path: str | None = None

    def to_session(self) -> MelographionSession:
        return MelographionSession.from_reflection(self)


class SymbolNode(BaseModel):
    label: str
    type: str
    aliases: list[str] = Field(default_factory=list)
    related_songs: list[str] = Field(default_factory=list)
    related_notes: list[str] = Field(default_factory=list)
    strength: float = 1.0
    first_seen: str = Field(default_factory=utcish_now)
    last_seen: str = Field(default_factory=utcish_now)


class AudioFeatureSet(BaseModel):
    audio_id: str = Field(default_factory=lambda: uuid4().hex)
    source_path: str
    imported_path: str | None = None
    song_id: str | None = None
    created_at: str = Field(default_factory=utcish_now)
    analyzer: str
    duration_seconds: float | None = None
    estimated_tempo: float | None = None
    rms_energy_mean: float | None = None
    rms_energy_std: float | None = None
    dynamic_contour: list[float] = Field(default_factory=list)
    loudness_intensity_shape: list[float] = Field(default_factory=list)
    onset_density: float | None = None
    silence_ratio: float | None = None
    spectral_centroid_mean: float | None = None
    spectral_centroid_std: float | None = None
    spectral_contrast_mean: float | None = None
    zero_crossing_rate_mean: float | None = None
    section_change_estimates: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphChange(BaseModel):
    nodes_added: list[dict[str, Any]] = Field(default_factory=list)
    nodes_updated: list[dict[str, Any]] = Field(default_factory=list)
    edges_added: list[dict[str, Any]] = Field(default_factory=list)
    edges_updated: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any([self.nodes_added, self.nodes_updated, self.edges_added, self.edges_updated])


class PlannedWrite(BaseModel):
    target_path: str
    content: str
    kind: str = "note"
    existed_before: bool = False


class BackupManifest(BaseModel):
    created_at: str = Field(default_factory=utcish_now)
    dry_run: bool = True
    backup_zip: str | None = None
    manifest_path: str | None = None
    target_paths: list[str] = Field(default_factory=list)
    existing_paths: list[str] = Field(default_factory=list)
    missing_paths: list[str] = Field(default_factory=list)


class VaultWritePreview(BaseModel):
    writes: list[PlannedWrite] = Field(default_factory=list)
    backup_manifest: BackupManifest
    graph_changes: GraphChange = Field(default_factory=GraphChange)
    index_changes: list[str] = Field(default_factory=list)

    def render(self) -> str:
        lines: list[str] = ["== Proposed Vault Write =="]
        for write in self.writes:
            lines.append(f"\n--- Target: {write.target_path}")
            lines.append(f"Kind: {write.kind}")
            lines.append(f"Existed before: {write.existed_before}")
            lines.append("")
            lines.append(write.content)
        lines.append("\n== Backup Manifest ==")
        lines.append(self.backup_manifest.model_dump_json(indent=2))
        lines.append("\n== Constellation Changes ==")
        lines.append("")
        lines.append("Nodes")
        lines.append(
            self._render_json(
                {
                    "added": self.graph_changes.nodes_added,
                    "updated": self.graph_changes.nodes_updated,
                }
            )
        )
        lines.append("")
        lines.append("Edges")
        lines.append(
            self._render_json(
                {
                    "added": self.graph_changes.edges_added,
                    "updated": self.graph_changes.edges_updated,
                }
            )
        )
        lines.append("")
        lines.append("New Orbits")
        lines.append(self._render_json([]))
        lines.append("")
        lines.append("Emerging Themes")
        lines.append(self._render_json(self._emerging_themes()))
        lines.append("\n== Index Changes ==")
        lines.extend(self.index_changes or ["(none)"])
        return "\n".join(lines)

    def _emerging_themes(self) -> list[dict[str, Any]]:
        themes: list[dict[str, Any]] = []
        for node in self.graph_changes.nodes_added + self.graph_changes.nodes_updated:
            if node.get("type") in {"symbol", "emotion", "body_response", "memory"}:
                themes.append(node)
        return themes

    @staticmethod
    def _render_json(payload: Any) -> str:
        import json

        return json.dumps(payload, indent=2, ensure_ascii=False)


def path_to_str(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(Path(path))


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
