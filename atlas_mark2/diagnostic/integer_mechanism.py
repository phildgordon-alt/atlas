#!/usr/bin/env python
"""
integer_mechanism.py -- exact real-versus-integer mechanism test on the frozen test set (diagnostic/integer_testset/,
docs/integer_count_translation.md).  ONE model per case; the continuous and integer versions differ ONLY by integrality.

Model (per case; candidate = the frozen pair's candidate orbit at (x0, delta0 = delta), unit weight):
  measurements   the pair's 306 ids (6 kernels x 51 centres), enclosures [E_lo, E_hi] from joint_primal_dual/measurements.json;
  window         [x0 - 3, x0 + 3], ordinate bins of width 0.02 (the frozen bins, with certified displacement limit d_max per bin);
  variables      on-line:  n_on[B] = number of zeros (with multiplicity) with beta = 1/2 and ordinate in B;       response u(g - t, 0)
                 off-line: n_off[B, S] = number of orbits {rho, 1 - conj rho} with ordinate in B and |beta - 1/2| in slab S, for
                           slabs S of (0, d_max(B)) cut at 0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4;                   response 2 u(g - t, d)
                 (u(r, d) = Re sech(a (r - i d)); every zero with ordinate in the window lies in exactly one variable, the candidate's orbit
                 excepted, which is fixed; the certified limits d_max are existing certificates);
  response bounds  per variable and measurement, [L, U] over the bin (and slab): u is decreasing in |r| for fixed d, and for fixed r
                 unimodal in d with maximum value coth(a r)/2 where cos(a d) = |sinh(a r)| (closed form, no numerical peak); enclosed in
                 Arb and rounded outward to binary64 rationals; mirror terms (ordinate + t ~ 2e4) are bounded by 1e-300;
  far remainder  zeros with ordinate outside the window: 0 <= contribution <= F_m, F_m = sum over unit shells of
                 [(theta(y) - theta(x))/pi + 2 S_max(y)] * cosh(a r)/sinh^2(a r) (r = distance from t to the shell's near edge), with
                 |S(T)| <= 0.112 log T + 0.278 log log T + 2.510 (Trudgian 2014), theta via Arb log-gamma, shells to distance 60, plus a
                 crude bound 1e-20 beyond;
  rows           for every measurement m:   sum n L_m + q0_lo,m <= E_hi,m     and     sum n U_m + q0_hi,m + F_m >= E_lo,m;
                 window count:  sum n_on + 2 sum n_off + 2 <= N_window (same N(T) bound);
  bounds         n <= (E_hi,m - q0_lo,m)/L_m for every m with L_m > 0 (valid for real counts; floored in the integer version, where
                 integrality implies the floor).
Certificates (exact rational arithmetic, fractions.Fraction):
  continuous infeasible  box-Farkas: y >= 0 with  sum_j min(0, (y^T A)_j) * ub_j > y^T b   (robust to rounding of y);
  continuous feasible    a rational point strictly inside every row (from the LP maximising a uniform slack), checked exactly;
  integer                floating-point MILP scouting first (labelled uncertified); an integer point is checked exactly; an
                         infeasibility claim is certified only by the exact branch-and-bound of stage 2 (not yet run).
No zero data is used.  No statement about RH is made.
"""
from __future__ import annotations
import json, math, sys, time
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
from flint import arb, acb, ctx

DIAG = Path(__file__).resolve().parent; TS = DIAG / "integer_testset"; OUT = DIAG / "integer_mechanism"
SLABS = (0.0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5); TINY = 1e-300
ctx.prec = 128


def dn(x): return math.nextafter(float(x), -math.inf)
def up(x): return math.nextafter(float(x), math.inf)


def u_arb(a, r, d):
    return (1 / (arb(a) * acb(arb(r), -arb(d))).cosh()).real


def bounds(a, g0, g1, t, d0, d1):
    """[L, U] of u(g - t, d) over g in [g0, g1], d in [d0, d1] (d1 <= 1/2).  Returns floats rounded outward."""
    r0, r1 = g0 - t, g1 - t
    far = max(abs(r0), abs(r1)); near = 0.0 if (r0 < 0 < r1) else min(abs(r0), abs(r1))
    if d1 == 0:
        return dn(u_arb(a, far, 0).lower()), up(u_arb(a, near, 0).upper()) + TINY
    L = min(u_arb(a, far, d0).lower(), u_arb(a, far, d1).lower())
    A = arb(a); s = (A * arb(near)).sinh(); c0, c1 = (A * arb(d0)).cos(), (A * arb(d1)).cos()   # c decreasing in d
    U = max(u_arb(a, near, d0).upper(), u_arb(a, near, d1).upper())
    if not (s > c0 or s < c1):                                              # peak (c = s) possibly inside [d0, d1]
        U = max(U, (((A * arb(near)).cosh() / (A * arb(near)).sinh()) / 2).upper() if near > 0 else U)
    return dn(L), up(U) + TINY


