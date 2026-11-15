// Tests for nuworks-mcp over real stdio, against a local fixture (never the real NUworks).
// Run: npm run test:nuworks
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { startFixture } from './fixture.mjs';
import { classifyPage, rowsFromApi, postingFromApi } from '../parse.mjs';

const SERVER = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'server.mjs');
let fx;
before(async () => { fx = await startFixture(); });
after(async () => { await fx.close(); });

function state(settings) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nuworks-test-'));
  fs.mkdirSync(path.join(dir, 'profile'), { recursive: true });
  if (settings) fs.writeFileSync(path.join(dir, 'profile', 'settings.json'), JSON.stringify(settings));
  return dir;
}
const ENABLED = { mode: 'nuworks+external', nuworks: { enabled: true } };

async function connect(dir, extraEnv = {}) {
  const transport = new StdioClientTransport({
    command: process.execPath, args: [SERVER], stderr: 'ignore',
    env: { ...process.env, COOP_STATE: dir, NUWORKS_BASE_URL: fx.base, NUWORKS_DELAY_MS: '10', NUWORKS_OPEN_CMD: 'true', NUWORKS_TEST_SIGNED_IN: '1',
      NUWORKS_DRY_OPEN: '1', NUWORKS_API_GRACE_MS: '1500', ...extraEnv },
  });
  const client = new Client({ name: 'nuworks-test', version: '0.0.0' });
  await client.connect(transport);
  return client;
}
const body = (r) => { const t = r.content[0].text; try { return JSON.parse(t); } catch { return t; } };

test('the tool list is exactly the five read-only tools', async () => {
  const c = await connect(state(ENABLED));
  try {
    const names = (await c.listTools()).tools.map((t) => t.name).sort();
    assert.deepEqual(names, ['nuworks_get_posting', 'nuworks_login', 'nuworks_open', 'nuworks_search', 'nuworks_status']);
    for (const n of names) assert.doesNotMatch(n, /apply|message|upload|rsvp|edit|submit|send/i);
  } finally { await c.close(); }
});

test('disabled settings: every tool but status refuses and nothing is loaded', async () => {
  for (const s of [null, { mode: 'external', nuworks: { enabled: true } }, { mode: 'nuworks+external', nuworks: { enabled: false } }]) {
    const before = fx.log.length;
    const c = await connect(state(s));
    try {
      for (const [name, args] of [['nuworks_search', { keywords: 'data' }], ['nuworks_get_posting', { id: 'a1b2c3' }],
        ['nuworks_open', { id: 'a1b2c3' }], ['nuworks_login', {}]]) {
        const r = await c.callTool({ name, arguments: args });
        assert.equal(r.isError, true, `${name} should refuse with ${JSON.stringify(s)}`);
        assert.match(r.content[0].text, /disabled/i);
      }
      const st = body(await c.callTool({ name: 'nuworks_status', arguments: {} }));
      assert.equal(st.enabled, false);
    } finally { await c.close(); }
    assert.equal(fx.log.length, before, 'a disabled server must not load any page');
  }
});

test('enabled: status, search, posting, cache, open, and no POST ever reaches NUworks', async () => {
  const dir = state(ENABLED);
  const c = await connect(dir);
  try {
    const st = body(await c.callTool({ name: 'nuworks_status', arguments: {} }));
    assert.equal(st.enabled, true); assert.equal(st.signed_in, true);

    const s = body(await c.callTool({ name: 'nuworks_search', arguments: { keywords: 'data', max_pages: 3 } }));
    assert.equal(s.rows.length, 3);
    const r = s.rows.find((x) => x.posting_id === 'a1b2c3');
    assert.equal(r.title, 'Data Analyst Co-op'); assert.equal(r.employer, 'Example Robotics');
    assert.equal(r.location, 'Boston, MA'); assert.equal(r.deadline, 'Dec 1, 2026'); assert.match(r.url, /jobs\/detail\/a1b2c3$/);

    const f = body(await c.callTool({ name: 'nuworks_search', arguments: { keywords: 'data', location: 'remote' } }));
    assert.deepEqual(f.rows.map((x) => x.posting_id), ['g7h8i9']);

    const p = body(await c.callTool({ name: 'nuworks_get_posting', arguments: { id: 'a1b2c3' } }));
    assert.equal(p.from_cache, false, `get_posting answered: ${JSON.stringify(p).slice(0, 600)}`);
    assert.match(p.description, /weekly reporting/);
    assert.match(p.qualifications, /Python and SQL/);
    assert.match(p.application_instructions, /resume and a cover letter/);
    assert.match(p.documents_required, /Resume, Cover Letter/);
    assert.equal(p.deadline, 'Dec 1, 2026');
    assert.match(p.applicant_type_message, /applicant type does not match/i);

    const hits = fx.log.filter((l) => l.url.includes('detail/a1b2c3')).length;
    const again = body(await c.callTool({ name: 'nuworks_get_posting', arguments: { id: 'a1b2c3' } }));
    assert.equal(again.from_cache, true);
    assert.equal(fx.log.filter((l) => l.url.includes('detail/a1b2c3')).length, hits, 'the cached posting is not loaded again');

    const o = body(await c.callTool({ name: 'nuworks_open', arguments: { id: 'a1b2c3' } }));
    assert.match(o.url, /jobs\/detail\/a1b2c3$/);

    await new Promise((res) => setTimeout(res, 300)); // let the page's own POST attempts fire, if any got through
    assert.deepEqual(fx.nonGet(), [], 'no POST or other non-GET request may reach NUworks');
    const st2 = body(await c.callTool({ name: 'nuworks_status', arguments: {} }));
    assert.ok(st2.blocked_requests >= 1, `the posting page tried to POST and was blocked (status: ${JSON.stringify(st2).slice(0, 400)})`);
  } finally { await c.close(); }
});

