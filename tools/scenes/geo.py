"""Shared helpers for analysing the keyframe SVGs and screenshots (raster geometry with OpenCV)."""
import re, sys
from pathlib import Path
import numpy as np, cv2
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import build_glyphs as B  # noqa: E402

GLYPHS = ROOT / 'assets' / 'glyphs'
W, H = 1920, 1080  # artboard


def elements(path):
    """List of (tag, [subpath Nx2 arrays], stroke_width or 0) in document order, transforms applied."""
    root = ET.parse(path).getroot(); classes = B.css_classes(root); out = []

    def walk(el, m):
        tag = el.tag.split('}')[-1]
        if tag in ('defs', 'style', 'title'): return
        m = m @ B.parse_transform(el.get('transform'))
        st = {}
        for c in (el.get('class') or '').split(): st.update(classes.get(c, {}))
        subs = None
        if tag == 'path': subs = B.parse_path(el.get('d', ''))
        elif tag in ('polygon', 'polyline'):
            v = [float(x) for x in re.findall(B.NUM, el.get('points', ''))]; subs = [list(zip(v[0::2], v[1::2]))]
        elif tag == 'rect':
            x, y = float(el.get('x', 0)), float(el.get('y', 0)); w, h = float(el.get('width')), float(el.get('height'))
            subs = [[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]]
        if subs is not None:
            sw = float(re.findall(B.NUM, st.get('stroke-width', '0'))[0]) if st.get('stroke') not in (None, 'none') else 0
            out.append((tag, [B.apply(m, s) for s in subs if len(s) > 2], sw))
        for ch in el: walk(ch, m)

    walk(root, B.mat())
    return out


def fill(mask, subs, scale, off=(0, 0), stroke=0):
    """Even-odd fill of the subpaths into mask (uint8), coordinates * scale + off. Optional stroke width (units)."""
    m = np.zeros_like(mask)
    for s in subs:
        p = np.round((np.asarray(s) * scale + off) * 16).astype(np.int32)
        t = np.zeros_like(mask); cv2.fillPoly(t, [p], 255, lineType=cv2.LINE_AA, shift=4); m ^= (t > 127).astype(np.uint8) * 255
    if stroke:
        for s in subs:
            p = np.round((np.asarray(s) * scale + off) * 16).astype(np.int32)
            cv2.polylines(m, [p], True, 255, thickness=max(1, int(round(stroke * scale))), lineType=cv2.LINE_8, shift=4)
    mask |= m
    return mask


def contours(mask, scale, off=(0, 0), eps=0.0):
    """Outer contours with their holes -> list of pieces [outer, hole, ...] in units ((px - off) / scale)."""
    cs, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    pieces = []
    if hier is None: return pieces
    hier = hier[0]
    def conv(c):
        if eps: c = cv2.approxPolyDP(c, eps, True)
        return (c.reshape(-1, 2).astype(float) + 0.5 - off) / scale
    for i, c in enumerate(cs):
        if hier[i][3] != -1 or cv2.contourArea(c) < 4: continue
        piece = [conv(c)]
        j = hier[i][2]
        while j != -1:
            if cv2.contourArea(cs[j]) >= 4: piece.append(conv(cs[j]))
            j = hier[j][0]
        pieces.append(piece)
    return pieces


def bbox(subs):
    p = np.vstack(subs); return p.min(0), p.max(0)


# ---------- path parsing that remembers which points came from curves ----------
def parse_path_flags(d):
    """Like build_glyphs.parse_path but returns [(points Nx2, is_curve bool N)] per subpath."""
    toks = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|' + B.NUM, d)
    i, cmd, subs = 0, None, []
    cur = None; flags = None
    pos = start = (0.0, 0.0); prev_c = None

    def nums(k):
        nonlocal i
        v = [float(x) for x in toks[i:i + k]]; i += k; return v

    def close():
        nonlocal cur, flags
        if cur and len(cur) > 2: subs.append((np.array(cur), np.array(flags)))
        cur = None; flags = None

    while i < len(toks):
        if re.fullmatch('[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                close(); pos = start; prev_c = None; continue
        rel = cmd.islower(); C = cmd.upper(); ox, oy = pos if rel else (0.0, 0.0)
        if C == 'M':
            x, y = nums(2); pos = start = (ox + x, oy + y); close(); cur = [pos]; flags = [False]
            cmd = 'l' if rel else 'L'; prev_c = None; continue
        if cur is None: cur = [pos]; flags = [False]
        if C == 'L':
            x, y = nums(2); pos = (ox + x, oy + y); cur.append(pos); flags.append(False); prev_c = None
        elif C == 'H':
            (x,) = nums(1); pos = (ox + x if rel else x, pos[1]); cur.append(pos); flags.append(False); prev_c = None
        elif C == 'V':
            (y,) = nums(1); pos = (pos[0], oy + y if rel else y); cur.append(pos); flags.append(False); prev_c = None
        elif C in 'CS':
            if C == 'C':
                x1, y1, x2, y2, x, y = nums(6); c1 = (ox + x1, oy + y1)
            else:
                x2, y2, x, y = nums(4); c1 = (2 * pos[0] - prev_c[0], 2 * pos[1] - prev_c[1]) if prev_c else pos
            c2 = (ox + x2, oy + y2); end = (ox + x, oy + y)
            pts = B.cubic(pos, c1, c2, end); cur += [tuple(p) for p in pts]; flags += [True] * len(pts)
            prev_c = c2; pos = end
        else:
            raise ValueError('unsupported path command ' + C)
    close()
    return subs


def raw_path_subs(path, index):
    """Curve-flagged subpaths of the index-th drawable element (document order) of an SVG, transforms applied."""
    root = ET.parse(path).getroot(); k = [-1]; out = []

    def walk(el, m):
        tag = el.tag.split('}')[-1]
        if tag in ('defs', 'style', 'title'): return
        m = m @ B.parse_transform(el.get('transform'))
        if tag in ('path', 'polygon', 'polyline', 'rect'):
            k[0] += 1
            if k[0] == index:
                if tag == 'path':
                    for p, f in parse_path_flags(el.get('d', '')): out.append((B.apply(m, p), f))
                else:
                    out.extend((s, np.zeros(len(s), bool)) for s in elements_single(el, m))
        for ch in el: walk(ch, m)

    walk(root, B.mat())
    return out


def elements_single(el, m):
    tag = el.tag.split('}')[-1]
    if tag in ('polygon', 'polyline'):
        v = [float(x) for x in re.findall(B.NUM, el.get('points', ''))]; s = list(zip(v[0::2], v[1::2]))
    else:
        x, y = float(el.get('x', 0)), float(el.get('y', 0)); w, h = float(el.get('width')), float(el.get('height'))
        s = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    return [B.apply(m, s)]


def curve_runs(subs):
    """Maximal runs of curve-generated points (each run includes the point where the curve started)."""
    runs = []
    for p, f in subs:
        n = len(p); cur = []
        for j in range(n):
            if f[j]:
                if not cur and j > 0: cur.append(p[j - 1])
                cur.append(p[j])
            elif cur:
                runs.append(np.array(cur)); cur = []
        if cur: runs.append(np.array(cur))
    return [r for r in runs if len(r) >= 6]


def fit_circle(p):
    A = np.c_[2 * p, np.ones(len(p))]; b = (p ** 2).sum(1)
    cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]
    return np.array([cx, cy]), np.sqrt(max(c + cx * cx + cy * cy, 0))