def theta_arb(t):
    return acb(arb(1) / 4, arb(t) / 2).lgamma().imag - arb(t) / 2 * arb.pi().log()


def Smax(T): return arb("0.112") * arb(T).log() + arb("0.278") * arb(T).log().log() + arb("2.510")


_CU = {}


def count_upper(x, y):
    k = (x, y)
    if k not in _CU: _CU[k] = arb(((theta_arb(y) - theta_arb(x)) / arb.pi() + 2 * Smax(y)).upper())
    return _CU[k]


def far_bound(a, t, wlo, whi):
    tot = arb(0); A = arb(a)
    for side in (+1, -1):
        edge = whi if side > 0 else wlo
        for k in range(0, 60):
            x0 = edge + side * k; x1 = edge + side * (k + 1); lo_, hi_ = min(x0, x1), max(x0, x1)
            r = abs(x0 - t)
            tot += count_upper(lo_, hi_) * ((A * arb(r)).cosh() / (A * arb(r)).sinh() ** 2)
    return up(tot.upper()) + 1e-20


def build(case, meas):
    r = json.loads((TS / f"{case['id']}.json").read_text())
    x0, d0c = case["candidate"]["x0"], case["delta"]; wlo, whi = case["window"]
    ids = r["measurement_ids"]; M = len(ids)
    vars_ = []                                                              # (kind, b0, b1, s0, s1)
    for b0, b1, dm in case["bins"]:
        vars_.append(("on", b0, b1, 0.0, 0.0))
        for s0, s1 in zip(SLABS[:-1], SLABS[1:]):
            if s0 >= dm: break
            vars_.append(("off", b0, b1, s0, min(s1, dm)))
    n = len(vars_); Lm = np.zeros((M, n)); Um = np.zeros((M, n)); Elo = np.zeros(M); Ehi = np.zeros(M); q0lo = np.zeros(M); q0hi = np.zeros(M); F = np.zeros(M)
    for m, key in enumerate(ids):
        a_s, t_s = key.split("|"); a, t = float(a_s), float(t_s); E = arb(meas[key])
        Elo[m], Ehi[m] = dn(E.lower()), up(E.upper())
        q = 2 * u_arb(a, x0 - t, d0c); q0lo[m], q0hi[m] = dn(q.lower()), up(q.upper()) + TINY
        F[m] = far_bound(a, t, wlo, whi)
        for j, (kind, b0, b1, s0, s1) in enumerate(vars_):
            L_, U_ = bounds(a, b0, b1, t, s0, s1)
            f = 1.0 if kind == "on" else 2.0
            Lm[m, j], Um[m, j] = dn(f * L_), up(f * U_)
    Nwin = up(count_upper(wlo, whi).upper())
    w = np.array([1.0 if k == "on" else 2.0 for k, *_ in vars_])
    ub = np.full(n, np.inf)
    for j in range(n):
        for m in range(M):
            if Lm[m, j] > 0: ub[j] = min(ub[j], up((Ehi[m] - q0lo[m]) / Lm[m, j]))
        ub[j] = min(ub[j], Nwin / w[j])
    # rows A x <= b:  L x <= Ehi - q0lo ;  -U x <= -(Elo - q0hi - F) ;  w x <= Nwin - 2
    A = np.vstack([Lm, -Um, w[None, :]]); b = np.concatenate([Ehi - q0lo, -(Elo - q0hi - F), [Nwin - 2]])
    return dict(vars=vars_, A=A, b=b, ub=ub, M=M, F=F, Nwin=Nwin)


def farkas_certificate(A, b, ub, y):
    """exact check: y >= 0 and sum_j min(0, (y^T A)_j) ub_j > y^T b  =>  no x in [0, ub] with A x <= b."""
    yF = [Fr(max(float(v), 0.0)) for v in y]; lhs = Fr(0)
    for j in range(A.shape[1]):
        c = sum((yF[i] * Fr(float(A[i, j])) for i in range(A.shape[0]) if yF[i]), Fr(0))
        if c < 0: lhs += c * Fr(float(ub[j]))
    rhs = sum((yF[i] * Fr(float(b[i])) for i in range(len(b)) if yF[i]), Fr(0))
    return lhs > rhs, float(lhs - rhs)


