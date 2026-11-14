---
description: A five-minute demo of the crew on a sample student (or your own profile after /setup). Scouts 3 public boards, judges 5 roles, researches 2, builds 1 one-page resume and 1 review pack, opens TODAY.html. Never sends or submits anything.
disable-model-invocation: true
---
!`python3 -I tools/demo.py prepare`

You are running the **demo** (CLAUDE.md). State root is `demo/`: every file path below is under `demo/`, and every tool
runs as `COOP_STATE=demo python3 -I tools/...`. NUworks and email are skipped. Nothing is ever submitted or sent.
Target: done in under 5 minutes, so keep each agent's task small and run the two researchers at once.

1. **Judge.** Delegate the ids listed "For the screener agent" above to the **screener** (state root demo/, no web
   search needed if the posting text in `demo/out/<id>/posting.md` is enough; skip pulling portal questions, write `[]`
   to `demo/out/<id>/questions.json`). Record its file:
   `COOP_STATE=demo python3 -I tools/pipeline.py apply-verdicts <file>`.
2. **Research 2.** Pick the two best KEEP roles (`COOP_STATE=demo python3 -I tools/pipeline.py list --status keep`).
   Delegate each to its own **researcher** in parallel (brief only, at most 4 page fetches each; skip the named person).
   Then `COOP_STATE=demo python3 -I tools/pipeline.py status <id1> <id2> researched --why "demo brief"`.
3. **Tailor 1.** Delegate the best of the two to the **tailor** (state root demo/; no cover note; answers.md may say the
   portal asks no extra questions; field log required). It must finish with `COOP_STATE=demo python3 -I tools/resume.py <id>`
   passing. Then `COOP_STATE=demo python3 -I tools/pipeline.py status <id> tailored --why "demo pack"`.
4. **Review pack.** Delegate that one role to the **gatekeeper** (state root demo/).
5. Run `COOP_STATE=demo python3 -I tools/demo.py finish`, and tell the room in a few lines: the 5 verdicts with their
   one-line reasons, the pack that is ready, that nothing was submitted or sent, and end with exactly:
   "Run /setup to make this yours."

If any step prints STOP, stop at once.
