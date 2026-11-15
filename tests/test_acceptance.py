# SPEC section 10 acceptance tests that run in code (standard library only). Each test works in its own temporary state
# folder with the bundled sample student, jev mocked and Mail mocked or on the .eml adapter. Nothing is submitted or sent.
#   python3 -m unittest discover -s tests -v
# Test 1 (fresh install + /demo): tests/acceptance_fresh_install.sh. Test 7 (NUworks): npm run test:nuworks.
# Test 10 (WSL): tests/acceptance_linux_docker.sh runs install.sh and the .eml test in a Linux container.
import datetime as dt, glob, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, time, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = f'{ROOT}/tools'
SAMPLE = f'{ROOT}/templates/sample-student/profile'

def make_state(**settings):
    st = tempfile.mkdtemp(prefix='coop-test-')
    shutil.copytree(SAMPLE, f'{st}/profile')
    s = json.load(open(f'{st}/profile/settings.json'))
    s.setdefault('mail', {})['adapter'] = 'mock'
    for k, v in settings.items():
        if isinstance(v, dict): s.setdefault(k, {}).update(v)
        else: s[k] = v
    json.dump(s, open(f'{st}/profile/settings.json', 'w'), indent=1)
    return st

def run(st, tool, *args, env=None, check=False):
    e = {**os.environ, 'COOP_STATE': st, 'COOP_JEV': 'mock', **(env or {})}
    e.pop('COOP_MAIL_ADAPTER', None)
    if env and 'COOP_MAIL_ADAPTER' in env: e['COOP_MAIL_ADAPTER'] = env['COOP_MAIL_ADAPTER']
    r = subprocess.run([sys.executable, '-I', f'{TOOLS}/{tool}', *args], env=e, capture_output=True, text=True, timeout=300)
    if check and r.returncode: raise AssertionError(f'{tool} {args} failed ({r.returncode}):\n{r.stdout}\n{r.stderr}')
    return r

def calls(st, log, action):
    p = f'{st}/logs/{log}'
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []

def actions(st, log, action): return [x for x in calls(st, log, action) if x['action'] == action]

def db(st):
    c = sqlite3.connect(f'{st}/data/pipeline.sqlite'); c.row_factory = sqlite3.Row; return c

GOOD_BODY = ("Hi Sam,\n\nI am a third-year Computer Science and Business Administration student at Northeastern University. "
             "At Northwind Freight I built an internal shipment-status dashboard in Python and React used by 3 operations teams.\n\n"
             "I am available for a six-month co-op from January to June 2027. Would you consider me for a co-op on your data team?\n\n"
             "If this isn't relevant, just let me know and I won't follow up.\n\nBest,\nAvery Example")
GOOD_FU = "Hi Sam,\n\nA short follow-up on my note about a spring co-op on your data team.\n\nBest,\nAvery Example"

def drafts(st, n=2):
    os.makedirs(f'{st}/data/incoming', exist_ok=True)
    xs = [{'id': f'mail-{i}', 'company': f'Example Data {i}', 'person': 'Sam Lee', 'to': f'sam{i}@example.com',
           'domains': ['example.com'], 'source_url': 'https://example.com/team', 'region': 'Boston',
           'subject': 'Spring 2027 co-op', 'body': GOOD_BODY, 'followup_subject': 'Re: Spring 2027 co-op', 'followup_body': GOOD_FU}
          for i in range(1, n + 1)]
    p = f'{st}/data/incoming/emails-test.json'; json.dump(xs, open(p, 'w')); return p

def full_cycle(st):
    r = run(st, 'cycle.py', 'run', '--offline', env={'COOP_MAIL_ADAPTER': 'mock'})
    assert r.returncode == 0, r.stdout + r.stderr
    return r

class T2_NoApprovalsNothingGoesOut(unittest.TestCase):
    def test_run_with_no_approvals_submits_and_sends_nothing(self):
        st = make_state()
        drafts(st)
        full_cycle(st)
        c = db(st)
        ready = c.execute("select count(*) from roles where status = 'ready'").fetchone()[0]
        self.assertGreater(ready, 0, 'the cycle should leave packs ready for review')
        slots = [r['slot'] for r in c.execute("select slot from emails")]
        self.assertTrue(all(slots), 'emails should be planned into slots')
        # run the sender at every planned slot and the applicant's submit on every ready id, as a careless agent would
        for s in slots: run(st, 'send_due.py', '--now', s, env={'COOP_MAIL_ADAPTER': 'mock'})
        ids = [r['id'] for r in c.execute("select id from roles where status = 'ready'")]
        out = run(st, 'applicant.py', 'submit', *ids).stdout
        self.assertIn('NOT submitted', out)
        self.assertEqual(actions(st, 'mock-jev.jsonl', 'submit'), [], 'no form may be submitted without approval')
        self.assertEqual(actions(st, 'mock-mail.jsonl', 'send') + actions(st, 'mock-mail.jsonl', 'draft'), [],
                         'no email may be drafted or sent without approval')
        self.assertGreater(len(actions(st, 'mock-jev.jsonl', 'prepare')), 0, 'forms are prepared (prepare mode)')

