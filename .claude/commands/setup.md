---
description: Set up coop-crew for you. An interview about your major, co-op cycle and goals, then your profile, then a dry run.
disable-model-invocation: true
---
!`python3 -I tools/crew_doctor.py --install || true`

Run the **onboarder** subagent to interview the student and write their profile. Pass it this instruction: "Run the full
/setup interview, one group at a time, and finish with setup_finish.py --show, the two student-only switches, and the
dry run."

The health check above is for context: if anything is marked FAIL, tell the student the fix first.

When the onboarder is done, tell the student, in a few lines:
- their profile is in `profile/` (private, never committed);
- the dry run result (submits 0, sends 0);
- the next step: `/run` for a first real cycle, then `/today`.
