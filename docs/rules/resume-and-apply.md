# Resume and application rules

- One page, text only, single column, built by `python3 -I tools/resume.py <id>` from `out/<id>/resume.md` (format at
  the top of that file) with `templates/resume/resume.html`. The build fails unless the PDF is exactly one page.
- Option A header: the name, a thin rule, the posting's exact job title, one centered middot contact line with GitHub.
- Order: Summary (2 to 3 lines), Skills, Experience, Projects, Education.
- Every claim from `profile/facts.md`; numbers exactly as written there, with their marks (+, ~, x). The build and the
  checker fail on any number or name not in the facts or the posting.
- Reweight and reorder bullets to the posting's top needs; never add a claim. Drop what does not fit to stay on one page.
- No colons in application writing, no em dashes, no banned words, the student's spelling.
- Answers and cover notes follow the posting's needs in its own order. A cover note only when there is a field for one or
  the student asked.
- File names: `out/<id>/resume.pdf`, `answers.md` (`## <question label>` per answer), `cover.md`, `field-log.md`,
  `questions.json`, `brief.md`, `person.md`, `soft-flags.md`.