class T3_ApproveExactlyThatId(unittest.TestCase):
    def test_approve_submits_exactly_that_id(self):
        st = make_state()
        drafts(st)
        full_cycle(st)
        c = db(st)
        ready = [r['id'] for r in c.execute("select id from roles where status = 'ready' and channel = 'form' order by id")]
        self.assertGreaterEqual(len(ready), 2, 'need two ready roles')
        target = ready[1]
        r = run(st, 'approve.py', target, 'mail-2', check=True)
        self.assertIn(f'{target}: approved', r.stdout)
        # an agent passes every ready id: only the approved one may go
        out = run(st, 'applicant.py', 'submit', *ready).stdout
        subs = actions(st, 'mock-jev.jsonl', 'submit')
        self.assertEqual(len(subs), 1, out)
        jev_id = db(st).execute('select jev_id from applications where role_id = ?', (target,)).fetchone()[0]
        self.assertEqual(subs[0]['ref'], jev_id)
        self.assertEqual(db(st).execute("select status from roles where id = ?", (target,)).fetchone()[0], 'submitted')
        others = db(st).execute("select count(*) from roles where status = 'submitted'").fetchone()[0]
        self.assertEqual(others, 1)
        # a second submit of the same id does nothing more
        run(st, 'applicant.py', 'submit', target)
        self.assertEqual(len(actions(st, 'mock-jev.jsonl', 'submit')), 1)
        # emails: only mail-2 is drafted (prepare mode), at its slot
        for s in [r['slot'] for r in db(st).execute('select slot from emails')]:
            run(st, 'send_due.py', '--now', s, env={'COOP_MAIL_ADAPTER': 'mock'})
        mail = actions(st, 'mock-mail.jsonl', 'draft') + actions(st, 'mock-mail.jsonl', 'send')
        self.assertEqual([m['id'] for m in mail], ['mail-2'])
        self.assertEqual(actions(st, 'mock-mail.jsonl', 'send'), [], 'prepare mode drafts, never sends')

    def test_send_mode_sends_only_the_approved_email(self):
        st = make_state(send={'mode': 'send'})
        drafts(st, 3)
        run(st, 'plan_emails.py', check=True)
        run(st, 'approve.py', 'mail-3', check=True)
        for s in [r['slot'] for r in db(st).execute('select slot from emails')]:
            run(st, 'send_due.py', '--now', s, env={'COOP_MAIL_ADAPTER': 'mock'})
        self.assertEqual([m['id'] for m in actions(st, 'mock-mail.jsonl', 'send')], ['mail-3'])

    def test_unapproved_role_cannot_be_approved_before_the_gate(self):
        st = make_state()
        full_cycle(st)
        dq = db(st).execute("select id from roles where status = 'dq' limit 1").fetchone()[0]
        self.assertIn('NOT approved', run(st, 'approve.py', dq).stdout)

    def test_daily_cap_holds(self):
        st = make_state(limits={'applications_per_day': 1})
        full_cycle(st)
        ready = [r['id'] for r in db(st).execute("select id from roles where status = 'ready' and channel = 'form'")][:3]
        run(st, 'approve.py', *ready, check=True)
        out = run(st, 'applicant.py', 'submit', *ready).stdout
        self.assertEqual(len(actions(st, 'mock-jev.jsonl', 'submit')), 1, out)
        self.assertIn('daily cap', out)

