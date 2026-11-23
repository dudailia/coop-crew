// Renders the README banner and the GitHub social preview from their HTML sources in docs/img/src/ (local files only):
// docs/img/banner.png (1280x400 at 2x) and docs/social-preview.png (1280x640, the size GitHub asks for).
// usage: node tools/render_art.mjs
import path from 'node:path';
import { chromium } from 'playwright';

const src = path.resolve('docs/img/src');
const browser = await chromium.launch();
for (const [file, out, w, h, scale] of [['banner.html', 'docs/img/banner.png', 1280, 400, 2], ['social.html', 'docs/social-preview.png', 1280, 640, 1]]) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
  await ctx.route('**/*', (r) => (/^(file|data):/.test(r.request().url()) ? r.continue() : r.abort()));
  const page = await ctx.newPage();
  await page.goto('file://' + path.join(src, file)); await page.waitForTimeout(300);
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
  await ctx.close();
  console.log(`${out}: ${w * scale}x${h * scale}`);
}
await browser.close();
