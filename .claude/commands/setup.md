---
description: Set up coop-crew for you. An interview about your major, co-op cycle and goals, then your profile, then a dry run.
disable-model-invocation: true
---
!`python3 -I tools/crew_doctor.py --install || true`

Run the **onboarder** subagent to interview the student and write their profile. Pass it this instruction: "Run the full
/setup interview, one group at a time, and finish with setup_finish.py --show, the two student-only switches, and the
dry run."

The health check above is for context: if anything is marked FAIL, tell the student the fix first.

The onboarder asks one group at a time and stops after each: show the student its questions as they are, and send
their answers back to the same onboarder (resume it) until it reports the dry run.

When the onboarder is done, tell the student, in a few lines:
- the profile summary it showed, and that they can reply with any correction (send corrections to the onboarder; a
  reply like "confirmed" needs nothing more, so just acknowledge it);
- their profile is in `profile/` (private, never committed);
- the dry run result (submits 0, sends 0). Its packs in `logs/dry-run/` are practice copies on sample roles: they
  cannot be approved, and `/approve` only ever acts on packs in TODAY.html after `/run`;
- the next step: `/run` for a first real cycle, then `/today`.
