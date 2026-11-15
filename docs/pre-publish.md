# Before the repo goes public

All must be true. Until then the repo stays private and nothing is pushed.

- [x] The author of `job-applications` and `anti-slop` approved including them (MIT) and asked not to be named;
      THIRD_PARTY.md and both skill files say so, and the name is in no file or commit (14 Nov 2026).
- [ ] The anti-slop catalogues' licenses checked; URLs pinned in `.claude/skills/anti-slop/refs.lock` only if allowed.
- [x] NUworks: approved by the Northeastern co-op office for read-only use (14 Nov 2026), recorded in
      `mcp/nuworks/APPROVAL.md`.
- [x] NUworks and Symplicity terms of use checked (14 Nov 2026): Symplicity prohibits automated access without its prior
      written permission. Default NUworks path is now job-alert emails and manual import; the browser reader stays off
      by default behind a terms notice and a typed acknowledgement. Recorded in `mcp/nuworks/APPROVAL.md`.
- [ ] Symplicity's US terms page (symplicity.com/support/terms-of-use) read by hand and its date noted in APPROVAL.md
      (the guard blocks fetching it here).
- [ ] `python3 -I tools/pii_scan.py` passes (with the private pattern file outside the repo) over the tree and the history.
- [ ] `python3 -m unittest discover -s tests`, `npm run test:nuworks` and `tests/acceptance_fresh_install.sh` pass.
- [ ] No Northeastern or Symplicity logos or trademarks beyond plain naming.
- [ ] The README screenshots show only the sample student.
