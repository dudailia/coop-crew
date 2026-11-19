# Security and privacy

## What runs where

Everything runs on the student's own computer. Claude Code runs on the student's own Claude plan, signed in with their
Claude account; coop-crew uses no API keys and no server of its own.

| Part | Runs | Talks to |
|---|---|---|
| Claude Code and the agents | the student's machine | Anthropic (the conversation), and the public web pages the scouts and researcher read |
| `tools/*.py` | the student's machine, Python standard library | company job boards' public JSON APIs (read-only GETs) |
| Resume PDFs | Playwright's Chromium, locally, with all network requests blocked | nothing |
| jev-job-search (`vendor/jev/src`) | the student's machine, its own Chrome window | the application forms of approved roles |
| NUworks reader (`mcp/nuworks`) | the student's machine, a local stdio MCP server; off by default | NUworks only, read-only GETs, with the student's own session |
| Mail | Apple Mail on a Mac, or `.eml` files elsewhere | the student's own mail account (Mail sends, never this code over SMTP) |

## What is stored, and where

All of it under the repo folder, all of it gitignored, none of it uploaded by coop-crew:

- `profile/` (settings, facts, locks, voice, base resume), `assets/cv.pdf`
- `data/pipeline.sqlite` (roles, applications, emails, approvals, events), `data/incoming/`, `data/outbox/` (`.eml`)
- `data/nuworks-alerts/`, `data/nuworks-import/` (NUworks job-alert emails and postings the student saved)
- `data/nuworks/browser-profile/` and `data/nuworks/storage-state.json` (mode 600), only if the student turned the
  optional NUworks browser reader on: the browser session and its cookies. The password is never seen or stored by
  coop-crew: the student types it into NUworks's own sign-in page
- `out/<role>/` (postings, briefs, resumes, answers), `logs/`, the HTML and Markdown pages
- `vendor/jev/src/data/` (jev's copy of the profile)

No SMTP password, IMAP password, API key or token is stored anywhere. jev is fetched from a
pinned commit at install.

## What can act, and how it is stopped

- **Submitting a form:** only `tools/applicant.py submit`, only for ids the student approved (`/approve` or
  `APPROVE.txt`), after the gate passes, under the daily cap, after jev re-checks the open form. NUworks roles are never
  submitted by the crew.
- **Sending email:** only `tools/send_due.py`, only approved ids, in each region's send window, under the caps
  (5 applications, 10 emails a day by default; 40 emails a day at most). Prepare mode (the default) only saves drafts.
- **A guard hook** (`tools/guard.py`, PreToolUse on every agent tool call) blocks direct `jev submit`, AppleScript,
  approval writes, pipeline writes outside `tools/pipeline.py`, edits to the safety files, LinkedIn fetching and NUworks
  fetching outside its server.
- **Kill switch:** `/stop` creates `STOP` in the repo (or `touch ~/STOP-AGENTS`). Every tool exits, the guard blocks every
  acting tool call, schedules skip their run, and the NUworks server loads nothing. `/crew-resume` removes it.
- **Schedules** are off by default; the student installs them (`tools/schedule.py install`) and removes them
  (`tools/schedule.py uninstall`).

## How to stop everything

1. `/stop` in Claude Code (or `touch STOP` in the repo folder, or `touch ~/STOP-AGENTS`).
2. `python3 -I tools/schedule.py uninstall` removes the schedules.
3. `python3 -I tools/nuworks_enable.py off` turns the NUworks reader off.

## Reporting a problem

Open an issue without personal data, or contact the maintainer privately. Before every push, run
`python3 -I tools/pii_scan.py` (with a private pattern file outside the repo) and the test suite.
