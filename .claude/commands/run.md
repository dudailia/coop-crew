---
description: One full daily cycle. Inbox, scouts, screener, researcher, tailor, editor, gatekeeper, outreach drafts, applicant prepare, sender, tracker. Produces TODAY.html. Submits and sends nothing unapproved.
---
!`python3 -I tools/cycle.py begin`

Run one full cycle as the conductor (CLAUDE.md). **Before every step**, run `python3 -I tools/cycle.py step <name>`.
If it prints STOP (exit 3), stop the cycle at once and tell the student. Limits for this run: at most 15 new postings
from each scout, and tailor at most `limits.applications_per_day` roles (profile/settings.json, default 5).

1. `inbox`: delegate to the **inbox** agent.
2. `scout`: run `python3 -I tools/scan_boards.py` (boards in data/boards.txt, if any). Delegate to **scout-web**
   (and **scout-nuworks** only if `profile/settings.json` has mode "nuworks+external" and nuworks.enabled true).
   Then append any new boards from `data/incoming/boards-*.txt` to `data/boards.txt` with the Write tool (no
   duplicates), and run `python3 -I tools/pipeline.py import` (it deduplicates against the pipeline).
   For roles with no or thin posting text, run `python3 -I tools/fetch_posting.py <id>`.
3. `screen`: run `python3 -I tools/screen_rules.py`. Delegate the roles it left as "new" to the **screener**
   (`python3 -I tools/pipeline.py list --status new`). Record its file: `python3 -I tools/pipeline.py apply-verdicts <file>`.
4. `research`: delegate the KEEP roles (`pipeline.py list --status keep`, at most the daily limit, earliest deadline
   first) to the **researcher**. Then `python3 -I tools/pipeline.py status <ids> researched --why "brief written"`.
5. `tailor`: delegate those roles to the **tailor**. Then `pipeline.py status <ids> tailored --why "packet built"`.
6. `edit`: delegate their resume.md, answers.md and cover.md to the **editor**; then rebuild each resume with
   `python3 -I tools/resume.py <id>` (it must pass).
7. `gate`: delegate to the **gatekeeper**; any "LOCK CONFLICT" goes back to HOLD with
   `pipeline.py verdict <id> HOLD --reason ... --question ...`. Then `python3 -I tools/gate.py <ids>`.
8. `outreach`: delegate to **outreach** the KEEP roles whose channel is email, and companies with a verified person in
   `out/<id>/person.md` that have no form. Then delegate the new drafts to the **editor**.
9. `applicant`: delegate to the **applicant**: `prepare` for roles with status ready and channel form. Never submit here.
10. `send`: run `python3 -I tools/send_due.py` (it only ever drafts or sends approved emails, in their windows).
11. `tracker`: delegate to the **tracker**.

Then run `python3 -I tools/cycle.py end` and tell the student, in a few lines: new roles, KEEP / HOLD / DQ counts, packs
ready for review, drafts waiting for approval, anything blocked, and "Open /today to review. Nothing was submitted or
sent."
