#!/usr/bin/env python3
"""SVG 읽기·외곽선 재분할 도우미 (tools/scenes/ 가 가져다 씀). 단독 실행용 예전 변환기는 더 이상 쓰지 않습니다.

(예전 설명) 글자 키프레임 SVG → assets/glyphs.json (글자 변형 데이터)

키프레임 SVG 규칙
  - 윤곽선 만들기(Create Outlines) 한 모양만. <text>(폰트 글자)는 안 됩니다.
  - 획(stroke)으로 그린 선은 '확장(Expand)'해서 면으로 만들어 주세요.
  - 같은 글자의 키프레임끼리는 조각 수가 같아야 합니다 (예: 용기 = 고리 2 + 막대 + 기둥 2 + 기 2 = 7조각).
    조각 안의 구멍 수도 같아야 합니다 (ㅇ = 바깥 + 안쪽 구멍).
  - 앵커 포인트 개수·순서는 맞출 필요 없습니다. 여기서 모든 외곽선을 같은 점 개수로 다시 나눠 맞춥니다.

설정은 아래 GLYPHS. 'unit' = SVG 1단위가 기준 화면(1526×848 그림)에서 몇 px인지,
'at' = 첫 키프레임의 왼쪽 위 모서리가 기준 화면에서 놓이는 위치(px).

실행: python3 tools/build_glyphs.py
"""
import json, math, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DESIGN = [1526, 848]  # 기준 화면(px) — 이 크기의 화면에서 그림과 픽셀 단위로 일치
GLYPHS = {
    'thought': {'files': ['assets/glyphs/생각0단계_트레이스.svg'], 'unit': 1.0, 'at': [38.0, 44.2], 'counter': 'top'},
    'courage': {'files': ['assets/glyphs/용기0단계.svg'], 'unit': 0.7944, 'at': [1004.4, 364.75], 'counter': 'top'},
}
SPACING = 2.0     # 다시 나눌 때 점 간격(기준 화면 px)
CORNER_DEG = 12   # 이 각도 이상 꺾이는 점은 모서리로 보고 정확히 보존

NUM = r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'


def fail(msg):
    sys.exit('오류: ' + msg)


# ---------- transforms ----------
def mat(a=1, b=0, c=0, d=1, e=0, f=0):
    return np.array([[a, c, e], [b, d, f], [0, 0, 1]], float)


