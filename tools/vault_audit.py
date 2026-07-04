#!/usr/bin/env python3
"""Read-only audit reporter for the Axisarium Obsidian vault.

This script scans vault files and writes markdown reports under reports/.
It does not modify existing notes, templates, or Obsidian settings.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


DEFAULT_VAULT_ROOT = Path(r"C:\Users\david\Documents\Axisarium Vault")
VAULT_ROOT = DEFAULT_VAULT_ROOT
REPORTS_DIR = DEFAULT_VAULT_ROOT / "reports"
TODAY = date.today()

WORKFLOW_TAGS = {
    "capture",
    "triage",
    "review",
    "active",
    "waiting",
    "draft",
    "source",
    "task",
    "question",
    "daily",
    "aletheion",
    "memory-annotation",
}

CANONICAL_TYPES = {
    "daily",
    "sky",
    "inbox",
    "source",
    "permanent",
    "constellation",
    "orbit",
    "project",
    "class",
    "clipping",
    "attachment-index",
    "index",
    "review",
}

CANONICAL_STATUSES = {
    "capture",
    "seed",
    "active",
    "paused",
    "waiting",
    "revising",
    "complete",
    "archived",
}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)")
TAG_RE = re.compile(r"(?<![\w/])#([A-Za-z0-9_/-]+)")
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


@dataclass
class Note:
    path: Path
    rel: str
    text: str
    frontmatter: dict[str, object]
    body: str
    links: list[str]
    tags: list[str]

    @property
    def folder(self) -> str:
        parts = Path(self.rel).parts
        return parts[0] if len(parts) > 1 else "[root]"

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def note_type(self) -> str:
        return str(self.frontmatter.get("type", "") or "")

    @property
    def status(self) -> str:
        return str(self.frontmatter.get("status", "") or "")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def rel(path: Path) -> str:
    return path.relative_to(VAULT_ROOT).as_posix()


def markdown_files() -> list[Path]:
    return sorted(
        p
        for p in VAULT_ROOT.rglob("*.md")
        if ".obsidian" not in p.parts and "reports" not in p.parts
    )


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    frontmatter: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        list_item = re.match(r"^\s+-\s+(.*)$", line)
        if list_item and current_key:
            frontmatter.setdefault(current_key, [])
            if isinstance(frontmatter[current_key], list):
                frontmatter[current_key].append(list_item.group(1).strip())
            continue
        key_value = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_value:
            key, value = key_value.group(1), key_value.group(2).strip()
            current_key = key
            if value == "":
                frontmatter[key] = ""
            elif value in {"[]", "[ ]"}:
                frontmatter[key] = []
            else:
                frontmatter[key] = value.strip("\"'")
    return frontmatter, text[match.end() :]


def normalize_tag(tag: str) -> str:
    return tag.strip().lstrip("#")


def tags_from_frontmatter(frontmatter: dict[str, object]) -> list[str]:
    value = frontmatter.get("tags")
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_tag(str(item)) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [normalize_tag(tag) for tag in re.findall(r"#?([A-Za-z0-9_/-]+)", value)]
    return []


def load_notes() -> list[Note]:
    notes: list[Note] = []
    for path in markdown_files():
        text = read_text(path)
        frontmatter, body = parse_frontmatter(text)
        body_tags = [normalize_tag(tag) for tag in TAG_RE.findall(text)]
        tags = tags_from_frontmatter(frontmatter) + body_tags
        links = [target.strip() for target in WIKI_LINK_RE.findall(text)]
        notes.append(Note(path, rel(path), text, frontmatter, body, links, tags))
    return notes


def md_table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    header_list = list(headers)
    lines = [
        "| " + " | ".join(header_list) + " |",
        "| " + " | ".join("---" for _ in header_list) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write_report(name: str, content: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / name
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def first_heading(note: Note) -> str:
    match = re.search(r"^#\s+(.+)$", note.body, re.MULTILINE)
    return match.group(1).strip() if match else ""


def date_from_note(note: Note) -> str:
    for value in (note.frontmatter.get("date"), note.frontmatter.get("created"), note.stem):
        match = DATE_RE.search(str(value))
        if match:
            return match.group(1)
    match = DATE_RE.search(note.rel)
    return match.group(1) if match else ""


def link_key(target: str) -> str:
    return Path(target).stem


def backlink_counts(notes: list[Note]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for note in notes:
        for target in note.links:
            counts[link_key(target)] += 1
    return counts


def report_inventory(notes: list[Note], backup_note: str) -> None:
    folder_counts = Counter(note.folder for note in notes)
    file_count = len(list(VAULT_ROOT.rglob("*")))
    markdown_count = len(notes)
    rows = [(folder, count) for folder, count in sorted(folder_counts.items())]
    content = f"""# Vault Inventory

