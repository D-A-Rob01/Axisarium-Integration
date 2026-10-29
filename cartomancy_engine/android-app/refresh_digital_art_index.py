"""Record the generated digital-edition artwork checksums and palette intent."""
from hashlib import sha256
import json
from pathlib import Path

root = Path(__file__).resolve().parent / 'app/src/main/assets/astrerium'
path = root / 'index.json'
index = json.loads(path.read_text(encoding='utf-8'))
index['files'] = {name: sha256((root / name).read_bytes()).hexdigest()
                  for name in index['files']}
index['edition'] = 'Astrerium — Digital Arcana'
index['generator'] = 'OpenAI built-in image generation; native identity typography'
index['palette_revision'] = 4
index['palette'] = {
    'primary_violet': '#8E00FF', 'secondary_aquamarine': '#00FFDA',
    'tertiary_blue_violet': '#6A51FF', 'tertiary_blue': '#19C4FF',
    'shadow': '#000B2B',
    'note': 'Art-directed target colors; generated imagery varies in local color and luminance.',
    'environment_sha256': sha256((root / 'environment.png').read_bytes()).hexdigest(),
}
path.write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')

# Update repeated edition-level visual descriptions while retaining each
# card's authored connections and the tradition-specific source contexts.
synthesis_path = root / 'synthesis-foundation.json'
content = synthesis_path.read_text(encoding='utf-8')
content = content.replace('One quiet elemental seal; the painted composition remains the primary sign.',
    'One quiet elemental seal; the digital composition remains the primary sign.')
content = content.replace('Continuous and interrupted edges echo the line vocabulary without turning the painting into a diagram.',
    'Continuous and interrupted edges echo the line vocabulary without turning the image into a diagram.')
content = content.replace('Saturated narrow light edges, small bloom and visible paint in shadow. Magenta accents mark tension; colors are not emission-line measurements.',
    'Narrow neon light edges and digital fragments emerge from deep blue shadow. Violet, aquamarine and blue are symbolic colors, not emission-line measurements.')
synthesis_path.write_text(content, encoding='utf-8')
