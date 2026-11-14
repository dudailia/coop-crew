---
name: anti-slop
description: >-
  Use this skill before you write or edit any outgoing copy: cold emails,
  follow-ups, recruiter replies, resumes and resume summaries, cover letters,
  job application answers, bios, and posts for X or LinkedIn. Also use it
  whenever someone asks to declaude, de-slop, humanize, or remove AI tells from
  a draft. It cleans AI-sounding prose without changing what it says, never adds
  a fact, number, name, date, quote, or citation, and keeps approved hooks and
  locked numbers. It is the house layer over unslop, humanizer v3.1.0, and
  declauding, so prefer it to those for copy. Do not use it for BLUF task logs,
  SBAR handoffs, knowledge or decision pages, code, or locked legal text.
---
# Anti-slop

Clean outgoing prose so it reads like its author wrote it. Keep what it says, and add nothing.

This file is the house layer. It holds the hard locks, the scope, and the order of work. The pattern catalogues are in `references/`. They are exact copies of the vendored upstream skills and should be replaced as a set when upstream changes. When a catalogue disagrees with this file, this file wins.

In coop-crew the catalogues are not committed to the repository, because their licenses are not yet confirmed for redistribution. `tools/fetch_antislop_refs.sh` installs them into `references/` on the student's machine. If `references/` is missing, apply the hard locks, the genre rules and the fallback list at the end of this file, and say in your note that the catalogues were not available.

## Hard locks

These hold for every pass, in every mode.

1. **Add no facts.** Never add a fact, number, name, date, quote, claim, or citation that is not in the source or given by the author (the person whose name goes on the text). Opinions and reactions count too: keep the ones the author wrote, and add none. If a sentence needs a detail you do not have, ask for it or write the plain version without it. A plainer sentence is often vaguer, and that is fine. Why: resumes, applications, and outreach go out under a real name. An invented detail is a false claim, and it can cost a job or a client.
2. **Keep approved hooks and numbers.** Copy them exactly, with their marks: an approved campaign opener the author locked, and resume figures such as a volume with a "+", a tilde percentage, or an "about 2×". A hook or number is approved when the author or the task says so, or when it comes from a locked template, `profile/facts.md`, or `profile/voice.md`. No catalogue rule overrides an approval. Why: the author chose these lines on purpose, and a number that loses its "+" or "~" makes a different claim.
3. **Leave locked or approved copy alone unless it has real slop.** Real slop is a strong tell that the author would not choose, such as a word from unslop 7, chatbot residue, or a run of em dashes. Then make the smallest fix and name the line in your note, so the author can undo it. Legal text, compliance lines (the footer address, the opt-out line, an AI disclosure), and template fields such as `{{firstName}}` never change.
4. **Clean mode by default.** Return the cleaned text and nothing else. Use embedded mode only when another task calls this pass as one of its steps. See "Return the text".
5. **Write internal prose in STE-lite.** For a note to the team or to the owner, use short clear sentences, active voice, and simple words. Treat the length caps (about 20 words for an instruction, 25 for other sentences) as a check, not a trimmer. Do not make every sentence the same length, because a run of equal short sentences is a tell too.
6. **Stay in scope.** Do not run this pass on BLUF task logs, SBAR handoffs, or shared knowledge and decision pages. Those formats have their own rules, and a style pass there adds risk without helping a reader.
7. **No hooks and no required scripts.** This skill has no Stop hook and no `hooks/hooks.json`. It never requires `declaude_review.py`, which sends text to a model API, or `declaude_rank.py`, which downloads a model. Reading the catalogues is the default path. The local lint and diff helpers are optional (see "Optional helpers").
8. **Cite unslop rules by number.** Unslop rule numbers are stable IDs that other skills cite, such as technical-writing and the Job resume rules. Cite a rule as "unslop 13" and never renumber. The catalogue can gain rules when it updates, so read `references/unslop/SKILL.md` instead of assuming a fixed list.

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
- docs, READMEs, RFCs, and PR descriptions: use technical-writing, which applies unslop
- a lookup of one unslop rule: open `references/unslop/SKILL.md` and cite the number

