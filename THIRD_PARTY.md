# Third-party notices

| Component | Where | License | Status |
|---|---|---|---|
| jev-job-search by Qendrim Beka | installed at a pinned commit into `vendor/jev/src` by `vendor/jev/install.sh`; `vendor/jev/jev-fixes.patch` modifies it | MIT (`vendor/jev/LICENSE`) | OK to ship. Its notice is kept in `vendor/jev/LICENSE`. |
| job-agents-kit | ported into `tools/` (settings, checker, sender rules, Mail adapter, email audit, pages, board scan) | MIT, same author as this repo | OK |
| internship-watcher | posting-text fetchers in `tools/fetch_posting.py` | same author as this repo | OK |
| `job-applications` skill | `.claude/skills/job-applications/SKILL.md` (adapted) | **pending**: the author's written OK, choice of credit and license | **Do not publish until confirmed** |
| `anti-slop` skill | `.claude/skills/anti-slop/SKILL.md` (adapted) | **pending**: as above | **Do not publish until confirmed** |
| unslop 0.15.36, humanizer 3.1.0, declauding 0.14.0 (anti-slop catalogues) | NOT in the repo. `tools/fetch_antislop_refs.sh` installs them locally | humanizer says MIT but carries no copyright line; unslop and declauding state no license | Not shipped. Pin download URLs in `.claude/skills/anti-slop/refs.lock` only once redistribution or fetching is allowed |
| Playwright, pdf-lib, @modelcontextprotocol/sdk, zod | npm dependencies (`package.json`) | Apache-2.0, MIT, MIT, MIT | OK |

The two skills' author is credited in each skill file as "the original author (credit and license pending)" until they
choose how to be credited.

No Northeastern University or Symplicity logos or trademarks are used. "NUworks" and "Northeastern" appear only as plain
names of the services a student uses.
