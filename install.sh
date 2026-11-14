#!/usr/bin/env bash
# coop-crew installer: macOS, Linux, or Windows through WSL. No API keys; Claude Code runs on your own Claude plan.
#   ./install.sh            install everything
#   ./install.sh --no-jev   skip jev-job-search (the form filler)
# It checks python3 3.9+, node 18+ and git; installs the Node packages and Playwright's Chromium; installs the patched
# jev-job-search (Node 22+ only); keeps the NUworks server disabled; runs the health check; prints one next step.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
say() { printf '\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\033[31mStopped: %s\033[0m\n' "$*" >&2; exit 1; }
START=$(date +%s)

# ---- 1. system ----
case "$(uname -s)" in
  Darwin) OS=macos ;;
  Linux) if grep -qi microsoft /proc/version 2>/dev/null; then OS=wsl; else OS=linux; fi ;;
  *) fail "unsupported system $(uname -s). On Windows, run install.ps1 (it uses WSL)." ;;
esac
say "coop-crew install ($OS)"

command -v git >/dev/null || fail "git is missing. macOS: xcode-select --install. Linux/WSL: sudo apt install git"
command -v python3 >/dev/null || fail "python3 is missing. macOS: xcode-select --install. Linux/WSL: sudo apt install python3"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || fail "python3 is $(python3 -V 2>&1); 3.9 or newer is needed"
python3 -c 'import sqlite3, zoneinfo' 2>/dev/null || fail "python3 lacks sqlite3 or zoneinfo; install the full python3 package"
command -v node >/dev/null || fail "Node.js is missing. Install Node 18 or newer (22+ for the form filler) from https://nodejs.org or with nvm"
NODE_MAJOR=$(node -p 'process.versions.node.split(".")[0]')
[ "$NODE_MAJOR" -ge 18 ] || fail "Node.js $(node -v) is too old; 18 or newer is needed"
say "ok: git, python3 $(python3 -c 'import platform; print(platform.python_version())'), node $(node -v)"

# ---- 2. dependencies (Python uses the standard library only) ----
say "Installing Node packages..."
npm install --no-audit --no-fund --loglevel=error
say "Installing Playwright's Chromium (resume PDFs and the NUworks reader)..."
if [ "$OS" != macos ]; then npx --no-install playwright install --with-deps chromium 2>/dev/null || npx --no-install playwright install chromium; else npx --no-install playwright install chromium; fi

# ---- 3. the form filler (patched jev-job-search) ----
if [[ " $* " == *" --no-jev "* ]]; then
  say "Skipping jev-job-search (--no-jev). Applications are prepared as review packs you submit by hand."
elif [ "$NODE_MAJOR" -lt 22 ]; then
  say "Skipping jev-job-search: it needs Node 22+, you have $(node -v). Everything else works; applications are prepared as review packs you submit by hand. Upgrade Node and run vendor/jev/install.sh later."
else
  bash vendor/jev/install.sh || say "jev-job-search did not install (see above). Everything else works; run vendor/jev/install.sh again later."
fi

# ---- 4. state folders, and NUworks off until /setup turns it on ----
mkdir -p profile assets data/incoming out logs
LOCAL=.claude/settings.local.json
if [ ! -f "$LOCAL" ]; then
  printf '{\n  "disabledMcpjsonServers": ["nuworks"]\n}\n' > "$LOCAL"
  say "NUworks reader registered but disabled (see mcp/nuworks/APPROVAL.md)."
fi
python3 -I tools/pipeline.py init >/dev/null

# ---- 5. health check ----
python3 -I tools/crew_doctor.py --install || true
say "Installed in $(( $(date +%s) - START )) s."
say "Next step: run  claude  in this folder, then type  /setup   (or /demo to see it work with a sample student first)."
