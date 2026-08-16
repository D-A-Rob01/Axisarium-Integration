#!/usr/bin/env python3
"""Hard date/provenance gate for Topologos Aletheion ingestion.

Topologos must not render a tandem artifact unless the requested date, source
filename date, Aletheion note H1 date, and Aletheion provenance all agree.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

SOURCE_NAME_RE = re.compile(r"^Daily Sky - (\d{4}-\d{2}-\d{2})\.md$")
H1_RE = re.compile(r"^# Daily Sky - (\d{4}-\d{2}-\d{2})$", re.MULTILINE)
TANDEM_NAME_RE = re.compile(
    r"^Daily Sky - (\d{4}-\d{2}-\d{2}) - Aletheion x Topologos\.md$"
)
TANDEM_H1_RE = re.compile(
    r"^# Daily Sky - (\d{4}-\d{2}-\d{2}) — Aletheion × Topologos$",
    re.MULTILINE,
)


class SourceValidationError(RuntimeError):
    pass


def canonical_iso(value: str) -> str:
    return date.fromisoformat(value).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _observation_record_set(path: Path, requested: str) -> tuple[str, int]:
    selected: list[dict] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise SourceValidationError(
                f"DYNAMIC_EVIDENCE_JSON_INVALID line={line_number} error={str(exc)!r}"
            ) from exc
        if record.get("date") == requested:
            selected.append(record)
    selected.sort(key=lambda record: str(record.get("observation_id", "")))
    payload = json.dumps(
        selected,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest(), len(selected)


def _resolved_equal(left: str | Path, right: str | Path) -> bool:
    return Path(left).resolve() == Path(right).resolve()


def validate_source(requested_date: str, source: Path) -> dict[str, str]:
    requested = canonical_iso(requested_date)
    source = source.resolve()
    if not source.is_file() or source.stat().st_size == 0:
        raise SourceValidationError(f"SOURCE_MISSING_OR_EMPTY path={str(source)!r}")

    filename_match = SOURCE_NAME_RE.fullmatch(source.name)
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
        "source_sha256": _sha256(source),
        "status": "valid",
    }


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SourceValidationError(f"{label}_MISSING_OR_EMPTY path={str(path)!r}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceValidationError(f"{label}_INVALID_JSON path={str(path)!r}") from exc
    if not isinstance(value, dict):
        raise SourceValidationError(f"{label}_INVALID_OBJECT path={str(path)!r}")
    return value


def validate_tandem_artifact(
    requested_date: str,
    source: Path,
    tandem: Path,
    manifest: Path | None = None,
    envelope: Path | None = None,
) -> dict[str, str]:
    """Validate Topologos output against its exact Aletheion source and evidence."""

    source_result = validate_source(requested_date, source)
    requested = source_result["requested_date"]
    source = source.resolve()
    tandem = tandem.resolve()
    output_dir = tandem.parent
    manifest = (manifest or output_dir / f"manifest-{requested}.json").resolve()
    envelope = (envelope or output_dir / f"cabeir-envelope-{requested}.json").resolve()

    if not tandem.is_file() or tandem.stat().st_size == 0:
        raise SourceValidationError(f"TANDEM_MISSING_OR_EMPTY path={str(tandem)!r}")
    filename_match = TANDEM_NAME_RE.fullmatch(tandem.name)
    if not filename_match or canonical_iso(filename_match.group(1)) != requested:
        raise SourceValidationError(
            f"TANDEM_FILENAME_DATE_MISMATCH requested={requested} actual={tandem.name!r}"
        )
    tandem_text = tandem.read_text(encoding="utf-8")
    h1_match = TANDEM_H1_RE.search(tandem_text)
    declared = canonical_iso(h1_match.group(1)) if h1_match else None
    if declared != requested:
        raise SourceValidationError(
            f"TANDEM_DECLARED_DATE_MISMATCH requested={requested} declared={declared!r}"
        )
    if f"- Aletheion source note: `{source}`" not in tandem_text:
        raise SourceValidationError("TANDEM_SOURCE_PATH_MISSING_OR_MISMATCHED")

    manifest_data = _load_json_object(manifest, "TANDEM_MANIFEST")
    if manifest_data.get("schema_version") != "aletheion-topologos.tandem.v1":
        raise SourceValidationError("TANDEM_MANIFEST_SCHEMA_INVALID")
    if manifest_data.get("date") != requested:
        raise SourceValidationError("TANDEM_MANIFEST_DATE_MISMATCH")
    if not _resolved_equal(manifest_data.get("aletheion_source", ""), source):
        raise SourceValidationError("TANDEM_MANIFEST_SOURCE_PATH_MISMATCH")
    if manifest_data.get("aletheion_source_sha256") != source_result["source_sha256"]:
        raise SourceValidationError("TANDEM_MANIFEST_SOURCE_HASH_MISMATCH")
    if manifest_data.get("tandem_note_sha256") != _sha256(tandem):
        raise SourceValidationError("TANDEM_MANIFEST_NOTE_HASH_MISMATCH")

    static_reference = manifest_data.get("static_reference", {})
    if not isinstance(static_reference, dict):
        raise SourceValidationError("TANDEM_STATIC_REFERENCE_INVALID")
    static_path = Path(str(static_reference.get("path", ""))).resolve()
    if not static_path.is_file():
        raise SourceValidationError("TANDEM_STATIC_REFERENCE_MISSING")
    if static_reference.get("sha256") != _sha256(static_path):
        raise SourceValidationError("TANDEM_STATIC_REFERENCE_HASH_MISMATCH")

    dynamic_evidence = manifest_data.get("dynamic_evidence", {})
    if not isinstance(dynamic_evidence, dict):
        raise SourceValidationError("TANDEM_DYNAMIC_EVIDENCE_INVALID")
    dynamic_path = Path(str(dynamic_evidence.get("path", ""))).resolve()
    if not dynamic_path.is_file():
        raise SourceValidationError("TANDEM_DYNAMIC_EVIDENCE_MISSING")
    dynamic_hash, dynamic_count = _observation_record_set(dynamic_path, requested)
    if dynamic_evidence.get("record_set_sha256") != dynamic_hash:
        raise SourceValidationError("TANDEM_DYNAMIC_EVIDENCE_HASH_MISMATCH")
    if dynamic_evidence.get("record_count") != dynamic_count or dynamic_count == 0:
        raise SourceValidationError("TANDEM_DYNAMIC_EVIDENCE_COUNT_MISMATCH")

    artifacts = manifest_data.get("artifacts", {})
    if not isinstance(artifacts, dict) or not _resolved_equal(
        artifacts.get("note", ""), tandem
    ):
        raise SourceValidationError("TANDEM_MANIFEST_NOTE_PATH_MISMATCH")
    telemetry = manifest_data.get("telemetry", {})
    if not isinstance(telemetry, dict) or telemetry.get("degraded") is not False:
        raise SourceValidationError("TANDEM_MANIFEST_DEGRADED_OR_UNDECLARED")

    envelope_data = _load_json_object(envelope, "CABEIR_ENVELOPE")
    if envelope_data.get("schema_version") != "cabeir.envelope.v1":
        raise SourceValidationError("CABEIR_ENVELOPE_SCHEMA_INVALID")
    if envelope_data.get("run_id") != manifest_data.get("run_id"):
        raise SourceValidationError("CABEIR_ENVELOPE_RUN_ID_MISMATCH")
    provenance = envelope_data.get("provenance", [])
    if not isinstance(provenance, list):
        raise SourceValidationError("CABEIR_ENVELOPE_PROVENANCE_INVALID")

    def provenance_record(label: str) -> dict[str, Any]:
        record = next(
            (
                item
                for item in provenance
                if isinstance(item, dict) and item.get("source") == label
            ),
            None,
        )
        if record is None:
            raise SourceValidationError(f"CABEIR_PROVENANCE_MISSING source={label!r}")
        return record

    source_record = provenance_record("Aletheion Daily Sky source note")
    if not _resolved_equal(source_record.get("source_path", ""), source):
        raise SourceValidationError("CABEIR_SOURCE_PATH_MISMATCH")
    if source_record.get("source_sha256") != source_result["source_sha256"]:
        raise SourceValidationError("CABEIR_SOURCE_HASH_MISMATCH")
    if source_record.get("verification_status") != "verified":
        raise SourceValidationError("CABEIR_SOURCE_NOT_VERIFIED")

    static_record = provenance_record("Topologos frozen natal topology")
    if not _resolved_equal(static_record.get("source_path", ""), static_path):
        raise SourceValidationError("CABEIR_STATIC_REFERENCE_PATH_MISMATCH")
    if static_record.get("source_sha256") != static_reference.get("sha256"):
        raise SourceValidationError("CABEIR_STATIC_REFERENCE_HASH_MISMATCH")

    observation_record = provenance_record("Aletheion persisted observation ledger")
    if not _resolved_equal(observation_record.get("source_path", ""), dynamic_path):
        raise SourceValidationError("CABEIR_DYNAMIC_EVIDENCE_PATH_MISMATCH")
    if observation_record.get("source_sha256") != dynamic_evidence.get(
        "record_set_sha256"
    ):
        raise SourceValidationError("CABEIR_DYNAMIC_EVIDENCE_HASH_MISMATCH")

    return {
        **source_result,
        "tandem_path": str(tandem),
        "tandem_sha256": _sha256(tandem),
        "manifest_path": str(manifest),
        "envelope_path": str(envelope),
        "tandem_status": "valid",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Aletheion source and optional Topologos tandem artifacts"
    )
    parser.add_argument("--requested-date", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--tandem")
    parser.add_argument("--manifest")
    parser.add_argument("--envelope")
    args = parser.parse_args()

    try:
        if args.tandem:
            result = validate_tandem_artifact(
                args.requested_date,
                Path(args.source),
                Path(args.tandem),
                Path(args.manifest) if args.manifest else None,
                Path(args.envelope) if args.envelope else None,
            )
        else:
            result = validate_source(args.requested_date, Path(args.source))
    except (ValueError, OSError, SourceValidationError) as exc:
        print(f"TOPOLOGOS_SOURCE_REJECTED: {exc}", file=sys.stderr)
        raise SystemExit(42)

    if args.tandem:
        print(
            "TOPOLOGOS_TANDEM_ACCEPTED "
            f"requested={result['requested_date']} "
            f"source_sha256={result['source_sha256']} "
            f"tandem_sha256={result['tandem_sha256']}"
        )
    else:
        print(
            "TOPOLOGOS_SOURCE_ACCEPTED "
            f"requested={result['requested_date']} "
            f"filename={result['filename_date']} "
            f"declared={result['declared_date']} "
            f"source_sha256={result['source_sha256']}"
        )


if __name__ == "__main__":
    main()
