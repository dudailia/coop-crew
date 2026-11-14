#!/usr/bin/env bash
# Installs the anti-slop pattern catalogues (unslop, humanizer v3.1.0, declauding) into
# .claude/skills/anti-slop/references/ on this machine. They are not committed to the repo: their licenses are not yet
# confirmed for redistribution (THIRD_PARTY.md). Two ways:
#   tools/fetch_antislop_refs.sh --from <folder that holds unslop/, humanizer/, declauding/>
#   tools/fetch_antislop_refs.sh            (downloads the pinned versions in refs.lock, once their URLs are filled in)
# The skill works without them (hard locks plus a fallback list).
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=.claude/skills/anti-slop/references
LOCK=.claude/skills/anti-slop/refs.lock
if [ "${1:-}" = "--from" ]; then
  SRC="${2:?folder}"
  for d in unslop humanizer declauding; do [ -f "$SRC/$d/SKILL.md" ] || { echo "missing $SRC/$d/SKILL.md"; exit 1; }; done
  mkdir -p "$DEST"; for d in unslop humanizer declauding; do rm -rf "${DEST:?}/$d"; cp -R "$SRC/$d" "$DEST/$d"; done
  echo "anti-slop catalogues installed from $SRC into $DEST (local only, gitignored)"; exit 0
fi
missing=0
while IFS='|' read -r name version url; do
  case "$name" in ''|\#*) continue ;; esac
  if [ -z "$url" ]; then echo "$name $version: no download URL pinned yet (needs the author's OK and license)"; missing=1; continue; fi
  mkdir -p "$DEST/$name"; curl -fsSL "$url" -o "$DEST/$name/SKILL.md" && echo "$name $version installed"
done < "$LOCK"
[ $missing = 0 ] || echo "Some catalogues were not installed; the anti-slop skill uses its fallback list until they are."
