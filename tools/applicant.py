# The applicant's only way to touch application forms. Agents cannot call jev submit directly (tools/guard.py blocks it).
#   prepare <id...>  jev prepare mode for roles whose pack passed the gate: fills and checks each form, submits nothing
#   submit  <id...>  only ids the student approved (/approve or APPROVE.txt). For each: kill switch, daily cap, gate
#                    re-run, jev re-check of the open form, then one submit. NUworks roles are never submitted.
# usage: python3 -I tools/applicant.py prepare|submit <id> [<id> ...]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P, gate, jev

def submitted_today(c):
    d = f'{K.now():%Y-%m-%d}'
    return c.execute('select count(*) from applications where submitted_at like ?', (d + '%',)).fetchone()[0]

def prepare(ids):
    c = P.db(); out = []
    with K.Lock('applicant: jev prepare'):
        for i in ids:
            K.exit_if_stopped('the applicant')
            r = c.execute('select * from roles where id = ?', (i,)).fetchone()
            if not r: out.append(f'{i}: no such role'); continue
            if r['channel'] != 'form': out.append(f'{i}: {r["channel"]} role, no form to prepare'); continue
            if r['status'] not in ('ready', 'approved'): out.append(f'{i}: not prepared, status "{r["status"]}" (the gate must pass first)'); continue
            try: jid = jev.prepare(r['url'])
            except Exception as e: out.append(f'{i}: prepare failed: {e}'); continue
            c.execute('insert or ignore into applications(role_id) values (?)', (i,))
            c.execute('update applications set jev_id = ?, prepared_at = ? where role_id = ?', (jid, P.stamp(), i))
            P.event(c, 'prepared', i, f'jev prepared form {jid}; nothing submitted'); c.commit()
            out.append(f'{i}: form prepared (jev {jid}); waiting for /approve {i}')
    return out

def submit(ids):
    c = P.db(); out = []
    with K.Lock('applicant: jev submit'):
        for i in ids:
            K.exit_if_stopped('the applicant')
            r = c.execute('select * from roles where id = ?', (i,)).fetchone()
            if not r: out.append(f'{i}: no such role'); continue
            if not P.is_approved(i, 'application'):
                out.append(f'{i}: NOT submitted: the student has not approved it (/approve {i})'); continue
            if r['channel'] == 'nuworks': out.append(f'{i}: NOT submitted: NUworks roles are applied to by the student in NUworks'); continue
            if r['channel'] != 'form': out.append(f'{i}: NOT submitted: {r["channel"]} role has no form'); continue
            a = c.execute('select * from applications where role_id = ?', (i,)).fetchone()
            if a and a['submitted_at']: out.append(f'{i}: already submitted {a["submitted_at"]}'); continue
            if submitted_today(c) >= K.APPS_PER_DAY:
                out.append(f'{i}: NOT submitted: the daily cap of {K.APPS_PER_DAY} applications is reached; it waits for tomorrow'); continue
            g = gate.check(i)
            if not g['ok']: out.append(f'{i}: NOT submitted: the gate fails now: ' + '; '.join(g['problems'])); continue
            if not a or not a['jev_id']:
                try: jid = jev.prepare(r['url'])
                except Exception as e: out.append(f'{i}: NOT submitted: prepare failed: {e}'); continue
                c.execute('insert or ignore into applications(role_id) values (?)', (i,))
                c.execute('update applications set jev_id = ?, prepared_at = ? where role_id = ?', (jid, P.stamp(), i)); c.commit()
            else: jid = a['jev_id']
            ok, why = jev.check(jid)
            if not ok: out.append(f'{i}: NOT submitted: the form changed or is not ready on re-check: {why[-200:]}'); continue
            K.exit_if_stopped('the applicant')
            ok, why = jev.submit(jid)
            if not ok:
                c.execute('update applications set unconfirmed = 1 where role_id = ?', (i,))
                P.event(c, 'submit-unconfirmed', i, why[-300:]); c.commit()
                out.append(f'{i}: submit clicked but not confirmed; marked unconfirmed: {why[-200:]}'); continue
            c.execute("update applications set submitted_at = ?, clean_pass = '' where role_id = ?", (P.stamp(), i))
            c.execute("update approvals set used_at = ? where id = ? and kind = 'application'", (P.stamp(), i))
            P.set_status(c, i, 'submitted', f'jev submitted form {jid} after the student approved it'); c.commit()
            out.append(f'{i}: submitted ({r["company"]}, {r["title"]}). Set clean_pass with: pipeline.py set {i} clean_pass=yes|no --why "..."')
    return out

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('prepare', 'submit'): sys.exit('usage: applicant.py prepare|submit <id> ...')
    K.exit_if_stopped('the applicant')
    try: print('\n'.join((prepare if sys.argv[1] == 'prepare' else submit)(sys.argv[2:])))
    except RuntimeError as e: sys.exit(str(e))
