"""Re-map the approved Neon Cyberspace palette while preserving texture and value.

The hue ranges are deliberately narrow enough to leave warm paint, skin, stone,
and neutral shadows intact. Saturation and value stay pixel-local so the
chiaroscuro and brush texture survive the palette change.
"""
from colorsys import rgb_to_hsv, hsv_to_rgb
from hashlib import sha256
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "app/src/main/assets/astrerium"
BLUE = "#00FFDA"
VIOLET = "#8e00ff"
TARGET_BLUE_H = 0x00FFDA / 255.0  # retained in metadata as the requested swatch
TARGET_VIOLET_H = 0x8e00ff / 255.0

def map_hue(h):
    # HSV hue ranges found in the generated card sheets. The endpoints are
    # intentionally kept away from red/orange/yellow and low-saturation paint.
    if 0.45 <= h <= 0.72:
        return 0.475, "blue"
    if 0.72 < h <= 0.98:
        return 0.758, "violet"
    return None, None

def recolor(path):
    image = Image.open(path).convert("RGBA")
    pixels = list(image.getdata())
    counts = {"blue": 0, "violet": 0}
    out = []
    for r, g, b, a in pixels:
        h, s, v = rgb_to_hsv(r / 255, g / 255, b / 255)
        target, name = map_hue(h) if s >= 0.2 and v >= 0.12 else (None, None)
        if target is not None:
            counts[name] += 1
            rr, gg, bb = hsv_to_rgb(target, s, v)
            out.append((round(rr * 255), round(gg * 255), round(bb * 255), a))
        else:
            out.append((r, g, b, a))
    image.putdata(out)
    image.save(path, format="PNG", optimize=True)
    return counts

def main():
    records = {}
    for path in sorted(ASSETS.glob("*.png")):
        counts = recolor(path)
        records[path.name] = {
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "pixels_remapped": counts,
        }
    index_path = ASSETS / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["palette_revision"] = 1
    index["palette"] = {
        "blue_source": "blue/cyan hues 162–259 degrees",
        "blue_target": BLUE,
        "violet_source": "violet/magenta hues 259–353 degrees",
        "violet_target": VIOLET,
        "method": "hue remap with local saturation/value preserved; warm and neutral pixels untouched",
        "assets": records,
    }
    # The index's existing file hashes are the source-of-truth used by the app.
    index["files"] = {name: record["sha256"] for name, record in records.items() if name.startswith("neon-")}
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": len(records), "remapped": records}, indent=2))

if __name__ == "__main__":
    main()
