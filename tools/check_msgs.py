# The message checker. Holds every planned email and LinkedIn note (pipeline), and every outgoing file in out/<role>/
# (resume.md, cover.md, answers.md), to the student's writing rules and to the facts rule: every number and every name
# in outgoing text must appear in profile/facts.md, the role's posting or brief, or the profile settings. It fixes nothing;
# it lists what breaks a rule. Ported from job-agents-kit's check_msgs.py, with the facts check added.
# usage: python3 -I tools/check_msgs.py                       everything; ends with "problems: N"
#        python3 -I tools/check_msgs.py --file F [--role ID]  one text file (exit 1 on any problem)
#        python3 -I tools/check_msgs.py --text "..." [--role ID]
import datetime as dt, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K
W, C, S = K.W, K.C, K.S
US_SPELL = [r'\boptimiz', r'\borganiz', r'\bcategoriz', r'\bprioritiz', r'\brecogniz', r'\bspecializ', r'\bnormaliz', r'\bcenter\b',
            r'\bcolor\b', r'\bbehavior', r'\banalyz', r'\bmodeling\b', r'\bfavor', r'\blicense\b', r'\bauthoriz']
UK_SPELL = [r'\boptimis', r'\borganis', r'\bcategoris', r'\bprioritis', r'\brecognis', r'\bspecialis(e|ed|es|ing|ation)', r'\bnormalis',
            r'\bcentre\b', r'\bcolour', r'\bbehaviour', r'\banalys(e|ed|ing)\b', r'\bmodelling\b', r'\bfavour', r'\blicence\b', r'\bauthoris']
INBOX_WORDS = {'opportunities', 'careers', 'career', 'team', 'hello', 'info', 'recruitment', 'hiring', 'jobs', 'talent', 'people', 'hr',
               'office', 'contact', 'enquiries'}
AI_OWN_WORK = re.compile(r'(without|no) (the )?(use|help|assistance) of (ai|artificial intelligence|chatgpt|generative)|'
                         r'(own|original) (work|words).{0,60}(ai|artificial intelligence|chatgpt|generative)|'
                         r'(ai|chatgpt|generative ai).{0,60}(not|never) (used|allowed|permitted)|written (entirely )?by (you|yourself)', re.I)

# Words that may start a capitalised run without being a name: sentence openers, days, months, titles, résumé headings.
COMMON = set('''i i'm i've i'd i'll a an the this that these those my our your their his her its we you they he she it
hi hello dear thanks thank best kind regards sincerely cheers yours warm and or but so if when while as at in on of for to from
with by about after before during since until over under into onto per via also then there here what which who why how
monday tuesday wednesday thursday friday saturday sunday january february march april may june july august september october
november december jan feb mar apr jun jul aug sep sept oct nov dec spring summer fall autumn winter co-op coop
summary skills experience projects education awards languages interests certifications coursework relevant technical
mr ms mrs dr prof re fw fwd ps please let would could should will can do does did is are was were be been being have has had
not no yes one two three four five six seven eight nine ten first second third last next new each every all any some most more
built led worked work working designed developed created wrote ran managed analyzed analysed improved reduced increased
helped used using made making taught tutored organized organised presented researched implemented automated
gpa usa us u.s. uk eu ai ml api apis sql pdf llm etc e.g i.e am pm est edt et pt
expected present current today now team role
'''.split())

def corpus_for(role_id=None):
    """All text a claim may come from: facts.md, the settings, and for a role its posting and brief."""
    parts = [K.read(K.FACTS_FILE), json.dumps(S, ensure_ascii=False)]
    if role_id:
        for f in ('posting.md', 'brief.md', 'person.md'):
            parts.append(K.read(f'{K.OUT}/{role_id}/{f}'))
        try:
            import pipeline as P
            r = P.db().execute('select * from roles where id = ?', (role_id,)).fetchone()
            if r: parts.append(' '.join(str(v) for v in dict(r).values()))
        except Exception: pass
    return K.fold('\n'.join(parts))

def numbers(text):
    """Every number as written: 40%, 1,200+, 3x, $25, 2027, 4.0. Dates like 2027-01-05 count as their parts."""
    return [m.group(0) for m in re.finditer(r'(?<![\w.])\$?\d[\d,]*(?:\.\d+)?\s?(?:%|\+|x\b|×|k\b|m\b)?', text)]

def norm_num(n): return re.sub(r'[\s,$]', '', n).rstrip('.').lower()

