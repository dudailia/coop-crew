# /demo: the crew on a sample student, built for a room of 100 people on shared Wi-Fi. State lives in demo/ (never the
# student's own files). Skips NUworks and email entirely; jev and Mail are mocked; it sends and submits nothing, ever.
# Scouts 3 public company boards (a cached copy if the network fails), judges 5 roles, researches 2, builds 1 one-page
# resume and 1 review pack, and opens TODAY.html.
#   prepare  reset demo/, pick the student (their own profile if /setup ran, else the sample), scan the boards, choose 5
#            roles, run the hard rules; prints the ids left for the screener agent
#   finish   gate, pages, open TODAY.html, final check that nothing was submitted or sent
#   run --offline   the whole demo with no agents (stand-ins), for tests and for a room with no Claude access
#   start [--offline]  what /demo runs: prepare, or with --offline (/demo --offline) the whole offline demo
# usage: python3 -I tools/demo.py prepare|finish [--no-open] | run --offline [--no-open] | start [--offline] [--no-open]
import json, os, re, shutil, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = f'{ROOT}/demo'
BOARDS = ['greenhouse:figureai', 'greenhouse:databricks', 'greenhouse:klaviyocampus']
CACHE = f'{ROOT}/templates/demo-cache/roles.json'

def env():
    return {**os.environ, 'COOP_STATE': DEMO, 'COOP_JEV': 'mock', 'COOP_MAIL_ADAPTER': 'mock'}

def tool(name, *args, quiet=False):
    r = subprocess.run([sys.executable, '-I', f'{ROOT}/tools/{name}', *args], env=env(), capture_output=True, text=True)
    if not quiet and (r.stdout or r.stderr).strip(): print('  ' + (r.stdout + r.stderr).strip().replace('\n', '\n  '))
    if r.returncode == 3: print('STOP: the kill switch is on; the demo stops.'); sys.exit(3)
    return r

def stopped(): return any(os.path.exists(p) for p in (f'{ROOT}/STOP', f'{DEMO}/STOP', os.path.expanduser('~/STOP-AGENTS')))

MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']

def relevance(r, words, coop):
    """How likely the screener keeps this role: title words, plus what the posting text says about the student's cycle.
    Titles alone picked roles that were summer-only or Master's-only (live /demo, 2026-11-14), so no pack was built."""
    t = r['title'].lower(); d = (r.get('description') or '').lower()
    season = (coop.get('cycle') or '').lower()
    month = MONTHS[int(coop['start'][5:7]) - 1] if re.fullmatch(r'\d{4}-\d\d-\d\d', coop.get('start', '')) else ''
    s = sum(1 for w in words if w in t)
    if re.search(r'\bco-?op\b', t): s += 2
    if season and re.search(rf'\b{season}\b', t + ' ' + d): s += 2
    if month and re.search(rf'\b{month}\b', d): s += 1
    if season != 'summer' and re.search(r'\bsummer\b', t + ' ' + d): s -= 3
    if re.search(r"\b(master'?s|ph\.?d)\b[^.]{0,60}\b(required|candidate|student|degree)", d): s -= 2
    return s

