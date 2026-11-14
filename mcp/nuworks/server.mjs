#!/usr/bin/env node
// nuworks-mcp: a local, READ-ONLY MCP server for NUworks (Symplicity CSM), run over stdio on the student's own machine.
// It reads only what the signed-in student can already see. There are no apply, message, upload, RSVP or profile-edit
// tools. Applying stays a human click in NUworks.
//
// Rules enforced in this file, not only in prompts:
//  - every tool but nuworks_status refuses unless profile/settings.json has "mode": "nuworks+external" and
//    "nuworks": {"enabled": true} (re-read on every call); the kill switch (STOP, ~/STOP-AGENTS) stops every page load
//  - headless runs abort every non-GET request and every page navigation off the NUworks host; nothing is clicked
//  - one page load every 3 to 5 seconds, at most 100 postings per run, a local cache, and a full stop on a CAPTCHA,
//    error page or sign-in redirect (every later call in this run refuses)
//  - the student signs in themselves in a visible window; the server never reads, types or stores a password
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { extractListing, extractPosting, classifyPage } from './parse.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const STATE = path.resolve(process.env.COOP_STATE || ROOT);
const NU_DIR = path.join(STATE, 'data', 'nuworks');
const PROFILE_DIR = path.join(NU_DIR, 'browser-profile');
const CACHE_DIR = path.join(NU_DIR, 'cache');
const SESSION_FILE = path.join(NU_DIR, 'session.json');
const SETTINGS_FILE = path.join(STATE, 'profile', 'settings.json');
const LOG_FILE = path.join(STATE, 'logs', 'nuworks.log');
const STOP_FILES = [...new Set([path.join(STATE, 'STOP'), path.join(ROOT, 'STOP'), path.join(os.homedir(), 'STOP-AGENTS')])];
const BUSY_FILE = path.join(STATE, 'logs', 'nuworks.busy'); // the Python tools' lock waits while a NUworks browser is open

const BASE = new URL(process.env.NUWORKS_BASE_URL || 'https://northeastern-csm.symplicity.com/students/');
const BASE_HOST = BASE.host;
const SEARCH_PATH = process.env.NUWORKS_SEARCH_PATH || 'app/jobs/search?keywords={keywords}&page={page}';
const POSTING_PATH = process.env.NUWORKS_POSTING_PATH || 'app/jobs/detail/{id}';
const MAX_POSTINGS = Math.min(100, Number(process.env.NUWORKS_MAX_POSTINGS) || 100);
const CACHE_TTL_MS = 24 * 3600 * 1000;
const TEST_SIGNED_IN = process.env.NUWORKS_TEST_SIGNED_IN === '1';
const DRY_OPEN = process.env.NUWORKS_DRY_OPEN === '1';
// Hosts the student's own sign-in may pass through (visible login window only).
const SSO_HOSTS = /(^|\.)(symplicity\.com|northeastern\.edu|microsoftonline\.com|microsoft\.com|live\.com|duosecurity\.com|okta\.com)$/i;

for (const d of [NU_DIR, CACHE_DIR, path.dirname(LOG_FILE)]) fs.mkdirSync(d, { recursive: true });

function log(msg) {
  const line = `${new Date().toISOString()} ${msg}\n`;
  try { fs.appendFileSync(LOG_FILE, line); } catch { /* logging never breaks a call */ }
  process.stderr.write(line);
}

// ---- run state (one run = one server process) ----
let halted = null;            // the reason this run stopped (CAPTCHA, error page, sign-in redirect)
const touched = new Set();    // posting ids read this run (max MAX_POSTINGS)
let lastLoad = 0;
let blockedRequests = 0;
let busy = Promise.resolve(); // one browser at a time

function serial(fn) { const p = busy.then(fn, fn); busy = p.catch(() => {}); return p; }