Stop instead of rewriting in one case. If an application asks the applicant to confirm that an answer is their own work, written without AI, do not draft or polish that answer. Flag it to the student (see the form-answers skill and `profile/locks.md`). This pass makes prose clear and true to its author. It is not a way to hide who wrote a text.

## Order of work

1. **List the locks.** Before you edit, write down what must not change: approved hooks; every number with its marks (`+`, `~`, `%`, `×`, ranges, times); names, dates, quotes, and URLs; template fields; and the sign-off, footer, and opt-out line.
2. **Read the whole piece once.** Say its point in one sentence. Note any contradiction or doubtful claim, and report it instead of fixing it silently. Only the author knows which version is true.
3. **Mark the tells.** Read `references/unslop/SKILL.md` first, because it is short. Then open the other catalogues the draft needs (see "Catalogues"). A strong tell justifies an edit on one sighting. A weak tell needs other tells near it.
4. **Make the smallest edit that removes the slop.** Keep the author's voice, opinions, rhythm, and the shape of the genre (see "Genre rules"). Leave a plain line as it is. The right edit to a clean draft is no edit. When you cut a staged shape, keep the claim inside it. "I didn't just build the agents, I led the deployments" says the author did both, so it becomes "I built the agents and led the deployments", not "I led the deployments".
5. **Check against the source, claim by claim.** Every number, name, date, quote, URL, and claim in the rewrite must be in the source or come from the author. Nothing on the lock list changed. No claim, hedge, ranking, or condition was dropped, including a claim inside a shape you cut. When you are not sure, read "Check what the edit did" in `references/declauding/SKILL.md`.
6. **Return the text** in the right mode.

## Genre rules

- **Email.** Keep the hook, the ask, the opt-out line, the signature, and the footer word for word. Keep the short paragraphs. Do not add a subject line, a P.S., a link, or a second ask. Stay inside any word limit.
- **Resume.** Keep bullets as bullets and keep the one-page shape. Clipped, verbless bullets are normal in a resume, so do not expand them into full sentences. Unslop 33, humanizer §11, and the declauding entry on subjectless fragments do not apply to bullets. Keep numbers, dates, and date ranges exactly as printed, including any "+", "~", or "×" marks. Never move a number to another line or role.
- **Application answer.** Answer the question in the first sentence. Stay inside the word limit. Keep each number next to the claim it supports.
- **Post.** Stay inside the platform limit. Keep the handles, links, and hashtags the author wrote, and add none.

Example. An approved opener the author locked, such as a short heads-up line that also contains exact times, stays as written. A catalogue rule that would cut the opener as a staged run-up does not apply: it is an approved hook, and every time in the line is a locked number. That line needs no edit.

## Return the text

**Clean mode (default).** Return the cleaned text, ready to paste, and nothing else. Why: the text goes straight into an outreach tool, a resume, or a portal form, often through another step, and commentary around it gets pasted by mistake. Do not describe, explain, or justify your edits; the author can compare the versions. Two short additions are allowed after the text. If you made no edit, say so in one line. If the author must decide something (a contradiction, a missing fact, or an edit to approved copy), say what in one or two sentences. Do not add a list of tells, a tally, annotations, or a draft-then-final pair. This replaces "What to return" in the humanizer file and the annotated mode in the declauding file.

**Embedded mode.** When another skill or task calls this pass as one step, for example a packet build that cleans its own draft, return only the final text to that step. Put any problem in that task's notes, never inside the text.

## Catalogues

Open only what the draft needs. Each folder has a `CONTENTS.md` that lists every heading with its line number, so you can open a long file at the right place. The copies keep upstream's folder layout, so links inside each upstream file still work.