def prepare(offline=False):
    if stopped(): print('STOP: the kill switch is on. /crew-resume first.'); sys.exit(3)
    t0 = time.time()
    shutil.rmtree(DEMO, ignore_errors=True); os.makedirs(f'{DEMO}/data/incoming')
    # COOP_DEMO_SAMPLE=1 (tools/record_demo.sh) always uses the made-up sample student, so a recording never shows yours
    own = os.path.exists(f'{ROOT}/profile/settings.json') and os.environ.get('COOP_DEMO_SAMPLE') != '1'
    shutil.copytree(f'{ROOT}/profile' if own else f'{ROOT}/templates/sample-student/profile', f'{DEMO}/profile')
    s = json.load(open(f'{DEMO}/profile/settings.json'))
    s['mail'] = {'adapter': 'mock'}; s['mode'] = 'external' if s.get('mode') != 'self-developed' else s['mode']
    s.setdefault('nuworks', {})['enabled'] = False
    json.dump(s, open(f'{DEMO}/profile/settings.json', 'w'), indent=1)
    who = s['student']['name']
    print(f'Student: {who} ({"your own profile" if own else "the bundled sample student; every detail is made up"})')
    found = f'{DEMO}/data/all-roles.json'
    if offline: shutil.copy(CACHE, found); print('Boards: cached copy (offline)')
    else:
        r = tool('scan_boards.py', *BOARDS, '--out', found, quiet=True)
        ok = os.path.exists(found) and json.load(open(found))
        print('Boards: ' + ('live: ' + '; '.join(l.strip() for l in r.stdout.splitlines() if 'postings,' in l)
                            if ok else 'network failed, using the cached copy'))
        if not ok: shutil.copy(CACHE, found)
    # choose 5: the 3 most relevant roles the hard rules leave open, and 2 the rules disqualify (one per board)
    sys.path.insert(0, f'{ROOT}/tools'); os.environ.update(env())
    import importlib, crew; importlib.reload(crew)
    import screen_rules as SR, pipeline as P
    roles = json.load(open(found))
    generic = {'intern', 'engineer', 'engineering', 'analyst', 'associate', 'coop'}
    words = {w for t in s['targets'].get('titles', []) for w in re.findall(r'[a-z]+', t.lower()) if len(w) > 3 and w not in generic}
    if words & {'software', 'data'}: words |= {'developer', 'platform', 'backend', 'infrastructure'}
    def verdict(x):
        v, why, _ = SR.judge({'company': x['company'], 'title': x['title'], 'location': x.get('location', ''), 'deadline': x.get('deadline', '')}, x.get('description', ''))
        return v, why
    judged = [(x, *verdict(x)) for x in roles]
    open_ = sorted([j for j in judged if j[1] is None], key=lambda j: -relevance(j[0], words, s['coop']))
    pick, per = [], {}
    for x, v, why in open_:
        if per.get(x['company'], 0) < 2 and len(pick) < 3: pick.append(x); per[x['company']] = per.get(x['company'], 0) + 1
    dq = sorted([j for j in judged if j[1] == 'DQ'], key=lambda j: -relevance(j[0], words, s['coop']))
    used = set()
    for x, v, why in dq:  # one disqualified role per board, other boards first, to show different reasons
        if len(pick) >= 5: break
        if x['company'] in used: continue
        pick.append(x); used.add(x['company'])
    for x, v, why in dq:
        if len(pick) >= 5: break
        if x not in pick: pick.append(x)
    json.dump(pick, open(f'{DEMO}/data/incoming/demo-roles.json', 'w'), indent=1)
    tool('pipeline.py', 'import')
    tool('screen_rules.py', '--offline' if offline else '--limit', *([] if offline else ['99']))
    c = P.db()
    print('\nThe 5 roles:')
    for r in c.execute('select id, company, title, location, status, reason from roles order by status'):
        print(f"  {r['id']:22} {r['status']:5} {r['company']}: {r['title']} [{r['location'][:30]}]" + (f"  ({r['reason'][:80]})" if r['reason'] else ''))
    left = [r['id'] for r in c.execute("select id from roles where status = 'new'")]
    print(f'\nFor the screener agent: {" ".join(left) or "(none)"}   ({time.time() - t0:.1f} s)')

def finish(no_open=False):
    sys.path.insert(0, f'{ROOT}/tools'); os.environ.update(env())
    import pipeline as P
    ids = [r['id'] for r in P.db().execute("select id from roles where status in ('tailored', 'blocked', 'ready')")]
    if ids: tool('gate.py', *ids)
    for t in ('build_today.py', 'build_tracker.py', 'morning.py'): tool(t, quiet=True)
    def calls(f, act):
        p = f'{DEMO}/logs/{f}'
        return sum(1 for l in open(p) if json.loads(l)['action'] == act) if os.path.exists(p) else 0
    subs, sends = calls('mock-jev.jsonl', 'submit'), calls('mock-mail.jsonl', 'send') + calls('mock-mail.jsonl', 'draft')
    page = f'{DEMO}/TODAY.html'
    if not no_open and os.environ.get('COOP_DEMO_NO_OPEN') != '1':
        for opener in (['open'], ['xdg-open'], ['wslview']):
            if shutil.which(opener[0]): subprocess.run(opener + [page], capture_output=True); break
    c = P.db()
    counts = {s: c.execute('select count(*) from roles where status = ?', (s,)).fetchone()[0] for s in ('keep', 'hold', 'dq', 'researched', 'tailored', 'ready', 'blocked')}
    print(f"\nDemo done. Judged {sum(1 for _ in c.execute('select 1 from roles'))} roles; " + ', '.join(f'{v} {k}' for k, v in counts.items() if v))
    print(f'Submitted: {subs}. Sent: {sends}. (The demo never submits or sends.)')
    print(f'TODAY.html: {page}')
    print('\nRun /setup to make this yours.')
    return subs == 0 and sends == 0

def run_offline(no_open):
    t0 = time.time()
    prepare(offline=True)
    sys.path.insert(0, f'{ROOT}/tools'); os.environ.update(env())
    import pipeline as P, cycle
    c = P.db()
    keep = [dict(r) for r in c.execute("select * from roles where status = 'keep' order by found_at")]
    for r in keep[:2]:
        cycle.offline_brief(r['id'], r); P.set_status(c, r['id'], 'researched', 'demo: offline brief from the posting')
    c.commit()
    for r in keep[:1]:
        ok = cycle.offline_pack(r['id'], r); P.set_status(c, r['id'], 'tailored' if ok else 'blocked', 'demo: offline pack')
    c.commit()
    ok = finish(no_open)
    print(f'(offline demo in {time.time() - t0:.1f} s)')
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    a = sys.argv[1:] or ['help']
    if a[0] == 'prepare': prepare('--offline' in a)
    elif a[0] == 'finish': sys.exit(0 if finish('--no-open' in a) else 1)
    elif a[0] == 'run' and '--offline' in a: run_offline('--no-open' in a)
    elif a[0] == 'start': run_offline('--no-open' in a) if '--offline' in a else prepare()
    else: sys.exit('usage: demo.py prepare [--offline] | finish [--no-open] | run --offline [--no-open] | start [--offline] [--no-open]')
