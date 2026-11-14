// Renders one HTML file to PDF with Playwright's Chromium and prints the page count as JSON: {"pages": N}.
// usage: node tools/render_pdf.mjs <in.html> <out.pdf>
import { chromium } from 'playwright';
import { PDFDocument } from 'pdf-lib';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const [inp, out] = process.argv.slice(2);
if (!inp || !out) { console.error('usage: node tools/render_pdf.mjs <in.html> <out.pdf>'); process.exit(2); }
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  // Only the local file: no network for a resume.
  await page.route('**/*', (r) => (r.request().url().startsWith('file:') ? r.continue() : r.abort()));
  await page.goto(pathToFileURL(path.resolve(inp)).href, { waitUntil: 'load' });
  await page.pdf({ path: out, preferCSSPageSize: true, printBackground: false });
} finally {
  await browser.close();
}
const doc = await PDFDocument.load(await readFile(out));
console.log(JSON.stringify({ pages: doc.getPageCount() }));
