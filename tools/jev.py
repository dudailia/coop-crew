# The only door to jev-job-search (vendor/jev/src, upstream plus jev-fixes.patch, prepare mode). Three verbs:
#   prepare(url)  -> jev apply <url>            fills and checks the form, leaves it open, submits nothing
#   check(jev_id) -> jev check <id>             re-reads the open form before any click
#   submit(jev_id)-> jev submit <id>            sends that one form (never --force)
# Only tools/applicant.py calls submit(), after its own approval checks. With COOP_JEV=mock nothing runs: every call is
# appended to logs/mock-jev.jsonl (used by the tests and /demo).
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

JEV_DIR = os.environ.get('COOP_JEV_DIR') or f'{K.ROOT}/vendor/jev/src'
MOCK_LOG = f'{K.LOGS}/mock-jev.jsonl'
def mocked(): return os.environ.get('COOP_JEV') == 'mock'
def installed(): return os.path.exists(f'{JEV_DIR}/package.json')

def _mock(action, ref, **extra):
    with open(MOCK_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'at': f'{K.now():%F %T}', 'action': action, 'ref': ref, **extra}) + '\n')

def _run(*args, timeout=1800):
    if not installed(): raise RuntimeError('jev is not installed: run vendor/jev/install.sh (needs Node.js 22+)')
    r = subprocess.run(['npx', '--no-install', 'jev', *args], cwd=JEV_DIR, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or '') + (r.stderr or '')

def prepare(url):
    """Returns the jev id of the prepared form, or raises."""
    if mocked():
        jid = 'mock-' + re.sub(r'[^a-z0-9]+', '-', url.lower())[-24:].strip('-')
        _mock('prepare', url, jev_id=jid); return jid
    code, out = _run('apply', url, '--json')
    try: data = json.loads(out[out.index('{'):] if '{' in out else out)
    except Exception: data = {}
    jid = data.get('id') or (data.get('results') or [{}])[0].get('id') if isinstance(data, dict) else None
    if code or not jid: raise RuntimeError(f'jev apply failed ({code}): {out[-400:]}')
    return jid

def check(jid):
    """(ready?, text). The form must still be ready, with no field changed or emptied since it was prepared."""
    if mocked():
        _mock('check', jid); return True, 'mock: ready'
    code, out = _run('check', jid, timeout=600)
    ok = code == 0 and re.search(r'\bready\b', out, re.I) and not re.search(r'needs[_ ]review|not ready|missing|error', out, re.I)
    return bool(ok), out[-600:]

def submit(jid):
    if mocked():
        _mock('submit', jid); return True, 'mock: submitted'
    code, out = _run('submit', jid, timeout=900)
    return code == 0 and bool(re.search(r'submitted|sent|confirm', out, re.I)), out[-600:]

def mock_calls(action=None):
    out = []
    if os.path.exists(MOCK_LOG):
        for l in open(MOCK_LOG, encoding='utf-8'):
            x = json.loads(l)
            if action is None or x['action'] == action: out.append(x)
    return out
