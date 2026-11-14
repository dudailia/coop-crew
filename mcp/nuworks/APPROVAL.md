# NUworks module approval

**Status: NOT APPROVED. The module ships disabled.**

Until the answer below is recorded as yes, `nuworks-mcp` stays off in every install. The installer adds it to
`disabledMcpjsonServers`, and the server refuses every call unless the student's settings enable it. The rest of coop-crew
does not need it.

## What to ask

Ask for written permission (email is fine) for a student-run, local, read-only tool that, inside the student's own
signed-in NUworks session:

- reads job listing and posting pages the student can already see, at most one page every 3 to 5 seconds and at most
  100 postings per run, with a local cache;
- never applies, messages, uploads, RSVPs or edits a profile, and sends no form data (only GET requests);
- never sees or stores the student's password (the student signs in in a visible window; SSO and Duo as usual);
- stops at once on a CAPTCHA, error page or sign-in redirect.

Also ask whether this is consistent with the NUworks and Symplicity terms of use, or whether the office prefers that
students read NUworks only by hand.

## Whom to ask

- Northeastern Cooperative Education / Employer Engagement and Career Design (the co-op office), through the student's
  co-op coordinator.
- Northeastern IT Services (information security), about automated access to a university-licensed system.
- Optional: Symplicity's terms of use for CSM student users. Read them and record the clause that applies.

## Where to record the answer

Fill in this section and commit it with the change that enables the module.

| Field | Value |
|---|---|
| Asked on | |
| Asked whom (office, role) | |
| Answer (yes / no / conditions) | |
| Written record (where the email is kept, not the email itself) | |
| Terms-of-use check (clause, date read) | |
| Decision | disabled |

If the answer is no, leave the module disabled and keep this file as the note that explains why.
