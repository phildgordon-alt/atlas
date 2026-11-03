"""M6: Turing count (Lemma T, THEORY_M5 section 4; separate method) at extra offsets v, from a SAVED scan directory (grid.npz +
zeros_intervals.json) with no zfast call.  The sign of Z(T0 + v) is read from the grid point u_k == v (exact binary64 equality
required; the point must be decided there, |mid| > rad).  Formulas identical to scan_turing2/3.py: Arb theta integrals (trapezoid
minus the theta'' ball term), Bober-Hiary B(x) = 0.128 log x + 2.30, Delta = 40 or less where the grid does not reach.
usage: turing_extra.py SCANDIR OUTJSON v1 v2 ... [--win a,b ...]    (OUTJSON must not exist)"""
import json, math, sys, os
import numpy as np
from flint import arb, acb, acb_series, ctx
SCAN = sys.argv[1]; OUT = sys.argv[2]; assert not os.path.exists(OUT)
vs = [float(x) for x in sys.argv[3:] if not x.startswith('--') and ',' not in x]
wins = [tuple(float(y) for y in x.split(',')) for x in sys.argv[3:] if ',' in x]
st = json.load(open(SCAN + '/scan_turing.json')); T0 = int(st['T0'])
fine = [tuple(x) for x in json.load(open(SCAN + '/zeros_intervals.json'))['intervals']]
g = np.load(SCAN + '/grid.npz'); u, m, r = g['u'], g['mid'], g['rad']
ulo, uhi = float(u[0]), float(u[-1])
ctx.prec = 300
def hx(v):
    from fractions import Fraction
    f = Fraction(T0) + Fraction(v); return arb(f.numerator) / arb(f.denominator)
def theta(t): return (acb(arb(1) / 4, t / 2).lgamma()).imag - t / 2 * arb.pi().log()
def theta2_ball(a, b):
    c = (a + b) / 2; rr = (b - a) / 2; t = c + arb(0, rr.upper())
    co = acb_series([acb(arb(1) / 4, t / 2), acb(0, arb(1) / 2)], 3).lgamma().coeffs(); return 2 * co[2].imag
def int_theta_pi_plus1(ua, ub):
    a, b = hx(ua), hx(ub); w = b - a
    I = w * (theta(a) + theta(b)) / 2 - w ** 3 / 12 * theta2_ball(a, b)
    return I / arb.pi() + w
def B(x): return arb('0.128') * x.log() + arb('2.30')
def Zsign(v):
    k = np.nonzero(u == v)[0]; assert len(k) == 1, f'{v} is not a grid point'; k = int(k[0])
    mid, rad = float(m[k]), float(r[k])
    sg = (1 if mid > 0 else -1) if abs(mid) > rad else 0
    return sg, dict(k=k, mid=mid, rad=rad)
def turing(v, D=40.0):
    sg, zd = Zsign(v)
    D = min(D, v - ulo, uhi - v - 1e-9)
    up = [(a, b) for a, b in fine if a >= v and b <= v + D]
    lo = [(a, b) for a, b in fine if b <= v and a >= v - D]
    Ip = int_theta_pi_plus1(v, v + D); Im = int_theta_pi_plus1(v - D, v)
    U = (B(hx(v + D)) + Ip - sum((hx(v + D) - hx(b) for a, b in up), arb(0))) / arb(D)
    Lb = (Im + sum((hx(a) - hx(v - D) for a, b in lo), arb(0)) - B(hx(v))) / arb(D)
    lo_i = int(arb(Lb.lower()).ceil().unique_fmpz()); hi_i = int(arb(U.upper()).floor().unique_fmpz())
    return dict(N_lower=lo_i, N_upper=hi_i, v=v, Z_sign=sg, Z_grid=zd, Delta=D, U=U.str(12, radius=False), L=Lb.str(12, radius=False),
                U_minus_L=float((U - Lb).upper()), zeros_up=len(up), zeros_down=len(lo), pinned=(lo_i == hi_i and sg != 0),
                N=(lo_i if lo_i == hi_i and sg != 0 else None))
pts = sorted(set(vs + [x for w in wins for x in w]))
TC = {str(v): turing(v) for v in pts}
def cnt(a, b): return (TC[str(b)]['N'] - TC[str(a)]['N']) if TC[str(a)]['N'] is not None and TC[str(b)]['N'] is not None else None
res = dict(T0=str(T0), scan=SCAN, turing=TC,
           windows={f'{a},{b}': dict(count=cnt(a, b), sign_changes_in_window=sum(1 for x, y in fine if x >= a and y <= b)) for a, b in wins})
json.dump(res, open(OUT, 'w'), indent=1); print(json.dumps(res['windows']), json.dumps({k: (v['N'], v['pinned'], round(v['U_minus_L'], 3), v['Delta']) for k, v in TC.items()}))
