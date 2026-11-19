# NUworks job alerts, read from the student's own email: the default NUworks path. NUworks (Symplicity CSM) can email
# the student when new postings match a saved search ("search agent"). This reads those emails, never the NUworks site,
# and turns each listed posting into a pipeline row with source "nuworks" (channel nuworks: the student applies in
# NUworks themselves; the crew never does).
#
# Where the emails come from (all local, read-only):
#   data/nuworks-alerts/  alert emails the inbox audit saved from Apple Mail (tools/email_audit.py, sender match only)
#   data/inbox/           .eml files the student saved (the .eml inbox adapter's folder)
#   data/nuworks-import/  .eml files the student dropped there by hand (tools/nuworks_import.py also reads this folder)
# An email counts as a NUworks alert when its sender matches settings nuworks.alert_senders (default: symplicity.com),
# or its subject names NUworks or a job alert and it links to a Symplicity host. Each file is read once (logs).
# Writes data/incoming/nuworks-alerts-<time>.json for `pipeline.py import`. Runs only in sourcing mode
# "nuworks+external"; it needs no NUworks sign-in and never loads a NUworks page.
# usage: python3 -I tools/nuworks_alerts.py [file.eml ...] [--dry-run]
import base64, datetime as dt, email, email.policy, email.utils, glob, hashlib, html, json, os, re, sys, urllib.parse
from html.parser import HTMLParser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

FOLDERS = [f'{K.DATA}/nuworks-alerts', f'{K.DATA}/inbox', f'{K.DATA}/nuworks-import']
SEEN_FILE = f'{K.LOGS}/nuworks-alerts-seen.json'
SYMPLICITY = re.compile(r'^https?://([\w-]+\.)*symplicity\.com/', re.I)
JOB_ID = [re.compile(r'/jobs?/(?:detail/|view/)?([A-Za-z0-9]{6,})(?:[/?#]|$)', re.I),
          re.compile(r'[?&](?:job_id|jid|jobid)=([A-Za-z0-9]{6,})', re.I),
          re.compile(r'^(?=[^#]*job)(?![^#]*[?&]s=event)[^#]*[?&]id=([A-Za-z0-9]{6,})', re.I)]   # id= only on a job link, never an event
NOT_A_TITLE = re.compile(r'^(view|apply|apply now|details?|more|here|click here|log ?in|sign ?in|nuworks|unsubscribe|manage|'
                         r'edit (your )?(search|agent|alert)s?|search agents?|view all|see all|privacy|terms|help|contact|rsvp|register|'
                         r'symplicity|northeastern|view (job|posting|details))\b', re.I)
LABEL = re.compile(r'^(employer|organization|company|location|city|deadline|application deadline|apply by|expires|expiration date|'
                   r'position type|job type|posted|date posted|industry|job id|salary|pay|compensation)\s*:\s*', re.I)
DATE = re.compile(r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+20\d\d|\d{1,2}/\d{1,2}/20\d\d|20\d\d-\d\d-\d\d)', re.I)
STATES = 'AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC'
PLACE = re.compile(r'(?i:\b(remote|hybrid|on-?site)\b)|,\s*(' + STATES + r')\b|(?i:,\s*(massachusetts|new york|california|united states|usa)\b)')
# A location line in the wider sense, used only for the line after the employer: "City, Region, Country", "City,
# Country", "Multiple Locations", "Nationwide, Country", as NUworks alerts print them. Too loose to tell an employer
# ("Northeastern University, College of Science") from a place, so it never decides the employer.
WIDE_PLACE = re.compile(PLACE.pattern + r'|^[A-Z][^,]{0,60}(,\s*[A-Z][^,]{0,40})?,\s*[A-Z][A-Za-z .]{1,40}$|^(?i:multiple locations)$|^(?i:nationwide)\b')
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
# boilerplate lines between postings (not an employer or a place); unlike NOT_A_TITLE it keeps "Northeastern University, ..."
NOT_INFO = re.compile(r'^(view|apply|apply now|details?|more|here|click here|log ?in|sign ?in|unsubscribe|manage|rsvp|register|'
                      r'view all|see all|privacy|terms|help|contact|view (job|posting|details))\b', re.I)
POSITION_TYPE = re.compile(r'^(co-?op|internship|intern|full[- ]time|part[- ]time|job|on-campus job|fellowship)$', re.I)
BLOCK = {'p', 'div', 'br', 'tr', 'td', 'th', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'ul', 'ol', 'section', 'hr'}

