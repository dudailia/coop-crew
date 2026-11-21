# Contributing to coop-crew

Thanks for helping. coop-crew acts for a student under their real name, so changes are judged first on whether they
keep its promises: nothing submitted or sent without the student's approval of that exact item, no invented facts, no
NUworks automation by default, and personal data stays on the student's machine.

## Before you start

- **Bugs and ideas**: open an issue with the templates. Reproduce with the bundled sample student (`/demo`, or
  `python3 -I tools/demo.py run --offline`), never with your own profile, resume or emails.
- **Safety problems**: report them privately (see [SECURITY.md](SECURITY.md)), not in an issue.
- **Bigger changes** (a new agent, a new source of roles, anything that sends, submits or reads mail): open an issue
  first so we can agree on the design.

## Setting up

```
git clone https://github.com/dudailia/coop-crew && cd coop-crew && ./install.sh
python3 -m unittest discover -s tests        # all tests must pass
npm run test:nuworks
```

## Rules for changes

1. **No new route out.** Submits go only through `tools/applicant.py` and emails only through `tools/send_due.py`. Do
   not add another way to submit, send or approve, and do not weaken `tools/guard.py`. A change to the guard, the
   approval path or the caps needs a test for both sides: what is still blocked and what is now allowed.
2. **No invented facts.** Anything that writes outgoing text must go through the checker (`tools/check_msgs.py`) and
   use only `profile/facts.md` and the posting.
3. **Sources.** Company-run boards and sites only. No LinkedIn automation, no aggregators, no scraping behind logins.
   NUworks stays email-and-files by default (see `mcp/nuworks/APPROVAL.md`).
4. **Python standard library only** in `tools/`, and **Python 3.9 syntax**: macOS ships 3.9, so no `match`, no
   `X | Y` type hints at runtime, and no backslashes inside f-string braces. On a Mac, run the tests with
   `/usr/bin/python3` too. Node code lives in `mcp/` and the renderers.
5. **No personal data in the repo**, including tests and fixtures. Use the sample student (Avery Example,
   `example.com`, 555 phone numbers). Fixtures modeled on real emails or pages must be made up from scratch, with the
   same structure only.
6. **Third-party text** only with a license that allows redistribution, credited in [THIRD_PARTY.md](THIRD_PARTY.md).
7. **Run every tool as** `python3 -I tools/<name>.py <args>` from the repo root, as the agents do.

## Pull requests

- One topic per pull request, with a test for the change.
- Describe what changes for the student, and how you checked it.
- Run `python3 -I tools/pii_scan.py` before you push. Add your own private patterns (your name, email, employers) to
  `~/.config/coop-crew/pii-patterns.txt`, outside the repo.

By contributing you agree that your contribution is released under the MIT license ([LICENSE](LICENSE)).
