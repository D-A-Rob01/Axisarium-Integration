from __future__ import annotations

import json
from pathlib import Path

import typer

from .audio_features import analyze_audio_file
from .audio_ingest.manual_file import import_audio_file
from .config import ensure_local_dirs, load_settings
from .graph_store import update_graph
from .lyric_ingest import ingest_lyrics_text
from .models import AudioFeatureSet, MelographionSession, ObservationSet, ReflectionSession
from .obsidian_exporter import (
    plan_index_rebuild,
    plan_init,
    plan_reflection_export,
    plan_session_export,
    write_preview,
    write_reflection_export,
    write_session_export,
)
from .prompt_engine import generate_prompt
from .response_analyzer import analyze_response
from .song_selector import suggest_song
from .spotify_client import authenticate, list_playlists, load_playlist
from .storage import (
    latest_reflection,
    latest_session,
    load_reflection,
    load_session,
    load_song_profile,
    save_audio_features,
    save_reflection,
    save_session,
    save_song_profile,
)


app = typer.Typer(help="Melographion resonance-session CLI.")
playlist_app = typer.Typer(help="Spotify playlist commands.")
song_app = typer.Typer(help="Song suggestion, reflection, and analysis commands.")
audio_app = typer.Typer(help="Manual audio ingest commands.")
graph_app = typer.Typer(help="Local graph commands.")
index_app = typer.Typer(help="Vault index commands.")
session_app = typer.Typer(help="Session-first Melographion commands.")

app.add_typer(playlist_app, name="playlist")
app.add_typer(song_app, name="song")
app.add_typer(audio_app, name="audio")
app.add_typer(graph_app, name="graph")
app.add_typer(index_app, name="index")
app.add_typer(session_app, name="session")


@app.command()
def init(
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--write",
        help="Preview vault writes by default. Use --write to create files.",
    )
):
    settings = load_settings()
    dirs = ensure_local_dirs(settings, dry_run=dry_run)
    preview = plan_init(settings, dry_run=dry_run)
    typer.echo("Local directories:")
    for directory in dirs:
        typer.echo(f"- {directory}")
    typer.echo(preview.render())
    if not dry_run:
        write_preview(settings, preview)
        typer.echo("Melographion vault scaffolding written after backup creation.")


@app.command("spotify-auth")
def spotify_auth():
    settings = load_settings()
    user = authenticate(settings)
    typer.echo(f"Spotify authentication succeeded for {user}.")


@playlist_app.command("list")
def playlist_list():
    settings = load_settings()
    playlists = list_playlists(settings)
    if not playlists:
        typer.echo("No playlists returned.")
        return
    for playlist in playlists:
        typer.echo(
            f"{playlist['name']} | tracks: {playlist.get('tracks_total')} | owner: {playlist.get('owner')}"
        )


@playlist_app.command("load")
def playlist_load(name: str):
    settings = load_settings()
    cache_path, profiles = load_playlist(settings, name)
    typer.echo(f"Loaded {len(profiles)} tracks.")
    typer.echo(f"Playlist cache: {cache_path}")


@song_app.command("suggest")
def song_suggest(mode: str = typer.Option("random", "--mode", "-m")):
    settings = load_settings()
    profile, reasoning = suggest_song(settings, mode=mode)
    typer.echo(f"{profile.track_id}: {profile.track_name} - {profile.display_artist}")
    typer.echo(reasoning)


