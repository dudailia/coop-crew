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
      return send(200, listing());
    }
    const m = u.pathname.match(/^\/students\/app\/jobs\/detail\/([\w-]+)$/);
    if (m) { const j = JOBS.find((x) => x.id === m[1]); if (j) return send(200, posting(j)); }
    return send(404, page('Page not found', '<h1>Page not found</h1>'));
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => {
    const base = `http://127.0.0.1:${server.address().port}/students/`;
    resolve({ base, log, close: () => new Promise((r) => server.close(r)), nonGet: () => log.filter((l) => l.method !== 'GET') });
  }));
}
