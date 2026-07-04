from __future__ import annotations

from pathlib import Path

from melographion.config import Settings
from melographion.models import MelographionSession, ObservationSet, ReflectionSession, SongProfile
from melographion.obsidian_exporter import (
    plan_reflection_export,
    render_reflection_note,
    render_session_note,
)


def settings_for(tmp_path: Path) -> Settings:
    return Settings(project_root=tmp_path / "project", vault_path=tmp_path / "vault")


def test_reflection_note_preserves_verbatim_response_before_inference():
    profile = SongProfile(
        track_id="track-1",
        track_name="Test Song",
        artist_names=["Test Artist"],
        playlist_name="Playlist",
    )
    session = ReflectionSession(
        song_id="track-1",
        prompt="Where does it land?",
        user_response="My exact words stay here.\nSecond line remains intact.",
        extracted_symbols=["mirror"],
        emotional_tags=["grief"],
    )
    note = render_reflection_note(session, profile)

    response_index = note.index("My exact words stay here.")
    inferred_index = note.index("## Inferred Observations")

    assert response_index < inferred_index
    assert "These observations are rule-based and provisional until reviewed." in note
    assert "analysis_status: inferred" in note
    assert "type: melographion-session" in note
    assert "origin:" in note
    assert "review:" in note
    assert "confidence:" in note


def test_dry_run_preview_does_not_write_to_vault(tmp_path: Path):
    settings = settings_for(tmp_path)
    settings.vault_path.mkdir(parents=True)
    profile = SongProfile(track_id="track-1", track_name="Song", artist_names=["Artist"])
    session = ReflectionSession(song_id="track-1", prompt="Prompt", user_response="Response")

    preview = plan_reflection_export(settings, session, profile, dry_run=True)

    assert preview.backup_manifest.dry_run is True
    assert preview.writes
    assert not Path(preview.writes[0].target_path).exists()
    assert "Response" in preview.render()
    assert "== Constellation Changes ==" in preview.render()


def test_one_event_session_has_frame_but_no_arc_summary():
    profile = SongProfile(track_id="track-1", track_name="Song", artist_names=["Artist"])
    session = MelographionSession()
    event = session.add_event(song_id="track-1", prompt="Prompt")
    event.capture_response("Response")
    event.set_inferred_observations(
        ObservationSet(extracted_symbols=["mirror"], emotional_tags=["grief"])
    )

    note = render_session_note(session, {"track-1": profile})

    assert "This one-song session has a frame" in note
    assert "does not generate a full arc summary until at least two events exist" in note


def test_two_event_session_allows_arc_summary():
    profiles = {
        "track-1": SongProfile(track_id="track-1", track_name="One", artist_names=["Artist"]),
        "track-2": SongProfile(track_id="track-2", track_name="Two", artist_names=["Artist"]),
    }
    session = MelographionSession(session_summary="The session moved from grief toward motion.")
    first = session.add_event(song_id="track-1", prompt="Prompt 1")
    first.capture_response("Response 1")
    second = session.add_event(song_id="track-2", prompt="Prompt 2")
    second.capture_response("Response 2")

    note = render_session_note(session, profiles)

    assert "The session moved from grief toward motion." in note
    assert note.index("Response 1") < note.index("## Song Event 2")
