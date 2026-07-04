from __future__ import annotations

import pytest

typer = pytest.importorskip("typer")
from typer.testing import CliRunner

from melographion.config import Settings
from melographion.cli import app
from melographion.models import SongProfile
from melographion.storage import load_session, save_song_profile


def test_init_dry_run_cli_renders_preview(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "08 Iridescentia" / "Indexes").mkdir(parents=True)
    (vault / "08 Iridescentia" / "Indexes" / "Constellation Index.md").write_text(
        "# Constellation Index\n\n| Constellation | Function | Status |\n|---|---|---|\n\n## Constellation Rules\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MELOGRAPHION_VAULT_PATH", str(vault))
    runner = CliRunner()

    result = runner.invoke(app, ["init", "--dry-run"])

    assert result.exit_code == 0
    assert "== Proposed Vault Write ==" in result.output
    assert "Melographion" in result.output
    assert not (vault / "08 Iridescentia" / "Constellations" / "Melographion.md").exists()


def test_index_rebuild_dry_run_cli_renders_preview(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "08 Iridescentia" / "Indexes").mkdir(parents=True)
    (vault / "08 Iridescentia" / "Indexes" / "Constellation Index.md").write_text(
        "# Constellation Index\n\n| Constellation | Function | Status |\n|---|---|---|\n\n## Constellation Rules\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MELOGRAPHION_VAULT_PATH", str(vault))
    runner = CliRunner()

    result = runner.invoke(app, ["index", "rebuild", "--dry-run"])

    assert result.exit_code == 0
    assert "Resonance Index" in result.output
    assert not (vault / "08 Iridescentia" / "Song Collage" / "Indexes").exists()


def test_session_cli_flow_uses_session_as_atomic_unit(tmp_path, monkeypatch):
    project = tmp_path / "project"
    vault = tmp_path / "vault"
    monkeypatch.setenv("MELOGRAPHION_PROJECT_ROOT", str(project))
    monkeypatch.setenv("MELOGRAPHION_VAULT_PATH", str(vault))
    settings = Settings(project_root=project, vault_path=vault)
    save_song_profile(
        settings,
        SongProfile(track_id="track-1", track_name="One", artist_names=["Artist"]),
    )
    save_song_profile(
        settings,
        SongProfile(track_id="track-2", track_name="Two", artist_names=["Artist"]),
    )
    runner = CliRunner()

    start = runner.invoke(app, ["session", "start", "--song-id", "track-1"])
    assert start.exit_code == 0
    session_id = _value_after(start.output, "Session started: ")
    session = load_session(settings, session_id)
    assert session.events[0].status == "pending_prompt"

    capture = runner.invoke(
        app,
        [
            "session",
            "capture-response",
            "--session-id",
            session_id,
            "--sequence",
            "1",
            "--response",
            "The mirror landed in my chest with grief.",
        ],
    )
    assert capture.exit_code == 0
    assert load_session(settings, session_id).events[0].status == "response_captured"

    infer = runner.invoke(app, ["session", "infer", "--session-id", session_id, "--sequence", "1"])
    assert infer.exit_code == 0
    assert load_session(settings, session_id).events[0].status == "inference_pending"

    review = runner.invoke(
        app,
        [
            "session",
            "review-inference",
            "--session-id",
            session_id,
            "--sequence",
            "1",
            "--review-note",
            "accepted",
        ],
    )
    assert review.exit_code == 0
    assert load_session(settings, session_id).events[0].status == "inference_reviewed"

    next_song = runner.invoke(
        app, ["session", "next-song", "--session-id", session_id, "--sequence", "1"]
    )
    assert next_song.exit_code == 0
    assert load_session(settings, session_id).events[0].status == "next_song_suggested"

    complete = runner.invoke(
        app, ["session", "complete-event", "--session-id", session_id, "--sequence", "1"]
    )
    assert complete.exit_code == 0
    assert load_session(settings, session_id).events[0].status == "complete"

    add = runner.invoke(
        app, ["session", "add-song", "--session-id", session_id, "--song-id", "track-2"]
    )
    assert add.exit_code == 0
    assert len(load_session(settings, session_id).events) == 2

    export = runner.invoke(app, ["session", "export", "--session-id", session_id, "--dry-run"])
    assert export.exit_code == 0
    assert "Melographion Session" in export.output
    assert "## Song Event 1" in export.output
    assert "## Song Event 2" in export.output
    assert not (vault / "08 Iridescentia").exists()


def _value_after(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise AssertionError(f"Could not find {prefix!r} in output:\n{output}")
