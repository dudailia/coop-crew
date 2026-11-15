// A local stand-in for NUworks (Symplicity CSM) used by the tests. It never talks to Northeastern.
// It records every request, so the tests can check that no POST (or other non-GET) ever arrived.
import http from 'node:http';

const JOBS = [
  { id: 'a1b2c3', title: 'Data Analyst Co-op', employer: 'Example Robotics', location: 'Boston, MA', deadline: 'Dec 1, 2026', type: 'Co-op' },
  { id: 'd4e5f6', title: 'Software Engineering Co-op', employer: 'Sample Health', location: 'Cambridge, MA', deadline: 'Dec 15, 2026', type: 'Co-op' },
  { id: 'g7h8i9', title: 'Finance Intern', employer: 'Demo Capital', location: 'Remote', deadline: 'Jan 5, 2027', type: 'Internship' },
];

const page = (title, body) => `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title></head><body>${body}</body></html>`;

function listing() {
  return page('Jobs - NUworks', `<h1>Jobs</h1><div class="jobs-list">` + JOBS.map((j) => `
    <div class="list-item" data-job-id="${j.id}">
      <a class="list-item-title" href="/students/app/jobs/detail/${j.id}">${j.title}</a>
      <div class="list-item-subtitle">${j.employer}</div>
      <div class="job-location">${j.location}</div>
      <div class="job-type">${j.type}</div>
      <div class="job-deadline">Deadline: ${j.deadline}</div>
      <div class="job-dates">Posted Nov 1, 2026</div>
    </div>`).join('') + `</div>`);
}

function posting(j) {
  // The page tries to POST twice on load (a fetch and an auto-submitted form). The server must block both.
  return page(`${j.title} - NUworks`, `
    <h1 class="job-title">${j.title}</h1>
    <dl>
      <dt>Employer</dt><dd>${j.employer}</dd>
      <dt>Location</dt><dd>${j.location}</dd>
      <dt>Position Type</dt><dd>${j.type}</dd>
      <dt>Application Deadline</dt><dd>${j.deadline}</dd>
    </dl>
    <h2>Job Description</h2><p>Work with the analytics team on weekly reporting.</p>
    <h2>Qualifications</h2><p>Python and SQL. Second-year students or above.</p>
    <h2>Application Instructions</h2><p>Submit a resume and a cover letter through NUworks.</p>
    <h2>Documents Required</h2><p>Resume, Cover Letter</p>
    <p class="alert">Your applicant type does not match the applicant types for this job.</p>
    <form id="apply" method="post" action="/students/app/jobs/apply/${j.id}"><button type="submit">Apply</button></form>
    <script>
      fetch('/students/app/jobs/apply/${j.id}', {method: 'POST', body: 'x'}).catch(() => {});
      setTimeout(() => document.getElementById('apply').submit(), 50);
    </script>`);
}

// The live student app (seen on NUworks, 2026-11-14): rows have no link or id in the markup (they open by click), and the
// page loads its rows from /api/v2/jobs and a posting from /api/v3/jobs/<id> as JSON. The keyword "app" serves that shape.
const APP_JOBS = [
  { job_id: '0123456789abcdef0123456789abcdef', job_title: 'Data Engineering Co-Op', name: 'Example Data Corp', job_location: 'Boston, Massachusetts, United States',
    deadline: 'Dec 26, 2026', postdate: 'Oct 30, 2026', job_type: ['Co-op'], blind_flag: 0 },
  { job_id: 'fedcba9876543210fedcba9876543210', job_title: 'Analytics Co-Op', name: 'Sample Insights', job_location: 'Remote',
    deadline: 'Nov 20, 2026', postdate: 'Nov 2, 2026', job_type: ['Co-op'], blind_flag: 0 },
];
function appListing(keywords) {
  return page('Search Results', `<div class="list-items">` + APP_JOBS.map((j, i) => `
    <div id="list-item-${i}" role="link" class="list-item list_rows cursor-pointer"><div class="list-item-body">
      <div class="list-item-title"><span>${j.job_title}</span></div><div class="list-item-subtitle"><span>${j.name} - ${j.job_location}</span></div>
    </div></div>`).join('') + `</div>
    <script>fetch('/api/v2/jobs?keywords=${encodeURIComponent(keywords)}&page=1&json_mode=read_only').then((r) => r.json()).catch(() => {});</script>`);
}
function appPosting(j) {
  return page('Job Details', `<div class="job-pane"><h1>${j.job_title}</h1></div>
    <script>fetch('/api/v3/jobs/${j.job_id}').then((r) => r.json()).catch(() => {});</script>`);
}

export function startFixture() {
  const log = [];
  const server = http.createServer((req, res) => {
    log.push({ method: req.method, url: req.url });
    const u = new URL(req.url, 'http://x');
    const send = (code, html, headers = {}) => { res.writeHead(code, { 'content-type': 'text/html', ...headers }); res.end(html); };
    if (req.method !== 'GET') return send(200, page('Applied', '<h1>Applied</h1>'));
    if (u.pathname === '/students/' || u.pathname === '/students') return send(200, page('Home - NUworks', '<h1>Welcome back</h1>'));
    if (u.pathname === '/login') return send(200, page('Sign in', '<form><input name="u"><input type="password" name="p"></form>'));
    if (u.pathname === '/students/app/jobs/search') {
      const k = u.searchParams.get('keywords') || '';
      if (k === 'captcha') return send(200, page('Security check', '<h1>Are you a robot?</h1><div class="g-recaptcha"></div>'));
      if (k === 'error') return send(500, page('Error', '<h1>Error</h1><p>Something went wrong.</p>'));
      if (k === 'login') return send(302, '', { location: '/login?next=/students/' });
      if (u.searchParams.get('page') !== '1') return send(200, page('Jobs - NUworks', '<p>No jobs found</p>'));
      if (k === 'app') return send(200, appListing(k));
      return send(200, listing());
    }
    const json = (v) => { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(v)); };
    if (u.pathname === '/api/v2/jobs') return json({ perPage: 20, page: 1, total: APP_JOBS.length, models: APP_JOBS });
    const api = u.pathname.match(/^\/api\/v3\/jobs\/([0-9a-f]{32})$/);
    if (api) {
      const j = APP_JOBS.find((x) => x.job_id === api[1]);
      if (j) return json({ job_id: j.job_id, job_title: j.job_title, employer_name: j.name, job_location: j.job_location,
        job_type: [{ _id: 1, _label: 'Co-op' }], job_desc: '<p>Build data pipelines &amp; dashboards.</p><ul><li>Python</li><li>SQL</li></ul>',
        qualifications: '<p>Second-year students or above.</p>', application_deadline: 'December 26, 2026', workplace_type: { _id: 'h', _label: 'Hybrid' } });
    }
    const app = u.pathname.match(/^\/students\/app\/jobs\/detail\/([0-9a-f]{32})$/);
    if (app) { const j = APP_JOBS.find((x) => x.job_id === app[1]); if (j) return send(200, appPosting(j)); }
    const m = u.pathname.match(/^\/students\/app\/jobs\/detail\/([\w-]+)$/);
    if (m) { const j = JOBS.find((x) => x.id === m[1]); if (j) return send(200, posting(j)); }
    return send(404, page('Page not found', '<h1>Page not found</h1>'));
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => {
    const base = `http://127.0.0.1:${server.address().port}/students/`;
    resolve({ base, log, close: () => new Promise((r) => server.close(r)), nonGet: () => log.filter((l) => l.method !== 'GET') });
  }));
}
