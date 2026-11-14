# Closes items without submitting or sending: /skip <ids>. A skipped role keeps its files in out/<id>/.
# usage: python3 -I tools/skip.py <id> [<id> ...] [--why "..."]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P

def skip(ids, why='skipped by the student'):
    c = P.db(); out = []
    for i in ids:
        if c.execute('select 1 from roles where id = ?', (i,)).fetchone():
            P.set_status(c, i, 'skipped', why)
            c.execute("delete from approvals where id = ? and kind = 'application' and used_at is null", (i,))
            out.append(f'{i}: skipped')
        elif c.execute('select 1 from emails where id = ?', (i,)).fetchone():
            P.email_status(c, i, 'skipped', why)
            c.execute("delete from approvals where id = ? and kind = 'email' and used_at is null", (i,))
            out.append(f'{i}: skipped (nothing will be drafted or sent)')
        else: out.append(f'{i}: no role or email with this id')
    c.commit(); return out

if __name__ == '__main__':
    a = sys.argv[1:]; why = 'skipped by the student'
    if '--why' in a: i = a.index('--why'); why = a[i + 1]; a = a[:i] + a[i + 2:]
    if not a: sys.exit('usage: /skip <id> [<id> ...]')
    print('\n'.join(skip(a, why)))
