# The screener's hard rules, in code, run before the screener agent judges anything. They only ever DQ (or HOLD with a
# question); they never KEEP a role, except with --offline (the /demo and test stand-in for the screener agent).
#  - employer blocked by locks.md (never-apply) or, in self-developed mode, the banned list   -> DQ
#  - title outside targets.title_regex, or inside targets.exclude_regex                       -> DQ
#  - deadline already passed                                                                   -> DQ
#  - posting requires citizenship or a clearance, and the student is not a citizen there       -> DQ (or HOLD if unclear)
#  - posting asks for sponsorship-free work and the student needs sponsorship there            -> HOLD with the question
# usage: python3 -I tools/screen_rules.py [--offline] [--limit N]
import datetime as dt, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P

CITIZEN = re.compile(r'(u\.?s\.? citizen(ship)? (is )?required|must be a u\.?s\.? citizen|security clearance|itar|'
                     r'only (u\.?s\.? )?citizens|citizens? (or|and) (permanent residents?|green card)|'
                     r'export[- ]controlled)', re.I)
NO_SPONSOR = re.compile(r'(will not|won\'t|does not|unable to|cannot|not able to) (provide |offer )?(visa )?sponsor|'
                        r'without (the need for )?(current or future )?(visa )?sponsorship|no sponsorship', re.I)
SUMMER_ONLY = re.compile(r'\bsummer (20\d\d )?(intern|internship|only)\b|10[- ]week|12[- ]week', re.I)

def us_auth():
    for c, w in K.S['work_auth'].items():
        if c.lower() in ('us', 'usa', 'united states'): return w
    return {}

US_HINT = re.compile(r'\b(united states|usa|u\.s\.|us remote|remote,? us|AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|'
                     r'MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b|california|washington|new york|'
                     r'massachusetts|texas|boston|seattle|austin|chicago|san francisco|mountain view|bellevue', re.I)
COUNTRY_OF = {'US': US_HINT}

def place_ok(loc):
    """(ok, why). A role passes when one of its places is a target city, or remote in a country the student can work in."""
    cities = [c.lower() for c in K.S['targets'].get('cities', []) if c]
    if not loc or not cities: return True, ''
    parts = [p.strip() for p in re.split(r';|\||/| or ', loc) if p.strip()]
    can = [c.upper() for c, w in K.S['work_auth'].items() if w.get('status')]
    for p in parts:
        pl = p.lower()
        in_country = any(c in COUNTRY_OF and COUNTRY_OF[c].search(p) for c in can)
        if any(c != 'remote' and c in pl for c in cities): return True, ''
        if 'remote' in pl and 'remote' in cities and (in_country or not re.search(r'\b[A-Z][a-z]+\b', p.replace('Remote', '').replace('remote', ''))):
            return True, ''
    if any(any(c in COUNTRY_OF and COUNTRY_OF[c].search(p) for c in can) for p in parts):
        return False, f'location "{loc}" is not one of the target cities ({", ".join(K.S["targets"]["cities"])})'
    return False, f'location "{loc}" is outside the countries the student can work in ({", ".join(can) or "none in the profile"})'

def judge(r, text, offline=False):
    T = K.S['targets']; title = r['title']
    b = K.blocked(r['company'])
    if b: return 'DQ', f'employer covered by "{b}" ({"banned list" if b in K.banned_list() else "never-apply in locks.md"})', ''
    if T.get('title_regex') and not re.search(T['title_regex'], title, re.I) and not re.search(T['title_regex'], text[:600], re.I):
        return 'DQ', f'title "{title}" is not a co-op or target role', ''
    if T.get('exclude_regex') and re.search(T['exclude_regex'], title, re.I): return 'DQ', f'title "{title}" is excluded by the targets', ''
    if r['deadline']:
        try:
            if dt.date.fromisoformat(r['deadline'][:10]) < K.now().date(): return 'DQ', f'deadline {r["deadline"]} has passed', ''
        except ValueError: pass
    ok, why = place_ok(r['location'])
    if not ok: return 'DQ', why, ''
    w = us_auth(); status = (w.get('status') or '').lower()
    if CITIZEN.search(text) and status and 'citizen' not in status:
        return 'DQ', 'the posting requires US citizenship or a clearance; the student is ' + w.get('status', ''), ''
    if NO_SPONSOR.search(text) and (w.get('sponsorship_now', '').lower().startswith('y') or w.get('sponsorship_later', '').lower().startswith('y')):
        q = (f'{r["company"]} says it will not sponsor visas. Your profile says sponsorship now: {w.get("sponsorship_now")}, '
             f'later: {w.get("sponsorship_later")}. With CPT for the co-op, do you want to apply anyway?')
        return 'HOLD', 'posting says no sponsorship; the student\'s status may need it later', q
    cycle = (K.S['coop'].get('cycle') or '').lower()
    if cycle and cycle != 'summer' and re.search(r'\bsummer\b', title, re.I) and not re.search(r'co-?op|fall|spring|winter|6[- ]month|six[- ]month', title, re.I):
        return 'DQ', f'summer internship (by its title); the student\'s co-op is a {cycle} cycle', ''
    if cycle and cycle != 'summer' and SUMMER_ONLY.search(title + ' ' + text[:1500]) and not re.search(r'co-?op|fall|spring|winter|6[- ]month|six[- ]month', title + ' ' + text[:1500], re.I):
        return 'DQ', f'summer-only internship; the student\'s co-op is a {cycle} cycle', ''
    if offline: return 'KEEP', 'offline rules: title, dates, eligibility and locks pass (no agent judgment in offline mode)', ''
    return None, '', ''

def run(offline=False, limit=None):
    K.exit_if_stopped('the screener rules')
    c = P.db(); n = {'KEEP': 0, 'HOLD': 0, 'DQ': 0, 'left': 0}
    rows = c.execute("select * from roles where status = 'new' order by found_at").fetchall()
    for r in rows[:limit] if limit else rows:
        K.exit_if_stopped('the screener rules')
        text = K.read(f'{K.OUT}/{r["id"]}/posting.md')
        v, why, q = judge(r, text, offline)
        if not v: n['left'] += 1; continue
        P.verdict(c, r['id'], v, why, q); n[v] += 1
    c.commit()
    print(f"rules: {n['DQ']} DQ, {n['HOLD']} HOLD, {n['KEEP']} KEEP, {n['left']} left for the screener agent")
    return n

if __name__ == '__main__':
    a = sys.argv
    run('--offline' in a, int(a[a.index('--limit') + 1]) if '--limit' in a else None)
