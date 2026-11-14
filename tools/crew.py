# Shared settings, paths and safety helpers for every coop-crew tool. Ported from job-agents-kit's tools/kit.py.
# Every value that belongs to one student is read from profile/ (settings.json, facts.md, locks.md, voice.md), never
# written into the code. Python standard library only.
#
# Where state lives: COOP_STATE (a folder) if set, else the repo root. Tests and /demo point COOP_STATE at their own
# folder, so they never touch a real student's files.
#
# usage: python3 -I tools/crew.py --check     validate profile/settings.json and print warnings
import datetime as dt, fcntl, json, os, re, sys, unicodedata, zoneinfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.abspath(os.environ.get('COOP_STATE') or ROOT)
PROFILE, DATA, LOGS, OUT = f'{STATE}/profile', f'{STATE}/data', f'{STATE}/logs', f'{STATE}/out'
ASSETS = f'{STATE}/assets'
SETTINGS_FILE, FACTS_FILE = f'{PROFILE}/settings.json', f'{PROFILE}/facts.md'
LOCKS_FILE, VOICE_FILE = f'{PROFILE}/locks.md', f'{PROFILE}/voice.md'
NEVER_FILE = LOCKS_FILE                       # never-apply employers are a section of locks.md
BANNED_FILE = f'{PROFILE}/banned-employers.md'  # self-developed mode: employers that recruit through NUworks
PIPELINE = f'{DATA}/pipeline.sqlite'
INCOMING = f'{DATA}/incoming'
APPROVE_FILE = f'{STATE}/APPROVE.txt'         # an approval file the student writes by hand: one id per line
NEEDS = f'{STATE}/needs-me.md'
SAMPLE = f'{ROOT}/templates/sample-student'

# ---- kill switch: one file stops every job. ~/STOP-AGENTS (the kit's switch) is honoured too. ----
STOPFILE = f'{STATE}/STOP'
STOPFILES = tuple(dict.fromkeys((STOPFILE, f'{ROOT}/STOP', os.path.expanduser('~/STOP-AGENTS'))))  # the repo's STOP always counts
def stopped(): return any(os.path.exists(p) for p in STOPFILES)
def exit_if_stopped(what='this job'):
    if stopped():
        print(f'STOP: the kill switch is on ({", ".join(p for p in STOPFILES if os.path.exists(p))}); {what} did nothing. /crew-resume turns it off.')
        sys.exit(3)

PAUSE, LOGINF = f'{LOGS}/SENDER-PAUSED', f'{LOGS}/MAIL-LOGIN-ERROR'
for d in (DATA, LOGS, OUT, INCOMING): os.makedirs(d, exist_ok=True)

HARD_MAX_EMAILS = 40  # per day, whatever the settings say

DEFAULTS = {
    'student': {'name': '', 'first_name': '', 'email': '', 'phone': '', 'city': '', 'linkedin': '', 'github': '', 'portfolio': ''},
    'program': {'college': '', 'major': '', 'concentration': '', 'minor': '', 'year': '', 'graduation': '', 'gpa': '', 'show_gpa': False},
    'coop': {'number': '', 'cycle': '', 'length_months': 6, 'start': '', 'end': '', 'summer_extension': False,
             'recruitment_term': False, 'availability': ''},
    'mode': 'external',                       # nuworks+external | external | self-developed
    'work_auth': {},                          # country -> {status, sentence, sponsorship_now, sponsorship_later, visa_type, never_visa_types}
    'targets': {'titles': [], 'title_regex': r'\bco-?op\b|\bintern(ship)?s?\b', 'exclude_regex': r'ph\.?d|summer only|senior|staff|principal',
                'industries': [], 'company_size': [], 'cities': [], 'work_style': ['on-site', 'hybrid', 'remote'],
                'pay_floor_hourly': 0},
    'limits': {'applications_per_day': 5, 'emails_per_day': 10, 'quiet_hours': ['22:00', '07:00'], 'schedule': False},
    'timezone': 'America/New_York',
    'regions': {},
    'default_window': ['08:00', '08:50'],
    'send': {'mode': 'prepare', 'gap_minutes': 4, 'per_run': 3, 'follow_up_working_days': 6, 'late_minutes': 50},
    'mail': {'adapter': 'auto', 'account': '', 'from': '', 'inbox': 'Inbox', 'drafts': 'Drafts', 'health_check': True,
             'stale_inbox_hours': 12},
    'writing': {'max_words': 170, 'banned': ['passionate', 'excited', 'thrilled', 'cutting[- ]edge', 'world[- ]class', 'leverag',
                                             'synerg', 'seamless', 'robust', 'game[- ]chang', 'to whom it may concern', '—'],
                'opt_out_line': "If this isn't relevant, just let me know and I won't follow up.", 'sign_off': 'Best,',
                'salutation_regex': r"^(Hi|Hello|Dear) [A-Z][\w'’-]+,$", 'linkedin_note_max': 300, 'spelling': 'US',
                'followup_max_lines': 2},
    'nuworks': {'enabled': False},
    'audit': {'mailboxes': ['inbox', 'archive'], 'sent_mailboxes': ['sent items', 'sent messages', 'sent', 'sent mail'],
              'my_addresses': [], 'generic_domains': ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com', 'me.com',
                                                      'proton.me', 'protonmail.com', 'northeastern.edu', 'husky.neu.edu'], 'first_days': 45},
    'hours': {'night_start': '00:00', 'sender_end': '23:59'},
    'replies': {},
}

