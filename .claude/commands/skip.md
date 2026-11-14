---
description: Close applications or emails by id without submitting or sending them.
argument-hint: <id> [<id> ...]
disable-model-invocation: true
---
!`python3 -I tools/skip.py $ARGUMENTS && python3 -I tools/build_today.py`

Tell the student which ids were skipped (lines above). Nothing was submitted or sent.
