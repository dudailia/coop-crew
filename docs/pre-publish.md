# Before the repo goes public

All must be true. Until then the repo stays private and nothing is pushed.

- [x] the author approved including `job-applications` and `anti-slop` (MIT, credit "the author"); THIRD_PARTY.md and both skill
      files updated (14 Nov 2026).
- [ ] the author's GitHub handle added to the credit (TODO markers in THIRD_PARTY.md and both skill files).
- [ ] The anti-slop catalogues' licenses checked; URLs pinned in `.claude/skills/anti-slop/refs.lock` only if allowed.
- [x] NUworks: approved by the Northeastern co-op office for read-only use (14 Nov 2026), recorded in
      `mcp/nuworks/APPROVAL.md`; the module stays opt-in and off by default.
- [ ] NUworks and Symplicity terms of use checked, and the clause recorded in `mcp/nuworks/APPROVAL.md`.
- [ ] `python3 -I tools/pii_scan.py` passes (with the private pattern file outside the repo) over the tree and the history.
- [ ] `python3 -m unittest discover -s tests`, `npm run test:nuworks` and `tests/acceptance_fresh_install.sh` pass.
- [ ] No Northeastern or Symplicity logos or trademarks beyond plain naming.
- [ ] The README screenshots show only the sample student.
