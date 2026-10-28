'use strict';
// 생각이 많아지면 — scenes measured from the design screenshots (assets/scenes.json, built by tools/build_scenes.py).
// s runs from -1 (용기 100) through 0 (first screen, 50:50) to +1 (생각 100). Everything between two scenes is interpolated:
// the dividing line, the letter shapes (corner-to-corner, rings stay ellipses), the phrases, the numbers and the gutters.
const $ = id => document.getElementById(id), NS = 'http://www.w3.org/2000/svg';
const mix = (a, b, t) => a + (b - a) * t, clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const ease = t => mix(t, t * t * (3 - 2 * t), .3); // mostly even speed, a slight rest at each designed scene
// something that leaves fades out in the first half of a step, something that arrives fades in during the second half
const handover = (a, b, t) => a === b ? a : a > b ? mix(b, a, clamp(1 - 2 * t)) : mix(a, b, clamp(2 * t - 1));
const RATE_THOUGHT = 1 / 16, RATE_COURAGE = 1 / 10; // progress per second while the pointer stays on that side
let D = null, W = 1920, H = 1077;
let active = false, inside = false, s = 0, offset = 0, shown = 0, px = 960, py = 540, last = 0, lastKey = '';
let angle = -.511, targetAngle = -.511, compassOp = 1;
let line = { c: Math.cos(1), sn: Math.sin(1), t: 0 };
const dist = (x, y) => x * line.c + y * line.sn - line.t; // < 0 : black (생각) side

// ---------- regions ----------
function halfPlane(th, t, keep) { // polygon of the screen where keep(d) holds, d = signed distance from the line
    const c = Math.cos(th), sn = Math.sin(th), pts = [[-4, -4], [W + 4, -4], [W + 4, H + 4], [-4, H + 4]], out = [];
    for (let i = 0; i < 4; i++) {
        const a = pts[i], b = pts[(i + 1) % 4], da = a[0] * c + a[1] * sn - t, db = b[0] * c + b[1] * sn - t;
        if (keep(da)) out.push(a);
        if (keep(da) !== keep(db)) { const k = da / (da - db); out.push([mix(a[0], b[0], k), mix(a[1], b[1], k)]); }
    }
    return out.length ? 'M' + out.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('L') + 'Z' : 'M0 0Z';
}

// ---------- letters ----------
// Straight pieces: corner lists matched step by step (tools/scenes/build_scenes.py), so every in-between shape keeps
// straight edges. Rings (ㅇ): always true ellipses; only centre, radii and tilt move.
const glyphEls = { thought: [], courage: [] };
function buildGlyph(name, group) {
    D.rings[name][0].forEach(() => {
        const mk = () => { const e = document.createElementNS(NS, 'path'); e.setAttribute('fill-rule', 'evenodd'); group.append(e); return e; };
        const e = mk(); e.ghost = mk(); glyphEls[name].push(e);
    });
}
const f1 = v => v.toFixed(1);
// Ellipses are drawn as dense polygons: SVG half-arcs whose end points get rounded become ambiguous and make the
// ring jump between two solutions from frame to frame (the trembling).
const RING_N = 180, COS = [], SIN = [];
for (let k = 0; k < RING_N; k++) { COS.push(Math.cos(2 * Math.PI * k / RING_N)); SIN.push(Math.sin(2 * Math.PI * k / RING_N)); }
function ellipsePath([cx, cy, rx, ry, a]) {
    const r = a * Math.PI / 180, c = Math.cos(r), sn = Math.sin(r); let d = '';
    for (let k = 0; k < RING_N; k++) {
        const x = rx * COS[k], y = ry * SIN[k];
        d += (k ? 'L' : 'M') + (cx + x * c - y * sn).toFixed(2) + ' ' + (cy + x * sn + y * c).toFixed(2);
    }
    return d + 'Z';
}
function ellipseBox([cx, cy, rx, ry, a]) {
    const r = a * Math.PI / 180, c = Math.cos(r), sn = Math.sin(r);
    return [cx, cy, 2 * Math.hypot(rx * c, ry * sn), 2 * Math.hypot(rx * sn, ry * c)];
}
const COUNTER = { thought: { 4: 'L' }, courage: { 0: 'Rtop', 4: 'Rbot' } };
// Draws glyph `name` for step `step` (between scenes a and b) at t; returns the counter boxes [cx, cy, w, h].
function setGlyph(name, step, fa, fb, t) {
    const pieces = D.steps[step][name], ra = D.rings[name][fa], rb = D.rings[name][fb], boxes = {};
    pieces.forEach((pc, i) => {
        let d = '';
        if (pc === null) {
            const o = ra[i].o.map((v, k) => mix(v, rb[i].o[k], t)), c = ra[i].i.map((v, k) => mix(v, rb[i].i[k], t));
            d = ellipsePath(o) + ellipsePath(c);
            if (COUNTER[name][i]) boxes[COUNTER[name][i]] = ellipseBox(c);
        } else {
            const [A, B, slide] = pc, el = glyphEls[name][i];
            const poly = (P, dx, dy) => { let q = ''; for (let k = 0; k < P.length; k += 2) q += (k ? 'L' : 'M') + f1(P[k] * .5 + dx) + ' ' + f1(P[k + 1] * .5 + dy); return q + 'Z'; };
            if (slide) { // old shape slides out toward the corner and fades, new shape fades in where it belongs
                const u = clamp(t * 1.6);
                el.setAttribute('d', poly(B, 0, 0)); el.setAttribute('opacity', clamp((t - .25) / .6).toFixed(3));
                el.ghost.setAttribute('d', poly(A, 420 * u * u, 160 * u * u)); el.ghost.setAttribute('opacity', (1 - u).toFixed(3));
                return;
            }
            el.setAttribute('opacity', 1); el.ghost.setAttribute('d', 'M0 0Z');
            for (let k = 0; k < A.length; k += 2) d += (k ? 'L' : 'M') + f1((A[k] + (B[k] - A[k]) * t) * .5) + ' ' + f1((A[k + 1] + (B[k + 1] - A[k + 1]) * t) * .5);
            d += 'Z';
        }
        glyphEls[name][i].setAttribute('d', d);
    });
    return boxes;
}

