---
name: nuworks
description: Use whenever reading NUworks (Northeastern's Symplicity job board) through the read-only nuworks MCP tools. What the tools may and may not do, politeness limits, and how NUworks roles flow to the student.
---
# NUworks (read-only)

NUworks runs on Symplicity CSM. There is no student API. The nuworks MCP server reads only what the signed-in student
can already see, in their own browser session saved on their machine. It is **off by default** and on only when the
student turned it on themselves (`tools/nuworks_enable.py on`) in mode "nuworks+external". The Northeastern co-op
office approved read-only access to listings the student can already see (`mcp/nuworks/APPROVAL.md`); stay inside that
scope.

## Tools (the only ones that exist)

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

## Politeness and stops

- The server waits 3 to 5 seconds between pages and reads at most 100 postings a run. Use specific keywords and
  `max_pages` 1 to 3; do not page through everything.
- If a tool reports a CAPTCHA, an error page or a sign-in page, stop all NUworks calls for this run and tell the
  student. Never retry around a CAPTCHA.
- Students can only apply in their recruitment term (`coop.recruitment_term`), and NUworks hides or blocks jobs whose
  applicant type does not match. If `nuworks_get_posting` shows a mismatch message, the role is DQ with that message.

## Flow

1. scout-nuworks writes rows to `data/incoming/nuworks-<date>.json` with `"source": "nuworks"`, `"channel": "nuworks"`,
   the posting id and URL, and the posting text as `description`.
2. The screener, researcher and tailor treat them like any role (resume and cover note built).
3. The gatekeeper shows them in TODAY.html under "NUworks: apply yourself" with an "Apply in NUworks" button.
4. The applicant never submits a NUworks role. The student applies in NUworks and tells the tracker.
