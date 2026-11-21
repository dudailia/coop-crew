# Publishing coop-crew v1.0

The exact steps to make the repository public, push it, and create the v1.0 release with the demo video. Run them from
the repo root, in order. Each block stops at the first failure (`set -e`).

## 0. Preflight (local, changes nothing)

```
set -e
git status --short                       # must print nothing
git log -1 --format='%h %an <%ae>'       # dudailia <239183685+dudailia@users.noreply.github.com>
test "$(git log --all --format='%ae%n%ce' | sort -u)" = "239183685+dudailia@users.noreply.github.com"
git tag -n1 v1.0                         # the release tag, on the last commit
test "$(git rev-list -n1 v1.0)" = "$(git rev-parse HEAD)"
python3 -m unittest discover -s tests    # 34 tests, OK
npm run test:nuworks                     # 11 tests, pass
python3 -I tools/pii_scan.py             # "no findings" (uses ~/.config/coop-crew/pii-patterns.txt)
gitleaks git --no-banner .               # "no leaks found"
ls -l docs/talk/demo.mp4                 # 1229869 bytes; gitignored, attached to the release below
gh auth status                           # signed in to github.com as dudailia
gh repo view dudailia/coop-crew >/dev/null 2>&1 && echo "STOP: the repo already exists" && exit 1 || true
```

## 1. Create the public repository and push

```
set -e
gh repo create dudailia/coop-crew --public \
  --description "A crew of Claude Code agents that works your co-op search overnight. Nothing is submitted or sent until you approve it." \
  --source . --remote origin
git push -u origin main
git push origin v1.0
gh repo edit dudailia/coop-crew --add-topic claude-code --add-topic co-op --add-topic job-search --add-topic northeastern
gh api -X PUT repos/dudailia/coop-crew/private-vulnerability-reporting   # SECURITY.md's "Report a vulnerability"
```

## 2. Create the release with the video

```
set -e
gh release create v1.0 docs/talk/demo.mp4 --verify-tag --title "coop-crew v1.0" --notes-file docs/releases/v1.0.md
gh release view v1.0 --json assets --jq '.assets[].name'   # demo.mp4
```

## 3. Verify from a signed-out clone

No GitHub token, no git credential helper, no prompt: what a stranger sees.

```
set -e
T=$(mktemp -d)
env -u GH_TOKEN -u GITHUB_TOKEN GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 \
  git clone -q https://github.com/dudailia/coop-crew "$T/coop-crew"
cd "$T/coop-crew"
git log --all --format='%ae' | sort -u                                   # only the no-reply address
git tag -l v1.0                                                          # v1.0
test ! -e docs/talk/demo.mp4 && echo "video not in git: ok"
python3 -m unittest discover -s tests                                    # 34 tests, OK
python3 -I tools/pii_scan.py --no-history                                # no findings (tree)
curl -s -o /dev/null -w 'release video: %{http_code}\n' -L https://github.com/dudailia/coop-crew/releases/download/v1.0/demo.mp4   # 200
curl -s -o /dev/null -w 'README GIF: %{http_code}\n' https://raw.githubusercontent.com/dudailia/coop-crew/main/docs/img/demo.gif     # 200
curl -s https://api.github.com/repos/dudailia/coop-crew | grep -E '"(visibility|default_branch)"'                                   # public, main
cd - >/dev/null && rm -rf "$T"
```

Then open https://github.com/dudailia/coop-crew in a private browser window: the README GIF plays, the QR code on
slide 12 of `docs/talk/slides.html` opens the repo, and the release page shows `demo.mp4`.

## 4. After publishing (by hand)

- Post the LinkedIn draft yourself (`LINKEDIN.md`, local and gitignored). Nothing in coop-crew posts to LinkedIn.
- Delete the local backup bundles in `logs/` once you are happy with the public history.

## Undo

Until someone else has cloned it: `gh release delete v1.0 --yes`, then `gh repo edit dudailia/coop-crew --visibility
private --accept-visibility-change-consequences`, or `gh repo delete dudailia/coop-crew --yes` (needs the `delete_repo`
scope: `gh auth refresh -s delete_repo`).