def ellipse_poly(e, n=720):
    (cx, cy), (w, h), ang = e
    a = np.linspace(0, 2 * np.pi, n, endpoint=False); r = np.radians(ang)
    x, y = w / 2 * np.cos(a), h / 2 * np.sin(a)
    return np.stack([cx + x * np.cos(r) - y * np.sin(r), cy + x * np.sin(r) + y * np.cos(r)], 1)


def fit_ellipse(p):
    return cv2.fitEllipseDirect(np.asarray(p, np.float32).reshape(-1, 1, 2))


def ring_from_runs(runs, split=None):
    """Classify arc runs into outer / inner by fitted radius and fit an ellipse to each group."""
    fits = [(fit_circle(r)[1], r) for r in runs]
    rad = np.array([f[0] for f in fits])
    thr = split if split is not None else (rad.min() + rad.max()) / 2
    outer = np.vstack([r for R, r in fits if R > thr]); inner = np.vstack([r for R, r in fits if R <= thr])
    return fit_ellipse(outer), fit_ellipse(inner), rad


def offset_polygon(p, d):
    """Mitered outward offset of a simple polygon by d (stroke / 2)."""
    p = np.asarray(p, float)
    keep = np.r_[np.linalg.norm(np.diff(p, axis=0), axis=1) > 1e-6, np.linalg.norm(p[-1] - p[0]) > 1e-6]
    p = p[keep]
    if B.area(p) < 0: p = p[::-1]  # positive area (y down) -> outward normal of edge (dx, dy) is (dy, -dx)
    n = len(p); out = []
    for i in range(n):
        a, b, c = p[i - 1], p[i], p[(i + 1) % n]
        e1, e2 = b - a, c - b
        n1 = np.array([e1[1], -e1[0]]) / np.linalg.norm(e1); n2 = np.array([e2[1], -e2[0]]) / np.linalg.norm(e2)
        m = n1 + n2; L = np.linalg.norm(m)
        if L < 1e-9: out.append(b + n1 * d); continue
        m /= L; k = d / max(np.dot(m, n1), 0.1)
        out.append(b + m * k)
    return np.array(out)


def rect(x0, y0, x1, y1):
    return np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], float)


# ---------- sturdier ring fitting (overrides the simple version above) ----------
def _axis_fit(p):
    x, y = p[:, 0], p[:, 1]
    D = np.c_[x * x, y * y, x, y, np.ones(len(p))]
    _, _, vt = np.linalg.svd(D, full_matrices=False); A, C, Dd, E, F = vt[-1]
    cx, cy = -Dd / (2 * A), -E / (2 * C)
    G = A * cx * cx + C * cy * cy - F
    a, b = np.sqrt(G / A), np.sqrt(G / C)
    return ((float(cx), float(cy)), (float(2 * a), float(2 * b)), 0.0)


def _concentric(p, e):
    (cx, cy), _, ang = e; r = np.radians(ang)
    q = p - (cx, cy); u = q[:, 0] * np.cos(r) + q[:, 1] * np.sin(r); v = -q[:, 0] * np.sin(r) + q[:, 1] * np.cos(r)
    sol = np.linalg.lstsq(np.c_[u * u, v * v], np.ones(len(p)), rcond=None)[0]
    return ((cx, cy), (float(2 / np.sqrt(sol[0])), float(2 / np.sqrt(sol[1]))), ang)


def ring_from_runs(runs, split=None, rotated=False, min_len=60):
    runs = [r for r in runs if np.linalg.norm(np.diff(r, axis=0), axis=1).sum() >= min_len]
    rad = np.array([fit_circle(r)[1] for r in runs])
    thr = split if split is not None else rad.min() * 1.3
    outer = np.vstack([r for R, r in zip(rad, runs) if R > thr]); inner = np.vstack([r for R, r in zip(rad, runs) if R <= thr])
    eo = fit_ellipse(outer) if rotated else _axis_fit(outer)
    return eo, _concentric(inner, eo), rad
