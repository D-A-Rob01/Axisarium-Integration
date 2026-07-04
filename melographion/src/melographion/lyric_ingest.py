from __future__ import annotations

import re
from pathlib import Path


def ingest_lyrics_text(file_path: str | Path | None = None, url_reference: str | None = None) -> dict:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")
        return {"source_type": "user_file", "reference": str(path), "features": analyze_lyrics(text)}
    if url_reference:
        return {"source_type": "url_reference", "reference": url_reference, "features": {}}
    return {"source_type": "none", "reference": None, "features": {}}


def analyze_lyrics(text: str) -> dict:
    lowered = text.lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    repeated = []
    seen = set()
    for line in lines:
        key = line.lower()
        if key in seen and line not in repeated:
            repeated.append(line)
        seen.add(key)
    pronouns = {
        pronoun: len(re.findall(rf"\b{pronoun}\b", lowered))
        for pronoun in ["i", "you", "we", "they", "he", "she"]
    }
    emotional_verbs = [
        word
        for word in ["want", "need", "fear", "love", "hate", "break", "stay", "leave"]
        if re.search(rf"\b{word}\b", lowered)
    ]
    images = [
        word
        for word in ["fire", "water", "house", "room", "road", "night", "light", "body"]
        if re.search(rf"\b{word}\b", lowered)
    ]
    return {
        "repeated_phrases": repeated[:10],
        "pronouns": pronouns,
        "emotional_verbs": emotional_verbs,
        "images_metaphors": images,
        "line_count": len(lines),
        "analysis_status": "inferred",
    }
