# The kill switch. /stop creates the STOP file: every job, tool and agent stops at its next step (tools/guard.py blocks
# every acting tool call; every python tool exits). /crew-resume deletes it. ~/STOP-AGENTS (the kit's switch) counts too.
# usage: python3 -I tools/killswitch.py stop|resume|status
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if a == 'stop':
        open(K.STOPFILE, 'w').write(f'stopped by the student at {K.now():%F %T}\n')
        K.log('killswitch', 'STOP on'); print(f'STOPPED. Every job stops at its next step. Turn it off with /crew-resume. ({K.STOPFILE})')
    elif a == 'resume':
        removed = []
        for p in K.STOPFILES:
            if os.path.exists(p): os.remove(p); removed.append(p)
        K.log('killswitch', 'STOP off'); print('kill switch off' + (f' (removed {", ".join(removed)})' if removed else ' (it was not on)'))
    else:
        on = [p for p in K.STOPFILES if os.path.exists(p)]
        print(f'kill switch: {"ON (" + ", ".join(on) + ")" if on else "off"}'); sys.exit(1 if on else 0)
