# Builds the talk deck docs/talk/slides.html from docs/talk/slides.tpl.html: one self-contained file (no network), with
# the screenshots (docs/talk/img/*.jpg, the bundled sample student only) and the QR code to the repo inlined, and the
# test counts on the "results" slide counted from the test files, so the slide never claims more than the repo has.
# usage: python3 -I tools/build_slides.py
import base64, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qr_svg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TALK = f'{ROOT}/docs/talk'
REPO_URL = 'https://github.com/dudailia/coop-crew'

def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()

def counts():
    py = len(re.findall(r'^\s+def test_', open(f'{ROOT}/tests/test_acceptance.py', encoding='utf-8').read(), re.M))
    js = open(f'{ROOT}/mcp/nuworks/test/server.test.mjs', encoding='utf-8').read()
    loop = re.search(r"for \(const \[kw, re\] of \[(.*?)\]\) \{", js)          # one test per CAPTCHA/error/login page
    nu = len(re.findall(r'^\s*test\(', js, re.M)) - (1 if loop else 0) + (len(re.findall(r"\['", loop.group(1))) if loop else 0)
    return py, nu

def main():
    t = open(f'{TALK}/slides.tpl.html', encoding='utf-8').read()
    py, nu = counts()
    svg = qr_svg.svg(REPO_URL, dark='#0d1522', module=12, border=2)
    out = (t.replace('{{TODAY_JPG}}', b64(f'{TALK}/img/today-deck.jpg')).replace('{{RESUME_JPG}}', b64(f'{TALK}/img/resume-deck.jpg'))
            .replace('{{QR_SVG}}', svg).replace('{{PY_TESTS}}', str(py)).replace('{{NU_TESTS}}', str(nu)))
    left = re.findall(r'\{\{\w+\}\}', out)
    if left: sys.exit(f'unfilled placeholders: {left}')
    if re.search(r'(src|href)="(https?:)?//', out): sys.exit('the deck must not load anything from the network')
    open(f'{TALK}/slides.html', 'w', encoding='utf-8').write(out)
    print(f'docs/talk/slides.html: {len(out) // 1024} KB, {out.count("<section class=")} slides, {py} Python tests, {nu} NUworks tests')

if __name__ == '__main__':
    main()
