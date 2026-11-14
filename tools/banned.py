# Self-developed co-op mode: the banned-list check (from fintech-outreach-eu's NUworks checks). A self-developed co-op
# cannot be with an employer that recruits through NUworks. Every employer is checked:
#   check    in code: the banned list (profile/banned-employers.md) and never-apply (locks.md), employer-wide and under any
#            common spelling ("Acme Robotics" = "ACME-Robotics, LLC" = "AcmeRobotics" = "Acme Robotics Boston").
#   record   the screener's three web checks, which only an agent with web search can run (banned-check skill):
#            (1) site:careers.northeastern.edu and site:khoury.northeastern.edu "<company>"
#            (2) site:northeastern.edu "<company>" co-op
#            (3) the company's own careers page: "co-op", "Northeastern", "university", "campus", "intern program"
#            A Northeastern-linked hit or a formal co-op program bans the employer (appended to banned-employers.md,
#            never rewritten); a plain internship program with no Northeastern link is held for the student;
#            an incidental word is clear, with the quote recorded.
# usage: python3 -I tools/banned.py check "<company>"
#        python3 -I tools/banned.py record "<company>" --s1 "..." --s2 "..." --s3 "..." --verdict ban|hold|clear [--evidence URL]
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

LOG = f'{K.PROFILE}/banned-checks.jsonl'

def check(company):
    """(verdict, detail): 'blocked' when listed (any spelling), 'clear-list' when not on any list (the web checks still run)."""
    for listed in K.banned_list():
        if K.matches(company, listed): return 'blocked', f'on the banned list as "{listed}"'
    for listed in K.never_list():
        if K.matches(company, listed): return 'blocked', f'on the never-apply list as "{listed}"'
    for x in recorded():
        if K.matches(company, x['company']) and x['verdict'] in ('ban', 'hold'):
            return ('blocked' if x['verdict'] == 'ban' else 'hold'), f"three-step check {x['at'][:10]}: {x['verdict']}"
    return 'clear-list', 'not on the banned or never-apply list; run the three web checks if not done'

def recorded():
    out = []
    if os.path.exists(LOG):
        for l in open(LOG, encoding='utf-8'):
            try: out.append(json.loads(l))
            except Exception: pass
    return out

def record(company, s1, s2, s3, verdict, evidence=''):
    if verdict not in ('ban', 'hold', 'clear'): raise SystemExit('verdict is ban, hold or clear')
    if not (s1 and s2 and s3): raise SystemExit('all three checks need a result (--s1, --s2, --s3), even "no hits"')
    x = {'at': f'{K.now():%F %T}', 'company': company, 's1': s1, 's2': s2, 's3': s3, 'verdict': verdict, 'evidence': evidence}
    os.makedirs(K.PROFILE, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f: f.write(json.dumps(x, ensure_ascii=False) + '\n')
    if verdict == 'ban':
        new = not os.path.exists(K.BANNED_FILE)
        with open(K.BANNED_FILE, 'a', encoding='utf-8') as f:  # append only, never rewritten
            if new: f.write('# Banned employers (self-developed co-op mode)\n\n')
            f.write(f'- {company} | {evidence or s1[:120]} ({x["at"][:10]}, three-step check)\n')
    print(f'{company}: {verdict} recorded' + (' and added to banned-employers.md' if verdict == 'ban' else ''))

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'check':
        v, d = check(a[1]); print(f'{a[1]}: {v} ({d})'); sys.exit(0 if v == 'clear-list' else 1)
    if len(a) >= 2 and a[0] == 'record':
        opt = lambda k: a[a.index(k) + 1] if k in a else ''
        record(a[1], opt('--s1'), opt('--s2'), opt('--s3'), opt('--verdict'), opt('--evidence')); sys.exit(0)
    sys.exit('usage: banned.py check "<company>" | record "<company>" --s1 .. --s2 .. --s3 .. --verdict ban|hold|clear')
