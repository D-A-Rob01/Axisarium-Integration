"""Add blue-violet to portions of each card's violet, without changing aqua."""
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'app/src/main/assets/astrerium'
index_path = ASSETS / 'index.json'
index = json.loads(index_path.read_text(encoding='utf-8'))
if index.get('palette_revision') != 2:
    raise SystemExit('Expected palette revision 2; refusing to repeat this operation.')

counts = {}
for name in sorted({c['file'] for c in index['cards']}):
    path = ASSETS / name
    pixels = np.array(Image.open(path).convert('RGBA'))
    height, width = pixels.shape[:2]
    for card in (c for c in index['cards'] if c['file'] == name):
        x0, x1 = round(card['left'] * width), round(card['right'] * width)
        y0, y1 = round(card['top'] * height), round(card['bottom'] * height)
        view = pixels[y0:y1, x0:x1, :3]
        rgb = view.astype(np.float32)
        low, high = rgb.min(axis=2), rgb.max(axis=2)
        chroma = high - low
        # Revision 2 violet has blue as maximum, green as minimum and a
        # distinctive red-to-chroma ratio near 142/255. Aqua is never selected.
        red, green, blue = np.moveaxis(rgb, 2, 0)
        ratio = np.divide(red - low, chroma, out=np.zeros_like(low), where=chroma > 0)
        violet = (high >= 31) & (chroma >= high * .2) & (blue == high) & (green == low) & (ratio > .45) & (ratio < .66)
        yy, xx = np.indices(low.shape, dtype=np.float32)
        # A broad spatial phase creates islands of tertiary light, with a soft
        # transition that follows the existing texture rather than a hard seam.
        phase = np.sin(xx / max(1, view.shape[1]) * 6.283 + yy / max(1, view.shape[0]) * 3.1416)
        blend = np.clip((phase - .25) / .35, 0, 1) * violet
        # Keep original violet ahead of aqua even on near-balanced cards.
        aqua_count = index['palette']['balance_results'][card['id']]['violet_before']
        allowance = max(1, (int(violet.sum()) - aqua_count) // 2)
        selected = int((blend > 0).sum())
        if selected > allowance:
            threshold = np.partition(phase[violet], -allowance)[-allowance]
            blend *= phase >= threshold
        # Blend toward #6A51FF at the same local maximum. Input saturation is
        # retained as texture, scaled to the tertiary swatch's saturation.
        target_s = chroma * (174 / 255)
        target_low = high - target_s
        target = (target_low + target_s * (25 / 174), target_low, high)
        for channel in range(3):
            view[:, :, channel] = np.rint(rgb[:, :, channel] * (1 - blend) + target[channel] * blend).clip(0, 255).astype(np.uint8)
        counts[card['id']] = {'violet_pixels': int(violet.sum()), 'tertiary_pixels': int((blend > .5).sum())}
    Image.fromarray(pixels).save(path, format='PNG', optimize=True)
    digest = sha256(path.read_bytes()).hexdigest()
    index['files'][name] = digest
    if name in index.get('palette', {}).get('assets', {}):
        index['palette']['assets'][name]['sha256'] = digest
index['palette_revision'] = 3
index['palette']['tertiary'] = {'target': '#6A51FF', 'method': 'soft spatial modulation of violet only; aquamarine pixels unchanged', 'cards': counts}
index_path.write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')
print(f"Processed {len(counts)} cards; no tertiary pixels: {[k for k, v in counts.items() if not v['tertiary_pixels']]}")
