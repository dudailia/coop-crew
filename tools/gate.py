# The gatekeeper's checks for one role's review pack, in code. A pack passes only with: a Company brief of 3 to 6
# bullets; a one-page resume.pdf that the build checked; every required portal question answered (or the role is a
# NUworks or email role with no form); a verbatim field log; no unknown claims; no answer to a question that asks for
# work written without AI. A pass sets the role to "ready" (it can then be approved); a fail sets "blocked".
# A ready pack is never permission to submit: only /approve is.
# usage: python3 -I tools/gate.py <id> [<id> ...]     prints the result and writes out/<id>/gate.json
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K, pipeline as P, check_msgs as CM

def sections(md):
    """'## Label' blocks of answers.md -> {label: text}."""
    out, cur = {}, None
    for l in md.splitlines():
        m = re.match(r'^##\s+(.+?)\s*$', l)
        if m: cur = m.group(1).strip(); out[cur] = ''; continue
        if cur is not None: out[cur] += l + '\n'
    return {k: v.strip() for k, v in out.items()}

def norm(s): return ' '.join(re.sub(r'[^\w ]', ' ', s.lower()).split())

def check(rid):
    c = P.db(); r = c.execute('select * from roles where id = ?', (rid,)).fetchone()
    if not r: return {'ok': False, 'problems': [f'no role {rid}']}
    d = f'{K.OUT}/{rid}'; problems, flags = [], []
    brief = K.read(f'{d}/brief.md')
    bullets = [l for l in brief.splitlines() if re.match(r'^\s*[-*]\s+\S', l)]
    if not brief: problems.append('no Company brief (brief.md)')
    elif not 3 <= len(bullets) <= 6: problems.append(f'Company brief has {len(bullets)} bullets (needs 3 to 6)')
    rc = K.load_json(f'{d}/resume.check.json', {})
    if not os.path.exists(f'{d}/resume.pdf'): problems.append('no resume.pdf')
    elif rc.get('pages') != 1: problems.append(f'resume.pdf was not built by tools/resume.py as exactly one page (pages: {rc.get("pages")})')
    elif not rc.get('ok'): problems.append('the resume build reported problems: ' + '; '.join(rc.get('problems', []))[:300])
    questions = K.load_json(f'{d}/questions.json', [])
    answers = sections(K.read(f'{d}/answers.md'))
    na = {norm(k): v for k, v in answers.items()}
    for q in questions:
        label = q.get('label', '')
        if CM.AI_OWN_WORK.search(label + ' ' + q.get('hint', '')):
            flags.append(f'"{label[:80]}" asks for work written without AI: not drafted, the student answers it')
            if na.get(norm(label)): problems.append(f'an answer was drafted for a question that asks for work written without AI: "{label[:60]}"')
            continue
        if q.get('required') and not na.get(norm(label)): problems.append(f'required question not answered: "{label[:80]}"')
    if r['channel'] == 'form' and not questions and not os.path.exists(f'{d}/questions.json'):
        problems.append('no questions.json: the portal\'s required questions were not pulled')
    log = K.read(f'{d}/field-log.md')
    if not log.strip(): problems.append('no field log (field-log.md)')
    for f in ('resume.md', 'cover.md', 'answers.md'):
        if os.path.exists(f'{d}/{f}'):
            for e in CM.check_file(f'{d}/{f}', rid):
                if 'without AI' in e: continue
                problems.append(f'{f}: {e}')
    # work authorization: any answer under a work-authorization question must be the profile sentence, word for word
    sentences = [w.get('sentence', '') for w in K.S['work_auth'].values() if w.get('sentence')]
    for label, text in answers.items():
        if re.search(r'authori[sz]|sponsor|visa|legally (able|eligible)|work permit', label, re.I) and len(text.split()) > 3:
            if not any(s and s in text for s in sentences):
                problems.append(f'work-authorization answer to "{label[:60]}" is not a profile sentence word for word')
    b = K.blocked(r['company'])
    if b: problems.append(f'{r["company"]} is blocked ({b})')
    soft = K.read(f'{d}/soft-flags.md').strip()
    res = {'id': rid, 'ok': not problems, 'problems': problems, 'flags': flags, 'soft_flags': soft, 'checked': P.stamp()}
    K.save_json(f'{d}/gate.json', res)
    if r['status'] in ('tailored', 'researched', 'keep', 'ready', 'blocked'):
        new = 'ready' if not problems else 'blocked'
        if new != r['status']: P.set_status(c, rid, new, 'gate: ' + ('pack complete' if not problems else '; '.join(problems)[:300]))
    c.commit()
    return res

if __name__ == '__main__':
    bad = 0
    for i in sys.argv[1:]:
        res = check(i)
        print(f"{i}: {'PASS (ready for review; not permission to submit)' if res['ok'] else 'BLOCKED'}")
        for p in res.get('problems', []): print(f'  - {p}')
        for f in res.get('flags', []): print(f'  ! {f}')
        bad += not res['ok']
    sys.exit(1 if bad else 0)