class T4_ResumeOnePage(unittest.TestCase):
    def test_one_page_passes_two_pages_fail(self):
        st = make_state()
        os.makedirs(f'{st}/out/one'); os.makedirs(f'{st}/out/two')
        base = open(f'{SAMPLE}/resume.md').read()
        open(f'{st}/out/one/resume.md', 'w').write(base)
        exp = base.split('## Experience\n')[1].split('## Projects')[0]
        open(f'{st}/out/two/resume.md', 'w').write(base.replace('## Projects', exp * 6 + '## Projects', 1))
        one = run(st, 'resume.py', 'one')
        self.assertEqual(one.returncode, 0, one.stdout + one.stderr)
        self.assertEqual(json.load(open(f'{st}/out/one/resume.check.json'))['pages'], 1)
        two = run(st, 'resume.py', 'two')
        self.assertEqual(two.returncode, 1, two.stdout)
        self.assertIn('must be exactly one page', two.stdout)
        self.assertGreaterEqual(json.load(open(f'{st}/out/two/resume.check.json'))['pages'], 2)
        self.assertFalse(os.path.exists(f'{st}/out/two/resume.pdf'), 'a failed build leaves no resume.pdf')

    def test_invented_claim_fails_the_build(self):
        st = make_state(); os.makedirs(f'{st}/out/x')
        base = open(f'{SAMPLE}/resume.md').read()
        open(f'{st}/out/x/resume.md', 'w').write(base.replace('used by 3 operations teams', 'used by 12 operations teams at Google'))
        r = run(st, 'resume.py', 'x')
        self.assertEqual(r.returncode, 1); self.assertIn('"12"', r.stdout); self.assertIn('Google', r.stdout)

class T5_CheckerFacts(unittest.TestCase):
    def test_unknown_number_and_name_fail(self):
        st = make_state()
        bad = run(st, 'check_msgs.py', '--text', 'At Northwind Freight I cut report time by 40% and later interned at Google.')
        self.assertEqual(bad.returncode, 1)
        self.assertIn('number "40%"', bad.stdout); self.assertIn('name "Google"', bad.stdout)
        ok = run(st, 'check_msgs.py', '--text', 'At Northwind Freight I wrote 40+ unit tests and built a dashboard used by 3 operations teams.')
        self.assertEqual(ok.returncode, 0, ok.stdout)

    def test_number_with_a_different_mark_fails(self):
        st = make_state()
        r = run(st, 'check_msgs.py', '--text', 'I wrote 40 unit tests and about 150x more.')
        self.assertEqual(r.returncode, 1); self.assertIn('150x', r.stdout)

    def test_planned_email_with_invented_fact_is_flagged(self):
        st = make_state(); p = drafts(st, 1)
        xs = json.load(open(p)); xs[0]['body'] = xs[0]['body'].replace('3 operations teams', '7 operations teams at Stripe')
        json.dump(xs, open(p, 'w'))
        r = run(st, 'check_msgs.py', '--drafts', p)
        self.assertEqual(r.returncode, 1); self.assertIn('"7"', r.stdout); self.assertIn('Stripe', r.stdout)
        good = drafts(st, 1)
        self.assertEqual(run(st, 'check_msgs.py', '--drafts', good).returncode, 0)

class T6_SelfDevelopedBanned(unittest.TestCase):
    def setUp(self):
        self.st = make_state(mode='self-developed')
        open(f'{self.st}/profile/banned-employers.md', 'w').write('# Banned employers\n\n- Acme Robotics Inc. | careers.northeastern.edu listing\n- Ramp\n')

    def test_listed_employer_blocked_under_other_spellings(self):
        for name in ('ACME-Robotics, LLC', 'AcmeRobotics', 'acme robotics boston', 'Acmé Robotics (US)', 'The Acme Robotics Company'):
            r = run(self.st, 'banned.py', 'check', name)
            self.assertEqual(r.returncode, 1, f'{name}: {r.stdout}')
        for name in ('Acme Robotic Arms', 'Onramp', 'Rampart Labs'):
            self.assertEqual(run(self.st, 'banned.py', 'check', name).returncode, 0, name)

    def test_pipeline_and_rules_refuse_the_banned_employer(self):
        os.makedirs(f'{self.st}/data/incoming', exist_ok=True)
        json.dump([{'source': 'web', 'company': 'ACME-Robotics, LLC', 'title': 'Software Engineering Co-op', 'location': 'Boston, MA',
                    'url': 'https://example.com/jobs/1', 'description': 'A spring co-op from January to June.'}],
                  open(f'{self.st}/data/incoming/r.json', 'w'))
        run(self.st, 'pipeline.py', 'import', check=True)
        rid = db(self.st).execute('select id from roles').fetchone()[0]
        r = run(self.st, 'pipeline.py', 'verdict', rid, 'KEEP', '--reason', 'looks great')
        self.assertNotEqual(r.returncode, 0); self.assertIn('cannot be KEEP', r.stdout + r.stderr)
        run(self.st, 'screen_rules.py', check=True)
        row = db(self.st).execute('select verdict, reason from roles').fetchone()
        self.assertEqual(row['verdict'], 'DQ'); self.assertIn('banned list', row['reason'])

    def test_external_mode_does_not_use_the_banned_list(self):
        st = make_state(mode='external')
        open(f'{st}/profile/banned-employers.md', 'w').write('- Acme Robotics Inc.\n')
        r = run(st, 'pipeline.py', 'init'); self.assertEqual(r.returncode, 0)
        out = subprocess.run([sys.executable, '-I', '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import crew; print(crew.blocked("AcmeRobotics"))', TOOLS],
                             env={**os.environ, 'COOP_STATE': st}, capture_output=True, text=True).stdout.strip()
        self.assertEqual(out, 'None')

