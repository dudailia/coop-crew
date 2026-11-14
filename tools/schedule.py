# Optional schedules (off by default). The STUDENT installs them (`! python3 -I tools/schedule.py install`); agents
# do not. Two jobs: the daily cycle (`claude -p "/run"` at 06:30 local time, headless, on the student's own Claude plan)
# and the sender (`tools/send_due.py` every 15 minutes, which only ever touches approved emails). Both stop on the kill
# switch, and both stay out of the student's quiet hours.
# macOS: launchd agents in ~/Library/LaunchAgents. Linux and WSL: lines in the user's crontab.
# usage: python3 -I tools/schedule.py install|uninstall|status
import os, plistlib, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

LABELS = {'run': 'com.coopcrew.run', 'send': 'com.coopcrew.send'}
LA = os.path.expanduser('~/Library/LaunchAgents')
PY = shutil.which('python3') or '/usr/bin/python3'

def jobs():
    claude = shutil.which('claude') or 'claude'
    gate = f'test -e "{K.STATE}/STOP" || test -e "$HOME/STOP-AGENTS" || '
    return {'run': (f'cd "{K.ROOT}" && {gate}"{claude}" -p "/run" --permission-mode acceptEdits >> "{K.LOGS}/scheduled-run.log" 2>&1', {'Hour': 6, 'Minute': 30}),
            'send': (f'cd "{K.ROOT}" && {gate}"{PY}" -I tools/send_due.py >> "{K.LOGS}/send.log" 2>&1', 900)}

def install():
    if sys.platform == 'darwin':
        os.makedirs(LA, exist_ok=True)
        for k, (cmd, when) in jobs().items():
            p = {'Label': LABELS[k], 'ProgramArguments': ['/bin/zsh', '-lc', cmd], 'RunAtLoad': False}
            if isinstance(when, int): p['StartInterval'] = when
            else: p['StartCalendarInterval'] = when
            path = f'{LA}/{LABELS[k]}.plist'
            with open(path, 'wb') as f: plistlib.dump(p, f)
            subprocess.run(['launchctl', 'load', '-w', path], capture_output=True)
            print(f'installed {path}')
    else:
        cur = subprocess.run(['crontab', '-l'], capture_output=True, text=True).stdout
        keep = [l for l in cur.splitlines() if 'coop-crew' not in l]
        cmd_run, _ = jobs()['run']; cmd_send, _ = jobs()['send']
        keep += [f'30 6 * * * bash -lc \'{cmd_run}\'  # coop-crew run', f'*/15 * * * * bash -lc \'{cmd_send}\'  # coop-crew send']
        subprocess.run(['crontab', '-'], input='\n'.join(keep) + '\n', text=True, check=True); print('installed 2 crontab lines (coop-crew)')
    s = K.load_json(K.SETTINGS_FILE, None)
    if s is not None: s.setdefault('limits', {})['schedule'] = True; K.save_json(K.SETTINGS_FILE, s)

def uninstall():
    if sys.platform == 'darwin':
        for lab in LABELS.values():
            path = f'{LA}/{lab}.plist'
            if os.path.exists(path): subprocess.run(['launchctl', 'unload', '-w', path], capture_output=True); os.remove(path); print(f'removed {path}')
    else:
        cur = subprocess.run(['crontab', '-l'], capture_output=True, text=True).stdout
        subprocess.run(['crontab', '-'], input='\n'.join(l for l in cur.splitlines() if 'coop-crew' not in l) + '\n', text=True); print('removed coop-crew crontab lines')
    s = K.load_json(K.SETTINGS_FILE, None)
    if s is not None: s.setdefault('limits', {})['schedule'] = False; K.save_json(K.SETTINGS_FILE, s)

if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if a == 'install': install()
    elif a == 'uninstall': uninstall()
    else:
        for k, (cmd, when) in jobs().items(): print(f'{k}: {when} -> {cmd}')
