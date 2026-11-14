# MORNING.md: what the last cycle did, from the pipeline's event log and the logs only. Never touches Mail.
# usage: python3 -I tools/morning.py
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P

def build():
    c = P.db(); now = K.now(); since = f'{(now - dt.timedelta(hours=24)):%Y-%m-%d %H:%M:%S}'
    ev = [dict(r) for r in c.execute('select * from events where at >= ? order by n', (since,))]
    cnt = lambda k: sum(1 for x in ev if x['kind'] == k)
    out = [f'# Morning, {now:%a %d %b %Y} ({now:%H:%M} {K.S["timezone"]})', '']
    if K.stopped(): out += ['**The kill switch is ON.** Nothing runs until you type `/crew-resume`.', '']
    for f, msg in ((K.PAUSE, 'SENDING IS PAUSED'), (K.LOGINF, 'SIGN IN TO MAIL AGAIN')):
        if os.path.exists(f): out += [f'**{msg}:** {K.read(f).strip()[:300]}', '']
    out += [f'**Mode:** {K.MODE}. Nothing was submitted or sent without your approval of that exact id.',
            f'**Your 20 minutes:** read this, answer [needs-reply.html](needs-reply.html), review [TODAY.html](TODAY.html), '
            '`/approve` what is right, apply in NUworks for NUworks roles, send LinkedIn notes by hand.', '']
    try:
        a = json.load(open(f'{K.LOGS}/email-audit-counts.json'))
        out += [f"**Emails needing you:** {a.get('overdue', 0)} overdue, {a.get('new', 0)} new (needs-reply.html)", '']
    except Exception: out += ['**Emails needing you:** no inbox check has run yet', '']
    out += ['## Last 24 hours',
            f'- new roles found: {cnt("role-added")}', f'- verdicts: {cnt("verdict")}',
            f'- forms prepared (not submitted): {cnt("prepared")}', f'- approved by you: {cnt("approved")}',
            f'- emails planned: {cnt("email-planned")}',
            f'- submitted: {sum(1 for x in ev if x["kind"] == "status" and "-> submitted" in x["detail"])}',
            f'- drafts saved or emails sent: {sum(1 for x in ev if x["kind"] == "email-status" and x["detail"].split(":")[0] in ("sent", "drafted", "followup-drafted", "followup-sent"))}', '']
    holds = c.execute("select id, company, title, hold_question from roles where status = 'hold'").fetchall()
    if holds: out += ['## Questions for you'] + [f"- `{r['id']}` {r['company']}, {r['title']}: {r['hold_question']}" for r in holds] + ['']
    ready = c.execute("select id, company, title from roles where status = 'ready'").fetchall()
    out += [f'## Ready for your review: {len(ready)}'] + [f"- `{r['id']}` {r['company']}, {r['title']}" for r in ready] + ['']
    blocked = c.execute("select id, company, title from roles where status = 'blocked'").fetchall()
    if blocked: out += [f'## Blocked by the gate: {len(blocked)}'] + [f"- `{r['id']}` {r['company']}, {r['title']}" for r in blocked] + ['']
    dues = c.execute("select id, company, followup_due from emails where status = 'sent' and followup_status = '' and followup_due is not null order by followup_due").fetchall()
    if dues: out += ['## Follow-ups coming'] + [f"- {r['followup_due']}: {r['company']} (`{r['id']}`)" for r in dues] + ['']
    cy = K.load_json(f'{K.LOGS}/cycle.json', {})
    if cy: out += ['## Last cycle', f"- started {cy.get('started', '?')}, ended {cy.get('ended', 'not recorded')}; steps: "
                   + ', '.join(f"{s['step']} ({s['status']})" for s in cy.get('steps', []) if s['status'] != 'running'), '']
    out += [f'Clean-pass streak: {P.streak(c)}. Kill switch: {"ON" if K.stopped() else "off"}.']
    open(f'{K.STATE}/MORNING.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'MORNING.md: {len(out)} lines')

if __name__ == '__main__':
    build()