Generated: {datetime.now().isoformat(timespec="seconds")}

{backup_note}

## Counts

- Markdown notes scanned: {markdown_count}
- Total filesystem entries in vault: {file_count}
- Vault root: `{VAULT_ROOT}`

## Markdown by Folder

{md_table(["Folder", "Markdown notes"], rows)}

## Top-Level Folders

{md_table(["Name"], ((p.name,) for p in sorted(VAULT_ROOT.iterdir()) if p.is_dir()))}
"""
    write_report("vault_inventory.md", content)


def report_properties(notes: list[Note]) -> None:
    keys = Counter()
    type_values = Counter()
    status_values = Counter()
    missing_frontmatter = []
    noncanonical_types = Counter()
    noncanonical_statuses = Counter()

    for note in notes:
        if not note.frontmatter:
            missing_frontmatter.append(note.rel)
        for key in note.frontmatter:
            keys[key] += 1
        if note.note_type:
            type_values[note.note_type] += 1
            if note.note_type not in CANONICAL_TYPES:
                noncanonical_types[note.note_type] += 1
        if note.status:
            status_values[note.status] += 1
            if note.status not in CANONICAL_STATUSES:
                noncanonical_statuses[note.status] += 1

    types_path = VAULT_ROOT / ".obsidian" / "types.json"
    types_json = {}
    if types_path.exists():
        types_json = json.loads(read_text(types_path))
    obsidian_types = types_json.get("types", {}) if isinstance(types_json, dict) else {}
    author_type = obsidian_types.get("author", "[missing]")

    recommended_types = {
        "aliases": "aliases",
        "cssclasses": "multitext",
        "tags": "tags",
        "type": "text",
        "status": "text",
        "created": "date",
        "updated": "date",
        "date": "date",
        "source": "text",
        "source_type": "text",
        "author": "text",
        "title": "text",
        "year": "number",
        "course": "text",
        "project": "text",
        "constellation": "text",
        "orbits": "multitext",
        "claim": "text",
        "next_action": "text",
        "reviewed": "checkbox",
        "energy": "text",
        "mood": "text",
        "body": "text",
        "focus": "text",
        "sky_note": "text",
    }

    content = f"""# Property Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

## Obsidian Property Types

- Current `.obsidian/types.json` has `author` typed as `{author_type}`.
- Recommended deferred change: set `author` to `text` and expand the property map below.
- No `.obsidian` settings were changed by this first pass.

```json
{json.dumps({"types": recommended_types}, indent=2)}
```

## Property Keys Used

{md_table(["Property", "Count"], keys.most_common())}

## Type Values

{md_table(["Type value", "Count"], type_values.most_common())}

## Noncanonical Type Values for Review

{md_table(["Type value", "Count"], noncanonical_types.most_common()) if noncanonical_types else "No noncanonical type values found."}

## Status Values

{md_table(["Status value", "Count"], status_values.most_common())}

## Noncanonical Status Values for Review

{md_table(["Status value", "Count"], noncanonical_statuses.most_common()) if noncanonical_statuses else "No noncanonical status values found."}

## Notes Missing Frontmatter

