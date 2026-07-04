from __future__ import annotations

from pathlib import Path

from ..audio_features import SUPPORTED_AUDIO_EXTENSIONS


def scan_audio_inbox(inbox_dir: str | Path) -> list[Path]:
    """Return candidate audio files for v0.2 association prompts."""
    root = Path(inbox_dir)
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


def associate_watch_folder_file(*args, **kwargs):
    raise NotImplementedError(
        "Watched-folder association is reserved for Melographion v0.2. "
        "Use `melographion audio import <path> --song-id <id>` in v0.1."
    )
