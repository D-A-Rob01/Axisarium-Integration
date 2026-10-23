"""Index the original generated atlases without altering image pixels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'app/src/main/assets/astrerium'
DECK = ROOT.parent / 'src/cartomancy_engine/data/decks/rider-waite-smith.json'
# Visually inspected tile seams, expressed in the 972 x 1620 preview coordinate space.
# Generated atlases are not assumed to divide into mathematically equal thirds.
SEAMS = {
    'major-0.png': ([0, 325, 647, 972], [0, 539, 1079, 1620]),
    'major-1.png': ([0, 328, 647, 972], [0, 539, 1079, 1620]),
    'major-2.png': ([0, 323, 647, 972], [0, 501, 1019, 1620]),
    'wands.png': ([0, 335, 637, 972], [0, 540, 1079, 1620]),
    'cups.png': ([0, 333, 646, 972], [0, 539, 1079, 1620]),
    'swords.png': ([0, 323, 647, 972], [0, 539, 1072, 1620]),
    'pentacles.png': ([0, 322, 649, 972], [0, 500, 1010, 1620]),
    'courts-0.png': ([0, 322, 650, 972], [0, 532, 1050, 1620]),
    'courts-1.png': ([0, 312, 629, 972], [0, 539, 1079, 1620]),
}

def location(card):
    n, suit = card['number'], card['suit']
    if card['arcana'] == 'major':
        return f'major-{n // 9}.png', n % 9
    suits = ['wands', 'cups', 'swords', 'pentacles']
    if n == 1:
        return 'major-2.png', 4 + suits.index(suit)
    if n <= 10:
        return f'{suit}.png', n - 2
    group = suits.index(suit)
    return f'courts-{group // 2}.png', (group % 2) * 4 + n - 11

def main():
    cards = json.loads(DECK.read_text(encoding='utf-8'))['cards']
    entries = []
    hashes = {}
    for card in cards:
        filename, tile = location(card)
        path = ASSETS / filename
        if not path.is_file():
            raise SystemExit(f'Missing production artwork: {filename}')
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        xs, ys = SEAMS[filename]
        col, row = tile % 3, tile // 3
        entries.append(dict(id=card['id'], file=filename, column=col, row=row,
                            left=(xs[col]+1)/972, top=(ys[row]+1)/1620,
                            right=(xs[col+1]-1)/972, bottom=(ys[row+1]-1)/1620))
    assert len(entries) == len({c['id'] for c in entries}) == 78
    assert len({(c['file'], c['column'], c['row']) for c in entries}) == 78
    result = dict(schema_version=1, edition='Astrerium', columns=3, rows=3,
                  generator='OpenAI built-in image generation', files=hashes, cards=entries)
    (ASSETS / 'index.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(f'Indexed {len(entries)} distinct card cells across {len(hashes)} verified files.')

if __name__ == '__main__':
    main()
