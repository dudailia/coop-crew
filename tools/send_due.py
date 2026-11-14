# The sender (from job-agents-kit's night_send.py rules). Run by the scheduler or /run. It decides from the pipeline alone
# and touches the mail adapter only when something is due:
#  - kill switch on -> exit, touch nothing. logs/SENDER-PAUSED or logs/MAIL-LOGIN-ERROR -> exit.
#  - only emails the student approved (/approve <id> or APPROVE.txt); an unapproved one waits, forever if need be.
#  - weekday, inside the recipient region's window, at most send.per_run per run and the daily cap (hard maximum 40),
#    never to a blocked employer, never twice to one address.
#  - prepare mode (the default): each due email is saved as a draft (Mail Drafts, or an .eml file) for the student to send.
#    send mode, mac-mail only: it is sent.
#  - follow-ups: one per company, follow_up_working_days (5 to 7) after the first email was sent, at the same local time;
#    cancelled by any reply from that company.
# One lock: never at the same time as the email audit, JEV or the NUworks browser.
# usage: python3 -I tools/send_due.py [--dry] [--now 2030-01-14T08:20]
#        python3 -I tools/send_due.py --mark-sent <id> ["YYYY-MM-DD HH:MM"]   you sent a draft by hand: schedule its follow-up
#        python3 -I tools/send_due.py --replied <id>                          a reply came: cancel the follow-up for that company
import datetime as dt, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P, mail

def sent_today(c, now):
    d = f'{now.astimezone(K.TZ):%Y-%m-%d}'
    return c.execute("select count(*) from events where kind = 'email-status' and (detail like 'sent:%' or detail like 'drafted:%' "
                     "or detail like 'followup-%') and at like ?", (d + '%',)).fetchone()[0]

def fu_due_at(x, sent_at):
    t = dt.datetime.fromisoformat(sent_at).replace(tzinfo=K.TZ).astimezone(K.tz_of(x))
    d = K.add_working_days(t.date(), int(K.S['send'].get('follow_up_working_days', 6)))
    a, b = K.window_of(x)
    tt = t.time() if a <= t.time() <= b else a
    return dt.datetime.combine(d, tt, K.tz_of(x)).replace(tzinfo=None).isoformat(timespec='minutes')

def mark_sent(c, x, when):
    due = fu_due_at(x, when) if x.get('followup_body') else None
    P.email_status(c, x['id'], 'sent', f'sent at {when}', sent_at=when, followup_due=due)

def due(c, now):
    out = []
    for e in c.execute("select * from emails where kind = 'email'").fetchall():
        x = P._email(e)
        if x['status'] in ('planned', 'approved') and x['slot'] and x['approved']:
            t = dt.datetime.fromisoformat(x['slot']).replace(tzinfo=K.tz_of(x))
            if t <= now: out.append((t, 'email', x))
        elif x['status'] == 'sent' and x['followup_due'] and not x['followup_status'] and x['followup_body']:
            t = dt.datetime.fromisoformat(x['followup_due']).replace(tzinfo=K.tz_of(x))
            if t <= now: out.append((t, 'followup', x))
    return sorted(out, key=lambda z: z[0])