def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out

def have_profile(): return os.path.exists(SETTINGS_FILE)

def load_settings(path=None):
    path = path or SETTINGS_FILE
    if not os.path.exists(path):
        return _merge(DEFAULTS, {})
    raw = json.load(open(path, encoding='utf-8'))
    return _merge(DEFAULTS, {k: v for k, v in raw.items() if not k.startswith('_')})

S = load_settings()
C = dict(S['student'], availability=S['coop'].get('availability', ''), program='co-op',  # kit name: the candidate
         situation=f"a {S['program'].get('major') or 'university'} student at {S['program'].get('college') or 'university'} "
                   f"looking for a {S['coop'].get('cycle') or ''} co-op {S['coop'].get('availability') or ''}".replace('  ', ' ').strip())
W = S['writing']
try: TZ = zoneinfo.ZoneInfo(S['timezone'])
except Exception: TZ = zoneinfo.ZoneInfo('America/New_York')
MODE = S['send']['mode'] if S['send']['mode'] in ('prepare', 'send') else 'prepare'  # anything unknown means prepare
SOURCING = S['mode'] if S['mode'] in ('nuworks+external', 'external', 'self-developed') else 'external'
APPS_PER_DAY = max(0, int(S['limits'].get('applications_per_day', 5)))
EMAILS_PER_DAY = max(0, min(int(S['limits'].get('emails_per_day', 10)), HARD_MAX_EMAILS))

def hm(s): h, m = map(int, s.split(':')); return dt.time(h, m)
NIGHT_START, SENDER_END = hm(S['hours']['night_start']), hm(S['hours']['sender_end'])
def now(): return dt.datetime.now(TZ)
def in_hours(t, start, end):
    t = t.time() if isinstance(t, dt.datetime) else t
    return start <= t < end if start <= end else (t >= start or t < end)
def sender_hours(t=None): return in_hours((t or now()).astimezone(TZ), NIGHT_START, SENDER_END)
def quiet(t=None):
    q = S['limits'].get('quiet_hours') or []
    return len(q) == 2 and in_hours((t or now()).astimezone(TZ), hm(q[0]), hm(q[1]))

# ---- regions and send windows: weekdays, inside the recipient's local window ----
def region(x):
    r = x.get('region', '') if isinstance(x, dict) else x
    return S['regions'].get(r, {})
def tz_of(x): return zoneinfo.ZoneInfo((x.get('tz') if isinstance(x, dict) else None) or region(x).get('tz') or S['timezone'])
def window_of(x):
    w = region(x).get('window') or S['default_window']
    return hm(w[0]), hm(w[1])
def slot_ok(t, x):
    lt = t.astimezone(tz_of(x)); a, b = window_of(x)
    return lt.weekday() < 5 and a <= lt.time() <= b and sender_hours(t)
def add_working_days(d, n):
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5: n -= 1
    return d

