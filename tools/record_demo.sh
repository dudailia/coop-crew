#!/usr/bin/env bash
# Runs /demo on the made-up sample student, then records a 60 to 90 second screen video of the result pages
# (TODAY.html, the review pack, the one-page resume, the tracker) and saves it as docs/talk/demo.mp4
# (gitignored: attach it to the GitHub release).
#   tools/record_demo.sh             live /demo through Claude Code (`claude -p "/demo"`, about 4 minutes, your plan)
#   tools/record_demo.sh --offline   the demo without agents (tools/demo.py run --offline), for no Claude access or Wi-Fi
#   tools/record_demo.sh --no-run    record the demo/ pages already there
# Always the sample student (COOP_DEMO_SAMPLE=1), never your profile. Sends and submits nothing (jev and Mail mocked).
# Needs: Node with Playwright's Chromium (./install.sh), ffmpeg (brew install ffmpeg), and for the live run, Claude Code.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=docs/talk/demo.mp4
mode=live
case "${1:-}" in --offline) mode=offline ;; --no-run) mode=none ;; '') ;; *) echo "usage: $0 [--offline|--no-run]"; exit 2 ;; esac
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing: brew install ffmpeg (or apt install ffmpeg)"; exit 1; }
[ -e STOP ] && { echo "STOP: the kill switch is on; /crew-resume first"; exit 3; }

export COOP_DEMO_SAMPLE=1 COOP_DEMO_NO_OPEN=1 COOP_JEV=mock COOP_MAIL_ADAPTER=mock
start=$(date +%s)
case "$mode" in
  live)
    command -v claude >/dev/null || { echo "Claude Code (claude) is not on PATH; use --offline"; exit 1; }
    echo "running /demo through Claude Code (about 4 minutes)..."
    claude -p "/demo" > logs/record-demo-claude.txt 2>&1 || { echo "/demo failed; see logs/record-demo-claude.txt (or use --offline)"; exit 1; } ;;
  offline)
    python3 -I tools/demo.py run --offline --no-open ;;
esac
[ "$mode" = none ] || echo "demo finished in $(( $(date +%s) - start )) s"

mkdir -p docs/talk logs
node tools/record_demo.mjs demo logs/demo-recording.webm
ffmpeg -loglevel error -y -i logs/demo-recording.webm -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart -an "$OUT"
rm -f logs/demo-recording.webm
secs=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
echo "saved $OUT: ${secs%.*} s, $(( $(wc -c < "$OUT") / 1024 )) KB"
awk -v s="$secs" 'BEGIN { exit !(s >= 60 && s <= 90) }' || { echo "warning: the video is ${secs%.*} s, outside 60 to 90 s"; exit 1; }
