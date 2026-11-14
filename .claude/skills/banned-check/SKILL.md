---
name: banned-check
description: Use in self-developed co-op mode before judging, researching or contacting any employer. The three-step check that keeps employers who recruit through NUworks out of a self-developed co-op search.
---
# Banned-list check (self-developed mode only)

A self-developed co-op cannot be with an employer that already recruits Northeastern students through NUworks. In
self-developed mode (`"mode": "self-developed"` in `profile/settings.json`), check every employer before anything is
built or drafted. In other modes, skip this skill.

## Step 0: the list, in code

`python3 -I tools/banned.py check "<company>"`. It matches employer-wide and under any common spelling (case, accents,
punctuation, Inc/LLC, joined words, a city after the name, a name in brackets). An acquired firm counts as its acquirer:
check both names. "blocked" means DQ with the reason it prints. "clear-list" means run the three web checks.

## The three web checks

Run all three and record each result, even "no hits":

1. WebSearch `site:careers.northeastern.edu "<company>"` and `site:khoury.northeastern.edu "<company>"`.
2. WebSearch `site:northeastern.edu "<company>" co-op`.
3. WebFetch the company's own careers page and look for "co-op", "Northeastern", "university", "campus",
   "intern program".

## Verdict

- A Northeastern-linked hit (a northeastern.edu page naming the firm as a co-op employer, an NU-specific program) or a
  formal co-op program: **ban**. The role is DQ.
- A plain internship program with no Northeastern link: **hold** for the student, with the evidence.
- An incidental word only (a "co-op" mention with no Northeastern link): **clear**, with the quote.

Record it: `python3 -I tools/banned.py record "<company>" --s1 "<result>" --s2 "<result>" --s3 "<result>"
--verdict ban|hold|clear --evidence <url>`. A ban is appended to `profile/banned-employers.md` (never rewritten).
Lines the student marked `[UNBANNED ...]` are allowed.

Never put the student's name or details in a search.
