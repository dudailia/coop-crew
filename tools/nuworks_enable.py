# Turns the read-only NUworks reader on or off. The STUDENT runs this themselves (`! python3 -I tools/nuworks_enable.py on`
# in Claude Code, or in a terminal); agents cannot (tools/guard.py blocks changes to the settings files).
# On: needs sourcing mode "nuworks+external", the student's typed acknowledgement, and it records the date.
# It removes "nuworks" from disabledMcpjsonServers in .claude/settings.local.json and sets nuworks.enabled in the profile.
# usage: python3 -I tools/nuworks_enable.py on|off|status
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

LOCAL = f'{K.ROOT}/.claude/settings.local.json'
NOTICE = """The NUworks reader signs in as you (you type your own password and Duo) and reads job listings you can already see.
It never applies, messages, uploads, RSVPs or edits your profile, waits 3 to 5 seconds between pages, reads at most 100
postings a run, and stops on any CAPTCHA or error page. The Northeastern co-op office approved this read-only use
(mcp/nuworks/APPROVAL.md). Turning it on is still your choice, and you stay responsible for using it within that scope
and within the NUworks and Symplicity terms of use."""

def main():
    a = sys.argv[1] if len(sys.argv) > 1 else 'status'
    local = K.load_json(LOCAL, {}); dis = set(local.get('disabledMcpjsonServers', []))
    raw = K.load_json(K.SETTINGS_FILE, None)
    if a == 'status':
        print(f"server: {'disabled' if 'nuworks' in dis else 'allowed'} in .claude/settings.local.json; profile: "
              f"{'enabled' if raw and raw.get('nuworks', {}).get('enabled') else 'disabled'}; mode: {K.SOURCING}"); return
    if raw is None: sys.exit('no profile yet: run /setup first')
    if a == 'off':
        dis.add('nuworks'); raw.setdefault('nuworks', {})['enabled'] = False
    elif a == 'on':
        if raw.get('mode') != 'nuworks+external': sys.exit('NUworks needs sourcing mode "nuworks+external" (set it in /setup)')
        print(NOTICE)
        if input('\nType "I understand" to turn it on: ').strip().lower() != 'i understand': sys.exit('not turned on')
        dis.discard('nuworks'); raw.setdefault('nuworks', {}).update({'enabled': True, 'enabled_at': f'{K.now():%F %T}'})
    else: sys.exit('usage: nuworks_enable.py on|off|status')
    local['disabledMcpjsonServers'] = sorted(dis)
    K.save_json(LOCAL, local); K.save_json(K.SETTINGS_FILE, raw)
    print(f'NUworks reader {a}. Restart Claude Code (exit, then claude) so it picks up the change.')

if __name__ == '__main__':
    main()
