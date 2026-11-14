# nuworks-mcp (read-only, opt-in)

A local MCP server that reads NUworks job listings the student can already see. It runs on the student's own machine
over stdio, through Playwright and a browser profile kept in `data/nuworks/browser-profile`. NUworks runs on Symplicity
CSM, which has no student API.

**Status: approved, off by default.** The Northeastern co-op office approved read-only access to listings the
student can already see (14 Nov 2026; `APPROVAL.md`). It stays off in every install until the student turns it on with
`python3 -I tools/nuworks_enable.py on`.

## Tools (exactly five)

| Tool | What it does |
|---|---|
| `nuworks_login` | Opens a **visible** browser window at NUworks. You sign in yourself (SSO and Duo). The server never sees, types or stores your password. It keeps only the browser session on disk. |
| `nuworks_status` | Says whether the module is enabled and whether the saved session is signed in. |
| `nuworks_search(keywords, position_type, location, industry, max_pages)` | Reads listing pages and returns rows: title, employer, location, dates, deadline, posting_id, url. |
| `nuworks_get_posting(id)` | Returns one posting: description, qualifications, application instructions, documents required, deadline, and any applicant-type mismatch message. |
| `nuworks_open(id)` | Opens that posting in **your own** browser (`open` on macOS, `wslview` on WSL, `xdg-open` on Linux), so you apply yourself. |

There are no apply, message, upload, RSVP or profile-edit tools. Applying stays a human click in NUworks.

## Rules enforced in the code (`server.mjs`)

- **Gate.** Every tool except `nuworks_status` refuses unless `profile/settings.json` has `"mode": "nuworks+external"`
  and `"nuworks": {"enabled": true}`. The file is read again on every call.
- **Read-only.** Headless runs abort every request that is not a GET (form posts, fetch POSTs), and every page
  navigation off the NUworks host. The server never clicks anything. The test fixture's posting page tries to POST twice
  on load, and the tests check that nothing reaches the server.
- **Politeness.** One page load every 3 to 5 seconds. At most 100 postings per run (one server process). Postings are
  cached in `data/nuworks/cache/` for 24 hours.
- **Stop.** A CAPTCHA or bot check, an error page (HTTP 400 or above, or an error title), or a redirect to a sign-in
  page stops the run. Every later call in that run refuses. The kill switch (`STOP` in the state folder, or
  `~/STOP-AGENTS`) stops every page load.
- **Sign-in.** During `nuworks_login` the window is yours: the server only waits for you to land back on NUworks.

`position_type`, `location` and `industry` filter the rows that were read. `keywords` goes into the NUworks search URL.

## Enable it (after the OK in APPROVAL.md)

1. In `profile/settings.json`: `"mode": "nuworks+external"` and `"nuworks": {"enabled": true}`. `/setup` asks about this.
2. Remove `nuworks` from `disabledMcpjsonServers` in `.claude/settings.local.json`. The installer puts it there.
3. Restart Claude Code, approve the `nuworks` server, and ask for `nuworks_login`.

## Configuration (environment)

| Variable | Default | Use |
|---|---|---|
| `COOP_STATE` | repo root | where `profile/`, `data/` and `logs/` are |
| `NUWORKS_BASE_URL` | `https://northeastern-csm.symplicity.com/students/` | NUworks student site |
| `NUWORKS_SEARCH_PATH` | `app/jobs/search?keywords={keywords}&page={page}` | listing URL, relative to the base |
| `NUWORKS_POSTING_PATH` | `app/jobs/detail/{id}` | posting URL, used when the search did not give one |
| `NUWORKS_DELAY_MS`, `NUWORKS_MAX_POSTINGS`, `NUWORKS_TEST_SIGNED_IN`, `NUWORKS_DRY_OPEN` | | tests only. `NUWORKS_MAX_POSTINGS` can only lower the cap of 100. |

## Not yet verified on the live site

The listing and posting selectors in `parse.mjs` and the search and posting URL patterns were written without a
NUworks login, against the public shape of Symplicity CSM. Acceptance test 7 must check them on a real, signed-in
session:

- the visible login works
- a search returns rows with the right fields
- a posting returns its fields
- the student app does not need a non-GET request just to list jobs (if it does, listing will fail closed, and the read-only rule must not be relaxed without the co-op office's OK)

Adjust only `parse.mjs` and the two path variables.

This Node server does not take the shared `logs/night.lock` that the Python tools use for Mail and the browser. The
conductor must not run it at the same time as an applicant (JEV) run.

## Tests

`npm run test:nuworks` runs the server over stdio against a local fixture (`test/fixture.mjs`) and never contacts
Northeastern. It checks:

- the tool list is exactly the five tools
- the gate holds
- search and posting fields are returned
- the cache is used
- no POST gets through
- a CAPTCHA, an error page or a sign-in redirect stops the run
- the postings cap holds
- the kill switch stops every load
