"""Canonical pieces for every 생각 / 용기 stage, in artboard units (1920 x 1077).

생각 order: ㅅ, ㅐ, ㄱ(각 첫 자음), ㅏ, ㅇ(outer, inner), ㄱ(받침)
용기 order: 위 ㅇ(outer, inner), 왼 기둥, 오른 기둥, 막대, 아래 ㅇ(outer, inner), 기 ㄱ, 기 ㅣ
Rings that the designer cut (by the screen edge or along the dividing line) are completed by fitting
ellipses to their visible arcs; merged shapes are split; stroked shapes are offset by half the stroke.
"""
from geo import *
from geo import _axis_fit
from place import THINK, YONG, off

TRACE = GLYPHS / '생각0단계_트레이스.svg'  # '생각0단계.svg' is font text, so the first screen uses a trace of the picture
THINK_SVG = lambda k: GLYPHS / f'생각{k}단계.svg'
YONG_SVG = lambda k: GLYPHS / f'용기{k}단계.svg'


def els(path):
    return elements(path)


def ring_of(subs):
    s = sorted(subs, key=lambda p: -abs(B.area(np.asarray(p))))
    return [np.asarray(s[0]), np.asarray(s[-1])]


def ring_fit(path, index, split=None, only_sub=None, rotated=False):
    subs = raw_path_subs(path, index)
    if only_sub is not None: subs = [subs[only_sub]]
    eo, ei, rad = ring_from_runs(curve_runs(subs), split, rotated)
    return [ellipse_poly(eo), ellipse_poly(ei)], (eo, ei, rad)


def poly(e):
    return np.asarray(e[1][0])


# ---------------- 생각 ----------------
def think_stage(k):
    if k == '0':
        e = els(TRACE)
        pieces = [poly(e[0]), poly(e[1]), poly(e[2]), poly(e[3]), ring_of(e[5][1]), poly(e[4])]
        return [[p / 0.7944] if not isinstance(p, list) else [q / 0.7944 for q in p] for p in pieces]
    e = els(THINK_SVG(k))
    if k == '4':
        s6 = els(THINK_SVG('6'))
        pieces = [
            np.array([(2.16, 0), (105.04, 0), (455.97, 384.37), (289.85, 384.37), (111.3, 183.49), (111.3, 384.37), (2.16, 384.37)]),
            np.array([(412.85, 0), (757.03, 0), (757.03, 384.37), (602.28, 384.37), (603.36, 112.16), (568.67, 112.16), (567.59, 384.37), (412.85, 384.37)]),
            poly(s6[2]), poly(s6[3]), ring_of(s6[4][1]),
            np.array([(800.62, 366.84), (1924.31, 366.83), (1924.31, 756.17), (1926.23, 766.77), (1501.4, 913.57), (1006.5, 1090.91),
                      (814.42, 1088.94), (809.32, 907.97), (1740.6, 593.68), (1740.6, 562.8), (1474.47, 562.59), (800.62, 562.59)])]
    elif k == '-3':
        sub = e[1][1]  # compound path: ring outer, ㅅ, ring inner, ㅐ  (2px stroke -> offset 1)
        pieces = [offset_polygon(sub[1], 1), offset_polygon(sub[3], 1), poly(e[2]), poly(e[3]),
                  [offset_polygon(sub[0], 1), offset_polygon(sub[2], -1)], poly(e[0])]
    else:
        order = {'1': [1, 0, 4, 5, 2, 3], '2': [1, 2, 3, 4, 0, 5], '3': [3, 5, 2, 4, 0, 1], '5': [0, 1, 2, 3, 4, 5],
                 '6': [0, 1, 2, 3, 4, 5], '-1': [0, 1, 4, 5, 2, 3], '-2': [1, 0, 4, 5, 2, 3]}[k]
        pieces = [ring_of(e[i][1]) if j == 4 else poly(e[i]) for j, i in enumerate(order)]
    return [[np.asarray(p)] if not isinstance(p, list) else p for p in pieces]


