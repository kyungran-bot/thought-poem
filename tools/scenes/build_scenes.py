"""Scenes (keyframes) measured from the 11 design screenshots -> assets/scenes.json for the site.

Run: python3 tools/scenes/build_scenes.py   (needs numpy and opencv-python)

Coordinates are artboard units (1920 x 1077). s = position on the piece's axis:
  -1 = 용기 100, 0 = first screen (50:50), +1 = 생각 100.
"""
import json, math, sys
import numpy as np
from canon import placed, B

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join('..', '..', 'assets', 'scenes.json')
W, H = 1920, 1077
LINES = json.load(open('lines.json'))
LINES['A50'] = [math.degrees(math.atan2(1920, 1077)), 1920 * 1077 / math.hypot(1920, 1077)]  # corner to corner
LINES['T100'] = [75.89, 1560.0]   # beyond the bottom-right corner: all black
LINES['C100'] = [76.0, -40.0]     # beyond the top-left corner: all white

ORDER = ['C100', 'C92', 'C85', 'C70', 'A50', 'T52', 'T55', 'T65', 'T90a', 'T90b', 'T100']
S = {'C100': -1, 'C92': -.75, 'C85': -.5, 'C70': -.25, 'A50': 0,
     'T52': 1 / 6, 'T55': 2 / 6, 'T65': 3 / 6, 'T90a': 4 / 6, 'T90b': 5 / 6, 'T100': 1}
# gutter between each word and the dividing line (chosen inside the range that reproduces each screenshot)
GAP_T = {'A50': 0, 'T52': 0, 'T55': 33, 'T65': 32, 'T90a': 30, 'T90b': 30, 'T100': 30, 'C70': 0, 'C85': 0, 'C92': 0, 'C100': 0}
GAP_C = {'A50': 20, 'T52': 20, 'T55': 21, 'T65': 38, 'T90a': 9, 'T90b': 3, 'T100': 3, 'C70': 28, 'C85': 32, 'C92': 30, 'C100': 30}

# glyph frames (one per scene that shows its own drawing)
T_FRAMES = ['A50', 'T52', 'T55', 'T65', 'T90a', 'T90b', 'T100', 'C70', 'C85', 'C92']
C_FRAMES = ['A50', 'T52', 'T55', 'T65', 'T90a', 'T90b', 'C70', 'C85', 'C92', 'C100']
T_OF = {n: T_FRAMES.index(n) for n in T_FRAMES}; T_OF['C100'] = T_FRAMES.index('C92')
C_OF = {n: C_FRAMES.index(n) for n in C_FRAMES}; C_OF['T100'] = C_FRAMES.index('T90b')
T_PARENT = {'T52': 'A50', 'T55': 'T52', 'T65': 'T55', 'T90a': 'T65', 'T90b': 'T90a', 'T100': 'T90b', 'C70': 'A50', 'C85': 'C70', 'C92': 'C85'}
C_PARENT = {'T52': 'A50', 'T55': 'T52', 'T65': 'T55', 'T90a': 'T65', 'T90b': 'T90a', 'C70': 'A50', 'C85': 'C70', 'C92': 'C85', 'C100': 'C92'}

# phrases: ink boxes [x0, y0, x1, y1] where the screenshot shows them
PHRASES = {
    'inc':     ('이 많아지면', 'white', {'T52': [877.5, 150, 1215, 237.5], 'T55': [1180, 127.5, 1597.5, 237.5], 'T65': [1359.3, 137.7, 1777.3, 247.8],
                                         'T90a': [806, 585.8, 1224.1, 695.9], 'T90b': [803.5, 605.8, 1221.6, 715.9]}),
    'more':    ('에 잠식당하셨군요..', 'white', {'T100': [808.6, 608.3, 1552, 720.9]}),
    'suffix':  ('를 잃는 법', 'black', {'T52': [1570, 292.5, 1877.5, 382.5], 'T55': [1597.5, 340, 1902.5, 430], 'T65': [1609.6, 453.1, 1915, 543.2],
                                        'T90a': [1341.7, 1006.3, 1557, 1071.4], 'T90b': [1424.4, 998.8, 1639.6, 1063.9]}),
    'notlose': ('을 잃진 않으니까!', 'white', {'C70': [420.0, 295.0, 777.5, 357.5], 'C85': [381.0, 40.1, 614.1, 82.7], 'C92': [262.8, 25.0, 493.1, 67.6]}),
    'have':    ('를 가진다고', 'black', {'C70': [1350, 942.5, 1767.5, 1050], 'C85': [1268.3, 937.4, 1686.9, 1045.2], 'C92': [1266.6, 938.7, 1684.7, 1046.4]}),
    'bold1':   ('있게', 'black', {'C100': [1471.3, 797.1, 1624.2, 904.9]}),
    'bold2':   ('저지르셨군요!', 'black', {'C100': [1125.4, 927.4, 1641.8, 1035.2]}),
}
# numbers: label, centre and digit height as measured; None = not visible in that screenshot
NUM_L = {'A50': (50, None, 30), 'T52': (52, (275, 507.5), 30), 'T55': (55, (335, 655), 30), 'T65': (65, (327.95, 735.95), 30),
         'T90a': (90, (379.25, 718.45), 30), 'T90b': (90, (376.75, 718.45), 30), 'T100': (100, (379.2, 718.45), 30),
         'C70': (30, (210, 410), 30), 'C85': (15, (94, 198.05), 30), 'C92': (8, (73.85, 141.45), 22.5), 'C100': (0, None, 22.5)}
