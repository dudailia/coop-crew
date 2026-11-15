# coop-crew: setup guide

From zero to your first review pack. Extended from job-agents-kit's guide for Claude Code agents, co-op cycles and
NUworks.

It works in **prepare mode**: every application is prepared and every email drafted, and nothing is submitted or sent
until you approve that exact item.

## What you need

| Item | Cost | Notes |
|---|---|---|
| A Mac, Linux, or Windows with WSL | Free | On Windows, `install.ps1` runs everything inside WSL (Ubuntu) |
| Python 3.9+ and git | Free | Mac: `xcode-select --install`. Ubuntu/WSL: `sudo apt install python3 git` |
| Node.js 18+ (22+ for the form filler) | Free | nodejs.org or `nvm install 22` |
| Claude Code with a paid Claude plan (Pro or Max) | Plan price | claude.com/claude-code. Signed in with your Claude account; no API key |
| Your CV as a PDF | | The version you want employers to see |
| Apple Mail (Mac only, optional) | Free | Otherwise outreach writes `.eml` drafts you send from your own client |

About 30 minutes, most of it the interview.

## 1. Install

```
git clone https://github.com/dudailia/coop-crew && cd coop-crew && ./install.sh && claude
```

The installer checks Python, Node and git; installs the Node packages and Playwright's Chromium (for resume PDFs and the
optional NUworks browser reader); installs jev-job-search (the form filler, Node 22+ only) in prepare mode; keeps the
NUworks browser reader disabled; runs the health check; and prints the next step. On Windows: open PowerShell in the folder and run
`.\install.ps1`.

The first time you run `claude` in the folder, accept the trust dialog: the crew's permissions and safety hook load only
in a trusted folder.

## 2. Try the demo (optional, 5 minutes)

Type `/demo`. The crew scouts three public company boards, judges five roles for a made-up student, researches two,
builds one resume and one review pack, and opens TODAY.html. It sends and submits nothing.

## 3. /setup: the interview

Type `/setup`. The onboarder asks one group at a time, never guesses, and writes "ask me" for anything you skip:

1. You: name, email, phone (optional), LinkedIn, GitHub, portfolio.
2. Program: college, major, concentration, minor, year, graduation, GPA (and whether to show it).
3. Co-op cycle: which co-op, spring or fall, 4 or 6 months, exact dates, summer extension, whether you are in your NUworks
   recruitment term. You agree the exact availability sentence.
4. Sourcing mode: (a) NUworks plus external, (b) external only, (c) self-developed co-op (turns on the banned-list check
   and keeps NUworks employers out).
5. Work authorization, per country: the exact sentence, and sponsorship now and later. F-1 students: the visa type is
   "F-1 CPT", and H-1B is never given as your type.
6. Targets: role titles, industries, company size, cities, remote/hybrid/on-site, pay floor.
7. Proof bank: upload your CV; the onboarder lists every job, project, award and skill, and you confirm each line and the
   numbers you can defend. Anything you don't confirm is never used.
8. Locks and never-apply: commute limits, office days, citizenship-only roles, employers to avoid.
9. Voice: plain or formal, spelling, words to avoid, sign-off, optional writing sample.
10. Limits: applications a day (default 5), emails a day (default 10, never more than 40), quiet hours, schedules.

It shows you the whole profile to confirm, then runs a dry run (the full cycle on a copy of your profile, with nothing
submitted or sent).

Two switches only you can turn on, by typing them yourself:
- schedules: `! python3 -I tools/schedule.py install` (a daily `/run` at 06:30 and the sender every 15 minutes)
- the optional NUworks browser reader (mode a only). Read the next section first: Symplicity's terms prohibit it as
  written.

## NUworks

In mode (a) the crew reads NUworks **through your own email and your own saved files**, and never loads a NUworks page:

1. **Job-alert emails (default).** In NUworks, save a search (for example "data", co-op, Boston) and turn on its email
   alerts. Each day the inbox agent reads those alert emails (`tools/nuworks_alerts.py`) and adds every posting they list
   to the pipeline as a NUworks role. On a Mac it finds them in Apple Mail; on Windows or Linux, save the alert emails as
   `.eml` files into `data/inbox/`.
