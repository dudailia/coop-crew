# Publishing coop-crew

The exact steps to make the repository public, push it, and create the v1.0 release with the demo video (sections 0 to
3), and to publish a later version such as v1.1 (section 5). Run them from the repo root, in order. Each block stops at
the first failure (`set -e`).

## 0. Preflight (local, changes nothing)

```
set -e
git status --short                       # must print nothing
git log -1 --format='%h %an <%ae>'       # dudailia <239183685+dudailia@users.noreply.github.com>
test "$(git log --all --format='%ae%n%ce' | sort -u)" = "239183685+dudailia@users.noreply.github.com"
git tag -n1 v1.0                         # the release tag, on the last commit
test "$(git rev-list -n1 v1.0)" = "$(git rev-parse HEAD)"
python3 -m unittest discover -s tests    # 36 tests, OK
/usr/bin/python3 -m unittest discover -s tests 2>/dev/null || python3.9 -m unittest discover -s tests   # again on Python 3.9, the oldest supported (macOS's own)
npm run test:nuworks                     # 11 tests, pass
python3 -I tools/pii_scan.py             # "no findings" (uses ~/.config/coop-crew/pii-patterns.txt)
gitleaks git --no-banner .               # "no leaks found"
ls -l docs/talk/demo.mp4                 # gitignored, attached to the release below (v1.1: 30 fps, 60 s)
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

## 1b. Already published: push fixes into v1.0 (only within a day or so of the first publish)

Run the preflight above without its last line (the repo exists), after moving the tag to the fixed commit:

```
set -e
git tag -f -a v1.0 -m "coop-crew v1.0" && git push origin main && git push -f origin v1.0
gh release edit v1.0 --notes-file docs/releases/v1.0.md
gh release view v1.0 --json assets,tagName --jq '.tagName, .assets[].name'   # v1.0, demo.mp4
```

Then skip to section 3.

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
bash tests/acceptance_fresh_install.sh                                   # empty HOME: install, /crew-doctor, /demo --offline
./install.sh                                                             # the resume tests need Playwright from the install
python3 -m unittest discover -s tests                                    # 36 tests, OK
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
- Upload the social preview by hand (GitHub has no API for it): Settings, General, Social preview, Edit, Upload an
  image, and pick `docs/social-preview.png` (1280x640).

## 5. A new version (v1.1 and later)

Record the media from the offline demo first (`tools/record_demo.sh --offline`: `docs/talk/demo.mp4` and
`docs/img/demo.gif`, checked for even motion and size), write `docs/releases/vX.Y.md` and the CHANGELOG entry, commit,
then run the preflight with `V` in place of v1.0:

```
set -e
V=v1.1
git tag -a $V -m "coop-crew $V" && git push origin main && git push origin $V
gh release create $V docs/talk/demo.mp4 --verify-tag --title "coop-crew $V" --notes-file docs/releases/$V.md --latest
gh release view $V --json assets,tagName --jq '.tagName, .assets[].name'   # v1.1, demo.mp4
gh repo edit dudailia/coop-crew --template --enable-discussions --homepage https://github.com/dudailia/coop-crew/releases/latest
gh run list --workflow tests.yml --limit 1                                    # completed, success: the README badge is green
```

Then section 3 with `$V` for v1.0 in the release-video URL.

## Undo

Until someone else has cloned it: `gh release delete v1.0 --yes`, then `gh repo edit dudailia/coop-crew --visibility
private --accept-visibility-change-consequences`, or `gh repo delete dudailia/coop-crew --yes` (needs the `delete_repo`
scope: `gh auth refresh -s delete_repo`).