class T8_KillSwitch(unittest.TestCase):
    def guard(self, st, tool, inp):
        return subprocess.run([sys.executable, '-I', f'{TOOLS}/guard.py'], input=json.dumps({'tool_name': tool, 'tool_input': inp}),
                              env={**os.environ, 'COOP_STATE': st}, capture_output=True, text=True)

    def test_guard_blocks_every_acting_tool_while_stopped(self):
        st = make_state()
        self.assertEqual(self.guard(st, 'Bash', {'command': 'python3 -I tools/pipeline.py list'}).returncode, 0)
        open(f'{st}/STOP', 'w').write('x')
        for tool, inp in (('Bash', {'command': 'python3 -I tools/pipeline.py list'}), ('Write', {'file_path': f'{st}/out/a.md'}),
                          ('Agent', {'prompt': 'go'}), ('WebFetch', {'url': 'https://example.com'}), ('mcp__nuworks__nuworks_search', {})):
            r = self.guard(st, tool, inp)
            self.assertEqual(r.returncode, 2, tool); self.assertIn('kill switch', r.stderr)
        self.assertEqual(self.guard(st, 'Read', {'file_path': f'{st}/MORNING.md'}).returncode, 0)

    def test_running_cycle_stops_within_one_step(self):
        st = make_state()
        e = {**os.environ, 'COOP_STATE': st, 'COOP_JEV': 'mock', 'COOP_MAIL_ADAPTER': 'mock'}
        p = subprocess.Popen([sys.executable, '-I', f'{TOOLS}/cycle.py', 'run', '--offline', '--step-delay', '1.5'], env=e,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        cyc = f'{st}/logs/cycle.json'
        for _ in range(100):
            time.sleep(0.1)
            if os.path.exists(cyc) and any(s['status'] == 'done' for s in json.load(open(cyc))['steps']): break
        done_before = sum(1 for s in json.load(open(cyc))['steps'] if s['status'] == 'done')
        open(f'{st}/STOP', 'w').write('stop')
        out, _ = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 3, out)
        steps = json.load(open(cyc))['steps']
        done_after = sum(1 for s in steps if s['status'] == 'done')
        self.assertLessEqual(done_after - done_before, 1, f'at most the step already running may finish: {steps}')
        self.assertEqual(steps[-1]['status'], 'stopped')
        self.assertIn('STOP', out)

    def test_tools_refuse_while_stopped(self):
        st = make_state(); open(f'{st}/STOP', 'w').write('x')
        for tool, args in (('applicant.py', ['submit', 'x']), ('send_due.py', []), ('screen_rules.py', []), ('cycle.py', ['step', 'scout'])):
            r = run(st, tool, *args)
            self.assertEqual(r.returncode, 3, f'{tool}: {r.stdout}{r.stderr}')

