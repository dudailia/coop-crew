# tracker.html: every role and email in the pipeline, with status, dates, follow-up dues and the clean-pass streak.
# Reads the pipeline only. usage: python3 -I tools/build_tracker.py
import html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P
from build_today import CSS

def e(s): return html.escape(str(s or ''))

def build():
    c = P.db()
    roles = [dict(r) for r in c.execute('select r.*, a.submitted_at, a.clean_pass, a.unconfirmed from roles r '
                                        'left join applications a on a.role_id = r.id order by r.updated_at desc')]
    mails = P.emails()
    dues = [x for x in mails if x['status'] == 'sent' and x['followup_due'] and not x['followup_status']]
    row = lambda cells: '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
    h = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Tracker</title><style>{CSS} table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{text-align:left;padding:5px 6px;'
         f'border-bottom:1px solid var(--line);vertical-align:top}}.wrap{{overflow-x:auto}}</style></head><body><main>',
         f'<h1>Tracker</h1><p class="sub">{len(roles)} roles · {len(mails)} emails and notes · clean-pass streak {P.streak(c)} '
         f'(the review gate holds until 5 in a row, then until you relax it) · updated {K.now():%a %d %b %H:%M}</p>']
    if dues: h.append('<h2>Follow-ups due</h2><ul>' + ''.join(f'<li>{e(x["company"])} · {e(x["to"])} · due {e(x["followup_due"])}</li>' for x in dues) + '</ul>')
    h.append('<h2>Roles</h2><div class="wrap"><table><tr><th>Status</th><th>Company</th><th>Role</th><th>Source</th><th>Deadline</th><th>Submitted</th><th>Clean pass</th><th>Why</th></tr>')
    h += [row([e(r['status']) + (' (unconfirmed)' if r['unconfirmed'] else ''), e(r['company']),
               f'<a href="{e(r["url"])}" target="_blank" rel="noopener">{e(r["title"])}</a>', e(r['source']), e(r['deadline']),
               e(r['submitted_at']), e(r['clean_pass']), e(r['reason'][:120])]) for r in roles]
    h.append('</table></div><h2>Emails and notes</h2><div class="wrap"><table><tr><th>Status</th><th>Company</th><th>To</th><th>Slot</th><th>Sent</th><th>Follow-up</th></tr>')
    h += [row([e(x['status']) + (' (approved)' if x['approved'] and x['status'] == 'planned' else ''), e(x['company']),
               e(x['to'] or x['profile_url']), e(x['slot']), e(x['sent_at']), e(x['followup_status'] or x['followup_due'])]) for x in mails]
    h.append('</table></div></main></body></html>')
    open(f'{K.STATE}/tracker.html', 'w', encoding='utf-8').write('\n'.join(h))
    print(f'tracker.html: {len(roles)} roles, {len(mails)} emails, {len(dues)} follow-ups due')

if __name__ == '__main__':
    build()
