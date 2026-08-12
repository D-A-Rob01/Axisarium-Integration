import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_topologos_source import SourceValidationError, validate_source  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
