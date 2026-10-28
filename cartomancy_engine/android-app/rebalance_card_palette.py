"""Reverse the two established neon colors per card, retaining pixel detail."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "app/src/main/assets/astrerium"
index_path = ASSETS / "index.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
if index.get("palette_revision") != 1:
    raise SystemExit("Expected palette revision 1; refusing to alter already-rebalanced artwork.")
results = {}
for name in sorted({c["file"] for c in index["cards"]}):
    path = ASSETS / name
    img = Image.open(path).convert("RGBA")
    pixels = np.array(img)
    height, width = pixels.shape[:2]
    for card in (c for c in index["cards"] if c["file"] == name):
        x0, x1 = round(card["left"] * width), round(card["right"] * width)
        y0, y1 = round(card["top"] * height), round(card["bottom"] * height)
        view = pixels[y0:y1, x0:x1, :3]
        rgb = view.astype(np.float32) / 255
        hi, lo = rgb.max(axis=2), rgb.min(axis=2)
        delta = hi - lo
        valid = (hi >= .12) & (delta >= hi * .2) & (delta > 0)
        hue = np.zeros_like(hi)
        red, green, blue = np.moveaxis(rgb, 2, 0)
        use = valid & (hi == red)
        hue[use] = ((green[use] - blue[use]) / delta[use]) % 6
        use = valid & (hi == green)
        hue[use] = (blue[use] - red[use]) / delta[use] + 2
        use = valid & (hi == blue)
        hue[use] = (red[use] - green[use]) / delta[use] + 4
        hue /= 6
        aqua = valid & (hue >= .44) & (hue <= .52)
        violet = valid & (hue >= .72) & (hue <= .80)
        na, nv = int(aqua.sum()), int(violet.sum())
        swapped = na > nv
        if swapped:
            # Set the requested target hues while preserving each pixel's value
            # and chroma; calculate both masks before making any changes.
            low, span = lo * 255, delta * 255
            for mask, channels in ((aqua, (142 / 255, 0, 1)),
                                   (violet, (0, 1, 218 / 255))):
                for channel, factor in enumerate(channels):
                    target = np.rint(low + span * factor).clip(0, 255).astype(np.uint8)
                    view[:, :, channel][mask] = target[mask]
        results[card["id"]] = {"aquamarine_before": na, "violet_before": nv,
                               "swapped": swapped}
    img = Image.fromarray(pixels)
    img.save(path, format="PNG", optimize=True)
    digest = sha256(path.read_bytes()).hexdigest()
    index["files"][name] = digest
    if name in index.get("palette", {}).get("assets", {}):
        index["palette"]["assets"][name]["sha256"] = digest
index["palette_revision"] = 2
index["palette"]["balance"] = "Per card, violet #8e00ff is dominant over aquamarine #00ffda; existing already-violet-dominant cards retained."
index["palette"]["balance_results"] = results
index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
print(f"Processed {len(results)} cards; swapped {sum(r['swapped'] for r in results.values())}.")
print("Zero-accent cards:", [k for k, v in results.items() if min(v['aquamarine_before'], v['violet_before']) == 0])