@song_app.command("reflect")
def song_reflect(
    song_id: str = typer.Option(..., "--song-id"),
    mode: str = typer.Option("manual", "--mode"),
    response: str | None = typer.Option(None, "--response", help="Optional response text."),
    lyrics_file: Path | None = typer.Option(None, "--lyrics-file"),
    lyrics_url: str | None = typer.Option(None, "--lyrics-url"),
):
    settings = load_settings()
    profile = load_song_profile(settings, song_id)
    lyric_payload = ingest_lyrics_text(lyrics_file, lyrics_url)
    if lyric_payload["features"]:
        profile.lyric_vector = lyric_payload["features"]
    if lyric_payload["reference"]:
        profile.lyric_reference = lyric_payload["reference"]
    prompt = generate_prompt(profile, mode=mode)
    typer.echo(prompt)
    captured_response = response if response is not None else typer.prompt("Response")
    session = MelographionSession(mode=mode)
    event = session.add_event(song_id=song_id, prompt=prompt)
    event.capture_response(captured_response)
    event.set_inferred_observations(ObservationSet.from_analyzer(analyze_response(captured_response)))
    save_song_profile(settings, profile)
    session_path = save_session(settings, session)
    changes = update_graph(settings, profile=profile, session=session, dry_run=False)
    typer.echo(f"Session captured: {session.session_id}")
    typer.echo(f"Event captured: {event.event_id}")
    typer.echo(f"Saved session: {session_path}")
    typer.echo(f"Constellation changes: {changes.model_dump_json(indent=2)}")


@session_app.command("start")
def session_start(
    song_id: str = typer.Option(..., "--song-id"),
    mode: str = typer.Option("manual", "--mode"),
    title: str = typer.Option("", "--title"),
):
    settings = load_settings()
    profile = load_song_profile(settings, song_id)
    prompt = generate_prompt(profile, mode=mode)
    session = MelographionSession(mode=mode, title=title)
    event = session.add_event(song_id=song_id, prompt=prompt)
    path = save_session(settings, session)
    changes = update_graph(settings, profile=profile, session=session, dry_run=False)
    typer.echo(f"Session started: {session.session_id}")
    typer.echo(f"Event pending prompt: {event.event_id}")
    typer.echo(prompt)
    typer.echo(f"Saved session: {path}")
    typer.echo(f"Constellation changes: {changes.model_dump_json(indent=2)}")


@session_app.command("capture-response")
def session_capture_response(
    session_id: str = typer.Option(..., "--session-id"),
    event_id: str | None = typer.Option(None, "--event-id"),
    sequence: int | None = typer.Option(None, "--sequence"),
    response: str | None = typer.Option(None, "--response"),
):
    settings = load_settings()
    session = load_session(settings, session_id)
    event = _select_event(session, event_id, sequence)
    captured = response if response is not None else typer.prompt("Response")
    event.capture_response(captured)
    path = save_session(settings, session)
    typer.echo(f"Response captured for event {event.event_id}.")
    typer.echo(f"Saved session: {path}")


@session_app.command("infer")
def session_infer(
    session_id: str = typer.Option(..., "--session-id"),
    event_id: str | None = typer.Option(None, "--event-id"),
    sequence: int | None = typer.Option(None, "--sequence"),
):
    settings = load_settings()
    session = load_session(settings, session_id)
    event = _select_event(session, event_id, sequence)
    if not event.user_response_verbatim:
        raise typer.BadParameter("Capture a verbatim response before running inference.")
    event.set_inferred_observations(
        ObservationSet.from_analyzer(analyze_response(event.user_response_verbatim))
    )
    path = save_session(settings, session)
    typer.echo(f"Inference recorded for event {event.event_id}.")
    typer.echo(f"Saved session: {path}")


@session_app.command("review-inference")
def session_review_inference(
    session_id: str = typer.Option(..., "--session-id"),
    event_id: str | None = typer.Option(None, "--event-id"),
    sequence: int | None = typer.Option(None, "--sequence"),
    review_note: str = typer.Option("", "--review-note"),
):
    settings = load_settings()
    session = load_session(settings, session_id)
    event = _select_event(session, event_id, sequence)
    if event.inferred_observations is None:
        raise typer.BadParameter("Run inference before reviewing observations.")
    reviewed = event.inferred_observations.model_copy(
        update={"analysis_status": "reviewed", "review_note": review_note}
    )
    event.review_observations(reviewed)
    path = save_session(settings, session)
    typer.echo(f"Reviewed observations recorded for event {event.event_id}.")
    typer.echo(f"Saved session: {path}")


