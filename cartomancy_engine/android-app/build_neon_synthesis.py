"""Author the explicitly labeled Kybernion lens, preserving v3 provenance."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'app/src/main/assets/astrerium'
SOURCE_CONTEXT={
 'alchemy': dict(title='Deck elemental vocabulary',url='',context='The bundled deck supplies the four-element association. The triangular seal is a design vocabulary; its relationship to this card is inherited deck metadata.'),
 'math': dict(title='Kybernion design specification',url='',context='Harmonic order, Gray-code register and orbit count are authored design data retained from the earlier sigil edition. They do not establish physical resonance or predictive power.'),
 'iching': dict(title='Minneapolis Institute of Art · Wearing the Cosmos',url='https://new.artsmia.org/hub/collection-exhibitions/symbolic-significance-daoist-priest-robes',context='The museum describes trigrams as three lines, continuous or broken, read from bottom to top. This source concerns Daoist robes; it does not assign trigrams to tarot cards.'),
 'chinese': dict(title='International Dunhuang Programme · Astrology and astronomy',url='https://idp.bl.uk/discover/learning/chinese-astronomy/articles/astrology-and-astronomy/',context='The IDP describes twelve animal years and the interacting stems-and-branches and five-phase cycles. Our phase assignment is an authored register, not a birth chart or a calendar calculation.'),
 'vedic': dict(title='The Met · Secrets of the Nine Luminaries',url='https://www.metmuseum.org/art/collection/search/45616',context='The Met identifies the Navagraha as the Sun, Moon, five visible planets and two lunar nodes, in a Japanese Buddhist scroll tracing the system to the Vedic tradition. Its context is not a tarot correspondence table.'),
 'yoruba': dict(title='UNESCO · Ifá divination system',url='https://ich.unesco.org/en/RL/ifa-divination-system-00146',context='UNESCO describes Ifá as a living Yorùbá corpus organized into 256 odù with poetic verses, transmitted by practitioners. Kybernion uses a methodological analogy to interpretation, not an odù assignment or a substitute for Ifá consultation. Source description verified through the indexed UNESCO record; the live page required a browser challenge.'),
 'norse': dict(title='National Museum of Denmark · Vikingernes vølver',url='https://natmus.dk/historisk-viden/danmark/oldtid-indtil-aar-1050/vikingetiden-800-1050/tro-og-magi-doed-og-ritual/vikingernes-voelver/',context='The museum describes the völva, staff, song and raised seat in accounts of seiðr. The design uses these as contextual motifs. Historical seiðr and diverse modern Ásatrú practices are not treated as one universal system.'),
 'spectral': dict(title='NASA · Visible Light',url='https://science.nasa.gov/ems/09_visiblelight/',context='Visible light is a range of electromagnetic wavelengths; spectra can distinguish physical sources. These RGB display colors and wave drawings are artistic metaphors, not measured spectral signatures, quantum states or a card frequency.'),
}
MAJOR_FORMS=[
 'an open path over a threshold','a focused intersection above four tools','a veil between opposing pillars',
 'growth around a receptive river','a seated center and bounded architecture','a shared axis between teacher and seekers',
 'two paths meeting without losing their origins','paired trajectories given a common direction','gentle contact with a powerful living form',
 'a small light and a deliberate climbing path','a turning rim with distinct orbit nodes','balanced planes and a vertical distinction',
 'an inverted viewpoint held in suspension','a relinquished crown and a surviving flower','two streams joining without losing their colors',
 'loose bonds with visible room for release','a fractured structure and an opening','two outflows beneath a modest guiding light',
 'a reflected path with phase-offset uncertainty','an illuminated rim and a returning horizon','a wave of response joining separate figures',
 'a complete ellipse containing a moving center']
RANK_FORMS={1:'one source becoming available',2:'two distinct forms in relation',3:'a three-part structure',4:'a bounded stable arrangement',5:'a pattern under strain',6:'a redistributed exchange',7:'a selective boundary',8:'an iterative sequence',9:'a developed field',10:'a complete pattern approaching transition',11:'a receptive seed',12:'a directed vector',13:'a sustaining field',14:'a governing architecture'}
SUITS={'wands':'branching ignition filaments','cups':'receptive bowls and continuous waves','swords':'sharp planes and discontinuities','pentacles':'stable nodes and cultivated lattices'}
PHASES={'wood':'branching potential','fire':'concentrated activity','earth':'a stabilizing center','metal':'separation and definition','water':'continuity and adaptation'}
LUMINARIES={'Sun':'direct attention','Moon':'reflected attention','Mercury':'exchange and articulation','Venus':'relation and attraction','Mars':'directed effort','Jupiter':'expanded perspective','Saturn':'limit and duration','ascending lunar node':'an emerging crossing','descending lunar node':'a releasing crossing'}
MAJOR_LUMINARIES=['ascending lunar node','Mercury','Moon','Venus','Saturn','Jupiter','Venus','Mars','Sun','Saturn','Jupiter','Saturn','descending lunar node','descending lunar node','Mercury','Mars','Mars','Venus','Moon','Sun','ascending lunar node','Jupiter']

def main():
    path=ASSETS/'synthesis-foundation.json'
    root=json.loads(path.read_text(encoding='utf-8'))
    deck=json.loads((ROOT.parent/'src/cartomancy_engine/data/decks/rider-waite-smith.json').read_text(encoding='utf-8'))['cards']
    by_id={c['id']:c for c in deck}
    for r in root['cards']:
        c=by_id[r['card_id']];n=c['number'];major=c['arcana']=='major'
        form=MAJOR_FORMS[n] if major else f"{RANK_FORMS[n]}, expressed through {SUITS[c['suit']]}"
        focus=r['intent'];phase=r['phase'];trigram=r['trigram'];element=r['element']
        luminary=MAJOR_LUMINARIES[n] if major else {'wands':'Mars','cups':'Moon','swords':'Mercury','pentacles':'Saturn'}[c['suit']]
        r['classification']='Kybernion synthesis — authored contemplative design'
        r['visual_grammar']=form
        r['legacy_spectral_colors']=r.get('legacy_spectral_colors',r['spectral_colors'])
        r['spectral_colors']=['#53E6FF','#A985FF']
        r['extension_status']='Authored lenses populated; tradition context, connection and visual translation kept separate'
        r['layers']=[
          dict(id='alchemy',title='Alchemy · '+element,connection=f"The inherited {element} association gives ‘{focus}’ an elemental lens. The triangular corner seal identifies that lens while {form} carries the narrative.",visual='One quiet elemental seal; the painted composition remains the primary sign.'),
          dict(id='math',title='Mathematical structure',connection=f"Read ‘{focus}’ through {form}. The earlier harmonic order {r['harmonic']}, orbit count {r['orbit_count']} and Gray-code register are retained as inspectable design coordinates, not hidden claims about nature.",visual='Thin optical planes, paired waves and interval spacing distinguish relations; the numeric register stays in this inspection layer.'),
          dict(id='iching',title='I Ching · '+trigram+' register',connection=f"The inherited {trigram} trigram is a secondary register for ‘{focus}’. Consider which part of {form} feels continuous and which feels interrupted. This juxtaposition is authored by Kybernion; no hexagram was cast.",visual='Continuous and interrupted edges echo the line vocabulary without turning the painting into a diagram.'),
          dict(id='chinese',title='Chinese cycles · '+phase+' register',connection=f"The inherited {phase} phase is read here as {PHASES[phase]}. Ask when ‘{focus}’ is timely within a larger cycle, rather than assigning this card a personal zodiac sign.",visual=f"The cyclic reading attends to the changing boundary in {form}. Phase names remain available here rather than becoming decorative animal badges."),
          dict(id='vedic',title='Vedic-derived luminary lens · '+luminary,connection=f"Kybernion pairs {luminary} with {LUMINARIES[luminary]} as an authored metaphor for ‘{focus}’. This is a design analogy to the luminary vocabulary, not a Jyotiṣa judgment or a traditional tarot equivalence.",visual=f"Locate the source, reflection or crossing of light within {form}; no deity portrait is substituted for the card."),
          dict(id='yoruba',title='Yorùbá / Ifá · narrative lens',connection=f"For {c['name']}, the connection is methodological: let ‘{focus}’ open a situated account rather than settle it. What lived story complicates the first reading of {form}? No odù or òrìṣà is assigned.",visual='Repeated traces invite revisiting an interpretation. Your Notice, Relate and Revisit entries preserve the developing account.'),
          dict(id='norse',title='Norse · seiðr context',connection=f"The staff, song and raised viewpoint offer a contextual comparison for ‘{focus}’: where could a change in vantage alter the meaning of {form}? This is a modern authored reading, not a ritual instruction.",visual='A quiet axis, a wave trace or a shift of plane suggests vantage and attention; no invented rune is presented as traditional.'),
          dict(id='spectral',title='Spectral and wavelength metaphor',connection=f"Cyan and violet hold two distinguishable perspectives around ‘{focus}’. Their crossing in {form} is an optical analogy for relation, not proof that the interpretations are physically superposed.",visual='Saturated narrow light edges, small bloom and visible paint in shadow. Magenta accents mark tension; colors are not emission-line measurements.'),
        ]
    root.update(schema=2,status='authored-release',edition='Astrerium Neon Cyberspace 0.5.0',sources=SOURCE_CONTEXT)
    assert len(root['cards'])==78 and all(len(r['layers'])==8 for r in root['cards'])
    path.write_text(json.dumps(root,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('78 complete authored records; eight separately attributed lenses per card.')
if __name__=='__main__':main()
