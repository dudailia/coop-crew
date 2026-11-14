# The pipeline

`data/pipeline.sqlite`, changed only through `tools/pipeline.py`. Every change is an event (`events` table) with the
reason, so the tracker never changes a row without a real event.

| Table | Holds |
|---|---|
| roles | every posting found: source (web, nuworks), company, title, place, URL, deadline, channel, status, verdict and reason, HOLD question |
| applications | per role: when the form was prepared (jev id), when submitted, `clean_pass` (yes, no, blank), unconfirmed |
| emails | email and LinkedIn drafts: recipient, source of the address, region, slot, text, follow-up, status, follow-up due |
| approvals | ids the student approved (`/approve`), and when each was used |
| events | the log |

Role statuses: new, keep, hold, dq, researched, tailored, ready (gate passed), blocked (gate failed), approved,
submitted, applied-by-hand, skipped, interview, rejected, offer, closed.

APPROVE.txt in the repo root is the other way to approve: one id per line, written by the student.