@session_app.command("next-song")
def session_next_song(
    session_id: str = typer.Option(..., "--session-id"),
    event_id: str | None = typer.Option(None, "--event-id"),
    sequence: int | None = typer.Option(None, "--sequence"),
    mode: str = typer.Option("resonance", "--mode"),
):
    settings = load_settings()
    session = load_session(settings, session_id)
    event = _select_event(session, event_id, sequence)
    profile, reasoning = suggest_song(settings, mode=mode)
    event.suggest_next_song(song_id=profile.track_id, reasoning_public=reasoning)
    path = save_session(settings, session)
    typer.echo(f"Next song suggested for event {event.event_id}: {profile.track_name} - {profile.display_artist}")
    typer.echo(reasoning)
    typer.echo(f"Saved session: {path}")


@session_app.command("complete-event")
def session_complete_event(
    session_id: str = typer.Option(..., "--session-id"),
    event_id: str | None = typer.Option(None, "--event-id"),
    sequence: int | None = typer.Option(None, "--sequence"),
):
    settings = load_settings()
    session = load_session(settings, session_id)
    event = _select_event(session, event_id, sequence)
    event.complete()
    path = save_session(settings, session)
    typer.echo(f"Event completed: {event.event_id}")
    typer.echo(f"Saved session: {path}")


@session_app.command("add-song")
def session_add_song(
    session_id: str = typer.Option(..., "--session-id"),
    song_id: str = typer.Option(..., "--song-id"),
):
    settings = load_settings()
    session = load_session(settings, session_id)
    profile = load_song_profile(settings, song_id)
    prompt = generate_prompt(profile, mode=session.mode)
    event = session.add_event(song_id=song_id, prompt=prompt)
    path = save_session(settings, session)
    changes = update_graph(settings, profile=profile, session=session, dry_run=False)
    typer.echo(f"Added event {event.event_id} as sequence {event.sequence}.")
    typer.echo(prompt)
    typer.echo(f"Saved session: {path}")
    typer.echo(f"Constellation changes: {changes.model_dump_json(indent=2)}")


@session_app.command("show")
def session_show(session_id: str = typer.Option(..., "--session-id")):
    settings = load_settings()
    session = load_session(settings, session_id)
    typer.echo(session.model_dump_json(indent=2))


@session_app.command("export")
def session_export(
    session_id: str = typer.Option(..., "--session-id"),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--write",
        help="Preview vault writes by default. Use --write to export.",
    ),
):
    settings = load_settings()
    session = load_session(settings, session_id)
    profiles = _profiles_for_session(settings, session)
    audio_features = _audio_features_for_session(session)
    if dry_run:
        preview = plan_session_export(settings, session, profiles, audio_features, dry_run=True)
        typer.echo(preview.render())
        return
    preview, updated_session = write_session_export(settings, session, profiles, audio_features)
    save_session(settings, updated_session)
    typer.echo(preview.render())
    typer.echo("Session note exported after backup creation.")


@song_app.command("analyze-audio")
def song_analyze_audio(path: Path, song_id: str = typer.Option(..., "--song-id")):
    settings = load_settings()
    profile = load_song_profile(settings, song_id)
    features = analyze_audio_file(path, song_id=song_id)
    feature_path = save_audio_features(settings, features)
    profile.audio_feature_path = str(feature_path)
    profile.sonic_vector = _sonic_vector_from_features(features)
    save_song_profile(settings, profile)
    changes = update_graph(settings, profile=profile, audio_features=features, dry_run=False)
    typer.echo(f"Audio features saved: {feature_path}")
    typer.echo(features.model_dump_json(indent=2))
    typer.echo(f"Constellation changes: {changes.model_dump_json(indent=2)}")


