"""Import 78 original RWS files and per-file Commons rights metadata.

Run from any directory: python3 scripts/import_commons.py
Requires network access to commons.wikimedia.org and upload.wikimedia.org.
Does not replace existing assets until ALL 78 files and rights pass validation.
"""
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
API = 'https://commons.wikimedia.org/w/api.php'
MAJORS = ['Fool','Magician','High Priestess','Empress','Emperor','Hierophant',
          'Lovers','Chariot','Strength','Hermit','Wheel of Fortune','Justice',
          'Hanged Man','Death','Temperance','Devil','Tower','Star','Moon','Sun',
          'Judgement','World']


def targets():
    items = [{'id': f'major-{i}', 'file_title': f'File:RWS Tarot {i:02d} {name}.jpg'}
             for i, name in enumerate(MAJORS)]
    for suit, prefix in enumerate(['Wands', 'Cups', 'Swords', 'Pents']):
        items.extend({'id': f'minor-{suit}-{i}', 'file_title': f'File:{prefix}{i+1:02d}.jpg'}
                     for i in range(14))
    return items


def plain(value):
    return unescape(re.sub(r'<[^>]+>', '', value)).strip()


def https_url(value, allowed_host):
    url = urllib.parse.urlsplit(value)
    if url.scheme != 'https' or url.hostname != allowed_host or url.username or url.password:
        raise ValueError(f'Unexpected source URL host: {url.hostname}')
    return value


def request(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'MoonlitTarot/1.0 (RWS attribution importer)'})
    with urllib.request.urlopen(req, timeout=45) as response:
        # Keep all requests on authoritative Commons/image hosts, including redirects.
        host = urllib.parse.urlsplit(response.url).hostname
        if host not in ['commons.wikimedia.org', 'upload.wikimedia.org']:
            raise ValueError(f'Unexpected redirect host: {host}')
        return response.read()


def api(params):
    return json.loads(request(API + '?' + urllib.parse.urlencode({
        'format': 'json', 'formatversion': 2, **params})))


def lookup(items):
    result = {}
    for start in range(0, len(items), 20):
        batch = items[start:start+20]
        response = api({'action': 'query', 'titles': '|'.join(x['file_title'] for x in batch),
                        'redirects': 1, 'prop': 'imageinfo',
                        'iiprop': 'url|timestamp|sha1|size|mime|extmetadata'})
        if 'error' in response:
            raise ValueError(str(response['error']))
        query = response['query']
        aliases = {x['from']: x['to'] for x in query.get('normalized', []) + query.get('redirects', [])}
        pages = {x['title']: x for x in query['pages']}
        for item in batch:
            title = item['file_title']
            seen = set()
            while title in aliases:
                if title in seen:
                    raise ValueError('Circular Commons redirect')
                seen.add(title)
                title = aliases[title]
            page = pages.get(title)
            if not page or page.get('missing') or not page.get('imageinfo'):
                raise ValueError(f'Missing Commons file; resolve its exact title before importing: {title}')
            result[item['id']] = page
    return result


def record(item, page, checked_at):
    info = page['imageinfo'][0]
    meta = info.get('extmetadata', {})
    value = lambda name: plain(meta.get(name, {}).get('value', ''))
    rights = value('LicenseShortName')
    # This importer is intentionally limited to original public-domain RWS scans.
    # Never infer public-domain status just from deck name or publication year.
    if rights.casefold() not in ['public domain', 'pd'] or value('Copyrighted').casefold() != 'false':
        raise ValueError(f'{page["title"]}: public-domain rights not confirmed: {rights}')
    author = value('Artist')
    if not author:
        raise ValueError(f'{page["title"]}: artist metadata missing; requires manual review')
    if info.get('mime') != 'image/jpeg':
        raise ValueError(f'{page["title"]}: expected a JPEG original')
    source_page = https_url(info['descriptionurl'], 'commons.wikimedia.org')
    image_url = https_url(info['url'], 'upload.wikimedia.org')
    return {
        'id': item['id'], 'provider': 'Wikimedia Commons',
        'file_title': page['title'], 'commons_page_id': page['pageid'],
        'source_page': source_page, 'original_image_url': image_url,
        'artist': author, 'credit': value('Credit'),
        'rights_label': rights, 'rights_url': value('LicenseUrl'),
        'usage_terms': value('UsageTerms'), 'copyrighted': value('Copyrighted'),
        'attribution_required': value('AttributionRequired'),
        'restrictions': value('Restrictions'), 'permission': value('Permission'),
        'file_timestamp': info['timestamp'], 'commons_sha1': info['sha1'],
        'checked_at_utc': checked_at,
        'local_file': f'assets/cards/{item["id"]}.jpg',
        'extmetadata': meta,
    }


