from __future__ import annotations

from datetime import date
import random

from cartomancy_engine.reading import draw_cards
from cartomancy_engine.resources import load_deck, load_spread


def test_draw_count_matches_spread_positions():
    reading = draw_cards(
        load_deck("rider-waite-smith"),
        load_spread("three-card"),
        mode="decision-support",
        rng=random.Random(42),
    )

    assert len(reading.cards) == 3


def test_draw_has_no_duplicate_cards():
    reading = draw_cards(
        load_deck("rider-waite-smith"),
        load_spread("three-card"),
        mode="decision-support",
        rng=random.Random(42),
    )

    ids = [drawn.card.id for drawn in reading.cards]
    assert len(ids) == len(set(ids))


def test_orientations_are_valid_when_reversals_allowed():
    reading = draw_cards(
        load_deck("rider-waite-smith"),
        load_spread("three-card"),
        mode="decision-support",
        allow_reversals=True,
        rng=random.Random(7),
    )

    assert {drawn.orientation for drawn in reading.cards} <= {"upright", "reversed"}


def test_no_reversals_produces_only_upright_cards():
    reading = draw_cards(
        load_deck("rider-waite-smith"),
        load_spread("three-card"),
        mode="decision-support",
        allow_reversals=False,
        rng=random.Random(7),
    )

    assert {drawn.orientation for drawn in reading.cards} == {"upright"}


def test_reading_date_can_be_fixed_for_tests():
    reading = draw_cards(
        load_deck("rider-waite-smith"),
        load_spread("three-card"),
        mode="decision-support",
        reading_date=date(2026, 6, 26),
        rng=random.Random(1),
    )

    assert reading.date.isoformat() == "2026-06-26"
