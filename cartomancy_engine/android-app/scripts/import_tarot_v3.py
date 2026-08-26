"""Import and verify Kybernion Tarot v3 artwork for the Android app."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


ANDROID_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ANDROID_ROOT.parent
DEFAULT_TARGET = ANDROID_ROOT / "app" / "src" / "main" / "assets" / "tarot-v3"
DEFAULT_DECK = ENGINE_ROOT / "src" / "cartomancy_engine" / "data" / "decks" / "rider-waite-smith.json"


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_index(source: Path, deck_path: Path) -> dict:
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    deck = json.loads(deck_path.read_text(encoding="utf-8"))
    artwork = manifest.get("cards", [])
    cards = deck.get("cards", [])
    if len(artwork) != 78 or len(cards) != 78:
        raise ValueError(f"Expected 78 artwork and deck cards; found {len(artwork)} and {len(cards)}")

    by_title: dict[str, dict] = {}
    for entry in artwork:
        key = normalized_title(entry["title"])
        if key in by_title:
            raise ValueError(f"Duplicate artwork title: {entry['title']}")
        by_title[key] = entry

    indexed = []
    used_files: set[str] = set()
    for card in cards:
        key = normalized_title(card["name"])
        if key not in by_title:
            raise ValueError(f"No artwork for canonical card {card['id']}: {card['name']}")
        entry = by_title[key]
        filename = entry["file"]
        svg = source / "cards" / filename
        if not svg.is_file():
            raise ValueError(f"Missing SVG declared by manifest: {filename}")
        if filename in used_files:
            raise ValueError(f"Artwork file mapped more than once: {filename}")
        used_files.add(filename)
        indexed.append(
            {
                "card_id": card["id"],
                "asset_path": f"tarot-v3/cards/{filename}",
                "sha256": digest(svg),
            }
        )

    if len(used_files) != 78:
        raise ValueError(f"Expected 78 unique artwork files; found {len(used_files)}")
    return {
        "schema": "kybernion-android-artwork-v1",
        "deck_id": deck["id"],
        "revision": "v3",
        "count": len(indexed),
        "cards": indexed,
    }


def verify_target(target: Path, expected: dict) -> None:
    index_path = target / "artwork-index.json"
    if not index_path.is_file():
        raise ValueError(f"Missing packaged artwork index: {index_path}")
    actual = json.loads(index_path.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError("Packaged artwork index differs from the authoritative v3 source")
    for entry in actual["cards"]:
        relative = Path(entry["asset_path"]).relative_to("tarot-v3")
        asset = target / relative
        if not asset.is_file() or digest(asset) != entry["sha256"]:
            raise ValueError(f"Packaged artwork failed checksum validation: {asset}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="Path containing v3 manifest.json and cards/")
    parser.add_argument("--deck", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source = args.source.resolve()
    target = args.target.resolve()
    expected = build_index(source, args.deck.resolve())
    if args.check:
        verify_target(target, expected)
        print("Kybernion artwork check passed: 78 canonical v3 SVGs")
        return 0

    cards_target = target / "cards"
    cards_target.mkdir(parents=True, exist_ok=True)
    for existing in cards_target.glob("*.svg"):
        existing.unlink()
    for entry in expected["cards"]:
        filename = Path(entry["asset_path"]).name
        shutil.copy2(source / "cards" / filename, cards_target / filename)
    shutil.copy2(source / "manifest.json", target / "source-manifest.json")
    (target / "artwork-index.json").write_text(
        json.dumps(expected, indent=2) + "\n", encoding="utf-8"
    )
    verify_target(target, expected)
    print(f"Imported {expected['count']} Kybernion v3 SVGs into {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