{md_table(["Note"], ((item,) for item in missing_frontmatter)) if missing_frontmatter else "No notes missing frontmatter."}
"""
    write_report("property_audit.md", content)


def tag_classification(tag: str) -> str:
    if tag in WORKFLOW_TAGS:
        return "Keep as workflow tag"
    if tag in {"daily-sky", "transits"}:
        return "Consider converting to #aletheion or sky property"
    if "/" in tag:
        return "Needs David review"
    return "Convert to link or property"


def report_tags(notes: list[Note]) -> None:
    tags = Counter(tag for note in notes for tag in note.tags)
    rows = [(f"#{tag}", count, tag_classification(tag)) for tag, count in tags.most_common()]
    content = f"""# Tag Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

Tags are for handling. Links are for meaning. Folders are for arenas. Properties are for state.

## Tags Found

{md_table(["Tag", "Count", "Recommendation"], rows) if rows else "No tags found."}

## Allowed Workflow Tags

{", ".join(f"`#{tag}`" for tag in sorted(WORKFLOW_TAGS))}
"""
    write_report("tag_audit.md", content)


def report_templates(notes: list[Note]) -> None:
    template_dir = VAULT_ROOT / "90 Templates"
    rows = []
    duplicate_headings: defaultdict[str, list[str]] = defaultdict(list)
    for path in sorted(template_dir.glob("*.md")) if template_dir.exists() else []:
        text = read_text(path)
        frontmatter, body = parse_frontmatter(text)
        heading = first_heading(Note(path, rel(path), text, frontmatter, body, [], []))
        duplicate_headings[heading].append(rel(path))
        repeated_sections = [
            section
            for section, count in Counter(re.findall(r"^##\s+(.+)$", body, re.MULTILINE)).items()
            if count > 1
        ]
        rows.append(
            (
                rel(path),
                frontmatter.get("type", ""),
                frontmatter.get("status", ""),
                heading or "[missing]",
                ", ".join(repeated_sections) or "",
            )
        )
    duplicates = [
        (heading or "[missing heading]", ", ".join(paths))
        for heading, paths in duplicate_headings.items()
        if len(paths) > 1
    ]
    content = f"""# Template Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

## Templates

{md_table(["Template", "Type", "Status", "First heading", "Repeated sections"], rows)}

## Duplicate or Near-Duplicate Signals

{md_table(["Signal", "Templates"], duplicates) if duplicates else "No duplicate headings found among templates."}
"""
    write_report("template_audit.md", content)


def report_links(notes: list[Note]) -> None:
    backlinks = backlink_counts(notes)
    no_outbound = [note.rel for note in notes if not note.links and note.folder != "90 Templates"]
    no_inbound = [
        note.rel
        for note in notes
        if backlinks[note.stem] == 0 and note.folder not in {"90 Templates", "reports"}
    ]
    rows_out = ((item,) for item in no_outbound)
    rows_in = ((item,) for item in no_inbound)
    content = f"""# Link Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

## Notes With No Outbound Wiki Links

{md_table(["Note"], rows_out) if no_outbound else "No notes missing outbound wiki links."}

## Notes With No Inbound Wiki Links

{md_table(["Note"], rows_in) if no_inbound else "No notes missing inbound wiki links."}
"""
    write_report("link_audit.md", content)


def report_daily_sky(notes: list[Note]) -> None:
    daily_notes = [note for note in notes if note.folder == "01 Daily Notes"]
    sky_notes = [note for note in notes if note.folder == "02 Daily Sky"]
    sky_stems = {note.stem for note in sky_notes}
    rows = []
    for note in daily_notes:
        note_date = date_from_note(note)
        expected = f"Daily Sky - {note_date}" if note_date else ""
        has_expected = expected in sky_stems if expected else False
        has_sky_link = any("Daily Sky" in link or "02 Daily Sky" in link for link in note.links)
        rows.append((note.rel, note_date, expected, "yes" if has_expected else "no", "yes" if has_sky_link else "no"))

    content = f"""# Daily Sky Linkage Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

