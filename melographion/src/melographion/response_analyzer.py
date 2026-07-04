from __future__ import annotations

import re


EMOTION_KEYWORDS = {
    "yearning": ["want", "longing", "yearn", "miss", "hunger"],
    "defiance": ["refuse", "defy", "fight", "won't", "will not"],
    "grief": ["grief", "loss", "mourning", "dead", "death", "gone"],
    "shame": ["shame", "ashamed", "embarrassed", "humiliated"],
    "tenderness": ["tender", "soft", "gentle", "care", "kind"],
    "eroticism": ["desire", "seduce", "erotic", "body", "touch"],
    "nostalgia": ["nostalgia", "childhood", "remember", "back then", "used to"],
    "alienation": ["alone", "alien", "outside", "unseen", "exile"],
    "transcendence": ["transcend", "holy", "radiant", "beyond", "sky"],
    "rage": ["rage", "furious", "anger", "angry", "wrath"],
    "collapse": ["collapse", "fall apart", "break down", "dissolve"],
    "catharsis": ["release", "cry", "clean", "relief", "purge"],
    "play": ["play", "laugh", "dance", "spark", "tease"],
    "irony": ["ironic", "joke", "absurd", "too funny"],
    "surrender": ["surrender", "let go", "yield", "give in"],
    "spectacle": ["stage", "glamour", "display", "performance", "spotlight"],
}

BODY_WORDS = [
    "throat",
    "chest",
    "heart",
    "stomach",
    "gut",
    "hands",
    "legs",
    "skin",
    "shoulders",
    "jaw",
    "back",
    "spine",
    "hips",
    "lungs",
]

THEME_KEYWORDS = {
    "containment": ["box", "cage", "room", "container", "held", "trapped"],
    "escape": ["escape", "leave", "run", "door", "window", "open"],
    "self-other tension": ["you", "me", "us", "them", "we"],
    "rebirth": ["rebirth", "again", "return", "new", "rise"],
    "motion": ["move", "dance", "run", "walk", "drive", "fall"],
    "stasis": ["still", "stuck", "frozen", "waiting"],
    "witness": ["see", "seen", "witness", "watch"],
}


def analyze_response(response: str) -> dict[str, object]:
    text = response.strip()
    lowered = text.lower()
    emotional_tags = [
        label for label, terms in EMOTION_KEYWORDS.items() if any(term in lowered for term in terms)
    ]
    body_response = [word for word in BODY_WORDS if re.search(rf"\b{re.escape(word)}\b", lowered)]
    themes = [
        label for label, terms in THEME_KEYWORDS.items() if any(term in lowered for term in terms)
    ]
    symbols = _extract_symbols(text)
    memories = _extract_memory_sentences(text)
    return {
        "extracted_themes": themes,
        "extracted_symbols": symbols,
        "body_response": body_response,
        "memories": memories,
        "emotional_valence": _valence(lowered, emotional_tags),
        "emotional_tags": emotional_tags,
        "intensity_score": _intensity_score(text, emotional_tags),
    }


def _extract_symbols(text: str) -> list[str]:
    candidates: list[str] = []
    image_match = re.search(r"\bimage(?: appeared| is| was)?\s*[:\-]?\s*([^.!?\n]+)", text, re.I)
    if image_match:
        candidates.append(image_match.group(1).strip()[:80])
    candidates.extend(item.strip() for item in re.findall(r'"([^"]{2,80})"', text))
    symbolic_words = [
        "mirror",
        "door",
        "house",
        "ocean",
        "fire",
        "ash",
        "stage",
        "mask",
        "window",
        "garden",
        "knife",
        "river",
        "room",
        "light",
    ]
    lowered = text.lower()
    candidates.extend(word for word in symbolic_words if re.search(rf"\b{word}\b", lowered))
    return _unique(candidates)


def _extract_memory_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    memory_terms = ["remember", "memory", "childhood", "when i was", "my mother", "my father"]
    return [
        sentence.strip()
        for sentence in sentences
        if any(term in sentence.lower() for term in memory_terms)
    ][:5]


def _valence(lowered: str, tags: list[str]) -> str:
    if any(tag in tags for tag in ["grief", "shame", "rage", "collapse", "alienation"]):
        if any(tag in tags for tag in ["tenderness", "play", "catharsis", "transcendence"]):
            return "mixed"
        return "heavy"
    if any(tag in tags for tag in ["tenderness", "play", "catharsis", "transcendence"]):
        return "opening"
    if any(word in lowered for word in ["not sure", "unclear", "confusing"]):
        return "unclear"
    return "mixed" if tags else "unclear"


def _intensity_score(text: str, tags: list[str]) -> float:
    punctuation = min(3, text.count("!") + text.count("?"))
    length_pressure = min(4, len(text) / 400)
    tag_pressure = min(3, len(tags) * 0.6)
    return round(min(10.0, punctuation + length_pressure + tag_pressure), 2)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result[:12]
