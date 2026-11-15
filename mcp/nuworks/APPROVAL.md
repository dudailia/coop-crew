# NUworks: approval, terms of use, and what coop-crew does

**Default NUworks path: job-alert emails and postings the student saves. Neither loads a NUworks page.**
**The browser reader (this folder) is optional, off by default, and conflicts with Symplicity's terms as written.**

| | Default path | Browser reader (`mcp/nuworks`) |
|---|---|---|
| What it reads | NUworks job-alert emails in the student's own mail, and postings the student saved from NUworks (PDF, HTML) into `data/nuworks-import/` | NUworks listing and posting pages, in a browser signed in as the student |
| Tools | `tools/nuworks_alerts.py` (run by the inbox agent), `tools/nuworks_import.py` | the read-only `nuworks` MCP server |
| Automated access to NUworks | none | yes: read-only GETs, 3 to 5 s apart, at most 100 postings a run |
| On by default | yes, in sourcing mode "nuworks+external" | no: the student turns it on with `tools/nuworks_enable.py on`, after a terms notice and a typed acknowledgement |

## 1. Co-op office approval

**Approved by the Northeastern co-op office (the maintainer's co-op advisor), 14 Nov 2026**, for read-only access to
NUworks listings the student can already see, inside the student's own signed-in session. No applying, messaging or
uploading.

| Field | Value |
|---|---|
| Approved on | 14 Nov 2026 |
| Approved by (office, role) | Northeastern co-op office, the maintainer's co-op advisor |
| Answer | Yes: read-only access to listings the student can already see; no apply, message or upload |
| Written record | Kept privately by the maintainer (not in this repo) |

Scope of what was approved (the browser reader as built): it reads job listing and posting pages the student can already
see, at most one page every 3 to 5 seconds and at most 100 postings per run, with a local cache; never applies,
messages, uploads, RSVPs or edits a profile, and sends no form data (GET requests only; anything else the page tries is
answered locally and never sent); never sees or stores the password (the student signs in in a visible window; SSO and
Duo as usual); stops at once on a CAPTCHA, error page or sign-in redirect. Any change that widens this scope (a new
tool, a non-GET request, a higher rate or cap) needs a new approval.

## 2. Terms of use check (14 Nov 2026)

**Finding: Symplicity's terms of use prohibit automated access to the site without Symplicity's prior written
permission. The co-op office's approval is not Symplicity's permission.** Northeastern's own IT policy is ambiguous for
this use, and there are no NUworks-specific terms.

### Symplicity (the company that runs NUworks)

- US terms: https://www.symplicity.com/support/terms-of-use, linked from the foot of every NUworks page. **Not read in
  full for this check**: the project's guard blocks fetching `symplicity.com`. Search-engine extracts of the page show
  the same clauses as the regional terms below. The student or maintainer should read the US page by hand and note its
  date here.
- Regional terms, same template, read in full: https://www.symplicity-mea.com/TermOfService ("Effective May 1, 2019",
  Symplicity MEA Corporation). Verbatim:
  - "This license is for the sole purpose of enabling you to use the Site as provided by Symplicity, in the manner
    permitted by these Terms. [...] and for only non-commercial use, and may not be utilized for any aggregation,
    collecting or posting of job posting/listing information on any other web site or in any other media or manner
    whatsoever."
  - "(f) use or attempt to use engines, manual or automated software, tools, devices, agents, scripts robots or other
    means, devices, mechanisms or processes (including, but not limited to, browsers, spiders, robots, avatars or
    intelligent agents) to navigate, search, access, “scrape,” “crawl,” or “spider” any web pages or any services
    provided on the Sites other than the search engine and search agents available from Symplicity MEA on the Site and
    other than generally available third party web browsers (e.g., Internet Explorer, Firefox, Safari)"
  - "(f) collect users’ content or information, or otherwise access the Site, using automated means (such as harvesting
    bots, robots, spiders, or scrapers) without our prior permission"
  - "if there is a conflict between the Terms of Use and Privacy Policies and the Symplicity MEA software license
    agreement, then the Symplicity MEA software license agreement will control for that conflict." (The university's
    license agreement with Symplicity is not public.)
- Reading: a script driving a browser is "automated software" used to "navigate, search, access" the site; the
  exception covers ordinary web browsers and Symplicity's own "search agents" (the saved searches that send job-alert
  emails). Slow, read-only, personal use has no exception. **Prohibited as written, unless Symplicity gives prior
  written permission.**

### Northeastern

- Policy 700, "Policy on Acceptable Use of IT Systems and Resources": https://policies.northeastern.edu/policy700/
  ("Last Revision Date: June 22, 2026"). No clause on bots or scrapers. Relevant lines, verbatim: users may not
  "Attempt to access and/or access information systems and/or resources for which authority has not been explicitly
  granted by the system owner(s);" or "Manipulate or tamper with uniform resource locators (URLs);" and "If there is a
  question as to whether a specific use is appropriate or acceptable under this policy, users are responsible for
  obtaining clarification from the Office of Information Security". **Ambiguous** for this use; the Office of
  Information Security can settle it in writing.
- No NUworks-specific terms were found. https://careers.northeastern.edu/terms-of-service/ covers the Career Design
  website (run by uConnect), not NUworks.

## 3. Decision

1. **Default path, no automated access to NUworks**: Symplicity's own "search agents" email new postings; the inbox
   agent reads those emails from the student's mail (`tools/nuworks_alerts.py`), and the student can save any posting
   from NUworks as a PDF or web page into `data/nuworks-import/` (`tools/nuworks_import.py`). Both are on in sourcing
   mode "nuworks+external". Applying always stays a human click in NUworks.
2. **Browser reader kept, off by default**: it ships disabled (`disabledMcpjsonServers`, and the server refuses every
   tool unless the profile enables it). `tools/nuworks_enable.py on` shows the notice with the quotes above and needs the
   student to type "I have read the Symplicity terms and accept the risk"; the date and wording go in the profile.
3. To make the browser reader a supported default, get **Symplicity's prior written permission** (ideally confirmed by
   Northeastern's Office of Information Security or Career Design) and record it here.

## 4. Live check (acceptance test 7), 14 Nov 2026

Run on the maintainer's own NUworks account, in a throwaway state folder outside the repo that was deleted afterwards
(session, cache and pages); NUworks was turned off again at the end. The account can browse but not apply.

| Check | Result |
|---|---|
| `nuworks_login`: student signs in in a visible window | PASS after two fixes: the sign-in check now waits for signed-in pages 3 times in a row (the form is drawn by JavaScript, so "no password field yet" had passed too early), and the session cookies are saved at sign-in and loaded into each later browser (Chromium drops session-only cookies when it closes) |
| `nuworks_status` | PASS: signed in |
| `nuworks_search` "data", 1 page | PASS after a fix: 20 rows (18 co-ops) with title, employer, location, deadline, id. The student app's rows have no link or id in the markup (they open by click), so rows now come from the JSON the page itself loads (`/api/v2/jobs`), with the markup parser as fallback |
| `nuworks_get_posting` | PASS: description, qualifications, deadline, workplace (from `/api/v3/jobs/<id>`, loaded by the page) |
| Nothing clicked, no non-GET request sent | PASS: 34 analytics POSTs answered locally, none sent |