def iso_date(s):
    s = s.strip().lower().rstrip('.')
    try:
        if re.fullmatch(r'20\d\d-\d\d-\d\d', s): return s
        if '/' in s: m, d, y = s.split('/'); return dt.date(int(y), int(m), int(d)).isoformat()
        mm = MONTHS.index(s[:3]) + 1; dd = int(re.search(r'\s(\d{1,2})', s).group(1)); yy = int(re.search(r'20\d\d', s).group(0))
        return dt.date(yy, mm, dd).isoformat()
    except Exception: return ''

class Tokens(HTMLParser):
    """The email's HTML as a flat stream: ('a', href, text) for links, ('t', text) for text lines."""
    def __init__(self):
        super().__init__(convert_charrefs=True); self.out = []; self.href = None; self.buf = []; self.line = []; self.skip = 0
    def flush_line(self):
        t = ' '.join(' '.join(self.line).split())
        if t: self.out.append(('t', t))
        self.line = []
    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script', 'head', 'title'): self.skip += 1
        if tag in BLOCK: self.flush_line()
        if tag == 'a': self.flush_line(); self.href = dict(attrs).get('href') or ''; self.buf = []
    def handle_endtag(self, tag):
        if tag in ('style', 'script', 'head', 'title'): self.skip = max(0, self.skip - 1)
        if tag == 'a' and self.href is not None:
            self.out.append(('a', self.href, ' '.join(' '.join(self.buf).split()))); self.href = None; self.buf = []
        if tag in BLOCK: self.flush_line()
    def handle_data(self, d):
        if self.skip: return
        (self.buf if self.href is not None else self.line).append(d)

def tokens_of(m):
    part = m.get_body(preferencelist=('html',))
    if part is not None:
        p = Tokens(); p.feed(part.get_content()); p.flush_line(); return p.out
    part = m.get_body(preferencelist=('plain',))
    out = []
    for line in (part.get_content() if part else '').splitlines():
        line = line.strip()
        for u in re.findall(r'https?://\S+', line):
            prev = next((x[1] for x in reversed(out) if x[0] == 't'), '')
            if out and out[-1][0] == 't': out.pop()
            out.append(('a', u.rstrip('>).,'), prev))
        line = re.sub(r'<?https?://\S+', '', line).strip()
        if line: out.append(('t', line))
    return out

SAFELINKS = re.compile(r'^https?://[\w.-]*safelinks\.protection\.outlook\.com/', re.I)

def real_url(href):
    """The posting's own address behind a link in an alert. University mail wraps every link in Outlook Safe Links
    (...safelinks.protection.outlook.com/?url=<the real link>), and NUworks alerts link to
    <host>/students/?jobRedirectUrl=<base64 of /app/jobs/detail/<id>>. Both are undone here, on the text only: nothing
    is fetched."""
    u = (href or '').strip()
    for _ in range(3):
        if not SAFELINKS.match(u): break
        u = urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get('url', [u])[0]
    p = urllib.parse.urlparse(u)
    red = urllib.parse.parse_qs(p.query).get('jobRedirectUrl', [''])[0]
    if red and SYMPLICITY.match(u):
        try: path = base64.b64decode(red + '=' * (-len(red) % 4), validate=False).decode('utf-8')
        except Exception: path = ''
        if re.fullmatch(r'/[\w/-]{1,200}', path): return f'{p.scheme}://{p.netloc}/students{path}'
    return u

def job_id(url):
    for rx in JOB_ID:
        m = rx.search(url)
        if m: return m.group(1)
    return ''

def is_alert(m, senders):
    frm = email.utils.parseaddr(str(m.get('From', '')))[1].lower()
    subj = str(m.get('Subject', ''))
    if any(s.lower() in frm for s in senders): return True
    if re.search(r'nuworks|job alert|search agent|saved search|new (jobs|postings)|latest .{0,80}jobs|job matches', subj, re.I):
        body = m.get_body(preferencelist=('html', 'plain'))
        return bool(body and re.search(r'symplicity\.com', body.get_content(), re.I))
    return False

