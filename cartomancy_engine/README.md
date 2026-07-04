# Cartomancy Engine

Local-first Tarot reading logger and symbolic audit tool for Axisarium.

Cartomancy Engine treats Tarot as structured symbolic inquiry, not automatic truth. A reading is useful only if it improves reflection, action, or later understanding. Phase 2 adds review and audit tools so symbolic practice can generate accountable personal knowledge over time.

This is not an oracle and not an AI interpretation engine. It does not tell you what is true. It helps you track what you asked, what symbols appeared, what you thought they meant, what action you chose, what later happened, and whether the reading helped.

The epistemic loop is:

```text
draw -> reflect -> choose action -> follow up -> audit usefulness
```

## Install

From this folder:

```powershell
pip install -e .
```

For development tests:

```powershell
pip install -e ".[dev]"
pytest
```

## Commands

Basic draw:

```powershell
cartomancy-engine draw --deck rider-waite-smith --spread three-card --mode decision-support
```

Draw with a question:

```powershell
cartomancy-engine draw --deck rider-waite-smith --spread three-card --mode decision-support --question "What should I prioritize this week?"
```

Draw with Phase 2 audit metadata:

```powershell
cartomancy-engine draw --mode decision-support --question "What should I prioritize this week?" --confidence 3 --context "career / writing / money"
```

Write to a specific folder:

```powershell
cartomancy-engine draw --deck rider-waite-smith --spread three-card --mode decision-support --question "What should I prioritize this week?" --output "H:\My Drive\Axisarium\03 Readings\Tarot"
```

Preview without writing:

```powershell
cartomancy-engine draw --deck rider-waite-smith --spread three-card --mode decision-support --question "What should I prioritize this week?" --dry-run
```

List bundled data:

```powershell
cartomancy-engine list-decks
cartomancy-engine list-spreads
```

Review a reading:

```powershell
cartomancy-engine review ".\readings\2026-06-26_tarot-reading_prioritize-this-week.md"
```

Update review frontmatter:

```powershell
cartomancy-engine review ".\readings\2026-06-26_tarot-reading_prioritize-this-week.md" --review-status reviewed --usefulness-score 4 --projection-risk medium --action-taken "Sent the email"
```

## Example Markdown Excerpt

```md
---
type: tarot-reading
date: '2026-06-26'
deck: rider-waite-smith
spread: three-card
mode: decision-support
question: 'What should I prioritize this week?'
context: ''
confidence: null
cards:
- position: 1
  card: The Fool
  orientation: upright
tags:
- tarot
- aletheion
- symbolic-audit
review_status: pending
review_date: null
usefulness_score: null
projection_risk: null
action_taken: null
claim_types:
- observation
- symbolic-association
- intuition
- interpretation
- prediction
- action-recommendation
---

# Tarot Reading - 2026-06-26

## Cards Drawn

| Position | Card | Orientation | Keywords |
| --- | --- | --- | --- |
| 1. Current Pattern | The Fool | upright | beginning, risk, innocence, threshold |

## Epistemic Claim Types

Use these labels while interpreting:

- Observation:
- Symbolic association:
- Intuition:
- Interpretation:
- Prediction:
- Action recommendation:
```

## v0.1 Boundaries

- Major Arcana only.
- No card images.
- No AI interpretation.
- No Obsidian plugin or daily note insertion.
- No cloud sync or web UI.
- No astrology/Aletheion sky correlation.
- No recurrence detection or statistics.
