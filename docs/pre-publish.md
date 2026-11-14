# Before the repo goes public

All must be true. Until then the repo stays private and nothing is pushed.

- [ ] The skills' author gave written OK to open-source `job-applications` and `anti-slop`, and chose the credit and
      license; THIRD_PARTY.md and both skill files updated.
- [ ] The anti-slop catalogues' licenses checked; URLs pinned in `.claude/skills/anti-slop/refs.lock` only if allowed.
- [ ] NUworks: the co-op office's or Northeastern IT's written answer recorded in `mcp/nuworks/APPROVAL.md`, and the
      NUworks and Symplicity terms of use checked. If the answer is no, the module stays disabled with that note.
- [ ] `python3 -I tools/pii_scan.py` passes (with the private pattern file outside the repo) over the tree and the history.
- [ ] `python3 -m unittest discover -s tests`, `npm run test:nuworks` and `tests/acceptance_fresh_install.sh` pass.
- [ ] No Northeastern or Symplicity logos or trademarks beyond plain naming.
- [ ] The README screenshots show only the sample student.