# ---------------- 용기 ----------------
def yong_stage(k):
    path = YONG_SVG(k); e = els(path)
    if k == '0':
        P = [ring_of(e[0][1]), poly(e[3]), poly(e[4]), poly(e[2]), ring_of(e[1][1]), poly(e[5]), poly(e[6])]
    elif k == '1':
        o = lambda i: offset_polygon(poly(e[i]), 6)
        P = [ring_of(e[1][1]), o(5), o(6), o(4), ring_of(e[3][1]), o(7), o(8)]
    elif k == '2':
        top, info = ring_fit(path, 0)
        (cx, cy), (w, h), a = info[0]; (icx, icy), (iw, ih), _ = info[1]
        stub_top = ((icy + ih / 2) + (cy + h / 2)) / 2
        runs = curve_runs(raw_path_subs(path, 0))
        xL = min(r[-1][0] for r in runs if abs(r[-1][1] - 263.05) < 1.5) if any(abs(r[-1][1] - 263.05) < 1.5 for r in runs) else 77.0
        bottom, _ = ring_fit(path, 2)
        P = [top, rect(xL, stub_top, 190.24, 323.27), rect(235.91, stub_top, 329.11, 323.27), rect(6.49, 303.27, 400.03, 385.70), bottom,
             np.array([(439.19, 0), (784.87, 0), (784.87, 124.55), (448.99, 622.72), (438.43, 622.72), (438.43, 430.89), (656.59, 119.58), (439.19, 119.58)]),
             poly(e[1])]
    elif k == '-1':
        top, _ = ring_fit(path, 0); bottom, _ = ring_fit(path, 5)
        R = 4; lo = np.array([300.0, -10.0]); m = np.zeros((int(540 * R), int(360 * R)), np.uint8)
        for i in (7, 8, 4): fill(m, e[i][1], R, -lo * R)
        gi = max(contours(m, R, -lo * R, eps=0.6 * R), key=lambda pc: abs(B.area(pc[0])))[0]
        P = [top, poly(e[1]), poly(e[2]), poly(e[3]), bottom, gi, poly(e[6])]
    elif k in ('-2', '-3'):
        top, _ = ring_fit(path, 2); bottom, _ = ring_fit(path, 6)
        P = [top, poly(e[4]), poly(e[5]), poly(e[0]), bottom, poly(e[3]), poly(e[1])]
    elif k == '3':
        top, _ = ring_fit(path, 1); bottom, _ = ring_fit(path, 0)
        P = [top, rect(64.44, 416.1, 219.63, 529.54), poly(e[4]), rect(25.71, 485.18, 654.47, 628.98), bottom, poly(e[2]), poly(e[5])]
    elif k == '4':
        top, _ = ring_fit(path, 6, rotated=True); bottom, _ = ring_fit(path, 2)
        P = [top, poly(e[5]), poly(e[4]), poly(e[3]), bottom, poly(e[0]), poly(e[1])]
    elif k == '5':
        top, _ = ring_fit(path, 6, rotated=True); bottom, _ = ring_fit(path, 0)
        P = [top, poly(e[5]), poly(e[4]), poly(e[3]), bottom, poly(e[1]), poly(e[2])]
    elif k == '6':
        top, _ = ring_fit(path, 6)
        bsubs = raw_path_subs(path, 0)
        eo = _axis_fit(np.vstack([r for r in curve_runs([bsubs[0]]) if np.linalg.norm(np.diff(r, axis=0), axis=1).sum() >= 60]))
        hole = sorted(e[0][1], key=lambda p: abs(B.area(np.asarray(p))))[0]
        P = [top, poly(e[4]), poly(e[5]), poly(e[3]), [ellipse_poly(eo), np.asarray(hole)], poly(e[1]), poly(e[2])]
    return [[np.asarray(p)] if not isinstance(p, list) else [np.asarray(q) for q in p] for p in P]


import json as _json, os as _os
_PS = _json.load(open(_os.path.join(_os.path.dirname(__file__), 'pieceshift.json'))) if _os.path.exists(_os.path.join(_os.path.dirname(__file__), 'pieceshift.json')) else {}


def placed(glyph, scene, shifts=True):
    P = _placed(glyph, scene)
    sh = _PS.get(f'{scene}:{glyph}') if shifts else None
    if sh: P = [[s + np.array(sh[i]) for s in pc] for i, pc in enumerate(P)]
    return P


def _placed(glyph, scene):
    """Canonical pieces of the stage shown in a scene, moved to artboard coordinates."""
    if glyph == 'thought':
        if scene == 'A50': return think_stage('0')
        k, o = THINK[scene]
        return [[s + off(scene, o, 'thought') for s in pc] for pc in think_stage(k)]
    if scene == 'A50':
        k, o = YONG['A50']; return [[s + o for s in pc] for pc in yong_stage(k)]
    k, o = YONG[scene]
    return [[s + off(scene, o, 'courage') for s in pc] for pc in yong_stage(k)]
