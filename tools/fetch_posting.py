# Fetches a posting's text for the screener and researcher, through the public JSON endpoints that JavaScript-rendered
# boards use (Workday, Ashby, Oracle Cloud, Greenhouse embeds, iCIMS; from internship-watcher's fetch_postings.py), or
# as HTML text otherwise. Read-only GETs. Writes out/<id>/posting.md when given a role id.
# usage: python3 -I tools/fetch_posting.py <role-id>     or     python3 -I tools/fetch_posting.py --url <url>
import html, json, os, re, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

MIN_WORDS = 120  # less is a JavaScript shell or an error page

def get(url, as_json=False):
    if re.search(r'linkedin\.com|symplicity\.com', url, re.I): raise ValueError('not fetched: LinkedIn and NUworks are never scraped')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (coop-crew; read-only)', 'Accept': 'application/json' if as_json else 'text/html'})
    with urllib.request.urlopen(req, timeout=20) as r: body = r.read().decode('utf-8', 'ignore')
    return json.loads(body) if as_json else body

def to_text(markup):
    markup = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', markup or '')
    markup = re.sub(r'(?i)<(br|/p|/li|/h\d|/div)[^>]*>', '\n', markup)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', markup))
    return '\n'.join(l for l in (re.sub(r'[ \t\xa0]+', ' ', x).strip() for x in text.splitlines()) if l)

def workday(url):
    m = re.match(r'https://([^.]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)/(job/[^?#]+)', url)
    if not m: return None
    tenant, wd, site, path = m.groups()
    info = get(f'https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/{path}', True)['jobPostingInfo']
    meta = [f'{k}: {info[k]}' for k in ('title', 'location', 'timeType', 'startDate') if info.get(k)]
    return '\n'.join(meta) + '\n\n' + to_text(info.get('jobDescription', ''))

def ashby(url):
    m = re.match(r'https://jobs\.ashbyhq\.com/([^/]+)/([0-9a-f-]{36})', url)
    if not m: return None
    org, jid = m.groups()
    job = next((j for j in get(f'https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true', True).get('jobs', []) if j.get('id') == jid), None)
    if not job: return None
    pay = (job.get('compensation') or {}).get('compensationTierSummary')
    return f"title: {job.get('title')}\nlocation: {job.get('location')}\n" + (f'compensation: {pay}\n' if pay else '') + '\n' + (job.get('descriptionPlain') or '')

def oracle(url):
    m = re.match(r'https://([^/]+)/hcmUI/CandidateExperience/[a-z]{2}(?:-[A-Z]{2})?/sites/([^/]+)/job/(\d+)', url)
    if not m: return None
    host, site, jid = m.groups()
    finder = urllib.parse.quote(f'ById;Id="{jid}",siteNumber={site}')
    job = (get(f'https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder={finder}', True).get('items') or [{}])[0]
    body = '\n'.join(to_text(job.get(k) or '') for k in ('ExternalDescriptionStr', 'ExternalResponsibilitiesStr', 'ExternalQualificationsStr'))
    return f"title: {job.get('Title')}\nlocation: {job.get('PrimaryLocation')}\n\n{body}"

def greenhouse(url, company=''):
    m = re.search(r'greenhouse\.io/([\w-]+)/jobs/(\d+)', url)
    jid = [m.group(2)] if m else urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('gh_jid')
    if not jid: return None
    host = urllib.parse.urlparse(url).hostname or ''
    tokens = [m.group(1)] if m else [t for t in dict.fromkeys(
        [p for p in host.split('.') if p not in ('www', 'careers', 'jobs', 'com', 'co', 'io')][:1] + [re.sub(r'[^a-z0-9]', '', company.lower())]) if t]
    for tok in tokens:
        try: job = get(f'https://boards-api.greenhouse.io/v1/boards/{tok}/jobs/{jid[0]}', True)
        except Exception: continue
        return f"title: {job.get('title')}\nlocation: {(job.get('location') or {}).get('name')}\n\n" + to_text(html.unescape(job.get('content') or ''))
    return None

def icims(url):
    m = re.match(r'https://([^/]+)/jobs/(\d+)', url)
    if not m: return None
    host, jid = m.groups()
    if 'icims.com' not in host: host = f"careers-{[p for p in host.split('.') if p not in ('www', 'careers', 'jobs', 'com')][0]}.icims.com"
    return to_text(get(f'https://{host}/jobs/{jid}/job?in_iframe=1'))

def fetch_text(url, company=''):
    for test, fn in (('icims', icims), ('oraclecloud.com', oracle), ('myworkdayjobs.com', workday), ('jobs.ashbyhq.com', ashby),
                     ('greenhouse', lambda u: greenhouse(u, company)), ('gh_jid=', lambda u: greenhouse(u, company))):
        if test in url:
            try:
                t = fn(url)
                if t and len(t.split()) >= MIN_WORDS: return t
            except Exception: pass
    return to_text(get(url))

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit('usage: fetch_posting.py <role-id> | --url <url>')
    K.exit_if_stopped('the posting fetch')
    if a[0] == '--url': print(fetch_text(a[1])[:20000]); sys.exit(0)
    import pipeline as P
    r = P.db().execute('select * from roles where id = ?', (a[0],)).fetchone()
    if not r: sys.exit(f'no role {a[0]}')
    t = fetch_text(r['url'], r['company'])
    if len(t.split()) < MIN_WORDS: print(f'only {len(t.split())} words came back: use WebFetch on {r["url"]}')
    os.makedirs(f'{K.OUT}/{r["id"]}', exist_ok=True)
    open(f'{K.OUT}/{r["id"]}/posting.md', 'w', encoding='utf-8').write(f"# {r['company']}: {r['title']}\n\nSource: {r['source']}\nURL: {r['url']}\nDeadline: {r['deadline']}\n\n{t}\n")
    print(f'out/{r["id"]}/posting.md: {len(t.split())} words')
