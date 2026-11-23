# Changelog

What changed in each release. Dates are when the release was published.

## v1.1 (23 November 2026)

Easier to start, easier to watch, the same crew. No change to what the crew does or to any safety rule.

- **A smooth demo.** `tools/record_demo.mjs` now records frame by frame: every frame is a screenshot at a computed
  scroll position, so the pages move at one constant speed with no jumps and no repeated frames. `demo.mp4` (attached
  to the release) is 1280x720, 30 fps, 60 s. The README GIF is 960x540, 15 fps, 14 s, a seamless loop under 8 MB, with
  large captions. Both come from the offline demo, so only the made-up student and companies appear.
- **A new README**: a banner, badges, a three-step quickstart at the top, a diagram of how the agents hand off, an FAQ,
  "Using this at another school" (what to change without NUworks), and the advanced sections folded away.
- **CI.** Every push and pull request runs `./install.sh`, the Python tests on Python 3.9 and 3.13, the NUworks server
  tests and the personal-data scan (`.github/workflows/tests.yml`).
- **Template repository and Discussions.** "Use this template" starts your own copy; questions go to Discussions, and
  the issue form links there.
- **A social preview image** (`docs/social-preview.png`, 1280x640) and the README banner, both drawn from HTML in
  `docs/img/src/` by `tools/render_art.mjs`.
- `/setup` accepts a summer cycle, for a summer internship at another school.
- `/setup`, from the new-student test: it explains that NUworks alert emails are read from Mail and only saved
  postings go in `data/nuworks-import/`, and it writes email regions from the student's own cities only (a template
  city no longer slips in).
- The project's Claude Code settings turn off the co-author and pull request attribution lines Claude Code adds by
  default (`attribution` in `.claude/settings.json`).
- The commit history was rewritten to drop those co-author lines from earlier commit messages. Every commit keeps its
  author, dates and files; only the hashes changed. The `v1.0` tag points to the rewritten v1.0 commit.

## v1.0 (21 November 2026)

The first public release: twelve agents, six skills and nine commands; TODAY.html with review packs; prepare mode by
default, approvals only from the student, the guard hook, the kill switch and the facts checker; NUworks only through
the student's own job-alert emails and saved postings, with the browser reader off; the Northeastern rules; the talk
materials. Details in [docs/releases/v1.0.md](docs/releases/v1.0.md).
