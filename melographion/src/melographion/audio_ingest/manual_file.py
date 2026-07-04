from __future__ import annotations

import shutil
from pathlib import Path

from ..audio_features import SUPPORTED_AUDIO_EXTENSIONS, analyze_audio_file
from ..config import Settings
from ..models import AudioFeatureSet
from ..storage import save_audio_features
from ..vault_paths import sanitize_filename


def import_audio_file(
    source_path: str | Path,
    *,
    song_id: str,
    settings: Settings,
    copy_to_inbox: bool = True,
) -> tuple[Path, AudioFeatureSet, Path]:
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError("Manual audio import supports WAV, MP3, and M4A files.")

    imported_path = source
    if copy_to_inbox:
        settings.audio_inbox_dir.mkdir(parents=True, exist_ok=True)
        target_name = sanitize_filename(f"{song_id} - {source.stem}") + source.suffix.lower()
        imported_path = settings.audio_inbox_dir / target_name
        if source.resolve() != imported_path.resolve():
            shutil.copy2(source, imported_path)

    features = analyze_audio_file(imported_path, song_id=song_id)
    features.imported_path = str(imported_path)
    feature_path = save_audio_features(settings, features)
    return imported_path, features, feature_path
