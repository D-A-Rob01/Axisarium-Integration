from __future__ import annotations

import random

from .models import SongProfile


PROMPTS = [
    "What image appeared first while this song was playing?",
    "Where did this song land in your body?",
    "What lyric, sound, or gesture feels like it knows too much?",
    "What does this song accuse you of, if anything?",
    "What part of you wants to move to this even if the song is carrying pain?",
    "What literary, mythic, or cinematic object does this song resemble?",
    "What would this song be trying to teach if it were not trying to seduce you?",
    "What does this song preserve, repeat, or refuse to release?",
]


def generate_prompt(profile: SongProfile, mode: str = "manual") -> str:
    base = random.choice(PROMPTS)
    return f"{profile.track_name} by {profile.display_artist}: {base}"
