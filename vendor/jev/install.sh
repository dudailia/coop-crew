#!/usr/bin/env bash
# Installs jev-job-search (MIT, by Qendrim Beka) at the pinned commit into vendor/jev/src and applies jev-fixes.patch:
# prepare mode by default (nothing is submitted until the student approves that form), focus ordering, the score floor,
# and the visa-type answer gate (for example F-1 CPT, never H-1B). Needs Node.js 22+ and git.
set -euo pipefail
cd "$(dirname "$0")"
. ./PIN
major=$(node -p 'process.versions.node.split(".")[0]')
[ "$major" -ge 22 ] || { echo "jev-job-search needs Node 22+; you have $(node -v). Skipped."; exit 1; }
if [ ! -d src/.git ]; then git clone --quiet "$repo" src; fi
cd src
git fetch --quiet origin
git checkout --quiet "$commit"
if git apply --check "../$patch" 2>/dev/null; then git apply "../$patch"; echo "jev-fixes.patch applied"
elif git apply --check --reverse "../$patch" 2>/dev/null; then echo "jev-fixes.patch already applied"
else echo "jev-fixes.patch does not apply to $commit"; exit 1; fi
npm install --no-audit --no-fund --loglevel=error
for f in profile.json bank.json policy.json voice.local.md; do [ -f "data/$f" ] || cp "../templates/$f" "data/$f"; done
echo "jev-job-search ready in vendor/jev/src (prepare mode). /setup fills data/profile.json from your profile."
