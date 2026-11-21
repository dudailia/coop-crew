#!/usr/bin/env bash
# Acceptance test 1, simulated: a fresh clone into an empty folder with an EMPTY HOME (no npm cache, no Playwright
# browsers, no Claude login), then install.sh, then the demo. It times both. A real fresh macOS user account, and the live
# /demo inside Claude Code, are the full test; this is the stand-in that runs unattended.
# Steps: install.sh, crew_doctor.py (/crew-doctor, must report 0 problems), demo.py start --offline (/demo --offline),
# demo.py prepare (the live board scan).
# usage: tests/acceptance_fresh_install.sh [--keep]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/coop-fresh.XXXX)"
export HOME="$T/home"; mkdir -p "$HOME"
unset PLAYWRIGHT_BROWSERS_PATH COOP_STATE COOP_JEV COOP_MAIL_ADAPTER
# A new Mac student has only macOS's own Python (3.9), not a newer one from Homebrew or conda: use it when it is there.
[ "$(uname)" = Darwin ] && [ -x /usr/bin/python3 ] && export PATH="/usr/bin:$PATH"
git clone -q "$REPO" "$T/coop-crew"
cd "$T/coop-crew"
S=$(date +%s)
./install.sh > "$T/install.log" 2>&1 || { tail -30 "$T/install.log"; exit 1; }
I=$(( $(date +%s) - S ))
tail -22 "$T/install.log"
python3 -I tools/crew_doctor.py > "$T/doctor.log" 2>&1 || { cat "$T/doctor.log"; exit 1; }   # what /crew-doctor runs
grep -E "problem\(s\)" "$T/doctor.log"
grep -q "^0 problem(s)" "$T/doctor.log" || { cat "$T/doctor.log"; exit 1; }
S=$(date +%s)
python3 -I tools/demo.py start --offline --no-open > "$T/demo-offline.log" 2>&1 || { cat "$T/demo-offline.log"; exit 1; }   # /demo --offline
O=$(( $(date +%s) - S ))
grep -q "Submitted: 0. Sent: 0." "$T/demo-offline.log" || { cat "$T/demo-offline.log"; exit 1; }
grep -q "1 ready" "$T/demo-offline.log" || { echo "offline demo built no review pack"; cat "$T/demo-offline.log"; exit 1; }
S=$(date +%s)
python3 -I tools/demo.py prepare > "$T/demo-live.log" 2>&1 || { cat "$T/demo-live.log"; exit 1; }
L=$(( $(date +%s) - S ))
grep -E "Boards:|For the screener" "$T/demo-live.log"
grep -E "Demo done|Submitted|Run /setup" "$T/demo-offline.log"
echo "RESULT install ${I}s (limit 300s), offline demo ${O}s, live board scan and pick ${L}s"
[ "$I" -lt 300 ] || { echo "FAIL: install took ${I}s"; exit 1; }
[ "${1:-}" = "--keep" ] && echo "kept: $T/coop-crew" || rm -rf "$T"
