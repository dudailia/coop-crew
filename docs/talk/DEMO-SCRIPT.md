# Demo script: two minutes

What the room sees: `docs/talk/demo.mp4` (78 seconds, no sound, captions on screen; not in git: download it from the
release into `docs/talk/`, or record it), recorded by `tools/record_demo.sh --offline` from the offline demo on the
made-up sample student, Avery Example. Every company in it is made up too. You talk over it. Have it open in a second
tab before the talk, and the deck on slide 4 ("one night") when you start.

Timings below follow the video. Spoken text is a guide, not a script to read; about 280 words in two minutes.

## Before you press play (0:00 to 0:25 of your two minutes)

> "Here is what you'd wake up to. This is the demo that ships with the repo: the crew picked five roles, judged them,
> researched the best ones, and built one application for review. The student and the companies are made up; every
> detail on screen is fake. Nothing was sent and nothing was submitted. With your own profile, agents do the judging and
> the research; in this recording, rules in code stand in for them so it runs anywhere."

Press play.

## Over the video

| Video | On screen | Say |
|---|---|---|
| 0:00 | TODAY.html, top | "This is the one page you read each morning. Everything the crew did overnight is here." |
| 0:12 | The review pack | "The review pack. First, why this role passed: title, dates, eligibility, your rules. Under it, a short company brief. With agents on, the brief also reads the company's own site." |
| 0:22 | Soft flags | "Soft flags are what you should know before you approve. Here: the rules judged this role instead of an agent, the brief is from the posting only, and the portal's own questions were not pulled, so check the live form." |
| 0:31 | Field log | "The field log: every field in the application form, and where its value came from. Nothing is typed from thin air." |
| 0:39 | Approve / Skip | "And then you decide. Approve sends that exact id to the applicant, which re-checks the form and submits it. Skip drops it. Nothing else moves." |
| 0:45 | The resume | "This is the resume built for this one role. One page, plain enough for an applicant tracking system. Every number and every name is checked against the student's own facts file; an invented number or employer fails the build." |
| 0:59 | The tracker | "And the tracker keeps every role and what happened to it: a deadline that passed, a city the student can't work in, so nothing gets lost." |
| 1:06 | Closing caption | "That's it. Twenty minutes a day, and you stay the one who presses the button." |

When a live run has a role that might break one of the student's rules, TODAY.html opens with **Questions for you
(HOLD)**: the crew asks instead of guessing. The offline recording has none; mention it if someone asks.

## After the video (last 15 seconds)

> "If you want to try it: one line to install, then `/demo`. The QR code is on the next slide." Go to slide 12.

## If something fails

Decide before the talk which of these you will use; the first two need no network at all.

1. **The video will not play.** It is a plain MP4 on your disk: open it in QuickTime or VLC. Still nothing: go to slides 5
   and 8, which show the same TODAY.html and resume, and talk through the table above.
2. **No Wi-Fi, but you want a live demo.** Run the offline demo, which needs no network and no Claude access:
   `python3 -I tools/demo.py run --offline`. It uses the bundled made-up postings, judges the roles by the rules in
   code, builds one pack and opens TODAY.html, in a few seconds. Say so: "this is the offline version: the
   rules in code instead of the agents."
3. **Wi-Fi is slow and you want the live `/demo`.** Don't start it on stage: it takes about 4 minutes. Run it before the
   talk and show the result pages; if the boards are unreachable, `/demo` falls back to its cached copy by itself.
4. **The laptop fails.** Have the deck as a PDF on a USB stick or your phone (open `slides.html` in Chrome, Print, Save
   as PDF: one slide per page) and `demo.mp4` with it.
5. **The kill switch is on** (`STOP: the kill switch is on`): type `/crew-resume`, or skip to the video.

Checklist for the morning of the talk: laptop charged, `slides.html` and `demo.mp4` open in two tabs, the offline demo
run once (`python3 -I tools/demo.py run --offline`) so its pages are fresh, notifications off, display mirrored.
