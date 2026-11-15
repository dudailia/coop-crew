# Manual NUworks import: postings the student saved from NUworks themselves. With the job-alert emails
# (tools/nuworks_alerts.py) this is the default NUworks path: the crew never loads a NUworks page.
# The student opens a posting in NUworks and saves it into data/nuworks-import/ as a PDF (Print > Save as PDF) or as a web
# page (Save Page As, .html). This reads each file once, local only:
#   .pdf   text by pdftotext (poppler)          .html/.htm  the page's text    .txt  as is
# (Alert emails dropped there as .eml are read by tools/nuworks_alerts.py, which also looks in this folder.)
# and writes data/incoming/nuworks-import-<time>.json (source "nuworks", channel nuworks) for `pipeline.py import`.
# When the posting is already in the pipeline (from an alert email), its full text goes to out/<id>/posting.md instead
# of a second row, so the screener reads the whole posting. Files are never moved, changed or uploaded.
# Runs only in sourcing mode "nuworks+external".
# usage: python3 -I tools/nuworks_import.py [file ...] [--dry-run]
import glob, hashlib, json, os, re, shutil, subprocess, sys
from html.parser import HTMLParser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P, nuworks_alerts as A

FOLDER = f'{K.DATA}/nuworks-import'
SEEN_FILE = f'{K.LOGS}/nuworks-import-seen.json'
KINDS = ('.pdf', '.html', '.htm', '.txt')
LABELS = {
    'company': r'employer|organization|company',
    'location': r'location|city|job location',
    'deadline': r'application deadline|deadline|expiration date|apply by|expires',
    'position_type': r'position type|job type',
    'pay': r'salary|pay|compensation|hourly rate',
    'posting_id': r'job id|position id|posting id',
    'title': r'job title|position title|title',
}
SITE_SUFFIX = re.compile(r'\s*[|–—-]\s*(nuworks|symplicity|northeastern).*$', re.I)

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.lines = []; self.cur = []; self.skip = 0; self.h1 = ''; self.in_h1 = False
        self.title = ''; self.in_title = False; self.urls = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style', 'noscript'): self.skip += 1
        if tag == 'title': self.in_title = True
        if tag == 'h1': self.in_h1 = True
        for k in ('href', 'content'):
            if a.get(k) and A.SYMPLICITY.match(a[k]): self.urls.append(a[k])
        if tag in A.BLOCK or tag in ('dt', 'dd', 'label', 'strong', 'b'): self.flush()
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'): self.skip = max(0, self.skip - 1)
        if tag == 'title': self.in_title = False
        if tag == 'h1': self.in_h1 = False
        if tag in A.BLOCK or tag in ('dt', 'dd', 'label', 'strong', 'b'): self.flush()
    def handle_comment(self, data):
        m = re.search(r'saved from url=\(\d+\)(\S+)', data)   # browsers' "Save Page As" mark
        if m and A.SYMPLICITY.match(m.group(1)): self.urls.insert(0, m.group(1))
    def handle_data(self, d):
        if self.skip: return
        if self.in_title: self.title += d
        if self.in_h1: self.h1 += d
        self.cur.append(d)
    def flush(self):
        t = ' '.join(' '.join(self.cur).split())
        if t: self.lines.append(t)
        self.cur = []

def text_of(path):
    """(lines, title hint, urls) from one saved file; ([], '', []) when it cannot be read."""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        exe = shutil.which('pdftotext')
        if not exe: print(f'skipped {os.path.basename(path)}: pdftotext is not installed (brew install poppler)'); return [], '', []
        r = subprocess.run([exe, '-layout', '-enc', 'UTF-8', path, '-'], capture_output=True, text=True, timeout=60)
        t = r.stdout
        return [ln.strip() for ln in t.splitlines()], '', re.findall(r'https?://[\w.-]*symplicity\.com/\S+', t)
    raw = open(path, 'rb').read().decode('utf-8', 'replace')
    if ext in ('.html', '.htm'):
        p = Page(); p.feed(raw); p.flush()
        return p.lines, (p.h1 or SITE_SUFFIX.sub('', p.title)).strip(), p.urls
    return [ln.strip() for ln in raw.splitlines()], '', re.findall(r'https?://[\w.-]*symplicity\.com/\S+', raw)

