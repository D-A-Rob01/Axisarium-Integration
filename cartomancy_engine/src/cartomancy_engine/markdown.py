from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import Reading


MAX_SLUG_LENGTH = 48


def slugify(value: str, *, fallback: str, max_length: int = MAX_SLUG_LENGTH) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if not text:
        text = fallback
    if len(text) > max_length:
        text = text[:max_length].rstrip("-")
    return text or fallback


def reading_filename(reading: Reading) -> str:
    source = reading.question or reading.spread
    slug = slugify(source, fallback=reading.spread)
    return f"{reading.date.isoformat()}_tarot-reading_{slug}.md"


def frontmatter(reading: Reading) -> str:
    payload = {
        "type": reading.type,
        "date": reading.date.isoformat(),
        "deck": reading.deck,
        "spread": reading.spread,
        "mode": reading.mode,
        "question": reading.question,
        "context": reading.context,
        "confidence": reading.confidence,
        "cards": [
            {
                "position": card.position,
                "card": card.card.name,
                "orientation": card.orientation,
            }
            for card in reading.cards
        ],
        "tags": reading.tags,
        "review_status": reading.review_status,
        "review_date": reading.review_date,
        "usefulness_score": reading.usefulness_score,
        "projection_risk": reading.projection_risk,
        "action_taken": reading.action_taken,
        "claim_types": reading.claim_types,
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False).strip()


def render_reading_markdown(reading: Reading) -> str:
    lines = [
        "---",
        frontmatter(reading),
        "---",
        "",
        f"# Tarot Reading - {reading.date.isoformat()}",
        "",
        "## Question",
        "",
        reading.question,
        "",
        "## Context",
        "",
        reading.context,
        "",
        "## Confidence",
        "",
        str(reading.confidence) if reading.confidence is not None else "",
        "",
        "## Spread",
        "",
        f"{reading.spread}",
        "",
        "## Cards Drawn",
        "",
        "| Position | Card | Orientation | Keywords |",
        "| --- | --- | --- | --- |",
    ]

    for drawn in reading.cards:
        keywords = ", ".join(drawn.keywords)
        lines.append(
            f"| {drawn.position}. {drawn.position_label} | {drawn.card.name} | {drawn.orientation} | {keywords} |"
        )

    lines.extend(
        [
            "",
            "## Epistemic Claim Types",
            "",
            "Use these labels while interpreting:",
            "",
            "- Observation:",
            "- Symbolic association:",
            "- Intuition:",
            "- Interpretation:",
            "- Prediction:",
            "- Action recommendation:",
            "",
            "## Initial Reading",
            "",
            "## Practical Counsel",
            "",
            "## Action Chosen",
            "",
            "## Follow-Up",
            "",
            "## Outcome / Audit",
            "",
            "### Review Metadata",
            "",
            "- Review date:",
            "- Time elapsed:",
            f"- Reading mode: {reading.mode}",
            "- Original confidence:",
            "",
            "### What Actually Happened?",
            "",
            "### What Action Did I Take?",
            "",
            "### What Did I Avoid?",
            "",
            "### Which Parts Were Useful?",
            "",
            "### Which Parts Were Projection?",
            "",
            "### Did This Clarify Action?",
            "",
            "- Yes / No / Mixed",
            "",
            "### Usefulness Score",
            "",
            "- Score: /5",
            "",
            "### Projection Risk",
            "",
            "- Low / Medium / High",
            "",
            "### Notes for Future Readings",
            "",
        ]
    )
    return "\n".join(lines)


def write_reading_markdown(reading: Reading, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / reading_filename(reading)
    path.write_text(render_reading_markdown(reading), encoding="utf-8")
    return path