def run(now=None, dry=False):
    K.exit_if_stopped('the sender')
    if os.path.exists(K.PAUSE) or os.path.exists(K.LOGINF): print('sending is paused (logs/SENDER-PAUSED or logs/MAIL-LOGIN-ERROR)'); return []
    now = now or K.now(); c = P.db(); done = []
    late = dt.timedelta(minutes=K.S['send']['late_minutes'])
    todo = []
    for t, kind, x in due(c, now):
        why = None
        if K.blocked(x['company']): why = f"employer blocked ({K.blocked(x['company'])})"
        elif kind == 'email' and c.execute("select 1 from emails where lower(to_addr) = ? and status = 'sent' and id != ?", (x['to'].lower(), x['id'])).fetchone():
            why = 'address already emailed'
        elif kind == 'followup' and c.execute("select 1 from emails where company = ? and followup_status in ('sent', 'drafted') and id != ?", (x['company'], x['id'])).fetchone():
            why = 'one follow-up per company: the company already had one'
        elif kind == 'followup' and c.execute("select 1 from emails where company = ? and status = 'replied'", (x['company'],)).fetchone():
            why = 'the company replied'
        elif now - t > late or not K.slot_ok(now, x):
            if kind == 'email':  # missed its window: next weekday, same local time (still needs nothing new from the student)
                lt = t.astimezone(K.tz_of(x)) + dt.timedelta(days=1)
                while lt.weekday() >= 5: lt += dt.timedelta(days=1)
                if not dry:
                    c.execute('update emails set slot = ? where id = ?', (lt.replace(tzinfo=None).isoformat(timespec='minutes'), x['id']))
                    P.event(c, 'email-slot', x['id'], 'missed its window; moved to the next weekday')
            continue
        if why:
            if not dry:
                if kind == 'email': P.email_status(c, x['id'], 'cancelled', why)
                else: c.execute('update emails set followup_status = ? where id = ?', ('cancelled', x['id'])); P.event(c, 'email-status', x['id'], f'followup-cancelled: {why}')
            continue
        todo.append((t, kind, x))
    room = max(0, K.EMAILS_PER_DAY - sent_today(c, now))
    todo = todo[:min(K.S['send']['per_run'], room)]
    if dry or not todo:
        c.commit()
        for t, kind, x in todo: print(f'due: {kind} {x["id"]} {x["company"]} <{x["to"]}>')
        if not todo: print(f'nothing due (sent or drafted today: {sent_today(c, now)}; cap {K.EMAILS_PER_DAY})')
        return []
    with K.Lock('sender'):
        for t, kind, x in todo:
            K.exit_if_stopped('the sender')
            subj = x['subject'] if kind == 'email' else x['followup_subject']; body = x['body'] if kind == 'email' else x['followup_body']
            if K.MODE == 'send' and K.mail_adapter() in ('mac-mail', 'mock'):
                r = mail.send(x['id'], x['to'], subj, body)
                if kind == 'email': mark_sent(c, x, f'{now.astimezone(K.TZ):%Y-%m-%dT%H:%M}')
                else: c.execute("update emails set followup_status = 'sent' where id = ?", (x['id'],)); P.event(c, 'email-status', x['id'], 'followup-sent')
            else:
                r = mail.draft(x['id'] + ('-followup' if kind == 'followup' else ''), x['to'], subj, body)
                if kind == 'email': P.email_status(c, x['id'], 'drafted', f'saved as a draft ({r}); the student sends it')
                else: c.execute("update emails set followup_status = 'drafted' where id = ?", (x['id'],)); P.event(c, 'email-status', x['id'], f'followup-drafted: {r}')
            c.commit(); done.append((kind, x['id'])); print(f'{kind} {x["id"]} {x["company"]}: {r}')
    return done

if __name__ == '__main__':
    a = sys.argv
    if '--mark-sent' in a:
        i = a.index('--mark-sent'); xid = a[i + 1]
        when = a[i + 2].replace(' ', 'T') if len(a) > i + 2 else f'{K.now():%Y-%m-%dT%H:%M}'
        c = P.db(); e = c.execute('select * from emails where id = ?', (xid,)).fetchone()
        if not e: sys.exit(f'no email {xid}')
        mark_sent(c, P._email(e), when); c.commit(); print(f'recorded {xid} as sent {when}; its follow-up is scheduled')
    elif '--replied' in a:
        xid = a[a.index('--replied') + 1]; c = P.db(); e = c.execute('select company from emails where id = ?', (xid,)).fetchone()
        if not e: sys.exit(f'no email {xid}')
        P.email_status(c, xid, 'replied', 'the company replied; follow-ups to it are cancelled'); c.commit(); print('follow-ups cancelled for', e['company'])
    else:
        now = dt.datetime.fromisoformat(a[a.index('--now') + 1]).replace(tzinfo=K.TZ) if '--now' in a else None
        try: run(now, '--dry' in a)
        except RuntimeError as e: sys.exit(str(e))
