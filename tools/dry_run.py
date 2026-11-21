# The dry run that ends /setup. Copies the student's profile into a throwaway state folder (logs/dry-run/) and runs the
# whole cycle offline there, with jev and Mail mocked: the profile checks, the screening rules, the student's own base
# resume built to one page and checked against their facts, the gate, the pages. Touches nothing in the real pipeline,
# submits and sends nothing (it also asserts that the mocks saw no submit and no send).
# usage: python3 -I tools/dry_run.py [--profile-dir DIR]
import json, os, re, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    src = sys.argv[sys.argv.index('--profile-dir') + 1] if '--profile-dir' in sys.argv else \
        os.path.join(os.environ.get('COOP_STATE') or ROOT, 'profile')
    if not os.path.exists(f'{src}/settings.json'): sys.exit(f'no profile in {src}: run /setup first')
    st = os.path.join(os.environ.get('COOP_STATE') or ROOT, 'logs', 'dry-run')
    shutil.rmtree(st, ignore_errors=True); os.makedirs(st)
    shutil.copytree(src, f'{st}/profile')
    s = json.load(open(f'{st}/profile/settings.json')); s.setdefault('mail', {})['adapter'] = 'mock'
    json.dump(s, open(f'{st}/profile/settings.json', 'w'), indent=1)
    env = {**os.environ, 'COOP_STATE': st, 'COOP_JEV': 'mock', 'COOP_MAIL_ADAPTER': 'mock'}
    # The cached sample roles are titled for a spring 2027 co-op. Relabel them with the student's own cycle and year (in
    # this throwaway copy only), so the screening rules keep some and the student's resume, gate and pages are exercised.
    coop = s.get('coop') or {}; cyc = (coop.get('cycle') or '').lower(); yr = (coop.get('start') or '')[:4]
    if cyc in ('spring', 'fall') and re.match(r'20\d\d$', yr):
        roles = json.load(open(f'{ROOT}/templates/demo-cache/roles.json'))
        term = lambda t: re.sub(r'\b(Spring|Fall)([\s,/-]*)20\d\d\b', lambda m: f'{cyc.title()}{m.group(2)}{yr}', t or '')
        for x in roles:
            for k in ('title', 'description'):
                if isinstance(x.get(k), str): x[k] = term(x[k])
        json.dump(roles, open(f'{st}/sample-roles.json', 'w'), indent=1); env['COOP_OFFLINE_ROLES'] = f'{st}/sample-roles.json'
    r = subprocess.run([sys.executable, '-I', f'{ROOT}/tools/cycle.py', 'run', '--offline'], env=env, text=True,
                       capture_output=True)
    print(r.stdout[-4000:], r.stderr[-1500:])
    def calls(f, act):
        p = f'{st}/logs/{f}'
        return sum(1 for l in open(p) if json.loads(l)['action'] == act) if os.path.exists(p) else 0
    subs, sends = calls('mock-jev.jsonl', 'submit'), calls('mock-mail.jsonl', 'send')
    print(f'dry run: exit {r.returncode}; submits {subs}, sends {sends} (both must be 0); pages in {st}')
    sys.exit(0 if r.returncode == 0 and subs == 0 and sends == 0 else 1)

if __name__ == '__main__':
    main()
