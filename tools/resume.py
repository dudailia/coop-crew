# Builds out/<role>/resume.pdf from out/<role>/resume.md with the Option A template, and FAILS (exit 1) unless the PDF is
# exactly one page and every number and name in it is in profile/facts.md or the posting. Writes resume.check.json, which
# the gate reads.
#
# resume.md format (text only, single column; section order is fixed):
#   ---
#   title: <the posting's exact job title>
#   ---
#   ## Summary            2 to 3 lines
#   ## Skills             one line per group, no colons
#   ## Experience
#   ### Employer | Title | City | Jan 2025 to Jun 2025
#   - bullet
#   ## Projects
#   ### Name | Role | 2025
#   - bullet
#   ## Education
#   ### School | Degree | Expected May 2028
#   - line
#
# usage: python3 -I tools/resume.py <role-id>
#        python3 -I tools/resume.py --md resume.md --pdf out.pdf [--role <id>]
import html, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, check_msgs as CM

ORDER = ['Summary', 'Skills', 'Experience', 'Projects', 'Education']

def parse(md):
    meta, body = {}, md
    m = re.match(r'^---\n(.*?)\n---\n', md, re.S)
    if m:
        for l in m.group(1).splitlines():
            k, _, v = l.partition(':'); meta[k.strip()] = v.strip()
        body = md[m.end():]
    secs, cur = [], None
    for l in body.splitlines():
        if l.startswith('## '): cur = {'name': l[3:].strip(), 'items': []}; secs.append(cur)
        elif cur is not None and l.strip(): cur['items'].append(l.rstrip())
    return meta, secs

def esc(s): return html.escape(s, quote=False)

def to_html(meta, secs):
    problems = []
    names = [s['name'] for s in secs]
    want = [n for n in ORDER if n in names]
    if names != want: problems.append(f'sections must be in the order {", ".join(ORDER)} (got {", ".join(names)})')
    if not meta.get('title'): problems.append('no title: the posting\'s exact job title goes in the front matter')
    out = []
    for s in secs:
        out.append(f'<h2>{esc(s["name"])}</h2>')
        if s['name'] == 'Summary':
            text = ' '.join(i.strip() for i in s['items'])
            out.append(f'<p>{esc(text)}</p>')
            continue
        ul = False
        for i in s['items']:
            if i.startswith('### '):
                if ul: out.append('</ul>'); ul = False
                parts = [p.strip() for p in i[4:].split('|')]
                when = parts[-1] if len(parts) > 2 else ''
                what = parts[0]; sub = ', '.join(p for p in parts[1:-1 if when else None] if p)
                out.append(f'<div class="entry"><div class="head"><span class="what">{esc(what)}</span><span class="when">{esc(when)}</span></div>'
                           + (f'<div class="sub">{esc(sub)}</div>' if sub else '') + '</div>')
            elif re.match(r'^\s*[-*]\s+', i):
                if not ul: out.append('<ul>'); ul = True
                out.append('<li>' + esc(re.sub(r'^\s*[-*]\s+', '', i)) + '</li>')
            else:
                if ul: out.append('</ul>'); ul = False
                out.append(f'<p>{esc(i.strip())}</p>')
        if ul: out.append('</ul>')
    return '\n'.join(out), problems

def contact_line():
    c = K.C; parts = [c.get('city'), c.get('phone'), c.get('email'), c.get('linkedin'), c.get('github'), c.get('portfolio')]
    if not c.get('github'): parts.append('(GitHub missing from profile)')
    return ' · '.join(esc(p.replace('https://', '').replace('www.', '')) for p in parts if p)

def build(md_path, pdf_path, role=None):
    md = K.read(md_path)
    if not md: return {'ok': False, 'pages': None, 'problems': [f'{md_path} is empty or missing']}
    meta, secs = parse(md)
    body, problems = to_html(meta, secs)
    tpl = K.read(f'{K.ROOT}/templates/resume/resume.html')
    page = tpl.replace('{{NAME}}', esc(K.C.get('name') or 'NAME MISSING')).replace('{{TITLE}}', esc(meta.get('title', ''))) \
              .replace('{{CONTACT}}', contact_line()).replace('{{BODY}}', body)
    html_path = os.path.splitext(pdf_path)[0] + '.html'
    open(html_path, 'w', encoding='utf-8').write(page)
    r = subprocess.run(['node', f'{K.ROOT}/tools/render_pdf.mjs', html_path, pdf_path], capture_output=True, text=True, cwd=K.ROOT)
    pages = None
    try: pages = json.loads(r.stdout.strip().splitlines()[-1])['pages']
    except Exception: problems.append(f'PDF build failed: {(r.stderr or r.stdout)[-300:]}')
    if pages is not None and pages != 1: problems.append(f'the resume is {pages} pages; it must be exactly one page')
    problems += CM.unknown_claims(re.sub(r'^---\n.*?\n---\n', '', md, flags=re.S), role)
    problems += [p for p in CM.style(md, 'resume') if 'em dash' in p or 'banned' in p]
    if ':' in ' '.join(i for s in secs for i in s['items'] if not i.startswith('### ')):
        problems.append('a colon in the resume body (no colons in application writing)')
    res = {'ok': not problems, 'pages': pages, 'problems': problems, 'pdf': pdf_path}
    K.save_json(os.path.join(os.path.dirname(pdf_path), 'resume.check.json'), res)
    if problems and os.path.exists(pdf_path) and pages != 1:
        os.replace(pdf_path, pdf_path + '.failed')  # a failed build never leaves a resume.pdf behind
    return res

if __name__ == '__main__':
    a = sys.argv[1:]
    if '--md' in a:
        res = build(a[a.index('--md') + 1], a[a.index('--pdf') + 1], a[a.index('--role') + 1] if '--role' in a else None)
    elif a and a[0] == 'base':  # the base resume from /setup: builds profile/resume.md into out/base/
        d = f'{K.OUT}/base'; os.makedirs(d, exist_ok=True)
        if not os.path.exists(f'{K.PROFILE}/resume.md'): sys.exit('No profile/resume.md yet: /setup writes it.')
        shutil.copyfile(f'{K.PROFILE}/resume.md', f'{d}/resume.md'); res = build(f'{d}/resume.md', f'{d}/resume.pdf', None)
    elif a:
        d = f'{K.OUT}/{a[0]}'; res = build(f'{d}/resume.md', f'{d}/resume.pdf', a[0])
    else: sys.exit(__doc__ or 'usage: resume.py <role-id> | base | --md F --pdf F')
    print(f"resume: {'PASS' if res['ok'] else 'FAIL'} (pages: {res['pages']})")
    for p in res['problems']: print(f'  - {p}')
    sys.exit(0 if res['ok'] else 1)
