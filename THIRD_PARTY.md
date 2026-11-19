# Third-party notices

Everything in this repository is MIT (see [LICENSE](LICENSE)) unless listed here. Checked 19 Nov 2026: only what has a
license that allows redistribution is shipped; anything unclear was replaced with text written for this repo.

## Shipped in the repository

| Component | Where | License | Notes |
|---|---|---|---|
| `job-applications` skill | `.claude/skills/job-applications/SKILL.md` (adapted) | MIT, contributed by its author for coop-crew | The author gave permission and asked not to be named. |
| `anti-slop` skill | `.claude/skills/anti-slop/SKILL.md` (adapted) | MIT, contributed by its author for coop-crew | Same author and terms as above. Its pattern list, `catalogue.md`, is coop-crew's own text. |
| job-agents-kit | ported into `tools/` (settings, checker, sender rules, Mail adapter, email audit, pages, board scan) | MIT | By the author of this repository. |
| internship-watcher | posting-text fetchers in `tools/fetch_posting.py` | MIT (this repository's) | By the author of this repository, who has no separate license for it; the ported code is released here under MIT. |
| jev-job-search patch and templates | `vendor/jev/jev-fixes.patch`, `vendor/jev/templates/`, `vendor/jev/install.sh` | MIT | jev-job-search is Copyright (c) Qendrim Beka; its notice is kept in `vendor/jev/LICENSE`. The patch modifies jev; the templates are coop-crew's own. |
| Short quotations | `mcp/nuworks/APPROVAL.md`, `GUIDE.md`, `tools/nuworks_enable.py`, `docs/talk/slides.html` | Quoted for comment, with the source named | Symplicity's terms of use (symplicity.com/support/terms-of-use, symplicity-mea.com/TermOfService) and Northeastern's Policy 700 (policies.northeastern.edu/policy700). The documents stay with their owners. |

## Installed on the student's machine, not shipped

| Component | How | License |
|---|---|---|
| jev-job-search by Qendrim Beka | `vendor/jev/install.sh` clones it at the commit pinned in `vendor/jev/PIN` into `vendor/jev/src/` (gitignored) | MIT |
| Playwright (and the Chromium it downloads), pdf-lib, @modelcontextprotocol/sdk, zod | `npm install` (`package.json`) | Apache-2.0, MIT, MIT, MIT |
| Job postings | fetched at run time from employers' public boards (Greenhouse, Lever, Ashby, Workable, career pages) into `out/` and `data/` (gitignored) | The employers' own. coop-crew stores them only on the student's machine and never republishes them. |

## Replaced with coop-crew's own text (19 Nov 2026)

- **The anti-slop pattern catalogues** (unslop, humanizer, declauding). Unslop and declauding state no license.
  Humanizer says MIT but names no copyright holder. None of them was ever committed. The skill now uses
  `.claude/skills/anti-slop/catalogue.md`, written for coop-crew, and `tools/fetch_antislop_refs.sh` and `refs.lock`
  are gone.
- **The offline demo's cached postings** (`templates/demo-cache/roles.json`). These had been copies of real postings
  from three public company boards, and the copies are now removed from git history too. The cache now holds made-up
  postings at made-up companies (Fernway Finance, Quillstack Data, Harborlight Robotics). The live `/demo` still reads
  real public boards at run time.

## Names and marks

No Northeastern University, Symplicity or other logos or trademarks are used. "NUworks", "Northeastern" and
"Symplicity" appear only as plain names of the services a student uses, and employer names appear only as plain text.
coop-crew is not affiliated with Northeastern University or Symplicity.
