from __future__ import annotations

from melographion.config import Settings
from melographion.graph_store import update_graph
from melographion.models import MelographionSession, ObservationSet, ReflectionSession, SongProfile


def test_graph_update_dry_run_previews_without_file_write(tmp_path):
    settings = Settings(project_root=tmp_path / "project", vault_path=tmp_path / "vault")
    profile = SongProfile(track_id="track-1", track_name="Song", artist_names=["Artist"])
    session = ReflectionSession(
        song_id="track-1",
        prompt="Prompt",
        user_response="Response",
        extracted_symbols=["mirror"],
        emotional_tags=["tenderness"],
        body_response=["chest"],
    )

    changes = update_graph(settings, profile=profile, session=session, dry_run=True)

    assert changes.nodes_added
    assert changes.edges_added
    assert not settings.graph_path.exists()


def test_graph_update_persists_file(tmp_path):
    settings = Settings(project_root=tmp_path / "project", vault_path=tmp_path / "vault")
    profile = SongProfile(track_id="track-1", track_name="Song", artist_names=["Artist"])

    changes = update_graph(settings, profile=profile, dry_run=False)

    assert changes.nodes_added
    assert settings.graph_path.exists()


def test_graph_update_uses_session_and_event_nodes(tmp_path):
    settings = Settings(project_root=tmp_path / "project", vault_path=tmp_path / "vault")
    session = MelographionSession()
    event = session.add_event(song_id="track-1", prompt="Prompt")
    event.capture_response("Response")
    event.set_inferred_observations(
        ObservationSet(extracted_symbols=["mirror"], emotional_tags=["grief"])
    )

    changes = update_graph(settings, session=session, dry_run=True)
    node_ids = {node["id"] for node in changes.nodes_added}

    assert f"session:{session.session_id}" in node_ids
    assert f"event:{session.session_id}:1" in node_ids
    assert not any(node_id.startswith("reflection:") for node_id in node_ids)
