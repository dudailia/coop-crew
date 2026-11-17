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
- [x] Symplicity's US terms page (symplicity.com/support/terms-of-use) read in full and its date noted in APPROVAL.md
      (16 Nov 2026: "Effective May 1, 2019"; same automated-access clauses as the regional text).
- [x] `python3 -I tools/pii_scan.py` passes (with the private pattern file outside the repo) over the tree and the history
      (16 Nov 2026, 16 private patterns, no findings). Rerun before the push.
- [x] `python3 -m unittest discover -s tests` (33), `npm run test:nuworks` (11) and `tests/acceptance_fresh_install.sh`
      (install 59 s) pass (16 Nov 2026).
- [ ] No Northeastern or Symplicity logos or trademarks beyond plain naming.
- [x] The README screenshots show only the sample student (`docs/img/today.png`, the only one the README uses, checked
      16 Nov 2026).
