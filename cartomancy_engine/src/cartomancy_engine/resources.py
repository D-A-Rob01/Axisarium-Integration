from __future__ import annotations

import json
from importlib import resources
from typing import Any

from pydantic import ValidationError

from .models import Deck, Spread


DECK_PACKAGE = "cartomancy_engine.data.decks"
SPREAD_PACKAGE = "cartomancy_engine.data.spreads"


class ResourceLoadError(ValueError):
    """Raised when bundled cartomancy data cannot be loaded or validated."""


def _json_resource_names(package: str) -> list[str]:
    return sorted(path.name.removesuffix(".json") for path in resources.files(package).iterdir() if path.name.endswith(".json"))


def list_decks() -> list[str]:
    return _json_resource_names(DECK_PACKAGE)


def list_spreads() -> list[str]:
    return _json_resource_names(SPREAD_PACKAGE)


def _load_json(package: str, resource_id: str) -> dict[str, Any]:
    resource_name = f"{resource_id}.json"
    try:
        payload = resources.files(package).joinpath(resource_name).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        available = ", ".join(_json_resource_names(package)) or "(none)"
        raise ResourceLoadError(f"Unknown resource '{resource_id}'. Available: {available}") from exc
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ResourceLoadError(f"Invalid JSON in {resource_name}: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ResourceLoadError(f"{resource_name} must contain a JSON object")
    return parsed


def load_deck(deck_id: str) -> Deck:
    payload = _load_json(DECK_PACKAGE, deck_id)
    try:
        deck = Deck.model_validate(payload)
    except ValidationError as exc:
        raise ResourceLoadError(f"Invalid deck '{deck_id}': {exc}") from exc
    if deck.id != deck_id:
        raise ResourceLoadError(f"Deck id mismatch: requested '{deck_id}', file contains '{deck.id}'")
    return deck


def load_spread(spread_id: str) -> Spread:
    payload = _load_json(SPREAD_PACKAGE, spread_id)
    try:
        spread = Spread.model_validate(payload)
    except ValidationError as exc:
        raise ResourceLoadError(f"Invalid spread '{spread_id}': {exc}") from exc
    if spread.id != spread_id:
        raise ResourceLoadError(f"Spread id mismatch: requested '{spread_id}', file contains '{spread.id}'")
    return spread
