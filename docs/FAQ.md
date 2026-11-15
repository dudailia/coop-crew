# FAQ

**Does it apply for me?** It prepares each application (resume, answers, the filled form) and submits only the ones you
approve, one id at a time, with `/approve <id>`. NUworks applications you always submit yourself in NUworks.

**Does it send emails?** In prepare mode (the default) it only saves drafts you send yourself. Even in send mode (Mac Mail
only) it sends only emails you approved, in the recipient's morning window, at most 10 a day by default and never more
than 40.

**Can it make things up?** Every number and name in a resume, answer or email must be in your `profile/facts.md` or the
posting; the checker and the resume build fail otherwise. Work authorization is your own sentence, word for word.

**How does it use NUworks?** By default only through your own email and files: the inbox agent reads NUworks job-alert
emails (from searches you saved in NUworks) and postings you save from NUworks into `data/nuworks-import/`. No NUworks
page is loaded, and you apply in NUworks yourself.

**Is the NUworks browser reader allowed?** Symplicity's terms of use, which govern NUworks, prohibit automated access
("automated software, tools, devices, agents, scripts robots [...] browsers [...] to navigate, search, access") without
Symplicity's prior permission. The Northeastern co-op office approved read-only use, but that is not Symplicity's
permission. So the reader stays off: it turns on only if you type an acknowledgement after that notice
(`mcp/nuworks/APPROVAL.md`, `GUIDE.md`).

**What is a self-developed co-op mode?** A co-op you find yourself cannot be with an employer that recruits through
NUworks. In that mode every employer is checked against your banned list (any spelling) and with three web checks.

**Does it use LinkedIn?** It never automates or scrapes LinkedIn. It may draft a note to a person with a verified profile;
you send it by hand.

**What does it cost?** The code is free (MIT). It runs on your own Claude plan; a daily run uses a good share of a Pro
plan's limits.

**What if I want to stop?** `/stop`. Everything stops at its next step. `/crew-resume` turns it back on.

**Windows?** Yes, through WSL (`install.ps1`). Email is written as `.eml` drafts you open in your own client.
