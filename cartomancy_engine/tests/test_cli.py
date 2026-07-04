from __future__ import annotations

import pytest

typer = pytest.importorskip("typer")
from typer.testing import CliRunner

from cartomancy_engine.cli import app


def test_acceptance_draw_writes_one_markdown_note(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "draw",
            "--deck",
            "rider-waite-smith",
            "--spread",
            "three-card",
            "--mode",
            "decision-support",
            "--question",
            "What should I prioritize this week?",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    notes = list(tmp_path.glob("*.md"))
    assert len(notes) == 1
    content = notes[0].read_text(encoding="utf-8")
    assert "question: What should I prioritize this week?" in content
    assert "| Position | Card | Orientation | Keywords |" in content
    assert "review_status: pending" in content


def test_dry_run_prints_markdown_and_writes_nothing(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "draw",
            "--deck",
            "rider-waite-smith",
            "--spread",
            "three-card",
            "--mode",
            "decision-support",
            "--question",
            "What should I prioritize this week?",
            "--output",
            str(tmp_path),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "# Tarot Reading -" in result.output
    assert "| Position | Card | Orientation | Keywords |" in result.output
    assert list(tmp_path.glob("*.md")) == []


def test_no_reversals_cli_writes_only_upright_cards(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "draw",
            "--deck",
            "rider-waite-smith",
            "--spread",
            "three-card",
            "--mode",
            "decision-support",
            "--no-reversals",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    content = next(tmp_path.glob("*.md")).read_text(encoding="utf-8")
    assert "orientation: reversed" not in content
    assert "| upright |" in content


def test_list_commands_show_bundled_resources():
    runner = CliRunner()

    decks = runner.invoke(app, ["list-decks"])
    spreads = runner.invoke(app, ["list-spreads"])

    assert decks.exit_code == 0
    assert "rider-waite-smith" in decks.output
    assert spreads.exit_code == 0
    assert "three-card" in spreads.output
    assert "avoidance-reality-next-move" in spreads.output


def test_draw_accepts_confidence_context_and_custom_tags(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "draw",
            "--deck",
            "rider-waite-smith",
            "--spread",
            "three-card",
            "--mode",
            "decision-support",
            "--question",
            "What should I prioritize this week?",
            "--confidence",
            "3",
            "--context",
            "career / writing / money",
            "--tags",
            "career,writing",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    content = next(tmp_path.glob("*.md")).read_text(encoding="utf-8")
    assert "confidence: 3" in content
    assert "context: career / writing / money" in content
    assert "- career" in content
    assert "- writing" in content
    assert "## Context\n\ncareer / writing / money" in content


def test_review_command_reads_valid_reading(tmp_path):
    runner = CliRunner()
    draw_result = runner.invoke(
        app,
        [
            "draw",
            "--deck",
            "rider-waite-smith",
            "--spread",
            "three-card",
            "--mode",
            "decision-support",
            "--question",
            "What should I prioritize this week?",
            "--output",
            str(tmp_path),
        ],
    )
    assert draw_result.exit_code == 0
    path = next(tmp_path.glob("*.md"))

    result = runner.invoke(app, ["review", str(path)])

    assert result.exit_code == 0
    assert "question: What should I prioritize this week?" in result.output
    assert "spread: three-card" in result.output
    assert "review_status: pending" in result.output


def test_review_command_rejects_non_reading_file(tmp_path):
    path = tmp_path / "not-reading.md"
    path.write_text("---\ntype: note\n---\nBody\n", encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(app, ["review", str(path)])

    assert result.exit_code != 0
    assert "File is not a tarot-reading" in result.output


def test_review_command_updates_frontmatter_without_damaging_body(tmp_path):
    runner = CliRunner()
    runner.invoke(
        app,
        [
            "draw",
            "--deck",
            "rider-waite-smith",
            "--spread",
            "three-card",
            "--mode",
            "decision-support",
            "--question",
            "What should I prioritize this week?",
            "--output",
            str(tmp_path),
        ],
    )
    path = next(tmp_path.glob("*.md"))
    before = path.read_text(encoding="utf-8")
    body = before.split("---", 2)[2]

    result = runner.invoke(
        app,
        [
            "review",
            str(path),
            "--review-status",
            "reviewed",
            "--usefulness-score",
            "4",
            "--projection-risk",
            "medium",
            "--action-taken",
            "Sent the email",
        ],
    )

    assert result.exit_code == 0
    after = path.read_text(encoding="utf-8")
    assert "review_status: reviewed" in after
    assert "usefulness_score: 4" in after
    assert "projection_risk: medium" in after
    assert "action_taken: Sent the email" in after
    assert after.split("---", 2)[2] == body
