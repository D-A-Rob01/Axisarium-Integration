from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(value: str, fallback: str = "untitled") -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("-", value).strip().strip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned[:150].strip()
    return cleaned or fallback


def date_prefix(iso_datetime: str) -> str:
    return iso_datetime[:10] if iso_datetime else "undated"


def assert_safe_vault_path(vault_path: Path, target: Path) -> None:
    vault = vault_path.resolve()
    resolved = target.resolve()
    if not str(resolved).lower().startswith(str(vault).lower()):
        raise ValueError(f"Target is outside the vault: {target}")
    parts = {part.lower() for part in resolved.parts}
    if ".obsidian" in parts or ".tmp.driveupload" in parts or ".tmp.drivedownload" in parts:
        raise ValueError(f"Refusing to write internal vault or sync path: {target}")


@dataclass(frozen=True)
class AxisariumPaths:
    vault_path: Path

    @property
    def iridescentia_root(self) -> Path:
        return self.vault_path / "08 Iridescentia"

    @property
    def song_collage_root(self) -> Path:
        return self.iridescentia_root / "Song Collage"

    @property
    def reflection_dir(self) -> Path:
        return self.song_collage_root / "Sessions"

    @property
    def song_profile_dir(self) -> Path:
        return self.song_collage_root / "Song Profiles"

    @property
    def song_index_dir(self) -> Path:
        return self.song_collage_root / "Indexes"

    @property
    def system_note(self) -> Path:
        return self.iridescentia_root / "Constellations" / "Melographion.md"

    @property
    def project_note(self) -> Path:
        return (
            self.vault_path
            / "06 Artificial Intelligence"
            / "Projects.py"
            / "In-Progress"
            / "Melographion.md"
        )

    @property
    def constellation_index(self) -> Path:
        return self.iridescentia_root / "Indexes" / "Constellation Index.md"

    @property
    def resonance_index(self) -> Path:
        return self.song_index_dir / "Resonance Index.md"

    @property
    def song_collage_index(self) -> Path:
        return self.resonance_index

    def reflection_note_path(self, date: str, song: str, artist: str) -> Path:
        name = sanitize_filename(f"{date} - {song} - {artist}") + ".md"
        return self.reflection_dir / name

    def song_profile_note_path(self, song: str, artist: str) -> Path:
        name = sanitize_filename(f"{song} - {artist}") + ".md"
        return self.song_profile_dir / name