def names(text):
    """Capitalised words and runs that read as names: 'Google', 'Goldman Sachs', 'GraphQL'. A lone capitalised word
    at the start of a sentence or line is skipped unless it is not a common word."""
    out = []
    for line in text.splitlines():
        for sent in re.split(r'(?<=[.!?:;])\s+|^\s*[-*•]\s*', line):
            toks = re.findall(r"[A-Za-z][\w'’&.+#-]*", sent)
            i = 0
            while i < len(toks):
                t = toks[i]
                if t[0].isupper() or re.search(r'[A-Z]', t[1:]):
                    j = i
                    while j + 1 < len(toks) and (toks[j + 1][0].isupper() or toks[j + 1] in ('of', 'and', '&')): j += 1
                    run = toks[i:j + 1]; start = i == 0
                    def common(w): return w.lower().strip(".'’,") in COMMON or w in ('of', 'and', '&')
                    while run and common(run[0]): run.pop(0); start = False
                    while run and common(run[-1]): run.pop()
                    phrase = ' '.join(run).strip(".'’-,")
                    inner_caps = bool(re.search(r'[A-Z]', phrase[1:].split(' ')[0])) if phrase else False
                    # A lone capitalised word opening a sentence is usually just a word ("Builds", "Shipped"): skip it
                    # unless it is written like a name (GitHub, AWS). A name used mid-sentence is caught there.
                    if phrase and not (start and len(run) == 1 and not inner_caps):
                        out.append(phrase)
                    i = j + 1
                else: i += 1
    return out

def unknown_claims(text, role_id=None, extra=''):
    """Numbers and names in text that appear nowhere in the facts corpus. extra: text that may also be used (recipient)."""
    corpus = corpus_for(role_id) + '\n' + K.fold(extra)
    known = {norm_num(n) for n in numbers(corpus)}
    bases = {re.sub(r'[%+x×km]$', '', k) for k in known} | set(re.findall(r'\d+', corpus))
    bad = []
    for n in numbers(text):
        k = norm_num(n)
        if not k or not re.search(r'\d', k): continue
        base = re.sub(r'[%+x×km]$', '', k)
        # A number with a mark (40%, 40+, 3x) must appear with that mark; a plain number must appear as a number.
        if (k != base and k not in known) or (k == base and base not in bases):
            bad.append(f'number "{n.strip()}" is not in facts.md or the posting')
    for nm in names(text):
        words = [w for w in re.findall(r"[a-z0-9+#]+", K.fold(nm)) if w not in COMMON]
        if not words: continue
        if re.search(r'(?<![a-z0-9])' + re.escape(K.fold(nm)) + r'(?![a-z0-9])', corpus): continue
        if all(re.search(r'(?<![a-z0-9])' + re.escape(w) + r'(?![a-z0-9])', corpus) for w in words): continue
        bad.append(f'name "{nm}" is not in facts.md or the posting')
    return sorted(set(bad), key=bad.index)

def style(t, nm):
    errs = []
    for p in W['banned']:
        if re.search(p, t, re.I): errs.append(f'{nm}: banned /{p}/')
    if '—' in t and not any(p == '—' for p in W['banned']): errs.append(f'{nm}: em dash')
    sp = W.get('spelling', 'US')
    for p in (US_SPELL if sp == 'UK' else UK_SPELL if sp == 'US' else []):
        if re.search(p, t, re.I): errs.append(f"{nm}: {'US' if sp == 'UK' else 'UK'} spelling /{p}/")
    return errs

def words(s): return len(re.findall(r"[\w'’.-]+", s.split('\n\n' + W['sign_off'])[0]))

def auth_sentences():
    return {c: v.get('sentence', '') for c, v in S['work_auth'].items() if v.get('sentence') and v.get('include_in_email')}

