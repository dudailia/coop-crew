# Mail adapters. Only tools/send_due.py calls draft() or send(), and only for emails the student approved.
#  - mac-mail: Apple Mail through AppleScript (from job-agents-kit's sender.py). Mail is launched hidden, never activated;
#              the front app is given back after every call. Drafts are never deleted.
#  - eml:      on Windows (WSL), Linux, or a Mac without Mail: each approved email is written to data/outbox/<id>.eml plus a
#              copy-ready list (data/outbox/READY.md). The student sends them from their own client. No SMTP, no passwords.
#  - mock:     tests. Every call is appended to logs/mock-mail.jsonl and nothing leaves the machine.
# Selected by COOP_MAIL_ADAPTER or settings.mail.adapter (auto = mac-mail on macOS with an account set, else eml).
import datetime as dt, email.message, email.utils, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

OUTBOX = f'{K.DATA}/outbox'
MOCK_LOG = f'{K.LOGS}/mock-mail.jsonl'

# argv: to, subject, body, from, then attachment paths. visible:false + close keep every window hidden.
SEND = '''on run argv
set toAddr to item 1 of argv
set subj to item 2 of argv
set bod to item 3 of argv
set fromAddr to item 4 of argv
tell application "Mail"
set m to make new outgoing message with properties {subject:subj, content:bod, visible:false}
if fromAddr is not "" then set sender of m to fromAddr
tell m to make new to recipient at end of to recipients with properties {address:toAddr}
if (count of argv) > 4 then
  repeat with i from 5 to count of argv
    tell content of m to make new attachment with properties {file name:((POSIX file (item i of argv)) as alias)} at after the last paragraph
  end repeat
  delay 5
end if
send m
try
close (every window whose name is subj) saving no
end try
end tell
return "sent"
end run'''
# argv: to, subject, body, from, account, drafts mailbox, then attachment paths. A draft with the same subject is never saved twice.
SAVE = '''on run argv
set toAddr to item 1 of argv
set subj to item 2 of argv
set bod to item 3 of argv
set fromAddr to item 4 of argv
set acc to item 5 of argv
set dbox to item 6 of argv
tell application "Mail"
set mb to mailbox dbox of account acc
if (count of (messages of mb whose subject is subj)) > 0 then return "exists"
set m to make new outgoing message with properties {subject:subj, content:bod, visible:false}
if fromAddr is not "" then set sender of m to fromAddr
tell m to make new to recipient at end of to recipients with properties {address:toAddr}
if (count of argv) > 6 then
  repeat with i from 7 to count of argv
    tell content of m to make new attachment with properties {file name:((POSIX file (item i of argv)) as alias)} at after the last paragraph
  end repeat
  delay 5
end if
save m
delay 4  -- without the pause, closing the hidden window can drop the draft
try
close (every window whose name is subj) saving yes
end try
end tell
return "saved"
end run'''

def _osa(script, *args, timeout=180):
    try: front = subprocess.run(['osascript', '-e', K.FRONT], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception: front = ''
    try: r = subprocess.run(['osascript', '-', *args], input=script, capture_output=True, text=True, timeout=timeout)
    finally: subprocess.run(['osascript', '-', front], input=K.RESTORE, capture_output=True, text=True, timeout=30)
    if r.returncode: raise RuntimeError(r.stderr.strip()[:300])
    return r.stdout.strip()

def _eml(xid, to, subj, body, attachments):
    os.makedirs(OUTBOX, exist_ok=True)
    m = email.message.EmailMessage()
    m['To'] = to; m['Subject'] = subj; m['Date'] = email.utils.formatdate(localtime=True)
    if K.sender_line(): m['From'] = K.sender_line()
    m['X-Unsent'] = '1'  # Outlook and Apple Mail open it as a draft
    m.set_content(body)
    for a in attachments:
        with open(a, 'rb') as f:
            m.add_attachment(f.read(), maintype='application', subtype='pdf' if a.endswith('.pdf') else 'octet-stream',
                             filename=os.path.basename(a))
    p = f'{OUTBOX}/{re.sub(r"[^A-Za-z0-9_.-]", "_", xid)}.eml'
    open(p, 'wb').write(bytes(m))
    with open(f'{OUTBOX}/READY.md', 'a', encoding='utf-8') as f:
        f.write(f'\n## {xid}: {subj}\nTo: {to}\nFile: {p}\n\n{body}\n')
    return p

def _mock(action, xid, to, subj):
    with open(MOCK_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'at': f'{K.now():%F %T}', 'action': action, 'id': xid, 'to': to, 'subject': subj}) + '\n')
    return action

def draft(xid, to, subj, body, attachments=()):
    """Prepare mode: a draft the student sends. Never sends."""
    a = K.mail_adapter()
    if a == 'mock': return _mock('draft', xid, to, subj)
    if a == 'eml': return 'eml: ' + _eml(xid, to, subj, body, attachments)
    return _osa(SAVE, to, subj, body, K.sender_line(), K.S['mail']['account'], K.S['mail']['drafts'], *attachments)

def send(xid, to, subj, body, attachments=()):
    """Send mode on mac-mail only. The eml adapter cannot send: it writes a draft file."""
    a = K.mail_adapter()
    if a == 'mock': return _mock('send', xid, to, subj)
    if a == 'eml': return 'eml (not sent): ' + _eml(xid, to, subj, body, attachments)
    return _osa(SEND, to, subj, body, K.sender_line(), *attachments)

def mock_calls(action=None):
    out = []
    if os.path.exists(MOCK_LOG):
        for l in open(MOCK_LOG, encoding='utf-8'):
            x = json.loads(l)
            if action is None or x['action'] == action: out.append(x)
    return out
