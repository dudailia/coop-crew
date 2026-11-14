# Reads company-run job boards through their public JSON APIs (Greenhouse, Lever, Ashby, Workable, SmartRecruiters,
# Recruitee, Personio; from job-agents-kit's scan_postings.py) and writes the postings that match the student's targets
# to data/incoming/web-<time>.json for `pipeline.py import`. Read-only HTTP GETs, no logins, no forms, no aggregators.
# A board is "greenhouse:cohere", a board URL (boards.greenhouse.io/x, jobs.lever.co/x, jobs.ashbyhq.com/x, ...), or a
# line in data/boards.txt (one per line; the scout adds boards it finds there).
# usage: python3 -I tools/scan_boards.py [board ...] [--max N] [--per-board N] [--out FILE] [--all-titles]
import datetime as dt, html, json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

UA = {'User-Agent': 'coop-crew/0.1 (student job search; read-only)', 'Accept': 'application/json'}
BOARDS_FILE = f'{K.DATA}/boards.txt'

def get(url, timeout=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', 'ignore'))

def text(s):
    s = html.unescape(s or '')
    s = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', s)
    s = re.sub(r'(?i)<(br|/p|/li|/h\d|/div)[^>]*>', '\n', s)
    s = html.unescape(re.sub(r'<[^>]+>', ' ', s))
    return '\n'.join(l for l in (re.sub(r'[ \t\xa0]+', ' ', x).strip() for x in s.splitlines()) if l)

def parse_board(b):
    b = b.strip()
    m = re.match(r'^(greenhouse|gh|lever|ashby|workable|sr|smartrecruiters|recruitee|personio):([\w.-]+)$', b, re.I)
    if m: return {'gh': 'greenhouse', 'sr': 'smartrecruiters'}.get(m.group(1).lower(), m.group(1).lower()), m.group(2)
    for rx, kind in ((r'(?:job-boards(?:\.eu)?|boards)\.greenhouse\.io/([\w-]+)', 'greenhouse'), (r'jobs\.lever\.co/([\w-]+)', 'lever'),
                     (r'jobs\.ashbyhq\.com/([\w.-]+)', 'ashby'), (r'apply\.workable\.com/([\w-]+)', 'workable'),
                     (r'jobs\.smartrecruiters\.com/([\w-]+)', 'smartrecruiters'), (r'([\w-]+)\.recruitee\.com', 'recruitee'),
                     (r'([\w-]+)\.jobs\.personio\.(?:de|com)', 'personio')):
        m = re.search(rx, b)
        if m: return kind, m.group(1)
    return None, None

def jobs_of(kind, b):
    """[(company, title, location, url, posting_id, description, posted)]"""
    out = []
    if kind == 'greenhouse':
        d = get(f'https://boards-api.greenhouse.io/v1/boards/{b}/jobs?content=true')
        try: co = get(f'https://boards-api.greenhouse.io/v1/boards/{b}').get('name') or b
        except Exception: co = b
        for j in d.get('jobs', []):
            out.append((co, j['title'], (j.get('location') or {}).get('name', ''), j['absolute_url'], str(j['id']), text(j.get('content')), j.get('updated_at', '')[:10]))
    elif kind == 'ashby':
        d = get(f'https://api.ashbyhq.com/posting-api/job-board/{b}?includeCompensation=true')
        co = (d.get('organization') or {}).get('name') if isinstance(d.get('organization'), dict) else None
        for j in d.get('jobs', []):
            pay = (j.get('compensation') or {}).get('compensationTierSummary') or ''
            loc = j.get('location', '') + (' (remote)' if j.get('isRemote') else '')
            out.append((co or b.replace('-', ' ').title(), j['title'], loc, j['jobUrl'], j['id'],
                        (f'Compensation: {pay}\n' if pay else '') + (j.get('descriptionPlain') or text(j.get('descriptionHtml'))), (j.get('publishedAt') or '')[:10]))
    elif kind == 'lever':
        for j in get(f'https://api.lever.co/v0/postings/{b}?mode=json'):
            lists = '\n'.join(f"{x.get('text', '')}\n{text(x.get('content'))}" for x in j.get('lists', []))
            out.append((b.replace('-', ' ').title(), j['text'], (j.get('categories') or {}).get('location', ''), j['hostedUrl'], j['id'],
                        (j.get('descriptionPlain') or '') + '\n' + lists, dt.datetime.fromtimestamp(j.get('createdAt', 0) / 1000).strftime('%Y-%m-%d')))
    elif kind == 'workable':
        d = get(f'https://apply.workable.com/api/v1/widget/accounts/{b}')
        for j in d.get('jobs', []):
            loc = ', '.join(x for x in (j.get('city'), j.get('country'), 'Remote' if j.get('telecommuting') else '') if x)
            out.append((d.get('name') or b, j['title'], loc, j.get('url') or j.get('shortlink'), j.get('shortcode', ''), text(j.get('description')), ''))
    elif kind == 'smartrecruiters':
        d = get(f'https://api.smartrecruiters.com/v1/companies/{b}/postings?limit=100')
        for j in d.get('content', []):
            out.append(((j.get('company') or {}).get('name') or b, j['name'], (j.get('location') or {}).get('city', ''),
                        f"https://jobs.smartrecruiters.com/{b}/{j['id']}", j['id'], '', (j.get('releasedDate') or '')[:10]))
    elif kind == 'recruitee':
        for j in get(f'https://{b}.recruitee.com/api/offers/').get('offers', []):
            out.append((j.get('company_name') or b, j['title'], j.get('location', ''), j['careers_url'], str(j['id']), text(j.get('description')), ''))
    return out

def scan(boards, max_total=None, per_board=None, all_titles=False):
    T = K.S['targets']
    title_rx = re.compile(T.get('title_regex') or '.', re.I); excl = re.compile(T.get('exclude_regex') or r'(?!x)x', re.I)
    found, errors = [], []
    for raw in boards:
        kind, b = parse_board(raw)
        if not kind: errors.append(f'{raw}: not a board this scanner reads'); continue
        try: js = jobs_of(kind, b)
        except Exception as e: errors.append(f'{kind}:{b}: {e.__class__.__name__} {str(e)[:80]}'); continue
        n = 0
        for co, title, loc, url, pid, desc, posted in js:
            if not all_titles and (not title_rx.search(title) or excl.search(title)): continue
            if K.blocked(co): continue
            found.append({'source': 'web', 'board': f'{kind}:{b}', 'company': co, 'title': title.strip(), 'location': loc, 'url': url,
                          'posting_id': pid, 'posted': posted, 'description': desc[:12000]})
            n += 1
            if per_board and n >= per_board: break
        print(f'{kind}:{b}: {len(js)} postings, {n} match the targets')
        time.sleep(0.5)
        if max_total and len(found) >= max_total: found = found[:max_total]; break
    for e in errors: print('error:', e)
    return found

def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    boards = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] not in ('--max', '--per-board', '--out'))]
    if not boards and os.path.exists(BOARDS_FILE): boards = [l.strip() for l in open(BOARDS_FILE) if l.strip() and not l.startswith('#')]
    if not boards: sys.exit('no boards: pass some (greenhouse:x, ashby:x, a board URL) or list them in data/boards.txt')
    K.exit_if_stopped('the board scan')
    found = scan(boards, int(opt('--max')) if opt('--max') else None, int(opt('--per-board')) if opt('--per-board') else None, '--all-titles' in a)
    out = opt('--out') or f'{K.INCOMING}/web-{K.now():%Y%m%d-%H%M%S}.json'
    K.save_json(out, found); print(f'{len(found)} postings written to {out}')

if __name__ == '__main__':
    main()
