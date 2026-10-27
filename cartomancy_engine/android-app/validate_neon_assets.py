"""Release integrity checks using only the Python standard library."""
import hashlib
import json
import struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'app/src/main/assets/astrerium'
index=json.loads((ASSETS/'index.json').read_text())
deck=json.loads((ROOT.parent/'src/cartomancy_engine/data/decks/rider-waite-smith.json').read_text())['cards']
synthesis=json.loads((ASSETS/'synthesis-foundation.json').read_text(encoding='utf-8'))
ids={c['id'] for c in deck}
assert len(ids)==len(index['cards'])==78
assert {c['id'] for c in index['cards']}==ids
assert len({(c['file'],c['column'],c['row']) for c in index['cards']})==78
assert {r['card_id'] for r in synthesis['cards']}==ids
assert len(synthesis['cards'])==78 and synthesis['status']=='authored-release'
sources=synthesis['sources']
for c in index['cards']:
    assert c['file'].startswith('neon-') and '/' not in c['file']
    assert 0<=c['left']<c['right']<=1 and 0<=c['top']<c['bottom']<=1
for name,sha in index['files'].items():
    data=(ASSETS/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==sha,name
    assert data[:8]==b'\x89PNG\r\n\x1a\n',name
    w,h=struct.unpack('>II',data[16:24])
    assert w>=900 and h>=1500,(name,w,h)
for r in synthesis['cards']:
    assert len(r['layers'])==8 and {x['id'] for x in r['layers']}==set(sources)
    for layer in r['layers']:
        assert layer['connection'].strip() and layer['visual'].strip()
    assert r['legacy_spectral_colors'] and r['spectral_colors']
assert {c['file'] for c in index['cards'] if c['id'].startswith(('major_07','major_14','major_18'))}=={'neon-the-chariot.png','neon-temperance.png','neon-the-moon.png'}
print('PASS: 78 unique neon paintings; bounds, PNGs, hashes, approved studies and 624 attributed synthesis lenses.')
