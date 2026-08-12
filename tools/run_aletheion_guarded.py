#!/usr/bin/env python3
"""Fail-closed production wrapper for Aletheion Daily Sky generation.

This wrapper owns the production date contract. It resolves the requested date in
America/New_York, requires strict ISO YYYY-MM-DD, validates Aletheion's calculated
sky date before any durable write, validates the rendered H1, and only then
publishes the canonical note and observation/event records.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

import aletheion

CANONICAL_TZ = "America/New_York"
H1_RE = re.compile(r"^# Daily Sky - (\d{4}-\d{2}-\d{2})$", re.MULTILINE)
FILENAME_RE = re.compile(r"^Daily Sky - (\d{4}-\d{2}-\d{2})\.md$")


def canonical_day(value: str | None, timezone: str = CANONICAL_TZ) -> str:
    if value:
        parsed = aletheion.parse_day(value)
    else:
        parsed = datetime.now(ZoneInfo(timezone)).date()
    return parsed.isoformat()


def validate_existing_note(path: Path, requested_day: str) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size == 0:
        return False, "missing-or-empty"
    match = FILENAME_RE.match(path.name)
    if not match or match.group(1) != requested_day:
        return False, "filename-date-mismatch"
    text = path.read_text(encoding="utf-8")
    h1 = H1_RE.search(text)
    if not h1 or h1.group(1) != requested_day:
        return False, "heading-date-mismatch"
    required = [
        "- Instrument: Aletheion",
        "- Sky data source: swetest",
        "- Data status: calculated / Swiss Ephemeris",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        return False, "invalid-provenance:" + ",".join(missing)
    return True, "valid"


def validate_rendered_note(note: str, requested_day: str, sky: dict) -> None:
    source_day = str(sky.get("date", ""))
    if source_day != requested_day:
        raise RuntimeError(
            f"DATE_INTEGRITY_FAILURE requested={requested_day} sky.date={source_day!r}"
        )
    h1 = H1_RE.search(note)
    if not h1 or h1.group(1) != requested_day:
        raise RuntimeError(
            f"DATE_INTEGRITY_FAILURE requested={requested_day} rendered_h1={h1.group(1) if h1 else None!r}"
        )
    if sky.get("source") != "swetest":
        raise RuntimeError(
            f"PROVENANCE_FAILURE requested={requested_day} source={sky.get('source')!r}"
        )
    if aletheion.sky_data_status(sky) != "calculated / Swiss Ephemeris":
        raise RuntimeError(
            "PROVENANCE_FAILURE requested="
            f"{requested_day} data_status={aletheion.sky_data_status(sky)!r}"
        )


def append_event(root: Path, requested_day: str, sky: dict, out_path: Path, contacts, sign_activations, temporal) -> None:
    aletheion.append_jsonl(
        root / "memory" / "events.jsonl",
        {
            "timestamp": datetime.now(ZoneInfo(CANONICAL_TZ)).isoformat(timespec="seconds"),
            "date": requested_day,
            "source": sky.get("source"),
            "output": str(out_path),
            "date_contract": "YYYY-MM-DD",
            "contact_count": len(contacts),
            "sign_activation_count": len(sign_activations),
            "lunation_alert_count": len(temporal.get("lunation_alerts", [])),
            "astronomy_alert_count": len(temporal.get("astronomy_alerts", [])),
            "eclipse_alert_count": len(temporal.get("eclipse_alerts", [])),
            "strongest_contact": None
            if not contacts
            else {
                "transiting_body": contacts[0].transiting_body,
                "aspect": contacts[0].aspect,
                "natal_point": contacts[0].natal_point,
                "orb": contacts[0].orb,
            },
        },
    )


def run(requested_day: str, force: bool = False) -> Path:
    root = Path(__file__).resolve().parents[1]
    config = aletheion.load_json(root / "config" / "aletheion.config.json")
    aletheion.resolve_repo_relative_config_paths(config, root)

    requested_day = canonical_day(requested_day, config.get("person", {}).get("timezone", CANONICAL_TZ))
    out_path = aletheion.output_path_for(config, requested_day)

    if not force:
        valid, reason = validate_existing_note(out_path, requested_day)
        if valid:
            print(json.dumps({"status": "already-valid", "date": requested_day, "output": str(out_path)}))
            return out_path
        if out_path.exists():
            raise RuntimeError(
                f"EXISTING_NOTE_INVALID requested={requested_day} path={out_path} reason={reason}"
            )

    sky, temporal, contacts, sign_activations, observations = aletheion.build_daily_context(
        config, root, requested_day
    )
    note = aletheion.render_daily_note(
        config, sky, contacts, sign_activations, temporal, observations
    )
    validate_rendered_note(note, requested_day, sky)

    # Durable writes begin only after every date/provenance invariant passes.
    aletheion.save_text(out_path, note)
    aletheion.upsert_jsonl_records(aletheion.observation_ledger_path(root), observations)
    append_event(root, requested_day, sky, out_path, contacts, sign_activations, temporal)

    print(json.dumps({"status": "written", "date": requested_day, "output": str(out_path)}))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Guarded Aletheion production runner")
    parser.add_argument("--date", help="Strict ISO date YYYY-MM-DD. Defaults to America/New_York today.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    run(canonical_day(args.date), force=args.force)


if __name__ == "__main__":
    main()
