# Overnight report, 14 to 15 November 2026

Worked alone from 23:55 to 00:25 ET. Everything is committed locally on `main`. Nothing was pushed or published,
no email was sent, Mail was never opened, and the two folders outside the repo were not touched. Every page, image and
video shows only the bundled, made-up sample student.

## What passed

| Check | Result |
|---|---|
| Python suite (`python3 -m unittest discover -s tests`) | **31/31 pass** |
| Python suite with the guard patch applied (on a copy of the repo) | **33/33 pass** |
| NUworks tests (`npm run test:nuworks`) | **11/11 pass** |
| Personal-data scan (`tools/pii_scan.py`), tree and full history, 16 private patterns | **no findings**, after one fix (below) |
| Live `/demo` inside `tools/record_demo.sh` | **189 s**, 5 roles judged, 1 review pack, **0 submitted, 0 sent** |
| `docs/talk/demo.mp4` | **84 s** (60 to 90 asked), 1280×720 H.264, 3.4 MB |
| Deck: 13 slides, every slide rendered and checked for overflow | no overflow, **0 network requests** |
| QR code on slide 12 | decodes to `https://github.com/dudailia/coop-crew` (checked with Apple's Vision framework) |

## What I did, step by step

1. **Guard: the three overbroad rules.** I cannot edit `tools/guard.py`: the guard blocks agents from changing the
   safety tools, by design, so the change is a patch for you, with its tests, in
   **`logs/guard-narrow-3-rules.patch`** (gitignored, so it survives). Nothing was committed for this step: committing the
   tests alone would break the suite.
   - `APPROVE.txt`: reading, listing, `test -e`, `wc`, `grep` and copying it out are allowed. Writing it is still
     blocked: redirects, `tee`, `cp`/`mv`/`rm`/`touch`, `sed -i`, `perl -i`, `dd of=`, editors, and any interpreter
     that names it.
   - sqlite: `sqlite3 -readonly ... "select ... from approvals"` is allowed. Still blocked: any write statement (even
     with `-readonly`, and after a `;`), the pipeline opened without `-readonly`, piping SQL into it, `ATTACH`,
     `.restore` and similar dot commands, and Python's `sqlite3` module writing.
   - NUworks and LinkedIn: a fetch now means a real fetcher. That is curl, wget, urllib, httpx, playwright and the
     like, `requests.get(...)`, `fetch(...)`, `webbrowser`, or `open <url>` as a command. Python's `open(...)`, the
     word "fetch" in prose, and a heredoc that edits a doc mentioning symplicity.com are no longer blocked. A
     `nuworks` mention needs an actual URL next to curl/wget.
   - 2 new tests (both sides: 31 blocked and 15 allowed commands), run on a patched copy: 33/33.
2. **Talk deck: `docs/talk/slides.html`** (commit `01f4f0b`). 13 slides: the problem, the crew diagram, one night
   (00:40 to 07:30), the review page, safety, NUworks within the rules, the resume and checker, results so far,
   install, what you need, the QR code, questions. Arrow keys, space, click, swipe; F for full screen; 16:9 stage;
   type 34 px or larger at 1920×1080; no logos.
   - It is built by `tools/build_slides.py` from `docs/talk/slides.tpl.html`. The QR code (`tools/qr_svg.py`, standard
     library) and the screenshots are inlined.
   - The results slide counts the tests from the test files at build time, so it never claims more than the repo has.
3. **Demo recording: `tools/record_demo.sh` → `docs/talk/demo.mp4`** (commit `2974fe4`). It runs the live `/demo` (or
   `--offline`, or `--no-run`), then records TODAY.html, the review pack, the resume and the tracker with on-screen
   captions, then converts to MP4 with ffmpeg.
   - `demo.py` gained `COOP_DEMO_SAMPLE=1`, so a recording always uses the sample student, never a real profile, and
     `COOP_DEMO_NO_OPEN=1`.
   - I watched the frames and fixed two bugs (the HOLD card was taken for the review pack; collapsed sections) before
     the final take.
4. **Demo script: `docs/talk/DEMO-SCRIPT.md`** (commit `a5a1226`). Two minutes over the video, keyed to its timestamps,
   with five fallbacks:
   - the video from disk;
   - the offline demo, which needs no network and no Claude;
   - pre-running `/demo`;
   - a PDF of the deck;
   - the kill switch.
5. **Attendee note: `docs/talk/BEFORE-THE-TALK.md`** (commit `2fbb9ff`). What to install the day before, how to check
   it (`/crew-doctor`, `/demo`, the offline demo), and 13 common errors with fixes, taken from the installer's real
   messages.
6. **README** (commit `333ac3a`): a three-line pitch, a fresh TODAY.html screenshot from tonight's demo, the install
   line, "how it works" with a simpler agent diagram, the commands, safety, links to the talk materials.
7. **Checks and this report.** One fix was needed (commit `d054439`): the personal-data scan read `demo.mp4`'s bytes
   as text and matched noise, two "emails" and a private pattern case-insensitively. Video now joins the images and
   PDFs the scanner already skips. I also added a structural test for the QR encoder.

## What needs you

1. **Apply the guard patch.** Type `! git apply logs/guard-narrow-3-rules.patch`, then run
   `python3 -m unittest discover -s tests` (expect 33) and `python3 -I tools/build_slides.py` (the deck then says 33),
   and commit.
2. **The QR code and the install line point to `github.com/dudailia/coop-crew`.** They only work once the repo is public
   at that address.
3. **Check the deck's claims and tone before the talk.**
   - The "one night" times are an example; only the 06:30 run is real (the optional schedule).
   - Slide 7 quotes Symplicity's terms (the regional text; the US page is still to be read by hand, as noted in
     APPROVAL.md).
4. **`docs/talk/demo.mp4` (3.4 MB).** Done on 15 November: removed from all of git history (commit hashes above are
   the rewritten ones), kept locally and gitignored; attach it to the GitHub release. Re-recording replaces it:
   `tools/record_demo.sh` (about 4 minutes, uses your Claude plan) or `--offline`.
5. **Deviations from the slide skill's defaults.**
   - System fonts (Iowan Old Style, Avenir Next, SF Mono, all on macOS) instead of web fonts, so the deck works with no
     Wi-Fi. Other systems fall back to similar faces.
   - No inline-editing mode, so a stray key during the talk cannot edit a slide.
6. **A refused install.** The auto-mode classifier refused `pip install segno` (a QR library) from the network, so I did
   not install anything. `tools/qr_svg.py` writes the QR code with the standard library instead.
7. **Unused images.** `docs/img/resume.png` and `docs/img/tracker.png` are refreshed but no longer used by the README
   (only TODAY.html is). Keep them or delete them.
8. **Still open from yesterday.**
   - Read Symplicity's US terms page by hand.
   - A real NUworks alert email (.eml) to check `tools/nuworks_alerts.py` against.
   - The Mac Mail alert-saving step has not run against real Mail.
