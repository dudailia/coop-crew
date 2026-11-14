#!/usr/bin/env bash
# Acceptance test 1, simulated: a fresh clone into an empty folder with an EMPTY HOME (no npm cache, no Playwright
# browsers, no Claude login), then install.sh, then the demo. It times both. A real fresh macOS user account, and the live
# /demo inside Claude Code, are the full test; this is the stand-in that runs unattended.
# usage: tests/acceptance_fresh_install.sh [--keep]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/coop-fresh.XXXX)"
export HOME="$T/home"; mkdir -p "$HOME"
unset PLAYWRIGHT_BROWSERS_PATH COOP_STATE COOP_JEV COOP_MAIL_ADAPTER
git clone -q "$REPO" "$T/coop-crew"
cd "$T/coop-crew"
S=$(date +%s)
./install.sh > "$T/install.log" 2>&1 || { tail -30 "$T/install.log"; exit 1; }
I=$(( $(date +%s) - S ))
tail -22 "$T/install.log"
S=$(date +%s)
python3 -I tools/demo.py run --offline --no-open > "$T/demo-offline.log" 2>&1 || { cat "$T/demo-offline.log"; exit 1; }
O=$(( $(date +%s) - S ))
S=$(date +%s)
python3 -I tools/demo.py prepare > "$T/demo-live.log" 2>&1 || { cat "$T/demo-live.log"; exit 1; }
L=$(( $(date +%s) - S ))
grep -E "Boards:|For the screener" "$T/demo-live.log"
grep -E "Demo done|Submitted|Run /setup" "$T/demo-offline.log"
echo "RESULT install ${I}s (limit 300s), offline demo ${O}s, live board scan and pick ${L}s"
[ "$I" -lt 300 ] || { echo "FAIL: install took ${I}s"; exit 1; }
[ "${1:-}" = "--keep" ] || rm -rf "$T"
