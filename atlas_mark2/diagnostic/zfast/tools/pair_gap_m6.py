"""M6 pair-gap tool (new file; modeled on tools/pair_gap2.py, unchanged): certified closest pair in a finished v5z4 window at
10^24/10^23, from RUN/intervals_summary.json (written by tools/window_intervals.py). Finds the two consecutive certified
sign-change intervals with the smallest upper gap, reports the certified gap enclosure [a2 - b1, b2 - a1] and the normalized
gap delta = gap * log(T/2pi)/(2pi) (mean local spacing is 2pi/log(T/2pi); computed in Arb at prec=200, same formula as
pair_gap2.py). Does not overwrite pair_gap2.py or any existing run file; writes nothing itself (prints JSON to stdout)."""
import json, sys
from fractions import Fraction as F
from flint import arb, ctx
ctx.prec = 200
s = json.load(open(sys.argv[1] + '/intervals_summary.json')); T0 = s['T0']; iv = s['intervals']
i = min(range(len(iv) - 1), key=lambda j: iv[j + 1][1] - iv[j][0])
(a1, b1), (a2, b2) = iv[i], iv[i + 1]
f = (arb(T0) / (2 * arb.pi())).log() / (2 * arb.pi())
g1, g2 = F(a2) - F(b1), F(b2) - F(a1); lo, hi = arb(g1.numerator) / arb(g1.denominator), arb(g2.numerator) / arb(g2.denominator)
print(json.dumps(dict(T0=str(T0), z1=[str(F(T0) + F(a1)), str(F(T0) + F(b1))], z2=[str(F(T0) + F(a2)), str(F(T0) + F(b2))],
                      z1_offsets=[a1, b1], z2_offsets=[a2, b2], gap=[float(lo), float(hi)], delta=[(lo * f).lower().str(6, radius=False), (hi * f).upper().str(6, radius=False)])))
