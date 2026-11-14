# Records the student's approval of exact items. Run ONLY by the /approve command (the student typing it), never by an
# agent: .claude/settings.json's PreToolUse hook (tools/guard.py) blocks any agent's call to this file. The student can
# also approve by writing ids, one per line, in APPROVE.txt.
# An approval covers one role's application (the applicant then submits that form) or one email with its follow-up (the
# sender then drafts or sends it in its window). NUworks roles are never submitted by the crew: approving one only marks it
# "apply in NUworks yourself".
# usage: python3 -I tools/approve.py <id> [<id> ...]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P

def approve(ids, source='session'):
    c = P.db(); out = []
    for i in ids:
        i = i.strip().strip(',')
        if not i: continue
        r = c.execute('select id, status, channel, company, title from roles where id = ?', (i,)).fetchone()
        e = c.execute('select id, kind, company, status from emails where id = ?', (i,)).fetchone()
        if r:
            if r['status'] not in ('ready', 'approved'):
                out.append(f'{i}: NOT approved. Its status is "{r["status"]}"; only a role whose review pack passed the gate (ready) can be approved'); continue
            kind = 'application'
            c.execute('insert or replace into approvals(id, kind, approved_at, source) values (?,?,?,?)', (i, kind, P.stamp(), source))
            c.execute("update roles set status = 'approved', updated_at = ? where id = ?", (P.stamp(), i))
            P.event(c, 'approved', i, f'{kind} approved by the student ({source})')
            how = 'apply in NUworks yourself (the crew never applies there)' if r['channel'] == 'nuworks' else \
                  'the applicant re-checks the form, then submits it' if r['channel'] == 'form' else 'outreach drafts the email'
            out.append(f'{i}: approved: {r["company"]}, {r["title"]}. Next: {how}.')
        elif e:
            if e['kind'] == 'linkedin':
                c.execute('insert or replace into approvals(id, kind, approved_at, source) values (?,?,?,?)', (i, 'email', P.stamp(), source))
                P.event(c, 'approved', i, 'LinkedIn note approved: the student sends it by hand')
                out.append(f'{i}: approved LinkedIn note for {e["company"]}. Send it yourself on LinkedIn (no LinkedIn automation).'); continue
            if e['status'] not in ('planned', 'approved'):
                out.append(f'{i}: NOT approved. The email is "{e["status"]}"'); continue
            c.execute('insert or replace into approvals(id, kind, approved_at, source) values (?,?,?,?)', (i, 'email', P.stamp(), source))
            P.email_status(c, i, 'approved', f'approved by the student ({source})')
            out.append(f'{i}: approved email to {e["company"]}. It goes in its send window ({K.MODE} mode: '
                       f'{"saved as a draft for you to send" if K.MODE == "prepare" else "sent"}), with its follow-up 5 to 7 working days later unless they reply.')
        else:
            out.append(f'{i}: no role or email with this id')
    c.commit()
    return out

if __name__ == '__main__':
    ids = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not ids: sys.exit('usage: /approve <id> [<id> ...]   (ids are in TODAY.html)')
    K.exit_if_stopped('/approve')
    print('\n'.join(approve(ids)))