def verify_image(content, expected_sha1):
    if not content.startswith(b'\xff\xd8'):
        raise ValueError('Downloaded asset is not a JPEG')
    actual = hashlib.sha1(content).hexdigest()
    # MediaWiki versions expose SHA-1 as either 40-digit hex or base 36.
    expected = (expected_sha1.lower() if re.fullmatch(r'[a-fA-F0-9]{40}', expected_sha1)
                else f'{int(expected_sha1, 36):040x}')
    if actual != expected:
        raise ValueError('Commons original file checksum mismatch')
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Check all metadata without downloading or replacing images')
    args = parser.parse_args()
    items = targets()
    pages = lookup(items)
    now = datetime.now(timezone.utc).isoformat()
    records = [record(item, pages[item['id']], now) for item in items]
    if len(records) != 78 or len({x['commons_page_id'] for x in records}) != 78:
        raise ValueError('Expected 78 distinct Commons files')
    if args.check_only:
        print('All 78 per-file rights records retrieved; images have not been replaced.')
        return
    with tempfile.TemporaryDirectory(prefix='commons-rws-') as folder:
        staging = Path(folder)
        for entry in records:
            content = request(entry['original_image_url'])
            entry['verified_local_sha1'] = verify_image(content, entry['commons_sha1'])
            entry['verified_local_sha256'] = hashlib.sha256(content).hexdigest()
            (staging / f'{entry["id"]}.jpg').write_bytes(content)
            print(f'Verified {entry["id"]}: {entry["file_title"]}')
        manifest = {'provider': 'Wikimedia Commons', 'deck': 'Original Rider-Waite-Smith',
                    'checked_at_utc': now, 'cards': records}
        (staging / 'commons-attribution.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        lines = ['# Wikimedia Commons — 78-card attribution register', '',
                 'Original Rider–Waite–Smith artwork. This is not the Universal Waite recoloring.',
                 f'Individual file metadata checked: {now}. Raw extmetadata is retained in commons-attribution.json.', '']
        for entry in records:
            lines.extend([f'## {entry["id"]} — {entry["file_title"]}',
                          f'- Source: {entry["source_page"]}', f'- Original: {entry["original_image_url"]}',
                          f'- Artist: {entry["artist"]}', f'- Rights: {entry["rights_label"]}',
                          f'- Rights URL: {entry["rights_url"] or "No separate URL returned; see original file page"}',
                          f'- Credit: {entry["credit"]}', f'- Usage terms: {entry["usage_terms"]}',
                          f'- Attribution required: {entry["attribution_required"]}',
                          f'- Restrictions: {entry["restrictions"]}',
                          f'- SHA-256: {entry["verified_local_sha256"]}', ''])
        (staging / 'COMMONS_ATTRIBUTION.md').write_text('\n'.join(lines))
        target = ROOT / 'assets/cards'
        # Preserve the previous deck outside the published assets before replacing it.
        backup = ROOT / 'dist' / ('pre-commons-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target, backup)
        try:
            for path in staging.iterdir():
                fd, temporary = tempfile.mkstemp(prefix='.commons-', dir=target)
                os.close(fd)
                shutil.copyfile(path, temporary)
                os.replace(temporary, target / path.name)
        except Exception:
            for previous in backup.iterdir():
                if previous.is_file(): shutil.copy2(previous, target / previous.name)
            for name in ['commons-attribution.json', 'COMMONS_ATTRIBUTION.md']:
                if not (backup/name).exists(): (target/name).unlink(missing_ok=True)
            raise
        print('Imported 78 verified Commons originals and their attribution register.')
        print('Next: rebuild the site, test it, and publish gh-pages.')


if __name__ == '__main__':
    main()
