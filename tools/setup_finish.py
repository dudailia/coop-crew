# The end of /setup: validates the profile the onboarder wrote, fills jev-job-search's data/profile.json and
# data/policy.json from it (prepare mode, never-apply employers excluded, the visa-type gate from work_auth), and
# prints the full profile for the student to confirm. Changes nothing outside profile/ and vendor/jev/src/data/.
# usage: python3 -I tools/setup_finish.py [--show]
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

JEV_DATA = f'{K.ROOT}/vendor/jev/src/data'

def jev_profile():
    S, C, Pg = K.S, K.S['student'], K.S['program']
    p = K.load_json(f'{JEV_DATA}/profile.json', None) or K.load_json(f'{K.ROOT}/vendor/jev/templates/profile.json', {})
    first, _, last = (C.get('name') or '').partition(' ')
    p.setdefault('name', {}).update({'first': C.get('first_name') or first, 'last': last})
    p['email'] = C.get('email', '')
    digits = re.sub(r'\D', '', C.get('phone', ''))
    p.setdefault('phone', {}).update({'national': digits[-10:], 'countryCode': '+1' if len(digits) in (10, 11) else ''})
    p.setdefault('links', {}).update({'linkedin': C.get('linkedin', ''), 'github': C.get('github', ''), 'website': C.get('portfolio', '')})
    ed = (p.get('education') or [{}])[0]
    ed.update({'school': Pg.get('college', ''), 'field': Pg.get('major', ''), 'minor': Pg.get('minor', '')})
    m = re.match(r'([A-Za-z]+)\s+(\d{4})', Pg.get('graduation', ''))
    if m:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        ed['gradMonth'] = months.index(m.group(1)[:3].lower()) + 1 if m.group(1)[:3].lower() in months else None
        ed['gradYear'] = int(m.group(2))
    if Pg.get('gpa') and Pg.get('show_gpa'):
        ed.setdefault('gpa', {})['cumulative'] = float(Pg['gpa'])
    p['education'] = [ed]
    wa = p.setdefault('workAuthorization', {})
    auth, later, spons = [], [], []
    for country, w in S['work_auth'].items():
        name = {'US': 'United States', 'USA': 'United States', 'UK': 'United Kingdom'}.get(country, country)
        now, fut = (w.get('sponsorship_now') or '').lower().startswith('y'), (w.get('sponsorship_later') or '').lower().startswith('y')
        (spons if now else later if fut else auth).append(name)
        if w.get('visa_type'):
            wa['visaType'] = w['visa_type']; wa['visaTypeNames'] = w.get('visa_type_names', []); wa['neverVisaTypes'] = w.get('never_visa_types', [])
    wa['authorizedCountries'] = auth; wa['authorizedWithSponsorshipLater'] = later
    return p

def jev_policy():
    pol = K.load_json(f'{JEV_DATA}/policy.json', None) or K.load_json(f'{K.ROOT}/vendor/jev/templates/policy.json', {})
    pol['mode'] = 'prepare'
    pol['target'] = min(int(pol.get('target') or 5), K.APPS_PER_DAY)
    pol['excludeEmployers'] = sorted(set(K.never_list() + (K.banned_list() if K.SOURCING == 'self-developed' else [])))
    return pol

def main():
    ok = K.check()
    if os.path.isdir(JEV_DATA):
        K.save_json(f'{JEV_DATA}/profile.json', jev_profile()); K.save_json(f'{JEV_DATA}/policy.json', jev_policy())
        print('jev-job-search: data/profile.json and data/policy.json filled from your profile (prepare mode)')
    else: print('jev-job-search is not installed: applications are prepared as review packs you submit by hand')
    if '--show' in sys.argv:
        print('\n==== profile/settings.json ====\n' + json.dumps({k: v for k, v in K.load_settings().items() if k not in ('audit', 'replies', 'hours')}, indent=1, ensure_ascii=False))
        for f in (K.FACTS_FILE, K.LOCKS_FILE, K.VOICE_FILE):
            print(f'\n==== {os.path.relpath(f, K.STATE)} ====\n' + (K.read(f) or '(missing)'))
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