Daily Note is the control room. Daily Sky is the weather satellite.

## Daily Notes

{md_table(["Daily note", "Date", "Expected sky note", "Sky exists", "Has sky link"], rows) if rows else "No daily notes found."}

## Daily Sky Notes

{md_table(["Sky note"], ((note.rel,) for note in sky_notes)) if sky_notes else "No Daily Sky notes found."}
"""
    write_report("daily_sky_audit.md", content)


def report_inbox(notes: list[Note]) -> None:
    inbox_notes = [note for note in notes if note.folder == "00 Inbox"]
    rows = []
    old_rows = []
    for note in inbox_notes:
        captures = re.findall(r"^\s*[-*]?\s*(?:\[(seed|question|task|source|draft|memory|project)\]|#([A-Za-z0-9_/-]+))", note.text, re.MULTILINE)
        note_date = date_from_note(note)
        age = ""
        if note_date:
            try:
                age = str((TODAY - datetime.strptime(note_date, "%Y-%m-%d").date()).days)
            except ValueError:
                age = ""
        rows.append((note.rel, note_date, age, len(captures)))
        for match in DATE_RE.finditer(note.text):
            found = datetime.strptime(match.group(1), "%Y-%m-%d").date()
            if (TODAY - found).days > 14:
                old_rows.append((note.rel, match.group(1), (TODAY - found).days))

    content = f"""# Inbox Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

New inbox categorization should be tested for 7 days before any rename, merge, or deletion of `Orbital Dowsings.md`.

## Inbox Notes

{md_table(["Inbox note", "Detected date", "Age days", "Detected prefixed/tagged captures"], rows) if rows else "No inbox notes found."}

## Inbox Dates Older Than 14 Days

{md_table(["Inbox note", "Date marker", "Age days"], old_rows) if old_rows else "No inbox date markers older than 14 days found."}
"""
    write_report("inbox_audit.md", content)


def report_constellation_orbit(notes: list[Note]) -> None:
    candidates = []
    for note in notes:
        text = note.text.lower()
        is_candidate = (
            note.note_type in {"constellation", "orbit"}
            or "constellation" in note.rel.lower()
            or "orbit" in note.rel.lower()
            or "## orbits" in text
        )
        if not is_candidate:
            continue
        missing_constellation = note.note_type == "orbit" and not note.frontmatter.get("constellation")
        candidates.append(
            (
                note.rel,
                note.note_type or "[missing]",
                note.frontmatter.get("constellation", ""),
                len(note.links),
                "yes" if missing_constellation else "no",
            )
        )

    content = f"""# Constellation and Orbit Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

Constellations are major gravitational bodies. Orbits are recurring sub-frameworks, not every stray spark.

## Candidates

{md_table(["Note", "Type", "Linked constellation", "Outbound links", "Orbit missing constellation"], candidates) if candidates else "No constellation or orbit candidates found."}
"""
    write_report("constellation_orbit_audit.md", content)


def report_sync() -> None:
    manifest_path = VAULT_ROOT / ".obsidian" / "plugins" / "remotely-save" / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(read_text(manifest_path))
    data_path = VAULT_ROOT / ".obsidian" / "plugins" / "remotely-save" / "data.json"
    types_path = VAULT_ROOT / ".obsidian" / "types.json"
    local_files = len([p for p in VAULT_ROOT.rglob("*") if p.is_file()])
    content = f"""# Sync Diagnosis

Generated: {datetime.now().isoformat(timespec="seconds")}

This first pass is diagnosis-only. No sync provider, vault path, plugin setting, or `.obsidian` setting was changed.

## Visible Local Facts

- Vault path: `{VAULT_ROOT}`
- Vault appears to live under OneDrive's `Apps/remotely-save` area.
- Remotely Save plugin installed: {"yes" if manifest_path.exists() else "no"}
- Remotely Save version: `{manifest.get("version", "[unknown]")}`
- Remotely Save settings file present: {"yes" if data_path.exists() else "no"}
- Settings file was not inspected because it is sensitive/encrypted.
- `.obsidian/types.json` present: {"yes" if types_path.exists() else "no"}
- Local file count at audit time: {local_files}

