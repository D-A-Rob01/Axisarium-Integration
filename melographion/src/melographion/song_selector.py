from __future__ import annotations

import random

from .config import Settings
from .models import MelographionSession, ObservationSet, ReflectionSession, SongProfile
from .storage import latest_session, list_song_profiles


SUPPORTED_MODES = {
    "random",
    "manual",
    "resonance",
    "counterpoint",
    "descent",
    "albedo",
    "kinetic",
    "shadow",
}


def suggest_song(settings: Settings, mode: str = "random") -> tuple[SongProfile, str]:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported mode {mode!r}. Choose one of: {', '.join(sorted(SUPPORTED_MODES))}")
    profiles = list_song_profiles(settings)
    if not profiles:
        raise ValueError("No song profiles are loaded yet. Run `melographion playlist load` first.")

    previous = latest_session(settings)
    if mode in {"random", "manual"} or not previous:
        profile = random.choice(profiles)
        return profile, "Random fallback: no prior session context was required for this suggestion."

    ranked = sorted(profiles, key=lambda profile: _score(profile, previous, mode), reverse=True)
    chosen = ranked[0]
    return chosen, f"{mode} heuristic selected this song from loaded profile metadata and current session context."


def _score(profile: SongProfile, previous: MelographionSession | ReflectionSession, mode: str) -> float:
    text = " ".join([profile.track_name, profile.display_artist, " ".join(profile.tags)]).lower()
    prior = _context_terms(previous)
    score = 0.0
    if mode == "resonance":
        score += sum(1.0 for term in prior if term.lower() in text)
    elif mode == "counterpoint":
        score += 1.0 / (1.0 + sum(1 for term in prior if term.lower() in text))
    elif mode == "descent":
        score += _keyword_score(text, ["dark", "deep", "night", "blood", "hunger", "ghost", "shadow"])
        score += len(prior) * 0.05
    elif mode == "albedo":
        score += _keyword_score(text, ["light", "clear", "soft", "home", "morning", "tender", "gold"])
    elif mode == "kinetic":
        score += _keyword_score(text, ["dance", "run", "move", "body", "speed", "electric"])
    elif mode == "shadow":
        score += _keyword_score(text, ["shame", "rage", "alone", "obsession", "rupture", "want"])
    return score + random.random() * 0.01


def _keyword_score(text: str, keywords: list[str]) -> float:
    return float(sum(1 for keyword in keywords if keyword in text))


def _context_terms(session: MelographionSession | ReflectionSession) -> set[str]:
    if isinstance(session, ReflectionSession):
        return set(session.emotional_tags + session.extracted_themes + session.extracted_symbols)
    terms: set[str] = set(session.session_themes + session.session_symbols)
    for event in session.events:
        observations = event.reviewed_observations or event.inferred_observations
        if observations:
            terms.update(_observation_terms(observations))
    return terms


def _observation_terms(observations: ObservationSet) -> set[str]:
    return set(
        observations.emotional_tags
        + observations.extracted_themes
        + observations.extracted_symbols
        + observations.body_response
    )
