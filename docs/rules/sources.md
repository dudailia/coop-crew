# Where roles come from

Allowed, for scout-web:
- Company-run job boards: Ashby (jobs.ashbyhq.com), Greenhouse (boards.greenhouse.io, job-boards.greenhouse.io),
  Lever (jobs.lever.co), Workable (apply.workable.com), SmartRecruiters, Recruitee, Personio, Workday and the company's
  own careers page. `tools/scan_boards.py` reads the first seven through their public JSON APIs; list boards you find in
  `data/boards.txt` so every run checks them.
- YC's public company directory, VC portfolio pages, and recent funding-round announcements, to find companies. Every
  posting you record must then come from the company's own board or site.
- In the student's regions (`targets.cities`) and cycle (`coop`).

Not allowed: LinkedIn Jobs (and any LinkedIn scraping), Indeed, Glassdoor, Handshake scraping, Wellfound, Simplify and
other community lists, job-alert sites, recruitment agencies, and anything behind a login. NUworks only through the
nuworks server.