# ---- employer matching: never-apply (locks.md) and, in self-developed mode, the banned list ----
def fold(s):
    """Lower case, accents removed, '&' read as 'and'."""
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return s.replace('&', ' and ')
STRIP = r'\b(ltd|limited|plc|inc|incorporated|llc|l\.l\.c|lda|sa|co|corp|corporation|company|group|holdings?|technologies|technology|labs?|the)\b'
def norm_name(s): return re.sub(r'[^\w ]', ' ', re.sub(STRIP, ' ', re.sub(r'[.,\'’]', '', fold(s)))).split()
SUFFIX = {'bank', 'us', 'usa', 'america', 'americas', 'north', 'international', 'global', 'inc', 'payments', 'capital', 'markets',
          'management', 'investments', 'securities', 'financial', 'finance', 'services', 'partners', 'ventures', 'software', 'ai',
          'health', 'healthcare', 'systems', 'solutions', 'research', 'boston', 'nyc', 'and', 'company', 'co', 'hq'}

def list_names(path, section=None):
    """Names from '- Name' or '- Name | note' lines. With section, only lines under a heading containing that word."""
    out = []
    if not os.path.exists(path): return out
    cur = ''
    for l in open(path, encoding='utf-8'):
        h = re.match(r'^#+\s*(.+)$', l)
        if h: cur = h.group(1).lower(); continue
        if section and section not in cur: continue
        m = re.match(r'^\s*[-*]\s+(.+)$', l)
        if not m: continue
        if re.search(r'\[UNBANNED', m.group(1), re.I): continue
        n = m.group(1).split('|')[0].split('\t')[0].strip()
        if n and not n.startswith('('): out.append(n)
    return out

def never_list(): return list_names(LOCKS_FILE, 'never')
def banned_list(): return list_names(BANNED_FILE)
NEVER = never_list()

def matches(company, listed):
    """True when company is the listed employer under any common spelling: case, accents, punctuation, legal suffixes,
    spaces ('Acme Robotics' = 'AcmeRobotics' = 'ACME-Robotics, Inc.'), generic words on either side ('Acme Robotics Boston'),
    or a name in brackets ('Foo (Acme Robotics)'). Whole names only: 'Ramp' does not match 'Onramp'."""
    names = [re.sub(r'\s*\(.*?\)\s*', ' ', company)] + re.findall(r'\((.*?)\)', company)
    nt = norm_name(listed)
    if not nt: return False
    for toks in (norm_name(x) for x in names):
        if not toks: continue
        if toks == nt or ''.join(toks) == ''.join(nt): return True
        if toks[:len(nt)] == nt and all(t in SUFFIX for t in toks[len(nt):]): return True
        if toks[-len(nt):] == nt and all(t in SUFFIX for t in toks[:-len(nt)]): return True
        # joined spelling against a split one, with generic words around it: 'AcmeRobotics Boston' vs 'Acme Robotics'
        joined = ''.join(nt)
        for i in range(len(toks)):
            for j in range(i + 1, len(toks) + 1):
                if ''.join(toks[i:j]) == joined and all(t in SUFFIX for t in toks[:i] + toks[j:]): return True
    return False

def blocked(company):
    """The never-apply name (locks.md) that covers this company, or None. In self-developed mode the banned list counts too."""
    lists = never_list() + (banned_list() if SOURCING == 'self-developed' else [])
    for listed in lists:
        if matches(company or '', listed): return listed
    return None

# ---- Mail helpers kept from the kit (macOS only) ----
FRONT = 'tell application "System Events" to get name of first application process whose frontmost is true'
RESTORE = """on run argv
set f to item 1 of argv
tell application "System Events"
  if f is not "Mail" and (exists process "Mail") then set visible of process "Mail" to false
  if f is not "" and f is not "Mail" then
    try
      set frontmost of process f to true
    end try
  end if
end tell
end run"""
def sender_line():
    return S['mail'].get('from') or (f"{C['name']} <{C['email']}>" if C.get('email') else '')
def mail_adapter():
    """'mac-mail' on macOS with an account set, else 'eml' (drafts written as .eml files the student sends by hand)."""
    a = os.environ.get('COOP_MAIL_ADAPTER') or S['mail'].get('adapter', 'auto')
    if a == 'auto':
        return 'mac-mail' if sys.platform == 'darwin' and S['mail'].get('account') else 'eml'
    return a

