"""Export a self-contained offline app, including all 78 card images."""
from pathlib import Path
import base64
import json
import re
root = Path(__file__).resolve().parents[1]
html = (root / 'index.html').read_text()
css = (root / 'src/style.css').read_text()
deck = (root / 'src/deck.js').read_text().replace('export const ', 'const ').replace('export function ', 'function ')
app = (root / 'src/app.js').read_text().split('\n', 1)[1]
def data_url(path, mime):
    return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
images = {p.stem: data_url(p, 'image/jpeg') for p in sorted((root / 'assets/cards').glob('*.jpg'))}
assert len(images) == 78, 'All 78 card images are required'
app = app.replace('const bundledImages={};', 'const bundledImages=' + json.dumps(images) + ';')
manifest = root / 'assets/cards/commons-attribution.json'
if manifest.exists():
    records = json.loads(manifest.read_text())['cards']
    assert len(records) == 78 and all(r.get('verified_local_sha256') for r in records)
    app = app.replace('const cardAttribution={};', 'const cardAttribution=' + json.dumps({r['id']: r for r in records}, ensure_ascii=False) + ';')
html = re.sub(r'src="(assets/spreads/[^"]+\.svg)"', lambda m: 'src="' + data_url(root / m[1], 'image/svg+xml') + '"', html)
html = html.replace('<link rel="stylesheet" href="./src/style.css">', '<style>' + css + '</style>')
html = html.replace('<script type="module" src="./src/app.js"></script>', '<script type="module">' + deck + '\n' + app + '</script>')
output = root / 'dist/moonlit-tarot.html'
output.parent.mkdir(exist_ok=True)
output.write_text(html)
print(output, output.stat().st_size, 'bytes; 78 embedded card images')
