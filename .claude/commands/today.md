---
description: Open today's pages. TODAY.html (review packs), MORNING.md and needs-reply.html.
disable-model-invocation: true
---
!`python3 -I tools/build_today.py && python3 -I tools/morning.py && (open TODAY.html 2>/dev/null || xdg-open TODAY.html 2>/dev/null || wslview TODAY.html 2>/dev/null || true) && (test -f needs-reply.html && (open needs-reply.html 2>/dev/null || xdg-open needs-reply.html 2>/dev/null || true) || true) && cat MORNING.md`

Show the student MORNING.md above in a short summary: what needs them first (questions, replies, deadlines), how many
packs wait for review, and the commands: `/approve <ids>` for what is right, `/skip <ids>` for the rest.
TODAY.html and needs-reply.html are open in their browser.
