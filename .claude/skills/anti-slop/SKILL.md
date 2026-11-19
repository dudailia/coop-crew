---
name: anti-slop
description: >-
  Use this skill before you write or edit any outgoing copy: cold emails,
  follow-ups, recruiter replies, resumes and resume summaries, cover letters,
  job application answers, bios, and posts for X or LinkedIn. Also use it
  whenever someone asks to declaude, de-slop, humanize, or remove AI tells from
  a draft. It cleans AI-sounding prose without changing what it says, never adds
  a fact, number, name, date, quote, or citation, and keeps approved hooks and
  locked numbers. Its tells are listed in catalogue.md, next to this file.
  Do not use it for BLUF task logs,
  SBAR handoffs, knowledge or decision pages, code, or locked legal text.
---
# Anti-slop

Adapted for coop-crew (MIT, contributed with the author's permission; see THIRD_PARTY.md).

Clean outgoing prose so it reads like its author wrote it. Keep what it says, and add nothing.

This file holds the hard locks, the scope, and the order of work. The tells are in `catalogue.md`, next to this file: coop-crew's own numbered list, written for this repo. When the catalogue disagrees with this file, this file wins.

## Hard locks

These hold for every pass, in every mode.

1. **Add no facts.** Never add a fact, number, name, date, quote, claim, or citation that is not in the source or given by the author (the person whose name goes on the text). Opinions and reactions count too: keep the ones the author wrote, and add none. If a sentence needs a detail you do not have, ask for it or write the plain version without it. A plainer sentence is often vaguer, and that is fine. Why: resumes, applications, and outreach go out under a real name. An invented detail is a false claim, and it can cost a job or a client.
2. **Keep approved hooks and numbers.** Copy them exactly, with their marks: an approved campaign opener the author locked, and resume figures such as a volume with a "+", a tilde percentage, or an "about 2×". A hook or number is approved when the author or the task says so, or when it comes from a locked template, `profile/facts.md`, or `profile/voice.md`. No catalogue rule overrides an approval. Why: the author chose these lines on purpose, and a number that loses its "+" or "~" makes a different claim.
3. **Leave locked or approved copy alone unless it has real slop.** Real slop is a strong tell that the author would not choose, such as a hype word (catalogue 8), chatbot residue (catalogue 18), or a run of em dashes. Then make the smallest fix and name the line in your note, so the author can undo it. Legal text, compliance lines (the footer address, the opt-out line, an AI disclosure), and template fields such as `{{firstName}}` never change.
4. **Clean mode by default.** Return the cleaned text and nothing else. Use embedded mode only when another task calls this pass as one of its steps. See "Return the text".
5. **Write internal prose in STE-lite.** For a note to the team or to the owner, use short clear sentences, active voice, and simple words. Treat the length caps (about 20 words for an instruction, 25 for other sentences) as a check, not a trimmer. Do not make every sentence the same length, because a run of equal short sentences is a tell too.
6. **Stay in scope.** Do not run this pass on BLUF task logs, SBAR handoffs, or shared knowledge and decision pages. Those formats have their own rules, and a style pass there adds risk without helping a reader.
7. **No hooks and no scripts.** This skill has no Stop hook and runs no script. It never sends text to a model API or downloads anything. `tools/check_msgs.py` is the separate lock-list check (numbers and names against the facts).
8. **Cite catalogue rules by number.** Catalogue numbers are stable IDs. Cite a rule as "catalogue 13" and never renumber. Read `catalogue.md` instead of assuming a fixed list.

## When to use it

Use it before you write or edit:

- email: cold outreach, follow-ups, and replies to recruiters or clients
- resumes, resume summaries, and cover letters
- answers to job application questions
- posts for X, LinkedIn, or similar, and short bios

Also use it when someone asks you to declaude, de-slop, or humanize a draft, or to remove AI tells from copy.

When you write new copy, draft it from the facts in the task, from the author, or from `profile/facts.md`. Then run this pass on your own draft before you hand it over. Hard lock 1 applies to your draft too.

Do not use it for:

- BLUF task logs, SBAR handoffs, and shared knowledge or decision pages (hard lock 6)
- code, quoted text, fiction, and poetry
- docs, READMEs, RFCs, and PR descriptions
- a lookup of one rule: open `catalogue.md` and cite the number

Stop instead of rewriting in one case. If an application asks the applicant to confirm that an answer is their own work, written without AI, do not draft or polish that answer. Flag it to the student (see the form-answers skill and `profile/locks.md`). This pass makes prose clear and true to its author. It is not a way to hide who wrote a text.

## Order of work

1. **List the locks.** Before you edit, write down what must not change: approved hooks; every number with its marks (`+`, `~`, `%`, `×`, ranges, times); names, dates, quotes, and URLs; template fields; and the sign-off, footer, and opt-out line.
2. **Read the whole piece once.** Say its point in one sentence. Note any contradiction or doubtful claim, and report it instead of fixing it silently. Only the author knows which version is true.
3. **Mark the tells.** Read `catalogue.md`. A strong tell justifies an edit on one sighting. A weak tell needs other tells near it.
4. **Make the smallest edit that removes the slop.** Keep the author's voice, opinions, rhythm, and the shape of the genre (see "Genre rules"). Leave a plain line as it is. The right edit to a clean draft is no edit. When you cut a staged shape, keep the claim inside it. "I didn't just build the agents, I led the deployments" says the author did both, so it becomes "I built the agents and led the deployments", not "I led the deployments".
5. **Check against the source, claim by claim.** Every number, name, date, quote, URL, and claim in the rewrite must be in the source or come from the author. Nothing on the lock list changed. No claim, hedge, ranking, or condition was dropped, including a claim inside a shape you cut. When you are not sure, keep the source's wording.
6. **Return the text** in the right mode.

## Genre rules

- **Email.** Keep the hook, the ask, the opt-out line, the signature, and the footer word for word. Keep the short paragraphs. Do not add a subject line, a P.S., a link, or a second ask. Stay inside any word limit.
- **Resume.** Keep bullets as bullets and keep the one-page shape. Clipped, verbless bullets are normal in a resume, so do not expand them into full sentences. Catalogue 7 and 15, and any rule about sentence fragments, do not apply to bullets. Keep numbers, dates, and date ranges exactly as printed, including any "+", "~", or "×" marks. Never move a number to another line or role.
- **Application answer.** Answer the question in the first sentence. Stay inside the word limit. Keep each number next to the claim it supports.
- **Post.** Stay inside the platform limit. Keep the handles, links, and hashtags the author wrote, and add none.

Example. An approved opener the author locked, such as a short heads-up line that also contains exact times, stays as written. A catalogue rule that would cut the opener as a staged run-up does not apply: it is an approved hook, and every time in the line is a locked number. That line needs no edit.

## Return the text

**Clean mode (default).** Return the cleaned text, ready to paste, and nothing else. Why: the text goes straight into an outreach tool, a resume, or a portal form, often through another step, and commentary around it gets pasted by mistake. Do not describe, explain, or justify your edits; the author can compare the versions. Two short additions are allowed after the text. If you made no edit, say so in one line. If the author must decide something (a contradiction, a missing fact, or an edit to approved copy), say what in one or two sentences. Do not add a list of tells, a tally, annotations, or a draft-then-final pair.

**Embedded mode.** When another skill or task calls this pass as one step, for example a packet build that cleans its own draft, return only the final text to that step. Put any problem in that task's notes, never inside the text.

## Where this file overrides the catalogue

- Catalogue 1 says to state Y in a "not just X, but Y" contrast. Keep X too when it is the author's claim (see step 4 of "Order of work").
- Parentheses are fine when the text inside is a full grammatical unit, but not as a dash substitute (catalogue 13 and 29).
- An author's own writing sample beats every catalogue rule. If the author uses dashes in their own emails, keep them at their rate. Only the hard locks rank above the sample.
