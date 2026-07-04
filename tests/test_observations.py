import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import aletheion  # noqa: E402


class ObservationTests(unittest.TestCase):
    def sample_context(self):
        config = {"temporal_awareness": {"exactitude_window_hours": 36}}
        sky = {
            "date": "2026-06-26",
            "source": "swetest",
            "bodies": [
                {
                    "name": "Sun",
                    "sign": "Cancer",
                    "degree": 4.91,
                    "longitude": 94.91,
                    "speed": "direct",
                    "speed_degrees_per_day": 0.95359,
                }
            ],
            "moon_phase": {
                "label": "Waxing Gibbous",
                "illumination_percent": 89.3,
                "sun_moon_angle": 141.77,
                "motion": "waxing",
                "confidence": "High",
                "source": "Swiss Ephemeris",
                "calculation": "Derived from Swiss Ephemeris Sun and Moon longitudes",
            },
        }
        contacts = [
            aletheion.Contact(
                transiting_body="Sun",
                natal_point="Midheaven",
                aspect="trine",
                orb=0.12,
                status="applying",
                transit_theme="identity, vitality, authorship",
                natal_keywords=["public language", "teaching"],
                priority=1,
                exact_at="2026-06-26 15:00 UTC",
            )
        ]
        sign_activations = [
            aletheion.SignActivation(
                transiting_body="Sun",
                sign="Cancer",
                natal_point="Sun",
                natal_keywords=["solar identity", "lineage"],
            )
        ]
        temporal = {
            "house_positions": [{"body": "Sun", "house": 10}],
            "lunation_alerts": [
                aletheion.TemporalEvent(
                    category="lunation",
                    title="Full Moon",
                    when="2026-06-29 23:56 UTC",
                    detail="Sun-Moon angle reaches 180 degrees.",
                    confidence="Medium",
                    source="Swiss Ephemeris",
                    calculation="Derived interpolation from 6-hour longitude samples.",
                )
            ],
            "astronomy_alerts": [],
            "eclipse_alerts": [],
        }
        return config, sky, contacts, sign_activations, temporal

    def test_observation_ids_are_deterministic(self):
        identity = {"body": "Sun"}
        first = aletheion.observation_id_for("2026-06-26", "sky_body", identity)
        second = aletheion.observation_id_for("2026-06-26", "sky_body", dict(identity))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("obs:2026-06-26:sky_body:"))

    def test_records_include_schema_version(self):
        records = aletheion.build_observation_records(*self.sample_context())
        self.assertTrue(records)
        self.assertTrue(all(record["schema_version"] == aletheion.OBSERVATION_SCHEMA_VERSION for record in records))
        self.assertTrue(all(record["layer"] == "observation" for record in records))

    def test_records_do_not_contain_interpretive_or_promotion_markers(self):
        records = aletheion.build_observation_records(*self.sample_context())
        serialized = json.dumps(records, ensure_ascii=False).lower()
        forbidden_terms = [
            "#mnemo",
            "mnemo",
            "promotion",
            "promoted",
            "aurelius",
            "aurelius vector",
            "interpretive weather",
            "symbolic reading",
            "practical emphasis",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, serialized)

        forbidden_fields = {
            "mnemo_status",
            "mnemo_tags",
            "promotion_score",
            "promotion_dimensions",
            "aurelius_vector",
        }
        for record in records:
            self.assertTrue(forbidden_fields.isdisjoint(record.keys()))
            self.assertTrue(forbidden_fields.isdisjoint(record.get("fields", {}).keys()))

    def test_upsert_jsonl_records_replaces_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.jsonl"
            first = aletheion.make_observation_record(
                day="2026-06-26",
                kind="sky_body",
                identity_fields={"body": "Sun"},
                description="Sun recorded in Cancer at 4.91 degrees.",
                source="Swiss Ephemeris",
                data_status="calculated / Swiss Ephemeris",
                confidence="High",
                calculation="Loaded from the daily sky body table.",
                fields={"body": "Sun", "degree": 4.91},
            )
            second = dict(first)
            second["fields"] = {"body": "Sun", "degree": 4.92}
            aletheion.upsert_jsonl_records(path, [first])
            aletheion.upsert_jsonl_records(path, [second])
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["fields"]["degree"], 4.92)

    def test_discover_vault_dates_excludes_addenda(self):
        with tempfile.TemporaryDirectory() as tmp:
            sky_dir = Path(tmp) / "02 Daily Sky"
            sky_dir.mkdir(parents=True)
            (sky_dir / "Daily Sky - 2026-06-24.md").write_text("", encoding="utf-8")
            (sky_dir / "Daily Sky - 2026-06-24 - Mnemo Candidate Addendum.md").write_text("", encoding="utf-8")
            (sky_dir / "Daily Sky - 2026-06-25.md").write_text("", encoding="utf-8")
            dates = aletheion.discover_vault_daily_sky_dates(
                {"obsidian_vault_path": tmp, "daily_note_folder": "02 Daily Sky"}
            )
            self.assertEqual(dates, ["2026-06-24", "2026-06-25"])


if __name__ == "__main__":
    unittest.main()
