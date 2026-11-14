# Third-party notices

| Component | Where | License | Status |
|---|---|---|---|
| jev-job-search by Qendrim Beka | installed at a pinned commit into `vendor/jev/src` by `vendor/jev/install.sh`; `vendor/jev/jev-fixes.patch` modifies it | MIT (`vendor/jev/LICENSE`) | OK to ship. Its notice is kept in `vendor/jev/LICENSE`. |
| job-agents-kit | ported into `tools/` (settings, checker, sender rules, Mail adapter, email audit, pages, board scan) | MIT, same author as this repo | OK |
| internship-watcher | posting-text fetchers in `tools/fetch_posting.py` | same author as this repo | OK |
| `job-applications` skill by the author | `.claude/skills/job-applications/SKILL.md` (adapted) | MIT, included with his permission | OK |
| `anti-slop` skill by the author | `.claude/skills/anti-slop/SKILL.md` (adapted) | MIT, included with his permission | OK |
| unslop 0.15.36, humanizer 3.1.0, declauding 0.14.0 (anti-slop catalogues) | NOT in the repo. `tools/fetch_antislop_refs.sh` installs them locally | Third-party: humanizer says MIT but carries no copyright line; unslop and declauding state no license. the author's permission covers his two skills, not these catalogues | Not shipped. Pin download URLs in `.claude/skills/anti-slop/refs.lock` only once each catalogue's own license allows redistribution or fetching |
| Playwright, pdf-lib, @modelcontextprotocol/sdk, zod | npm dependencies (`package.json`) | Apache-2.0, MIT, MIT, MIT | OK |

The `job-applications` and `anti-slop` skills are by the author, included with his permission under the MIT license and
credited as "the author".
<!-- TODO: add the author's GitHub handle to this credit, the README and both skill files. -->

No Northeastern University or Symplicity logos or trademarks are used. "NUworks" and "Northeastern" appear only as plain
names of the services a student uses.
