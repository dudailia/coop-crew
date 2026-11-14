# Agent reference

| Agent | Job | Tools | Skills | Never |
|---|---|---|---|---|
| onboarder | the /setup interview; writes `profile/`; builds the proof bank from the CV and answers | Read, Write, Edit, Bash | | guess a fact |
| scout-web | postings from company-run boards, YC and VC portfolios, funding news, in the student's places and cycle | WebSearch, WebFetch, Read, Write | job-applications | use aggregators; scrape LinkedIn |
| scout-nuworks | NUworks listings through the read-only server | nuworks status/search/get_posting, Read, Write | nuworks | apply, message, touch anything but listings |
| screener | KEEP / HOLD (with the exact question) / DQ (with the reason); portal questions; banned check in self-developed mode | Read, Write, WebSearch, WebFetch | job-applications, banned-check, form-answers | pass a role that conflicts with a lock |
| researcher | Company brief (3 to 6 bullets) and at most one named person with a cited source | WebSearch, WebFetch, Read, Write | job-applications, outreach-rules | write research memos; guess emails |
| tailor | one-page ATS resume, portal answers, field log, cover note only when asked | Read, Write, Edit, Bash | job-applications, form-answers | invent a claim; exceed one page |
| editor | anti-slop pass on every outgoing text (embedded mode) | Read, Write, Edit | anti-slop | add a fact, number, name or opinion |
| gatekeeper | judgment on each review pack; lock conflicts; soft flags | Read, Write | job-applications | treat a ready pack as permission |
| applicant | jev prepare; submit only approved ids through `applicant.py` | Bash, Read, Write | | submit anything unapproved |
| outreach | email and LinkedIn drafts; planning into send windows; follow-ups | Read, Write, Bash | outreach-rules, anti-slop | send unapproved; buy or guess addresses |
| inbox | read-only audit; needs-reply.html; suggested replies | Bash, Read, Write | anti-slop | send, move, delete or mark mail |
| tracker | pipeline events, dues, clean-pass streak, the pages | Read, Write, Bash | job-applications | change a row without a real event |

Agents without Bash hand their results to the conductor as files in `data/incoming/` (roles, verdicts, drafts); the
conductor records them through `tools/pipeline.py`, which checks every change in code.
