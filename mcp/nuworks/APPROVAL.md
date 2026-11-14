# NUworks module approval

**Status: APPROVED by the Northeastern co-op office (advisor), 14 Nov 2026.**

**Scope of the approval:** read-only access to NUworks listings the student can already see, inside the student's own
signed-in session. No applying, messaging or uploading.

**The module stays opt-in, exactly as built.** It is off in every install: the installer adds it to
`disabledMcpjsonServers`, and the server refuses every call unless the student turns it on themselves
(`python3 -I tools/nuworks_enable.py on`, in sourcing mode "nuworks+external"). The rest of coop-crew does not need it.

## What was approved

A student-run, local, read-only tool that, inside the student's own signed-in NUworks session:

- reads job listing and posting pages the student can already see, at most one page every 3 to 5 seconds and at most
  100 postings per run, with a local cache;
- never applies, messages, uploads, RSVPs or edits a profile, and sends no form data (only GET requests; anything else
  the page tries is answered locally and never sent);
- never sees or stores the student's password (the student signs in in a visible window; SSO and Duo as usual);
- stops at once on a CAPTCHA, error page or sign-in redirect.

Any change that widens this scope (a new tool, a non-GET request, a higher rate or cap) needs a new approval.

## Record

| Field | Value |
|---|---|
| Approved on | 14 Nov 2026 |
| Approved by (office, role) | Northeastern co-op office, the maintainer's co-op advisor |
| Answer | Yes: read-only access to listings the student can already see; no apply, message or upload |
| Written record | Kept privately by the maintainer (not in this repo) |
| Terms-of-use check (NUworks / Symplicity clause, date read) | Not recorded yet |
| Decision | Approved; ships off by default, opt-in per student |
