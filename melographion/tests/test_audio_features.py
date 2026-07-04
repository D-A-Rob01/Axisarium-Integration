from __future__ import annotations

import math
import wave
from pathlib import Path

from melographion.audio_features import analyze_audio_file


def write_test_wav(path: Path) -> None:
    sample_rate = 8000
    duration = 0.25
    frames = []
    for index in range(int(sample_rate * duration)):
        sample = int(16000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        frames.append(sample.to_bytes(2, byteorder="little", signed=True))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(frames))


def test_wav_audio_analysis_returns_feature_shape(tmp_path: Path):
    path = tmp_path / "tone.wav"
    write_test_wav(path)

    features = analyze_audio_file(path, song_id="track-1")

    assert features.song_id == "track-1"
    assert features.duration_seconds and features.duration_seconds > 0
    assert features.rms_energy_mean and features.rms_energy_mean > 0
    assert features.dynamic_contour
