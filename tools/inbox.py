# The inbox agent's one entry point. Picks the read-only adapter: the Apple Mail audit on a Mac with a Mail account
# (tools/email_audit.py), otherwise the .eml folder reader (tools/inbox_eml.py). Neither sends, moves, deletes or marks.
# usage: python3 -I tools/inbox.py [--force-window]
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

if __name__ == '__main__':
    K.exit_if_stopped('the inbox check')
    a = K.mail_adapter()
    if a == 'mock': print('inbox: mock adapter, nothing read'); sys.exit(0)
    tool = 'email_audit.py' if a == 'mac-mail' else 'inbox_eml.py'
    args = ['--force-window'] if tool == 'email_audit.py' else []
    # email_audit.py takes logs/night.lock itself while Mail is open; the .eml reader touches no app and needs no lock.
    sys.exit(subprocess.run([sys.executable, '-I', f'{K.ROOT}/tools/{tool}', *args]).returncode)
