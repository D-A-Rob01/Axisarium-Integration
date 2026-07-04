from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from .config import Settings
from .models import AudioFeatureSet, MelographionSession, ReflectionSession, SongProfile
from .vault_paths import sanitize_filename

ModelT = TypeVar("ModelT", bound=BaseModel)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_model(path: Path, model: BaseModel) -> None:
    write_json(path, model.model_dump(mode="json"))


def load_model(path: Path, model_type: type[ModelT]) -> ModelT:
    return model_type.model_validate(read_json(path, {}))


def profile_path(settings: Settings, track_id: str) -> Path:
    return settings.song_profiles_dir / f"{sanitize_filename(track_id)}.json"


def save_song_profile(settings: Settings, profile: SongProfile) -> Path:
    path = profile_path(settings, profile.track_id)
    save_model(path, profile)
    return path


def load_song_profile(settings: Settings, track_id: str) -> SongProfile:
    return load_model(profile_path(settings, track_id), SongProfile)


def list_song_profiles(settings: Settings) -> list[SongProfile]:
    if not settings.song_profiles_dir.exists():
        return []
    profiles = []
    for path in sorted(settings.song_profiles_dir.glob("*.json")):
        try:
            profiles.append(load_model(path, SongProfile))
        except Exception:
            continue
    return profiles


def reflection_path(settings: Settings, session_id: str) -> Path:
    return settings.reflections_dir / f"{sanitize_filename(session_id)}.json"


def save_reflection(settings: Settings, session: ReflectionSession) -> Path:
    path = reflection_path(settings, session.session_id)
    save_model(path, session)
    return path


def load_reflection(settings: Settings, session_id: str) -> ReflectionSession:
    return load_model(reflection_path(settings, session_id), ReflectionSession)


def latest_reflection(settings: Settings) -> ReflectionSession | None:
    if not settings.reflections_dir.exists():
        return None
    paths = sorted(settings.reflections_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not paths:
        return None
    return load_model(paths[-1], ReflectionSession)


def session_path(settings: Settings, session_id: str) -> Path:
    return settings.sessions_dir / f"{sanitize_filename(session_id)}.json"


def save_session(settings: Settings, session: MelographionSession) -> Path:
    session.refresh_rollups()
    path = session_path(settings, session.session_id)
    save_model(path, session)
    return path


def load_session(settings: Settings, session_id: str) -> MelographionSession:
    canonical_path = session_path(settings, session_id)
    if canonical_path.exists():
        return load_model(canonical_path, MelographionSession)
    legacy_path = reflection_path(settings, session_id)
    if legacy_path.exists():
        return load_reflection(settings, session_id).to_session()
    raise FileNotFoundError(canonical_path)


def latest_session(settings: Settings) -> MelographionSession | None:
    session_paths = []
    if settings.sessions_dir.exists():
        session_paths.extend(settings.sessions_dir.glob("*.json"))
    if session_paths:
        latest_path = sorted(session_paths, key=lambda p: p.stat().st_mtime)[-1]
        return load_model(latest_path, MelographionSession)
    reflection = latest_reflection(settings)
    return reflection.to_session() if reflection else None


def list_sessions(settings: Settings) -> list[MelographionSession]:
    sessions: list[MelographionSession] = []
    if settings.sessions_dir.exists():
        for path in sorted(settings.sessions_dir.glob("*.json")):
            try:
                sessions.append(load_model(path, MelographionSession))
            except Exception:
                continue
    if sessions:
        return sessions
    if settings.reflections_dir.exists():
        for path in sorted(settings.reflections_dir.glob("*.json")):
            try:
                sessions.append(load_model(path, ReflectionSession).to_session())
            except Exception:
                continue
    return sessions


def audio_features_path(settings: Settings, audio_id: str) -> Path:
    return settings.audio_features_dir / f"{sanitize_filename(audio_id)}.json"


def save_audio_features(settings: Settings, features: AudioFeatureSet) -> Path:
    path = audio_features_path(settings, features.audio_id)
    save_model(path, features)
    return path


def load_audio_features(settings: Settings, audio_id: str) -> AudioFeatureSet:
    return load_model(audio_features_path(settings, audio_id), AudioFeatureSet)
