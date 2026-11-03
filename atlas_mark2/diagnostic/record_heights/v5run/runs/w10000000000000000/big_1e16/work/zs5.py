"""atlas_v5 sign changes of Hardy's Z in WORK coordinates (height = BASE + w exactly; atlas_v4 zs4.py with Z/sgn at exact heights;
the search logic is unchanged).  atlas_v4 docstring follows.
atlas_v4 sign changes of Hardy's Z (generator side, NOT trusted; every interval is re-verified by verify_zs at replay).
find(lo, hi, step): grid of step `step`; at every same-sign local minimum of |Z| (a possible close pair, Lehmer-type) DIP extra points
are inserted between the two neighbours; every bracket of opposite signs is bisected to width <= REFINE.  Uses zfun.Z / zfun.sgn
(Arb at 96 / 160 / 256 bits).  Returns sorted disjoint intervals [(t1, t2)] with Z(t1), Z(t2) of strictly opposite sign (as seen by Arb)."""
import os
from zfun5 import Z as _Z, sgn as _sgn

REFINE = float(os.environ.get('ZS_REFINE', '1e-4')); DIP = int(os.environ.get('ZS_DIP', '8'))
BASE = [0]


def Z(t, prec): return _Z(BASE[0], t, prec)


def sgn(t): return _sgn(BASE[0], t)


def _val(t):
    v = Z(t, 96)
    if v.lower() > 0 or v.upper() < 0: return float(v.mid())
    s = sgn(t)
    return 0.0 if s == 0 else s * 1e-300


def find(lo, hi, step, stats=None):
    n = int((hi - lo) / step); ts = [lo + k * step for k in range(n + 1)]
    if ts[-1] < hi: ts.append(hi)
    pts = {t: _val(t) for t in ts}; ev = len(ts); dips = 0
    for t0, t1, t2 in zip(ts, ts[1:], ts[2:]):
        z0, z1, z2 = pts[t0], pts[t1], pts[t2]
        if z0 * z1 > 0 and z1 * z2 > 0 and abs(z1) < abs(z0) and abs(z1) < abs(z2):
            dips += 1
            for j in range(1, 2 * DIP):
                t = t0 + (t2 - t0) * j / (2 * DIP)
                if t not in pts: pts[t] = _val(t); ev += 1
    seq = [(t, z) for t, z in sorted(pts.items()) if z != 0.0]
    out = []
    for (t1, z1), (t2, z2) in zip(seq, seq[1:]):
        if z1 * z2 >= 0: continue
        s1 = 1 if z1 > 0 else -1
        while t2 - t1 > REFINE:
            m = (t1 + t2) / 2; sm = sgn(m); ev += 1
            if sm == 0: break
            if sm == s1: t1 = m
            else: t2 = m
        out.append((t1, t2))
    if stats is not None: stats.update(evals=ev, dips=dips, grid=len(ts), intervals=len(out))
    return out