class Guard_RulesInCode(unittest.TestCase):
    def guard(self, tool, inp):
        return subprocess.run([sys.executable, '-I', f'{TOOLS}/guard.py'], input=json.dumps({'tool_name': tool, 'tool_input': inp}),
                              env={**os.environ, 'COOP_STATE': tempfile.mkdtemp()}, capture_output=True, text=True).returncode

    def test_blocked(self):
        for cmd in ('npx jev submit abc', 'cd vendor/jev/src && npx --no-install jev submit x', 'npx jev daily --send',
                    'npx jev apply --submit --count 3', 'osascript -e \'tell application "Mail" to send\'',
                    'python3 -I tools/approve.py r1', 'echo r1 >> APPROVE.txt',
                    'sqlite3 data/pipeline.sqlite "insert into approvals values (1)"', 'python3 -I tools/send_due.py --mark-sent m1',
                    'rm STOP', 'curl https://www.linkedin.com/in/someone'):
            self.assertEqual(self.guard('Bash', {'command': cmd}), 2, cmd)
        # every way of running approve.py (or its code) is blocked
        for cmd in ('python3 tools/approve.py r1', 'cd tools && python3 approve.py r1', 'COOP_STATE=demo python3 -I tools/approve.py r1',
                    '/usr/bin/python3.12 -I /x/coop-crew/tools/approve.py r1', 'env X=1 python tools/approve.py r1',
                    'uv run tools/approve.py r1', 'bash -c "python3 -I tools/approve.py r1"', './tools/approve.py r1',
                    'cd tools; python3 -m approve r1', 'python3 -c "import approve; approve.approve([\'r1\'])"',
                    'python3 -c "from approve import approve"', 'python3 -c "import runpy; runpy.run_path(\'tools/approve.py\')"',
                    'echo tools/approve.py | xargs python3', 'ls; python3 -I tools/approve.py r1', 'sh tools/approve.py r1'):
            self.assertEqual(self.guard('Bash', {'command': cmd}), 2, cmd)
        # a fetch is blocked wherever the URL sits in the command, not only right after curl
        for cmd in ('for u in https://www.symplicity.com/terms https://www.symplicity.com/legal; do curl -s "$u"; done',
                    'U=https://northeastern-csm.symplicity.com/students/; curl -sL "$U"', 'wget -qO- https://x.symplicity.com/a',
                    'U=https://www.linkedin.com/in/x; curl "$U"', 'python3 -c "import urllib.request as u; u.urlopen(\'https://www.linkedin.com/in/x\')"'):
            self.assertEqual(self.guard('Bash', {'command': cmd}), 2, cmd)
        for p in ('APPROVE.txt', 'data/pipeline.sqlite', '.claude/settings.json', '.mcp.json', 'tools/applicant.py'):
            self.assertEqual(self.guard('Write', {'file_path': f'/x/coop-crew/{p}'}), 2, p)
        self.assertEqual(self.guard('WebFetch', {'url': 'https://www.linkedin.com/in/x'}), 2)
        self.assertEqual(self.guard('WebFetch', {'url': 'https://northeastern-csm.symplicity.com/students/'}), 2)

    def test_allowed(self):
        for cmd in ('python3 -I tools/applicant.py submit r1', 'python3 -I tools/pipeline.py list', 'sqlite3 -readonly data/pipeline.sqlite "select 1"',
                    'python3 -I tools/send_due.py', 'COOP_STATE=demo python3 -I tools/resume.py x',
                    # reading approve.py is not running it
                    'sed -n 1,60p tools/approve.py; grep -n "mock" tools/email_audit.py', 'cat tools/approve.py', 'head -20 tools/approve.py',
                    'grep -rn "approve.py" .claude/commands', 'wc -l tools/approve.py && git log --oneline -- tools/approve.py',
                    'git diff tools/approve.py', 'grep -rn "symplicity.com" mcp/nuworks', 'grep -n linkedin.com profile/settings.json'):
            self.assertEqual(self.guard('Bash', {'command': cmd}), 0, cmd)

    def test_every_write_rule_has_an_edit_rule(self):
        # Claude Code checks the Write tool against Edit(...) rules: a Write(...) rule alone is not applied, and a headless
        # /run then cannot hand off through data/incoming/ (found in the live acceptance run, 2026-11-14)
        allow = json.load(open(f'{ROOT}/.claude/settings.json'))['permissions']['allow']
        for r in allow:
            m = re.fullmatch(r'Write\((.*)\)', r)
            if m: self.assertIn(f'Edit({m.group(1)})', allow, f'{r} needs a matching Edit rule')
        self.assertEqual(self.guard('Write', {'file_path': '/x/coop-crew/out/r1/brief.md'}), 0)

FIX = f'{ROOT}/tests/fixtures/nuworks'

