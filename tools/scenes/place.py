# Registered placements: artboard = svg coords + offset (half-size screenshots corrected by +2.5 for the edge pixel)
C = 2.5
THINK = {'T52': ('1', (48.5, 59.2)), 'T55': ('2', (-2.6, -0.8)), 'T65': ('3', (-2.2, -1.9)), 'T90a': ('4', (-3.6, -10.6)),
         'T90b': ('5', (-5.1, -3.0)), 'T100': ('6', (-4.3, -6.2)), 'C70': ('-1', (-1.7, -2.4)), 'C85': ('-2', (-2.4, -2.7)),
         'C92': ('-3', (-2.7, -2.8))}
YONG = {'A50': ('0', (1263.5, 458.4)), 'T52': ('1', (1175.2, 383.1)), 'T55': ('2', (976.2, 442.8)), 'T65': ('-1', (1153.2, 560.2)),
        'T90a': ('-2', (1574.2, 861.1)), 'T90b': ('-3', (1653.0, 899.4)), 'C70': ('3', (462.9, 92.0)), 'C85': ('4', (220.0, -2.2)),
        'C92': ('5', (29.6, 2.2)), 'C100': ('6', (-6.5, -4.8))}
import json as _json, os as _os
_REF = _json.load(open(_os.path.join(_os.path.dirname(__file__), 'refine.json')))


def off(n, o, glyph=None):
    if n == 'A50': return (o[0], o[1])
    dx, dy = _REF.get(f'{n}:{glyph}', (-C, -C)) if glyph else (-C, -C)
    return (o[0] + C + dx, o[1] + C + dy)
