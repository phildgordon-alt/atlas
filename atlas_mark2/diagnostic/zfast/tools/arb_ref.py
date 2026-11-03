"""Arb reference Z(T0+u): the verify_zs5 Zg formula (Gamma phase x zeta), prec 160 + bitlen(T0).  Lines 'T0 u' on stdin -> JSON."""
import sys, json, time, resource
from fractions import Fraction
from flint import arb, acb, ctx
def hx(T0, u):
    f = Fraction(T0) + Fraction(u); p, q = f.numerator, f.denominator
    old = ctx.prec; ctx.prec = max(old, abs(p).bit_length() + q.bit_length() + 8)
    try: v = arb(p) / arb(q)
    finally: ctx.prec = old
    assert v.rad() == 0
    return v
def Zg(T0, t):
    prec = 160 + T0.bit_length(); old = ctx.prec; ctx.prec = prec
    try:
        T = hx(T0, t); g = acb(arb(1) / 4, T / 2).gamma(); ph = g / abs(g)
        pw = acb(0, -T / 2) * arb.pi().log(); e = ph * acb(pw.real.exp() * pw.imag.cos(), pw.real.exp() * pw.imag.sin())
        return (e * acb(arb(1) / 2, T).zeta()).real
    finally: ctx.prec = old
for line in sys.stdin:
    if not line.strip(): continue
    T0s, us = line.split(); T0 = int(T0s); u = float(us)
    t0 = time.time(); z = Zg(T0, u); dt = time.time() - t0
    print(json.dumps(dict(T0=T0s, u=us, Z=z.str(30, radius=True), Z_mid=z.mid().str(25, radius=False), Z_rad=float(z.rad()), sec=dt,
                          maxrss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20)), flush=True)
