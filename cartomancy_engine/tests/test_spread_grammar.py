from datetime import date
import random

import pytest

from cartomancy_engine.markdown import render_reading_markdown
from cartomancy_engine.models import Reading
from cartomancy_engine.reading import draw_cards
from cartomancy_engine.resources import list_spreads, load_deck, load_spread


@pytest.mark.parametrize('spread_id', [
    'the-constellation', 'the-fork', 'the-aperture', 'the-crucible',
    'the-interface', 'the-vector',
])
@pytest.mark.parametrize('reversals', [False, True])
def test_seven_position_contracts_draw_and_export_without_losing_metadata(spread_id, reversals):
    assert spread_id in list_spreads()
    spread = load_spread(spread_id)
    assert [position.index for position in spread.positions] == list(range(1, 8))
    reading = draw_cards(load_deck('rider-waite-smith'), spread,
                         mode='decision-support', question='What could I test?',
                         reading_date=date(2026, 9, 19), allow_reversals=reversals,
                         rng=random.Random(34))
    assert len({drawn.card.id for drawn in reading.cards}) == 7
    assert [drawn.position_label for drawn in reading.cards] == [p.label for p in spread.positions]
    assert [drawn.position_prompt for drawn in reading.cards] == [p.prompt for p in spread.positions]
    if not reversals:
        assert all(drawn.orientation == 'upright' for drawn in reading.cards)
    assert Reading.model_validate_json(reading.model_dump_json()) == reading
    markdown = render_reading_markdown(reading)
    assert f'spread: {spread_id}' in markdown
    assert all(position.label in markdown for position in spread.positions)
    assert 'action-recommendation' in markdown
    assert 'review_status: pending' in markdown