2. **Manual import (default).** For a posting you want judged and tailored on its full text, open it in NUworks and save
   it into `data/nuworks-import/`: Print > Save as PDF, or Save Page As (.html). The next `/run` reads it
   (`tools/nuworks_import.py`); if the posting came in from an alert, its full text is added to that role.

NUworks roles are always yours to apply to: TODAY.html shows "Apply in NUworks", and the crew never applies there.

**The optional browser reader** (`mcp/nuworks`) drives a browser, signed in as you, through NUworks listings. It is off
in every install. Before you consider it, read what Symplicity's terms of use say (quoted from
[symplicity-mea.com/TermOfService](https://www.symplicity-mea.com/TermOfService); the current US terms are linked at the
foot of every NUworks page, [symplicity.com/support/terms-of-use](https://www.symplicity.com/support/terms-of-use)):

> "use or attempt to use engines, manual or automated software, tools, devices, agents, scripts robots or other means,
> devices, mechanisms or processes (including, but not limited to, browsers, spiders, robots, avatars or intelligent
> agents) to navigate, search, access, "scrape," "crawl," or "spider" any web pages or any services provided on the
> Sites other than the search engine and search agents available from Symplicity [...] and other than generally
> available third party web browsers"
>
> "collect users' content or information, or otherwise access the Site, using automated means (such as harvesting bots,
> robots, spiders, or scrapers) without our prior permission"

The reader is automated access, however slow and read-only. The Northeastern co-op office approved read-only use, but
that is not Symplicity's permission; using it may breach those terms and put your NUworks account at risk
(`mcp/nuworks/APPROVAL.md` has the full record). If you still want it: `! python3 -I tools/nuworks_enable.py on` shows
this notice and turns the reader on only if you type exactly **I have read the Symplicity terms and accept the risk**.
Then restart Claude Code and sign in with `nuworks_login` in the window it opens. `! python3 -I tools/nuworks_enable.py
off` turns it off.

## 4. Every day: about 20 minutes

1. `/run` (or let the schedule do it), then `/today`.
2. Read MORNING.md: questions for you (HOLD), replies, deadlines, interview invites.
3. Answer what needs you in needs-reply.html (the suggested replies are never sent).
4. Review TODAY.html. Each pack has the Company brief, the resume, the answers, soft flags, the named person and a draft
   note, what was filled from your profile, and the field log. Approve what is right: `/approve <id> <id>`. Skip the rest:
   `/skip <id>`.
5. NUworks roles: click "Apply in NUworks" and apply there yourself with the resume from the pack.
6. LinkedIn notes: send them yourself (copy button in TODAY.html).
7. In prepare mode, send the email drafts from Mail Drafts (or your `.eml` files in `data/outbox/`), then record each
   with `! python3 -I tools/send_due.py --mark-sent <id>` so its follow-up is drafted 5 to 7 working days later.

After each submitted application, tell the crew whether you made heavy edits (`clean_pass`). The review gate stays until
five in a row need none, and after that until you relax it.

## 5. Stop at any time

`/stop` stops everything at its next step; `/crew-resume` turns it off. `touch ~/STOP-AGENTS` works too.
`python3 -I tools/schedule.py uninstall` removes the schedules. See SECURITY.md.

## Files

| Path | What |
|---|---|
| `profile/` | your settings, facts (the only facts ever used), locks, voice, base resume |
| `out/<role-id>/` | posting, brief, person, questions, resume.md/.pdf, answers, cover, field log, soft flags |
| `data/pipeline.sqlite` | every role, application, email and approval, with an event log |
| `TODAY.html`, `MORNING.md`, `needs-reply.html`, `tracker.html` | your pages |
| `APPROVE.txt` | optional: approve by writing ids here, one per line |
| `data/nuworks-import/` | NUworks postings you saved (PDF or HTML) or alert emails (.eml), for the next `/run` |

## Troubleshooting

`/crew-doctor` lists what is missing and how to fix it. Common ones: Playwright's Chromium (`npx playwright install
chromium`), jev on Node below 22 (packs are submitted by hand until you upgrade), Mail asking for Automation permission
(System Settings, Privacy & Security, Automation: allow Terminal to control Mail).
