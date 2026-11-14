# The email planner. Takes the outreach agent's drafts (a JSON list in the kit's email format: id, company, person, to,
# domains, source_url, region, subject, body, followup_subject, followup_body, role_id; LinkedIn notes have profile_url
# and body instead of to), adds them to the pipeline (one email per person, ever), and gives every email without a slot
# the next free one: a weekday, inside the recipient region's send window, send.gap_minutes from every other planned send
# or follow-up, under the student's daily cap, and a second person at the same company on a later day.
# Planning is not approval: nothing is drafted or sent until the student approves the id.
# usage: python3 -I tools/plan_emails.py [drafts.json ...]     (default: data/incoming/emails*.json)
import datetime as dt, glob, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P

def planned_times(c):
    out = []
    for e in c.execute("select * from emails where kind = 'email' and slot != '' and status not in ('skipped', 'cancelled')"):
        x = dict(e)
        t = dt.datetime.fromisoformat(x['slot']).replace(tzinfo=K.tz_of(x))
        out.append((t.astimezone(K.TZ), x['company']))
        if x['followup_due']: out.append((dt.datetime.fromisoformat(x['followup_due']).replace(tzinfo=K.tz_of(x)).astimezone(K.TZ), x['company']))
    return out

def next_slot(x, busy, start):
    tz = K.tz_of(x); a, b = K.window_of(x); gap = K.S['send']['gap_minutes']
    day = start.astimezone(tz).date()
    same_firm_days = {t.date() for t, co in busy if K.matches(co, x['company'])}
    for _ in range(90):
        if day.weekday() < 5 and day not in same_firm_days:
            per_day = sum(1 for t, _ in busy if t.date() == day)
            if per_day < K.EMAILS_PER_DAY:
                t = dt.datetime.combine(day, a, tz)
                while t.time() <= b and t.date() == day:
                    if t > start and K.slot_ok(t, x) and all(abs((t - z).total_seconds()) >= gap * 60 for z, _ in busy):
                        return t
                    t += dt.timedelta(minutes=1)
        day += dt.timedelta(days=1)
    return None

def plan(paths):
    files = []
    for p in paths or [f'{K.INCOMING}/emails*.json']:
        files += sorted(glob.glob(p))
    for f in files:
        P.import_emails(f)
        if os.path.dirname(os.path.abspath(f)) == os.path.abspath(K.INCOMING):
            os.makedirs(f'{K.INCOMING}/done', exist_ok=True); shutil.move(f, f'{K.INCOMING}/done/{os.path.basename(f)}')
    c = P.db(); busy = planned_times(c); start = K.now() + dt.timedelta(hours=1); n = 0
    for e in c.execute("select * from emails where kind = 'email' and slot = '' and status = 'planned' order by created_at").fetchall():
        x = dict(e)
        if K.blocked(x['company']):
            P.email_status(c, x['id'], 'cancelled', f'employer blocked ({K.blocked(x["company"])})'); continue
        t = next_slot(x, busy, start)
        if not t: print(f"{x['id']}: no free slot in the next 90 days"); continue
        slot = t.replace(tzinfo=None).isoformat(timespec='minutes')
        c.execute('update emails set slot = ? where id = ?', (slot, x['id']))
        P.event(c, 'email-slot', x['id'], f'planned for {slot} {K.region(x).get("tz", "")}'); busy.append((t.astimezone(K.TZ), x['company'])); n += 1
    c.commit(); print(f'slotted {n} emails (cap {K.EMAILS_PER_DAY}/day; none goes out before the student approves it)')

if __name__ == '__main__':
    plan(sys.argv[1:])
