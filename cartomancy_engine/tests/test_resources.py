from __future__ import annotations

import pytest
from pydantic import ValidationError

from cartomancy_engine.models import Deck, Spread
from cartomancy_engine.resources import list_decks, list_spreads, load_deck, load_spread


def test_bundled_deck_loads_major_arcana():
    deck = load_deck("rider-waite-smith")

    assert deck.id == "rider-waite-smith"
    assert len(deck.cards) == 22
    assert {card.arcana for card in deck.cards} == {"major"}


def test_bundled_spreads_load():
    spreads = list_spreads()

    assert "three-card" in spreads
    assert "situation-obstacle-counsel" in spreads
    assert "body-mind-action" in spreads
    assert "avoidance-reality-next-move" in spreads
    assert load_spread("three-card").positions[0].label == "Current Pattern"


def test_list_decks_shows_bundled_deck():
    assert list_decks() == ["rider-waite-smith"]


def test_invalid_deck_duplicate_cards_fails_clearly():
    card = {
        "id": "major_00_fool",
        "name": "The Fool",
        "arcana": "major",
        "number": 0,
        "suit": None,
        "element": "air",
        "upright_keywords": [],
        "reversed_keywords": [],
        "notes": "",
    }

    with pytest.raises(ValidationError, match="duplicate card ids"):
        Deck.model_validate({"id": "bad", "name": "Bad Deck", "cards": [card, card]})


def test_invalid_spread_duplicate_positions_fails_clearly():
    position = {"index": 1, "label": "One", "prompt": "First?"}

    with pytest.raises(ValidationError, match="duplicate position indexes"):
        Spread.model_validate({"id": "bad", "name": "Bad Spread", "positions": [position, position]})