@audio_app.command("import")
def audio_import(path: Path, song_id: str = typer.Option(..., "--song-id")):
    settings = load_settings()
    profile = load_song_profile(settings, song_id)
    imported_path, features, feature_path = import_audio_file(
        path, song_id=song_id, settings=settings, copy_to_inbox=True
    )
    profile.audio_feature_path = str(feature_path)
    profile.sonic_vector = _sonic_vector_from_features(features)
    save_song_profile(settings, profile)
    changes = update_graph(settings, profile=profile, audio_features=features, dry_run=False)
    typer.echo(f"Imported audio: {imported_path}")
    typer.echo(f"Audio features saved: {feature_path}")
    typer.echo(f"Constellation changes: {changes.model_dump_json(indent=2)}")


@app.command("export-note")
def export_note(
    session_id: str | None = typer.Option(None, "--session-id"),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--write",
        help="Preview vault writes by default. Use --write to export.",
    ),
):
    settings = load_settings()
    session = load_session(settings, session_id) if session_id else latest_session(settings)
    if not session:
        raise typer.BadParameter("No Melographion session found.")
    profiles = _profiles_for_session(settings, session)
    audio_features = _audio_features_for_session(session)
    if dry_run:
        preview = plan_session_export(settings, session, profiles, audio_features, dry_run=True)
        typer.echo(preview.render())
        return
    preview, updated_session = write_session_export(settings, session, profiles, audio_features)
    save_session(settings, updated_session)
    typer.echo(preview.render())
    typer.echo("Session note exported after backup creation.")


@graph_app.command("update")
def graph_update(
    session_id: str | None = typer.Option(None, "--session-id"),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--write",
        help="Preview constellation changes by default. Use --write to persist.",
    ),
):
    settings = load_settings()
    session = load_session(settings, session_id) if session_id else latest_session(settings)
    if not session:
        raise typer.BadParameter("No Melographion session found.")
    changes = update_graph(
        settings,
        session=session,
        dry_run=dry_run,
    )
    typer.echo(changes.model_dump_json(indent=2))
    if dry_run:
        typer.echo(f"Dry-run only. Graph target would be: {settings.graph_path}")
    else:
        typer.echo(f"Graph updated: {settings.graph_path}")


def _index_rebuild_impl(dry_run: bool) -> None:
    settings = load_settings()
    preview = plan_index_rebuild(settings, dry_run=dry_run)
    typer.echo(preview.render())
    if not dry_run:
        write_preview(settings, preview)
        typer.echo("Indexes rebuilt after backup creation.")


@index_app.command("rebuild")
def index_rebuild(
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--write",
        help="Preview vault writes by default. Use --write to rebuild indexes.",
    ),
):
    _index_rebuild_impl(dry_run)


@app.command("index-rebuild")
def index_rebuild_alias(
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--write",
        help="Preview vault writes by default. Use --write to rebuild indexes.",
    ),
):
    _index_rebuild_impl(dry_run)


def _load_linked_audio_features(path_text: str | None) -> AudioFeatureSet | None:
    if not path_text:
        return None
    path = Path(path_text)
    if not path.exists():
        return None
    return AudioFeatureSet.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _select_event(
    session: MelographionSession,
    event_id: str | None = None,
    sequence: int | None = None,
):
    if event_id or sequence is not None:
        return session.get_event(event_id=event_id, sequence=sequence)
    return session.latest_event()


def _profiles_for_session(settings, session: MelographionSession) -> dict[str, object]:
    profiles = {}
    for event in session.events:
        if event.song_id in profiles:
            continue
        profiles[event.song_id] = load_song_profile(settings, event.song_id)
    return profiles


def _audio_features_for_session(session: MelographionSession) -> dict[str, AudioFeatureSet]:
    features = {}
    for event in session.events:
        loaded = _load_linked_audio_features(event.audio_feature_path)
        if loaded:
            features[event.event_id] = loaded
    return features


def _sonic_vector_from_features(features: AudioFeatureSet) -> dict[str, float]:
    return {
        "duration_seconds": features.duration_seconds or 0.0,
        "estimated_tempo": features.estimated_tempo or 0.0,
        "rms_energy_mean": features.rms_energy_mean or 0.0,
        "silence_ratio": features.silence_ratio or 0.0,
    }


def main() -> None:
    app()


if __name__ == "__main__":
    main()