# ---- files ----
def load_json(p, d):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d
def save_json(p, v):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(v, open(p + '.tmp', 'w', encoding='utf-8'), ensure_ascii=False, indent=1); os.replace(p + '.tmp', p)
def read(p, d=''):
    try: return open(p, encoding='utf-8').read()
    except Exception: return d
def fill(template, **extra):
    vals = {**C, 'sign_off': W['sign_off'], **extra}
    return re.sub(r'\{(\w+)\}', lambda m: str(vals.get(m.group(1), m.group(0))), template)
def emails():  # kit name: the planned emails, now kept in the pipeline
    import pipeline
    return pipeline.emails()

def log(name, msg):
    with open(f'{LOGS}/{name}.log', 'a', encoding='utf-8') as f: f.write(f'{now():%F %T} {msg}\n')

# ---- one lock: agents that touch Mail or the browser never run at the same time ----
class Lock:
    """with Lock('mail'): ...  Holds logs/night.lock. Raises RuntimeError if another Mail or browser job holds it."""
    def __init__(self, who, wait=False): self.who, self.wait = who, wait
    def __enter__(self):
        busy = f'{LOGS}/nuworks.busy'  # the NUworks server (Node) marks its open browser here
        if os.path.exists(busy):
            try: os.kill(int(open(busy).read().strip() or 0), 0); raise RuntimeError('the NUworks reader has a browser open; try again when it ends')
            except (ProcessLookupError, ValueError): os.remove(busy)
        self.f = open(f'{LOGS}/night.lock', 'a+')
        try: fcntl.flock(self.f, fcntl.LOCK_EX | (0 if self.wait else fcntl.LOCK_NB))
        except OSError:
            self.f.seek(0); held = self.f.read().strip()
            raise RuntimeError(f'another Mail or browser job is running ({held or "unknown"}); try again when it ends')
        self.f.seek(0); self.f.truncate(); self.f.write(f'{self.who} pid {os.getpid()} since {now():%H:%M:%S}'); self.f.flush()
        return self
    def __exit__(self, *a):
        self.f.seek(0); self.f.truncate(); fcntl.flock(self.f, fcntl.LOCK_UN); self.f.close()

def check():
    warn = []
    if not have_profile(): warn.append(f'{SETTINGS_FILE} does not exist: run /setup (or /demo, which uses the sample student)')
    for k in ('name', 'email'):
        if have_profile() and not C.get(k): warn.append(f'student.{k} is empty')
    if have_profile() and not S['coop'].get('start'): warn.append('coop.start is empty')
    for c, w in S['work_auth'].items():
        if not w.get('sentence'): warn.append(f'work_auth.{c}.sentence is empty: forms and emails for {c} will be held')
    if have_profile() and not os.path.exists(FACTS_FILE): warn.append('profile/facts.md is missing: no claim can be made')
    for name, r in S['regions'].items():
        try: zoneinfo.ZoneInfo(r.get('tz', ''))
        except Exception: warn.append(f'region {name}: unknown time zone "{r.get("tz")}"')
    if int(S['limits'].get('emails_per_day', 10)) > HARD_MAX_EMAILS: warn.append(f'limits.emails_per_day is above the hard maximum; {HARD_MAX_EMAILS} is used')
    if SOURCING == 'self-developed' and not os.path.exists(BANNED_FILE): warn.append('self-developed mode but profile/banned-employers.md is missing')
    print(f'state: {STATE}\nsourcing mode: {SOURCING}; send mode: {MODE} (nothing is sent or submitted without /approve)')
    print(f'never-apply: {len(never_list())} names; banned (self-developed): {len(banned_list())}; regions: {", ".join(S["regions"]) or "none"}')
    print(f'limits: {APPS_PER_DAY} applications/day, {EMAILS_PER_DAY} emails/day; mail adapter: {mail_adapter()}')
    print('\n'.join(f'warning: {w}' for w in warn) or 'no warnings')
    return not warn

if __name__ == '__main__':
    sys.exit(0 if check() else 1)
