#!/usr/bin/env bash
# Acceptance test 10, stand-in: WSL is Ubuntu on Windows; this runs the same install in an Ubuntu container (Node 22,
# Python 3), then the .eml adapter tests and the whole code-level suite. Real WSL on a Windows machine is the full test.
# usage: tests/acceptance_linux_docker.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/coop-linux.XXXX)"
git clone -q "$REPO" "$T/coop-crew"
docker run --rm -v "$T/coop-crew:/src:ro" ubuntu:24.04 bash -lc '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq >/dev/null && apt-get install -y -qq git python3 curl ca-certificates tzdata >/dev/null
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null 2>&1 && apt-get install -y -qq nodejs >/dev/null
  cp -r /src /root/coop-crew && cd /root/coop-crew
  echo "== install.sh =="; START=$(date +%s); ./install.sh 2>&1 | tail -20; echo "install took $(( $(date +%s) - START ))s"
  echo "== eml adapter (test 10) =="; python3 -m unittest tests.test_acceptance.T10_EmlAdapter -v 2>&1 | tail -6
  echo "== full suite on Linux =="; python3 -m unittest discover -s tests 2>&1 | tail -3
  echo "== doctor =="; python3 -I tools/crew_doctor.py | tail -8
'
rm -rf "$T"
