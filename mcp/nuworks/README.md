# nuworks-mcp: the optional NUworks browser reader (read-only, off by default)

> **Use the default NUworks path first.** coop-crew reads NUworks through your own email and your own saved files, and
> never loads a NUworks page that way:
>
> 1. **Job-alert emails.** In NUworks, save a search and turn on its email alerts (NUworks calls them search agents).
>    The inbox agent reads those emails (`tools/nuworks_alerts.py`) and adds each posting to the pipeline as a NUworks
>    role. On a Mac it finds them in Apple Mail; elsewhere, save them as `.eml` into `data/inbox/`.
> 2. **Manual import.** Open a posting in NUworks and save it into `data/nuworks-import/` (Print > Save as PDF, or Save
>    Page As). `tools/nuworks_import.py` (run by the inbox agent) reads it, so the screener and tailor get the full text.
>
> Both are on in sourcing mode "nuworks+external". You always apply in NUworks yourself.

This folder is the other way: a local MCP server that drives a browser, signed in as you, through NUworks listings and
postings. It runs on your machine over stdio, through Playwright and a browser profile kept in
`data/nuworks/browser-profile`. NUworks runs on Symplicity CSM, which has no student API.

## Read this before you turn it on: Symplicity's terms of use

NUworks runs on Symplicity CSM. Symplicity's published terms of use (quoted from
[symplicity-mea.com/TermOfService](https://www.symplicity-mea.com/TermOfService); read the current US terms, linked at
the foot of every NUworks page, at [symplicity.com/support/terms-of-use](https://www.symplicity.com/support/terms-of-use))
say you may not:

> "use or attempt to use engines, manual or automated software, tools, devices, agents, scripts robots or other means,
> devices, mechanisms or processes (including, but not limited to, browsers, spiders, robots, avatars or intelligent
> agents) to navigate, search, access, "scrape," "crawl," or "spider" any web pages or any services provided on the
> Sites other than the search engine and search agents available from Symplicity [...] and other than generally
> available third party web browsers"

> "collect users' content or information, or otherwise access the Site, using automated means (such as harvesting bots,
> robots, spiders, or scrapers) without our prior permission"

This reader is automated access, however slow and read-only. The Northeastern co-op office approved read-only use
(14 Nov 2026), but that is not Symplicity's permission, and using the reader may breach those terms and put your NUworks
account at risk. The full record, with Northeastern's IT policy, is in [APPROVAL.md](APPROVAL.md). **Status: kept in the
repo, off by default in every install, opt-in per student after this notice.**

## Turn it on (your choice) and off

1. `/setup` sets sourcing mode "nuworks+external" (the default NUworks path needs only this).
2. In Claude Code type `! python3 -I tools/nuworks_enable.py on` (or run it in a terminal). It prints the notice above
   and turns the reader on only if you type exactly: **I have read the Symplicity terms and accept the risk**. The date
   and the wording go in your profile. Agents cannot run it for you.
3. Restart Claude Code, approve the `nuworks` server, and ask for `nuworks_login`. Sign in yourself in the window.

`python3 -I tools/nuworks_enable.py off` turns it off again (and takes `nuworks` out of `enabledMcpjsonServers`);
`python3 -I tools/nuworks_enable.py notice` prints the notice.

## Tools (exactly five)

| Tool | What it does |
|---|---|
| `nuworks_login` | Opens a **visible** browser window at NUworks. You sign in yourself (SSO and Duo). The server never sees, types or stores your password. It keeps the browser session on disk (the profile, plus its cookies in `data/nuworks/storage-state.json`, mode 600). |
| `nuworks_status` | Says whether the module is enabled and whether the saved session is signed in. |
| `nuworks_search(keywords, position_type, location, industry, max_pages)` | Reads listing pages and returns rows: title, employer, location, dates, deadline, posting_id, url, position_type. |
| `nuworks_get_posting(id)` | Returns one posting: description, qualifications, application instructions, documents required, deadline, workplace, dates, pay, and any applicant-type mismatch message. |
| `nuworks_open(id)` | Opens that posting in **your own** browser (`open` on macOS, `wslview` on WSL, `xdg-open` on Linux), so you apply yourself. |

There are no apply, message, upload, RSVP or profile-edit tools. Applying stays a human click in NUworks.

## Rules enforced in the code (`server.mjs`)

- **Gate.** Every tool except `nuworks_status` refuses unless `profile/settings.json` has `"mode": "nuworks+external"`
  and `"nuworks": {"enabled": true}`. The file is read again on every call.
- **Read-only.** Headless runs answer every request that is not a GET (form posts, fetch POSTs, analytics) locally with
  an empty 204, so it never leaves the machine, and block every page navigation off the NUworks host. The server never
  clicks or types anything.
- **Politeness.** One page load every 3 to 5 seconds. At most 100 postings per run (one server process). Postings are
  cached in `data/nuworks/cache/` for 24 hours.
- **Stop.** A CAPTCHA or bot check, an error page (HTTP 400 or above, or an error title), or a redirect to a sign-in
  page stops the run. Every later call in that run refuses. The kill switch (`STOP` in the state folder, or
  `~/STOP-AGENTS`) stops every page load.
- **Sign-in.** During `nuworks_login` the window is yours: the server waits until it sees signed-in NUworks pages
  (no password field, a sign-out link or the student app) three checks in a row.

`position_type`, `location` and `industry` filter the rows that were read. `keywords` goes into the NUworks search URL.

## How it reads the live site (checked 14 Nov 2026, acceptance test 7)

The student app is an Angular app. Its listing rows carry no posting link or id in the markup (a row opens its posting
by click), so the server takes the rows from the JSON the page itself loads, `/api/v2/jobs?keywords=...&page=N`, and a
posting from `/api/v3/jobs/<id>`, as the page receives them: no extra request and no click. `extractListing` and
`extractPosting` in `parse.mjs` parse the markup when that data does not arrive (older `index.php` pages). The live
check: sign-in, status, a search for "data" (20 rows, 18 co-ops) and a posting read all passed; 34 analytics POSTs were
answered locally and none was sent. If NUworks changes, adjust only `parse.mjs` and the path variables below.

This Node server does not take the shared `logs/night.lock` that the Python tools use for Mail and the browser. The
conductor must not run it at the same time as an applicant (JEV) run.

## Configuration (environment)

| Variable | Default | Use |
|---|---|---|
| `COOP_STATE` | repo root | where `profile/`, `data/` and `logs/` are |
| `NUWORKS_BASE_URL` | `https://northeastern-csm.symplicity.com/students/` | NUworks student site |
| `NUWORKS_SEARCH_PATH` | `app/jobs/search?keywords={keywords}&page={page}` | listing URL, relative to the base |
| `NUWORKS_POSTING_PATH` | `app/jobs/detail/{id}` | posting URL, used when the search did not give one |
| `NUWORKS_API_GRACE_MS` | 6000 | after a page loads, how long to wait for its own data before parsing the markup |
| `NUWORKS_DELAY_MS`, `NUWORKS_MAX_POSTINGS`, `NUWORKS_TEST_SIGNED_IN`, `NUWORKS_DRY_OPEN` | | tests only. `NUWORKS_MAX_POSTINGS` can only lower the cap of 100. |

## Tests

`npm run test:nuworks` runs the server over stdio against a local fixture (`test/fixture.mjs`) and never contacts
Northeastern. It checks:

- the tool list is exactly the five tools
- the gate holds
- search and posting fields are returned, from the markup and, like the live student app, from the page's own JSON
- the cache is used
- no POST gets through
- a CAPTCHA, an error page or a sign-in redirect stops the run
- the postings cap holds
- the kill switch stops every load

The default path is tested in `tests/test_acceptance.py` (`NUworks_DefaultPath`): alert emails become NUworks rows,
saved HTML and PDF postings are imported or fill a role's full text, and both stay off outside "nuworks+external".