NUM_R = {'A50': (50, 'top', None), 'T52': (48, 'top', (1341.25, 525)), 'T55': (45, 'top', (1187.5, 567.5)), 'T65': (35, 'top', (1340.5, 665.85)),
         'T90a': (10, 'top', (1653, 878)), 'T90b': (5, 'top', None), 'T100': (0, 'top', None),
         'C70': (70, 'bot', (787.5, 1020)), 'C85': (85, 'bot', (582.75, 1010.15)), 'C92': (92, 'bot', (458.1, 983.8)), 'C100': (100, 'bot', (427.35, 862.25))}
NUM_R_SHOW = {'A50': 1, 'T52': 1, 'T55': 1, 'T65': 1, 'T90a': 1, 'T90b': 0, 'T100': 0, 'C70': 1, 'C85': 1, 'C92': 1, 'C100': 1}
NUM_L_SHOW = {n: 0 if n == 'C100' else 1 for n in ORDER}  # 생각 is gone at 용기 100


# steps where a morph would poke a spike into the picture: the old shape slides out and fades, the new one fades in
SLIDE = set()
# steps where shapes should pair by where they are on screen (the long band retracts into the short leg)
NEAR = {('T90a', 'T90b', 'thought', 5)}
# outlined words (Pear) that pop in one by one up to the 59 scene (screenshot at s = 0.4056) and pop out before 65
WORDS = [{"text": "고민 불안", "rot": 0, "box": [1266.2, 265.3, 1477.4, 342.4], "box2": [1492.0, 153.9, 1719.2, 237.6], "in": 0.385}, {"text": "어떡하지", "rot": 0, "box": [850.9, 226.7, 1096.4, 331.0], "box2": [1626.5, 253.4, 1872.0, 357.7], "in": 0.388}, {"text": "할까말까", "rot": 0, "box": [716.5, 518.1, 877.1, 582.7], "box2": [803.1, 713.9, 979.4, 785.1], "in": 0.394}, {"text": "할까말까", "rot": 0, "box": [716.5, 604.3, 877.1, 667.7], "box2": [803.1, 799.8, 979.4, 871.1], "in": 0.397}, {"text": "할까말까", "rot": 0, "box": [716.5, 690.5, 877.1, 753.9], "box2": [803.1, 885.8, 979.4, 957.1], "in": 0.4}, {"text": "걱정", "rot": 0, "box": [221.3, 629.2, 422.4, 790.2], "box2": [261.9, 647.1, 478.0, 814.5], "in": 0.403}, {"text": "음...", "rot": 0, "box": [18.2, 961.4, 163.7, 1054.3], "box2": [11.2, 968.4, 153.9, 1056.6], "in": 0.4056}, {"text": "할까말까", "rot": 0, "box": None, "box2": [985.5, 713.9, 1161.8, 785.1], "in": 0.44}, {"text": "할까말까", "rot": 0, "box": None, "box2": [1167.9, 713.9, 1344.2, 785.1], "in": 0.4686}, {"text": "할까말까", "rot": 0, "box": None, "box2": [985.5, 799.8, 1161.8, 871.1], "in": 0.4971}, {"text": "할까말까", "rot": 0, "box": None, "box2": [1269.8, 539.6, 1446.1, 610.9], "in": 0.5257}, {"text": "할까말까", "rot": 0, "box": None, "box2": [1452.2, 539.6, 1628.5, 610.9], "in": 0.5543}, {"text": "할까말까", "rot": 0, "box": None, "box2": [1634.6, 539.6, 1811.0, 610.9], "in": 0.5829}, {"text": "할까말까", "rot": 0, "box": None, "box2": [1269.8, 627.9, 1446.1, 699.1], "in": 0.6114}, {"text": "할까말까", "rot": 0, "box": None, "box2": [1452.2, 627.9, 1628.5, 699.1], "in": 0.64}]
WORD_SCENES = [0.4056, 0.6653]  # 59 and 89 screenshots
RING = {'thought': [4], 'courage': [0, 4]}  # pieces that are ㅇ rings (outer + counter)
ROTATED = {('courage', 'C85', 0), ('courage', 'C92', 0)}  # 용 top ring is drawn tilted in these scenes