function settings() {
  try { return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8')); } catch { return null; }
}
function gate() {
  const s = settings();
  if (!s) return `NUworks is disabled: ${SETTINGS_FILE} does not exist. Run /setup first.`;
  if (s.mode !== 'nuworks+external') return `NUworks is disabled: sourcing mode is "${s.mode || 'unset'}", not "nuworks+external".`;
  if (!(s.nuworks && s.nuworks.enabled === true)) return 'NUworks is disabled: profile/settings.json has no "nuworks": {"enabled": true}. It is off by default: the student turns it on with tools/nuworks_enable.py (approved read-only scope: mcp/nuworks/APPROVAL.md). Automated read access (mcp/nuworks/APPROVAL.md).';
  return null;
}
function stopped() { return STOP_FILES.find((f) => fs.existsSync(f)) || null; }

function text(obj, isError = false) {
  return { content: [{ type: 'text', text: typeof obj === 'string' ? obj : JSON.stringify(obj, null, 1) }], ...(isError ? { isError: true } : {}) };
}
function refuse(why) { log(`refused: ${why}`); return text(why, true); }

function preflight() {
  const g = gate(); if (g) return g;
  const s = stopped(); if (s) return `STOP: the kill switch is on (${s}). Nothing was loaded.`;
  if (halted) return `This NUworks run stopped earlier and loads nothing more: ${halted}. Check NUworks yourself in your browser; the next run starts fresh.`;
  return null;
}

async function politeWait() {
  const fixed = process.env.NUWORKS_DELAY_MS;
  const gap = fixed !== undefined ? Number(fixed) : 3000 + Math.random() * 2000;
  const wait = lastLoad ? Math.max(0, lastLoad + gap - Date.now()) : 0;
  if (wait) await new Promise((r) => setTimeout(r, wait));
  lastLoad = Date.now();
}

async function withBrowser(fn, { headless = true } = {}) {
  fs.mkdirSync(path.dirname(BUSY_FILE), { recursive: true });
  fs.writeFileSync(BUSY_FILE, String(process.pid));
  let ctx;
  try { ctx = await chromium.launchPersistentContext(PROFILE_DIR, { headless, viewport: { width: 1280, height: 900 } }); }
  catch (e) { fs.rmSync(BUSY_FILE, { force: true }); throw e; }
  try {
    if (headless) {
      await ctx.route('**/*', (route) => {
        const req = route.request();
        let host = '';
        try { host = new URL(req.url()).host; } catch { /* data: and similar */ }
        if (req.method() !== 'GET') { blockedRequests++; log(`blocked ${req.method()} ${req.url()}`); return route.fulfill({ status: 204, body: '' }); } // answered locally: never sent, and a 204 keeps the page where it is
        let mainNav = false;
        try { mainNav = req.isNavigationRequest() && req.frame() === req.frame().page().mainFrame(); } catch { /* worker requests */ }
        if (mainNav && host && host !== BASE_HOST) {
          // A redirect to sign-in is let through only so it can be recognised and the run stopped; nothing is done there.
          if (SSO_HOSTS.test(host.split(':')[0])) return route.continue();
          blockedRequests++; log(`blocked navigation to ${req.url()}`); return route.fulfill({ status: 204, body: '' }); // answered locally: never sent, and a 204 keeps the page where it is
        }
        return route.continue();
      });
    }
    const page = ctx.pages()[0] || await ctx.newPage();
    return await fn(page, ctx);
  } finally {
    // after reading, let in-flight requests reach the route guard (so every blocked attempt is counted) before closing
    for (const pg of ctx.pages()) await pg.waitForLoadState('networkidle', { timeout: 1500 }).catch(() => {});
    fs.rmSync(BUSY_FILE, { force: true });
    await ctx.close().catch(() => {});
  }
}

/** Loads one NUworks page, politely. Returns null when fine, else stops the run and returns the reason. */
async function load(page, url) {
  const s = stopped(); if (s) return `STOP: the kill switch is on (${s})`;
  if (new URL(url).host !== BASE_HOST) return `refused: ${url} is not on NUworks (${BASE_HOST})`;
  await politeWait();
  let status = 0;
  try {
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    status = resp ? resp.status() : 0;
    await page.waitForSelector('[data-job-id], .list-item, li.job, .job-item, h1, dt, form, input[type=password]', { timeout: 8000 }).catch(() => {});
  } catch (e) {
    halted = `the page did not load (${String(e.message || e).split('\n')[0]})`;
    return halted;
  }
  const read = () => page.evaluate(() => ({
    title: document.title,
    text: (document.body && document.body.innerText) || '',
    hasPassword: !!document.querySelector('input[type=password]'),
    hasCaptchaFrame: !!document.querySelector('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"], .g-recaptcha, .h-captcha, #challenge-form'),
  }));
  const info = await read().catch(async () => { await page.waitForLoadState('domcontentloaded').catch(() => {}); return read(); })
    .catch(() => ({ title: '', text: '', hasPassword: false, hasCaptchaFrame: false }));
  const why = classifyPage({ status, url: page.url(), ...info }, BASE_HOST);
  if (why) { halted = why; log(`run stopped: ${why}`); return why; }
  return null;
}

function cacheGet(id) {
  try {
    const c = JSON.parse(fs.readFileSync(path.join(CACHE_DIR, `posting-${safeId(id)}.json`), 'utf8'));
    return Date.now() - c.fetched_at < CACHE_TTL_MS ? c : null;
  } catch { return null; }
}
function cachePut(id, v) { fs.writeFileSync(path.join(CACHE_DIR, `posting-${safeId(id)}.json`), JSON.stringify({ ...v, fetched_at: Date.now() }, null, 1)); }
const INDEX_FILE = path.join(CACHE_DIR, 'index.json');
function index() { try { return JSON.parse(fs.readFileSync(INDEX_FILE, 'utf8')); } catch { return {}; } }
function remember(rows) { const ix = index(); for (const r of rows) if (r.posting_id && r.url) ix[r.posting_id] = r.url; fs.writeFileSync(INDEX_FILE, JSON.stringify(ix, null, 1)); }
function safeId(id) { return String(id).replace(/[^\w-]/g, '_').slice(0, 80); }
function postingUrl(id) {
  const known = index()[id];
  if (known && new URL(known).host === BASE_HOST) return known;
  return new URL(POSTING_PATH.replace('{id}', encodeURIComponent(id)), BASE).href;
}
function signedInMarker() { try { return JSON.parse(fs.readFileSync(SESSION_FILE, 'utf8')); } catch { return null; } }

// ---- the server: exactly five tools, all read-only ----
const server = new McpServer({ name: 'nuworks', version: '0.1.0' });

server.registerTool('nuworks_login', {
  title: 'Sign in to NUworks (you sign in yourself)',
  description: 'Opens a visible browser window at NUworks so the student signs in themselves (Northeastern SSO and Duo). The server never sees, types or stores the password; it keeps only the browser session on disk. Waits up to 5 minutes.',
  inputSchema: {},
}, async () => serial(async () => {
  const g = gate(); if (g) return refuse(g);
  const s = stopped(); if (s) return refuse(`STOP: the kill switch is on (${s}).`);
  if (TEST_SIGNED_IN) { fs.writeFileSync(SESSION_FILE, JSON.stringify({ signed_in_at: new Date().toISOString(), test: true })); return text('Test mode: sign-in window skipped.'); }
  log('login: opening a visible window; the student signs in');
  const done = await withBrowser(async (page) => {
    await page.goto(BASE.href, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
    const until = Date.now() + 5 * 60 * 1000;
    while (Date.now() < until) {
      if (page.isClosed()) return false;
      const u = new URL(page.url());
      const pw = await page.$('input[type=password]').catch(() => null);
      if (u.host === BASE_HOST && !/\/(login|sso|saml|auth)/i.test(u.pathname) && !pw) return true;
      await new Promise((r) => setTimeout(r, 2000));
    }
    return false;
  }, { headless: false });
  if (!done) return text('Not signed in: the window closed or 5 minutes passed. Run nuworks_login again when you are ready.', true);
  fs.writeFileSync(SESSION_FILE, JSON.stringify({ signed_in_at: new Date().toISOString() }));
  halted = null;
  return text('Signed in. The session is saved in data/nuworks/browser-profile on this machine; no password was seen or stored.');
}));

server.registerTool('nuworks_status', {
  title: 'NUworks status',
  description: 'Says whether the NUworks module is enabled and whether the saved session is signed in. Loads at most one page, and none when disabled.',
  inputSchema: {},
}, async () => serial(async () => {
  const g = gate();
  const out = { enabled: !g, why_disabled: g || '', base_url: BASE.href, signed_in: null, run_stopped: halted || '',
    postings_read_this_run: touched.size, max_postings_per_run: MAX_POSTINGS, blocked_requests: blockedRequests,
    session_saved_at: signedInMarker()?.signed_in_at || '' };
  if (g) return text(out);
  if (stopped()) { out.signed_in = 'unknown (kill switch on)'; return text(out); }
  if (halted) { out.signed_in = 'unknown (run stopped)'; return text(out); }
  const why = await withBrowser((page) => load(page, BASE.href));
  if (why && /not signed in/.test(why)) { halted = null; out.signed_in = false; out.note = 'Run nuworks_login and sign in yourself.'; }
  else if (why) { out.signed_in = 'unknown'; out.run_stopped = why; }
  else out.signed_in = true;
  return text(out);
}));

server.registerTool('nuworks_search', {
  title: 'Search NUworks listings (read-only)',
  description: 'Reads NUworks job listing pages the signed-in student can already see and returns rows: title, employer, location, dates, deadline, posting_id, url. Polite: one page every 3 to 5 s, at most 100 postings per run; stops on a CAPTCHA, error or sign-in page.',
  inputSchema: {
    keywords: z.string().default('').describe('Search words, as typed in NUworks'),
    position_type: z.string().optional().describe('Filter, e.g. "co-op"; matched against each row'),
    location: z.string().optional().describe('Filter, e.g. "Boston"; matched against each row'),
    industry: z.string().optional().describe('Filter; matched against each row'),
    max_pages: z.number().int().min(1).max(10).default(3),
  },
}, async ({ keywords = '', position_type, location, industry, max_pages = 3 }) => serial(async () => {
  const p = preflight(); if (p) return refuse(p);
  const rows = []; const seen = new Set(); let stop = null; let capped = false;
  await withBrowser(async (page) => {
    for (let n = 1; n <= max_pages; n++) {
      const url = new URL(SEARCH_PATH.replace('{keywords}', encodeURIComponent(keywords)).replace('{page}', String(n)), BASE).href;
      stop = await load(page, url);
      if (stop) return;
      const { rows: got } = await page.evaluate(extractListing);
      const fresh = got.filter((r) => !seen.has(r.posting_id));
      if (!fresh.length) return;
      for (const r of fresh) {
        if (!touched.has(r.posting_id) && touched.size >= MAX_POSTINGS) { capped = true; return; }
        touched.add(r.posting_id); seen.add(r.posting_id); rows.push(r);
      }
    }
  });
  const has = (r, f) => !f || Object.values(r).join(' ').toLowerCase().includes(String(f).toLowerCase());
  const out = rows.filter((r) => has(r, position_type) && has(r, location) && has(r, industry));
  remember(rows);
  const notes = [];
  if (stop) notes.push(`Stopped: ${stop}`);
  if (capped) notes.push(`Reached the limit of ${MAX_POSTINGS} postings for this run.`);
  log(`search "${keywords}": ${rows.length} rows read, ${out.length} after filters${stop ? `; stopped: ${stop}` : ''}`);
  return text({ rows: out, rows_read: rows.length, postings_read_this_run: touched.size, notes }, !!stop && !rows.length);
}));

server.registerTool('nuworks_get_posting', {
  title: 'Read one NUworks posting (read-only)',
  description: 'Returns one posting: description, qualifications, application instructions, documents required, deadline, and any applicant-type mismatch message. Served from the local cache when read in the last 24 hours.',
  inputSchema: { id: z.string().min(1).describe('posting_id from nuworks_search') },
}, async ({ id }) => serial(async () => {
  const g = gate(); if (g) return refuse(g);
  const cached = cacheGet(id);
  if (cached) return text({ ...cached, from_cache: true });
  const p = preflight(); if (p) return refuse(p);
  if (!touched.has(id) && touched.size >= MAX_POSTINGS) return refuse(`Reached the limit of ${MAX_POSTINGS} postings for this run.`);
  const url = postingUrl(id);
  let res = null; let stop = null;
  await withBrowser(async (page) => {
    stop = await load(page, url);
    if (stop) return;
    res = await page.evaluate(extractPosting);
  });
  if (stop) return refuse(`Stopped: ${stop}`);
  touched.add(id);
  const out = { posting_id: id, url, title: res.title || '', employer: res.employer || '', location: res.location || '',
    position_type: res.position_type || '', description: res.description || '', qualifications: res.qualifications || '',
    application_instructions: res.application_instructions || '', documents_required: res.documents_required || '',
    deadline: res.deadline || '', applicant_type_message: res.applicant_type_message || '' };
  cachePut(id, out);
  return text({ ...out, from_cache: false });
}));

server.registerTool('nuworks_open', {
  title: 'Open a posting in your own browser',
  description: "Opens the posting in the student's own default browser, so they read it and apply themselves. It does not apply or click anything.",
  inputSchema: { id: z.string().min(1).describe('posting_id from nuworks_search') },
}, async ({ id }) => {
  const g = gate(); if (g) return refuse(g);
  const url = postingUrl(id);
  if (new URL(url).host !== BASE_HOST) return refuse(`refused: ${url} is not on NUworks`);
  if (DRY_OPEN) return text({ opened: false, url, note: 'dry run' });
  const isWsl = process.platform === 'linux' && /microsoft/i.test((() => { try { return fs.readFileSync('/proc/version', 'utf8'); } catch { return ''; } })());
  const cmd = process.env.NUWORKS_OPEN_CMD || (process.platform === 'darwin' ? 'open' : isWsl ? 'wslview' : process.platform === 'win32' ? 'explorer' : 'xdg-open');
  try { spawn(cmd, [url], { detached: true, stdio: 'ignore' }).unref(); }
  catch (e) { return text({ opened: false, url, note: `could not start ${cmd}: ${e.message}; open the URL yourself` }, true); }
  return text({ opened: true, url, note: 'Opened in your browser. Apply there yourself.' });
});

await server.connect(new StdioServerTransport());
log(`nuworks-mcp ready (state ${STATE}, base ${BASE.href}, ${gate() ? 'disabled' : 'enabled'})`);