def parse_alert(m, name=''):
    """Rows for every posting an alert email lists. Only what the email says: title, employer, location, deadline, link."""
    subj = str(m.get('Subject', ''))
    when = email.utils.parsedate_to_datetime(m['Date']) if m.get('Date') else K.now()
    agent = (re.search(r'["“]([^"”]{1,80})["”]', subj) or re.search(r'(?:search agent|saved search|alert)[:\s-]+(.{1,60})$', subj, re.I))
    agent = agent.group(1).strip() if agent else ''
    toks = [(t[0], real_url(t[1]), t[2]) if t[0] == 'a' else t for t in tokens_of(m)]
    jobs = [i for i, t in enumerate(toks) if t[0] == 'a' and SYMPLICITY.match(t[1]) and job_id(t[1]) and t[2] and not NOT_A_TITLE.match(t[2])]
    rows, seen = [], set()
    for n, i in enumerate(jobs):
        _, url, title = toks[i]
        pid = job_id(url)
        if pid in seen: continue
        seen.add(pid)
        stop = jobs[n + 1] if n + 1 < len(jobs) else len(toks)
        lines = [t[1] if t[0] == 't' else t[2] for t in toks[i + 1:stop]][:8]
        company = location = deadline = ''
        for ln in lines:
            lab = LABEL.match(ln); val = LABEL.sub('', ln).strip()
            key = lab.group(1).lower() if lab else ''
            if key in ('employer', 'organization', 'company'): company = company or val
            elif key in ('location', 'city'): location = location or val
            elif key in ('deadline', 'application deadline', 'apply by', 'expires', 'expiration date'): deadline = deadline or iso_date((DATE.search(val) or [''])[0] if DATE.search(val) else '')
            elif not key and not NOT_INFO.match(ln) and not POSITION_TYPE.match(ln):
                if not company and not PLACE.search(ln) and not DATE.search(ln): company = ln
                elif not location and WIDE_PLACE.search(ln): location = ln
                elif not deadline and DATE.search(ln) and re.search(r'deadline|apply by|expires|due', ln, re.I): deadline = iso_date(DATE.search(ln).group(1))
        company = re.sub(r'\s*[|•·-]\s*$', '', company).strip()
        rows.append({
            'source': 'nuworks', 'channel': 'nuworks', 'company': company or '(employer not named in the alert)',
            'title': title, 'location': location, 'url': url, 'posting_id': pid, 'deadline': deadline,
            'posted': f'{when:%Y-%m-%d}',
            'description': (f'From a NUworks job alert email{f" (saved search: {agent})" if agent else ""}, received {when:%Y-%m-%d}. '
                            'The alert lists only the title, employer, location and deadline. The full posting is in NUworks: '
                            'to give the screener the full text, open it in NUworks and save it (Print > Save as PDF, or '
                            'Save Page As) into data/nuworks-import/, then run tools/nuworks_import.py. Apply in NUworks yourself.'),
        })
    return rows

def files_to_read(paths):
    if paths: return paths
    return [f for d in FOLDERS for f in sorted(glob.glob(f'{d}/*.eml'))]

def main(argv):
    K.exit_if_stopped('the NUworks alert reader')
    dry = '--dry-run' in argv; paths = [a for a in argv if not a.startswith('--')]
    if K.SOURCING != 'nuworks+external':
        print(f'NUworks alerts: off (sourcing mode is "{K.SOURCING}"; NUworks is used only in "nuworks+external")'); return 0
    senders = (K.S.get('nuworks') or {}).get('alert_senders') or ['symplicity.com']
    seen = K.load_json(SEEN_FILE, {})
    rows, nalerts = [], 0
    for f in files_to_read(paths):
        try: raw = open(f, 'rb').read()
        except OSError: continue
        h = hashlib.sha1(raw).hexdigest()
        if h in seen and not paths: continue
        m = email.message_from_bytes(raw, policy=email.policy.default)
        if not is_alert(m, senders): continue
        got = parse_alert(m, os.path.basename(f)); nalerts += 1
        rows += got; seen[h] = {'file': os.path.basename(f), 'rows': len(got), 'read_at': f'{K.now():%F %T}'}
    if not rows:
        print(f'NUworks alerts: {nalerts} alert email(s), no new postings');
        if not dry: K.save_json(SEEN_FILE, seen)
        return 0
    if dry:
        print(json.dumps(rows, indent=1)); return 0
    os.makedirs(K.INCOMING, exist_ok=True)
    out = f'{K.INCOMING}/nuworks-alerts-{K.now():%Y%m%d-%H%M%S}.json'
    K.save_json(out, rows); K.save_json(SEEN_FILE, seen)
    K.log('nuworks-alerts', f'{nalerts} alert emails, {len(rows)} postings -> {os.path.basename(out)}')
    print(f'NUworks alerts: {nalerts} alert email(s), {len(rows)} postings written to {os.path.relpath(out, K.STATE)} '
          f'(run pipeline.py import)')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
