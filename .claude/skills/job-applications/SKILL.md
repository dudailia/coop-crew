---
name: job-applications
description: >-
  Use when you find or judge a role, build a resume or packet, fill a portal,
  run the review gate, submit, log an application, or follow up. House how-to
  for the application pipeline. Facts and numbers live in the student's own
  profile (profile/facts.md is the proof bank, profile/locks.md the locks).
---
# Job applications

One shared how-to for the application path. Adapted for coop-crew from the job-applications skill by its original
author (credit and license pending, see THIRD_PARTY.md).
Facts, locks, and numbers live in the student's `profile/`. Load this skill for the path; read the named files for the rules.
In this file "the student" is the owner: the person whose name goes on every application.

## Path

1. Find a role. Sweep company-run boards and company sites (`docs/rules/sources.md`). NUworks roles come only through the read-only nuworks server (nuworks skill).
2. Judge it KEEP, HOLD, or DQ against `profile/settings.json` (targets, cycle dates, work_auth, pay floor) and `profile/locks.md`. Run `python3 -I tools/screen_rules.py` first: it applies the hard rules in code. Record your verdict with `python3 -I tools/pipeline.py verdict <id> KEEP|HOLD|DQ --reason "..." [--question "..."]`. Channel choice is in `docs/rules/channel-mix.md`.
3. Before writing the resume, cover note, or Company brief, pull the portal's required questions into `out/<id>/questions.json` (`[{"label": "...", "required": true, "hint": "..."}]`). If a required question conflicts with a lock (office days that conflict with a commute or location lock, citizenship-only, and similar), stop: HOLD the role with the verbatim question for the student. Do not build the packet until the student says to proceed or to drop the role. A posting that says remote does not override a required office-days question; ask the student.
4. Write a Company brief (`out/<id>/brief.md`), then build the one-page packet (`docs/rules/resume-and-apply.md`, base resume `profile/resume.md`).
5. Pull every portal field the form asks for. Writing (essays and any cover note) goes to the student for review in TODAY.html before the live form is filled. The form is filled once, after that writing is approved.
6. Try to find one named person and, if a verified work email is published, draft one short note for the student to review with the application (`out/<id>/person.md`). Do not enrich a long backup list. Do not write a general research memo on outreach methods. A missing name does not block submit after review. See the outreach-rules skill.
7. Log every field verbatim in `out/<id>/field-log.md`, including blanks with a reason (`| Field | Value | Source |`). The review pack is: new writing, soft flags (`out/<id>/soft-flags.md`), the named-person draft, and one filled-from-locks list (field-log rows whose source is profile or locks).
8. Submit only after the student approves that exact application (`/approve <id>`). Only `tools/applicant.py submit` submits, and it checks the approval itself.
9. Right after submit, the pipeline row is updated by the applicant tool. Set `clean_pass` once the student says whether they made heavy edits. Check dues.
10. Draft the follow-up for the student. Put it in the morning pack. Nothing is auto-sent.

Each weekday, aim for one batch of up to `limits.applications_per_day` applications (default 5) in TODAY.html by the morning. If a sweep finds no fresh KEEP roles, put older candidates that pass pay and place in the pack as one yes-or-no list. Named-person drafts, outreach drafts, and follow-up drafts go in the same pack. Nothing is auto-sent.
Public portfolio work is not a submit gate; cite only already-public work that is in `profile/facts.md`.
Durable do and don't lessons live in `profile/lessons.md` (the student's, if they keep one). The end-to-end path is in `docs/architecture.md`.

## Find and fill

