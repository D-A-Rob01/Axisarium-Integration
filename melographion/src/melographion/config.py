from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VAULT_PATH = Path(r"C:\Users\david\Documents\Axisarium Vault")


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(path)
        return
    except Exception:
        pass
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    vault_path: Path = DEFAULT_VAULT_PATH
    spotify_client_id: str | None = None
    spotify_client_secret: str | None = None
    spotify_redirect_uri: str = "http://127.0.0.1:8888/callback"
    cobalt_api_url: str | None = None

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def playlist_cache_dir(self) -> Path:
        return self.data_dir / "cache" / "playlists"

    @property
    def song_profiles_dir(self) -> Path:
        return self.data_dir / "song_profiles"

    @property
    def reflections_dir(self) -> Path:
        return self.data_dir / "reflections"

    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    @property
    def audio_features_dir(self) -> Path:
        return self.data_dir / "audio_features"

    @property
    def graphs_dir(self) -> Path:
        return self.data_dir / "graphs"

    @property
    def graph_path(self) -> Path:
        return self.graphs_dir / "melographion_graph.json"

    @property
    def audio_inbox_dir(self) -> Path:
        return self.project_root / "inbox" / "audio"

    @property
    def backup_root(self) -> Path:
        return self.project_root.parent / "scratch" / "backups" / "melographion"

    @property
    def spotify_cache_path(self) -> Path:
        return self.data_dir / "cache" / ".spotify_token"

    def required_dirs(self) -> list[Path]:
        return [
            self.playlist_cache_dir,
            self.song_profiles_dir,
            self.reflections_dir,
            self.sessions_dir,
            self.audio_features_dir,
            self.graphs_dir,
            self.audio_inbox_dir,
        ]


def load_settings(project_root: Path | None = None) -> Settings:
    root = project_root or Path(os.environ.get("MELOGRAPHION_PROJECT_ROOT", str(PROJECT_ROOT)))
    _load_dotenv(root / ".env")
    return Settings(
        project_root=root,
        vault_path=Path(os.environ.get("MELOGRAPHION_VAULT_PATH", str(DEFAULT_VAULT_PATH))),
        spotify_client_id=os.environ.get("SPOTIPY_CLIENT_ID") or None,
        spotify_client_secret=os.environ.get("SPOTIPY_CLIENT_SECRET") or None,
        spotify_redirect_uri=os.environ.get(
            "SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
        ),
        cobalt_api_url=os.environ.get("COBALT_API_URL") or None,
    )


def ensure_local_dirs(settings: Settings, dry_run: bool = False) -> list[Path]:
    dirs = settings.required_dirs()
    if not dry_run:
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
    return dirs
