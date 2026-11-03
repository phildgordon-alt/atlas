"""Closest certified pair in a closed window: from crosscheck.json (exact rational interval endpoints, each interval holds exactly one
simple on-line zero once the window is certified).  Gap bounds are exact: [lo_{i+1} - hi_i, hi_{i+1} - lo_i].  Normalised gap
delta = gap * log(T/2pi)/(2pi) (mean spacing 1).  usage: closest_pair.py RUN_DIR"""
import sys, json, math
from fractions import Fraction as F
c = json.load(open(sys.argv[1] + '/crosscheck.json')); T0 = c['T0']
iv = [(F(a), F(b)) for a, b in c['intervals_inside']]
off = [float((a + b) / 2 - T0) for a, b in iv]
g = [(iv[i + 1][0] - iv[i][1], iv[i + 1][1] - iv[i][0], i) for i in range(len(iv) - 1)]
dens = math.log(T0 / (2 * math.pi)) / (2 * math.pi)
lo, hi, i = min(g)
print(json.dumps(dict(T0=T0, zeros=len(iv), offsets=[round(x, 5) for x in off],
                      gaps=[round(float(a), 5) for a, b, _ in g], closest_pair_index=[i, i + 1],
                      closest_gap_bounds=[float(lo), float(hi)], normalised_gap=round(float(lo) * dens, 4),
                      mean_spacing=round(1 / dens, 5), min_normalised_gap_all=[round(float(a) * dens, 3) for a, b, _ in g]), indent=1))
