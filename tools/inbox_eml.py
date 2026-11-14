# The inbox agent's mail adapter where Apple Mail is not used (Windows/WSL, Linux, or by choice): reads .eml files
# the student saved or exported into data/inbox/ (or a folder given), READ-ONLY, and rebuilds needs-reply.html:
# replies from employers we wrote to (their follow-ups are cancelled), interview invites, deadlines read from the text,
# and messages that ask the student something. Suggested replies are written by the inbox agent, never sent.
# usage: python3 -I tools/inbox_eml.py [folder]
import datetime as dt, email, email.policy, email.utils, glob, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P

INVITE = re.compile(r'\b(interview|phone screen|screening call|schedule (a|some) time|calendly|book a (time|slot)|availability for a (call|chat)|next round|onsite|super ?day)\b', re.I)
ASK = re.compile(r'\?|\bplease (send|share|confirm|complete|let us know|reply)|\bcould you\b|\bcan you\b|\bwould you\b', re.I)
AUTO = re.compile(r'no-?reply|do not reply|automatic reply|auto-?reply|out of (the )?office|unsubscribe|newsletter', re.I)
DEADLINE = re.compile(r'(?:by|before|deadline|due|no later than|until)\s+(?:\w+day,?\s+)?((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+20\d\d)?|\d{1,2}/\d{1,2}(?:/20\d\d)?)', re.I)
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

def body_of(m):
    part = m.get_body(preferencelist=('plain', 'html'))
    t = part.get_content() if part else ''
    if part is not None and part.get_content_type() == 'text/html':
        t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    return re.split(r'\n\s*(?:>|On .{0,120}wrote:|-{2,}\s*Original)', t, maxsplit=1)[0].strip()

def deadline(text, sent):
    m = DEADLINE.search(text)
    if not m: return ''
    s = m.group(1).lower(); y = sent.year
    try:
        if '/' in s:
            p = s.split('/'); d = dt.date(int(p[2]) if len(p) > 2 else y, int(p[0]), int(p[1]))
        else:
            mm = MONTHS.index(s[:3]) + 1; dd = int(re.search(r'\d{1,2}', s).group(0)); yy = re.search(r'20\d\d', s)
            d = dt.date(int(yy.group(0)) if yy else y, mm, dd)
            if not yy and d < sent.date() - dt.timedelta(days=30): d = d.replace(year=y + 1)
        return d.isoformat()
    except Exception: return ''

def scan(folder):
    me = {a.lower() for a in K.S['audit']['my_addresses'] + [K.C.get('email', '')] if a}
    c = P.db(); sent = [P._email(e) for e in c.execute("select * from emails where kind = 'email' and status in ('sent', 'drafted', 'replied')")]
    items = []
    for f in sorted(glob.glob(f'{folder}/*.eml')):
        try: m = email.message_from_bytes(open(f, 'rb').read(), policy=email.policy.default)
        except Exception: continue
        frm = str(m.get('From', '')); addr = email.utils.parseaddr(frm)[1].lower()
        if not addr or addr in me or m.get('X-Unsent'): continue
        subj = str(m.get('Subject', '')); when = email.utils.parsedate_to_datetime(m['Date']) if m.get('Date') else K.now()
        text = body_of(m); auto = bool(AUTO.search(addr + ' ' + subj + ' ' + text[:500]))
        dom = addr.split('@')[-1]
        ours = next((x for x in sent if dom == x['to'].split('@')[-1].lower() or dom in [d.lower() for d in x['domains']]), None)
        kind = 'interview' if INVITE.search(subj + ' ' + text) else 'reply' if ours else 'question' if ASK.search(text) else 'info'
        if auto and not ours: continue
        if ours and not auto and ours['status'] != 'replied':
            P.email_status(c, ours['id'], 'replied', f'reply from {addr} ({subj[:60]}); follow-ups cancelled')
        items.append({'file': f, 'from': frm, 'subject': subj, 'when': when.isoformat(timespec='minutes'), 'kind': kind,
                      'deadline': deadline(subj + ' ' + text, when), 'company': ours['company'] if ours else '', 'text': text[:1500]})
    c.commit()
    order = {'interview': 0, 'reply': 1, 'question': 2, 'info': 3}
    items.sort(key=lambda x: (order[x['kind']], x['deadline'] or '9999', x['when']))
    return items

def write(items):
    from build_today import CSS
    e = lambda s: html.escape(str(s or ''))
    h = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Needs reply</title><style>{CSS}</style></head><body><main>',
         f'<h1>Needs reply</h1><p class="sub">{len(items)} messages · read-only · nothing here was answered, moved or deleted · {K.now():%a %d %b %H:%M}</p>']
    sugg = K.load_json(f'{K.LOGS}/suggested-replies.json', {})
    for x in items:
        if x['kind'] == 'info': continue
        tag = {'interview': 'Interview invite', 'reply': f'Reply from {x["company"]}', 'question': 'Asks you something'}[x['kind']]
        h.append(f'<section class="pack"><h3>{e(tag)}: {e(x["subject"])}</h3><div class="meta">{e(x["from"])} · {e(x["when"])}'
                 + (f' · <b>deadline {e(x["deadline"])}</b>' if x['deadline'] else '') + f'</div><pre>{e(x["text"][:1200])}</pre>'
                 + (f'<details open><summary>Suggested reply (not sent)</summary><pre>{e(sugg[x["file"]])}</pre></details>' if sugg.get(x['file']) else '')
                 + '</section>')
    h.append('</main></body></html>')
    open(f'{K.STATE}/needs-reply.html', 'w', encoding='utf-8').write('\n'.join(h))
    counts = {'new': sum(1 for x in items if x['kind'] != 'info'), 'overdue': sum(1 for x in items if x['deadline'] and x['deadline'] < f'{K.now():%Y-%m-%d}'),
              'interviews': sum(1 for x in items if x['kind'] == 'interview'), 'scan': K.now().isoformat()}
    K.save_json(f'{K.LOGS}/email-audit-counts.json', counts); K.save_json(f'{K.LOGS}/inbox-items.json', items)
    print(f"needs-reply.html: {counts['new']} need you ({counts['interviews']} interview invites, {counts['overdue']} past a deadline)")

if __name__ == '__main__':
    K.exit_if_stopped('the inbox check')
    folder = sys.argv[1] if len(sys.argv) > 1 else f'{K.DATA}/inbox'
    os.makedirs(folder, exist_ok=True)
    write(scan(folder))
