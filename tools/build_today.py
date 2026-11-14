# TODAY.html: the student's review page. One review pack per application (new writing, soft flags, the named-person
# draft, the filled-from-locks list, the field log), HOLD questions, emails and LinkedIn notes waiting for approval, and
# NUworks roles to apply to by hand. Buttons copy the exact command (/approve <id>, /skip <id>) to paste into Claude Code:
# the page itself never approves, submits or sends anything.
# usage: python3 -I tools/build_today.py
import datetime as dt, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P

def e(s): return html.escape(str(s or ''))
def md(s):
    """Just enough Markdown for packs: headings, bullets, tables, paragraphs."""
    out, ul = [], False
    for l in (s or '').splitlines():
        if re.match(r'^\s*[-*]\s+', l):
            if not ul: out.append('<ul>'); ul = True
            out.append(f'<li>{e(re.sub(r"^\s*[-*]\s+", "", l))}</li>'); continue
        if ul: out.append('</ul>'); ul = False
        if re.match(r'^#+\s', l): out.append(f'<h4>{e(l.lstrip("#").strip())}</h4>')
        elif l.startswith('|') and not re.match(r'^\|[-| :]+\|$', l.strip()):
            out.append('<div class="row">' + ''.join(f'<span>{e(c.strip())}</span>' for c in l.strip().strip('|').split('|')) + '</div>')
        elif l.strip() and not re.match(r'^\|[-| :]+\|$', l.strip()): out.append(f'<p>{e(l)}</p>')
    if ul: out.append('</ul>')
    return '\n'.join(out)

def btn(label, cmd, cls=''): return f'<button class="{cls}" data-copy="{e(cmd)}">{e(label)}</button>'

def locks_filled(rid):
    """Answers that came straight from the profile: work authorization, availability, contact details."""
    out = []
    log = K.read(f'{K.OUT}/{rid}/field-log.md')
    for l in log.splitlines():
        if l.startswith('|') and re.search(r'\|\s*(profile|locks|settings|work[_ -]auth)', l, re.I):
            cells = [c.strip() for c in l.strip().strip('|').split('|')]
            if len(cells) >= 2: out.append(f'{cells[0]}: {cells[1]}')
    return out

def pack(r):
    rid, d = r['id'], f'{K.OUT}/{r["id"]}'
    g = K.load_json(f'{d}/gate.json', {})
    parts = [f'<h3>{e(r["company"])}: {e(r["title"])}</h3>',
             f'<div class="meta">{e(r["location"])} · {e(r["source"])} · deadline {e(r["deadline"] or "not stated")} · '
             f'<a href="{e(r["url"])}" target="_blank" rel="noopener">posting</a> · id <code>{e(rid)}</code></div>']
    if r['reason']: parts.append(f'<p class="why">Screener: {e(r["reason"])}</p>')
    if g.get('problems'): parts.append('<div class="block"><b>Gate blocked this pack</b><ul>' + ''.join(f'<li>{e(p)}</li>' for p in g['problems']) + '</ul></div>')
    for f in g.get('flags', []): parts.append(f'<div class="flag">{e(f)}</div>')
    brief = K.read(f'{d}/brief.md')
    if brief: parts.append('<details open><summary>Company brief</summary>' + md(brief) + '</details>')
    if os.path.exists(f'{d}/resume.pdf'): parts.append(f'<p><a href="file://{e(d)}/resume.pdf" target="_blank">resume.pdf</a> (one page, checked)</p>')
    for f, label in (('cover.md', 'Cover note (new writing)'), ('answers.md', 'Portal answers (new writing)')):
        t = K.read(f'{d}/{f}')
        if t.strip(): parts.append(f'<details open><summary>{label}</summary>{md(t)}</details>')
    soft = K.read(f'{d}/soft-flags.md')
    if soft.strip(): parts.append(f'<details open><summary>Soft flags</summary>{md(soft)}</details>')
    person = K.read(f'{d}/person.md')
    if person.strip(): parts.append(f'<details><summary>Named person and note draft</summary>{md(person)}</details>')
    lf = locks_filled(rid)
    if lf: parts.append('<details><summary>Filled from your profile and locks</summary><ul>' + ''.join(f'<li>{e(x)}</li>' for x in lf) + '</ul></details>')
    log = K.read(f'{d}/field-log.md')
    if log.strip(): parts.append(f'<details><summary>Field log (every field, verbatim)</summary>{md(log)}</details>')
    acts = []
    if r['channel'] == 'nuworks':
        acts.append(f'<a class="go" href="{e(r["url"])}" target="_blank" rel="noopener">Apply in NUworks</a>')
        acts.append(btn('Copy: open in NUworks', f'Open NUworks posting {r["posting_id"]} with nuworks_open'))
    if r['status'] in ('ready',) or (r['status'] == 'approved' and r['channel'] == 'form'):
        acts.append(btn('Approve' if r['status'] == 'ready' else 'Approved', f'/approve {rid}', 'ok'))
    acts.append(btn('Skip', f'/skip {rid}', 'skip'))
    parts.append('<div class="acts">' + ''.join(acts) + '</div>')
    return '<section class="pack">' + '\n'.join(parts) + '</section>'

