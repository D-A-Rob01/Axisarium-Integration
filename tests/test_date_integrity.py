import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_topologos_source import (  # noqa: E402
    SourceValidationError,
    validate_source,
    validate_tandem_artifact,
)
from run_aletheion_guarded import (  # noqa: E402
    append_event,
    canonical_day,
    validate_rendered_note,
)


VALID_PROVENANCE = """# Daily Sky - {day}

## Provenance
- Instrument: Aletheion
- Sky data source: swetest
- Data status: calculated / Swiss Ephemeris
"""


class DateIntegrityTests(unittest.TestCase):
    def _write(self, folder: Path, filename_day: str, declared_day: str) -> Path:
        path = folder / f"Daily Sky - {filename_day}.md"
        path.write_text(VALID_PROVENANCE.format(day=declared_day), encoding="utf-8")
        return path

    def test_valid_iso_source_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._write(Path(tmp), "2026-08-11", "2026-08-11")
            result = validate_source("2026-08-11", source)
            self.assertEqual(result["status"], "valid")
            self.assertEqual(
                result["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest()
            )

    def test_august_9_month_day_swap_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._write(Path(tmp), "2026-09-08", "2026-09-08")
            with self.assertRaises(SourceValidationError):
                validate_source("2026-08-09", source)

    def test_august_10_month_day_swap_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._write(Path(tmp), "2026-10-08", "2026-10-08")
            with self.assertRaises(SourceValidationError):
                validate_source("2026-08-10", source)

    def test_august_11_month_day_swap_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._write(Path(tmp), "2026-11-08", "2026-11-08")
            with self.assertRaises(SourceValidationError):
                validate_source("2026-08-11", source)

    def test_filename_and_declared_date_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._write(Path(tmp), "2026-08-11", "2026-11-08")
            with self.assertRaises(SourceValidationError):
                validate_source("2026-08-11", source)

    def test_invalid_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Daily Sky - 2026-08-11.md"
            path.write_text("# Daily Sky - 2026-08-11\n", encoding="utf-8")
            with self.assertRaises(SourceValidationError):
                validate_source("2026-08-11", path)

    def test_guarded_render_requires_provenance_markers(self):
        sky = {"date": "2026-08-16", "source": "swetest"}
        with self.assertRaisesRegex(RuntimeError, "PROVENANCE_FAILURE"):
            validate_rendered_note("# Daily Sky - 2026-08-16\n", "2026-08-16", sky)

    def test_event_timestamp_uses_portable_utc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            append_event(
                root,
                "2026-08-16",
                {"source": "swetest"},
                root / "Daily Sky - 2026-08-16.md",
                [],
                [],
                {},
            )
            record = json.loads(
                (root / "memory" / "events.jsonl").read_text(encoding="utf-8")
            )
            timestamp = datetime.fromisoformat(record["timestamp"])
            self.assertEqual(timestamp.utcoffset(), timedelta(0))

    def test_guarded_runner_rejects_noncanonical_iso_dates(self):
        self.assertEqual(canonical_day("2026-08-16"), "2026-08-16")
        for value in (
            "20260816",
            "2026-W33-7",
            "2026-8-16",
            "2026-08-16T00:00:00",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "exact YYYY-MM-DD"):
                    canonical_day(value)

    def test_scheduled_runner_orders_guarded_producer_before_source_gate(self):
        runner = (ROOT / "run-daily-aletheion.ps1").read_text(encoding="utf-8")
        producer_call = runner.index("$Output = & $Python @Arguments")
        gate_call = runner.index("$GateOutput = & $Python @GateArguments")
        self.assertLess(producer_call, gate_call)
        self.assertIn('"--dry-run", "--stage-dir"', runner)
        self.assertIn("production note, ledgers, and captures were not written", runner)

    def test_scheduled_runner_rejects_noncanonical_dates_before_paths(self):
        runner = (ROOT / "run-daily-aletheion.ps1").read_text(encoding="utf-8")
        exact_parse = runner.index("[DateTime]::TryParseExact")
        output_path = runner.index("$OutputPath =")
        self.assertLess(exact_parse, output_path)
        self.assertIn('"yyyy-MM-dd"', runner)
        self.assertIn("expected exact YYYY-MM-DD", runner)
        self.assertNotIn("$Day = $Date", runner)

    def test_tandem_requires_hash_bound_manifest_and_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            day = "2026-08-15"
            source = self._write(folder, day, day).resolve()
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            tandem = folder / f"Daily Sky - {day} - Aletheion x Topologos.md"
            tandem.write_text(
                f"# Daily Sky - {day} — Aletheion × Topologos\n\n"
                f"- Aletheion source note: `{source}`\n",
                encoding="utf-8",
            )
            static_reference = folder / "topologos.static-reference.json"
            static_reference.write_text('{"schema_version":"test"}\n', encoding="utf-8")
            observations = folder / "observations.jsonl"
            observation = {
                "schema_version": "aletheion.observation.v1",
                "observation_id": f"obs:{day}:sky_body:test",
                "date": day,
                "kind": "sky_body",
                "source": "Swiss Ephemeris",
                "data_status": "calculated / Swiss Ephemeris",
            }
            observations.write_text(json.dumps(observation) + "\n", encoding="utf-8")
            record_payload = json.dumps(
                [observation],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
            record_hash = hashlib.sha256(record_payload).hexdigest()
            static_hash = hashlib.sha256(static_reference.read_bytes()).hexdigest()
            tandem_hash = hashlib.sha256(tandem.read_bytes()).hexdigest()
            manifest = folder / f"manifest-{day}.json"
            manifest_data = {
                "schema_version": "aletheion-topologos.tandem.v1",
                "date": day,
                "run_id": "run-1",
                "aletheion_source": str(source),
                "aletheion_source_sha256": source_hash,
                "tandem_note_sha256": tandem_hash,
                "static_reference": {
                    "path": str(static_reference.resolve()),
                    "sha256": static_hash,
                },
                "dynamic_evidence": {
                    "path": str(observations.resolve()),
                    "record_set_sha256": record_hash,
                    "record_count": 1,
                },
                "artifacts": {"note": str(tandem.resolve())},
                "telemetry": {"degraded": False},
            }
            manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
            envelope = folder / f"cabeir-envelope-{day}.json"
            envelope.write_text(
                json.dumps(
                    {
                        "schema_version": "cabeir.envelope.v1",
                        "run_id": "run-1",
                        "provenance": [
                            {
                                "source": "Aletheion Daily Sky source note",
                                "source_path": str(source),
                                "source_sha256": source_hash,
                                "verification_status": "verified",
                            },
                            {
                                "source": "Topologos frozen natal topology",
                                "source_path": str(static_reference.resolve()),
                                "source_sha256": static_hash,
                                "verification_status": "verified",
                            },
                            {
                                "source": "Aletheion persisted observation ledger",
                                "source_path": str(observations.resolve()),
                                "source_sha256": record_hash,
                                "verification_status": "verified",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = validate_tandem_artifact(day, source, tandem, manifest, envelope)
            self.assertEqual(result["tandem_status"], "valid")

            manifest_data["aletheion_source_sha256"] = "0" * 64
            manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
            with self.assertRaisesRegex(
                SourceValidationError, "TANDEM_MANIFEST_SOURCE_HASH_MISMATCH"
            ):
                validate_tandem_artifact(day, source, tandem, manifest, envelope)


if __name__ == "__main__":
    unittest.main()
