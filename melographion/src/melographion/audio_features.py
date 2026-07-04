from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path

from .models import AudioFeatureSet


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a"}


class AudioAnalysisError(RuntimeError):
    pass


def analyze_audio_file(path: str | Path, song_id: str | None = None) -> AudioFeatureSet:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise AudioAnalysisError(
            f"Unsupported audio extension {source.suffix!r}. Use WAV, MP3, or M4A."
        )

    try:
        return _analyze_with_librosa(source, song_id=song_id)
    except (ModuleNotFoundError, ImportError):
        if source.suffix.lower() == ".wav":
            return _analyze_wav_fallback(source, song_id=song_id)
        raise AudioAnalysisError(
            "MP3/M4A analysis requires librosa and its audio backend. "
            "Install the project dependencies or provide a WAV file."
        )


def _coarse(values: list[float], bins: int = 12) -> list[float]:
    if not values:
        return []
    if len(values) <= bins:
        return [round(float(value), 6) for value in values]
    step = len(values) / bins
    result = []
    for index in range(bins):
        start = int(index * step)
        end = int((index + 1) * step) or start + 1
        chunk = values[start:end]
        result.append(round(sum(chunk) / max(1, len(chunk)), 6))
    return result


def _analyze_with_librosa(source: Path, song_id: str | None) -> AudioFeatureSet:
    import librosa
    import numpy as np

    y, sr = librosa.load(source, sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    if duration <= 0:
        raise AudioAnalysisError("Audio file has no measurable duration.")

    rms = librosa.feature.rms(y=y)[0]
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)[0]

    tempo_value: float | None = None
    try:
        tempo = librosa.beat.tempo(y=y, sr=sr)
        tempo_value = float(np.asarray(tempo).reshape(-1)[0])
    except Exception:
        tempo_value = None

    section_times: list[float] = []
    if len(onset_env) > 3:
        diffs = np.abs(np.diff(onset_env))
        threshold = float(np.percentile(diffs, 90))
        frames = np.where(diffs >= threshold)[0][:16]
        section_times = [round(float(librosa.frames_to_time(frame, sr=sr)), 3) for frame in frames]

    return AudioFeatureSet(
        source_path=str(source),
        song_id=song_id,
        analyzer="librosa",
        duration_seconds=round(duration, 3),
        estimated_tempo=round(tempo_value, 3) if tempo_value else None,
        rms_energy_mean=round(float(np.mean(rms)), 6),
        rms_energy_std=round(float(np.std(rms)), 6),
        dynamic_contour=_coarse([float(value) for value in rms]),
        loudness_intensity_shape=_coarse([float(value) for value in onset_env]),
        onset_density=round(float(len(onset_frames) / duration), 6),
        silence_ratio=round(float(np.mean(np.abs(y) < 0.01)), 6),
        spectral_centroid_mean=round(float(np.mean(centroid)), 6),
        spectral_centroid_std=round(float(np.std(centroid)), 6),
        spectral_contrast_mean=round(float(np.mean(contrast)), 6),
        zero_crossing_rate_mean=round(float(np.mean(zcr)), 6),
        section_change_estimates=section_times,
        metadata={"sample_rate": sr, "samples": int(len(y))},
    )


def _analyze_wav_fallback(source: Path, song_id: str | None) -> AudioFeatureSet:
    with wave.open(str(source), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frame_count = wav.getnframes()
        frames = wav.readframes(frame_count)

    if sample_width != 2:
        raise AudioAnalysisError(
            "The built-in WAV fallback supports 16-bit PCM WAV files. "
            "Install librosa for broader audio support."
        )
    if frame_count == 0 or sample_rate == 0:
        raise AudioAnalysisError("Audio file has no measurable duration.")

    samples = array("h")
    samples.frombytes(frames)
    if channels > 1:
        mono = []
        for index in range(0, len(samples), channels):
            mono.append(sum(samples[index : index + channels]) / channels)
    else:
        mono = [float(value) for value in samples]

    normalized = [value / 32768.0 for value in mono]
    duration = frame_count / float(sample_rate)
    window_size = max(1, int(sample_rate * 0.05))
    rms_values: list[float] = []
    for index in range(0, len(normalized), window_size):
        chunk = normalized[index : index + window_size]
        if not chunk:
            continue
        rms_values.append(math.sqrt(sum(value * value for value in chunk) / len(chunk)))

    rms_mean = sum(rms_values) / max(1, len(rms_values))
    rms_std = math.sqrt(
        sum((value - rms_mean) ** 2 for value in rms_values) / max(1, len(rms_values))
    )
    silence_ratio = sum(1 for value in normalized if abs(value) < 0.01) / max(1, len(normalized))
    zero_crossings = 0
    for left, right in zip(normalized, normalized[1:]):
        if (left < 0 <= right) or (left >= 0 > right):
            zero_crossings += 1
    zcr = zero_crossings / max(1, len(normalized) - 1)

    return AudioFeatureSet(
        source_path=str(source),
        song_id=song_id,
        analyzer="wav-fallback",
        duration_seconds=round(duration, 3),
        rms_energy_mean=round(rms_mean, 6),
        rms_energy_std=round(rms_std, 6),
        dynamic_contour=_coarse(rms_values),
        loudness_intensity_shape=_coarse(rms_values),
        silence_ratio=round(silence_ratio, 6),
        zero_crossing_rate_mean=round(zcr, 6),
        metadata={
            "sample_rate": sample_rate,
            "channels": channels,
            "sample_width": sample_width,
            "frames": frame_count,
            "fallback_note": "Install librosa for tempo, onset, and spectral features.",
        },
    )
