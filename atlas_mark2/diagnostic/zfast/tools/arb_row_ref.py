"""Arb reference for rows: zeta, zeta' at s = 1/2 + pi/(2a) + i(T0+u) via acb_series([s,1],2).zeta() (atlas_v5's mzl construction),
precision 128 + bitlen(T0) (v5 uses 128).  Lines 'T0 u a' -> JSON."""
import sys, json, time, resource
from fractions import Fraction
from flint import arb, acb, ctx, acb_series
def hx(T0, u):
    f = Fraction(T0) + Fraction(u); p, q = f.numerator, f.denominator
    old = ctx.prec; ctx.prec = max(old, abs(p).bit_length() + q.bit_length() + 8)
    try: v = arb(p) / arb(q)
    finally: ctx.prec = old
    return v
for line in sys.stdin:
    if not line.strip(): continue
    T0s, us, as_ = line.split(); T0 = int(T0s)
    ctx.prec = 128 + T0.bit_length(); t0 = time.time()
    s = acb(arb(1) / 2 + arb.pi() / (2 * arb(float(as_))), hx(T0, float(us)))
    c = acb_series([s, 1], 2).zeta().coeffs(); P = (-c[1] / c[0]).real
    print(json.dumps(dict(T0=T0s, u=us, a=as_, zeta_re=c[0].real.str(25, radius=True), zeta_im=c[0].imag.str(25, radius=True),
        dzeta_re=c[1].real.str(25, radius=True), dzeta_im=c[1].imag.str(25, radius=True), P=P.str(25, radius=True), sec=time.time() - t0,
        maxrss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20)), flush=True)
