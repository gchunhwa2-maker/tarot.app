"""Local validation only; these fixtures are NOT live Commons rights verification."""
import hashlib
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('commons',Path(__file__).resolve().parents[1]/'scripts/import_commons.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class CommonsValidation(unittest.TestCase):
 def test_mapping(self):
  cards=module.targets();self.assertEqual(len(cards),78);self.assertEqual(len({x['id'] for x in cards}),78)
  self.assertEqual(cards[22]['file_title'],'File:Wands01.jpg')
 def test_checksum(self):
  content=b'\xff\xd8test-fixture';sha=hashlib.sha1(content).hexdigest()
  self.assertEqual(module.verify_image(content,sha),sha)
  with self.assertRaises(ValueError):module.verify_image(content,'0'*40)
  with self.assertRaises(ValueError):module.verify_image(b'error page',sha)
 def test_rights(self):
  info={'extmetadata':{'LicenseShortName':{'value':'Public domain'},'Copyrighted':{'value':'False'},'Artist':{'value':'<b>Fixture author</b>'}},'mime':'image/jpeg','descriptionurl':'https://commons.wikimedia.org/wiki/File:Fixture.jpg','url':'https://upload.wikimedia.org/fixture.jpg','timestamp':'2026-01-01T00:00:00Z','sha1':'0'*40}
  page={'title':'File:Fixture.jpg','pageid':1,'imageinfo':[info]}
  self.assertEqual(module.record({'id':'major-0'},page,'2026-01-01')['artist'],'Fixture author')
  info['extmetadata']['LicenseShortName']['value']='Unknown'
  with self.assertRaises(ValueError):module.record({'id':'major-0'},page,'2026-01-01')
 def test_no_untrusted_hosts(self):
  for url in ['http://commons.wikimedia.org/a','https://example.org/a','https://name@commons.wikimedia.org/a']:
   with self.assertRaises(ValueError):module.https_url(url,'commons.wikimedia.org')
if __name__=='__main__':unittest.main()
