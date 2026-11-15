// Records the demo's result pages as a screen video (Playwright, headless Chromium): TODAY.html, the review pack, the
// one-page resume and the tracker. Local files only: every request that is not file: or data: is blocked. Writes a WebM
// that tools/record_demo.sh converts to MP4 with ffmpeg.
// usage: node tools/record_demo.mjs <demo state dir> <out.webm>
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const [demo, outFile] = process.argv.slice(2);
if (!demo || !outFile) { console.error('usage: node tools/record_demo.mjs <demo dir> <out.webm>'); process.exit(2); }
const today = path.resolve(demo, 'TODAY.html');
if (!fs.existsSync(today)) { console.error(`no ${today}: run /demo first`); process.exit(1); }
const packs = fs.readdirSync(path.join(demo, 'out')).filter((d) => fs.existsSync(path.join(demo, 'out', d, 'gate.json')));
const pack = packs.find((d) => fs.existsSync(path.join(demo, 'out', d, 'resume.html')));

const W = 1280, H = 720;
const tmp = fs.mkdtempSync(path.join(path.dirname(path.resolve(outFile)), '.rec-'));
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1, recordVideo: { dir: tmp, size: { width: W, height: H } } });
await ctx.route('**/*', (r) => (/^(file|data):/.test(r.request().url()) ? r.continue() : r.abort()));
const page = await ctx.newPage();
const wait = (ms) => page.waitForTimeout(ms);
const t0 = Date.now();

// A caption bar drawn on top of the page, so the video explains itself with the sound off.
async function caption(text) {
  await page.evaluate((t) => {
    let c = document.getElementById('__cap');
    if (!c) {
      c = document.createElement('div'); c.id = '__cap';
      c.style.cssText = 'position:fixed;left:24px;bottom:24px;z-index:99999;max-width:900px;padding:14px 22px;border-radius:12px;'
        + 'background:rgba(13,21,34,.92);color:#f4ecdc;font:600 22px/1.35 "Avenir Next",Avenir,"Segoe UI",sans-serif;'
        + 'box-shadow:0 10px 40px rgba(0,0,0,.35);border-left:6px solid #ffb547;transition:opacity .3s';
      document.body.appendChild(c);
    }
    if (t) c.textContent = t;            // an empty caption only fades out, so no empty bar is ever shown
    c.style.opacity = t ? '1' : '0';
  }, text);
}
// Smooth scroll to the element (or by a distance), at a reading pace.
async function glide(target, ms = 4000) {
  const y = typeof target === 'number' ? target
    : await page.evaluate((sel) => { const e = document.querySelector(sel); return e ? e.getBoundingClientRect().top + scrollY - 90 : scrollY; }, target);
  await page.evaluate(([to, dur]) => new Promise((done) => {
    const from = scrollY, start = performance.now();
    const step = (now) => { const k = Math.min(1, (now - start) / dur); scrollTo(0, from + (to - from) * (1 - Math.pow(1 - k, 3))); k < 1 ? requestAnimationFrame(step) : done(); };
    requestAnimationFrame(step);
  }), [y, ms]);
}

// 1. TODAY.html: the one page the student reads each morning (about 40 s)
await page.goto('file://' + today); await wait(600);
await caption('TODAY.html: everything the crew prepared overnight, for a made-up sample student'); await wait(5500);
await glide('h2', 2500);
const hasHold = await page.evaluate(() => [...document.querySelectorAll('h2')].some((h) => /HOLD/.test(h.textContent)));
if (hasHold) { await caption('A HOLD: the crew asks before it builds anything that might break your rules'); await wait(6000); }
// The review pack is the first section.pack after the "Applications to review" heading (a HOLD card is a section.pack
// too). Its collapsed parts (field log, filled-from-profile) are opened on this local page so the video can show them.
const yOf = (finder) => page.evaluate((f) => {
  const h = [...document.querySelectorAll('h2')].find((x) => /Applications to review/.test(x.textContent));
  let pack = h && h.nextElementSibling;
  while (pack && !pack.matches('section.pack')) pack = pack.nextElementSibling;
  if (!pack) return null;
  pack.querySelectorAll('details').forEach((d) => { d.open = true; });
  const el = f === 'pack' ? pack : f === 'acts' ? pack.querySelector('.acts')
    : [...pack.querySelectorAll('summary')].find((s) => new RegExp(f).test(s.textContent));
  return el ? el.getBoundingClientRect().top + scrollY - (f === 'acts' ? 420 : 90) : null;
}, finder);
const go = async (finder, ms) => { const y = await yOf(finder); if (y !== null) await glide(y, ms); return y !== null; };
if (await go('pack', 3000)) {
  await caption('A review pack: the screener\'s reasons, then a short company brief from the posting and the company\'s own site'); await wait(6500);
  await go('Soft flags', 4000);
  await caption('Soft flags: anything you should know before you approve'); await wait(5500);
  await go('Field log', 3500);
  await caption('The field log: every form field and where its value came from'); await wait(5500);
  await go('acts', 2500);
  await caption('Approve or Skip. Nothing is submitted or sent until you approve that exact id'); await wait(5500);
} else {
  await caption('No review pack in this run: the screener kept nothing it was not sure of'); await wait(8000);
}

// 2. The one-page resume built for this role (about 15 s)
if (pack) {
  await caption('');
  await page.goto('file://' + path.resolve(demo, 'out', pack, 'resume.html')); await wait(500);
  await caption('The one-page resume for this role: every number and name comes from the student\'s own facts'); await wait(6000);
  await glide(260, 4000); await wait(3500);
}

// 3. The tracker (about 10 s)
const tracker = path.resolve(demo, 'tracker.html');
if (fs.existsSync(tracker)) {
  await caption('');
  await page.goto('file://' + tracker); await wait(500);
  await caption('The tracker: every role and what happened to it'); await wait(6500);
}

// 4. Back to the top of TODAY.html, to close (about 6 s)
await page.goto('file://' + today); await wait(400);
await caption('Run /demo yourself: five minutes, nothing sent. github.com/dudailia/coop-crew'); await wait(6000);

const secs = (Date.now() - t0) / 1000;
const video = page.video();
await ctx.close(); await browser.close();
fs.renameSync(await video.path(), outFile);
fs.rmSync(tmp, { recursive: true, force: true });
console.log(`recorded ${secs.toFixed(1)} s -> ${outFile}${pack ? ` (pack ${pack})` : ' (no review pack found)'}`);
