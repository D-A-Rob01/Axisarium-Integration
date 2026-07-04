from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import ProjectionRisk, ReviewStatus


class ReviewError(ValueError):
    """Raised when a reading file cannot be reviewed or updated."""


def split_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown.startswith("---\n"):
        raise ReviewError("File does not start with YAML frontmatter")
    try:
        _, frontmatter_text, body = markdown.split("---", 2)
    except ValueError as exc:
        raise ReviewError("File does not contain a complete YAML frontmatter block") from exc
    try:
        parsed = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise ReviewError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ReviewError("YAML frontmatter must be a mapping")
    if parsed.get("type") != "tarot-reading":
        raise ReviewError("File is not a tarot-reading")
    return parsed, body


def load_reading_frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ReviewError(f"Reading file not found: {path}")
    frontmatter, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    return frontmatter


def summarize_frontmatter(frontmatter: dict[str, Any]) -> str:
    cards = frontmatter.get("cards") or []
    lines = [
        f"date: {frontmatter.get('date') or ''}",
        f"question: {frontmatter.get('question') or ''}",
        f"spread: {frontmatter.get('spread') or ''}",
        "cards:",
    ]
    for card in cards:
        if isinstance(card, dict):
            lines.append(
                f"- {card.get('position')}: {card.get('card')} ({card.get('orientation')})"
            )
    lines.extend(
        [
            f"review_status: {frontmatter.get('review_status') or ''}",
            f"usefulness_score: {frontmatter.get('usefulness_score') or ''}",
            f"projection_risk: {frontmatter.get('projection_risk') or ''}",
        ]
    )
    return "\n".join(lines)


def update_reading_frontmatter(
    path: Path,
    *,
    review_status: ReviewStatus | None = None,
    usefulness_score: int | None = None,
    projection_risk: ProjectionRisk | None = None,
    action_taken: str | None = None,
) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(original)

    if review_status is not None:
        frontmatter["review_status"] = review_status
    if usefulness_score is not None:
        if not 1 <= usefulness_score <= 5:
            raise ReviewError("usefulness_score must be between 1 and 5")
        frontmatter["usefulness_score"] = usefulness_score
    if projection_risk is not None:
        frontmatter["projection_risk"] = projection_risk
    if action_taken is not None:
        frontmatter["action_taken"] = action_taken

    updated = yaml.safe_dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()
    path.write_text(f"---\n{updated}\n---{body}", encoding="utf-8")
    return frontmatter