def parse_transform(s):
    m = mat()
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', s or ''):
        v = [float(x) for x in re.findall(NUM, args)]
        if name == 'matrix':
            t = mat(*v)
        elif name == 'translate':
            t = mat(e=v[0], f=v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            t = mat(a=v[0], d=v[1] if len(v) > 1 else v[0])
        elif name == 'rotate':
            r = math.radians(v[0]); co, si = math.cos(r), math.sin(r)
            t = mat(co, si, -si, co)
            if len(v) == 3:
                t = mat(e=v[1], f=v[2]) @ t @ mat(e=-v[1], f=-v[2])
        elif name == 'skewX':
            t = mat(c=math.tan(math.radians(v[0])))
        elif name == 'skewY':
            t = mat(b=math.tan(math.radians(v[0])))
        else:
            fail(f'알 수 없는 transform: {name}')
        m = m @ t
    return m


def apply(m, pts):
    p = np.asarray(pts, float)
    return p @ m[:2, :2].T + m[:2, 2]


# ---------- path flattening ----------
def cubic(p0, p1, p2, p3):
    L = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
    n = max(6, math.ceil(L / 1.0))
    t = np.linspace(0, 1, n + 1)[1:, None]
    p0, p1, p2, p3 = map(np.array, (p0, p1, p2, p3))
    return list((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def parse_path(d):
    toks = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|' + NUM, d)
    i, cmd, subs, cur = 0, None, [], None
    pos = start = (0.0, 0.0); prev_c = prev_q = None

    def nums(k):
        nonlocal i
        v = [float(x) for x in toks[i:i + k]]; i += k
        return v

    while i < len(toks):
        if re.fullmatch('[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                if cur and len(cur) > 2: subs.append(cur)
                cur = None; pos = start; prev_c = prev_q = None
                continue
        if cmd is None: fail('path 데이터가 명령어로 시작하지 않습니다')
        rel = cmd.islower(); C = cmd.upper(); ox, oy = pos if rel else (0.0, 0.0)
        if C == 'M':
            x, y = nums(2); pos = start = (ox + x, oy + y)
            if cur and len(cur) > 2: subs.append(cur)
            cur = [pos]; cmd = 'l' if rel else 'L'; prev_c = prev_q = None
            continue
        if cur is None: cur = [pos]
        if C == 'L':
            x, y = nums(2); pos = (ox + x, oy + y); cur.append(pos); prev_c = prev_q = None
        elif C == 'H':
            (x,) = nums(1); pos = (ox + x if rel else x, pos[1]); cur.append(pos); prev_c = prev_q = None
        elif C == 'V':
            (y,) = nums(1); pos = (pos[0], oy + y if rel else y); cur.append(pos); prev_c = prev_q = None
        elif C in 'CS':
            if C == 'C':
                x1, y1, x2, y2, x, y = nums(6); c1 = (ox + x1, oy + y1)
            else:
                x2, y2, x, y = nums(4)
                c1 = (2 * pos[0] - prev_c[0], 2 * pos[1] - prev_c[1]) if prev_c else pos
            c2 = (ox + x2, oy + y2); end = (ox + x, oy + y)
            cur += cubic(pos, c1, c2, end); prev_c = c2; prev_q = None; pos = end
        elif C in 'QT':
            if C == 'Q':
                x1, y1, x, y = nums(4); q = (ox + x1, oy + y1)
            else:
                x, y = nums(2); q = (2 * pos[0] - prev_q[0], 2 * pos[1] - prev_q[1]) if prev_q else pos
            end = (ox + x, oy + y)
            c1 = (pos[0] + 2 / 3 * (q[0] - pos[0]), pos[1] + 2 / 3 * (q[1] - pos[1]))
            c2 = (end[0] + 2 / 3 * (q[0] - end[0]), end[1] + 2 / 3 * (q[1] - end[1]))
            cur += cubic(pos, c1, c2, end); prev_q = q; prev_c = None; pos = end
        elif C == 'A':
            fail('호(arc) 명령은 지원하지 않습니다. 일러스트레이터에서 다시 내보내 주세요')
    if cur and len(cur) > 2: subs.append(cur)
    return subs


def ellipse(cx, cy, rx, ry):
    n = max(64, math.ceil(2 * math.pi * max(rx, ry) / 1.0))
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return [list(zip(cx + rx * np.cos(a), cy + ry * np.sin(a)))]


# ---------- SVG reading ----------
def css_classes(root):
    rules = {}
    for st in root.iter('{http://www.w3.org/2000/svg}style'):
        for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', st.text or ''):
            props = dict((k.strip(), v.strip()) for k, v in re.findall(r'([\w-]+)\s*:\s*([^;]+)', body))
            for name in re.findall(r'\.([\w-]+)', sel):
                rules.setdefault(name, {}).update(props)
    return rules


def read_svg(path):
    root = ET.parse(path).getroot()
    classes = css_classes(root)
    pieces = []

    def style(el):
        s = {}
        for c in (el.get('class') or '').split(): s.update(classes.get(c, {}))
        s.update(dict((k.strip(), v.strip()) for k, v in re.findall(r'([\w-]+)\s*:\s*([^;]+)', el.get('style') or '')))
        for k in ('fill', 'stroke', 'display', 'opacity'):
            if el.get(k) is not None: s[k] = el.get(k)
        return s

    def walk(el, m):
        tag = el.tag.split('}')[-1]
        if tag in ('defs', 'clipPath', 'mask', 'style', 'title', 'desc', 'metadata'): return
        st = style(el)
        if st.get('display') == 'none': return
        m = m @ parse_transform(el.get('transform'))
        subs = None
        if tag == 'text':
            fail(f'{path.name}: 글자가 폰트 텍스트로 들어 있습니다 — 일러스트레이터에서 "윤곽선 만들기" 후 다시 내보내 주세요')
        elif tag == 'path':
            subs = parse_path(el.get('d', ''))
        elif tag in ('polygon', 'polyline'):
            v = [float(x) for x in re.findall(NUM, el.get('points', ''))]
            subs = [list(zip(v[0::2], v[1::2]))]
        elif tag == 'rect':
            x, y = float(el.get('x', 0)), float(el.get('y', 0)); w, h = float(el.get('width')), float(el.get('height'))
            if el.get('rx') or el.get('ry'): print(f'  주의: {path.name}의 rect 둥근 모서리는 무시됩니다')
            subs = [[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]]
        elif tag in ('circle', 'ellipse'):
            cx, cy = float(el.get('cx', 0)), float(el.get('cy', 0))
            r = el.get('r'); rx = float(el.get('rx', r)); ry = float(el.get('ry', r))
            subs = ellipse(cx, cy, rx, ry)
        if subs is not None:
            if st.get('fill') == 'none':
                print(f'  주의: {path.name}에 채우기 없는(선만 있는) 모양이 있어 건너뜁니다 — 확장(Expand) 해주세요')
                return
            subs = [apply(m, s) for s in subs if len(s) > 2]
            if subs: pieces.append(subs)
        for ch in el: walk(ch, m)

    walk(root, mat())
    if not pieces: fail(f'{path.name}: 모양을 찾지 못했습니다')
    return pieces


# ---------- resampling ----------
def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def clean(p):
    p = np.asarray(p, float)
    keep = np.r_[True, np.linalg.norm(np.diff(p, axis=0), axis=1) > 1e-6]
    p = p[keep]
    if len(p) > 1 and np.linalg.norm(p[0] - p[-1]) < 1e-6: p = p[:-1]
    if area(p) < 0: p = p[::-1]  # 모든 외곽선 방향 통일 (그릴 때는 even-odd 사용)
    return p


def corners(p):
    a = p - np.roll(p, 1, 0); b = np.roll(p, -1, 0) - p
    ang = np.degrees(np.abs(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1))))
    return np.nonzero(ang > CORNER_DEG)[0]


def perimeter(p):
    return np.linalg.norm(np.roll(p, -1, 0) - p, axis=1).sum()


def resample(p, N):
    # 둘레를 N등분하되, 모서리 점은 가장 가까운 샘플 자리에 그대로 박아 넣어 모양을 정확히 유지
    c = corners(p)
    if len(c): p = np.roll(p, -c[0], 0); c = (c - c[0]) % len(p)
    Q = np.vstack([p, p[:1]]); seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    cum = np.r_[0, np.cumsum(seg)]; L = cum[-1]
    s = np.arange(N) * L / N
    k = np.clip(np.searchsorted(cum, s, side='right') - 1, 0, len(seg) - 1)
    t = ((s - cum[k]) / np.maximum(seg[k], 1e-12))[:, None]
    out = Q[k] + (Q[k + 1] - Q[k]) * t
    used = set()
    for ci in c:
        j = int(round(cum[ci] / L * N)) % N
        for d in range(N):
            for jj in ((j + d) % N, (j - d) % N):
                if jj not in used: break
            else: continue
            break
        used.add(jj); out[jj] = p[ci]
    return out


def normalized(p):
    q = p - p.mean(0)
    return q / max(np.sqrt((q ** 2).sum(1).mean()), 1e-9)


def best_roll(ref, p):
    # ref와 가장 잘 겹치도록 시작점을 돌림 (모양 위치·크기는 정규화해서 비교)
    a, b = normalized(ref), normalized(p)
    fa, fb = np.fft.fft(a[:, 0] + 1j * a[:, 1]), np.fft.fft(b[:, 0] + 1j * b[:, 1])
    corr = np.fft.ifft(fa * np.conj(fb)).real  # corr[k] = Σ a[n+k]·b[n]  (원형 상호상관)
    return np.roll(p, int(np.argmax(corr)), 0)


def match_pieces(ref, cur, fname):
    if len(ref) != len(cur):
        fail(f'{fname}: 조각 수가 첫 키프레임과 다릅니다 ({len(cur)} vs {len(ref)})')
    allr = np.vstack([s for pc in ref for s in pc]); allc = np.vstack([s for pc in cur for s in pc])
    def key(pc, lo, hi): return (np.vstack(pc).mean(0) - lo) / np.maximum(hi - lo, 1e-9)
    rk = [key(pc, allr.min(0), allr.max(0)) for pc in ref]
    ck = [key(pc, allc.min(0), allc.max(0)) for pc in cur]
    order, free = [], set(range(len(cur)))
    for i, pc in enumerate(ref):
        cand = [j for j in free if len(cur[j]) == len(pc)]
        if not cand: fail(f'{fname}: 첫 키프레임의 {i + 1}번째 조각과 구멍 수가 맞는 조각이 없습니다')
        j = min(cand, key=lambda j: np.linalg.norm(rk[i] - ck[j]))
        order.append(j); free.discard(j)
    return [cur[j] for j in order]


def build(name, cfg):
    frames = []
    for f in cfg['files']:
        path = ROOT / f
        pieces = [[clean(s * cfg['unit']) for s in pc] for pc in read_svg(path)]
        pieces = [sorted(pc, key=lambda s: -abs(area(s))) for pc in pieces]  # 바깥 외곽선 먼저, 구멍은 뒤
        if frames: pieces = match_pieces(frames[0], pieces, path.name)
        frames.append(pieces)
    origin = np.vstack([s for pc in frames[0] for s in pc]).min(0)
    out = [[[] for _ in pc] for pc in frames[0]]
    for pi, pc in enumerate(frames[0]):
        for si in range(len(pc)):
            per = max(perimeter(fr[pi][si]) for fr in frames)
            nc = max(len(corners(fr[pi][si])) for fr in frames)
            N = int(min(1600, max(48, 3 * nc, math.ceil(per / SPACING))))
            prev = None
            for fi, fr in enumerate(frames):
                r = resample(fr[pi][si], N)
                if prev is not None: r = best_roll(prev, r)
                prev = r
                out[pi][si].append(r - origin)
    data = [[[np.round(out[pi][si][fi], 2).ravel().tolist() for si in range(len(out[pi]))]
             for pi in range(len(out))] for fi in range(len(frames))]
    pts0 = np.vstack([s for pc in frames[0] for s in pc]) - origin
    # 숫자가 들어갈 ㅇ 구멍: 구멍 있는 조각 중 가장 위(top) 또는 아래(bottom)
    rings = [pi for pi, pc in enumerate(frames[0]) if len(pc) >= 2]
    counter = None
    if rings:
        pick = min if cfg.get('counter', 'top') == 'top' else max
        pi = pick(rings, key=lambda i: frames[0][i][0][:, 1].mean())
        counter = [pi, 1]
    n_pts = sum(len(s) // 2 for pc in data[0] for s in pc)
    print(f'{name}: 키프레임 {len(frames)}개, 조각 {len(data[0])}개, 프레임당 점 {n_pts}개')
    return {'frames': data, 'at': cfg['at'], 'size': np.round(pts0.max(0), 2).tolist(), 'counter': counter}


if __name__ == '__main__':
    result = {'design': DESIGN, 'glyphs': {n: build(n, c) for n, c in GLYPHS.items()}}
    (ROOT / 'assets/glyphs.json').write_text(json.dumps(result, separators=(',', ':')), encoding='utf-8')
    print('저장:', ROOT / 'assets/glyphs.json')
