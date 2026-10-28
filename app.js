'use strict';
const $ = id => document.getElementById(id), NS = 'http://www.w3.org/2000/svg';
const mix = (a, b, t) => a + (b - a) * t, clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const ratios = [.5, .56, .65, .75, .85, .90, .95, 1];
const slopes = [-570 / 1016, -.5, -.60, -.8, -.83, -.56, -.35, -.35];
const scales = [.46, .53, .59, .59, .59, .59, .59, .59];
// Glyph data (assets/glyphs.json, built by tools/build_glyphs.py) is in pixels of the reference screen picture.
// SX/SY convert those pixels to this 1016×570 viewBox, so on a screen of the reference size it matches pixel for pixel.
let glyphs, SX = 1016 / 1526, SY = 570 / 848;
let active = false, p = 0, dwell = 0, inside = false, hover = false, px = 508, py = 285, originX = 508, originY = 285, angle = -.511, targetAngle = -.511, offset = 0, slope = slopes[0], intercept = 570, last = 0;
function artwork(name, x, y, w, h, outlined = false) {
    const spec = typography[name], e = document.createElementNS(NS, 'svg');
    // 'meet' keeps the original letter proportions; overflow visible prevents glyph edges from being cut.
    for (const [k, v] of Object.entries({ x, y, width: w, height: h, viewBox: spec.viewBox.join(' '), preserveAspectRatio: 'xMinYMin meet', overflow: 'visible' })) e.setAttribute(k, v);
    // 'rotate' = ordinary horizontal lines turned 90° clockwise (not vertical writing).
    const holder = spec.rotate ? document.createElementNS(NS, 'g') : e; if (spec.rotate) { holder.setAttribute('transform', 'rotate(90)'); e.append(holder); }
    spec.lines.forEach((line, i) => {
        const text = document.createElementNS(NS, 'text'); text.textContent = line;
        text.setAttribute('x', 0); text.setAttribute('y', i * 110); text.setAttribute('font-family', spec.family); text.setAttribute('font-size', 100); text.setAttribute('font-weight', 400);
        text.setAttribute('fill', outlined ? 'none' : (['courage', 'suffix', 'courageMore'].includes(name) ? 'black' : '#ffffff'));
        if (outlined) { text.setAttribute('stroke', '#aaa'); text.setAttribute('stroke-width', .65); text.setAttribute('vector-effect', 'non-scaling-stroke'); }
        holder.append(text);
    }); return e;
}
// 생각 / 용기 letters: one <path> per piece (holes via even-odd), shapes interpolated between keyframes.
const glyphEls = {}, shapeCache = {};
function buildGlyph(name, group) {
    glyphEls[name] = glyphs.glyphs[name].frames[0].map(() => { const e = document.createElementNS(NS, 'path'); e.setAttribute('fill-rule', 'evenodd'); group.append(e); return e; });
}
// f = keyframe position (0 … count-1). Returns the box [cx, cy, w, h] of the ㅇ counter that holds the number.
function setGlyph(name, f) {
    const g = glyphs.glyphs[name], F = g.frames.length; f = clamp(f, 0, F - 1);
    const cached = shapeCache[name]; if (cached && Math.abs(cached.f - f) < 1e-4) return cached.counter;
    const a = Math.min(F - 1, Math.floor(f)), b = Math.min(F - 1, a + 1), t = f - a; let counter = null;
    g.frames[a].forEach((piece, pi) => {
        let d = '';
        piece.forEach((A, si) => {
            const B = g.frames[b][pi][si], isCounter = g.counter && pi === g.counter[0] && si === g.counter[1];
            let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
            for (let k = 0; k < A.length; k += 2) {
                const x = A[k] + (B[k] - A[k]) * t, y = A[k + 1] + (B[k + 1] - A[k + 1]) * t;
                d += (k ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
                if (isCounter) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
            }
            d += 'Z'; if (isCounter) counter = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0];
        });
        glyphEls[name][pi].setAttribute('d', d);
    });
    shapeCache[name] = { f, counter }; return counter;
}
const suffixArtwork = artwork('suffix', 0, 0, 234, 74); suffixArtwork.setAttribute('id', 'suffix'); suffixArtwork.setAttribute('opacity', 0); $('braveryText').append(suffixArtwork);
// Shown when the 용기 side reaches 55% or more: "용기가 많아진다고 / 생각을 잃진 않으니까".
// Plain <text> so the real glyph edges can be measured for exact left/right alignment.
function plainText(str, size, fill) { const t = document.createElementNS(NS, 'text'); t.textContent = str; t.setAttribute('font-family', 'Pear'); t.setAttribute('font-size', size); t.setAttribute('fill', fill); t.setAttribute('opacity', 0); return t; }
const NOTLOSE_SIZE = 50; // '을 잃진 않으니까' font size
const courageMore = plainText('많아진다고', 58, 'black'); $('braveryText').append(courageMore);
const notLose = plainText('을 잃진 않으니까', NOTLOSE_SIZE, '#ffffff'); $('words').after(notLose);
// Left-align "을 잃진 않으니까" under 생각, right-align "많아진다고" above 용기.
// Canvas measureText gives true ink bounds (SVG getBBox includes empty ascent space), so both gaps match exactly.
const inkCtx = document.createElement('canvas').getContext('2d'), GAP = 25;
function ink(str, size, family) { inkCtx.font = `${size}px ${family}`; return inkCtx.measureText(str); }
// thoughtBox / courageBox: where the letters sit on screen right now, [x, y, w, h] in viewBox units.
function alignPhrases(thoughtBox, courageBox, cs) {
    const m = ink(notLose.textContent, NOTLOSE_SIZE, 'Pear');
    notLose.setAttribute('x', thoughtBox[0] + m.actualBoundingBoxLeft); notLose.setAttribute('y', thoughtBox[1] + thoughtBox[3] + GAP + m.actualBoundingBoxAscent);
    const size = 58 * cs, m2 = ink(courageMore.textContent, size, 'Pear'); courageMore.setAttribute('font-size', size);
    courageMore.setAttribute('x', courageBox[0] + courageBox[2] - m2.actualBoundingBoxRight); courageMore.setAttribute('y', courageBox[1] - GAP * cs - m2.actualBoundingBoxDescent);
}
let q = 0;
const words = [
    ['increases', 465, 139, 234, 66, 0.08],
    ['worry', 104, 269, 193, 137, 0.10],
    ['top', 350, 32, 271, 59, .24],
    ['lost', 112, 429, 337, 108, .37],
    ['hesitate', 522, 233, 457, 58, .38],
    ['failure', 522, 300, 300, 57, .51],
    ['vertical', 370, 228, 87, 195, .66],
    ['hmm', 522, 369, 264, 60, .68],
    ['ambiguous', 522, 442, 464, 57, .82],
    ['more', 522, 145, 371, 68, .97]
].map(([name, x, y, w, h, at]) => { let e = artwork(name, x, y, w, h, !['increases', 'more'].includes(name)); $('words').append(e); return { name, e, at, w }; });
const chunks = { top: ['어떡하지', '어떡하지 음…'], hesitate: ['할까말까', '할까말까 확신이', '할까말까 확신이 안서긴 해'], hmm: ['흠…', '흠… 아닌가?'], ambiguous: ['애매하긴 해', '애매하긴 해 잘', '애매하긴 해 잘 모르겠네..'] };
// Percent numbers sit in the middle of each word's ㅇ counter (생각: its ㅇ, 용기: the ㅇ of 용).
function makeNumber(group) { const e = document.createElementNS(NS, 'text'); e.setAttribute('fill', 'white'); e.setAttribute('font-family', 'Neurimbo'); group.append(e); return e; }
const leftNum = makeNumber($('leftNumber')), rightNum = makeNumber($('rightNumber'));
function setNumber(e, n, at) {
    if (!at) return 0; const s = String(n), size = Math.min(28, at[2] * .42); if (size < 9) return 0;
    if (e.textContent !== s) e.textContent = s; e.setAttribute('font-size', size.toFixed(2));
    const m = ink(s, size, 'Neurimbo');
    e.setAttribute('x', (at[0] - (m.actualBoundingBoxRight - m.actualBoundingBoxLeft) / 2).toFixed(2));
    e.setAttribute('y', (at[1] + (m.actualBoundingBoxAscent - m.actualBoundingBoxDescent) / 2).toFixed(2)); return 1;
}
function area(m, b) { let points = [[0, 0], [1016, 0], [1016, 570], [0, 570]], out = []; for (let i = 0; i < 4; i++) { let a = points[i], c = points[(i + 1) % 4], fa = a[1] - m * a[0] - b, fc = c[1] - m * c[0] - b; if (fa <= 0) out.push(a); if ((fa <= 0) !== (fc <= 0)) { let t = fa / (fa - fc); out.push([mix(a[0], c[0], t), mix(a[1], c[1], t)]); } } let sum = 0; for (let i = 0; i < out.length; i++) { let a = out[i], c = out[(i + 1) % out.length]; sum += a[0] * c[1] - c[0] * a[1]; } return { fraction: Math.abs(sum) / 2 / (1016 * 570), points: out }; }
function boundary(m, r) { let lo = -1200, hi = 2000; for (let i = 0; i < 34; i++) { let b = (lo + hi) / 2; if (area(m, b).fraction < r) lo = b; else hi = b; } return (lo + hi) / 2; }
function fadeAt(x, at, width = .045) { return clamp((x - at) / width); }
// shown: numbers and the compass stay hidden on the first screen and fade in once the piece starts.
let shown = 0;
function draw(dt) {
    const stage = p * 7, i = Math.min(6, Math.floor(stage)), t = stage - i;
    slope = mix(slopes[i], slopes[i + 1], t);
    const movement = active ? clamp((slope * px + intercept - py) / 570 * .30, -.15, .15) : 0;
    offset = mix(offset, movement, 1 - Math.exp(-dt * 4));
    shown = mix(shown, active ? 1 : 0, 1 - Math.exp(-dt * 3));
    const r = clamp(mix(ratios[i], ratios[i + 1], t) + offset * (1 - p), .35, 1);
    q = mix(q, Math.round((1 - r) * 100) >= 55 ? 1 : 0, 1 - Math.exp(-dt * 2.5));
    const qv = q * (1 - fadeAt(p, .03, .05)); courageMore.setAttribute('opacity', qv); notLose.setAttribute('opacity', qv);
    intercept = boundary(slope, r);
    const shape = area(slope, intercept).points; const d = 'M' + shape.map(a => a.join(' ')).join('L') + 'Z';
    $('background').setAttribute('d', d); $('blackPath').setAttribute('d', d);
    $('whitePath').setAttribute('d', `M0 0H1016V570H0Z ${d}`); $('whitePath').setAttribute('clip-rule', 'evenodd');
    // 생각: top-left corner fixed where the first screen puts it; grows with the stage (and slowly while hovered).
    const TG = glyphs && glyphs.glyphs.thought; let thoughtBox = null, leftAt = null;
    if (TG) {
        const tk = mix(scales[i], scales[i + 1], t) / scales[0] * (1 + (tb - 1) * (1 - p));
        const counter = setGlyph('thought', clamp(stage / 5) * (TG.frames.length - 1));
        const tx = TG.at[0] * SX, ty = TG.at[1] * SY, kx = SX * tk, ky = SY * tk;
        $('thought').setAttribute('transform', `translate(${tx} ${ty}) scale(${kx} ${ky})`);
        thoughtBox = [tx, ty, TG.size[0] * kx, TG.size[1] * ky];
        if (counter) leftAt = [tx + counter[0] * kx, ty + counter[1] * ky, counter[2] * kx];
    }
    words.forEach(({ e, name, at }) => {
        let opacity = name === 'more' ? fadeAt(p, .96, .03) : fadeAt(p, at); if (name === 'increases') opacity *= 1 - fadeAt(p, .97, .03); e.setAttribute('opacity', opacity);
        if (name === 'increases') { e.setAttribute('x', mix(465, 522, clamp(stage - 1))); e.setAttribute('y', mix(139, 154, clamp(stage - 1))); }
        if (name === 'hesitate') e.setAttribute('width', 457);
    });
    // Reveal longer thoughts in whole word chunks, so no letter is ever cut in half.
    const reveals = { top: fadeAt(p, .5, .08), hesitate: fadeAt(p, .65, .06), hmm: fadeAt(p, .82, .06), ambiguous: fadeAt(p, .97, .03) };
    words.forEach(({ name, e }) => { if (!(name in chunks)) return; const c = chunks[name], k = Math.min(c.length - 1, Math.floor(reveals[name] * c.length)); const tx = e.querySelector('text'); if (tx.textContent !== c[k]) tx.textContent = c[k]; });
    // 용기: shrinks toward the bottom-right corner as 생각 takes over; hover growth expands it up and left.
    const courageScales = [1, .84, .70, .62, .43, .27, .25, 0], base = mix(courageScales[i], courageScales[i + 1], t);
    const bx = mix([574, 650, 695, 716, 775, 817, 825, 930][i], [574, 650, 695, 716, 775, 817, 825, 930][i + 1], t);
    const by = mix([354, 378, 399, 410, 430, 450, 467, 560][i], [354, 378, 399, 410, 430, 450, 467, 560][i + 1], t);
    const cs = base * Math.min(1.3, cb * (1 + .2 * q)), CG = glyphs && glyphs.glyphs.courage; let courageBox = null, rightAt = null;
    if (CG) {
        const counter = setGlyph('courage', 0), w = CG.size[0] * SX, h = CG.size[1] * SY;
        // Bottom-right corner: equals the first-screen position at stage 0, then follows the original path to (930, 560).
        const right = bx + 309 * base + (CG.at[0] * SX + w - 883) * base, bottom = by + 115 * base + (CG.at[1] * SY + h - 469) * base;
        const x = right - w * cs, y = bottom - h * cs;
        $('bravery').setAttribute('transform', `translate(${x} ${y}) scale(${SX * cs} ${SY * cs})`);
        courageBox = [x, y, w * cs, h * cs];
        if (counter) rightAt = [x + counter[0] * SX * cs, y + counter[1] * SY * cs, counter[2] * SX * cs];
        // '를 잃는 법' sits just above 용기, right edges aligned.
        const sw = 234 * cs, sh = 74 * cs, sfx = $('suffix');
        sfx.setAttribute('x', right - sw); sfx.setAttribute('y', y - sh - 8 * cs); sfx.setAttribute('width', Math.max(sw, .001)); sfx.setAttribute('height', Math.max(sh, .001));
    }
    $('suffix').setAttribute('opacity', fadeAt(p, .08) * (1 - q));
    if (qv > 0.001 && thoughtBox && courageBox) alignPhrases(thoughtBox, courageBox, cs);
    const n = Math.round(r * 100);
    $('leftNumber').setAttribute('opacity', shown * setNumber(leftNum, n, leftAt));
    $('rightNumber').setAttribute('opacity', shown * setNumber(rightNum, 100 - n, rightAt));
    // Place the compass halfway along the visible dividing line.
    const hits = []; for (const x of [0, 1016]) { const y = slope * x + intercept; if (y >= 0 && y <= 570) hits.push([x, y]); } for (const y of [0, 570]) { const x = (y - intercept) / slope; if (x >= 0 && x <= 1016) hits.push([x, y]); }
    let cx = 508, cy = 285; if (hits.length >= 2) { cx = (hits[0][0] + hits[1][0]) / 2; cy = (hits[0][1] + hits[1][1]) / 2; }
    angle += Math.atan2(Math.sin(targetAngle - angle), Math.cos(targetAngle - angle)) * (1 - Math.exp(-dt * 8));
    $('compass').setAttribute('transform', `translate(${cx} ${cy}) rotate(${angle * 180 / Math.PI})`); $('compass').setAttribute('opacity', shown * (1 - fadeAt(p, .975, .025)));
    hover = inside && py < slope * px + intercept;
}
// tb/cb: slow hover growth of the 생각 / 용기 typography (up to +25%), easing back when the pointer leaves.
let tb = 1, cb = 1;
function tick(time) {
    const dt = Math.min(.05, (time - last) / 1000 || 0); last = time;
    tb = active && hover ? Math.min(1.12, tb + dt * .04) : Math.max(1, tb - dt * .15);
    cb = active && inside && !hover ? Math.min(1.25, cb + dt * .06) : Math.max(1, cb - dt * .15);
    if (active && hover && p < 1) { dwell += dt; p = clamp(p + dt / 8); } else if (!hover) { dwell = 0; if (active && inside) p = clamp(p - dt / 12); } draw(dt); requestAnimationFrame(tick);
}
function move(e) { const r = $('art').getBoundingClientRect(), nx = (e.clientX - r.left) / r.width * 1016, ny = (e.clientY - r.top) / r.height * 570; const dx = nx - px, dy = ny - py; if (Math.hypot(dx, dy) > .5) targetAngle = Math.atan2(dy, dx); px = nx; py = ny; inside = true; const dot = $('cursorDot'); dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px'; dot.style.opacity = e.pointerType === 'touch' ? '0' : '1'; }
$('art').addEventListener('pointermove', move); $('art').addEventListener('pointerleave', () => { inside = false; hover = false; dwell = 0; $('cursorDot').style.opacity = 0; });
function start() { active = true; originX = px; originY = py; inside = true; $('start').hidden = true; $('help').style.opacity = 0; }
function reset() { active = false; p = 0; tb = 1; cb = 1; dwell = 0; offset = 0; $('start').hidden = false; $('help').style.opacity = 1; }
$('start').addEventListener('pointerdown', e => { move(e); start(); }); $('start').addEventListener('click', () => { if (!active) { px = 200; py = 150; start(); } }); $('reset').addEventListener('click', reset);
document.addEventListener('keydown', e => { if (e.key.toLowerCase() === 'r' || e.key === 'Escape') reset(); });
document.addEventListener('visibilitychange', () => { inside = false; hover = false; dwell = 0; $('cursorDot').style.opacity = 0; });
fetch('assets/glyphs.json').then(r => { if (!r.ok) throw Error('glyph load'); return r.json(); }).then(data => {
    glyphs = data; SX = 1016 / data.design[0]; SY = 570 / data.design[1];
    buildGlyph('thought', $('thought')); buildGlyph('courage', $('bravery')); draw(0);
}).catch(() => { $('help').textContent = '글자 파일을 불러오지 못했어요. 새로고침해 주세요.'; });
requestAnimationFrame(tick);