## Recommendations

- Keep the current provider during this first pass; changing sync and metadata structure at the same time would blur cause and effect.
- Confirm phone and desktop use the same remote vault target/name inside Remotely Save.
- Confirm Obsidian is open long enough on mobile for the plugin to complete sync.
- Treat Google Drive as a later migration candidate only after confirming current Remotely Save behavior and plan/cost constraints.
- If migration is chosen later, make a fresh backup first and test with a small disposable vault before moving the real vault.

## Documentation Notes

- Remotely Save uses provider-specific remote storage such as OneDrive app storage.
- Google Drive support in Remotely Save is documented separately and may involve paid/pro constraints.
- Auto-sync can fail silently depending on app state, platform background limits, and plugin settings, so sync should be tested with a dated scratch note on both devices.
"""
    write_report("sync_diagnosis.md", content)


def report_review_index(backup_note: str) -> None:
    content = f"""# First Pass Review

Generated: {datetime.now().isoformat(timespec="seconds")}

{backup_note}

Meaning may be mythic; metadata must be mechanical.

## New Governance Docs

- [[Property Schema]]
- [[Tag Policy]]
- [[Daily Note Protocol]]
- [[Inbox Protocol]]
- [[Constellation & Orbit Protocol]]

## Generated Reports

- [[reports/vault_inventory|Vault Inventory]]
- [[reports/property_audit|Property Audit]]
- [[reports/tag_audit|Tag Audit]]
- [[reports/template_audit|Template Audit]]
- [[reports/link_audit|Link Audit]]
- [[reports/daily_sky_audit|Daily Sky Linkage Audit]]
- [[reports/inbox_audit|Inbox Audit]]
- [[reports/constellation_orbit_audit|Constellation and Orbit Audit]]
- [[reports/sync_diagnosis|Sync Diagnosis]]

## Deferred Until Review

- Bulk frontmatter migration.
- Rename, merge, or deletion of `00 Inbox/Orbital Dowsings.md`.
- Any `.obsidian` setting change.
- Any sync provider switch.
- Vault rename.
"""
    write_report("first_pass_review.md", content)


def configure_paths(vault_root: Path, reports_dir: Path | None) -> None:
    global VAULT_ROOT, REPORTS_DIR
    VAULT_ROOT = vault_root.resolve()
    REPORTS_DIR = (reports_dir or VAULT_ROOT / "reports").resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate read-only audit reports for an Obsidian vault.")
    parser.add_argument(
        "--vault",
        default=str(DEFAULT_VAULT_ROOT),
        help="Vault root to scan. Defaults to the live Axisarium vault.",
    )
    parser.add_argument(
        "--reports-dir",
        help="Directory where reports should be written. Defaults to <vault>/reports.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    vault_root = Path(args.vault).expanduser()
    if not vault_root.exists():
        raise SystemExit(f"Vault path does not exist: {vault_root}")
    reports_dir = Path(args.reports_dir).expanduser() if args.reports_dir else None
    configure_paths(vault_root, reports_dir)

    backup_note_path = VAULT_ROOT / "reports" / ".backup_path"
    backup_note = ""
    if backup_note_path.exists():
        backup_path = read_text(backup_note_path).strip()
        backup_note = f"- Backup path: `{backup_path}`"
    else:
        backup_note = "- Backup path: not recorded in reports/.backup_path"

    notes = load_notes()
    report_inventory(notes, backup_note)
    report_properties(notes)
    report_tags(notes)
    report_templates(notes)
    report_links(notes)
    report_daily_sky(notes)
    report_inbox(notes)
    report_constellation_orbit(notes)
    report_sync()
    report_review_index(backup_note)
    print(f"Wrote reports to {REPORTS_DIR}")


if __name__ == "__main__":
    main()
