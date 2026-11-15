# Personal-data scan, to run before every push. Scans every tracked file, every hidden file in the tree, every commit's
# full diff (git log -p --all) and every commit's author and committer, for:
#  - email addresses outside the allowed sample domains (example.com/.org/.edu, users.noreply.github.com, noreply.anthropic.com)
#  - phone numbers that are not 555 numbers
#  - keys and tokens (Anthropic, OpenAI, GitHub, AWS, Slack, Google, private keys, .env assignments)
#  - personal patterns from a private file kept OUTSIDE the repo (default ~/.config/coop-crew/pii-patterns.txt, or
#    --patterns FILE): one case-insensitive regular expression per line (names, employers, projects, addresses)
# Exit 1 on any finding. The sample student (Avery Example, example.com, 555) passes by design.
# usage: python3 -I tools/pii_scan.py [--patterns FILE] [--no-history]
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_EMAIL = re.compile(r'@(?:[\w-]+\.)*(example\.(com|org|net|edu)|users\.noreply\.github\.com|anthropic\.com|localhost|test)\b', re.I)
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PHONE = re.compile(r'(?<![\w.])(?:\+?1[\s.-]?)?\(?\b(\d{3})\)?[\s.-](\d{3})[\s.-](\d{4})\b')
SECRETS = [(r'sk-ant-[A-Za-z0-9_-]{20,}', 'Anthropic key'), (r'\bsk-[A-Za-z0-9]{32,}', 'OpenAI-style key'),
           (r'\bgh[pousr]_[A-Za-z0-9]{30,}', 'GitHub token'), (r'\bAKIA[0-9A-Z]{16}\b', 'AWS key'), (r'\bxox[baprs]-[A-Za-z0-9-]{10,}', 'Slack token'),
           (r'\bAIza[0-9A-Za-z_-]{35}\b', 'Google key'), (r'-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----', 'private key'),
           (r'(?im)^\s*(ANTHROPIC|OPENAI|OPENROUTER|GITHUB|AWS|SMTP|MAIL)_[A-Z_]*(KEY|TOKEN|PASSWORD|SECRET)\s*=\s*\S{8,}', '.env secret')]
# Binary media are not text: a regex over their bytes only finds noise. What they show (the sample student only, in
# docs/img and docs/talk) is checked by eye when they are made.
SKIP = re.compile(r'(^|/)(node_modules|vendor/jev/src|\.git)/|package-lock\.json$|\.(png|jpg|jpeg|gif|pdf|ico|woff2?|mp4|webm|mov|m4a|mp3)$')

def private_patterns(path):
    if not os.path.exists(path): return []
    out = []
    for l in open(path, encoding='utf-8'):
        l = l.strip()
        if l and not l.startswith('#'): out.append(re.compile(l, re.I))
    return out

PUBLIC_POSTINGS = re.compile(r'^templates/demo-cache/')  # cached public job postings: employers' own published addresses

def check_text(text, where, pats, findings):
    public = bool(PUBLIC_POSTINGS.search(where))
    for m in EMAIL.finditer('' if public else text):
        if not ALLOWED_EMAIL.search(m.group(0)): findings.append((where, f'email {m.group(0)}'))
    for m in PHONE.finditer('' if public else text):
        if m.group(2) != '555' and not re.search(r'\d{4}-\d{2}-\d{2}', text[max(0, m.start() - 3):m.end() + 3]):
            findings.append((where, f'phone-like number {m.group(0).strip()}'))
    for rx, what in SECRETS:
        if re.search(rx, text): findings.append((where, what))
    for p in pats:
        m = p.search(text)
        if m: findings.append((where, f'private pattern /{p.pattern}/ matched "{m.group(0)}"'))

def main():
    a = sys.argv[1:]
    pfile = a[a.index('--patterns') + 1] if '--patterns' in a else os.path.expanduser('~/.config/coop-crew/pii-patterns.txt')
    pats = private_patterns(pfile)
    findings = []
    files = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, text=True).stdout.split('\0')
    hidden = [os.path.relpath(os.path.join(d, f), ROOT) for d, _, fs in os.walk(ROOT) for f in fs
              if f.startswith('.') and not SKIP.search(os.path.relpath(os.path.join(d, f), ROOT))]
    untracked_not_ignored = subprocess.run(['git', 'ls-files', '-z', '--others', '--exclude-standard'], cwd=ROOT, capture_output=True, text=True).stdout.split('\0')
    for f in sorted(set(x for x in files + hidden + untracked_not_ignored if x)):
        if SKIP.search(f) or not os.path.isfile(os.path.join(ROOT, f)): continue
        try: t = open(os.path.join(ROOT, f), encoding='utf-8', errors='ignore').read()
        except Exception: continue
        check_text(t, f, pats, findings)
        check_text(f, f'{f} (file name)', pats, findings)
    if '--no-history' not in a:
        log = subprocess.run(['git', 'log', '--all', '-p', '--format=COMMIT %H%nAUTHOR %an <%ae>%nCOMMITTER %cn <%ce>%n%B'],
                             cwd=ROOT, capture_output=True, text=True, errors='ignore').stdout
        chunk, commit, path = [], 'history', ''
        def flush():
            if chunk and not SKIP.search(path or 'x'): check_text('\n'.join(chunk), (path or commit) if not path else path, pats, findings)
        for line in log.splitlines():
            if line.startswith('COMMIT ') or line.startswith('diff --git '):
                flush(); chunk = []
                if line.startswith('COMMIT '): commit, path = f'history {line[7:15]}', ''
                else: path = line.split(' b/', 1)[-1]
                continue
            chunk.append(line)
        flush()
    seen = set(); out = []
    for w, f in findings:
        if (w, f) not in seen: seen.add((w, f)); out.append(f'{w}: {f}')
    print(f'pii scan: {len(files)} tracked files, {len(hidden)} hidden files, history {"skipped" if "--no-history" in a else "included"}, '
          f'{len(pats)} private patterns' + ('' if pats else f' (none: {pfile} is missing)'))
    print('\n'.join(out) or 'no findings')
    sys.exit(1 if out else 0)

if __name__ == '__main__':
    main()
