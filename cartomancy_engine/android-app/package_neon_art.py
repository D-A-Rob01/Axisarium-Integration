"""Package original generated pixels and rebuild their display-bound index."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'app/src/main/assets/astrerium'
GENERATED = Path.home() / '.codex/generated_images/01a15fcd-c391-7c22-8164-dd90b4742f1f'
STUDIES = ROOT.parents[3] / 'sibyllic-concept/neon-cyberspace-studies'
SOURCES = {
 'major-0': 'bf6ba43f-90e7-44b6-ac10-f5f59e366b16',
 'major-1': 'b5fe2c33-f8de-48d8-8abe-401d67edc2b3',
 'major-2': '736221f8-ce34-49e6-bcdb-f2523ad97f87',
 'wands': '0815f9fc-01b8-4d9c-8708-4289084e280b',
 'cups': 'd48b559d-e1cb-4c18-9aed-5ff9419ec291',
 'swords': 'd329cd31-f0b1-4528-b31c-f43ca4168947',
 'pentacles': 'a6d34192-6d55-44b5-a8a4-fd46d7a7ce4e',
 'courts-0': 'b71add82-5e60-4163-bae3-dc8adf5f529f',
 'courts-1': 'c16c7bb5-6c4a-48d9-adfa-961c831f9a55',
 'corrections': 'dffa331f-9db3-4c91-9fda-39abc0641051',
 'ten-swords': 'e51262e2-650a-49fc-97c8-0652956c577f',
}
# Measured seams in the 971x1619 rendered previews; rows are not assumed equal.
SEAMS = {
 'major-0': ([0,324,647,971], [0,540,1080,1619]),
 'major-1': ([0,326,649,971], [0,535,1049,1619]),
 'major-2': ([0,324,647,971], [0,540,1080,1619]),
 'wands': ([0,324,647,971], [0,540,1080,1619]),
 'cups': ([0,324,647,971], [0,539,1075,1619]),
 'swords': ([0,324,647,971], [0,537,1076,1619]),
 'pentacles': ([0,324,647,971], [0,540,1078,1619]),
 'courts-0': ([0,324,647,971], [0,539,1078,1619]),
 'courts-1': ([0,324,647,971], [0,539,1078,1619]),
 'corrections': ([0,324,647,971], [0,501,1019,1619]),
}

def location(card):
    n,suit = card['number'],card['suit']
    if card['arcana']=='major':
        if n in [7,14,18]:
            return {7:'the-chariot',14:'temperance',18:'the-moon'}[n],0,True
        return f'major-{n//9}',n%9,False
    fixed={('wands',6):0,('cups',10):1,('swords',9):2,('pentacles',9):4,('pentacles',10):5}
    if (suit,n) in fixed:
        return 'corrections',fixed[(suit,n)],False
    if suit=='swords' and n==10:
        return 'ten-swords',0,True
    suits=['wands','cups','swords','pentacles']
    if n==1:
        return 'major-2',4+suits.index(suit),False
    if n<=10:
        return suit,n-2,False
    group=suits.index(suit)
    return f'courts-{group//2}',(group%2)*4+n-11,False

def rebuild_index():
    deck=json.loads((ROOT.parent/'src/cartomancy_engine/data/decks/rider-waite-smith.json').read_text(encoding='utf-8'))['cards']
    entries,hashes=[],{}
    for card in deck:
        name,tile,single=location(card)
        filename=f'neon-{name}.png'
        hashes[filename]=hashlib.sha256((ASSETS/filename).read_bytes()).hexdigest()
        col,row=tile%3,tile//3
        if single:
            # Approved study title bands are excluded only at display time.
            bounds=(.025,.02,.975,.85 if name!='ten-swords' else .98)
        else:
            xs,ys=SEAMS[name]
            bounds=((xs[col]+3)/971,(ys[row]+3)/1619,(xs[col+1]-3)/971,(ys[row+1]-3)/1619)
        entries.append(dict(id=card['id'],file=filename,column=col,row=row,
            **dict(zip(['left','top','right','bottom'],bounds))))
    assert len(entries)==len({c['id'] for c in entries})==78
    assert len({(c['file'],c['column'],c['row']) for c in entries})==78
    result=dict(schema_version=2,edition='Astrerium — Neon Cyberspace',columns=3,rows=3,
        generator='OpenAI built-in image generation; native identity typography',files=hashes,cards=entries)
    (ASSETS/'index.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'Indexed {len(entries)} distinct new paintings across {len(hashes)} verified files.')

if __name__=='__main__':
    import sys
    if '--copy-originals' in sys.argv:
        for name,source in SOURCES.items():
            shutil.copyfile(GENERATED/f'exec-{source}.png',ASSETS/f'neon-{name}.png')
        for name in ['the-moon','temperance','the-chariot']:
            shutil.copyfile(STUDIES/f'{name}.png',ASSETS/f'neon-{name}.png')
        shutil.copyfile(GENERATED/'exec-589e21a8-fc1e-4b53-8cc7-6c56dcaf92dc.png',ASSETS/'environment.png')
    rebuild_index()
