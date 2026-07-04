from __future__ import annotations

from datetime import date
import random

import yaml

from cartomancy_engine.markdown import reading_filename, render_reading_markdown
from cartomancy_engine.reading import draw_cards
from cartomancy_engine.resources import load_deck, load_spread


def make_reading(question: str = "", context: str = "", confidence: int | None = None):
    return draw_cards(
        load_deck("rider-waite-smith"),
        load_spread("three-card"),
        mode="decision-support",
        question=question,
        context=context,
        confidence=confidence,
        reading_date=date(2026, 6, 26),
        rng=random.Random(4),
    )


def test_filename_uses_spread_when_question_empty():
    assert reading_filename(make_reading("")) == "2026-06-26_tarot-reading_three-card.md"


def test_filename_slugs_and_caps_question():
    filename = reading_filename(make_reading("What should I prioritize this week? Also: avoid chaos."))

    assert filename == "2026-06-26_tarot-reading_what-should-i-prioritize-this-week-also-avoid-ch.md"


def test_frontmatter_is_valid_with_punctuation_heavy_question():
    question = "What now: act, wait, or say 'no'?"
    markdown = render_reading_markdown(make_reading(question))
    frontmatter = markdown.split("---", 2)[1]

    parsed = yaml.safe_load(frontmatter)

    assert parsed["question"] == question
    assert parsed["type"] == "tarot-reading"
    assert parsed["cards"]
    assert parsed["review_status"] == "pending"
    assert parsed["review_date"] is None
    assert parsed["usefulness_score"] is None
    assert parsed["projection_risk"] is None
    assert parsed["action_taken"] is None
    assert parsed["claim_types"] == [
        "observation",
        "symbolic-association",
        "intuition",
        "interpretation",
        "prediction",
        "action-recommendation",
    ]


def test_card_table_claim_types_and_audit_sections_render():
    markdown = render_reading_markdown(
        make_reading(
            "What should I prioritize this week?",
            context="career / writing / money",
            confidence=3,
        )
    )

    assert "| Position | Card | Orientation | Keywords |" in markdown
    assert "## Context\n\ncareer / writing / money" in markdown
    assert "## Confidence\n\n3" in markdown
    assert "## Epistemic Claim Types" in markdown
    assert "- Symbolic association:" in markdown
    assert "### Review Metadata" in markdown
    assert "### What Actually Happened?" in markdown
    assert "### Which Parts Were Projection?" in markdown
    assert "### Projection Risk" in markdown