def email_card(x):
    kind = 'LinkedIn note (you send it by hand)' if x['kind'] == 'linkedin' else f'Email to {x["to"]} · {x["region"]} · slot {x["slot"] or "not planned"}'
    body = x['body'] + (f'\n\n--- follow-up ({K.S["send"]["follow_up_working_days"]} working days later unless they reply) ---\n'
                        f'Subject: {x["followup_subject"]}\n\n{x["followup_body"]}' if x.get('followup_body') else '')
    src = f' · <a href="{e(x["source_url"])}" target="_blank" rel="noopener">address source</a>' if x.get('source_url') else ''
    prof = f' · <a href="{e(x["profile_url"])}" target="_blank" rel="noopener">profile</a>' if x.get('profile_url') else ''
    return (f'<section class="pack"><h3>{e(x["company"])}: {e(x["person"] or x["to"])}</h3><div class="meta">{e(kind)}{src}{prof} · id <code>{e(x["id"])}</code></div>'
            + (f'<p><b>Subject:</b> {e(x["subject"])}</p>' if x.get('subject') else '') + f'<pre>{e(body)}</pre>'
            + '<div class="acts">' + (btn('Copy note', x['body']) if x['kind'] == 'linkedin' else '')
            + btn('Approve', f'/approve {x["id"]}', 'ok') + btn('Skip', f'/skip {x["id"]}', 'skip') + '</div></section>')

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--mut:#66665f;--line:#e2e1dc;--ok:#1f6f43;--bad:#9b2c2c;--warn:#8a5a00;--acc:#2f4f8f}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#20201e;--ink:#ecebe6;--mut:#a3a29b;--line:#34332f;--ok:#5fbf86;--bad:#e57373;--warn:#e0b050;--acc:#8fb0ef}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 80px}h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 10px;
border-bottom:1px solid var(--line);padding-bottom:6px}h3{font-size:16px;margin:0 0 4px}h4{font-size:14px;margin:10px 0 4px}
.sub{color:var(--mut);margin:0 0 16px}.pack{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:0 0 12px}
.meta{color:var(--mut);font-size:13px;margin-bottom:8px}.why{color:var(--mut);font-size:14px}details{margin:8px 0}summary{cursor:pointer;font-weight:600}
.row{display:grid;grid-template-columns:1fr 1.4fr .8fr;gap:8px;font-size:13px;border-bottom:1px solid var(--line);padding:3px 0}
.block{border-left:3px solid var(--bad);padding:6px 10px;margin:8px 0}.flag{border-left:3px solid var(--warn);padding:6px 10px;margin:8px 0}
.acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}button,.go{font:inherit;font-size:14px;padding:6px 12px;border-radius:7px;border:1px solid var(--line);
background:var(--card);color:var(--ink);cursor:pointer;text-decoration:none}button.ok{border-color:var(--ok);color:var(--ok)}button.skip{color:var(--mut)}
.go{border-color:var(--acc);color:var(--acc)}pre{white-space:pre-wrap;font:13px/1.45 ui-monospace,Menlo,monospace;background:var(--bg);padding:10px;border-radius:7px;margin:8px 0}
code{font-size:12px}.note{color:var(--mut);font-size:13px}#toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);
padding:6px 12px;border-radius:7px;opacity:0;transition:opacity .15s}#toast.on{opacity:1}ul{margin:4px 0;padding-left:20px}
"""
JS = """document.addEventListener('click',ev=>{const b=ev.target.closest('[data-copy]');if(!b)return;const t=b.dataset.copy;
const done=()=>{const s=document.getElementById('toast');s.textContent='Copied: '+t.slice(0,60)+' (paste it into Claude Code)';s.classList.add('on');setTimeout(()=>s.classList.remove('on'),1800)};
if(navigator.clipboard)navigator.clipboard.writeText(t).then(done,()=>prompt('Copy this:',t));else prompt('Copy this:',t)});"""

def build(path=None):
    c = P.db(); now = K.now()
    roles = [dict(r) for r in c.execute("select * from roles order by deadline = '', deadline, found_at")]
    packs = [r for r in roles if r['status'] in ('ready', 'blocked', 'approved')]
    holds = [r for r in roles if r['status'] == 'hold']
    nuw = [r for r in roles if r['channel'] == 'nuworks' and r['status'] in ('ready', 'approved', 'keep', 'researched', 'tailored')]
    mails = [x for x in P.emails() if x['status'] == 'planned' and not x['approved']]
    approved_mail = [x for x in P.emails() if x['approved'] and x['status'] in ('approved', 'planned')]
    counts = {s: sum(1 for r in roles if r['status'] == s) for s in ('new', 'keep', 'hold', 'dq', 'ready', 'blocked', 'approved', 'submitted')}
    stop = K.stopped()
    h = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Today</title><style>{CSS}</style></head><body><main>',
         f'<h1>Today, {now:%A %d %B}</h1><p class="sub">{e(K.C.get("name") or "No profile yet")} · sourcing: {e(K.SOURCING)} · '
         f'mode: {e(K.MODE)} · nothing is submitted or sent until you approve that exact id. '
         f'Clean-pass streak: {P.streak(c)}.</p>']
    if stop: h.append('<div class="block"><b>The kill switch is ON.</b> Nothing runs until you type /crew-resume.</div>')
    h.append(f'<p class="note">Pipeline: {", ".join(f"{v} {k}" for k, v in counts.items() if v)}. '
             f'<a href="needs-reply.html">needs-reply.html</a> · <a href="tracker.html">tracker.html</a> · <a href="MORNING.md">MORNING.md</a></p>')
    if holds:
        h.append('<h2>Questions for you (HOLD)</h2>')
        for r in holds:
            h.append(f'<section class="pack"><h3>{e(r["company"])}: {e(r["title"])}</h3><div class="meta">id <code>{e(r["id"])}</code> · '
                     f'<a href="{e(r["url"])}" target="_blank" rel="noopener">posting</a></div><p>{e(r["hold_question"])}</p>'
                     f'<div class="acts">{btn("Skip", "/skip " + r["id"], "skip")}</div><p class="note">Answer in Claude Code, for example: '
                     f'"{e(r["id"])}: yes, build it" or "{e(r["id"])}: drop it".</p></section>')
    h.append(f'<h2>Applications to review ({len(packs)})</h2>')
    h += [pack(r) for r in packs if r['channel'] != 'nuworks'] or ['<p class="note">No review packs today.</p>']
    if nuw:
        h.append(f'<h2>NUworks: apply yourself ({len(nuw)})</h2><p class="note">The crew only reads NUworks. Open the posting and apply there with the resume below.</p>')
        h += [pack(r) for r in nuw]
    h.append(f'<h2>Emails and LinkedIn notes waiting for approval ({len(mails)})</h2>')
    h += [email_card(x) for x in mails] or ['<p class="note">None.</p>']
    if approved_mail:
        h.append('<h2>Approved, going in their windows</h2><ul>' + ''.join(f'<li>{e(x["company"])} · {e(x["to"])} · {e(x["slot"])}</li>' for x in approved_mail) + '</ul>')
    h.append(f'<div id="toast"></div><script>{JS}</script></main></body></html>')
    page = '\n'.join(h)
    p = path or f'{K.STATE}/TODAY.html'
    open(p, 'w', encoding='utf-8').write(page)
    print(f'TODAY.html: {len(packs)} packs, {len(holds)} holds, {len(mails)} drafts waiting, {len(nuw)} NUworks ({p})')
    return p

if __name__ == '__main__':
    build()
