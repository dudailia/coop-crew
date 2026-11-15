// Parsing and page checks for NUworks (Symplicity CSM). Read-only: these functions only read the DOM.
//
// extractListing and extractPosting run INSIDE the page (page.evaluate), so they must not use anything outside their own
// body. They are written defensively against Symplicity's markup (both the current Angular student app,
// /students/app/jobs/..., and the older index.php?s=jobs pages). The selectors were written without access to the live
// site: verify them against a real signed-in NUworks session (acceptance test 7) and adjust here only.

/** Rows from a job listing page: [{title, employer, location, dates, deadline, posting_id, url}] */
export function extractListing() {
  const txt = (el) => (el ? (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim() : '');
  const pick = (root, sels) => { for (const s of sels) { const el = root.querySelector(s); if (el && txt(el)) return el; } return null; };
  const idFrom = (href) => {
    if (!href) return '';
    const m = href.match(/jobs\/detail\/([\w-]+)/) || href.match(/[?&]id=([\w-]+)/) || href.match(/\/jobs\/([\w-]{4,})(?:[/?#]|$)/);
    return m ? m[1] : '';
  };
  const ITEM_SELECTORS = ['[data-job-id]', '.list-item', 'li.job', 'div.job-item', '.jobs-list li', 'tr.job', '[class*="job-list-item"]',
    '[class*="list-item"]'];
  let items = [];
  for (const s of ITEM_SELECTORS) { items = Array.from(document.querySelectorAll(s)); if (items.length) break; }
  if (!items.length) { // last resort: every link to a posting
    items = Array.from(document.querySelectorAll('a[href*="jobs/detail/"], a[href*="s=jobs"][href*="id="]')).map((a) => a.closest('li, tr, div') || a);
  }
  const rows = []; const seen = new Set();
  for (const it of items) {
    const link = it.matches('a[href]') ? it : (it.querySelector('a[href*="jobs/detail/"], a[href*="id="], a[href*="/jobs/"]') || it.querySelector('a[href]'));
    const href = link ? link.href : '';
    const id = it.getAttribute('data-job-id') || idFrom(href);
    const titleEl = pick(it, ['.list-item-title', '.job-title', '[class*="title"]', 'h3', 'h4', 'a']);
    const title = txt(titleEl);
    if (!title || !id || seen.has(id)) continue;
    seen.add(id);
    const employer = txt(pick(it, ['.list-item-subtitle', '.employer', '.company', '[class*="employer"]', '[class*="organization"]']));
    const location = txt(pick(it, ['[class*="location"]', '.city']));
    let deadline = txt(pick(it, ['[class*="deadline"]', '[class*="expir"]']));
    const all = txt(it);
    if (!deadline) { const m = all.match(/(?:deadline|expires?|apply by)[:\s]+([A-Za-z]{3,9}\.? \d{1,2},? \d{4}|\d{1,2}\/\d{1,2}\/\d{2,4})/i); if (m) deadline = m[1]; }
    deadline = deadline.replace(/^(application )?(deadline|expires?|expiration date|apply by)[:\s]*/i, '');
    const dates = txt(pick(it, ['[class*="dates"]', '[class*="posted"]', '[class*="date"]:not([class*="deadline"])']));
    rows.push({ title, employer, location, dates, deadline, posting_id: id, url: href });
  }
  const noResults = /no (jobs|results|postings) (were )?found|0 results/i.test(txt(document.body));
  return { rows, noResults };
}

/** Fields from one posting page. */
export function extractPosting() {
  const txt = (el) => (el ? (el.innerText || el.textContent || '').replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim() : '');
  const LABELS = {
    description: /^(job |position )?description$/i,
    qualifications: /^(qualifications|requirements|desired skills|minimum qualifications)$/i,
    application_instructions: /^(application instructions|how to apply|instructions)$/i,
    documents_required: /^(documents? required|required documents|application documents)$/i,
    deadline: /^(application deadline|deadline|expiration date|apply by)$/i,
    location: /^(location|city|job location)$/i,
    position_type: /^(position type|job type|type)$/i,
    employer: /^(employer|organization|company)$/i,
  };
  const out = {};
  const nodes = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,dt,label,strong,b,th,.field-label,[class*="label"]'));
  for (const n of nodes) {
    const label = txt(n).replace(/[:*]\s*$/, '').trim();
    if (!label || label.length > 40) continue;
    for (const [key, re] of Object.entries(LABELS)) {
      if (out[key] || !re.test(label)) continue;
      let val = '';
      if (n.tagName === 'DT') { const dd = n.nextElementSibling; val = dd && dd.tagName === 'DD' ? txt(dd) : ''; }
      else if (n.tagName === 'TH') { val = txt(n.nextElementSibling); }
      if (!val) {
        let sib = n.nextElementSibling; const parts = [];
        while (sib && !/^H[1-5]$/.test(sib.tagName) && parts.join(' ').length < 6000) { parts.push(txt(sib)); sib = sib.nextElementSibling; if (n.tagName !== 'H2' && n.tagName !== 'H3') break; }
        val = parts.filter(Boolean).join('\n');
      }
      if (!val && n.parentElement) val = txt(n.parentElement).replace(txt(n), '').replace(/^[:\s]+/, '');
      if (val) out[key] = val.slice(0, 8000);
    }
  }
  const h = document.querySelector('h1, .job-title, [class*="job-title"]');
  out.title = txt(h);
  const body = txt(document.body);
  const m = body.match(/[^.\n]*(applicant type|not eligible to apply|does not match your (profile|applicant)|you are not eligible|you cannot apply|not open to your)[^.\n]*[.]?/i);
  out.applicant_type_message = m ? m[0].trim() : '';
  if (!out.description) out.description = body.slice(0, 8000);
  return out;
}

const CAPTCHA_RE = /captcha|are you a robot|verify (that )?you are (a )?human|unusual traffic|security check|cf-challenge|turnstile/i;
const ERROR_RE = /^(error|access denied|forbidden|page not found|not found|service unavailable|something went wrong|session expired)\b/i;
export const LOGIN_PATH_RE = /\/(login|signin|sign-in|sso|saml|shibboleth|auth|idp|adfs)(\b|\/|\.|\?)/i;

/**
 * Classifies a loaded page. Returns null when it is a normal NUworks page, else the reason to stop the run.
 * p: {status, url, title, text, hasPassword, hasCaptchaFrame}
 */
export function classifyPage(p, baseHost) {
  if (p.status && p.status >= 400) return `error page (HTTP ${p.status}) at ${p.url}`;
  if (p.hasCaptchaFrame || CAPTCHA_RE.test(p.title || '') || CAPTCHA_RE.test((p.text || '').slice(0, 3000))) return `CAPTCHA or bot check at ${p.url}`;
  let u;
  try { u = new URL(p.url); } catch { return `unreadable page address ${p.url}`; }
  if (u.host !== baseHost || LOGIN_PATH_RE.test(u.pathname + u.search) || p.hasPassword) return `not signed in: NUworks sent the browser to a sign-in page (${u.host}${u.pathname}). Run nuworks_login.`;
  if (ERROR_RE.test((p.title || '').trim()) || ERROR_RE.test(((p.text || '').trim().split('\n')[0] || ''))) return `error page ("${(p.title || p.text || '').trim().slice(0, 60)}") at ${p.url}`;
  return null;
}

/** Text near an applicant-type mismatch, for rows filtered by NUworks. Exported for tests. */
export function applicantTypeMessage(text) {
  const m = (text || '').match(/[^.\n]*(applicant type|not eligible to apply|does not match your (profile|applicant)|you are not eligible)[^.\n]*[.]?/i);
  return m ? m[0].trim() : '';
}

// ---- The student app's own data (live check, 2026-11-14) ----
// The listing page (/students/app/jobs/search) is an Angular app: its rows carry no posting link or id in the markup
// (a row opens its posting by click, and the reader never clicks). The page fetches its rows as JSON from
// /api/v2/jobs?keywords=...&page=N&json_mode=read_only, and a posting from /api/v3/jobs/<id>. The server reads those
// responses as the page receives them (no extra request); extractListing/extractPosting stay as the fallback.
export const LIST_API = /^\/api\/v\d+\/jobs\/?$/;
export const POSTING_API = /^\/api\/v\d+\/jobs\/([0-9a-f]{16,})\/?$/i;

/** Plain text from the app's values: HTML strings, {_label} objects, and lists of either. */
export function plain(v) {
  if (v == null) return '';
  if (Array.isArray(v)) return v.map(plain).filter(Boolean).join(', ');
  if (typeof v === 'object') return plain(v._label ?? v.label ?? v.name ?? '');
  return String(v).replace(/<(br|\/p|\/li|\/div|\/h\d)\s*\/?>/gi, '\n').replace(/<li[^>]*>/gi, '- ').replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/&#39;|&rsquo;|&lsquo;/g, "'").replace(/&ldquo;|&rdquo;/g, '"').replace(/&ndash;|&mdash;/g, '-')
    .replace(/[ \t]+/g, ' ').replace(/\n\s*\n\s*\n+/g, '\n\n').trim();
}

/** Rows from the listing JSON: [{title, employer, location, dates, deadline, posting_id, url, position_type}] */
export function rowsFromApi(json, base) {
  const models = (json && Array.isArray(json.models)) ? json.models : [];
  return models.filter((m) => m && m.job_id && m.job_title).map((m) => ({
    title: plain(m.job_title), employer: m.blind_flag ? '(employer hidden by NUworks)' : plain(m.name),
    location: plain(m.job_location), dates: plain(m.postdate) ? `posted ${plain(m.postdate)}` : '', deadline: plain(m.deadline),
    posting_id: String(m.job_id), url: new URL(`app/jobs/detail/${m.job_id}`, base).href, position_type: plain(m.job_type),
  }));
}

/** Fields from one posting's JSON, in the shape nuworks_get_posting returns. */
export function postingFromApi(j) {
  if (!j || !j.job_id) return null;
  return {
    title: plain(j.job_title), employer: plain(j.employer_name || j.job_emp), location: plain(j.job_location || j.location),
    position_type: plain(j.job_type), description: plain(j.job_desc), qualifications: plain(j.qualifications),
    application_instructions: plain(j.contact_blurb || j.resume_mode), documents_required: plain(j.documents_required),
    deadline: plain(j.application_deadline), dates: plain(j.job_dates || [j.start_date, j.job_end].filter(Boolean).join(' to ')),
    work_term: plain(j.el_work_term || j.recruiting_cycle), workplace: plain(j.workplace_type || j.symp_remote_onsite || j.location_type),
    pay: plain(j.payment_range || j.salary), work_authorization: plain(j.work_authorization),
  };
}
