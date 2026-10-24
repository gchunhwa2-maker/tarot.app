"""Build a static HTTPS hosting bundle. No accounts or credentials are included."""
from pathlib import Path
import json, shutil, zipfile
root=Path(__file__).resolve().parents[1]
files=['index.html','manifest.webmanifest','src/app.js','src/deck.js','src/style.css']
files += [str(p.relative_to(root)) for p in (root/'assets').rglob('*') if p.is_file()]
# Cache same-origin application assets for use after the first online visit.
worker='''const CACHE='moonlit-site-v3-label';
const FILES=__FILES__;
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(FILES)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('moonlit-site-')&&key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET'||new URL(event.request.url).origin!==self.location.origin)return;
 if(event.request.mode==='navigate'){event.respondWith(fetch(event.request).catch(()=>caches.match('./index.html')));return;}
 event.respondWith(caches.match(event.request).then(cached=>cached||fetch(event.request)));});
'''.replace('__FILES__',json.dumps(['./'+f for f in files]))
(root/'sw.js').write_text(worker)
files.append('sw.js')
site=root/'dist/site'
if site.exists(): shutil.rmtree(site)
site.mkdir(parents=True)
for name in files:
 target=site/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
# Only embed attribution after the 78 Commons originals have been verified.
manifest=root/'assets/cards/commons-attribution.json'
if manifest.exists():
 records=json.loads(manifest.read_text())['cards']
 if len(records)!=78 or len({r['id'] for r in records})!=78 or not all(r.get('verified_local_sha256') for r in records):
  raise ValueError('Incomplete Commons attribution; refuse to publish')
 app=site/'src/app.js'
 app.write_text(app.read_text().replace('const cardAttribution={};','const cardAttribution='+json.dumps({r['id']:r for r in records},ensure_ascii=False)+';'))
archive=root/'dist/moonlit-iphone-site.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(site/name,name)
print(archive,archive.stat().st_size,'bytes')
