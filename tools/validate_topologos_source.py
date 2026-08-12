#!/usr/bin/env python3
"""Hard date/provenance gate for Topologos Aletheion ingestion.

Topologos must not render a tandem artifact unless the requested date, source
filename date, Aletheion note H1 date, and Aletheion provenance all agree.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import sys

SOURCE_NAME_RE = re.compile(r"^Daily Sky - (\d{4}-\d{2}-\d{2})\.md$")
H1_RE = re.compile(r"^# Daily Sky - (\d{4}-\d{2}-\d{2})$", re.MULTILINE)


class SourceValidationError(RuntimeError):
    pass


def canonical_iso(value: str) -> str:
    return date.fromisoformat(value).isoformat()


def validate_source(requested_date: str, source: Path) -> dict[str, str]:
    requested = canonical_iso(requested_date)

    filename_match = SOURCE_NAME_RE.match(source.name)
    if not filename_match:
        raise SourceValidationError(
            f"SOURCE_FILENAME_INVALID expected='Daily Sky - YYYY-MM-DD.md' actual={source.name!r}"
        )
    filename_date = canonical_iso(filename_match.group(1))

    text = source.read_text(encoding="utf-8")
    h1_match = H1_RE.search(text)
    if not h1_match:
        raise SourceValidationError("SOURCE_DECLARED_DATE_MISSING no canonical Daily Sky H1")
    declared_date = canonical_iso(h1_match.group(1))

    values = {
        "requested_date": requested,
        "filename_date": filename_date,
        "declared_date": declared_date,
    }
    if len(set(values.values())) != 1:
        raise SourceValidationError(
            "SOURCE_DATE_MISMATCH " + " ".join(f"{k}={v}" for k, v in values.items())
        )

    required = {
        "instrument": "- Instrument: Aletheion",
        "source": "- Sky data source: swetest",
        "status": "- Data status: calculated / Swiss Ephemeris",
    }
    missing = [name for name, marker in required.items() if marker not in text]
    if missing:
        raise SourceValidationError("SOURCE_PROVENANCE_INVALID missing=" + ",".join(missing))

    return {
        **values,
        "source_path": str(source),
        "status": "valid",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Aletheion source before Topologos ingestion")
    parser.add_argument("--requested-date", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()

    try:
        result = validate_source(args.requested_date, Path(args.source))
    except (ValueError, OSError, SourceValidationError) as exc:
        print(f"TOPOLOGOS_SOURCE_REJECTED: {exc}", file=sys.stderr)
        raise SystemExit(42)

    print(
        "TOPOLOGOS_SOURCE_ACCEPTED "
        f"requested={result['requested_date']} filename={result['filename_date']} declared={result['declared_date']}"
    )


if __name__ == "__main__":
    main()
