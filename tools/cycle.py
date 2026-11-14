# The daily cycle's step runner. /run calls `cycle.py step <name>` before each step; it exits 3 (and prints STOP) when the
# kill switch is on, so the conductor stops within one step. Together with tools/guard.py (which blocks every acting tool
# call while STOP exists) this is how the kill switch reaches a cycle that is already running.
#
# `cycle.py run --offline` runs the whole cycle with no agents: the code steps for real, the agent steps by deterministic
# stand-ins (rule screening, a brief from the posting, the base resume retitled). /demo --offline and the tests use it,
# always with COOP_JEV=mock and the mock or eml mail adapter. It never submits or sends: approvals are the student's.
#
# usage: python3 -I tools/cycle.py begin|end
#        python3 -I tools/cycle.py step <name>
#        python3 -I tools/cycle.py run --offline [--roles N] [--step-delay S]
import datetime as dt, json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P

STEPS = ['inbox', 'scout', 'screen', 'research', 'tailor', 'edit', 'gate', 'outreach', 'applicant', 'send', 'tracker']
STATE_FILE = f'{K.LOGS}/cycle.json'

def mark(name, status='running'):
    s = K.load_json(STATE_FILE, {'steps': []})
    s['steps'].append({'step': name, 'status': status, 'at': f'{K.now():%F %T}'}); s['last'] = name
    K.save_json(STATE_FILE, s)

def step(name):
    if K.stopped():
        mark(name, 'stopped'); K.log('cycle', f'STOP before step {name}')
        print(f'STOP: the kill switch is on. The cycle stops before "{name}". Make no more tool calls; tell the student.')
        sys.exit(3)
    mark(name); K.log('cycle', f'step {name}'); print(f'go: {name}')

def py(tool, *args):
    r = subprocess.run([sys.executable, '-I', f'{K.ROOT}/tools/{tool}', *args], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out: print('   ' + out.replace('\n', '\n   '))
    if r.returncode == 3: sys.exit(3)  # a tool saw the kill switch
    return r.returncode, out

# ---- offline stand-ins for the agent steps ----
def offline_brief(rid, r):
    text = K.read(f'{K.OUT}/{rid}/posting.md')
    body = '\n'.join(l for l in text.splitlines()[5:] if l.strip())
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', body) if 40 < len(s.strip()) < 220][:4]
    while len(sents) < 3: sents.append(f'{r["company"]} posted this role as {r["title"]} ({r["location"] or "location not stated"}).')
    open(f'{K.OUT}/{rid}/brief.md', 'w', encoding='utf-8').write(
        f'# Company brief: {r["company"]}\n\n' + ''.join(f'- {s}\n' for s in sents[:6]) + f'\nSource: {r["url"]}\n')

def offline_pack(rid, r):
    d = f'{K.OUT}/{rid}'
    base = K.read(f'{K.PROFILE}/resume.md') or K.read(f'{K.SAMPLE}/profile/resume.md')
    open(f'{d}/resume.md', 'w', encoding='utf-8').write(re.sub(r'(?m)^title: .*$', f'title: {r["title"]}', base, count=1))
    K.save_json(f'{d}/questions.json', [])
    open(f'{d}/answers.md', 'w', encoding='utf-8').write('# Answers\n\n(The portal asked no extra questions in offline mode.)\n')
    open(f'{d}/field-log.md', 'w', encoding='utf-8').write(
        '# Field log\n\n| Field | Value | Source |\n|---|---|---|\n'
        f'| Name | {K.C.get("name", "")} | profile |\n| Email | {K.C.get("email", "")} | profile |\n'
        '| Resume | resume.pdf | built by tools/resume.py |\n| Cover letter | (blank) | no field; not asked for |\n')
    code, out = py('resume.py', rid)
    return code == 0

def run_offline(nroles=None, delay=0.0):
    os.environ.setdefault('COOP_JEV', 'mock'); os.environ.setdefault('COOP_MAIL_ADAPTER', 'mock')
    t0 = time.time()
    for name in STEPS:
        step(name)
        if name == 'inbox': print('   offline: inbox skipped')
        elif name == 'scout':
            src = os.environ.get('COOP_OFFLINE_ROLES') or f'{K.ROOT}/templates/demo-cache/roles.json'
            os.makedirs(K.INCOMING, exist_ok=True); shutil.copy(src, f'{K.INCOMING}/offline-roles.json')
            py('pipeline.py', 'import')
        elif name == 'screen': py('screen_rules.py', '--offline', *(['--limit', str(nroles)] if nroles else []))
        elif name == 'research':
            c = P.db()
            for r in c.execute("select * from roles where status = 'keep'").fetchall():
                offline_brief(r['id'], r); P.set_status(c, r['id'], 'researched', 'offline brief written from the posting')
            c.commit()
        elif name == 'tailor':
            c = P.db()
            for r in c.execute("select * from roles where status = 'researched'").fetchall():
                ok = offline_pack(r['id'], r); P.set_status(c, r['id'], 'tailored' if ok else 'blocked', 'offline pack built' if ok else 'resume build failed')
            c.commit()
        elif name == 'edit': print('   offline: no editor pass (no new writing)')
        elif name == 'gate':
            ids = [r['id'] for r in P.db().execute("select id from roles where status = 'tailored'")]
            if ids: py('gate.py', *ids)
        elif name == 'outreach': py('plan_emails.py')
        elif name == 'applicant':
            ids = [r['id'] for r in P.db().execute("select id from roles where status = 'ready' and channel = 'form'")]
            if ids: py('applicant.py', 'prepare', *ids)
            ids = [r['id'] for r in P.db().execute("select id from roles where status = 'approved'")]
            if ids: py('applicant.py', 'submit', *ids)  # only ever approved ids; it re-checks the approval itself
        elif name == 'send': py('send_due.py')
        elif name == 'tracker':
            for t in ('build_today.py', 'build_tracker.py', 'morning.py'): py(t)
        mark(name, 'done')
        if delay: time.sleep(delay)
    print(f'cycle done in {time.time() - t0:.1f} s')

if __name__ == '__main__':
    a = sys.argv[1:] or ['help']
    if a[0] == 'begin':
        K.exit_if_stopped('the cycle'); K.save_json(STATE_FILE, {'started': f'{K.now():%F %T}', 'steps': []}); print('cycle started')
    elif a[0] == 'end':
        s = K.load_json(STATE_FILE, {}); s['ended'] = f'{K.now():%F %T}'; K.save_json(STATE_FILE, s); print('cycle ended')
    elif a[0] == 'step': step(a[1])
    elif a[0] == 'run' and '--offline' in a:
        K.exit_if_stopped('the cycle'); K.save_json(STATE_FILE, {'started': f'{K.now():%F %T}', 'steps': [], 'offline': True})
        run_offline(int(a[a.index('--roles') + 1]) if '--roles' in a else None,
                    float(a[a.index('--step-delay') + 1]) if '--step-delay' in a else 0.0)
    else: sys.exit('usage: cycle.py begin|end | step <name> | run --offline [--roles N] [--step-delay S]')
