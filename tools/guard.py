#!/usr/bin/env python3
# PreToolUse hook for every agent in this project (.claude/settings.json). The safety rules in code, not only in prompts:
#  1. Kill switch: while STOP (or ~/STOP-AGENTS) exists, every tool call that could act is blocked, so a running cycle
#     stops at its next step. Reading files is still allowed.
#  2. Submits and sends have one door each: tools/applicant.py (checks the student's approval) and tools/send_due.py.
#     Direct jev submits, AppleScript, and any approval writing by an agent are blocked.
#  3. No LinkedIn automation or scraping; NUworks only through the read-only nuworks MCP server.
# Exit code 2 blocks the call and shows the reason to the agent.
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.abspath(os.environ.get('COOP_STATE') or ROOT)
STOPS = (f'{STATE}/STOP', f'{ROOT}/STOP', f'{ROOT}/demo/STOP', os.path.expanduser('~/STOP-AGENTS'))
READ_ONLY = {'Read', 'Glob', 'Grep', 'LS', 'TodoWrite', 'TaskList', 'TaskGet'}

BASH_RULES = [
    (r'\bjev\b[^|;&]*\b(submit|daily|resume\s+--submit)\b|\bjev\b[^|;&]*--submit|--force\b[^|;&]*\bjev\b',
     'jev submits only through tools/applicant.py, which checks the student\'s approval'),
    (r'\bosascript\b', 'AppleScript is off limits to agents: Mail is used only by tools/send_due.py and tools/email_audit.py'),
    (r'tools/approve\.py|approve\.py\b', 'only the student approves (/approve or APPROVE.txt); an agent cannot run approve.py'),
    (r'APPROVE\.txt', 'APPROVE.txt is written by the student only'),
    (r'sqlite3?\b[^|;&]*(approvals|insert|update|delete|drop)', 'the pipeline changes only through tools/pipeline.py (every change is an event)'),
    (r'send_due\.py[^|;&]*--mark-sent', 'only the student records a hand-sent email'),
    (r'\brm\b[^|;&]*\bSTOP\b|STOP-AGENTS', 'the kill switch is turned off only by the student (/crew-resume)'),
    (r'(curl|wget|python3?[^|;&]*urllib)[^|;&]*linkedin\.com', 'no LinkedIn automation or scraping'),
    (r'(curl|wget)[^|;&]*(symplicity\.com|nuworks)', 'NUworks is read only through the nuworks MCP server'),
    (r'\bsmtp|sendmail\b|\bmsmtp\b|\bmutt\b', 'no SMTP: email goes only through the student\'s approved drafts'),
]
PATH_RULES = [
    (r'(^|/)APPROVE\.txt$', 'APPROVE.txt is written by the student only'),
    (r'(^|/)data/pipeline\.sqlite', 'the pipeline changes only through tools/pipeline.py'),
    (r'(^|/)\.claude/settings(\.local)?\.json$|(^|/)\.mcp\.json$', 'agents do not change the safety settings'),
    (r'(^|/)tools/(guard|approve|applicant|send_due|mail|jev)\.py$', 'agents do not change the safety tools'),
]

def block(msg):
    print(f'coop-crew guard: blocked. {msg}', file=sys.stderr); sys.exit(2)

def main():
    try: ev = json.load(sys.stdin)
    except Exception: sys.exit(0)
    tool = ev.get('tool_name', ''); inp = ev.get('tool_input') or {}
    if any(os.path.exists(p) for p in STOPS) and tool not in READ_ONLY:
        block('The kill switch is on (STOP file). Stop the cycle now: make no further tool calls and tell the student '
              'that everything is stopped. Only the student turns it off, with /crew-resume.')
    if tool == 'Bash':
        cmd = inp.get('command', '')
        for rx, why in BASH_RULES:
            if re.search(rx, cmd, re.I): block(why)
    if tool in ('Write', 'Edit', 'MultiEdit', 'NotebookEdit'):
        p = inp.get('file_path') or inp.get('notebook_path') or ''
        for rx, why in PATH_RULES:
            if re.search(rx, p): block(why)
    if tool == 'WebFetch':
        u = inp.get('url', '')
        if re.search(r'linkedin\.com', u, re.I): block('no LinkedIn scraping: record the profile URL from a search result or the firm\'s own page instead')
        if re.search(r'symplicity\.com|nuworks', u, re.I): block('NUworks is read only through the nuworks MCP server')
    sys.exit(0)

if __name__ == '__main__':
    main()
