// Records the demo's result pages (TODAY.html, the review pack, the one-page resume, the tracker) frame by frame with
// Playwright's headless Chromium, so the video is exactly smooth: every frame is a screenshot taken at a computed scroll
// position, the pages scroll at one constant speed (whole pixels per frame, no easing, no pauses), captions fade out and in,
// and scenes dip through white into each other. ffmpeg joins the frames.
//   video cut: 1280x720, 30 fps, about 60 s, 1 px per frame          -> <out.mp4>
//   gif cut:   the same pages, about 14 s, 960 px wide, 15 fps, a seamless loop  -> --gif <out.gif>
// Local files only: every request that is not file: or data: is blocked.
// usage: node tools/record_demo.mjs <demo state dir> <out.mp4> [--gif <out.gif>]
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync, spawn } from 'node:child_process';
import { chromium } from 'playwright';

const args = process.argv.slice(2);
const gifAt = args.indexOf('--gif');
const gifOut = gifAt >= 0 ? args.splice(gifAt, 2)[1] : null;
const [demo, mp4Out] = args;
if (!demo || !mp4Out) { console.error('usage: node tools/record_demo.mjs <demo dir> <out.mp4> [--gif <out.gif>]'); process.exit(2); }
const today = path.resolve(demo, 'TODAY.html'), tracker = path.resolve(demo, 'tracker.html');
if (!fs.existsSync(today)) { console.error(`no ${today}: run the demo first`); process.exit(1); }
const pack = fs.readdirSync(path.join(demo, 'out'))
  .find((d) => fs.existsSync(path.join(demo, 'out', d, 'gate.json')) && fs.existsSync(path.join(demo, 'out', d, 'resume.html')));
if (!pack) { console.error('no review pack with a resume in the demo: run the offline demo (tools/demo.py run --offline)'); process.exit(1); }
const resume = path.resolve(demo, 'out', pack, 'resume.html');

// Each cut: frame size, body zoom, frames per second, frames in a scene change (FADE, about 0.5 s) and in each half of
// a caption change (HALF).
const VIDEO = { W: 1280, H: 720, ZOOM: 4 / 3, FPS: 30, FADE: 16, HALF: 8 };
const GIF = { W: 960, H: 540, ZOOM: 1, FPS: 15, FADE: 8, HALF: 4 };
let W, H, ZOOM, FPS, FADE, HALF, ctx, page;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'coop-rec-'));
const browser = await chromium.launch();
async function use(cut) {
  ({ W, H, ZOOM, FPS, FADE, HALF } = cut);
  if (ctx) await ctx.close();
  ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1, colorScheme: 'light' });
  await ctx.route('**/*', (r) => (/^(file|data):/.test(r.request().url()) ? r.continue() : r.abort()));
  page = await ctx.newPage();
}

// Opens a page zoomed on <body> (4/3 in the video): the text is larger and still sharp, and the window scrolls in screen pixels,
// so one pixel per frame is an exact, even speed. Returns the page's scroll range and the y of the parts we caption.
async function open(file, capPx) {
  await page.goto('file://' + file);
  return page.evaluate(([zoom, capPx]) => {
    document.querySelectorAll('details').forEach((d) => { d.open = true; });
    const st = document.createElement('style');
    st.textContent = `html{scrollbar-width:none;overflow-x:hidden} html::-webkit-scrollbar{display:none} body{zoom:${zoom}}
      .__cap{position:fixed;left:28px;bottom:28px;z-index:99999;max-width:${Math.round((innerWidth - 100) / zoom)}px;
      padding:${14 / zoom}px ${24 / zoom}px;border-radius:${12 / zoom}px;background:rgba(13,21,34,.94);color:#f7f0e2;
      font:600 ${capPx / zoom}px/1.3 "Avenir Next",Avenir,"Segoe UI",system-ui,sans-serif;border-left:${7 / zoom}px solid #ffb547;
      box-shadow:0 8px 32px rgba(0,0,0,.3);opacity:0;transition:none;text-wrap:balance}`;
    document.head.appendChild(st);
    const c = document.createElement('div'); c.className = '__cap'; c.id = '__cap0'; document.body.appendChild(c);
    const y = (el) => (el ? Math.round(el.getBoundingClientRect().top + scrollY) : null);
    const h = [...document.querySelectorAll('h2')].find((x) => /Applications to review/.test(x.textContent));
    let p = h && h.nextElementSibling;
    while (p && !p.matches('section.pack')) p = p.nextElementSibling;
    const sum = (re) => p && [...p.querySelectorAll('summary')].find((s) => re.test(s.textContent));
    return { max: document.documentElement.scrollHeight - innerHeight, pack: y(p), soft: y(sum(/Soft flags/)),
      log: y(sum(/Field log/)), acts: y(p && p.querySelector('.acts')) };
  }, [ZOOM, capPx]);
}

