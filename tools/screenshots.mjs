// Screenshots for the README and the talk deck, from a finished demo state (use the offline demo, so only the made-up
// companies in templates/demo-cache appear): docs/img/{today,resume,tracker}.png and docs/talk/img/{today,resume}-deck.jpg.
// Local files only: every request that is not file: or data: is blocked.
// usage: python3 -I tools/demo.py run --offline --no-open && node tools/screenshots.mjs demo
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const demo = path.resolve(process.argv[2] || 'demo');
const today = path.join(demo, 'TODAY.html'), tracker = path.join(demo, 'tracker.html');
if (!fs.existsSync(today)) { console.error(`no ${today}: run the demo first`); process.exit(1); }
const pack = fs.readdirSync(path.join(demo, 'out')).find((d) => fs.existsSync(path.join(demo, 'out', d, 'gate.json'))
  && fs.existsSync(path.join(demo, 'out', d, 'resume.html')));
if (!pack) { console.error('no review pack with a resume in the demo'); process.exit(1); }
const resume = path.join(demo, 'out', pack, 'resume.html');

const browser = await chromium.launch();
async function shot(file, out, { width, height, scale = 1, type = 'png' }) {
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: scale, colorScheme: 'light' });
  await ctx.route('**/*', (r) => (/^(file|data):/.test(r.request().url()) ? r.continue() : r.abort()));
  const page = await ctx.newPage();
  await page.goto('file://' + file); await page.waitForTimeout(400);
  await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
  await page.screenshot({ path: out, type, ...(type === 'jpeg' ? { quality: 85 } : {}), clip: { x: 0, y: 0, width, height } });
  await ctx.close();
  console.log(`${out}: ${width * scale}x${height * scale}`);
}
await shot(today, 'docs/img/today.png', { width: 1200, height: 1500, scale: 2 });
await shot(resume, 'docs/img/resume.png', { width: 900, height: 1165, scale: 2 });
await shot(tracker, 'docs/img/tracker.png', { width: 1200, height: 800, scale: 2 });
await shot(today, 'docs/talk/img/today-deck.jpg', { width: 1100, height: 1238, type: 'jpeg' });
await shot(resume, 'docs/talk/img/resume-deck.jpg', { width: 1000, height: 844, type: 'jpeg' });
await browser.close();
