---
description: Approve applications or emails by id (from TODAY.html). The applicant then submits those forms; approved emails go out in their send window.
argument-hint: <id> [<id> ...]
disable-model-invocation: true
---
!`python3 -I tools/approve.py '$ARGUMENTS' || true`

The student approved the ids above (the lines say what was recorded; a line saying "NOT approved" was not).

- For each id recorded as an approved application whose next step says the applicant submits it: delegate to the
  **applicant** with exactly those ids: `python3 -I tools/applicant.py submit <ids>`. No other ids.
- Approved emails need nothing now: `tools/send_due.py` drafts or sends them in their window (the schedule or the next
  /run). Approved LinkedIn notes and NUworks roles are the student's to send or apply.
- Then run `python3 -I tools/build_today.py` and report each result line to the student. If a role was submitted, ask
  whether they made heavy edits, and set clean_pass with
  `python3 -I tools/pipeline.py set <id> clean_pass=yes|no --why "<their answer>"`.