def solve_continuous(mod):
    from scipy.optimize import linprog
    A, b, ub = mod["A"], mod["b"], mod["ub"]; n = A.shape[1]
    # max slack s:  A x + s <= b, 0 <= x <= ub, s <= 1
    r = linprog(np.concatenate([np.zeros(n), [-1.0]]), A_ub=np.hstack([A, np.ones((len(b), 1))]), b_ub=b,
                bounds=[(0, u) for u in ub] + [(None, 1.0)], method="highs")
    if r.status != 0: return dict(status="solver status %d" % r.status)
    s = -r.fun
    if s > 0:
        x = [Fr(float(v)) for v in np.clip(r.x[:n], 0, ub)]
        ok = all(sum((Fr(float(A[i, j])) * x[j] for j in range(n) if x[j]), Fr(0)) <= Fr(float(b[i])) for i in range(len(b)))
        return dict(status="FEASIBLE (certified rational interior point)" if ok else "feasible in float, exact check failed", slack=float(s), certified=ok)
    y = -np.array(r.ineqlin.marginals)                                     # duals of the slack LP give a Farkas direction
    ok, gap = farkas_certificate(A, b, ub, y)
    return dict(status="INFEASIBLE (certified box-Farkas)" if ok else "infeasible in float, Farkas check failed", slack=float(s), certified=ok, farkas_gap=gap,
                farkas_y=[[i, float(v)] for i, v in enumerate(np.clip(y, 0, None)) if v > 0])


def scout_integer(mod):
    from scipy.optimize import milp, LinearConstraint, Bounds
    A, b, ub = mod["A"], mod["b"], mod["ub"]; n = A.shape[1]
    ubi = np.floor(np.minimum(ub, 1e6))
    r = milp(np.zeros(n), constraints=LinearConstraint(A, -np.inf, b), integrality=np.ones(n), bounds=Bounds(np.zeros(n), ubi),
             options=dict(time_limit=600))
    out = dict(status=r.status, message=r.message, integer_upper_bounds_max=float(ubi.max()), integer_upper_bounds_sum=float(ubi.sum()))
    if r.x is not None:
        x = [Fr(int(round(v))) for v in r.x]
        ok = all(sum((Fr(float(A[i, j])) * x[j] for j in range(n) if x[j]), Fr(0)) <= Fr(float(b[i])) for i in range(len(b)))
        out.update(integer_point_certified=ok, nonzero=int(sum(1 for v in x if v)))
    return out


def main():
    t0 = time.time(); OUT.mkdir(exist_ok=True)
    T = json.loads((TS / "testset.json").read_text()); meas = json.loads((DIAG / "joint_primal_dual" / "measurements.json").read_text())
    res = []
    only = sys.argv[1:]
    for case in T["cases"]:
        if only and case["id"] not in only: continue
        ts = time.time(); mod = build(case, meas); tb = time.time() - ts
        c = solve_continuous(mod); tc = time.time() - ts - tb
        g = scout_integer(mod); tg = time.time() - ts - tb - tc
        abl = {}
        for name in ("no count row", "no displacement limits", "neither"):
            c2 = dict(case, bins=[[b0, b1, 0.5] for b0, b1, _ in case["bins"]]) if name != "no count row" else case
            m2 = build(c2, meas) if name != "no count row" else dict(mod)
            if name in ("no count row", "neither"): m2 = dict(m2, A=m2["A"][:-1], b=m2["b"][:-1])
            cc = solve_continuous(m2); abl[name] = dict(status=cc["status"], slack=cc["slack"])
        rec = dict(id=case["id"], variables=len(mod["vars"]), rows=len(mod["b"]), far_max=float(mod["F"].max()), N_window=mod["Nwin"],
                   continuous=c, integer_scouting=g, ablations=abl,
                   model=dict(window=case["window"], bin_width=case["bin_width"], slabs=SLABS, candidate=case["candidate"], delta=case["delta"],
                              ub=[float(v) for v in mod["ub"]], rows="0..M-1: upper rows L x <= Ehi - q0lo; M..2M-1: -U x <= -(Elo - q0hi - F); 2M: window count"),
                   seconds=dict(build=round(tb, 1), continuous=round(tc, 1), integer=round(tg, 1)))
        res.append(rec)
        print(f"{case['id']}: {len(mod['vars'])} vars, far <= {rec['far_max']:.3g}, N_window <= {mod['Nwin']:.2f} | continuous: {c['status']} "
              f"(slack {c.get('slack')}) | integer scouting (uncertified): status {g['status']} {g['message'][:60]}; "
              f"integer point certified {g.get('integer_point_certified')} | ablations {{{', '.join(k + ': ' + v['status'].split(' ')[0] for k, v in abl.items())}}} | {rec['seconds']}", flush=True)
    (OUT / "results.json").write_text(json.dumps(dict(script="diagnostic/integer_mechanism.py", results=res, runtime=round(time.time() - t0, 1)), indent=1) + "\n")


if __name__ == "__main__":
    main()
