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
COUNTERS = json.load(open('counters.json'))

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
    'notlose': ('을 잃진 않으니까', 'white', {'C70': [420, 295, 777.5, 357.5], 'C85': [381, 40.1, 614.1, 82.7], 'C92': [262.8, 25, 493.1, 67.6]}),
    'have':    ('를 가진다고', 'black', {'C70': [1350, 942.5, 1767.5, 1050], 'C85': [1268.3, 937.4, 1686.9, 1045.2], 'C92': [1266.6, 938.7, 1684.7, 1046.4]}),
    'bold1':   ('있게', 'black', {'C100': [1471.3, 797.1, 1624.2, 904.9]}),
    'bold2':   ('저지르셨군요!', 'black', {'C100': [1125.4, 927.4, 1641.8, 1035.2]}),
}
# numbers: label, centre and digit height as measured; None = not visible in that screenshot
NUM_L = {'A50': (50, None, 30), 'T52': (52, (275, 507.5), 30), 'T55': (55, (335, 655), 30), 'T65': (65, (327.95, 735.95), 30),
         'T90a': (90, (379.25, 718.45), 30), 'T90b': (90, (376.75, 718.45), 30), 'T100': (100, (379.2, 718.45), 30),
         'C70': (30, (210, 410), 30), 'C85': (15, (94, 198.05), 30), 'C92': (15, (73.85, 141.45), 22.5), 'C100': (15, None, 22.5)}
NUM_R = {'A50': (50, 'top', None), 'T52': (48, 'top', (1341.25, 525)), 'T55': (45, 'top', (1187.5, 567.5)), 'T65': (35, 'top', (1340.5, 665.85)),
         'T90a': (10, 'top', (1653, 878)), 'T90b': (5, 'top', None), 'T100': (0, 'top', None),
         'C70': (70, 'bot', (787.5, 1020)), 'C85': (85, 'bot', (582.75, 1010.15)), 'C92': (92, 'bot', (458.1, 983.8)), 'C100': (100, 'bot', (427.35, 862.25))}
NUM_R_SHOW = {'A50': 1, 'T52': 1, 'T55': 1, 'T65': 1, 'T90a': 1, 'T90b': 0, 'T100': 0, 'C70': 1, 'C85': 1, 'C92': 1, 'C100': 1}
NUM_L_SHOW = {n: 1 for n in ORDER}


def resample_glyph(frames, parent_of, names):
    """frames: name -> pieces. Returns name -> pieces resampled to common point counts, start points aligned."""
    out = {n: [[None] * len(pc) for pc in frames[n]] for n in names}
    base = names[0]
    for pi, pc in enumerate(frames[base]):
        for si in range(len(pc)):
            subs = {n: B.clean(frames[n][pi][si]) for n in names}
            per = max(B.perimeter(s) for s in subs.values())
            nc = max(len(B.corners(s)) for s in subs.values())
            N = int(min(1400, max(48, 3 * nc, math.ceil(per / 4.0))))
            done = {}
            for n in names:  # names are ordered so parents come first
                r = B.resample(subs[n], N)
                if n in parent_of: r = B.best_roll(done[parent_of[n]], r)
                done[n] = r; out[n][pi][si] = r
    return out


def flat(pieces):
    return [[np.round(s * 2).astype(int).ravel().tolist() for s in pc] for pc in pieces]  # half-unit integers


def main():
    T = {n: placed('thought', n) for n in T_FRAMES}
    C = {n: placed('courage', n) for n in C_FRAMES}
    T = resample_glyph(T, T_PARENT, T_FRAMES)
    C = resample_glyph(C, C_PARENT, C_FRAMES)
    scenes = []
    for n in ORDER:
        sc = {'id': n, 's': S[n], 'line': [round(LINES[n][0], 3), round(LINES[n][1], 2)], 'gapT': GAP_T[n], 'gapC': GAP_C[n],
              'thought': T_OF[n], 'courage': C_OF[n], 'text': {}, 'num': {}}
        for key, (txt, col, boxes) in PHRASES.items():
            if n in boxes: sc['text'][key] = boxes[n] + [1]
            else:  # hidden: park it on the nearest scene that shows it so it fades in place
                near = min(boxes, key=lambda m: abs(S[m] - S[n]))
                sc['text'][key] = boxes[near] + [0]
        cnt = COUNTERS.get(n if n != 'C100' else 'C92', {})
        lab, c, h = NUM_L[n]
        if c is None: rel = [0, 0]
        else: L = COUNTERS[n]['L'] if n in COUNTERS and 'L' in COUNTERS[n] else cnt['L']; rel = [(c[0] - L[0]) / L[2], (c[1] - L[1]) / L[3]]
        sc['num']['L'] = [lab, round(rel[0], 4), round(rel[1], 4), h, NUM_L_SHOW[n]]
        lab, anchor, c = NUM_R[n]
        cn = COUNTERS[n if n != 'T100' else 'T90b']['Rtop' if anchor == 'top' else 'Rbot']
        rel = [0, 0] if c is None else [(c[0] - cn[0]) / cn[2], (c[1] - cn[1]) / cn[3]]
        sc['num']['R'] = [lab, round(rel[0], 4), round(rel[1], 4), 30, NUM_R_SHOW[n], 1 if anchor == 'top' else 0]
        scenes.append(sc)
    data = {'W': W, 'H': H, 'thought': [flat(T[n]) for n in T_FRAMES], 'courage': [flat(C[n]) for n in C_FRAMES],
            'counters': {'thought': [4, 1], 'courageTop': [0, 1], 'courageBottom': [4, 1]},
            'phrases': {k: [v[0], v[1]] for k, v in PHRASES.items()}, 'scenes': scenes}
    s = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    open(OUT, 'w', encoding='utf-8').write(s)
    npts = lambda fr: sum(len(x) // 2 for pc in fr for x in pc)
    print('saved', OUT, f'{len(s) / 1024:.0f} KB', ' points/frame: thought', npts(data['thought'][0]), 'courage', npts(data['courage'][0]))


if __name__ == '__main__':
    main()
