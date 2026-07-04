from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .markdown import render_reading_markdown, write_reading_markdown
from .models import ReadingMode
from .reading import draw_cards
from .review import ReviewError, load_reading_frontmatter, summarize_frontmatter, update_reading_frontmatter
from .resources import ResourceLoadError, list_decks as resource_list_decks, list_spreads as resource_list_spreads, load_deck, load_spread


app = typer.Typer(help="Cartomancy Engine reading logger.")


DEFAULT_OUTPUT_DIR = Path("readings")
VALID_MODES = {"reflective", "predictive", "ritual", "creative", "decision-support"}
VALID_REVIEW_STATUSES = {"pending", "reviewed"}
VALID_PROJECTION_RISKS = {"low", "medium", "high"}


def parse_tags(raw_tags: str) -> list[str]:
    defaults = ["tarot", "aletheion", "symbolic-audit"]
    custom = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    if not custom:
        return defaults
    merged = defaults.copy()
    for tag in custom:
        if tag not in merged:
            merged.append(tag)
    return merged


@app.command("list-decks")
def list_decks() -> None:
    """List bundled deck ids."""
    for deck_id in resource_list_decks():
        typer.echo(deck_id)


@app.command("list-spreads")
def list_spreads() -> None:
    """List bundled spread ids."""
    for spread_id in resource_list_spreads():
        typer.echo(spread_id)


@app.command()
def draw(
    deck: Annotated[str, typer.Option("--deck", help="Bundled deck id.")] = "rider-waite-smith",
    spread: Annotated[str, typer.Option("--spread", help="Bundled spread id.")] = "three-card",
    mode: Annotated[str, typer.Option("--mode", help="Reading mode.")] = "decision-support",
    question: Annotated[str, typer.Option("--question", help="Optional reading question.")] = "",
    confidence: Annotated[
        int | None,
        typer.Option("--confidence", min=1, max=5, help="Original confidence from 1-5."),
    ] = None,
    context: Annotated[str, typer.Option("--context", help="Optional decision or life context.")] = "",
    tags: Annotated[str, typer.Option("--tags", help="Comma-separated custom tags.")] = "",
    no_reversals: Annotated[bool, typer.Option("--no-reversals", help="Draw only upright cards.")] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Directory for generated Markdown readings."),
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print Markdown without writing a file.")] = False,
) -> None:
    """Draw a spread and create a Markdown reading note."""
    if mode not in VALID_MODES:
        raise typer.BadParameter(f"Invalid mode '{mode}'. Choose one of: {', '.join(sorted(VALID_MODES))}")

    try:
        loaded_deck = load_deck(deck)
        loaded_spread = load_spread(spread)
        reading = draw_cards(
            loaded_deck,
            loaded_spread,
            mode=mode,  # type: ignore[arg-type]
            question=question,
            context=context,
            confidence=confidence,
            tags=parse_tags(tags),
            allow_reversals=not no_reversals,
        )
    except (ResourceLoadError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    markdown = render_reading_markdown(reading)
    if dry_run:
        typer.echo(markdown)
        return

    target_dir = output or DEFAULT_OUTPUT_DIR
    path = write_reading_markdown(reading, target_dir)
    typer.echo(f"Reading written: {path}")


@app.command()
def review(
    path: Annotated[Path, typer.Argument(help="Path to a generated tarot reading Markdown file.")],
    review_status: Annotated[
        str | None,
        typer.Option("--review-status", help="Set review status: pending or reviewed."),
    ] = None,
    usefulness_score: Annotated[
        int | None,
        typer.Option("--usefulness-score", min=1, max=5, help="Set usefulness score from 1-5."),
    ] = None,
    projection_risk: Annotated[
        str | None,
        typer.Option("--projection-risk", help="Set projection risk: low, medium, or high."),
    ] = None,
    action_taken: Annotated[
        str | None,
        typer.Option("--action-taken", help="Set the action taken summary."),
    ] = None,
) -> None:
    """Summarize and optionally update a tarot reading's audit frontmatter."""
    if review_status is not None and review_status not in VALID_REVIEW_STATUSES:
        raise typer.BadParameter(
            f"Invalid review status '{review_status}'. Choose one of: {', '.join(sorted(VALID_REVIEW_STATUSES))}"
        )
    if projection_risk is not None and projection_risk not in VALID_PROJECTION_RISKS:
        raise typer.BadParameter(
            f"Invalid projection risk '{projection_risk}'. Choose one of: {', '.join(sorted(VALID_PROJECTION_RISKS))}"
        )

    try:
        if any(value is not None for value in [review_status, usefulness_score, projection_risk, action_taken]):
            frontmatter = update_reading_frontmatter(
                path,
                review_status=review_status,  # type: ignore[arg-type]
                usefulness_score=usefulness_score,
                projection_risk=projection_risk,  # type: ignore[arg-type]
                action_taken=action_taken,
            )
        else:
            frontmatter = load_reading_frontmatter(path)
    except ReviewError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(summarize_frontmatter(frontmatter))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
