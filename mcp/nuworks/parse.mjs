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
const LOGIN_PATH_RE = /\/(login|signin|sign-in|sso|saml|shibboleth|auth|idp|adfs)(\b|\/|\.|\?)/i;

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
