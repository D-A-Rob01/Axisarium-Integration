from __future__ import annotations

from melographion.audio_ingest.cobalt_api_client import CobaltApiClient, CobaltApiConfig
from melographion.audio_ingest.cobalt_watch_folder import scan_audio_inbox


def test_cobalt_api_is_disabled_without_endpoint():
    config = CobaltApiConfig()
    assert config.enabled is False


def test_cobalt_api_client_is_placeholder():
    client = CobaltApiClient(CobaltApiConfig(api_url="http://localhost:9000"))
    try:
        client.download("https://example.com/video")
    except NotImplementedError as exc:
        assert "v0.3" in str(exc)
    else:
        raise AssertionError("Expected cobalt API placeholder to raise.")


def test_watch_folder_scan_is_read_only(tmp_path):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not a real wav")
    ignored = tmp_path / "note.txt"
    ignored.write_text("ignore", encoding="utf-8")

    assert scan_audio_inbox(tmp_path) == [audio]