// ---------- phrases and numbers (sized so their ink boxes match the screenshots) ----------
const ctx = document.createElement('canvas').getContext('2d');
function ink(str, family) { ctx.font = `100px ${family}`; const m = ctx.measureText(str); return { l: m.actualBoundingBoxLeft, r: m.actualBoundingBoxRight, a: m.actualBoundingBoxAscent, d: m.actualBoundingBoxDescent }; }
const phrases = {};
function buildPhrases() {
    for (const [key, [str, colour]] of Object.entries(D.phrases)) {
        const e = document.createElementNS(NS, 'text'); e.textContent = str; e.setAttribute('font-family', 'Pear'); e.setAttribute('opacity', 0);
        $('labels').append(e); // filled phrases: white + difference blend = always the opposite colour of what is underneath (outlined words are not inverted)
        phrases[key] = { e, m: ink(str, 'Pear'), n: [...str].length };
    }
}
// Pear text: size from the screenshot's ink height, natural letter shapes with slightly open tracking (no squeezing).
// Phrases that hug something on their right (를 잃는 법 → 용기, 를 가진다고, 있게 저지르셨군요!) keep their right edge.
const TRACK = .04; // extra space between letters, in em
const RIGHT_ANCHORED = new Set(['suffix', 'have', 'bold1', 'bold2']);
function placePhrase(p, box, op, right = false) {
    const [x0, y0, x1, y1] = box, perK = (p.m.l + p.m.r) + TRACK * 100 * (p.n - 1); // width per unit of k
    // as tall as the design, unless the opened spacing would overrun the designed width: then a touch smaller
    const k = Math.min((y1 - y0) / (p.m.a + p.m.d), (x1 - x0) * 1.03 / perK), size = 100 * k, ls = TRACK * size;
    const width = perK * k, left = right ? x1 - width : x0;
    p.e.setAttribute('font-size', size.toFixed(2)); p.e.setAttribute('letter-spacing', ls.toFixed(2));
    p.e.setAttribute('x', (left + p.m.l * k).toFixed(1)); p.e.setAttribute('y', (y0 + p.m.a * k).toFixed(1)); p.e.setAttribute('opacity', op.toFixed(3));
}
// ---------- outlined words that pop in one by one (no fade) ----------
const words = [];
function buildWords() {
    for (const w of D.words) {
        const e = document.createElementNS(NS, 'text'); e.textContent = w.text; e.setAttribute('font-family', 'Pear'); e.style.display = 'none';
        $('words').append(e);
        words.push({ ...w, e, p: { e, m: ink(w.text, 'Pear'), n: [...w.text].length }, k: 0 });
    }
}
// Words are always in place but hidden: a soft torch around the pointer reveals only what is near it (생각 side only).
// They sit at their 59 places, glide to their 89 places as 생각 grows, and stay there.
let torch = 0;
function updateWords(v, dt) {
    const [s59, s89] = D.wordScenes, u = ease(clamp((v - s59) / (s89 - s59)));
    for (const w of words) {
        const box = w.box ? w.box.map((x, i) => mix(x, w.box2[i], u)) : w.box2;
        placePhrase(w.p, box, 1); w.e.removeAttribute('opacity'); w.e.style.display = '';
        const cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2;
        w.e.setAttribute('transform', w.rot ? `rotate(${w.rot} ${cx} ${cy})` : '');
    }
    torch = mix(torch, active && inside ? 1 : 0, 1 - Math.exp(-dt * 6));
    const spot = $('torchSpot'), r = $('art').getBoundingClientRect(), k = (r.width / W) / (r.height / H);
    spot.setAttribute('cx', px.toFixed(1)); spot.setAttribute('cy', py.toFixed(1));
    spot.setAttribute('rx', (170 / Math.sqrt(k)).toFixed(1)); spot.setAttribute('ry', (170 * Math.sqrt(k)).toFixed(1));
    spot.setAttribute('opacity', torch.toFixed(3));
}
const nums = {};
function buildNumbers() {
    for (const [key, parent] of [['L', 'labels'], ['Rtop', 'labels'], ['Rbot', 'labels']]) {
        const e = document.createElementNS(NS, 'text'); e.setAttribute('font-family', 'Neurimbo'); e.setAttribute('opacity', 0); $(parent).append(e); nums[key] = e;
    }
}
function placeNumber(e, label, counter, rx, ry, h, op) {
    if (!counter || op < .002) { e.setAttribute('opacity', 0); return; }
    const str = String(label), m = ink(str, 'Neurimbo'), k = h / (m.a + m.d);
    const cx = counter[0] + rx * counter[2], cy = counter[1] + ry * counter[3];
    if (e.textContent !== str) e.textContent = str;
    e.setAttribute('font-size', (100 * k).toFixed(2));
    e.setAttribute('x', (cx - (m.r - m.l) * k / 2).toFixed(1)); e.setAttribute('y', (cy + (m.a - m.d) * k / 2).toFixed(1));
    e.setAttribute('opacity', op.toFixed(3));
}