def ellipse_params(points, rotated=False):
    """[cx, cy, rx, ry, angle_deg] with the angle kept in (-45, 45] so neighbouring scenes never spin."""
    import cv2
    from geo import _axis_fit
    p = np.asarray(points, float)
    (cx, cy), (w, h), a = cv2.fitEllipseDirect(p.astype(np.float32).reshape(-1, 1, 2)) if rotated else _axis_fit(p)
    rx, ry = w / 2, h / 2
    while a > 45: a -= 90; rx, ry = ry, rx
    while a <= -45: a += 90; rx, ry = ry, rx
    return [round(float(v), 2) for v in (cx, cy, rx, ry, a)]


def corners_only(p):
    """Keep only real corners of a straight-edged piece (drop duplicates and points on straight runs)."""
    p = B.clean(p)
    changed = True
    while changed and len(p) > 3:
        changed = False
        for i in range(len(p)):
            a, b, c = p[i - 1], p[i], p[(i + 1) % len(p)]
            e1, e2 = b - a, c - b
            l1, l2 = np.linalg.norm(e1), np.linalg.norm(e2)
            ang = 0 if l1 < .3 or l2 < .3 else np.degrees(abs(np.arctan2(e1[0] * e2[1] - e1[1] * e2[0], e1 @ e2)))
            if l1 < .3 or ang < 1.0:
                p = np.delete(p, i, 0); changed = True; break
    return p


def match_polygons(A, Bp, lam=0.08, absolute=False):
    """Corner correspondence between two closed polygons (same winding). Returns equal-length vertex lists:
    corners are paired with corners where the shapes agree, otherwise a corner is paired with a point on the
    other polygon's edge, so every in-between shape is again a polygon with straight edges."""
    def norm(P):
        if absolute: return P / 1000.0
        lo, hi = P.min(0), P.max(0); return (P - lo) / np.maximum(hi - lo, 1e-6)
    def proj(p, a, b):
        d = b - a; L = d @ d
        u = 0.0 if L < 1e-12 else float(np.clip((p - a) @ d / L, 0, 1)); return u, np.linalg.norm(p - (a + u * d))
    n, m = len(A), len(Bp); An = norm(A); best = None
    for s in range(m):
        Bs = np.roll(Bp, -s, 0); Bn = np.roll(norm(Bp), -s, 0)
        INF = 1e18; D = np.full((n + 1, m + 1), INF); D[0, 0] = np.linalg.norm(An[0] - Bn[0]); back = {}
        for i in range(n + 1):
            for j in range(m + 1):
                if D[i, j] >= INF: continue
                if i < n and j < m and (i + 1 < n) == (j + 1 < m) or (i + 1 == n and j + 1 == m):
                    if i < n and j < m:
                        c = D[i, j] + np.linalg.norm(An[(i + 1) % n] - Bn[(j + 1) % m])
                        if c < D[i + 1, j + 1]: D[i + 1, j + 1] = c; back[(i + 1, j + 1)] = (i, j, 'M', 0)
                if i + 1 < n and j < m:  # A corner lands on B's edge j -> j+1
                    u, dd = proj(An[i + 1], Bn[j % m], Bn[(j + 1) % m]); c = D[i, j] + dd + lam
                    if c < D[i + 1, j]: D[i + 1, j] = c; back[(i + 1, j)] = (i, j, 'A', u)
                if j + 1 < m and i < n:  # B corner lands on A's edge i -> i+1
                    u, dd = proj(Bn[j + 1], An[i % n], An[(i + 1) % n]); c = D[i, j] + dd + lam
                    if c < D[i, j + 1]: D[i, j + 1] = c; back[(i, j + 1)] = (i, j, 'B', u)
        if best is None or D[n, m] < best[0]: best = (D[n, m], s, back)
    _, s, back = best; Bs = np.roll(Bp, -s, 0)
    pairs = []; i, j = n, m
    while (i, j) != (0, 0):
        pi, pj, kind, u = back[(i, j)]
        if kind == 'M': pairs.append((A[i % n], Bs[j % m]))
        elif kind == 'A': pairs.append((A[i % n], Bs[pj % m] + u * (Bs[(pj + 1) % m] - Bs[pj % m])))
        else: pairs.append((A[pi % n] + u * (A[(pi + 1) % n] - A[pi % n]), Bs[j % m]))
        i, j = pi, pj
    pairs.reverse()  # the last pair is (A0, B0) again: it closes the loop
    return np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])


def frame_of(glyph, scene):
    """Pieces of one scene: straight pieces as corner lists, rings as two ellipses."""
    out = []
    for i, pc in enumerate(placed(glyph, scene)):
        if i in RING[glyph]:
            rot = (glyph, scene, i) in ROTATED
            out.append({'o': ellipse_params(pc[0], rot), 'i': ellipse_params(pc[1], rot)})
        else:
            out.append(corners_only(pc[0]))
    return out