test('the live student app: rows and postings come from the JSON the page loads (no ids in the markup, nothing clicked)', async () => {
  const c = await connect(state(ENABLED));
  try {
    const s = body(await c.callTool({ name: 'nuworks_search', arguments: { keywords: 'app', max_pages: 1 } }));
    assert.equal(s.rows.length, 2, `search answered: ${JSON.stringify(s).slice(0, 500)}`);
    const r = s.rows.find((x) => x.posting_id === '0123456789abcdef0123456789abcdef');
    assert.equal(r.title, 'Data Engineering Co-Op'); assert.equal(r.employer, 'Example Data Corp');
    assert.equal(r.location, 'Boston, Massachusetts, United States'); assert.equal(r.deadline, 'Dec 26, 2026');
    assert.equal(r.position_type, 'Co-op'); assert.match(r.url, /app\/jobs\/detail\/0123456789abcdef0123456789abcdef$/);
    const p = body(await c.callTool({ name: 'nuworks_get_posting', arguments: { id: '0123456789abcdef0123456789abcdef' } }));
    assert.match(p.description, /Build data pipelines & dashboards\.\n+- Python/);
    assert.equal(p.employer, 'Example Data Corp'); assert.equal(p.position_type, 'Co-op'); assert.equal(p.workplace, 'Hybrid');
    assert.equal(p.deadline, 'December 26, 2026'); assert.match(p.qualifications, /Second-year/);
    assert.deepEqual(fx.nonGet(), [], 'no POST or other non-GET request may reach NUworks');
  } finally { await c.close(); }
});

test('rowsFromApi and postingFromApi read the app JSON', () => {
  const base = new URL('https://x.example/students/');
  const rows = rowsFromApi({ models: [{ job_id: 'abc', job_title: 'Co-op &amp; more', name: 'Hidden Co', blind_flag: 1, job_type: ['Co-op', 'Full Time'] }, { job_title: 'no id' }] }, base);
  assert.deepEqual(rows.map((x) => [x.title, x.employer, x.position_type, x.url]),
    [['Co-op & more', '(employer hidden by NUworks)', 'Co-op, Full Time', 'https://x.example/students/app/jobs/detail/abc']]);
  assert.deepEqual(rowsFromApi(null, base), []);
  assert.equal(postingFromApi({}), null);
  assert.equal(postingFromApi({ job_id: 'abc', job_emp: { name: 'Emp' } }).employer, 'Emp');
});

for (const [kw, re] of [['captcha', /CAPTCHA/], ['error', /error page/], ['login', /not signed in/]]) {
  test(`a ${kw} page stops the run and later calls refuse`, async () => {
    const c = await connect(state(ENABLED));
    try {
      const r = await c.callTool({ name: 'nuworks_search', arguments: { keywords: kw } });
      assert.equal(r.isError, true); assert.match(r.content[0].text, re);
      const before = fx.log.length;
      const r2 = await c.callTool({ name: 'nuworks_search', arguments: { keywords: 'data' } });
      assert.equal(r2.isError, true); assert.match(r2.content[0].text, /stopped earlier/);
      const r3 = await c.callTool({ name: 'nuworks_get_posting', arguments: { id: 'd4e5f6' } });
      assert.equal(r3.isError, true);
      assert.equal(fx.log.length, before, 'nothing more is loaded after a stop');
    } finally { await c.close(); }
  });
}

test('the postings-per-run cap holds across calls', async () => {
  const c = await connect(state(ENABLED), { NUWORKS_MAX_POSTINGS: '2' });
  try {
    const s = body(await c.callTool({ name: 'nuworks_search', arguments: { keywords: 'data' } }));
    assert.equal(s.rows.length, 2);
    assert.match(s.notes.join(' '), /limit of 2/);
    const r = await c.callTool({ name: 'nuworks_get_posting', arguments: { id: 'g7h8i9' } });
    assert.equal(r.isError, true); assert.match(r.content[0].text, /limit/);
  } finally { await c.close(); }
});

test('the kill switch stops every load', async () => {
  const dir = state(ENABLED);
  fs.writeFileSync(path.join(dir, 'STOP'), '');
  const c = await connect(dir);
  try {
    const r = await c.callTool({ name: 'nuworks_search', arguments: { keywords: 'data' } });
    assert.equal(r.isError, true); assert.match(r.content[0].text, /STOP/);
  } finally { await c.close(); }
});

test('classifyPage spots sign-in pages, CAPTCHAs and errors', () => {
  const host = 'northeastern-csm.symplicity.com';
  assert.equal(classifyPage({ status: 200, url: `https://${host}/students/app/jobs/search`, title: 'Jobs', text: 'Jobs' }, host), null);
  assert.match(classifyPage({ status: 200, url: 'https://login.microsoftonline.com/x', title: 'Sign in', text: '' }, host), /not signed in/);
  assert.match(classifyPage({ status: 200, url: `https://${host}/students/`, title: 'x', text: '', hasCaptchaFrame: true }, host), /CAPTCHA/);
  assert.match(classifyPage({ status: 503, url: `https://${host}/students/`, title: '', text: '' }, host), /HTTP 503/);
});