// ---------- one frame ----------
function pair(v) { // -> [scene a, scene b, eased t, step index]
    const sc = D.scenes, n = sc.length;
    if (v <= sc[0].s) return [sc[0], sc[1], 0, 0];
    for (let i = 0; i < n - 1; i++) if (v <= sc[i + 1].s) return [sc[i], sc[i + 1], ease((v - sc[i].s) / (sc[i + 1].s - sc[i].s)), i];
    return [sc[n - 2], sc[n - 1], 1, n - 2];
}
function draw(v) {
    const [a, b, t, step] = pair(v), key = a.id + b.id + t.toFixed(4) + shown.toFixed(3);
    if (key === lastKey) return; lastKey = key;
    const th = mix(a.line[0], b.line[0], t) * Math.PI / 180, lt = mix(a.line[1], b.line[1], t);
    line = { c: Math.cos(th), sn: Math.sin(th), t: lt };
    const gapT = mix(a.gapT, b.gapT, t), gapC = mix(a.gapC, b.gapC, t), black = halfPlane(th, lt, d => d < 0);
    $('background').setAttribute('d', black); $('blackPath').setAttribute('d', black);
    $('whitePath').setAttribute('d', halfPlane(th, lt, d => d >= 0));
    $('thoughtPath').setAttribute('d', halfPlane(th, lt - gapT, d => d < 0));
    $('couragePath').setAttribute('d', halfPlane(th, lt + gapC, d => d > 0));
    const tb = setGlyph('thought', step, a.thought, b.thought, t), cb = setGlyph('courage', step, a.courage, b.courage, t);
    for (const k in phrases) {
        const A = a.text[k], B = b.text[k];
        placePhrase(phrases[k], [0, 1, 2, 3].map(i => mix(A[i], B[i], t)), handover(A[4], B[4], t), RIGHT_ANCHORED.has(k));
    }
    const L = [0, 1, 2, 3, 4].map(i => mix(a.num.L[i], b.num.L[i], t));
    placeNumber(nums.L, Math.round(L[0]), tb.L, L[1], L[2], L[3], shown * handover(a.num.L[4], b.num.L[4], t));
    const R = [0, 1, 2, 3, 4, 5].map(i => mix(a.num.R[i], b.num.R[i], t)), label = Math.round(R[0]);
    // the 용기 number sits in the top ㅇ on the 생각 side and in the bottom ㅇ on the 용기 side; it crossfades between them
    const rel = top => { const ia = a.num.R[5] === top, ib = b.num.R[5] === top, A = a.num.R, B = b.num.R;
        return ia && ib ? [mix(A[1], B[1], t), mix(A[2], B[2], t)] : ia ? [A[1], A[2]] : ib ? [B[1], B[2]] : [0, 0]; };
    const rt = rel(1), rb = rel(0);
    const vis = handover(a.num.R[4], b.num.R[4], t), top = handover(a.num.R[5], b.num.R[5], t), bot = handover(1 - a.num.R[5], 1 - b.num.R[5], t);
    placeNumber(nums.Rtop, label, cb.Rtop, rt[0], rt[1], R[3], shown * vis * top);
    placeNumber(nums.Rbot, label, cb.Rbot, rb[0], rb[1], R[3], shown * vis * bot);
    // compass: half white / half black disc in the middle of the line, shown only before the first click
    compassOp = active ? 0 : 1; // only on the first screen, gone the moment the piece starts (no fade)
    const hits = []; const c = Math.cos(th), sn = Math.sin(th);
    for (const x of [0, W]) { const y = (lt - x * c) / sn; if (y >= 0 && y <= H) hits.push([x, y]); }
    for (const y of [0, H]) { const x = (lt - y * sn) / c; if (x >= 0 && x <= W) hits.push([x, y]); }
    compassAt = hits.length >= 2 ? [(hits[0][0] + hits[1][0]) / 2, (hits[0][1] + hits[1][1]) / 2] : null;
}
let compassAt = null;
function drawCompass(dt) {
    angle += Math.atan2(Math.sin(targetAngle - angle), Math.cos(targetAngle - angle)) * (1 - Math.exp(-dt * 8));
    const g = $('compass');
    if (!compassAt || compassOp < .002) { g.setAttribute('opacity', 0); return; }
    // the drawing is stretched with the screen, so undo that for the disc to stay round
    const r = $('art').getBoundingClientRect(), k = (r.width / W) / (r.height / H);
    g.setAttribute('transform', `translate(${compassAt[0].toFixed(1)} ${compassAt[1].toFixed(1)}) scale(${(1 / Math.sqrt(k)).toFixed(4)} ${Math.sqrt(k).toFixed(4)}) rotate(${(angle * 180 / Math.PI).toFixed(2)})`);
    g.setAttribute('opacity', compassOp.toFixed(3));
}

