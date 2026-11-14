# The one application record: data/pipeline.sqlite. Roles, applications, emails, contacts, approvals, and an event log.
# Every change writes an event (what happened, from where), so no row changes without a real event.
#
# usage: python3 -I tools/pipeline.py init
#        python3 -I tools/pipeline.py import [file-or-folder ...]      roles from scouts (default data/incoming/*.json)
#        python3 -I tools/pipeline.py import-emails <file.json>        email and LinkedIn drafts from outreach
#        python3 -I tools/pipeline.py verdict <id> KEEP|HOLD|DQ --reason "..." [--question "..."]
#        python3 -I tools/pipeline.py status <id> <status> --why "..."
#        python3 -I tools/pipeline.py set <id> key=value ... --why "..."  (application fields: clean_pass, unconfirmed, jev_id)
#        python3 -I tools/pipeline.py list [--status S] [--source S] [--json]
#        python3 -I tools/pipeline.py show <id>
#        python3 -I tools/pipeline.py streak | dues
import argparse, datetime as dt, glob, hashlib, json, os, re, shutil, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

ROLE_STATUSES = ['new', 'keep', 'hold', 'dq', 'researched', 'tailored', 'ready', 'blocked', 'approved', 'submitted',
                 'applied-by-hand', 'skipped', 'interview', 'rejected', 'offer', 'closed']
SCHEMA = """
create table if not exists roles (
  id text primary key, source text not null, company text not null, title text not null, location text default '',
  url text default '', posting_id text default '', deadline text default '', posted text default '', start text default '',
  pay text default '', work_style text default '', channel text default 'form', found_at text, status text default 'new',
  verdict text default '', reason text default '', hold_question text default '', fit integer default 0,
  banned_check text default '', person text default '', notes text default '', updated_at text);
create unique index if not exists roles_url on roles(url) where url != '';
create table if not exists applications (
  role_id text primary key references roles(id), prepared_at text, jev_id text default '', submitted_at text,
  clean_pass text default '', unconfirmed integer default 0);
create table if not exists emails (
  id text primary key, role_id text default '', kind text default 'email', company text not null, person text default '',
  to_addr text default '', domains text default '[]', source_url text default '', region text default '', slot text default '',
  subject text default '', body text default '', followup_subject text default '', followup_body text default '',
  profile_url text default '', status text default 'planned', hold text default '', sent_at text, followup_due text,
  followup_status text default '', created_at text);
create table if not exists contacts (
  id integer primary key autoincrement, company text, name text, title text, email text default '', email_source text default '',
  profile_url text default '', evidence_url text default '');
create table if not exists approvals (
  id text not null, kind text not null, approved_at text not null, source text not null, used_at text,
  primary key (id, kind));
create table if not exists events (
  n integer primary key autoincrement, at text not null, kind text not null, ref text not null, detail text default '');
"""

def db():
    c = sqlite3.connect(K.PIPELINE); c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c

def stamp(): return f'{K.now():%Y-%m-%d %H:%M:%S}'
def event(c, kind, ref, detail=''):
    c.execute('insert into events(at, kind, ref, detail) values (?,?,?,?)', (stamp(), kind, ref, detail))

def slug(s): return re.sub(r'[^a-z0-9]+', '-', K.fold(s)).strip('-')[:20] or 'x'
def role_id(company, title, url):
    h = hashlib.sha1(f'{K.fold(company)}|{K.fold(title)}|{url}'.encode()).hexdigest()[:6]
    return f'{slug(company)}-{h}'

def norm_title(s): return ' '.join(re.sub(r'[^\w ]', ' ', K.fold(s)).split())

def find_dupe(c, r):
    if r.get('url'):
        x = c.execute('select id from roles where url = ?', (r['url'],)).fetchone()
        if x: return x['id']
    if r.get('posting_id'):
        x = c.execute('select id from roles where source = ? and posting_id = ?', (r['source'], str(r['posting_id']))).fetchone()
        if x: return x['id']
    # Same employer, same title, same place: the same role seen on two sources (a board and NUworks, say).
    for x in c.execute('select id, company, title, location, url from roles'):
        if norm_title(x['title']) == norm_title(r['title']) and K.matches(r['company'], x['company']) \
                and norm_title(x['location']) == norm_title(r.get('location', '')): return x['id']
    return None

def add_role(c, r):
    """Adds one role if it is new. Returns (id, added?)."""
    for k in ('source', 'company', 'title'):
        if not r.get(k): raise ValueError(f'role without "{k}": {json.dumps(r)[:200]}')
    d = find_dupe(c, r)
    if d: return d, False
    rid = role_id(r['company'], r['title'], r.get('url', ''))
    cols = ['id', 'source', 'company', 'title', 'location', 'url', 'posting_id', 'deadline', 'posted', 'start', 'pay',
            'work_style', 'channel', 'found_at', 'status', 'updated_at']
    channel = r.get('channel') or ('nuworks' if r['source'] == 'nuworks' else 'form')
    vals = [rid, r['source'], r['company'], r['title'], r.get('location', ''), r.get('url', ''), str(r.get('posting_id', '')),
            r.get('deadline', ''), r.get('posted', ''), r.get('start', ''), r.get('pay', ''), r.get('work_style', ''), channel,
            stamp(), 'new', stamp()]
    c.execute(f'insert into roles({",".join(cols)}) values ({",".join("?" * len(cols))})', vals)
    event(c, 'role-added', rid, f"{r['source']}: {r['company']} / {r['title']}")
    if r.get('description'):
        os.makedirs(f'{K.OUT}/{rid}', exist_ok=True)
        open(f'{K.OUT}/{rid}/posting.md', 'w', encoding='utf-8').write(
            f"# {r['company']}: {r['title']}\n\nSource: {r['source']}\nURL: {r.get('url', '')}\nDeadline: {r.get('deadline', '')}\n\n{r['description']}\n")
    return rid, True

