# Before the repo goes public

All must be true. Until then the repo stays private and nothing is pushed. `PUBLISH.md` has the commands.

- [x] The author of `job-applications` and `anti-slop` approved including them (MIT) and asked not to be named;
      THIRD_PARTY.md and both skill files say so, and the name is in no file or commit (14 Nov 2026).
- [x] Licenses of every third-party text checked (19 Nov 2026). The anti-slop catalogues (unslop and declauding state
      no license; humanizer names no copyright holder) are replaced by coop-crew's own
      `.claude/skills/anti-slop/catalogue.md`, and their fetch script and `refs.lock` are removed. The offline demo's
      cached postings (copies of real employers' postings) are replaced by made-up ones, in the history too. Credits in
      THIRD_PARTY.md.
- [x] NUworks: approved by the Northeastern co-op office for read-only use (14 Nov 2026), recorded in
      `mcp/nuworks/APPROVAL.md`.
- [x] NUworks and Symplicity terms of use checked (14 Nov 2026): Symplicity prohibits automated access without its prior
      written permission. Default NUworks path is now job-alert emails and manual import; the browser reader stays off
      by default behind a terms notice and a typed acknowledgement. Recorded in `mcp/nuworks/APPROVAL.md`.
- [x] Symplicity's US terms page (symplicity.com/support/terms-of-use) read in full and its date noted in APPROVAL.md
      (16 Nov 2026: "Effective May 1, 2019"; same automated-access clauses as the regional text).
- [x] A real NUworks job-alert email tested (19 Nov 2026), read-only and outside the repo: the Mail alert-saving step
      (`tools/email_audit.py --nuworks-alerts-only`) saved 40 emails from the Symplicity sender, and
      `tools/nuworks_alerts.py` now reads all of them (Outlook Safe Links, job-redirect links, employer and location
      lines). The copies were deleted; the repo has only the made-up `tests/fixtures/nuworks/alert-safelinks.eml`.
- [x] No Northeastern, Symplicity or other logos or trademarks beyond plain naming (19 Nov 2026): every image in
      `docs/img/` and `docs/talk/img/`, all 13 slides and frames of `demo.mp4` checked by eye. They show page text
      only.
- [x] The README images show only the sample student (`docs/img/demo.gif`, checked 19 Nov 2026).
- [x] v1.1 media (23 Nov 2026): `demo.mp4` (1810 frames) and `docs/img/demo.gif` (209 frames) re-recorded from the
      offline demo; every GIF frame and every fifth video frame read by OCR (only Quillstack Data, Fernway Finance,
      Harborlight Robotics, Northwind Freight and the sample student's university), and the pages have no images. The
      banner and social preview are original HTML drawings with no logos.
- [x] Commit author and committer are `239183685+dudailia@users.noreply.github.com` on every commit (19 Nov 2026), and
      the repo's git config uses it.
- [x] `python3 -I tools/pii_scan.py` (with the private pattern file outside the repo) and `gitleaks` pass over the tree
      and the history (19 Nov 2026). Rerun before the push.
- [x] `python3 -m unittest discover -s tests` (36), `npm run test:nuworks` (11) and `tests/acceptance_fresh_install.sh`
      (clone, install, `/crew-doctor`, `/demo --offline`) pass (19 Nov 2026).