// ---------- interaction ----------
function tick(time) {
    const dt = Math.min(.05, (time - last) / 1000 || 0); last = time;
    if (D) {
        const d = dist(px, py);
        if (active && inside) s = clamp(s + (d < 0 ? RATE_THOUGHT : -RATE_COURAGE) * dt, -1, 1);
        // (no pointer-depth nudge: it fed back through the moving line and made the rings tremble)
        offset = 0;
        shown = mix(shown, active ? 1 : 0, 1 - Math.exp(-dt * 3)); if (Math.abs(shown - (active ? 1 : 0)) < .001) shown = active ? 1 : 0;
        const v = clamp(s + offset * (1 - Math.abs(s)), -1, 1); draw(v); drawCompass(dt); updateWords(v, dt);
    }
    requestAnimationFrame(tick);
}
function move(e) {
    const r = $('art').getBoundingClientRect(), nx = (e.clientX - r.left) / r.width * W, ny = (e.clientY - r.top) / r.height * H;
    if (Math.hypot(nx - px, ny - py) > 1) targetAngle = Math.atan2(ny - py, nx - px); // the disc turns toward where the pointer heads
    px = nx; py = ny; inside = true;
    const dot = $('cursorDot'); dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px'; dot.style.opacity = e.pointerType === 'touch' ? '0' : '1';
}
$('art').addEventListener('pointermove', move);
$('art').addEventListener('pointerleave', () => { inside = false; $('cursorDot').style.opacity = 0; });
function start() { active = true; inside = true; $('start').hidden = true; $('compass').setAttribute('opacity', 0); compassOp = 0; }
function reset() { active = false; s = 0; offset = 0; $('start').hidden = false; }
$('start').addEventListener('pointerdown', e => { move(e); start(); });
$('start').addEventListener('click', () => { if (!active) start(); });
$('reset').addEventListener('click', reset);
document.addEventListener('keydown', e => { if (e.key.toLowerCase() === 'r' || e.key === 'Escape') reset(); });
document.addEventListener('visibilitychange', () => { inside = false; $('cursorDot').style.opacity = 0; });
Promise.all([fetch('assets/scenes.json').then(r => { if (!r.ok) throw Error('scenes'); return r.json(); }),
             document.fonts.load('100px Pear', '이 많아지면'), document.fonts.load('100px Neurimbo', '0123456789')]).then(([data]) => {
    D = data; W = D.W; H = D.H;
    buildGlyph('thought', $('thought')); buildGlyph('courage', $('bravery')); buildPhrases(); buildNumbers(); buildWords(); draw(0);
}).catch(() => { const h = $('help'); h.hidden = false; h.textContent = '파일을 불러오지 못했어요. 새로고침해 주세요.'; });
requestAnimationFrame(tick);
