---
name: outreach-rules
description: Use before planning, drafting, scheduling or following up any cold email or LinkedIn note to an employer. Send windows, caps, follow-up timing, honesty rules, published-address-only, one email per person, and the email format the checker enforces.
---
# Outreach rules

From the fintech-outreach-eu system and job-agents-kit, for coop-crew. The checker (`tools/check_msgs.py`) and the
sender (`tools/send_due.py`) enforce most of this in code; this skill is how to write drafts that pass.

## What outreach is for

- KEEP roles with no application form (the posting says "email us"), and strong-fit targets with no posting.
- One named person per company, found with a source you can cite. A missing person never blocks an application.

## Honesty (hard rules)

1. **Facts only from `profile/facts.md`.** Every number and every name must be there or on the employer's own page you
   read. The checker fails anything else. If a sentence needs a fact you do not have, leave the sentence out.
2. **Availability** is `coop.availability`, word for word. **Work authorization** is the profile sentence for that
   country, word for word, and only if `work_auth.<country>.include_in_email` is true. Never stronger than the profile.
3. **Addresses only if published** verbatim on the company's own site, team page, a press release, a conference page, or
   the person's own site or GitHub. Record the exact page in `source_url`. Never guess or construct an address, never
   use email-finder sites (RocketReach, Apollo, Hunter, ContactOut, SignalHire and the like), never buy one. A generic
   address (careers@, jobs@, talent@) is acceptable only from the company's own site.
4. **LinkedIn:** a person needs a verified profile URL (the company's site links it, or a reputable page names them in
   that role). No LinkedIn automation of any kind: the student sends notes by hand. Never fetch linkedin.com.
5. **Anti-collision:** at most one email per person, ever, across all of a student's outreach (the pipeline refuses a
   second). Write something specific to that person and company, from their own page, so a hundred students using this
   tool never send the same template to the same founder.
6. If an application or a reply asks the student to confirm the text is their own work written without AI, do not
   draft it; flag it to the student.

## Format (the checker's rules, from `profile/settings.json` writing)

- Salutation `Hi <FirstName>,` (or Hello/Dear) with the person's real first name, never an inbox word ("Hi Team" fails
  unless no person is named and the address is generic; then use "Hi <Company> team,").
- At most `writing.max_words` words (default 170) above the sign-off. Short paragraphs: who you are (one line from
  facts), the one specific reason this company (from their own page), what you ask (a co-op for the stated dates),
  availability, the opt-out line, then the sign-off and the full name.
- The opt-out line, word for word: `writing.opt_out_line`.
- No em dashes. No banned words (`writing.banned`). The student's spelling (US or UK).
- Subject: plain, under 8 words, says what it is ("Spring 2027 co-op: data engineering").
- Follow-up: same salutation, at most 2 lines, then the sign-off; its own subject ("Re: <subject>").
- The anti-slop skill runs on every draft (editor agent, embedded mode).

## Draft file format

Write drafts as a JSON list to `data/incoming/emails-<date>.json`, then run `python3 -I tools/plan_emails.py`:

```json
[{"id": "acme-1", "role_id": "<role id or empty>", "company": "Acme", "person": "Sam Lee", "to": "sam@example.com",
  "domains": ["example.com"], "source_url": "https://example.com/team", "region": "Boston",
  "subject": "...", "body": "...", "followup_subject": "Re: ...", "followup_body": "..."},
 {"id": "acme-li-1", "kind": "linkedin", "company": "Acme", "person": "Sam Lee",
  "profile_url": "https://www.linkedin.com/in/...", "body": "note under 300 characters"}]
```

## Timing (enforced by the planner and the sender)

- Send windows: weekdays, inside the recipient region's window (default 08:00 to 08:50 local time), at least
  `send.gap_minutes` apart, a second person at the same company on a later day.
- Caps: `limits.emails_per_day` (default 10) counting follow-ups; hard maximum 40 a day whatever the settings say;
  `send.per_run` per sender run.
- Follow-up: one per company, `send.follow_up_working_days` (5 to 7, default 6) working days after the first email was
  sent, same local time, cancelled by any reply from that company (the inbox marks replies).
- Prepare mode by default: approved emails are saved as drafts (Mail Drafts on a Mac, `.eml` files elsewhere) and the
  student sends them. Only approved ids are ever drafted or sent: `/approve <id>`.
- The kill switch (`/stop`) stops the sender at once.