def tiny_pdf(lines):
    """A one-page PDF with these text lines (standard library only), for the NUworks import test."""
    esc = lambda s: s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    content = 'BT /F1 11 Tf 50 750 Td 14 TL ' + ' '.join(f'({esc(l)}) Tj T*' for l in lines) + ' ET'
    objs = ['<< /Type /Catalog /Pages 2 0 R >>', '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
            f'<< /Length {len(content)} >>\nstream\n{content}\nendstream', '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    out, offs = '%PDF-1.4\n', []
    for i, o in enumerate(objs, 1): offs.append(len(out)); out += f'{i} 0 obj\n{o}\nendobj\n'
    x = len(out)
    out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n' + ''.join(f'{o:010d} 00000 n \n' for o in offs)
    return (out + f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n').encode('latin-1')

class NUworks_DefaultPath(unittest.TestCase):
    """The default NUworks path: job-alert emails and postings the student saved. No NUworks page is ever loaded."""
    def setUp(self):
        self.st = make_state(mode='nuworks+external')
        os.makedirs(f'{self.st}/data/inbox'); os.makedirs(f'{self.st}/data/nuworks-import')

    def incoming(self, prefix):
        fs = sorted(glob.glob(f'{self.st}/data/incoming/{prefix}-*.json'))
        return [r for f in fs for r in json.load(open(f))]

    def test_alert_email_becomes_nuworks_rows(self):
        shutil.copy(f'{FIX}/alert.eml', f'{self.st}/data/inbox/alert.eml')
        # an ordinary email in the same folder is not an alert
        open(f'{self.st}/data/inbox/recruiter.eml', 'w').write('From: Sam Lee <sam@example.com>\nSubject: Coffee chat?\n'
            'Date: Fri, 13 Nov 2026 09:00:00 -0500\nContent-Type: text/plain\n\nWould you like to talk about the data team?\n')
        r = run(self.st, 'nuworks_alerts.py', check=True)
        self.assertIn('1 alert email(s), 2 postings', r.stdout)
        rows = {x['posting_id']: x for x in self.incoming('nuworks-alerts')}
        self.assertEqual(set(rows), {'0123456789abcdef0123456789abcdef', 'fedcba9876543210fedcba9876543210'}, 'footer links are not postings')
        a, b = rows['0123456789abcdef0123456789abcdef'], rows['fedcba9876543210fedcba9876543210']
        self.assertEqual((a['title'], a['company'], a['location'], a['deadline']), ('Data Analyst Co-op', 'Example Analytics Inc.', 'Boston, MA', '2026-12-15'))
        self.assertEqual((b['title'], b['company'], b['location'], b['deadline']), ('Machine Learning Engineering Co-op', 'Example Robotics LLC', 'Remote', '2027-01-08'))
        self.assertTrue(all(x['source'] == 'nuworks' and x['channel'] == 'nuworks' for x in rows.values()))
        self.assertIn('saved search: Data co-op', a['description'])
        # each email is read once
        self.assertIn('no new postings', run(self.st, 'nuworks_alerts.py', check=True).stdout)
        run(self.st, 'pipeline.py', 'import', check=True)
        got = db(self.st).execute("select source, channel from roles").fetchall()
        self.assertEqual([(x['source'], x['channel']) for x in got], [('nuworks', 'nuworks')] * 2)

    def test_off_outside_nuworks_mode(self):
        st = make_state(mode='external'); os.makedirs(f'{st}/data/inbox')
        shutil.copy(f'{FIX}/alert.eml', f'{st}/data/inbox/alert.eml')
        self.assertIn('off', run(st, 'nuworks_alerts.py', check=True).stdout)
        self.assertIn('off', run(st, 'nuworks_import.py', check=True).stdout)
        self.assertEqual(glob.glob(f'{st}/data/incoming/nuworks-*.json'), [])

    def test_manual_import_html_pdf_and_fill_existing(self):
        shutil.copy(f'{FIX}/alert.eml', f'{self.st}/data/inbox/alert.eml')
        run(self.st, 'nuworks_alerts.py', check=True); run(self.st, 'pipeline.py', 'import', check=True)
        known = db(self.st).execute("select id from roles where posting_id = '0123456789abcdef0123456789abcdef'").fetchone()['id']
        for f in ('posting-saved.html', 'posting-new.html'): shutil.copy(f'{FIX}/{f}', f'{self.st}/data/nuworks-import/{f}')
        has_pdf = bool(shutil.which('pdftotext'))
        if has_pdf:
            open(f'{self.st}/data/nuworks-import/saved.pdf', 'wb').write(tiny_pdf([
                'Data Engineering Co-op', 'Employer: Example Health Group', 'Location: Boston, MA',
                'Application Deadline: Dec 1, 2026', 'Job ID: 99887766', 'Description',
                'Build data pipelines in Python for six months.']))
        r = run(self.st, 'nuworks_import.py', check=True)
        self.assertIn(f'full text added to 1 role(s) already in the pipeline: {known}', r.stdout)
        posting = open(f'{self.st}/out/{known}/posting.md').read()
        self.assertIn('builds SQL pipelines and Python dashboards', posting)
        self.assertNotIn('var x', posting, 'scripts are not posting text')
        rows = {x['title']: x for x in self.incoming('nuworks-import')}
        new = rows['Software Engineering Co-op']
        self.assertEqual((new['company'], new['location'], new['deadline'], new['posting_id']),
                         ('Example Freight Systems', 'New York, NY', '2027-01-20', 'aaaabbbbccccddddeeeeffff00001111'))
        if has_pdf:
            p = rows['Data Engineering Co-op']
            self.assertEqual((p['company'], p['location'], p['deadline'], p['posting_id']), ('Example Health Group', 'Boston, MA', '2026-12-01', '99887766'))
        self.assertTrue(all(x['source'] == 'nuworks' for x in rows.values()))
        self.assertIn('nothing to import', run(self.st, 'nuworks_import.py', check=True).stdout, 'each file is read once')
        self.assertTrue(os.path.exists(f'{self.st}/data/nuworks-import/posting-new.html'), 'the student\'s files are not moved')

class Pipeline_ApplyVerdicts(unittest.TestCase):
    def test_missing_file_fails_loudly_and_state_relative_path_works(self):
        st = make_state()
        r = run(st, 'pipeline.py', 'apply-verdicts', 'data/incoming/missing.json')
        self.assertEqual(r.returncode, 1); self.assertIn('nothing recorded', r.stderr)
        os.makedirs(f'{st}/data/incoming', exist_ok=True)
        json.dump([{'id': 'zz', 'verdict': 'DQ', 'reason': 'x'}], open(f'{st}/data/incoming/v.json', 'w'))
        r = run(st, 'pipeline.py', 'apply-verdicts', 'data/incoming/v.json')   # relative to the state folder, as in /demo
        self.assertEqual(r.returncode, 0); self.assertIn('zz: not recorded: no role zz', r.stdout)

class T10_EmlAdapter(unittest.TestCase):
    def test_eml_drafts_instead_of_mail(self):
        st = make_state(mail={'adapter': 'eml'})
        drafts(st, 2); run(st, 'plan_emails.py', check=True)
        run(st, 'approve.py', 'mail-1', check=True)
        for s in [r['slot'] for r in db(st).execute('select slot from emails')]:
            run(st, 'send_due.py', '--now', s, env={'COOP_MAIL_ADAPTER': 'eml'}, check=True)
        out = sorted(os.listdir(f'{st}/data/outbox'))
        self.assertEqual(out, ['READY.md', 'mail-1.eml'])
        eml = open(f'{st}/data/outbox/mail-1.eml').read()
        self.assertIn('X-Unsent: 1', eml); self.assertIn('To: sam1@example.com', eml)
        self.assertEqual(db(st).execute("select status from emails where id = 'mail-1'").fetchone()[0], 'drafted')
        self.assertEqual(db(st).execute("select status from emails where id = 'mail-2'").fetchone()[0], 'planned')

    def test_send_mode_on_eml_never_sends(self):
        st = make_state(mail={'adapter': 'eml'}, send={'mode': 'send'})
        drafts(st, 1); run(st, 'plan_emails.py', check=True); run(st, 'approve.py', 'mail-1', check=True)
        s = db(st).execute('select slot from emails').fetchone()[0]
        r = run(st, 'send_due.py', '--now', s, env={'COOP_MAIL_ADAPTER': 'eml'}, check=True)
        self.assertTrue(os.path.exists(f'{st}/data/outbox/mail-1.eml'), r.stdout)

class Outreach_Rules(unittest.TestCase):
    def test_one_email_per_person_and_follow_up_once_per_company(self):
        st = make_state(mail={'adapter': 'mock'})
        p = drafts(st, 1)
        xs = json.load(open(p)); dup = dict(xs[0], id='mail-dup'); json.dump(xs + [dup], open(p, 'w'))
        out = run(st, 'plan_emails.py', check=True).stdout
        self.assertIn('one email per person', out)
        self.assertEqual(db(st).execute('select count(*) from emails').fetchone()[0], 1)
        run(st, 'approve.py', 'mail-1', check=True)
        slot = db(st).execute('select slot from emails').fetchone()[0]
        run(st, 'send_due.py', '--now', slot, env={'COOP_MAIL_ADAPTER': 'mock'}, check=True)
        e = {**os.environ, 'COOP_STATE': st}
        # the student sent the draft by hand: the follow-up comes 6 working days later, at most once, and a reply cancels it
        subprocess.run([sys.executable, '-I', f'{TOOLS}/send_due.py', '--mark-sent', 'mail-1', slot.replace('T', ' ')], env=e, check=True, capture_output=True)
        due = db(st).execute("select followup_due from emails where id = 'mail-1'").fetchone()[0]
        d0, d1 = dt.date.fromisoformat(slot[:10]), dt.date.fromisoformat(due[:10])
        wd = sum(1 for i in range(1, (d1 - d0).days + 1) if (d0 + dt.timedelta(days=i)).weekday() < 5)
        self.assertTrue(5 <= wd <= 7, (slot, due))
        run(st, 'send_due.py', '--now', due, env={'COOP_MAIL_ADAPTER': 'mock'}, check=True)
        run(st, 'send_due.py', '--now', due, env={'COOP_MAIL_ADAPTER': 'mock'}, check=True)
        self.assertEqual([m['id'] for m in actions(st, 'mock-mail.jsonl', 'draft')], ['mail-1', 'mail-1-followup'])

    def test_reply_cancels_follow_up(self):
        st = make_state(); drafts(st, 1); run(st, 'plan_emails.py', check=True); run(st, 'approve.py', 'mail-1', check=True)
        slot = db(st).execute('select slot from emails').fetchone()[0]
        e = {**os.environ, 'COOP_STATE': st}
        subprocess.run([sys.executable, '-I', f'{TOOLS}/send_due.py', '--mark-sent', 'mail-1', slot.replace('T', ' ')], env=e, check=True, capture_output=True)
        os.makedirs(f'{st}/data/inbox')
        open(f'{st}/data/inbox/r.eml', 'w').write('From: Sam Lee <sam1@example.com>\nTo: avery.example@example.com\nSubject: Re: Spring 2027 co-op\n'
                                                   'Date: Mon, 16 Nov 2026 09:00:00 -0500\n\nThanks Avery, can you talk Thursday?\n')
        run(st, 'inbox.py', env={'COOP_MAIL_ADAPTER': 'eml'}, check=True)
        self.assertEqual(db(st).execute("select status from emails where id = 'mail-1'").fetchone()[0], 'replied')
        due = db(st).execute("select followup_due from emails where id = 'mail-1'").fetchone()[0]
        run(st, 'send_due.py', '--now', due, env={'COOP_MAIL_ADAPTER': 'mock'}, check=True)
        self.assertEqual(actions(st, 'mock-mail.jsonl', 'draft'), [])
        self.assertIn('Interview invite', open(f'{st}/needs-reply.html').read())  # "can you talk Thursday?" is a call offer

    def test_hard_cap_40(self):
        st = make_state(limits={'emails_per_day': 500})
        r = subprocess.run([sys.executable, '-I', '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import crew; print(crew.EMAILS_PER_DAY)', TOOLS],
                           env={**os.environ, 'COOP_STATE': st}, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), '40')

class Gate_Rules(unittest.TestCase):
    def test_gate_blocks_missing_pieces_and_ai_own_work(self):
        st = make_state(); full_cycle(st)
        rid = db(st).execute("select id from roles where status = 'ready' limit 1").fetchone()[0]
        d = f'{st}/out/{rid}'
        os.remove(f'{d}/brief.md')
        json.dump([{'label': 'Why this company?', 'required': True},
                   {'label': 'Confirm this answer is your own work, written without the use of AI', 'required': True}], open(f'{d}/questions.json', 'w'))
        open(f'{d}/answers.md', 'w').write('## Confirm this answer is your own work, written without the use of AI\nYes it is.\n')
        r = run(st, 'gate.py', rid)
        self.assertEqual(r.returncode, 1)
        for want in ('no Company brief', 'required question not answered: "Why this company?"', 'written without AI'):
            self.assertIn(want, r.stdout)
        self.assertEqual(db(st).execute('select status from roles where id = ?', (rid,)).fetchone()[0], 'blocked')
        self.assertIn('NOT approved', run(st, 'approve.py', rid).stdout)

class T9_PersonalDataScan(unittest.TestCase):
    def test_scan_finds_planted_data_and_passes_the_repo(self):
        # The planted values are built at run time, so this test file itself contains none of them.
        name, mail, phone, key = 'Jane' + ' Realperson', 'jane' + '@' + 'gmail.com', '617-' + '232-' + '9911', 'sk-' + 'ant-' + 'abcdefghij' * 3
        pat = tempfile.mktemp(); open(pat, 'w').write('\\b' + name + '\\b\n')
        r = subprocess.run([sys.executable, '-I', f'{TOOLS}/pii_scan.py', '--patterns', pat], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        repo = tempfile.mkdtemp(); shutil.copytree(TOOLS, f'{repo}/tools')
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
        open(f'{repo}/notes.md', 'w').write(f'Contact {name} at {mail} or {phone}. key {key}\n'
                                            'Sample: avery.example@example.com, (617) 555-0142\n')
        subprocess.run(['git', 'add', '-A'], cwd=repo, check=True)
        subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-qm', 'x'], cwd=repo, check=True)
        os.remove(f'{repo}/notes.md')  # gone from the tree, still in the history
        r = subprocess.run([sys.executable, '-I', f'{repo}/tools/pii_scan.py', '--patterns', pat], cwd=repo, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        for want in (mail, phone, 'Anthropic key', name): self.assertIn(want, r.stdout)
        self.assertNotIn('avery.example', r.stdout); self.assertNotIn('555', r.stdout)

if __name__ == '__main__':
    unittest.main()