| File | What it holds | Open it when |
|---|---|---|
| `references/unslop/SKILL.md` | The house catalogue: short, numbered rules | Every pass. Cite rules by number. |
| `references/humanizer/SKILL.md` | Humanizer v3.1.0: numbered patterns, strongest first, with before and after examples. Long: use `CONTENTS.md`. | Email, answers, and posts. §1 to §5 act on one sighting. §16 covers sales language; §26 covers a reply that re-explains what the reader knows. |
| `references/declauding/SKILL.md` | Declauding's method: the generative test (stating or staging?), overcorrection, signs of a person writing, earned exceptions | A long or heavily staged draft, or when you are tempted to rewrite a lot |
| `references/declauding/references/register.md` | The full register of tells, grouped in families, with before and after pairs. Very long. | Never read it whole. Find the family in the table under "The generative test" in the declauding `SKILL.md`, then use `references/declauding/CONTENTS.md` to open those entries. |
| `references/declauding/references/exceptions.md` | When a flagged shape carries a claim | Before you delete a flagged shape |
| `references/declauding/references/preservation.md` | How a style pass loses or invents claims | When the check step is unsure |
| `references/declauding/references/models/` | Tells of each model's drafts | When you know which model wrote the draft, including you |

## Where this file overrides the catalogues

The catalogues are upstream text, copied without changes. Use them for patterns and method, with these exceptions:

- The declauding file tells you to load it for any prose task and to run scripts at several steps. Ignore both. Scope comes from this file. Skip its Stop hook, its newcomer-read step, `declaude_review.py`, `declaude_rank.py`, and annotated mode.
- The humanizer file is v3.1.0, and it is pinned. Version 4.0.0 and later tell the model to add details that are not in the source, which invents facts. Never fetch or follow a newer humanizer.
- The humanizer "Voice" section lets you add a reaction where the writer would. Do not. Hard lock 1 covers opinions too.
- Unslop 9 and humanizer §1 say to state the point of a "not just X, but Y" contrast directly. Keep X too when it is the author's claim (see step 4 of "Order of work").
- On punctuation, follow unslop: no em dashes in outgoing copy (unslop 13). Parentheses are fine when the text inside is a full grammatical unit, as technical-writing allows, but not as a dash substitute.
- An author's own writing sample beats every catalogue rule. If the author uses dashes in their own emails, keep them at their rate. Only the hard locks rank above the sample.

## Optional helpers

coop-crew does not ship these scripts; `tools/check_msgs.py` is its own lock-list check (numbers and names against the facts). If the vendored declauding scripts are present, two local helpers can help. Both use only the Python standard library and make no network calls. Neither is required.

- `python3 vendor/declauding/scripts/declaude_lint.py DRAFT.md` flags greppable tells with line numbers. A clean report does not prove a clean draft.
- `python3 vendor/declauding/scripts/declaude_diff.py SOURCE.md REWRITE.md` lists the numbers, names, quotes, code, and links that the rewrite lost or added. It is a fast check for hard lock 1.

## Fallback when the catalogues are missing

Use this short list only when `references/` is not installed. It is a reminder of the most common tells, not a replacement for the catalogues.

- No em dashes in outgoing copy. Use a comma, a period, or parentheses around a full unit.
- Cut "not X, but Y" staging when nobody claimed X. Keep X when it is the author's own claim.
- Cut a staged run-up before the point ("Here's the thing:", "The truth is"). Start with the point.
- Cut one-line closers that restate the paragraph as a slogan.
- Break up reflexive groups of three when the third item adds nothing.
- Replace hype words (passionate, excited, cutting-edge, seamless, robust, leverage, synergy) with the plain claim, or drop them.
- Remove chatbot residue ("I hope this helps", "Great question", "Certainly").
- Do not stack hedges ("I believe it might possibly").
- Keep the author's own words, numbers with their marks, names, dates and the sign-off exactly as written.