def check_email(x):
    errs, b, fu = [], x.get('body', ''), x.get('followup_body', '')
    for k in ('id', 'company', 'to', 'region', 'subject', 'body'):
        if not x.get(k): errs.append(f'missing "{k}"')
    reg = x.get('region', '')
    if reg and reg not in S['regions']: errs.append(f'region "{reg}" is not in settings.regions')
    if x.get('to') and not re.match(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', x['to'], re.I): errs.append(f'address "{x["to"]}" does not look like an email address')
    if x.get('to') and not x.get('source_url'): errs.append('no source_url: an address must be published on a page you can name')
    if K.blocked(x.get('company', '')): errs.append(f'employer is blocked ({K.blocked(x["company"])})')
    if x.get('slot'):
        try:
            t = dt.datetime.fromisoformat(x['slot']).replace(tzinfo=K.tz_of(x))
            if not K.slot_ok(t, x): errs.append(f'slot {x["slot"]} is outside the {reg} window or on a weekend')
        except ValueError: errs.append(f'slot "{x["slot"]}" is not YYYY-MM-DDTHH:MM')
    errs += style(b, 'body') + style(fu, 'follow-up') + style(x.get('subject', ''), 'subject')
    if W.get('max_words') and words(b) > W['max_words']: errs.append(f'{words(b)} words (>{W["max_words"]})')
    country = K.region(x).get('country', '')
    A = auth_sentences()
    if A.get(country) and A[country] not in b: errs.append(f'missing the {country} work-authorization sentence, word for word')
    for cn, s in A.items():
        if cn != country and s != A.get(country) and s in b: errs.append(f'work-authorization sentence for {cn} in an email to {country or reg}')
    if W.get('opt_out_line') and W['opt_out_line'] not in b: errs.append('missing the opt-out line (writing.opt_out_line)')
    first = b.split('\n')[0]
    if W.get('salutation_regex') and not re.match(W['salutation_regex'], first): errs.append(f'salutation "{first[:40]}"')
    nm = re.match(r"^\w+ ([A-Z][\w'’-]+),$", first)
    if nm and nm.group(1).lower() in INBOX_WORDS: errs.append(f'salutation "{first}" is an inbox word, not a name')
    if nm and x.get('person') and nm.group(1) not in x['person']: errs.append(f'salutation "{first}" does not match the recipient "{x["person"][:40]}"')
    sign = f"{W['sign_off']}\n{C['name']}" if C.get('name') else W['sign_off']
    if not b.rstrip().endswith(sign): errs.append(f'body does not end with the sign-off "{sign}"')
    if fu:
        if not fu.rstrip().endswith(sign): errs.append('follow-up does not end with the sign-off')
        lines = [l for l in fu.split('\n') if l.strip() and l.strip() not in (W['sign_off'], C.get('name')) and l.strip() != first]
        if len(lines) > W['followup_max_lines']: errs.append(f'follow-up longer than {W["followup_max_lines"]} lines')
        if not x.get('followup_subject'): errs.append('follow-up has no subject')
    extra = ' '.join([x.get('company', ''), x.get('person', ''), x.get('to', ''), x.get('subject', '')])
    errs += unknown_claims(b + '\n' + fu, x.get('role_id') or None, extra)
    return errs

def check_note(x):
    n = x.get('body', '') or x.get('note', '')
    errs = style(n, 'note')
    if len(n) > W['linkedin_note_max']: errs.append(f"note {len(n)} characters (>{W['linkedin_note_max']})")
    if K.blocked(x.get('company', '')): errs.append(f'employer is blocked ({K.blocked(x["company"])})')
    if not re.match(r'^https://(www\.)?linkedin\.com/in/', x.get('profile_url', '')): errs.append('no verified LinkedIn profile URL')
    errs += unknown_claims(n, x.get('role_id') or None, ' '.join([x.get('company', ''), x.get('person', '')]))
    return errs

def check_file(path, role_id=None):
    t = K.read(path)
    kind = os.path.basename(path)
    errs = style(t, kind)
    if kind.startswith('answers') and AI_OWN_WORK.search(t):
        errs.append('a question asks for work written without AI: do not draft it; flag it to the student')
    errs += unknown_claims(re.sub(r'(?m)^#+ .*$|^Q: .*$', '', t), role_id)
    return errs

def check_all():
    import pipeline as P
    bad = 0
    for x in P.emails():
        if x['status'] in ('sent', 'cancelled', 'skipped'): continue
        e = check_note(x) if x['kind'] == 'linkedin' else check_email(x)
        if e: bad += 1; print(f"{x['kind'][:5]} {x['id'][:24]:24} {x['company'][:22]:22} " + '; '.join(e))
    for d in sorted(os.listdir(K.OUT)) if os.path.isdir(K.OUT) else []:
        for f in ('resume.md', 'cover.md', 'answers.md'):
            p = f'{K.OUT}/{d}/{f}'
            if os.path.exists(p):
                e = check_file(p, d)
                if e: bad += 1; print(f'file  {d[:24]:24} {f:22} ' + '; '.join(e))
    print('problems:', bad)
    return bad

if __name__ == '__main__':
    a = sys.argv
    role = a[a.index('--role') + 1] if '--role' in a else None
    if '--drafts' in a:  # an outreach drafts file, before it is planned
        bad = 0
        for x in K.load_json(a[a.index('--drafts') + 1], []):
            e = check_note(x) if (x.get('kind') == 'linkedin' or (x.get('profile_url') and not x.get('to'))) else check_email(dict(x, slot=''))
            if e: bad += 1; print(f"{str(x.get('id', ''))[:24]:24} {x.get('company', '')[:22]:22} " + '; '.join(e))
        print('problems:', bad); sys.exit(1 if bad else 0)
    if '--file' in a or '--text' in a:
        if '--file' in a: e = check_file(a[a.index('--file') + 1], role)
        else: e = style(a[a.index('--text') + 1], 'text') + unknown_claims(a[a.index('--text') + 1], role)
        print('\n'.join(e) or 'ok'); print('problems:', len(e)); sys.exit(1 if e else 0)
    sys.exit(1 if check_all() else 0)
