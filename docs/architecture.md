# Architecture

One Claude Code project. The main session is the **conductor** (`CLAUDE.md`). Specialist **subagents**
(`.claude/agents/`) each do one job with only the tools they need. **Skills** (`.claude/skills/`) hold the house rules.
Shared state is local files plus one SQLite pipeline (`data/pipeline.sqlite`). Everything that must never go wrong is in
code, in `tools/`, not only in prompts.

```
/run  ->  cycle.py step <name> (kill switch check) before every step
  1 inbox        inbox agent      -> tools/inbox.py (email_audit.py on Mac Mail | inbox_eml.py) -> needs-reply.html
  2 scout        scan_boards.py + scout-web (+ scout-nuworks via MCP) -> data/incoming/*.json -> pipeline.py import
  3 screen       screen_rules.py (hard DQ/HOLD) -> screener -> verdicts file -> pipeline.py apply-verdicts
  4 research     researcher -> out/<id>/brief.md, person.md
  5 tailor       tailor -> resume.md -> resume.py (one page or fail; facts check) + answers.md, field-log.md
  6 edit         editor (anti-slop, embedded) -> resume.py again
  7 gate         gatekeeper (judgment) -> gate.py (code) -> status ready | blocked
  8 outreach     outreach -> drafts -> check_msgs.py --drafts -> plan_emails.py (slots, caps, one per person)
  9 applicant    applicant.py prepare (jev, prepare mode: fills, submits nothing)
 10 send         send_due.py (approved ids only, in windows; drafts in prepare mode)
 11 tracker      build_today.py, build_tracker.py, morning.py

/approve <ids> -> approve.py (the student's command) -> applicant.py submit <exactly those ids>
```

## The two doors

| Action | Only through | Checks in code |
|---|---|---|
| Submit an application | `tools/applicant.py submit` -> `tools/jev.py` | approval, kill switch, daily cap, channel (never NUworks), gate re-run, jev re-check of the open form, one submit |
| Draft or send an email | `tools/send_due.py` -> `tools/mail.py` | approval, kill switch, pause files, weekday and window, daily cap (hard maximum 40), one email per address, one follow-up per company, cancelled by a reply |

`tools/guard.py` (a PreToolUse hook on every agent tool call) blocks the other routes: direct `jev submit`, AppleScript,
`approve.py`, `APPROVE.txt`, pipeline writes, edits to the safety files, LinkedIn and NUworks fetching. While `STOP`
exists it blocks every acting tool call.

## State

See the map in `CLAUDE.md` and `docs/pipeline.md`. `COOP_STATE` points every tool at another state folder (the demo uses
`demo/`, the tests a temporary folder), so a demo or a test never touches the student's files.

## Concurrency

One lock (`logs/night.lock`): the sender, the applicant and the Mac Mail audit never run at the same time; the NUworks
server marks `logs/nuworks.busy` while its browser is open and the lock waits for it.