def import_roles(paths):
    c = db(); added = dupes = 0
    files = []
    for p in paths or [K.INCOMING]:
        files += sorted(glob.glob(f'{p}/*.json')) if os.path.isdir(p) else [p]
    files = [f for f in files if not os.path.basename(f).startswith('emails')]
    for f in files:
        rows = K.load_json(f, None)
        if not isinstance(rows, list): print(f'skipped {f}: not a JSON list'); continue
        for r in rows:
            try: _, new = add_role(c, r)
            except ValueError as e: print(f'skipped: {e}'); continue
            added += new; dupes += (not new)
        if os.path.dirname(os.path.abspath(f)) == os.path.abspath(K.INCOMING):
            os.makedirs(f'{K.INCOMING}/done', exist_ok=True); shutil.move(f, f'{K.INCOMING}/done/{os.path.basename(f)}')
    c.commit(); print(f'imported {added} new roles, {dupes} already in the pipeline'); return added

def set_status(c, rid, status, why):
    if status not in ROLE_STATUSES: raise SystemExit(f'unknown status {status}; one of {", ".join(ROLE_STATUSES)}')
    if not why: raise SystemExit('a status change needs --why (the real event behind it)')
    r = c.execute('select status from roles where id = ?', (rid,)).fetchone()
    if not r: raise SystemExit(f'no role {rid}')
    c.execute('update roles set status = ?, updated_at = ? where id = ?', (status, stamp(), rid))
    event(c, 'status', rid, f"{r['status']} -> {status}: {why}")

def verdict(c, rid, v, reason, question=''):
    v = v.upper()
    if v not in ('KEEP', 'HOLD', 'DQ'): raise SystemExit('verdict is KEEP, HOLD or DQ')
    if v == 'HOLD' and not question: raise SystemExit('a HOLD needs --question: the exact question for the student')
    if not reason: raise SystemExit('a verdict needs --reason')
    r = c.execute('select company from roles where id = ?', (rid,)).fetchone()
    if not r: raise SystemExit(f'no role {rid}')
    b = K.blocked(r['company'])
    if b and v == 'KEEP': raise SystemExit(f'{r["company"]} is covered by "{b}" (locks or banned list): it cannot be KEEP')
    c.execute('update roles set verdict = ?, reason = ?, hold_question = ?, status = ?, banned_check = ?, updated_at = ? where id = ?',
              (v, reason, question, v.lower(), f'blocked by "{b}"' if b else 'clear', stamp(), rid))
    event(c, 'verdict', rid, f'{v}: {reason}' + (f' | ask: {question}' if question else ''))

APP_FIELDS = {'clean_pass': ('yes', 'no', ''), 'unconfirmed': ('0', '1'), 'jev_id': None, 'prepared_at': None}
def set_fields(c, rid, pairs, why):
    if not why: raise SystemExit('a change needs --why')
    c.execute('insert or ignore into applications(role_id) values (?)', (rid,))
    for p in pairs:
        k, _, v = p.partition('=')
        if k not in APP_FIELDS: raise SystemExit(f'unknown field {k}; one of {", ".join(APP_FIELDS)}')
        if APP_FIELDS[k] and v not in APP_FIELDS[k]: raise SystemExit(f'{k} must be one of {APP_FIELDS[k]}')
        c.execute(f'update applications set {k} = ? where role_id = ?', (v, rid))
        event(c, 'set', rid, f'{k}={v}: {why}')

def streak(c=None):
    """Consecutive clean_pass = yes at the end of the submitted list. A no or a blank at the end means 0."""
    c = c or db(); n = 0
    for r in c.execute("select clean_pass from applications where submitted_at is not null order by submitted_at desc"):
        if r['clean_pass'] == 'yes': n += 1
        else: break
    return n

# ---- emails: the outreach plan, kept here instead of the kit's data/emails.json ----
EMAIL_COLS = ['id', 'role_id', 'kind', 'company', 'person', 'to_addr', 'domains', 'source_url', 'region', 'slot', 'subject', 'body',
              'followup_subject', 'followup_body', 'profile_url', 'status', 'hold', 'sent_at', 'followup_due', 'followup_status']
def _email(r):
    x = dict(r); x['to'] = x.pop('to_addr'); x['domains'] = json.loads(x.get('domains') or '[]')
    x['approved'] = is_approved(x['id'], 'email')
    return x