def _crosses(P):
    n = len(P)
    def seg(a, b, c, d):
        o = lambda p, q, r: np.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
        return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1: continue
            if seg(P[i], P[(i + 1) % n], P[j], P[(j + 1) % n]): return True
    return False


def awkward(A, Bp):
    """True when the straight morph would fold or poke inward (self-crossing or a collapsing in-between area):
    such pieces crossfade instead of morphing."""
    for t in (.25, .5, .75):
        M = A + (Bp - A) * t
        if _crosses(M): return True
        if abs(B.area(M)) < 0.75 * min(abs(B.area(A)), abs(B.area(Bp))): return True
    return False


def ints(p):
    return np.round(np.asarray(p) * 2).astype(int).ravel().tolist()  # half-unit integers


def counter_box(e):
    cx, cy, rx, ry, a = e; r = math.radians(a)
    return [cx, cy, 2 * math.sqrt((rx * math.cos(r)) ** 2 + (ry * math.sin(r)) ** 2), 2 * math.sqrt((rx * math.sin(r)) ** 2 + (ry * math.cos(r)) ** 2)]


def main():
    T = {n: frame_of('thought', n) for n in T_FRAMES}
    C = {n: frame_of('courage', n) for n in C_FRAMES}
    rings = {'thought': [[T[n][i] if i in RING['thought'] else None for i in range(len(T[n]))] for n in T_FRAMES],
             'courage': [[C[n][i] if i in RING['courage'] else None for i in range(len(C[n]))] for n in C_FRAMES]}
    # one entry per step between neighbouring scenes: matched corner lists for every straight piece
    steps = []
    for a, b in zip(ORDER, ORDER[1:]):
        st = {}
        for g, F, OF in (('thought', T, T_OF), ('courage', C, C_OF)):
            fa, fb = F[T_FRAMES[OF[a]] if g == 'thought' else C_FRAMES[OF[a]]], F[T_FRAMES[OF[b]] if g == 'thought' else C_FRAMES[OF[b]]]
            pieces = []
            for i in range(len(fa)):
                if i in RING[g]: pieces.append(None); continue
                A2, B2 = match_polygons(fa[i], fb[i], absolute=(a, b, g, i) in NEAR); pieces.append([ints(A2), ints(B2), 1 if (a, b, g, i) in SLIDE or awkward(A2, B2) else 0])
            st[g] = pieces
        steps.append(st)
    counters = {}
    for n in ORDER:
        tf = T[T_FRAMES[T_OF[n]]]; cf = C[C_FRAMES[C_OF[n]]]
        counters[n] = {'L': counter_box(tf[4]['i']), 'Rtop': counter_box(cf[0]['i']), 'Rbot': counter_box(cf[4]['i'])}
    scenes = []
    for n in ORDER:
        sc = {'id': n, 's': S[n], 'line': [round(LINES[n][0], 3), round(LINES[n][1], 2)], 'gapT': GAP_T[n], 'gapC': GAP_C[n],
              'thought': T_OF[n], 'courage': C_OF[n], 'text': {}, 'num': {}}
        for key, (txt, col, boxes) in PHRASES.items():
            if n in boxes: sc['text'][key] = boxes[n] + [1]
            else:
                near = min(boxes, key=lambda m: abs(S[m] - S[n])); sc['text'][key] = boxes[near] + [0]
        lab, c, h = NUM_L[n]; L = counters[n]['L']
        rel = [0, 0] if c is None else [(c[0] - L[0]) / L[2], (c[1] - L[1]) / L[3]]
        sc['num']['L'] = [lab, round(rel[0], 4), round(rel[1], 4), h, NUM_L_SHOW[n]]
        lab, anchor, c = NUM_R[n]; cn = counters[n]['Rtop' if anchor == 'top' else 'Rbot']
        rel = [0, 0] if c is None else [(c[0] - cn[0]) / cn[2], (c[1] - cn[1]) / cn[3]]
        sc['num']['R'] = [lab, round(rel[0], 4), round(rel[1], 4), 30, NUM_R_SHOW[n], 1 if anchor == 'top' else 0]
        scenes.append(sc)
    data = {'W': W, 'H': H, 'rings': rings, 'steps': steps, 'ringPieces': RING,
            'phrases': {k: [v[0], v[1]] for k, v in PHRASES.items()}, 'words': WORDS, 'wordScenes': WORD_SCENES, 'scenes': scenes}
    s = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    open(OUT, 'w', encoding='utf-8').write(s)
    print('saved', OUT, f'{len(s) / 1024:.0f} KB')


if __name__ == '__main__':
    main()