def fields(lines):
    """Label: value pairs, on one line ("Employer: X") or a label line then its value line."""
    out = {}
    for i, ln in enumerate(lines):
        for key, rx in LABELS.items():
            if key in out: continue
            m = re.match(rf'^({rx})\s*[:*]?\s*(.*)$', ln, re.I)
            if not m: continue
            val = m.group(2).strip(' :*')
            if not val and ln.strip().rstrip(':*').strip().lower() == m.group(1).lower():
                val = next((x for x in lines[i + 1:i + 3] if x.strip()), '').strip()
            if val and len(val) < 200: out[key] = val; break
    return out

def row_of(path):
    lines, hint, urls = text_of(path)
    lines = [ln for ln in lines if ln]
    if not lines: return None
    f = fields(lines)
    url = next((u for u in urls if A.job_id(u)), urls[0] if urls else '')
    pid = f.get('posting_id') or A.job_id(url) or ''
    body = '\n'.join(lines)
    title = SITE_SUFFIX.sub('', f.get('title') or hint or lines[0]).strip()
    dl = A.DATE.search(f.get('deadline', ''))
    return {
        'source': 'nuworks', 'channel': 'nuworks', 'company': f.get('company') or '(employer not found in the saved file)',
        'title': title[:200], 'location': f.get('location', ''), 'url': url,
        'posting_id': pid or 'file-' + hashlib.sha1(body.encode()).hexdigest()[:10],
        'deadline': A.iso_date(dl.group(1)) if dl else '', 'pay': f.get('pay', ''),
        'description': f'(Saved from NUworks by the student: {os.path.basename(path)})\n\n' + body[:20000],
    }

def main(argv):
    K.exit_if_stopped('the NUworks import')
    dry = '--dry-run' in argv; paths = [a for a in argv if not a.startswith('--')]
    if K.SOURCING != 'nuworks+external':
        print(f'NUworks import: off (sourcing mode is "{K.SOURCING}"; NUworks is used only in "nuworks+external")'); return 0
    files = paths or sorted(f for f in glob.glob(f'{FOLDER}/*') if f.lower().endswith(KINDS))
    seen = K.load_json(SEEN_FILE, {}); rows, filled, n = [], [], 0
    c = P.db()
    for f in files:
        try: h = hashlib.sha1(open(f, 'rb').read()).hexdigest()
        except OSError: continue
        if h in seen and not paths: continue
        n += 1
        r = row_of(f)
        if not r: print(f'skipped {os.path.basename(f)}: no text found'); continue
        old = c.execute("select id from roles where source = 'nuworks' and posting_id = ?", (r['posting_id'],)).fetchone() if r['posting_id'] else None
        if old and not dry:
            os.makedirs(f'{K.OUT}/{old["id"]}', exist_ok=True)
            open(f'{K.OUT}/{old["id"]}/posting.md', 'w', encoding='utf-8').write(
                f"# {r['company']}: {r['title']}\n\nSource: nuworks (saved by the student)\nURL: {r['url']}\nDeadline: {r['deadline']}\n\n{r['description']}\n")
            filled.append(old['id'])
        else: rows.append(r)
        seen[h] = {'file': os.path.basename(f), 'role': old['id'] if old else r['posting_id']}
    if dry: print(json.dumps(rows, indent=1)); return 0
    if rows:
        os.makedirs(K.INCOMING, exist_ok=True)
        out = f'{K.INCOMING}/nuworks-import-{K.now():%Y%m%d-%H%M%S}.json'; K.save_json(out, rows)
        print(f'NUworks import: {len(rows)} posting(s) written to {os.path.relpath(out, K.STATE)} (run pipeline.py import)')
    if filled: print(f'NUworks import: full text added to {len(filled)} role(s) already in the pipeline: {", ".join(filled)}')
    if not rows and not filled: print(f'NUworks import: {n} new file(s) in {os.path.relpath(FOLDER, K.STATE)}, nothing to import')
    K.save_json(SEEN_FILE, seen)
    if rows or filled: K.log('nuworks-import', f'{len(rows)} new rows, {len(filled)} filled from {n} files')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