def emails(kind=None):
    c = db(); q = 'select * from emails' + (' where kind = ?' if kind else '') + ' order by slot, id'
    return [_email(r) for r in c.execute(q, (kind,) if kind else ())]

def import_emails(path):
    c = db(); n = 0
    for x in K.load_json(path, []):
        if not x.get('id') or not x.get('company'): print(f'skipped (no id or company): {str(x)[:120]}'); continue
        if c.execute('select 1 from emails where id = ?', (x['id'],)).fetchone(): print(f'skipped {x["id"]}: already planned'); continue
        to = (x.get('to') or '').lower()
        if to and c.execute("select 1 from emails where lower(to_addr) = ? and kind = 'email'", (to,)).fetchone():
            print(f'skipped {x["id"]}: {to} already has an email (one email per person)'); continue
        vals = {k: x.get(k, '') for k in EMAIL_COLS}; vals['to_addr'] = x.get('to', ''); vals['domains'] = json.dumps(x.get('domains', []))
        vals['kind'] = x.get('kind') or ('linkedin' if x.get('profile_url') and not x.get('to') else 'email')
        vals['status'] = 'planned'; vals['sent_at'] = None; vals['followup_due'] = None
        c.execute(f'insert into emails({",".join(EMAIL_COLS)}, created_at) values ({",".join("?" * len(EMAIL_COLS))}, ?)',
                  [vals[k] for k in EMAIL_COLS] + [stamp()])
        event(c, 'email-planned', x['id'], f"{vals['kind']} to {x.get('person') or x.get('to') or x.get('profile_url')} at {x['company']}"); n += 1
    c.commit(); print(f'planned {n} new drafts'); return n

def email_status(c, eid, status, why, **extra):
    sets = ', '.join(['status = ?'] + [f'{k} = ?' for k in extra])
    c.execute(f'update emails set {sets} where id = ?', [status, *extra.values(), eid])
    event(c, 'email-status', eid, f'{status}: {why}')

# ---- approvals: written only by tools/approve.py (from /approve) or read from APPROVE.txt, which the student writes ----
def file_approvals():
    out = set()
    if os.path.exists(K.APPROVE_FILE):
        for l in open(K.APPROVE_FILE, encoding='utf-8'):
            l = l.split('#')[0].strip()
            if l: out.add(l)
    return out
def is_approved(xid, kind):
    c = sqlite3.connect(K.PIPELINE); c.executescript(SCHEMA)
    return bool(c.execute('select 1 from approvals where id = ? and kind = ?', (xid, kind)).fetchone()) or xid in file_approvals()

def show(rid):
    c = db(); r = c.execute('select * from roles where id = ?', (rid,)).fetchone()
    if not r: raise SystemExit(f'no role {rid}')
    print(json.dumps(dict(r), indent=1))
    a = c.execute('select * from applications where role_id = ?', (rid,)).fetchone()
    if a: print(json.dumps(dict(a), indent=1))
    for e in c.execute('select at, kind, detail from events where ref = ? order by n', (rid,)): print(f"{e['at']} {e['kind']}: {e['detail']}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
    ap.add_argument('--reason', default=''); ap.add_argument('--question', default=''); ap.add_argument('--why', default='')
    ap.add_argument('--status'); ap.add_argument('--source'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args(); c = db()
    if a.cmd == 'init': print(f'pipeline ready: {K.PIPELINE}')
    elif a.cmd == 'import': import_roles(a.args)
    elif a.cmd == 'import-emails': import_emails(a.args[0])
    elif a.cmd == 'verdict': verdict(c, a.args[0], a.args[1], a.reason, a.question); c.commit(); print(f'{a.args[0]}: {a.args[1].upper()}')
    elif a.cmd == 'status': set_status(c, a.args[0], a.args[1], a.why); c.commit(); print(f'{a.args[0]}: {a.args[1]}')
    elif a.cmd == 'set': set_fields(c, a.args[0], a.args[1:], a.why); c.commit(); print('ok')
    elif a.cmd == 'list':
        q, p = 'select * from roles where 1=1', []
        if a.status: q += ' and status = ?'; p.append(a.status)
        if a.source: q += ' and source = ?'; p.append(a.source)
        rows = [dict(r) for r in c.execute(q + ' order by found_at', p)]
        if a.json: print(json.dumps(rows, indent=1))
        else:
            for r in rows: print(f"{r['id']:28} {r['status']:10} {r['source']:8} {r['company'][:24]:24} {r['title'][:50]}")
            print(f'{len(rows)} roles')
    elif a.cmd == 'show': show(a.args[0])
    elif a.cmd == 'streak': print(f'clean-pass streak: {streak(c)} (the review gate holds until 5, and after that until the student relaxes it)')
    elif a.cmd == 'dues':
        today = f'{K.now():%Y-%m-%d}'
        for e in c.execute("select id, company, followup_due from emails where status = 'sent' and followup_status = '' and followup_due <= ?", (today + 'T23:59',)):
            print(f"follow-up due {e['followup_due']}: {e['id']} {e['company']}")
    else: raise SystemExit(f'unknown command {a.cmd}')

if __name__ == '__main__':
    main()
