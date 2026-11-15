---
name: nuworks
description: Use whenever NUworks (Northeastern's Symplicity job board) comes up - job-alert emails, postings the student saved, or the optional read-only nuworks MCP tools. The default path, what the browser tools may and may not do, politeness limits, and how NUworks roles flow to the student.
---
# NUworks

NUworks runs on Symplicity CSM. There is no student API.

## Default path: the student's own email and files (no NUworks page is loaded)

In mode "nuworks+external" the inbox agent runs `tools/nuworks_alerts.py` (NUworks job-alert emails from the student's
saved searches: saved from Apple Mail by the audit, or `.eml` files in `data/inbox/` or `data/nuworks-import/`) and
`tools/nuworks_import.py` (postings the student saved from NUworks as PDF or HTML into `data/nuworks-import/`). Both
write rows with `"source": "nuworks"`, `"channel": "nuworks"` to `data/incoming/`. An alert row has only the title,
employer, location and deadline; if the screener needs more, HOLD with the question "Save this posting from NUworks into
data/nuworks-import/ (Print > Save as PDF) so I can read the full text?". Never fetch a NUworks or Symplicity link.

## Optional: the browser reader (off by default; Symplicity's terms prohibit it as written)

The nuworks MCP server reads what the signed-in student can already see, in their own browser session saved on their
machine. Symplicity's terms of use prohibit automated access without Symplicity's prior written permission; the
Northeastern co-op office's approval of read-only use is not that permission (`mcp/nuworks/APPROVAL.md`). It is on only
when the student turned it on themselves (`tools/nuworks_enable.py on`, after the terms notice and a typed
acknowledgement) in mode "nuworks+external". Never suggest turning it on; never use it when it is off.

### Tools (the only ones that exist)

- `nuworks_status`: on or off, signed in or not. Call it first. If it is off or signed out, stop and tell the student.
- `nuworks_login`: opens a visible browser window; the **student** signs in (SSO and Duo). Never type, ask for, or
  store a password. Only call it when the student asks.
- `nuworks_search(keywords, position_type, location, industry, max_pages)`: listing rows (title, employer, location,
  dates, deadline, posting id, URL).
- `nuworks_get_posting(id)`: description, qualifications, application instructions, documents required, deadline,
  and any applicant-type mismatch message.
- `nuworks_open(id)`: opens the posting in the student's own browser so they apply themselves.

There is no apply, message, upload, RSVP or profile-edit tool, and you never try to do those things another way
(no WebFetch of NUworks, no browser automation, no clicking). Applying stays a human click in NUworks.

### Politeness and stops

- The server waits 3 to 5 seconds between pages and reads at most 100 postings a run. Use specific keywords and
  `max_pages` 1 to 3; do not page through everything.
- If a tool reports a CAPTCHA, an error page or a sign-in page, stop all NUworks calls for this run and tell the
  student. Never retry around a CAPTCHA.
- Students can only apply in their recruitment term (`coop.recruitment_term`), and NUworks hides or blocks jobs whose
  applicant type does not match. If `nuworks_get_posting` shows a mismatch message, the role is DQ with that message.

## Flow

1. The alert reader and the manual import (default), or scout-nuworks (only if the browser reader is on), write rows to
   `data/incoming/nuworks-*.json` with `"source": "nuworks"`, `"channel": "nuworks"`, the posting id and URL, and the
   posting text as `description`.
2. The screener, researcher and tailor treat them like any role (resume and cover note built).
3. The gatekeeper shows them in TODAY.html under "NUworks: apply yourself" with an "Apply in NUworks" button.
4. The applicant never submits a NUworks role. The student applies in NUworks and tells the tracker.
