'use strict';
// 생각이 많아지면 — scenes measured from the design screenshots (assets/scenes.json, built by tools/build_scenes.py).
// s runs from -1 (용기 100) through 0 (first screen, 50:50) to +1 (생각 100). Everything between two scenes is interpolated:
// the dividing line, the letter shapes (point-by-point morph), the phrases, the numbers and the gutters along the line.
const $ = id => document.getElementById(id), NS = 'http://www.w3.org/2000/svg';
const mix = (a, b, t) => a + (b - a) * t, clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const ease = t => t * t * (3 - 2 * t); // each designed scene is a gentle resting point
// something that leaves fades out in the first half of a step, something that arrives fades in during the second half
const handover = (a, b, t) => a === b ? a : a > b ? mix(b, a, clamp(1 - 2 * t)) : mix(a, b, clamp(2 * t - 1));
const RATE_THOUGHT = 1 / 8, RATE_COURAGE = 1 / 10; // progress per second while the pointer stays on that side
let D = null, W = 1920, H = 1077;
let active = false, inside = false, s = 0, offset = 0, shown = 0, px = 960, py = 540, last = 0, lastKey = '';
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
const glyphEls = { thought: [], courage: [] };
function buildGlyph(name, group) {
    D[name][0].forEach(() => { const e = document.createElementNS(NS, 'path'); e.setAttribute('fill-rule', 'evenodd'); group.append(e); glyphEls[name].push(e); });
}
// Draws the morph between frames fa and fb; returns the boxes [cx, cy, w, h] of the requested counters (ㅇ holes).
function setGlyph(name, fa, fb, t, wanted) {
    const A = D[name][fa], B = D[name][fb], boxes = {};
    A.forEach((piece, pi) => {
        let d = '';
        piece.forEach((a, si) => {
            const b = B[pi][si], key = pi + ':' + si, want = wanted[key];
            let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
            for (let k = 0; k < a.length; k += 2) {
                const x = (a[k] + (b[k] - a[k]) * t) * .5, y = (a[k + 1] + (b[k + 1] - a[k + 1]) * t) * .5;
                d += (k ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
                if (want) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
            }
            d += 'Z'; if (want) boxes[want] = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0];
        });
        glyphEls[name][pi].setAttribute('d', d);
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
        (colour === 'white' ? $('blackText') : $('whiteText')).append(e);
        phrases[key] = { e, m: ink(str, 'Pear'), n: [...str].length };
    }
}
function placePhrase(p, box, op) {
    const [x0, y0, x1, y1] = box, k = (y1 - y0) / (p.m.a + p.m.d), size = 100 * k;
    const ls = p.n > 1 ? ((x1 - x0) - (p.m.l + p.m.r) * k) / (p.n - 1) : 0;
    p.e.setAttribute('font-size', size.toFixed(2)); p.e.setAttribute('letter-spacing', ls.toFixed(2));
    p.e.setAttribute('x', (x0 + p.m.l * k).toFixed(1)); p.e.setAttribute('y', (y0 + p.m.a * k).toFixed(1)); p.e.setAttribute('opacity', op.toFixed(3));
}
const nums = {};
function buildNumbers() {
    for (const [key, parent] of [['L', 'blackText'], ['Rtop', 'whiteText'], ['Rbot', 'whiteText']]) {
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
function pair(v) {
    const sc = D.scenes;
    if (v <= sc[0].s) return [sc[0], sc[0], 0];
    for (let i = 0; i < sc.length - 1; i++) if (v <= sc[i + 1].s) return [sc[i], sc[i + 1], ease((v - sc[i].s) / (sc[i + 1].s - sc[i].s))];
    const z = sc[sc.length - 1]; return [z, z, 0];
}
function draw(v) {
    const [a, b, t] = pair(v), key = a.id + b.id + t.toFixed(4) + shown.toFixed(3);
    if (key === lastKey) return; lastKey = key;
    const th = mix(a.line[0], b.line[0], t) * Math.PI / 180, lt = mix(a.line[1], b.line[1], t);
    line = { c: Math.cos(th), sn: Math.sin(th), t: lt };
    const gapT = mix(a.gapT, b.gapT, t), gapC = mix(a.gapC, b.gapC, t), black = halfPlane(th, lt, d => d < 0);
    $('background').setAttribute('d', black); $('blackPath').setAttribute('d', black);
    $('whitePath').setAttribute('d', halfPlane(th, lt, d => d >= 0));
    $('thoughtPath').setAttribute('d', halfPlane(th, lt - gapT, d => d < 0));
    $('couragePath').setAttribute('d', halfPlane(th, lt + gapC, d => d > 0));
    const ct = D.counters, tb = setGlyph('thought', a.thought, b.thought, t, { [ct.thought.join(':')]: 'L' });
    const cb = setGlyph('courage', a.courage, b.courage, t, { [ct.courageTop.join(':')]: 'Rtop', [ct.courageBottom.join(':')]: 'Rbot' });
    for (const k in phrases) {
        const A = a.text[k], B = b.text[k];
        placePhrase(phrases[k], [0, 1, 2, 3].map(i => mix(A[i], B[i], t)), handover(A[4], B[4], t));
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
}

// ---------- interaction ----------
function tick(time) {
    const dt = Math.min(.05, (time - last) / 1000 || 0); last = time;
    if (D) {
        const d = dist(px, py);
        if (active && inside) s = clamp(s + (d < 0 ? RATE_THOUGHT : -RATE_COURAGE) * dt, -1, 1);
        // the deeper the pointer sits in one side, the more the scene leans toward that side
        offset = mix(offset, active && inside ? clamp(-d / H * .4, -.12, .12) : 0, 1 - Math.exp(-dt * 4));
        shown = mix(shown, active ? 1 : 0, 1 - Math.exp(-dt * 3)); if (Math.abs(shown - (active ? 1 : 0)) < .001) shown = active ? 1 : 0;
        draw(clamp(s + offset * (1 - Math.abs(s)), -1, 1));
    }
    requestAnimationFrame(tick);
}
function move(e) {
    const r = $('art').getBoundingClientRect(); px = (e.clientX - r.left) / r.width * W; py = (e.clientY - r.top) / r.height * H; inside = true;
    const dot = $('cursorDot'); dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px'; dot.style.opacity = e.pointerType === 'touch' ? '0' : '1';
}
$('art').addEventListener('pointermove', move);
$('art').addEventListener('pointerleave', () => { inside = false; $('cursorDot').style.opacity = 0; });
function start() { active = true; inside = true; $('start').hidden = true; }
function reset() { active = false; s = 0; offset = 0; $('start').hidden = false; }
$('start').addEventListener('pointerdown', e => { move(e); start(); });
$('start').addEventListener('click', () => { if (!active) start(); });
$('reset').addEventListener('click', reset);
document.addEventListener('keydown', e => { if (e.key.toLowerCase() === 'r' || e.key === 'Escape') reset(); });
document.addEventListener('visibilitychange', () => { inside = false; $('cursorDot').style.opacity = 0; });
Promise.all([fetch('assets/scenes.json').then(r => { if (!r.ok) throw Error('scenes'); return r.json(); }),
             document.fonts.load('100px Pear', '이 많아지면'), document.fonts.load('100px Neurimbo', '0123456789')]).then(([data]) => {
    D = data; W = D.W; H = D.H;
    buildGlyph('thought', $('thought')); buildGlyph('courage', $('bravery')); buildPhrases(); buildNumbers(); draw(0);
}).catch(() => { const h = $('help'); h.hidden = false; h.textContent = '파일을 불러오지 못했어요. 새로고침해 주세요.'; });
requestAnimationFrame(tick);
