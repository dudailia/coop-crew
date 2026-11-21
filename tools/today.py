# /today in one allowed command: rebuilds TODAY.html and MORNING.md, opens TODAY.html (and needs-reply.html, if there is
# one) in the browser, and prints MORNING.md. Reads the pipeline and logs only; never touches Mail.
# usage: python3 -I tools/today.py [--no-open]
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, build_today, morning

def open_page(path):
    for opener in ('open', 'xdg-open', 'wslview'):  # macOS, Linux, WSL
        if shutil.which(opener):
            subprocess.run([opener, path], capture_output=True); return True
    return False

def main():
    page = build_today.build(); morning.build()
    if '--no-open' not in sys.argv and os.environ.get('COOP_DEMO_NO_OPEN') != '1':
        opened = [p for p in (page, f'{K.STATE}/needs-reply.html') if os.path.exists(p) and open_page(p)]
        print('Opened in your browser: ' + (', '.join(os.path.basename(p) for p in opened) or f'nothing (open {page} yourself)'))
    print('\n' + K.read(f'{K.STATE}/MORNING.md'))

if __name__ == '__main__':
    main()
