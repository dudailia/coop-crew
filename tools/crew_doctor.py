# /crew-doctor: a health check. Tools, login states, schedules, disk, kill switch, last run results. Reads only.
# usage: python3 -I tools/crew_doctor.py [--install]
import json, os, platform, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

def run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e: return 1, str(e)

def main():
    rows = []
    def add(ok, what, detail=''): rows.append(('ok  ' if ok is True else 'WARN' if ok is None else 'FAIL', what, detail))
    add(sys.version_info >= (3, 9), 'python3', platform.python_version())
    code, v = run(['node', '-v']); major = int(v.lstrip('v').split('.')[0]) if code == 0 and v.startswith('v') else 0
    add(major >= 18, 'node', v if code == 0 else 'missing')
    add(bool(shutil.which('git')), 'git')
    add(os.path.exists(f'{K.ROOT}/node_modules/playwright'), 'Node packages', 'npm install' if not os.path.exists(f'{K.ROOT}/node_modules/playwright') else '')
    code, out = run(['node', '-e', "import('playwright').then(p=>{const fs=require('fs');console.log(fs.existsSync(p.chromium.executablePath())?'yes':'no')})"], 60)
    add(out.strip().endswith('yes') or None, 'Playwright Chromium', '' if out.strip().endswith('yes') else 'run: npx playwright install chromium')
    jev = os.path.exists(f'{K.ROOT}/vendor/jev/src/package.json')
    add(True if jev else None, 'jev-job-search (form filler)', 'installed, prepare mode' if jev else 'not installed: packs are submitted by hand (needs Node 22+: vendor/jev/install.sh)')
    add(bool(shutil.which('claude')) or None, 'Claude Code', '' if shutil.which('claude') else 'install from claude.com/claude-code')
    add(K.have_profile() or None, 'profile', K.SETTINGS_FILE if K.have_profile() else 'none yet: run /setup (or /demo with the sample student)')
    add(os.path.exists(K.FACTS_FILE) or None, 'facts.md (proof bank)')
    a = K.mail_adapter()
    detail = {'mac-mail': f'Apple Mail, account "{K.S["mail"].get("account")}"', 'eml': '.eml drafts in data/outbox (you send them)', 'mock': 'mock (tests)'}.get(a, a)
    add(True, 'email adapter', detail)
    if a == 'mac-mail': add(None if os.path.exists(K.LOGINF) else True, 'Mail login', 'MAIL-LOGIN-ERROR: sign in to Mail, then delete logs/MAIL-LOGIN-ERROR' if os.path.exists(K.LOGINF) else 'no login error recorded')
    local = K.load_json(f'{K.ROOT}/.claude/settings.local.json', {})
    nu_off = 'nuworks' in local.get('disabledMcpjsonServers', [])
    nu_on = K.S['nuworks'].get('enabled') and K.SOURCING == 'nuworks+external'
    add(True, 'NUworks reader', 'disabled (default)' if nu_off or not nu_on else 'enabled in your profile; sign in with nuworks_login')
    if os.path.exists(f'{K.DATA}/nuworks/browser-profile'): add(True, 'NUworks session', 'a saved browser session exists (nuworks_status says if it is still signed in)')
    add(not K.stopped() or None, 'kill switch', 'ON: nothing runs (/crew-resume)' if K.stopped() else 'off')
    for f, m in ((K.PAUSE, 'sending paused'), (K.LOGINF, 'Mail login error')):
        if os.path.exists(f): add(None, m, K.read(f)[:120])
    sched = []
    if sys.platform == 'darwin':
        la = os.path.expanduser('~/Library/LaunchAgents')
        sched = [f for f in os.listdir(la) if 'coopcrew' in f] if os.path.isdir(la) else []
    else:
        code, out = run(['crontab', '-l']); sched = [l for l in out.splitlines() if 'coop-crew' in l] if code == 0 else []
    add(True, 'schedules', ', '.join(sched) if sched else 'off (default; /setup can turn them on)')
    free = shutil.disk_usage(K.STATE).free / 1e9
    add(free > 2 or None, 'disk', f'{free:.1f} GB free')
    cy = K.load_json(f'{K.LOGS}/cycle.json', {})
    if cy:
        bad = [s for s in cy.get('steps', []) if s['status'] == 'stopped']
        add(None if bad else True, 'last cycle', f"started {cy.get('started')}, ended {cy.get('ended', 'not recorded')}, last step {cy.get('last', '?')}" + (' (stopped by the kill switch)' if bad else ''))
    elif '--install' not in sys.argv: add(None, 'last cycle', 'no cycle has run yet')
    try:
        import pipeline as P
        c = P.db(); n = c.execute('select count(*) from roles').fetchone()[0]
        add(True, 'pipeline', f'{n} roles, clean-pass streak {P.streak(c)}')
    except Exception as e: add(False, 'pipeline', str(e)[:120])
    w = max(len(r[1]) for r in rows)
    for s, what, d in rows: print(f'{s}  {what:<{w}}  {d}')
    fails = [r for r in rows if r[0] == 'FAIL']
    print(f'\n{len(fails)} problem(s), {sum(1 for r in rows if r[0] == "WARN")} note(s).')
    sys.exit(1 if fails else 0)

if __name__ == '__main__':
    main()
