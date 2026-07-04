#!/usr/bin/env python3
"""Aletheion: Obsidian-ready daily astrological observatory notes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any


SIGNS = {
    "Aries": 0,
    "Taurus": 30,
    "Gemini": 60,
    "Cancer": 90,
    "Leo": 120,
    "Virgo": 150,
    "Libra": 180,
    "Scorpio": 210,
    "Sagittarius": 240,
    "Capricorn": 270,
    "Aquarius": 300,
    "Pisces": 330,
}

ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180,
}

BODY_THEMES = {
    "Sun": "identity, vitality, authorship",
    "Moon": "mood, body rhythm, instinctive attention",
    "Mercury": "language, study, correspondence, interpretation",
    "Venus": "desire, affinity, aesthetics, value",
    "Mars": "heat, action, conflict, courage",
    "Jupiter": "growth, doctrine, opportunity, excess",
    "Saturn": "limits, structure, obligation, mastery",
    "Uranus": "disruption, liberation, pattern-break",
    "Neptune": "dream, fog, devotion, permeability",
    "Pluto": "depth pressure, compulsion, underworld material",
    "Chiron": "wound, apprenticeship, medicine, difficult integration",
    "True Node": "growth vector, crossings, directional pressure",
}

CONTACT_DURATION_SCALE = {
    "Moon": "Hours",
    "Sun": "Days",
    "Mercury": "Days",
    "Venus": "Days",
    "Mars": "Days",
    "Jupiter": "Weeks",
    "Saturn": "Months",
    "Uranus": "Months",
    "Neptune": "Years",
    "Pluto": "Years",
    "Chiron": "Months",
    "True Node": "Months",
    "Mean Node": "Months",
}

ASPECT_TONES = {
    "conjunction": "fuses with",
    "sextile": "opens a workable channel to",
    "square": "pressurizes",
    "trine": "flows through",
    "opposition": "polarizes against",
}

PLANET_CODE_NAMES = {
    "0": "Sun",
    "1": "Moon",
    "2": "Mercury",
    "3": "Venus",
    "4": "Mars",
    "5": "Jupiter",
    "6": "Saturn",
    "7": "Uranus",
    "8": "Neptune",
    "9": "Pluto",
    "D": "Chiron",
    "t": "True Node",
}

NAME_ALIASES = {
    "true Node": "True Node",
    "true node": "True Node",
    "mean Node": "Mean Node",
    "mean node": "Mean Node",
}

BACKGROUND_BODIES = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron", "True Node"}

SCAN_STEP_HOURS = 6
ALERT_HORIZON_DAYS = 7
ECLIPSE_HORIZON_DAYS = 30
EXACT_EVENT_ORB = 0.5
EXACTITUDE_WINDOW_HOURS = 36
ECLIPSE_NATAL_ORB = 2.0
SIGN_ACTIVATION_VISIBLE_LIMIT = 5
OBSERVATION_SCHEMA_VERSION = "aletheion.observation.v1"
OBSERVATION_LEDGER_FILENAME = "observations.jsonl"
OBSERVATION_KIND_ORDER = {
    "sky_body": 1,
    "moon_phase": 2,
    "natal_contact": 3,
    "exactitude": 4,
    "sign_activation": 5,
    "house_position": 6,
    "temporal_event": 7,
}
LUNATION_TARGETS = {
    "New Moon": 0,
    "First Quarter": 90,
    "Full Moon": 180,
    "Last Quarter": 270,
}


@dataclass
class Contact:
    transiting_body: str
    natal_point: str
    aspect: str
    orb: float
    status: str
    transit_theme: str
    natal_keywords: list[str]
    priority: int
    exact_at: str | None = None
    confidence: str = "High"
    calculation: str = "Swiss Ephemeris longitude comparison"


@dataclass
class SignActivation:
    transiting_body: str
    sign: str
    natal_point: str
    natal_keywords: list[str]


@dataclass
class TemporalEvent:
    category: str
    title: str
    when: str
    detail: str
    confidence: str
    source: str
    calculation: str
    elevated: bool = False


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_repo_relative_config_paths(config: dict[str, Any], root: Path) -> None:
    ephemeris = config.get("ephemeris", {})
    for key in ("swetest_executable", "ephemeris_files_path"):
        value = ephemeris.get(key)
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            ephemeris[key] = str((root / path).resolve())


def normalize_body_name(name: str) -> str:
    return NAME_ALIASES.get(name, name)


def parse_day(day: str) -> date:
    return date.fromisoformat(day)


def parse_utc_time(value: str) -> time:
    parts = [int(part) for part in value.split(":")]
    while len(parts) < 3:
        parts.append(0)
    return time(parts[0], parts[1], parts[2])


def default_snapshot_datetime(day: str, ephemeris: dict[str, Any]) -> datetime:
    return datetime.combine(parse_day(day), parse_utc_time(ephemeris.get("default_utc_time", "12:00:00")))


def temporal_setting(config: dict[str, Any], name: str, default: float) -> float:
    return float(config.get("temporal_awareness", {}).get(name, default))


def format_utc(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def parse_event_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M UTC")
    except ValueError:
        return None


def signed_delta(value: float, target: float) -> float:
    return ((value - target + 180) % 360) - 180


def zodiac_arc_contains(start: float, end: float, value: float) -> bool:
    start %= 360
    end %= 360
    value %= 360
    if start < end:
        return start <= value < end
    return value >= start or value < end


def aspect_signed_delta(transit_longitude: float, natal_longitude: float, exact_angle: float) -> tuple[float, float]:
    separation = (transit_longitude - natal_longitude) % 360
    targets = [exact_angle] if exact_angle in {0, 180} else [exact_angle, (360 - exact_angle) % 360]
    target = min(targets, key=lambda item: abs(signed_delta(separation, item)))
    return signed_delta(separation, target), target


def body_lookup(bodies: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {normalize_body_name(body.get("name", "")): body for body in bodies}


def body_longitude(bodies: list[dict[str, Any]], name: str) -> float | None:
    body = body_lookup(bodies).get(normalize_body_name(name))
    if not body:
        return None
    return longitude_from_point(body)


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def upsert_jsonl_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_id: dict[str, dict[str, Any]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                observation_id = record.get("observation_id")
                if observation_id:
                    by_id[str(observation_id)] = record
    for record in records:
        observation_id = record.get("observation_id")
        if not observation_id:
            raise ValueError("Observation record is missing observation_id")
        by_id[str(observation_id)] = record
    ordered = sorted(
        by_id.values(),
        key=lambda item: (
            item.get("date", ""),
            OBSERVATION_KIND_ORDER.get(str(item.get("kind", "")), 99),
            item.get("observation_id", ""),
        ),
    )
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in ordered:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def longitude_from_point(point: dict[str, Any]) -> float | None:
    if point.get("longitude") is not None:
        return float(point["longitude"]) % 360
    sign = point.get("sign")
    degree = point.get("degree")
    if sign in SIGNS and degree is not None:
        return (SIGNS[sign] + float(degree)) % 360
    return None


def sign_degree_from_longitude(longitude: float) -> tuple[str, float]:
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    sign = list(SIGNS.keys())[sign_index]
    return sign, longitude - (sign_index * 30)


def angular_distance(a: float, b: float) -> float:
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def contact_duration_scale(contact: Contact) -> str:
    return CONTACT_DURATION_SCALE.get(contact.transiting_body, "Days")


def exactitude_window_contacts(day: str, contacts: list[Contact], hours: int = EXACTITUDE_WINDOW_HOURS) -> list[tuple[datetime, Contact]]:
    start = datetime.combine(parse_day(day), time(0, 0))
    end = start + timedelta(hours=hours)
    exact_contacts: list[tuple[datetime, Contact]] = []
    for contact in contacts:
        exact_dt = parse_event_utc(contact.exact_at)
        if exact_dt and start <= exact_dt <= end:
            exact_contacts.append((exact_dt, contact))
    return sorted(exact_contacts, key=lambda item: item[0])


def find_exact_aspect_time(
    samples: list[dict[str, Any]],
    transiting_body: str,
    natal_longitude: float,
    exact_angle: float,
    target: float,
) -> str | None:
    previous: tuple[datetime, float] | None = None
    for sample in samples:
        longitude = body_longitude(sample["bodies"], transiting_body)
        if longitude is None:
            continue
        separation = (longitude - natal_longitude) % 360
        delta = signed_delta(separation, target)
        if previous:
            prev_dt, prev_delta = previous
            if abs(delta) < 0.01 or prev_delta == 0 or (prev_delta < 0 <= delta) or (prev_delta > 0 >= delta):
                return format_utc(interpolate_crossing_time(prev_dt, prev_delta, sample["dt"], delta))
        previous = (sample["dt"], delta)
    return None


def detect_contacts(config: dict[str, Any], sky: dict[str, Any], samples: list[dict[str, Any]] | None = None) -> list[Contact]:
    contacts: list[Contact] = []
    orbs = config.get("aspect_orbs", {})
    natal_points = config.get("natal_points", [])
    samples = samples or []

    for body in sky.get("bodies", []):
        transit_longitude = longitude_from_point(body)
        if transit_longitude is None:
            continue
        for natal in natal_points:
            natal_longitude = longitude_from_point(natal)
            if natal_longitude is None:
                continue
            distance = angular_distance(transit_longitude, natal_longitude)
            for aspect, exact_angle in ASPECTS.items():
                orb_limit = float(orbs.get(aspect, 0))
                orb = abs(distance - exact_angle)
                if orb <= orb_limit:
                    signed, target = aspect_signed_delta(transit_longitude, natal_longitude, exact_angle)
                    next_status = "active"
                    if len(samples) > 1:
                        future_longitude = body_longitude(samples[1]["bodies"], body["name"])
                        if future_longitude is not None:
                            future_signed, _ = aspect_signed_delta(future_longitude, natal_longitude, exact_angle)
                            next_status = "applying" if abs(future_signed) < abs(signed) else "separating"
                    exact_at = find_exact_aspect_time(samples, body["name"], natal_longitude, exact_angle, target)
                    if exact_at:
                        next_status = "applying"
                    priority = 1 if orb < EXACT_EVENT_ORB or exact_at else 2 if next_status == "applying" else 3
                    contacts.append(
                        Contact(
                            transiting_body=normalize_body_name(body["name"]),
                            natal_point=natal["name"],
                            aspect=aspect,
                            orb=round(orb, 2),
                            status=next_status,
                            transit_theme=BODY_THEMES.get(normalize_body_name(body["name"]), "symbolic pressure"),
                            natal_keywords=natal.get("keywords", []),
                            priority=priority,
                            exact_at=exact_at,
                            confidence="High" if orb < EXACT_EVENT_ORB else "Medium" if exact_at else "High",
                            calculation="Swiss Ephemeris longitude comparison" if not exact_at else "Derived interpolation from 6-hour Swiss Ephemeris samples",
                        )
                    )
    return sorted(contacts, key=lambda item: (item.priority, item.orb))


def detect_sign_activations(config: dict[str, Any], sky: dict[str, Any]) -> list[SignActivation]:
    activations: list[SignActivation] = []
    natal_points = config.get("natal_points", [])
    for body in sky.get("bodies", []):
        body_sign = body.get("sign")
        if not body_sign:
            continue
        for natal in natal_points:
            if natal.get("sign") == body_sign:
                activations.append(
                    SignActivation(
                        transiting_body=normalize_body_name(body.get("name", "")),
                        sign=body_sign,
                        natal_point=natal.get("name", ""),
                        natal_keywords=natal.get("keywords", []),
                    )
                )
    return activations


def sky_file_for(day: str, root: Path) -> Path:
    return root / "data" / f"manual_sky_{day}.json"


def load_sky(day: str, root: Path, config: dict[str, Any]) -> dict[str, Any]:
    ephemeris = config.get("ephemeris", {})
    if ephemeris.get("provider") == "swetest":
        executable = ephemeris.get("swetest_executable", "")
        if executable and Path(executable).exists():
            return load_sky_from_swetest(day, ephemeris)

    path = sky_file_for(day, root)
    if path.exists():
        return load_json(path)
    sample_files = sorted((root / "data").glob("manual_sky_*.json"))
    if not sample_files:
        raise FileNotFoundError("No sky data file found in data/.")
    sky = load_json(sample_files[0])
    sky["date"] = day
    sky["source"] = "sample_fallback"
    sky["source_note"] = (
        "No manual sky file exists for this date. This note uses sample data only."
    )
    return sky


def load_sky_from_swetest(day: str, ephemeris: dict[str, Any]) -> dict[str, Any]:
    snapshot_dt = default_snapshot_datetime(day, ephemeris)
    planet_sequence = ephemeris.get("swetest_planet_sequence", "0123456789Dt")
    bodies = calculate_swetest_bodies(ephemeris, snapshot_dt, planet_sequence)
    return {
        "date": day,
        "snapshot_utc": format_utc(snapshot_dt),
        "source": "swetest",
        "source_note": "Planetary positions calculated by a configured Swiss Ephemeris swetest executable.",
        "location": {"label": "geocentric", "latitude": None, "longitude": None},
        "moon_phase": calculate_moon_phase(bodies),
        "weather": {"source": "not_configured", "summary": "Weather provider not connected yet."},
        "bodies": bodies,
        "collective_aspects": [],
        "events": [],
    }


def calculate_swetest_bodies(
    ephemeris: dict[str, Any],
    snapshot_dt: datetime,
    planet_sequence: str | None = None,
) -> list[dict[str, Any]]:
    planet_sequence = planet_sequence or ephemeris.get("swetest_planet_sequence", "0123456789Dt")
    swetest_date = f"{snapshot_dt.day}.{snapshot_dt.month}.{snapshot_dt.year}"
    utc_time = snapshot_dt.strftime("%H:%M:%S")
    command = [
        ephemeris["swetest_executable"],
        f"-b{swetest_date}",
        f"-ut{utc_time}",
        f"-p{planet_sequence}",
        "-fPls",
        "-g,",
        "-head",
        "-speed",
    ]
    ephe_path = ephemeris.get("ephemeris_files_path")
    if ephe_path:
        command.append(f"-edir{ephe_path}")

    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return parse_swetest_output(result.stdout, planet_sequence)


def parse_swetest_output(output: str, planet_sequence: str) -> list[dict[str, Any]]:
    bodies: list[dict[str, Any]] = []
    expected_names = [PLANET_CODE_NAMES.get(code) for code in planet_sequence if code in PLANET_CODE_NAMES]
    expected_index = 0
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or "," not in line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 3:
            continue
        name = normalize_body_name(parts[0] or (expected_names[expected_index] if expected_index < len(expected_names) else ""))
        try:
            longitude = float(parts[1])
            speed_value = float(parts[2])
        except ValueError:
            continue
        sign, degree = sign_degree_from_longitude(longitude)
        bodies.append(
            {
                "name": name,
                "sign": sign,
                "degree": round(degree, 4),
                "longitude": round(longitude % 360, 6),
                "speed": "retrograde" if speed_value < -0.00001 else "direct",
                "speed_degrees_per_day": speed_value,
                "house": None,
            }
        )
        expected_index += 1
    if not bodies:
        raise ValueError("swetest returned no parseable planetary rows.")
    return bodies


def calculate_moon_phase(bodies: list[dict[str, Any]]) -> dict[str, Any]:
    sun_longitude = body_longitude(bodies, "Sun")
    moon_longitude = body_longitude(bodies, "Moon")
    if sun_longitude is None or moon_longitude is None:
        return {
            "label": "not calculated",
            "illumination_percent": None,
            "confidence": "Low",
            "source": "Swiss Ephemeris",
            "calculation": "Sun or Moon longitude unavailable",
        }
    elongation = (moon_longitude - sun_longitude) % 360
    illumination = (1 - math.cos(math.radians(elongation))) / 2 * 100
    if elongation < 45 or elongation >= 315:
        label = "New Moon" if elongation < 6 or elongation >= 354 else "Waning Crescent" if elongation >= 315 else "Waxing Crescent"
    elif elongation < 135:
        label = "First Quarter" if abs(elongation - 90) < 6 else "Waxing Crescent" if elongation < 90 else "Waxing Gibbous"
    elif elongation < 225:
        label = "Full Moon" if abs(elongation - 180) < 6 else "Waxing Gibbous" if elongation < 180 else "Waning Gibbous"
    elif elongation < 315:
        label = "Last Quarter" if abs(elongation - 270) < 6 else "Waning Gibbous" if elongation < 270 else "Waning Crescent"
    else:
        label = "Waning Crescent"
    return {
        "label": label,
        "illumination_percent": round(illumination, 1),
        "sun_moon_angle": round(elongation, 2),
        "motion": "waxing" if elongation < 180 else "waning",
        "confidence": "High",
        "source": "Swiss Ephemeris",
        "calculation": "Derived from Swiss Ephemeris Sun and Moon longitudes",
    }


def build_scan_samples(config: dict[str, Any], day: str, horizon_days: int) -> list[dict[str, Any]]:
    ephemeris = config.get("ephemeris", {})
    if ephemeris.get("provider") != "swetest" or not Path(ephemeris.get("swetest_executable", "")).exists():
        return []
    start_dt = default_snapshot_datetime(day, ephemeris)
    samples: list[dict[str, Any]] = []
    step_hours = int(temporal_setting(config, "scan_step_hours", SCAN_STEP_HOURS))
    steps = int(horizon_days * 24 / step_hours)
    for step in range(steps + 1):
        dt = start_dt + timedelta(hours=step * step_hours)
        samples.append({"dt": dt, "bodies": calculate_swetest_bodies(ephemeris, dt)})
    return samples


def interpolate_crossing_time(dt1: datetime, value1: float, dt2: datetime, value2: float) -> datetime:
    denominator = abs(value1) + abs(value2)
    fraction = 0.5 if denominator == 0 else abs(value1) / denominator
    return dt1 + (dt2 - dt1) * fraction


def find_lunation_alerts(samples: list[dict[str, Any]]) -> list[TemporalEvent]:
    events: list[TemporalEvent] = []
    seen: set[str] = set()
    elongations: list[tuple[datetime, float]] = []
    previous_unwrapped: float | None = None
    for sample in samples:
        sun = body_longitude(sample["bodies"], "Sun")
        moon = body_longitude(sample["bodies"], "Moon")
        if sun is None or moon is None:
            continue
        raw = (moon - sun) % 360
        if previous_unwrapped is None:
            unwrapped = raw
        else:
            unwrapped = raw
            while unwrapped < previous_unwrapped - 180:
                unwrapped += 360
            while unwrapped > previous_unwrapped + 180:
                unwrapped -= 360
        previous_unwrapped = unwrapped
        elongations.append((sample["dt"], unwrapped))

    for (dt1, value1), (dt2, value2) in zip(elongations, elongations[1:]):
        low, high = sorted([value1, value2])
        for label, base_target in LUNATION_TARGETS.items():
            cycle_start = math.floor((low - base_target) / 360) - 1
            cycle_end = math.ceil((high - base_target) / 360) + 1
            for cycle in range(cycle_start, cycle_end + 1):
                target = base_target + 360 * cycle
                if low <= target <= high:
                    event_dt = interpolate_crossing_time(dt1, value1 - target, dt2, value2 - target)
                    key = f"{label}:{event_dt.date().isoformat()}"
                    if key in seen:
                        continue
                    seen.add(key)
                    events.append(
                        TemporalEvent(
                            category="lunation",
                            title=label,
                            when=format_utc(event_dt),
                            detail=f"Sun-Moon angle reaches {base_target} degrees.",
                            confidence="Medium",
                            source="Swiss Ephemeris",
                            calculation="Derived interpolation from 6-hour longitude samples",
                            elevated=True,
                        )
                    )
    return sorted(events, key=lambda event: event.when)


def find_sign_ingress_alerts(samples: list[dict[str, Any]]) -> list[TemporalEvent]:
    events: list[TemporalEvent] = []
    for current, nxt in zip(samples, samples[1:]):
        current_bodies = body_lookup(current["bodies"])
        next_bodies = body_lookup(nxt["bodies"])
        for name, body in current_bodies.items():
            next_body = next_bodies.get(name)
            if not next_body:
                continue
            current_sign = body.get("sign")
            next_sign = next_body.get("sign")
            if current_sign and next_sign and current_sign != next_sign:
                current_longitude = longitude_from_point(body)
                next_longitude = longitude_from_point(next_body)
                if current_longitude is None or next_longitude is None:
                    event_dt = current["dt"] + (nxt["dt"] - current["dt"]) / 2
                else:
                    boundary = SIGNS[next_sign]
                    d1 = signed_delta(current_longitude, boundary)
                    d2 = signed_delta(next_longitude, boundary)
                    event_dt = interpolate_crossing_time(current["dt"], d1, nxt["dt"], d2)
                events.append(
                    TemporalEvent(
                        category="ingress",
                        title=f"{name} enters {next_sign}",
                        when=format_utc(event_dt),
                        detail=f"Sign ingress from {current_sign} to {next_sign}.",
                        confidence="Medium",
                        source="Swiss Ephemeris",
                        calculation="Derived interpolation from 6-hour longitude samples",
                    )
                )
    return events


def find_station_alerts(samples: list[dict[str, Any]]) -> list[TemporalEvent]:
    events: list[TemporalEvent] = []
    for current, nxt in zip(samples, samples[1:]):
        current_bodies = body_lookup(current["bodies"])
        next_bodies = body_lookup(nxt["bodies"])
        for name, body in current_bodies.items():
            next_body = next_bodies.get(name)
            if not next_body:
                continue
            speed = float(body.get("speed_degrees_per_day", 0))
            next_speed = float(next_body.get("speed_degrees_per_day", 0))
            if speed == 0 or (speed < 0 <= next_speed) or (speed > 0 >= next_speed):
                if abs(speed) > 0.25 and abs(next_speed) > 0.25:
                    continue
                event_dt = interpolate_crossing_time(current["dt"], speed, nxt["dt"], next_speed)
                direction = "direct" if next_speed > speed else "retrograde"
                events.append(
                    TemporalEvent(
                        category="station",
                        title=f"{name} stations {direction}",
                        when=format_utc(event_dt),
                        detail=f"Longitude speed crosses zero near {event_dt.strftime('%Y-%m-%d')}.",
                        confidence="Medium",
                        source="Swiss Ephemeris",
                        calculation="Derived interpolation from 6-hour speed samples",
                        elevated=name in {"Mercury", "Venus", "Mars"},
                    )
                )
    return events


def natal_house_cusps(config: dict[str, Any]) -> list[float] | None:
    cusps = config.get("natal_house_cusps", [])
    if len(cusps) != 12:
        return None
    longitudes: list[float] = []
    for item in cusps:
        longitude = item.get("longitude") if isinstance(item, dict) else item
        if longitude is None:
            return None
        longitudes.append(float(longitude) % 360)
    return longitudes


def natal_house_for_longitude(longitude: float, cusps: list[float]) -> int:
    for index, start in enumerate(cusps):
        end = cusps[(index + 1) % 12]
        if zodiac_arc_contains(start, end, longitude):
            return index + 1
    return 12


def natal_house_positions(config: dict[str, Any], sky: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    cusps = natal_house_cusps(config)
    if not cusps:
        return [], "Natal house positions not configured: add 12 cusp longitudes to natal_house_cusps."
    positions = []
    for body in sky.get("bodies", []):
        longitude = longitude_from_point(body)
        if longitude is None:
            continue
        positions.append({"body": normalize_body_name(body.get("name", "")), "house": natal_house_for_longitude(longitude, cusps)})
    return positions, None


def find_house_ingress_alerts(config: dict[str, Any], samples: list[dict[str, Any]]) -> list[TemporalEvent]:
    cusps = natal_house_cusps(config)
    if not cusps:
        return []
    events: list[TemporalEvent] = []
    for current, nxt in zip(samples, samples[1:]):
        current_bodies = body_lookup(current["bodies"])
        next_bodies = body_lookup(nxt["bodies"])
        for name, body in current_bodies.items():
            next_body = next_bodies.get(name)
            current_longitude = longitude_from_point(body)
            next_longitude = longitude_from_point(next_body) if next_body else None
            if current_longitude is None or next_longitude is None:
                continue
            current_house = natal_house_for_longitude(current_longitude, cusps)
            next_house = natal_house_for_longitude(next_longitude, cusps)
            if current_house != next_house:
                events.append(
                    TemporalEvent(
                        category="house ingress",
                        title=f"{name} enters natal house {next_house}",
                        when=format_utc(current["dt"] + (nxt["dt"] - current["dt"]) / 2),
                        detail=f"Natal-house ingress from house {current_house} to house {next_house}.",
                        confidence="Medium",
                        source="Swiss Ephemeris",
                        calculation="Derived interpolation from 6-hour longitude samples and configured natal cusps",
                    )
                )
    return events


def parse_eclipse_datetime(line: str) -> datetime | None:
    match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2}(?:\.\d+)?)", line)
    if not match:
        return None
    day, month, year, hour, minute, second = match.groups()
    whole_second = int(float(second))
    return datetime(int(year), int(month), int(day), int(hour), int(minute), whole_second)


def run_eclipse_command(ephemeris: dict[str, Any], day: str, eclipse_kind: str) -> str:
    snapshot_dt = default_snapshot_datetime(day, ephemeris)
    command = [
        ephemeris["swetest_executable"],
        f"-b{snapshot_dt.day}.{snapshot_dt.month}.{snapshot_dt.year}",
        f"-ut{snapshot_dt.strftime('%H:%M:%S')}",
        eclipse_kind,
        "-head",
    ]
    ephe_path = ephemeris.get("ephemeris_files_path")
    if ephe_path:
        command.append(f"-edir{ephe_path}")
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout


def eclipse_natal_contacts(config: dict[str, Any], ephemeris: dict[str, Any], eclipse_dt: datetime, eclipse_kind: str) -> list[str]:
    try:
        bodies = calculate_swetest_bodies(ephemeris, eclipse_dt)
    except subprocess.CalledProcessError:
        return []
    luminary = "Sun" if eclipse_kind == "-solecl" else "Moon"
    longitude = body_longitude(bodies, luminary)
    if longitude is None:
        return []
    contacts = []
    for natal in config.get("natal_points", []):
        natal_longitude = longitude_from_point(natal)
        if natal_longitude is None:
            continue
        for aspect, angle in ASPECTS.items():
            if abs(angular_distance(longitude, natal_longitude) - angle) <= temporal_setting(config, "eclipse_natal_orb", ECLIPSE_NATAL_ORB):
                contacts.append(f"{luminary} {aspect} natal {natal.get('name')}")
    return contacts[:4]


def find_eclipse_alerts(config: dict[str, Any], day: str) -> list[TemporalEvent]:
    ephemeris = config.get("ephemeris", {})
    if ephemeris.get("provider") != "swetest" or not Path(ephemeris.get("swetest_executable", "")).exists():
        return []
    start_dt = default_snapshot_datetime(day, ephemeris)
    events: list[TemporalEvent] = []
    for command_name, label in [("-solecl", "Solar eclipse"), ("-lunecl", "Lunar eclipse")]:
        output = run_eclipse_command(ephemeris, day, command_name)
        first_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
        event_dt = parse_eclipse_datetime(first_line)
        if not event_dt:
            continue
        delta_days = (event_dt - start_dt).total_seconds() / 86400
        eclipse_horizon = temporal_setting(config, "eclipse_horizon_days", ECLIPSE_HORIZON_DAYS)
        alert_horizon = temporal_setting(config, "alert_horizon_days", ALERT_HORIZON_DAYS)
        if not (0 <= delta_days <= eclipse_horizon):
            continue
        natal_hits = eclipse_natal_contacts(config, ephemeris, event_dt, command_name)
        elevated = delta_days <= alert_horizon or bool(natal_hits)
        detail = first_line
        if natal_hits:
            detail += "; natal contacts: " + "; ".join(natal_hits)
        events.append(
            TemporalEvent(
                category="eclipse",
                title=label,
                when=format_utc(event_dt),
                detail=detail,
                confidence="High",
                source="Swiss Ephemeris",
                calculation="Direct Swiss Ephemeris eclipse search; natal relevance by longitude comparison",
                elevated=elevated,
            )
        )
    return sorted(events, key=lambda event: event.when)


def build_temporal_awareness(config: dict[str, Any], day: str, sky: dict[str, Any]) -> dict[str, Any]:
    samples = build_scan_samples(config, day, int(temporal_setting(config, "alert_horizon_days", ALERT_HORIZON_DAYS)))
    house_positions, house_note = natal_house_positions(config, sky)
    astronomy_alerts = []
    astronomy_alerts.extend(find_station_alerts(samples))
    astronomy_alerts.extend(find_sign_ingress_alerts(samples))
    astronomy_alerts.extend(find_house_ingress_alerts(config, samples))
    return {
        "samples": samples,
        "house_positions": house_positions,
        "house_note": house_note,
        "lunation_alerts": find_lunation_alerts(samples),
        "astronomy_alerts": sorted(astronomy_alerts, key=lambda event: event.when),
        "eclipse_alerts": find_eclipse_alerts(config, day),
    }


def sky_data_status(sky: dict[str, Any]) -> str:
    source = sky.get("source", "unknown")
    if source == "swetest":
        return "calculated / Swiss Ephemeris"
    if "sample" in str(source):
        return "sample / not verified"
    return "manual / user supplied"


def observation_source(sky: dict[str, Any]) -> str:
    return "Swiss Ephemeris" if sky.get("source") == "swetest" else str(sky.get("source", "unknown"))


def observation_confidence_for_sky(sky: dict[str, Any]) -> str:
    source = str(sky.get("source", "unknown"))
    if source == "swetest":
        return "High"
    if "sample" in source:
        return "Low"
    return "Medium"


def observation_id_for(day: str, kind: str, identity_fields: dict[str, Any]) -> str:
    identity = {
        "date": day,
        "kind": kind,
        "fields": identity_fields,
        "schema_version": OBSERVATION_SCHEMA_VERSION,
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()[:16]
    return f"obs:{day}:{kind}:{digest}"


def make_observation_record(
    day: str,
    kind: str,
    identity_fields: dict[str, Any],
    description: str,
    source: str,
    data_status: str,
    confidence: str,
    calculation: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    return {
        "observation_id": observation_id_for(day, kind, identity_fields),
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "date": day,
        "layer": "observation",
        "kind": kind,
        "description": description,
        "source": source,
        "data_status": data_status,
        "confidence": confidence,
        "calculation": calculation,
        "fields": fields,
    }


def build_observation_records(
    config: dict[str, Any],
    sky: dict[str, Any],
    contacts: list[Contact],
    sign_activations: list[SignActivation],
    temporal: dict[str, Any],
) -> list[dict[str, Any]]:
    day = sky["date"]
    source = observation_source(sky)
    data_status = sky_data_status(sky)
    sky_confidence = observation_confidence_for_sky(sky)
    records: list[dict[str, Any]] = []

    for body in sky.get("bodies", []):
        name = normalize_body_name(str(body.get("name", "")))
        degree = body.get("degree")
        longitude = longitude_from_point(body)
        fields = {
            "body": name,
            "sign": body.get("sign"),
            "degree": None if degree is None else round(float(degree), 4),
            "longitude": None if longitude is None else round(float(longitude), 4),
            "speed": body.get("speed"),
            "speed_degrees_per_day": None
            if body.get("speed_degrees_per_day") is None
            else round(float(body["speed_degrees_per_day"]), 6),
        }
        records.append(
            make_observation_record(
                day=day,
                kind="sky_body",
                identity_fields={"body": name},
                description=f"{name} recorded in {fields['sign']} at {fields['degree']} degrees.",
                source=source,
                data_status=data_status,
                confidence=sky_confidence,
                calculation="Loaded from the daily sky body table.",
                fields=fields,
            )
        )

    moon = sky.get("moon_phase", {})
    if moon:
        fields = {
            "label": moon.get("label"),
            "illumination_percent": moon.get("illumination_percent"),
            "sun_moon_angle": moon.get("sun_moon_angle"),
            "motion": moon.get("motion"),
        }
        records.append(
            make_observation_record(
                day=day,
                kind="moon_phase",
                identity_fields={"phase": "moon"},
                description=f"Moon phase recorded as {fields['label']} with {fields['illumination_percent']}% illumination.",
                source=str(moon.get("source", source)),
                data_status=data_status,
                confidence=str(moon.get("confidence", sky_confidence)),
                calculation=str(moon.get("calculation", "Loaded from moon phase data.")),
                fields=fields,
            )
        )

    for contact in contacts:
        fields = {
            "transiting_body": contact.transiting_body,
            "natal_point": contact.natal_point,
            "aspect": contact.aspect,
            "orb": contact.orb,
            "status": contact.status,
            "priority": contact.priority,
            "exact_at": contact.exact_at,
            "duration_scale": contact_duration_scale(contact),
        }
        records.append(
            make_observation_record(
                day=day,
                kind="natal_contact",
                identity_fields={
                    "transiting_body": contact.transiting_body,
                    "natal_point": contact.natal_point,
                    "aspect": contact.aspect,
                },
                description=(
                    f"Transiting {contact.transiting_body} {contact.aspect} natal {contact.natal_point} "
                    f"at {contact.orb:.2f} degrees orb; status {contact.status}."
                ),
                source=source,
                data_status=data_status,
                confidence=contact.confidence,
                calculation=contact.calculation,
                fields=fields,
            )
        )

    exactitude_hours = int(config.get("temporal_awareness", {}).get("exactitude_window_hours", EXACTITUDE_WINDOW_HOURS))
    for exact_dt, contact in exactitude_window_contacts(day, contacts, exactitude_hours):
        exact_at = format_utc(exact_dt)
        fields = {
            "transiting_body": contact.transiting_body,
            "natal_point": contact.natal_point,
            "aspect": contact.aspect,
            "exact_at": exact_at,
            "duration_scale": contact_duration_scale(contact),
            "window_hours": exactitude_hours,
        }
        records.append(
            make_observation_record(
                day=day,
                kind="exactitude",
                identity_fields={
                    "transiting_body": contact.transiting_body,
                    "natal_point": contact.natal_point,
                    "aspect": contact.aspect,
                },
                description=f"{contact.transiting_body} {contact.aspect} natal {contact.natal_point} exact at {exact_at}.",
                source=source,
                data_status=data_status,
                confidence=contact.confidence,
                calculation=contact.calculation,
                fields=fields,
            )
        )

    for activation in sign_activations:
        fields = {
            "transiting_body": activation.transiting_body,
            "sign": activation.sign,
            "natal_point": activation.natal_point,
        }
        records.append(
            make_observation_record(
                day=day,
                kind="sign_activation",
                identity_fields=fields,
                description=f"Transiting {activation.transiting_body} in {activation.sign} shares sign with natal {activation.natal_point}.",
                source=source,
                data_status=data_status,
                confidence="Low",
                calculation="Transit sign equals configured natal sign.",
                fields=fields,
            )
        )

    for item in temporal.get("house_positions", []):
        fields = {"body": item["body"], "house": item["house"]}
        records.append(
            make_observation_record(
                day=day,
                kind="house_position",
                identity_fields={"body": item["body"]},
                description=f"{item['body']} recorded in natal house {item['house']}.",
                source=source,
                data_status=data_status,
                confidence="High",
                calculation="Longitude placed between configured natal house cusps.",
                fields=fields,
            )
        )

    for event in (
        temporal.get("lunation_alerts", [])
        + temporal.get("astronomy_alerts", [])
        + temporal.get("eclipse_alerts", [])
    ):
        fields = {
            "category": event.category,
            "title": event.title,
            "when": event.when,
            "detail": event.detail,
            "elevated": event.elevated,
        }
        records.append(
            make_observation_record(
                day=day,
                kind="temporal_event",
                identity_fields={"category": event.category, "title": event.title, "when": event.when},
                description=f"{event.when}: {event.title}. {event.detail}",
                source=event.source,
                data_status=data_status,
                confidence=event.confidence,
                calculation=event.calculation,
                fields=fields,
            )
        )

    return records


def render_observations_section(lines: list[str], observations: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for record in observations:
        kind = str(record.get("kind", "unknown"))
        counts[kind] = counts.get(kind, 0) + 1
    lines.extend(
        [
            "",
            "## Observations",
            f"- Schema: {OBSERVATION_SCHEMA_VERSION}",
            f"- Ledger: memory/{OBSERVATION_LEDGER_FILENAME}",
            f"- Sky bodies recorded: {counts.get('sky_body', 0)}.",
            f"- Natal contacts recorded: {counts.get('natal_contact', 0)}.",
            f"- Exactitude events recorded: {counts.get('exactitude', 0)}.",
            f"- Sign-level matches recorded: {counts.get('sign_activation', 0)}.",
            f"- Natal house positions recorded: {counts.get('house_position', 0)}.",
            f"- Temporal alerts recorded: {counts.get('temporal_event', 0)}.",
        ]
    )


def render_daily_note(
    config: dict[str, Any],
    sky: dict[str, Any],
    contacts: list[Contact],
    sign_activations: list[SignActivation],
    temporal: dict[str, Any],
    observations: list[dict[str, Any]] | None = None,
) -> str:
    day = sky["date"]
    person = config.get("person", {}).get("name", "the querent")
    source = sky.get("source", "unknown")
    source_note = sky.get("source_note", "")
    weather = sky.get("weather", {})
    moon = sky.get("moon_phase", {})
    data_status = sky_data_status(sky)
    if observations is None:
        observations = build_observation_records(config, sky, contacts, sign_activations, temporal)

    lines: list[str] = [
        f"# Daily Sky - {day}",
        "",
        "## Provenance",
        f"- Instrument: {config.get('name', 'Aletheion')}",
        f"- Sky data source: {source}",
        f"- Data status: {data_status}",
    ]
    if source_note:
        lines.append(f"- Note: {source_note}")

    priority_contacts = [contact for contact in contacts if contact.priority == 1]
    active_contacts = [contact for contact in contacts if contact.priority in {2, 3}]

    lines.extend(["", "## Highest-Priority Natal Contacts"])
    if priority_contacts:
        for contact in priority_contacts[: int(config.get("interpretation_style", {}).get("contact_tiers", {}).get("max_exact_urgent", 8))]:
            render_contact_line(lines, contact)
    else:
        lines.append("- None.")

    render_observations_section(lines, observations)

    interpretive_lines = interpret_day(person, contacts, sign_activations, sky)
    lines.extend(["", "## Interpretive Weather", *interpretive_lines])

    exactitude_hours = int(config.get("temporal_awareness", {}).get("exactitude_window_hours", EXACTITUDE_WINDOW_HOURS))
    render_exactitude_window(lines, day, contacts, exactitude_hours)

    lines.extend(
        [
            "",
            "## Moon Phase",
            f"- Label: {moon.get('label', 'not supplied')}",
            f"- Illumination: {moon.get('illumination_percent') if moon.get('illumination_percent') is not None else 'not supplied'}%",
            f"- Sun-Moon angle: {moon.get('sun_moon_angle', 'not supplied')} deg",
            f"- Motion: {moon.get('motion', 'not supplied')}",
            f"- Confidence: {moon.get('confidence', 'not supplied')}",
            f"- Source: {moon.get('source', source)}",
            f"- Calculation: {moon.get('calculation', 'not supplied')}",
        ]
    )

    lines.extend(
        [
            "",
            "## Raw Sky Data",
            "| Body | Sign | Degree | Speed | Longitude speed/day |",
            "| --- | --- | ---: | --- | ---: |",
        ]
    )
    for body in sky.get("bodies", []):
        degree = body.get("degree")
        degree_text = "" if degree is None else f"{float(degree):.2f}"
        speed_value = body.get("speed_degrees_per_day")
        speed_text = "" if speed_value is None else f"{float(speed_value):.5f}"
        lines.append(
            f"| {body.get('name', '')} | {body.get('sign', '')} | {degree_text} | {body.get('speed', '')} | {speed_text} |"
        )

    lines.extend(["", "## Active Natal Contacts"])

    if active_contacts:
        tier_config = config.get("interpretation_style", {}).get("contact_tiers", {})
        max_active = int(tier_config.get("max_active", 8))
        max_separating = int(tier_config.get("max_background", 6))
        lines.append(f"- {len(contacts)} configured contacts detected; showing applying/separating priorities before sign-level activations.")
        applying_contacts = [contact for contact in active_contacts if contact.priority == 2]
        separating_contacts = [contact for contact in active_contacts if contact.priority == 3]
        if len(applying_contacts) > max_active:
            lines.append(f"- Priority 2 limited to strongest {max_active} of {len(applying_contacts)} applying contacts.")
        render_contact_tier(lines, "Priority 2 - Applying", applying_contacts[:max_active])
        if len(separating_contacts) > max_separating:
            lines.append(f"- Priority 3 limited to strongest {max_separating} of {len(separating_contacts)} separating contacts.")
        render_contact_tier(lines, "Priority 3 - Separating", separating_contacts[:max_separating])
    else:
        lines.append("- No applying or separating configured natal contacts detected.")

    render_sign_activations(lines, sign_activations)

    lines.extend(["", "## Natal House Positions"])
    if temporal.get("house_note"):
        lines.append(f"- {temporal['house_note']}")
        lines.append("- Confidence: Low")
        lines.append("- Source: Config scaffold")
        lines.append("- Calculation: Waiting for exact natal Placidus cusp longitudes")
    elif temporal.get("house_positions"):
        for item in temporal["house_positions"]:
            lines.append(f"- {item['body']}: natal house {item['house']}")
        lines.append("- Confidence: High")
        lines.append("- Source: Swiss Ephemeris + configured natal cusps")
        lines.append("- Calculation: Longitude placed between configured natal house cusps")
    else:
        lines.append("- None calculated.")

    lines.extend(["", "## Lunation Alerts"])
    render_events(lines, temporal.get("lunation_alerts", []), empty="- No exact lunations detected in the next 7 days.")

    lines.extend(["", "## 7-Day Astronomy Alerts"])
    render_events(lines, temporal.get("astronomy_alerts", []), empty="- No stations, sign ingresses, or configured house ingresses detected in the next 7 days.")

    lines.extend(["", "## Eclipse Alerts"])
    render_events(lines, temporal.get("eclipse_alerts", []), empty="- No solar or lunar eclipses detected in the next 30 days.")

    lines.extend(
        [
            "",
            "## Weather",
            f"- Source: {weather.get('source', 'not configured')}",
            f"- Summary: {weather.get('summary', 'Weather data not supplied.')}",
            "",
            "## Writing Current",
            "- Track where language wants precision instead of volume.",
            "- Note any phrase, image, or conceptual pressure that repeats twice today.",
            "",
            "## Study Current",
            "- Give one difficult source a clean thirty-minute window.",
            "- Mark whether attention feels analytic, associative, resistant, or devotional.",
            "",
            "## Body / Energy Attention",
            "- Record sleep, appetite, and nervous-system weather in one plain sentence.",
            "",
            "## Ritual or Reflection Prompt",
            "- What is asking to become visible without being forced into certainty?",
            "",
            "## Tags",
            "#daily-sky #transits #aletheion",
        ]
    )

    return "\n".join(lines) + "\n"


def tier_contacts(config: dict[str, Any], contacts: list[Contact]) -> dict[str, list[Contact]]:
    tier_config = config.get("interpretation_style", {}).get("contact_tiers", {})
    exact_orb = float(tier_config.get("exact_urgent_orb", 0.5))
    active_orb = float(tier_config.get("active_orb", 1.5))
    max_exact = int(tier_config.get("max_exact_urgent", 8))
    max_active = int(tier_config.get("max_active", 8))
    max_background = int(tier_config.get("max_background", 6))

    exact_urgent: list[Contact] = []
    active: list[Contact] = []
    background: list[Contact] = []

    for contact in contacts:
        is_background_body = contact.transiting_body in BACKGROUND_BODIES
        if contact.orb < exact_orb:
            exact_urgent.append(contact)
        elif contact.orb <= active_orb and not is_background_body:
            active.append(contact)
        else:
            background.append(contact)

    return {
        "exact_urgent": exact_urgent[:max_exact],
        "active": active[:max_active],
        "background": background[:max_background],
    }


def render_contact_tier(lines: list[str], title: str, contacts: list[Contact]) -> None:
    lines.append(f"### {title}")
    if not contacts:
        lines.append("- None.")
        return
    for contact in contacts:
        render_contact_line(lines, contact)


def render_exactitude_window(lines: list[str], day: str, contacts: list[Contact], hours: int) -> None:
    lines.extend(["", "## Today's Exactitude Window"])
    exact_contacts = exactitude_window_contacts(day, contacts, hours)
    if not exact_contacts:
        lines.append(f"- No configured transit-to-natal aspects perfect within the next {hours} hours.")
        return
    day_date = parse_day(day)
    for exact_dt, contact in exact_contacts:
        relative = "today" if exact_dt.date() == day_date else "tomorrow"
        lines.append(
            f"- {contact.transiting_body} {contact.aspect} natal {contact.natal_point}: "
            f"exact at {format_utc(exact_dt)} ({relative}). Duration: {contact_duration_scale(contact)}."
        )


def render_sign_activations(lines: list[str], sign_activations: list[SignActivation]) -> None:
    lines.append("### Priority 4 - Sign-Level Activations")
    if not sign_activations:
        lines.append("- No sign-level activations detected from the configured natal foundation.")
        return

    visible = sign_activations[:SIGN_ACTIVATION_VISIBLE_LIMIT]
    hidden = sign_activations[SIGN_ACTIVATION_VISIBLE_LIMIT:]
    for activation in visible:
        render_sign_activation_line(lines, activation)

    if hidden:
        lines.extend(["", f"<details><summary>{len(hidden)} additional sign-level activations</summary>", ""])
        for activation in hidden:
            render_sign_activation_line(lines, activation)
        lines.extend(["", "</details>"])


def render_sign_activation_line(lines: list[str], activation: SignActivation) -> None:
    keywords = ", ".join(activation.natal_keywords) or "natal theme not configured"
    lines.append(f"- {activation.transiting_body} in {activation.sign} activates natal {activation.natal_point}: {keywords}.")


def render_contact_line(lines: list[str], contact: Contact) -> None:
    keywords = ", ".join(contact.natal_keywords) or "natal theme not configured"
    exact_text = f"; exact within horizon: {contact.exact_at}" if contact.exact_at else ""
    lines.append(
        f"- Transiting {contact.transiting_body} {contact.aspect} natal {contact.natal_point} "
        f"(orb {contact.orb:.2f} deg; {contact.status}{exact_text}): "
        f"{contact.transiting_body} themes ({contact.transit_theme}) "
        f"{ASPECT_TONES.get(contact.aspect, 'contacts')} {contact.natal_point} themes ({keywords}). "
        f"Duration: {contact_duration_scale(contact)}. "
        f"Confidence: {contact.confidence}. Source: Swiss Ephemeris. Calculation: {contact.calculation}."
    )


def render_events(lines: list[str], events: list[TemporalEvent], empty: str) -> None:
    if not events:
        lines.append(empty)
        return
    for event in events:
        elevated = " Elevated." if event.elevated else ""
        lines.append(
            f"- {event.when}: {event.title}. {event.detail}{elevated} "
            f"Confidence: {event.confidence}. Source: {event.source}. Calculation: {event.calculation}."
        )


def interpret_day(
    person: str,
    contacts: list[Contact],
    sign_activations: list[SignActivation],
    sky: dict[str, Any],
) -> list[str]:
    if not contacts:
        if sign_activations:
            strongest = sign_activations[0]
            keywords = ", ".join(strongest.natal_keywords) or "the configured natal theme"
            lines = [
                f"- {person}, exact aspect detection is waiting on natal degrees, but the sign-field is already speaking.",
                f"- Most visible sign activation: {strongest.transiting_body} in {strongest.sign} activates natal {strongest.natal_point}, emphasizing {keywords}.",
                "- Treat this as a lower-resolution signal: useful for reflection, not proof of exact timing.",
            ]
            if "sample" in sky.get("source", ""):
                lines.append("- Caution: this is a symbolic demonstration until the sky data is replaced with verified ephemeris values.")
            return lines
        return [
            f"- {person}, the instrument is quiet because natal longitudes are incomplete.",
            "- Treat today as calibration: collect mood, language, weather, and task-flow data.",
        ]

    strongest = contacts[0]
    lines = [
        f"- Strongest configured contact: {strongest.transiting_body} {strongest.aspect} natal {strongest.natal_point}.",
        f"- Symbolic reading: {strongest.transiting_body} {ASPECT_TONES.get(strongest.aspect, 'contacts')} {strongest.natal_point}, asking for attention to {', '.join(strongest.natal_keywords) or 'the configured natal theme'}.",
    ]
    if strongest.transiting_body in {"Mercury", "Moon"}:
        lines.append("- Practical emphasis: write before judging the writing. Let the first pass be diagnostic.")
    elif strongest.transiting_body in {"Mars", "Saturn", "Pluto"}:
        lines.append("- Practical emphasis: move deliberately. Intensity becomes useful when bounded by form.")
    else:
        lines.append("- Practical emphasis: notice what becomes easier when you stop overexplaining it.")

    if "sample" in sky.get("source", ""):
        lines.append("- Caution: this is a symbolic demonstration until the sky data is replaced with verified ephemeris values.")
    return lines


def output_path_for(config: dict[str, Any], day: str) -> Path:
    folder = config.get("daily_note_folder", "02 Daily Sky")
    filename = f"Daily Sky - {day}.md"
    vault = config.get("obsidian_vault_path")
    if not vault:
        raise ValueError("obsidian_vault_path is blank in config/aletheion.config.json")
    return Path(vault) / folder / filename


def observation_ledger_path(root: Path) -> Path:
    return root / "memory" / OBSERVATION_LEDGER_FILENAME


def build_daily_context(config: dict[str, Any], root: Path, day: str) -> tuple[dict[str, Any], dict[str, Any], list[Contact], list[SignActivation], list[dict[str, Any]]]:
    sky = load_sky(day, root, config)
    temporal = build_temporal_awareness(config, day, sky)
    contacts = detect_contacts(config, sky, temporal.get("samples", []))
    sign_activations = detect_sign_activations(config, sky)
    observations = build_observation_records(config, sky, contacts, sign_activations, temporal)
    return sky, temporal, contacts, sign_activations, observations


def date_range(start: str, end: str) -> list[str]:
    start_date = parse_day(start)
    end_date = parse_day(end)
    if end_date < start_date:
        raise ValueError("--to must be on or after --from")
    days: list[str] = []
    current = start_date
    while current <= end_date:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def discover_vault_daily_sky_dates(config: dict[str, Any]) -> list[str]:
    vault = config.get("obsidian_vault_path")
    if not vault:
        raise ValueError("obsidian_vault_path is blank in config/aletheion.config.json")
    folder = Path(vault) / config.get("daily_note_folder", "02 Daily Sky")
    if not folder.exists():
        raise FileNotFoundError(f"Daily Sky folder not found: {folder}")
    dates: list[str] = []
    pattern = re.compile(r"^Daily Sky - (\d{4}-\d{2}-\d{2})\.md$")
    for path in folder.glob("Daily Sky - *.md"):
        match = pattern.match(path.name)
        if match:
            dates.append(match.group(1))
    return sorted(set(dates))


def run_daily(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parent
    config = load_json(root / "config" / "aletheion.config.json")
    resolve_repo_relative_config_paths(config, root)
    day = args.date or date.today().isoformat()
    sky, temporal, contacts, sign_activations, observations = build_daily_context(config, root, day)
    note = render_daily_note(config, sky, contacts, sign_activations, temporal, observations)
    out_path = Path(args.output) if args.output else output_path_for(config, day)
    save_text(out_path, note)
    upsert_jsonl_records(observation_ledger_path(root), observations)
    append_jsonl(
        root / "memory" / "events.jsonl",
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "date": day,
            "source": sky.get("source"),
            "output": str(out_path),
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
    print(str(out_path))


def run_observations(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parent
    config = load_json(root / "config" / "aletheion.config.json")
    resolve_repo_relative_config_paths(config, root)

    if args.discover_vault:
        days = discover_vault_daily_sky_dates(config)
    elif args.date:
        days = [args.date]
    elif args.from_date and args.to_date:
        days = date_range(args.from_date, args.to_date)
    else:
        raise ValueError("Provide --date, --from/--to, or --discover-vault.")

    records: list[dict[str, Any]] = []
    for day in days:
        parse_day(day)
        _, _, _, _, observations = build_daily_context(config, root, day)
        records.extend(observations)

    out_path = Path(args.output) if args.output else observation_ledger_path(root)
    upsert_jsonl_records(out_path, records)
    print(f"{len(records)} observation records written to {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Aletheion Obsidian notes.")
    sub = parser.add_subparsers(dest="command", required=True)
    daily = sub.add_parser("daily", help="Generate a daily sky note.")
    daily.add_argument("--date", help="Date in YYYY-MM-DD format. Defaults to today.")
    daily.add_argument("--output", help="Write to a specific markdown path.")
    daily.add_argument("--vault", action="store_true", help="Deprecated compatibility flag; the configured Obsidian vault is now the default output target.")
    daily.set_defaults(func=run_daily)
    observations = sub.add_parser("observations", help="Generate observation ledger records.")
    observations.add_argument("--date", help="Date in YYYY-MM-DD format.")
    observations.add_argument("--from", dest="from_date", help="Start date in YYYY-MM-DD format.")
    observations.add_argument("--to", dest="to_date", help="End date in YYYY-MM-DD format.")
    observations.add_argument("--discover-vault", action="store_true", help="Backfill exact Daily Sky dates discovered in the configured live vault.")
    observations.add_argument("--output", help=f"Write to a specific JSONL path. Defaults to memory/{OBSERVATION_LEDGER_FILENAME}.")
    observations.set_defaults(func=run_observations)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
