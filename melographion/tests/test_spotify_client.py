from melographion.spotify_client import track_to_profile


def test_track_to_profile_maps_spotify_shape():
    profile = track_to_profile(
        {
            "id": "abc123",
            "name": "Blue Signal",
            "artists": [{"name": "Artist One"}, {"name": "Artist Two"}],
            "album": {"name": "Album Name"},
            "duration_ms": 123000,
            "external_urls": {"spotify": "https://open.spotify.com/track/abc123"},
        },
        playlist_name="Iridescentia Animae",
        date_added="2026-06-24T12:00:00Z",
    )

    assert profile.track_id == "abc123"
    assert profile.track_name == "Blue Signal"
    assert profile.artist_names == ["Artist One", "Artist Two"]
    assert profile.playlist_name == "Iridescentia Animae"
    assert profile.spotify_url.endswith("abc123")
