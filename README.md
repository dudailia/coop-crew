# coop-crew

**A crew of Claude Code agents that works your co-op and internship search overnight.**
It finds roles on company job boards and in your NUworks job-alert emails, researches each company, and prepares a
one-page resume, the form answers and any outreach email. You read one page in the morning and approve what is right.
**Nothing is submitted or sent until you approve that exact item.**

![TODAY.html: a question for the student and a review pack with the company brief, resume, soft flags and field log](docs/img/today.png)

*TODAY.html for the bundled sample student, after `/demo`. Every detail in it is made up.*

## Install (one line)

```
git clone https://github.com/dudailia/coop-crew && cd coop-crew && ./install.sh && claude
```

Then type `/demo` to watch the crew work on a sample student in about five minutes, and `/setup` to make it yours.

You need macOS, Linux, or Windows with WSL (run `install.ps1` in PowerShell); Python 3.9+, Node.js 18+ (22+ for the
form filler) and git; and Claude Code on a paid Claude plan (Pro or Max). No API keys. The installer checks everything
and prints one next step. Details in [GUIDE.md](GUIDE.md); going to a talk? See
[docs/talk/BEFORE-THE-TALK.md](docs/talk/BEFORE-THE-TALK.md).

## How it works

1. **`/setup`** interviews you once (about 30 minutes): program, co-op dates, work authorization, targets, the facts
   you can defend, your rules ("locks"), your voice. Every claim the crew ever makes about you comes from that profile.
2. **`/run`** (by hand, or scheduled at 06:30) runs the crew: the conductor hands each agent one job, and the agents
   hand off through files and one SQLite pipeline.
3. **TODAY.html** is the result: questions for you, and review packs with the brief, the resume, the answers, soft flags
   and a field log of every form field.
4. **`/approve <id>`** is the only way anything leaves: the applicant re-checks that form and submits it, and an approved
   email goes out in its send window.

```
   you ── /setup /run /approve ──> conductor (main Claude Code session)
                                      │
   onboarder → profile/          inbox (replies, deadlines, NUworks alerts)
                                      │
   scout-web ─┐                       │
   scout-nuworks (optional, off) ─┴─> screener (KEEP / HOLD / DQ: dates, eligibility, locks)
                                      │
                                 researcher (3 to 6 bullet company brief)
                                      │
                                 tailor (one-page resume, answers) → editor (anti-slop)
                                      │
                                 gatekeeper (review pack) ──> TODAY.html: you approve or skip
                                      │
              applicant (submits approved forms)   outreach (drafts emails, plans sends)
                                      │
                                 tracker (pipeline, MORNING.md, tracker.html)
```

Twelve agents in `.claude/agents/`, six skills in `.claude/skills/`, the commands in `.claude/commands/`, Python tools
(standard library only) in `tools/`. More in [docs/architecture.md](docs/architecture.md) and
[docs/agents.md](docs/agents.md).

| Command | What it does |
|---|---|
| `/setup` | The interview, your profile, optional schedules, then a dry run |
| `/run` | One full daily cycle: inbox, scouts, screening, research, resumes, review packs, outreach drafts |
| `/today` | Opens TODAY.html, MORNING.md and needs-reply.html |
| `/approve <ids>` | Approves those applications or emails, and nothing else |
| `/skip <ids>` | Closes items without submitting |
| `/stop`, `/crew-resume` | Kill switch on or off: every job stops at its next step |
| `/demo` | The five-minute demo on a sample student |
| `/crew-doctor` | Health check: tools, logins, schedules, disk, kill switch, last run |

## Safety, in code

- **Prepare mode by default.** A form is submitted only by `tools/applicant.py` for an id you approved, after the gate
  and a re-check of the form; an email goes only through `tools/send_due.py` for an id you approved, inside its send
  window, under the daily caps (5 applications and 10 emails by default; never more than 40 emails a day).
- **A guard hook** (`tools/guard.py`) blocks every agent from submitting, sending, approving, editing the pipeline or
  changing the safety files any other way, and blocks every acting tool call while the kill switch (`/stop`) is on.
- **No invented facts.** Every number and name in outgoing text must be in your `profile/facts.md` (or the posting): the
  checker and the resume build fail otherwise. Work authorization is your sentence, word for word, per country.
- **NUworks within the rules.** By default it comes only from your own email and files: NUworks job-alert emails from
  your saved searches, and postings you save into `data/nuworks-import/`. No NUworks page is loaded and you apply there
  yourself. The optional read-only browser reader is off by default: Symplicity's terms of use prohibit automated access
  without Symplicity's permission, so it turns on only after that notice and a typed acknowledgement
  ([mcp/nuworks/APPROVAL.md](mcp/nuworks/APPROVAL.md), [GUIDE.md](GUIDE.md#nuworks)).
- No LinkedIn automation, no aggregators, no scraping behind logins. Questions that ask you to confirm an answer is your
  own work written without AI are never drafted.
- **Your data stays on your machine**: `profile/`, `data/`, `out/` and the pages are never committed.

More in [SECURITY.md](SECURITY.md).

## Talk materials

[docs/talk/](docs/talk/): the slide deck (`slides.html`, offline, arrow keys), a recorded demo (`demo.mp4`,
`tools/record_demo.sh`), the spoken demo script with a no-Wi-Fi plan, and the attendee pre-install note.

## Tests

```
python3 -m unittest discover -s tests -v     # SPEC section 10 in code, guard, NUworks default path
npm run test:nuworks                         # the NUworks server against a local fake site
tests/acceptance_fresh_install.sh            # fresh clone + empty HOME: install and demo, timed
tests/acceptance_linux_docker.sh             # the same install on Ubuntu (WSL stand-in) + the .eml adapter
python3 -I tools/pii_scan.py                 # personal-data scan of the tree and the git history
```

## Credits

MIT licensed ([LICENSE](LICENSE)). Built on jev-job-search by Qendrim Beka (MIT), job-agents-kit, and the
job-applications and anti-slop skills (MIT, contributed with the author's permission). See
[THIRD_PARTY.md](THIRD_PARTY.md). Not affiliated with Northeastern University or Symplicity.
