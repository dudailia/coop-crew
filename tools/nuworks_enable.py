# Turns the optional NUworks BROWSER reader on or off. The STUDENT runs this themselves (`! python3 -I tools/nuworks_enable.py
# on` in Claude Code, or in a terminal); agents cannot (tools/guard.py blocks changes to the settings files).
# The default NUworks path needs none of this: job-alert emails (tools/nuworks_alerts.py) and postings the student saves
# (tools/nuworks_import.py) never load a NUworks page. The browser reader does, and Symplicity's terms of use prohibit
# automated access without Symplicity's prior written permission (mcp/nuworks/APPROVAL.md), so turning it on shows that
# notice and needs the exact acknowledgement typed. The date and the wording acknowledged go in the profile.
# On: needs sourcing mode "nuworks+external". It removes "nuworks" from disabledMcpjsonServers in
# .claude/settings.local.json and sets nuworks.enabled in the profile. Off: the reverse, and it also takes "nuworks" out of
# enabledMcpjsonServers (Claude Code adds it there when the server is approved at start-up).
# usage: python3 -I tools/nuworks_enable.py on|off|status
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

LOCAL = f'{K.ROOT}/.claude/settings.local.json'
ACK = 'I have read the Symplicity terms and accept the risk'
NOTICE = f"""NUworks BROWSER READER: read this first.

You do not need this to use NUworks with coop-crew. The default NUworks path reads your NUworks job-alert emails and
postings you save yourself (data/nuworks-import/); neither loads a NUworks page. This reader is different: it drives a
browser, signed in as you, through NUworks listings and postings.

NUworks runs on Symplicity CSM. Symplicity's published terms of use (quoted from https://www.symplicity-mea.com/TermOfService;
read the current US terms, linked at the foot of every NUworks page, at https://www.symplicity.com/support/terms-of-use)
say you may not:

  "use or attempt to use engines, manual or automated software, tools, devices, agents, scripts robots or other means,
   devices, mechanisms or processes (including, but not limited to, browsers, spiders, robots, avatars or intelligent
   agents) to navigate, search, access, "scrape," "crawl," or "spider" any web pages or any services provided on the
   Sites other than the search engine and search agents available from Symplicity [...] and other than generally
   available third party web browsers"

  "collect users' content or information, or otherwise access the Site, using automated means (such as harvesting bots,
   robots, spiders, or scrapers) without our prior permission"

Read slowly and read-only, this reader is still automated access. The Northeastern co-op office approved read-only use
(mcp/nuworks/APPROVAL.md), but that approval is not Symplicity's permission. Using the reader may breach those terms and
put your NUworks account at risk. It never applies, messages, uploads, RSVPs or edits your profile; it sends only GET
requests, waits 3 to 5 seconds between pages, reads at most 100 postings a run, and stops on any CAPTCHA or error page.
The choice and the responsibility are yours."""

def main():
    a = sys.argv[1] if len(sys.argv) > 1 else 'status'
    local = K.load_json(LOCAL, {}); dis = set(local.get('disabledMcpjsonServers', [])); ena = set(local.get('enabledMcpjsonServers', []))
    raw = K.load_json(K.SETTINGS_FILE, None)
    if a == 'status':
        print(f"server: {'disabled' if 'nuworks' in dis else 'allowed'} in .claude/settings.local.json; profile: "
              f"{'enabled' if raw and raw.get('nuworks', {}).get('enabled') else 'disabled'}; mode: {K.SOURCING}"); return
    if a == 'notice': print(NOTICE); return
    if raw is None: sys.exit('no profile yet: run /setup first')
    if a == 'off':
        dis.add('nuworks'); ena.discard('nuworks'); raw.setdefault('nuworks', {})['enabled'] = False
    elif a == 'on':
        if raw.get('mode') != 'nuworks+external': sys.exit('NUworks needs sourcing mode "nuworks+external" (set it in /setup)')
        print(NOTICE)
        try: typed = input(f'\nTo turn it on, type exactly: {ACK}\n> ')
        except EOFError: typed = ''
        if ' '.join(typed.split()).lower().rstrip('.') != ACK.lower(): sys.exit('not turned on (the acknowledgement did not match)')
        dis.discard('nuworks')
        raw.setdefault('nuworks', {}).update({'enabled': True, 'enabled_at': f'{K.now():%F %T}', 'acknowledged': ACK})
    else: sys.exit('usage: nuworks_enable.py on|off|status|notice')
    local['disabledMcpjsonServers'] = sorted(dis)
    if ena: local['enabledMcpjsonServers'] = sorted(ena)
    else: local.pop('enabledMcpjsonServers', None)
    K.save_json(LOCAL, local); K.save_json(K.SETTINGS_FILE, raw)
    print(f'NUworks browser reader {a}. Restart Claude Code (exit, then claude) so it picks up the change.')

if __name__ == '__main__':
    main()
