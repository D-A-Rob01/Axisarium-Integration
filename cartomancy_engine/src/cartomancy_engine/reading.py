from __future__ import annotations

from datetime import date
import random

from .models import Deck, DrawnCard, Orientation, Reading, ReadingMode, Spread


def draw_cards(
    deck: Deck,
    spread: Spread,
    *,
    mode: ReadingMode,
    question: str = "",
    context: str = "",
    confidence: int | None = None,
    tags: list[str] | None = None,
    allow_reversals: bool = True,
    reading_date: date | None = None,
    rng: random.Random | None = None,
) -> Reading:
    if len(spread.positions) > len(deck.cards):
        raise ValueError("spread requires more cards than the deck contains")

    random_source = rng or random.SystemRandom()
    selected_cards = random_source.sample(deck.cards, len(spread.positions))
    drawn: list[DrawnCard] = []

    for position, card in zip(spread.positions, selected_cards, strict=True):
        orientation: Orientation = "upright"
        if allow_reversals:
            orientation = random_source.choice(["upright", "reversed"])
        drawn.append(
            DrawnCard(
                position=position.index,
                position_label=position.label,
                position_prompt=position.prompt,
                card=card,
                orientation=orientation,
            )
        )

    return Reading(
        date=reading_date or date.today(),
        deck=deck.id,
        spread=spread.id,
        mode=mode,
        question=question,
        context=context,
        confidence=confidence,
        cards=drawn,
        tags=tags or ["tarot", "aletheion", "symbolic-audit"],
    )
