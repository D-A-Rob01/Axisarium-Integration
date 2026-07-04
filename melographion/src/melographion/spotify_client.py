from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Settings
from .models import SongProfile
from .storage import save_song_profile, write_json
from .vault_paths import sanitize_filename


SPOTIFY_SCOPE = "playlist-read-private playlist-read-collaborative"


class SpotifyConfigurationError(RuntimeError):
    pass


def get_spotify_client(settings: Settings):
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise SpotifyConfigurationError(
            "Spotify credentials are missing. Add SPOTIPY_CLIENT_ID and "
            "SPOTIPY_CLIENT_SECRET to melographion/.env."
        )
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ModuleNotFoundError as exc:
        raise SpotifyConfigurationError(
            "spotipy is not installed. Install Melographion dependencies first."
        ) from exc

    auth = SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope=SPOTIFY_SCOPE,
        cache_path=str(settings.spotify_cache_path),
    )
    return spotipy.Spotify(auth_manager=auth)


def authenticate(settings: Settings) -> str:
    client = get_spotify_client(settings)
    user = client.current_user()
    return user.get("display_name") or user.get("id") or "Spotify user"


def list_playlists(settings: Settings) -> list[dict[str, Any]]:
    client = get_spotify_client(settings)
    playlists: list[dict[str, Any]] = []
    page = client.current_user_playlists(limit=50)
    while page:
        for item in page.get("items", []):
            playlists.append(
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "tracks_total": item.get("tracks", {}).get("total"),
                    "owner": item.get("owner", {}).get("display_name"),
                }
            )
        page = client.next(page) if page.get("next") else None
    return playlists


def load_playlist(settings: Settings, playlist_name: str) -> tuple[Path, list[SongProfile]]:
    client = get_spotify_client(settings)
    playlist = _find_playlist(client, playlist_name)
    if not playlist:
        raise ValueError(f"No Spotify playlist named {playlist_name!r} was found.")

    items: list[dict[str, Any]] = []
    page = client.playlist_items(playlist["id"], limit=100)
    while page:
        items.extend(page.get("items", []))
        page = client.next(page) if page.get("next") else None

    profiles: list[SongProfile] = []
    for item in items:
        track = item.get("track") or {}
        if not track or track.get("is_local"):
            continue
        profile = track_to_profile(track, playlist_name=playlist["name"], date_added=item.get("added_at"))
        profiles.append(profile)
        save_song_profile(settings, profile)

    cache_path = settings.playlist_cache_dir / f"{sanitize_filename(playlist['name'])}.json"
    write_json(
        cache_path,
        {
            "playlist": {
                "id": playlist["id"],
                "name": playlist["name"],
                "tracks_total": playlist.get("tracks", {}).get("total"),
            },
            "tracks": [profile.model_dump(mode="json") for profile in profiles],
        },
    )
    return cache_path, profiles


def track_to_profile(track: dict[str, Any], playlist_name: str = "", date_added: str | None = None) -> SongProfile:
    return SongProfile(
        track_id=track.get("id") or track.get("uri") or sanitize_filename(track.get("name", "unknown")),
        track_name=track.get("name") or "Unknown Track",
        artist_names=[artist.get("name", "Unknown Artist") for artist in track.get("artists", [])],
        album=(track.get("album") or {}).get("name") or "",
        duration_ms=track.get("duration_ms"),
        spotify_url=(track.get("external_urls") or {}).get("spotify") or "",
        playlist_name=playlist_name,
        date_added=date_added,
        metadata_source="spotify",
    )


def _find_playlist(client, playlist_name: str) -> dict[str, Any] | None:
    page = client.current_user_playlists(limit=50)
    while page:
        for item in page.get("items", []):
            if item.get("name", "").casefold() == playlist_name.casefold():
                return item
        page = client.next(page) if page.get("next") else None
    return None