This is the scouts' and the applicant's work: find roles, fill forms, submit after approval, follow up, and log. Do not rewrite packets.
Never use LinkedIn Jobs or job aggregators, and never scrape behind a login (the student's own NUworks session through the nuworks server is the one exception). Stop at site checkpoints (CAPTCHA, sign-in).
Do not invent salary or details the posting did not show. Standing answers and soft-flag cases are in the form-answers skill and `profile/locks.md`.
Draft follow-ups for the morning pack; the student sends them.
Do not start another full-board sweep while a role is still in writing or in the student's review, unless the list of fresh KEEP roles is empty.

## Build the packet

This is the tailor's work: a one-page ATS PDF and the answers the portal actually asks for, built on demand for one role. Do not submit or pick roles.
The Company brief is 3 to 6 short bullets from the posting and the company site. Do not write a research memo. Deep company research waits until an interview.
Write a cover note only when the portal has a cover-letter field, or when the student asked for one.
Cover letters and answers fill the posting's stated needs in the posting's own order, linear like the resume. Add only what helps the reader. Do not add tooling, subscription, or skill-list lines the posting did not ask for.
Reweight proof-bank bullets to the posting's top problems. Never invent claims.
Build the PDF with `python3 -I tools/resume.py <id>`: it fails unless the PDF is exactly one page and every number and name is in the facts or the posting. Run the anti-slop pass (editor) before handoff.

## Check gates

This is the gatekeeper's work: check gates. Do not source roles, write packets, or submit.
Do not clear a packet that is missing a Company brief, has blank required answers, or is missing a verbatim field log. `python3 -I tools/gate.py <id>` checks this in code and sets the role to ready or blocked.
A ready packet or a gate check is not permission to submit. Check the pipeline for dues at the start of work (`python3 -I tools/pipeline.py dues`).

## ATS resume

Follow `docs/rules/resume-and-apply.md`. Locked there, and carried here so the packet matches:

- One page, text only, single column. No tables, graphics, icons, or header-footer content.
- Section order: the student's name, the posting's exact job title, contact line with GitHub, Summary, Skills, Experience, Projects, Education.
- Centered Option A header: name, a thin rule, then one centered middot contact line that includes GitHub. No labeled Location, Cell, Email, or LinkedIn stack. (`templates/resume/resume.html`.)
- Summary is 2 to 3 lines.
- Body is black and gray only, about 10 point. The build fails if the PDF is not exactly one page.
- Do not use a left-label two-column body or a vertical-rule layout.
- Every claim comes from `profile/facts.md`. Quantify impact. No hidden text. No banned language. No colon in application writing.
- Fine-tune to the posting. Do not keyword-stuff or costume the posting.

## Review gate

Submit only after the student approves that exact application.
The gate holds until at least five applications in a row need no heavy edits, and it stays after that until the student relaxes it.
A clean pass means no heavy edits. After submit, set `clean_pass` to yes or no: `python3 -I tools/pipeline.py set <id> clean_pass=yes --why "student approved with no heavy edits"`. The live streak (`pipeline.py streak`) is the count of consecutive yes values at the end of the submitted list. A no or a blank at the end means the streak is 0.
A named hiring manager, founder, or recruiter is useful for a same-day note, but a missing name does not block submit after review.

## Pipeline

The only application record is `data/pipeline.sqlite`, changed only through `tools/pipeline.py` (every change is an event). How-to: `docs/pipeline.md`.

```
python3 -I tools/pipeline.py import                       # scouts' files in data/incoming/
python3 -I tools/pipeline.py verdict <id> KEEP --reason "..."
python3 -I tools/pipeline.py status <id> researched --why "brief written"
python3 -I tools/pipeline.py set <id> clean_pass=yes --why "..."
python3 -I tools/pipeline.py streak | dues
```
A form that was clicked but not confirmed is marked unconfirmed by the applicant tool. Confirm it after the student checks.
On a reply, interview, or rejection, update the stage with a `--why` that names the email.
A dues check reports follow-ups and changes nothing. The pipeline never sends email.

## Where the rules live (formerly knowledge pages)

- Find: `docs/rules/sources.md`, `profile/settings.json` targets, `docs/rules/channel-mix.md`
- Judge: `profile/settings.json` (targets, coop, work_auth), `profile/locks.md`, `docs/rules/soft-flags.md`
- Packet: `docs/rules/resume-and-apply.md`, `profile/resume.md`, `profile/facts.md`
- Outreach: the outreach-rules skill
- Path and log: `docs/architecture.md`, `docs/pipeline.md`, `profile/lessons.md`