// One frame: scroll to y (screen px) and set the caption (text and opacity), then take the screenshot.
async function frame(y, caps) {
  await page.evaluate(([y, caps]) => {
    scrollTo(0, y);
    caps.forEach(([t, o], i) => { const c = document.getElementById('__cap' + i); if (c.textContent !== t) c.textContent = t; c.style.opacity = String(o); });
  }, [y, caps]);
  return page.screenshot({ type: 'png' });
}

// A scene: frames from scroll y0 at `speed` whole px per frame; caption i shows from frame at[i].
async function scene(name, file, capPx, plan) {
  const m = await open(file, capPx);
  const { y0, n, captions, speed = 1 } = plan(m);
  const y1 = y0 + (n - 1) * speed;
  if (y0 < 0 || y1 > m.max) throw new Error(`${name}: needs scroll ${y0} to ${y1}, page allows 0 to ${m.max}`);
  const short = captions.map((c, i) => [c, ((captions[i + 1] || [n])[0] - c[0]) / FPS]).filter(([, s]) => s < 3.5);
  if (short.length) console.error(`warning: ${name}: captions shorter than 3.5 s: ${short.map(([c, s]) => `"${c[1]}" ${s.toFixed(1)} s`).join('; ')}`);
  const out = path.join(tmp, name + '.mkv');
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'ffv1', '-pix_fmt', 'bgr0', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((ok, bad) => ff.on('close', (c) => (c ? bad(new Error(`ffmpeg exited ${c} on ${name}`)) : ok())));
  for (let f = 0; f < n; f++) {
    // a caption change fades the old text out over HALF frames, then the new text in over HALF frames
    let cur = -1;
    captions.forEach(([at], i) => { if (f >= at) cur = i; });
    let caps = [['', 0]];
    if (cur >= 0) {
      const j = f - captions[cur][0];
      if (cur === 0 && captions[0][0] === 0) caps = [[captions[0][1], 1]];
      else if (j < HALF && cur > 0) caps = [[captions[cur - 1][1], 1 - (j + 1) / HALF]];
      else caps = [[captions[cur][1], Math.min(1, (j - (cur > 0 ? HALF : 0) + 1) / HALF)]];
    }
    const png = await frame(y0 + f * speed, caps);
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done;
  console.log(`  ${name}: ${n} frames (${(n / FPS).toFixed(1)} s), scroll ${y0} to ${y1} of ${m.max}, ${speed} px per frame`);
  return { file: out, n };
}

// Joins scenes, each dipping through white into the next over FADE frames. Returns the joined file and its frame count.
function join(parts, out) {
  const inputs = parts.flatMap((p) => ['-i', p.file]);
  let f = '', last = '[0:v]', t = parts[0].n;
  for (let i = 1; i < parts.length; i++) {
    const tag = i === parts.length - 1 ? '[v]' : `[x${i}]`;
    f += `${last}[${i}:v]xfade=transition=fadewhite:duration=${FADE / FPS}:offset=${((t - FADE) / FPS).toFixed(6)}${tag};`;
    last = tag; t += parts[i].n - FADE;
  }
  const r = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', ...inputs, '-filter_complex', f.replace(/;$/, ''), '-map', '[v]',
    '-c:v', 'ffv1', '-pix_fmt', 'bgr0', out], { stdio: 'inherit' });
  if (r.status) throw new Error('ffmpeg could not join the scenes');
  return t;
}
const run = (a) => { const r = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', ...a], { stdio: 'inherit' }); if (r.status) throw new Error('ffmpeg failed: ' + a.join(' ')); };

// The video cut: TODAY.html top to bottom, the resume, the tracker, then the top of TODAY.html to close.
if (!process.env.REC_GIF_ONLY) {
  console.log('video cut (1280x720, 30 fps):');
  await use(VIDEO);
  const V = 30;  // caption size in screen px
  const v = [
    await scene('v1-today', today, V, (m) => ({ y0: 0, n: m.max + 1, captions: [
      [0, 'TODAY.html: what the crew prepared overnight, for a made-up sample student'],
      [m.pack - 60, 'A review pack for each role: why it was kept, and a short company brief'],
      [m.soft - 380, 'Soft flags: what to check yourself before you approve'],
      [m.log - 470, 'The field log: every form field, its exact value and where it came from'],
      [m.acts - 560, 'Approve or Skip. Nothing is submitted or sent until you approve that exact id']] })),
    await scene('v2-resume', resume, V, (m) => ({ y0: 0, n: m.max + 1, captions: [
      [0, 'A one-page resume for this role, built only from the student\'s own facts']] })),
    await scene('v3-tracker', tracker, V, (m) => ({ y0: 0, n: m.max + 1, captions: [
      [0, 'The tracker: every role the crew judged, and the reason for each']] })),
    await scene('v4-close', today, V, () => ({ y0: 0, n: 210, captions: [
      [0, 'Try it yourself: /demo runs on a made-up student and sends nothing. github.com/dudailia/coop-crew']] })),
  ];
  const vn = join(v, path.join(tmp, 'video.mkv'));
  fs.mkdirSync(path.dirname(path.resolve(mp4Out)), { recursive: true });
  run(['-i', path.join(tmp, 'video.mkv'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-movflags', '+faststart', '-an', mp4Out]);
  console.log(`saved ${mp4Out}: ${vn} frames, ${(vn / FPS).toFixed(1)} s, ${Math.round(fs.statSync(mp4Out).size / 1024)} KB`);
}

// The GIF cut: shorter, recorded at 960x540 and 15 fps, 3 px per frame, with larger captions. It loops without a jump:
// its first FADE frames of TODAY.html are moved to the end, where the resume dips into them.
if (gifOut) {
  console.log('gif cut (960x540, 15 fps, seamless loop):');
  await use(GIF);
  const G = 30;
  const g1 = await scene('g1-today', today, G, () => ({ y0: 0, n: 100, speed: 3, captions: [
    [0, 'TODAY.html: each role the crew kept. Nothing is sent until you approve it']] }));
  const g2 = await scene('g2-log', today, G, (m) => ({ y0: m.max - 3 * 66, n: 67, speed: 3, captions: [
    [0, 'Every form field, with its exact value and where it came from']] }));
  const g3 = await scene('g3-resume', resume, G, () => ({ y0: 0, n: 66, speed: 3, captions: [
    [0, 'A one-page resume for each role, from your own facts only']] }));
  // split g1 into its head (the loop's landing frames) and the rest
  const head = path.join(tmp, 'g1-head.mkv'), rest = path.join(tmp, 'g1-rest.mkv');
  run(['-i', g1.file, '-vf', `trim=start_frame=0:end_frame=${FADE},setpts=PTS-STARTPTS`, '-c:v', 'ffv1', '-pix_fmt', 'bgr0', head]);
  run(['-i', g1.file, '-vf', `trim=start_frame=${FADE},setpts=PTS-STARTPTS`, '-c:v', 'ffv1', '-pix_fmt', 'bgr0', rest]);
  var gn = join([{ file: rest, n: g1.n - FADE }, g2, g3, { file: head, n: FADE }], path.join(tmp, 'gif.mkv'));
  const pal = path.join(tmp, 'palette.png');
  run(['-i', path.join(tmp, 'gif.mkv'), '-vf', `palettegen=max_colors=${process.env.REC_COLORS || 64}:stats_mode=full`, pal]);
  run(['-i', path.join(tmp, 'gif.mkv'), '-i', pal, '-lavfi', `[0:v][1:v]paletteuse=dither=none:diff_mode=rectangle`, '-loop', '0', gifOut]);
  console.log(`saved ${gifOut}: ${gn} frames at ${FPS} fps, ${(gn / FPS).toFixed(1)} s, ${(fs.statSync(gifOut).size / 1048576).toFixed(2)} MB`);
}

await browser.close();
if (process.env.REC_KEEP) console.log('kept the frames in ' + tmp); else fs.rmSync(tmp, { recursive: true, force: true });
