"""Package locally bundled app assets; no remote website is used by Android."""
from pathlib import Path
import json
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
subprocess.run(['python3',str(ROOT/'scripts/package_site.py')],cwd=ROOT,check=True)
source=ROOT/'dist/site'
target=ROOT/'dist/android-web'
if target.exists():shutil.rmtree(target)
shutil.copytree(source,target)
html=(target/'index.html').read_text()
html=html.replace('<head>','<head><meta name="moonlit-runtime" content="android">',1)
html=html.replace('이 브라우저에만 저장됩니다.','이 기기에만 저장됩니다.')
html=html.replace('</footer>','<p><a href="./privacy.html">개인정보 안내</a></p></footer>')
shutil.copy2(ROOT/'privacy.html',target/'privacy.html')
# No PWA worker in the native app; installed assets update with the APK/AAB.
(target/'sw.js').unlink(missing_ok=True)
(target/'index.html').write_text(html)
print('Android assets:',target,'— all 78 card images included')
