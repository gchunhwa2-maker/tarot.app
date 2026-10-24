// Tests the packaged assets, not a device/emulator installation.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve('dist/android-web');
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.json':'application/json','.webmanifest':'application/manifest+json'};
const server=createServer(async(req,res)=>{try{const path=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(path!==root&&!path.startsWith(root+'/'))throw Error('invalid path');const file=path===root?resolve(root,'index.html'):path;res.setHeader('Content-Type',mime[extname(file)]||'application/octet-stream');res.end(await readFile(file));}catch{res.writeHead(404);res.end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try{
 browser=await chromium.launch({...(process.env.MOONLIT_BROWSER_PATH?{executablePath:process.env.MOONLIT_BROWSER_PATH}:{}),args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 const page=await context.newPage(),errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));
 const origin=`http://127.0.0.1:${server.address().port}`;
 await page.route('**/*',route=>{if(!route.request().url().startsWith(origin)){external.push(route.request().url());return route.abort();}return route.continue();});
 await page.goto(origin+'/');
 assert.equal(await page.locator('meta[name=moonlit-runtime]').getAttribute('content'),'android');
 assert.equal(await page.evaluate(async()=>(await navigator.serviceWorker.getRegistrations()).length),0);
 for(const [spread,count] of [['single',1],['three',3],['four',4],['comparison',7],['timeline',6],['celtic',10]]){
  await page.click(`[data-spread="${spread}"]`);await page.click('#shuffle');await page.waitForFunction(()=>!document.querySelector('#shuffle').disabled);await page.click('#draw');
  assert.equal(await page.locator('#spread-board .slot').count(),count);
  await page.waitForFunction(()=>[...document.querySelectorAll('#spread-board img')].every(i=>i.complete&&i.naturalWidth>0));
  assert.equal(new Set(await page.locator('#spread-board strong').allTextContents()).size,count);
 }
 await page.reload();await page.click('[data-page=history]');assert.equal(await page.locator('.history-entry').count(),6);
 await page.locator('.history-entry').first().click();assert.equal(await page.locator('#spread-board .slot').count(),10);
 await page.click('[data-page=library]');assert.equal(await page.locator('#library-list details').count(),78);
 await page.click('[data-page=history]');await page.click('#clear');await page.reload();await page.click('[data-page=history]');assert.equal(await page.locator('.history-entry').count(),0);
 await page.goto(origin+'/privacy.html');assert.ok(await page.locator('h1').isVisible());
 assert.deepEqual(external,[]);assert.deepEqual(errors,[]);
 console.log('PASS: packaged Android web assets, six spreads, 78 image cards, persistent/clearable history, privacy page, no remote requests, no service worker. Actual Android device testing is still required.');
}finally{await browser?.close();await new Promise(resolve=>server.close(resolve));}
