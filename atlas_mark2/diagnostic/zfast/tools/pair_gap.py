"""Certified closest pair in a finished window: from intervals_summary.json, the two consecutive certified intervals with the smallest
upper gap; certified gap in [a2 - b1, b2 - a1]; normalized delta = gap * log(T/2pi)/(2pi) (Arb)."""
import json, sys
from fractions import Fraction as F
from flint import arb, ctx
ctx.prec = 200
s = json.load(open(sys.argv[1] + '/intervals_summary.json')); T0 = s['T0']; iv = s['intervals']
i = min(range(len(iv) - 1), key=lambda j: iv[j + 1][1] - iv[j][0])
(a1, b1), (a2, b2) = iv[i], iv[i + 1]
f = (arb(T0) / (2 * arb.pi())).log() / (2 * arb.pi())
lo, hi = arb(F(a2) - F(b1)), arb(F(b2) - F(a1))
print(json.dumps(dict(T0=str(T0), z1=[str(F(T0) + F(a1)), str(F(T0) + F(b1))], z2=[str(F(T0) + F(a2)), str(F(T0) + F(b2))],
                      z1_offsets=[a1, b1], z2_offsets=[a2, b2], gap=[float(lo), float(hi)], delta=[(lo * f).lower().str(6, radius=False), (hi * f).upper().str(6, radius=False)])))
