---
description: Kill switch ON. Every job, agent and schedule stops at its next step.
disable-model-invocation: true
---
!`python3 -I tools/killswitch.py stop`

The kill switch is on. Stop any work in progress now: make no more tool calls in this turn beyond this message. Tell the
student everything is stopped, nothing more will be submitted, drafted or sent, and `/crew-resume` turns it off.
