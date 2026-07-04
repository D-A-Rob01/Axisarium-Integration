from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ReadingMode = Literal["reflective", "predictive", "ritual", "creative", "decision-support"]
Orientation = Literal["upright", "reversed"]
ReviewStatus = Literal["pending", "reviewed"]
ProjectionRisk = Literal["low", "medium", "high"]


CLAIM_TYPES = [
    "observation",
    "symbolic-association",
    "intuition",
    "interpretation",
    "prediction",
    "action-recommendation",
]


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    arcana: Literal["major", "minor"]
    number: int
    suit: str | None
    element: str | None
    upright_keywords: list[str] = Field(default_factory=list)
    reversed_keywords: list[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("id", "name")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class Deck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    cards: list[Card]

    @field_validator("cards")
    @classmethod
    def cards_must_be_unique(cls, cards: list[Card]) -> list[Card]:
        ids = [card.id for card in cards]
        if len(ids) != len(set(ids)):
            raise ValueError("deck contains duplicate card ids")
        if not cards:
            raise ValueError("deck must contain at least one card")
        return cards


class SpreadPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    label: str
    prompt: str

    @field_validator("label", "prompt")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class Spread(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    positions: list[SpreadPosition]

    @field_validator("positions")
    @classmethod
    def positions_must_be_unique_and_ordered(cls, positions: list[SpreadPosition]) -> list[SpreadPosition]:
        indexes = [position.index for position in positions]
        if len(indexes) != len(set(indexes)):
            raise ValueError("spread contains duplicate position indexes")
        if not positions:
            raise ValueError("spread must contain at least one position")
        if indexes != sorted(indexes):
            raise ValueError("spread positions must be sorted by index")
        return positions


class DrawnCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: int
    position_label: str
    position_prompt: str
    card: Card
    orientation: Orientation

    @property
    def keywords(self) -> list[str]:
        if self.orientation == "reversed":
            return self.card.reversed_keywords
        return self.card.upright_keywords


class Reading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["tarot-reading"] = "tarot-reading"
    date: date
    deck: str
    spread: str
    mode: ReadingMode
    question: str = ""
    context: str = ""
    confidence: int | None = Field(default=None, ge=1, le=5)
    cards: list[DrawnCard]
    tags: list[str] = Field(default_factory=lambda: ["tarot", "aletheion", "symbolic-audit"])
    review_status: ReviewStatus = "pending"
    review_date: str | None = None
    usefulness_score: int | None = Field(default=None, ge=1, le=5)
    projection_risk: ProjectionRisk | None = None
    action_taken: str | None = None
    claim_types: list[str] = Field(default_factory=lambda: CLAIM_TYPES.copy())
