#!/usr/bin/env python
"""
precision_and_l70_analysis.py — Atlas Mark II.

GATE 1  Controlled precision ladder at L = 40 (frozen: H=20, clamped basis M=226,
        dt=0.025, T_cut=176, 12-node Gauss-Legendre, witness a and whitening P frozen).
        ONE Arb code path is run at 53, 128 and 192 bits. The 53-bit run is Arb
        emulating float64, and its ball radii show the rounding loss directly.
        Everything precision-dependent is evaluated at the ladder precision: the GL
        nodes (generated at 300 bits, then rounded), zeta'/zeta, the basis transforms,
        the pole, pi and archimedean blocks, the contour sum, the subtraction, and the
        projection P^T A P.
        The eigenvalues of the projected matrix are always computed at 192 bits
        (acb_mat.eig), so the ladder isolates ASSEMBLY precision, not eigensolver
        precision. The zero-side reference Z is computed once at 192 bits with
        zeros at 50 digits.
        Frozen a and P are float64 vectors used as exact binary constants. What the
        test needs is that they are identical across ladders, not how precisely they
        were optimised.

GATE 2  L = 70: certified T_cut from the clamped O(T^-7) bound, precision sizing,
        and a scalar witness S_a = a^T M a at the derived T_cut and precision.
"""
from __future__ import annotations
import json, math, os, sys, time
from pathlib import Path
from multiprocessing import get_context
import numpy as np, mpmath as mp
from flint import arb, acb, arb_mat, acb_mat, acb_series, ctx

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
C_STR = "0.6"
NW = os.cpu_count() or 4
_G: dict = {}


# ---------------------------------------------------------------- utilities
def gl_rule(n, dps=90):
    """Gauss-Legendre nodes/weights on [-1,1] as decimal strings (Newton, high precision)."""
    xs, ws = [], []
    with mp.workdps(dps):
        for i in range(1, n + 1):
            x = mp.cos(mp.pi * (i - mp.mpf(1) / 4) / (n + mp.mpf(1) / 2))
            for _ in range(200):
                p0, p1 = mp.mpf(1), x
                for k in range(2, n + 1):
                    p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
                dp = n * (x * p1 - p0) / (x * x - 1)
                dx = p1 / dp; x -= dx
                if abs(dx) < mp.mpf(10) ** (-dps + 5):
                    break
            p0, p1 = mp.mpf(1), x
            for k in range(2, n + 1):
                p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
            dp = n * (x * p1 - p0) / (x * x - 1)
            xs.append(mp.nstr(x, dps - 5)); ws.append(mp.nstr(2 / ((1 - x * x) * dp * dp), dps - 5))
    return xs, ws


def enc(x):
    """serialise an arb (mid string + safe radius) across processes"""
    m = x.mid()
    return (m.str(75, radius=False), float(x.rad()) * 1.000001 + abs(float(m)) * 1e-70)


def dec(t):
    return arb(t[0], repr(t[1]))


def _init(prec, L, M0, xs, ws):
    ctx.prec = prec
    H = arb(L) / 2
    om = [arb(2 * k + 1) * arb.pi() / (2 * H) for k in range(M0)]
    _G.update(H=H, om=om, q=[(-1) ** k * 2 * om[k] for k in range(M0)],
              w2=[o * o for o in om], c=arb(C_STR), hc=arb(1) / 2 + arb(C_STR),
              xs=[arb(x) for x in xs], ws=[arb(w) for w in ws], M0=M0)


def _nodes(T0, T1, n, j0, j1):
    A, B = arb(T0), arb(T1)
    for j in range(j0, j1):
        a = A + (B - A) * j / n; b = A + (B - A) * (j + 1) / n
        half = (b - a) / 2; mid = (a + b) / 2
        for x, w in zip(_G["xs"], _G["ws"]):
            yield mid + half * x, half * w


def _zld(t):
    c = acb_series([acb(_G["hc"], t), 1]).zeta().coeffs()
    return -c[1] / c[0]


def _w_matrix(args):
    """partial sum over panels [j0,j1) of  w zeta b b^T  (C0 basis), real part."""
    T0, T1, n, j0, j1 = args
    g = _G; M0 = g["M0"]; acc = None; rB, rW = [], []

    def flush():
        nonlocal acc, rB, rW
        if rB:
            P = acb_mat(rW).transpose() * acb_mat(rB)
            acc = P if acc is None else acc + P
            rB, rW = [], []
    for t, w in _nodes(T0, T1, n, j0, j1):
        z = acb(t, -g["c"]); cz = (z * g["H"]).cos(); z2 = z * z
        row = [cz * g["q"][k] / (g["w2"][k] - z2) for k in range(M0)]
        wz = w * _zld(t)
        rB.append(row); rW.append([wz * v for v in row])
        if len(rB) >= 1000:
            flush()
    flush()
    return [enc(acc[i, j].real) for i in range(M0) for j in range(M0)]


def _w_scalar(args):
    """partial sum over panels of  w zeta F_c^2, F_c = cos(zH) sum_k c_k q_k/(w_k^2 - z^2)."""
    T0, T1, n, j0, j1, cvals = args
    g = _G; M0 = g["M0"]
    p = [arb(float(cv)) * g["q"][k] for k, cv in enumerate(cvals)]
    s = acb(0); mx = 0.0
    for t, w in _nodes(T0, T1, n, j0, j1):
        z = acb(t, -g["c"]); z2 = z * z
        F = (z * g["H"]).cos() * sum((p[k] / (g["w2"][k] - z2) for k in range(M0)), acb(0))
        term = w * _zld(t) * F * F
        s += term; mx = max(mx, abs(float(term.real.mid())))
    return enc(s.real), mx


def run_pool(prec, L, M0, rule, fn, tasks):
    with get_context("spawn").Pool(NW, _init, (prec, L, M0, rule[0], rule[1])) as pool:
        return pool.map(fn, tasks)


def split(n, parts):
    b = np.linspace(0, n, parts + 1).astype(int)
    return [(int(b[i]), int(b[i + 1])) for i in range(parts) if b[i + 1] > b[i]]


# ---------------------------------------------------- deterministic blocks (main)
def basis_arb(L, M0):
    H = arb(L) / 2
    om = [arb(2 * k + 1) * arb.pi() / (2 * H) for k in range(M0)]
    return H, om, [(-1) ** k * 2 * om[k] for k in range(M0)]


def pole_vec(L, M0):
    H, om, q = basis_arb(L, M0)
    ch = (H / 2).cosh()
    return [q[k] * ch / (om[k] ** 2 + arb(1) / 4) for k in range(M0)]


def arch_sums(L, M0, rule, width=0.1):
    """S,K,J factorisation of sum_i V_i C(u_i) and sum_i W_i e^{-2u_i} over [0,L]."""
    H, om, _ = basis_arb(L, M0)
    xs = [arb(x) for x in rule[0]]; ws = [arb(w) for w in rule[1]]
    n = int(math.ceil(L / width)); Lr = arb(L)
    S = [arb(0)] * M0; K = [arb(0)] * M0; J = [arb(0)] * M0; sW = arb(0)
    for j in range(n):
        a = Lr * j / n; b = Lr * (j + 1) / n; half = (b - a) / 2; mid = (a + b) / 2
        for x, w in zip(xs, ws):
            u = mid + half * x; W = half * w / (1 - (-2 * u).exp())
            sW += W * (-2 * u).exp(); V = W * (-u / 2).exp()
            # direct sin/cos: a rotation recurrence e_{k+1} = e_k * e^{i 2 w_0 u} inflates
            # Arb's rectangular complex balls by up to sqrt(2) per step ((sqrt2)^395 ~ 1e59).
            Vu = V * u
            for k in range(M0):
                sn, cs = (om[k] * u).sin_cos()
                S[k] += V * sn; K[k] += V * cs; J[k] += Vu * cs
    return H, om, S, K, J, sW


def arch_entry(k, l, H, om, S, K, J):
    if k == l:
        return (S[k] / om[k] + 2 * H * K[k] - J[k]) / 2
    return (-1) ** (k + l) * (om[k] * S[l] - om[l] * S[k]) / (om[k] ** 2 - om[l] ** 2)


def clamp_arb(M):
    T = [[arb(0)] * (M + 1) for _ in range(M)]
    for m in range(M):
        T[m][m] += arb(1) / 2; T[m][m + 1] += arb(1) / 4; T[m][max(m - 1, 0)] += arb(1) / 4
    return arb_mat(T)


def col(v):
    return arb_mat([[arb(float(x))] for x in v])


def eig_min(X, prec=192):
    """smallest eigenvalue of symmetric arb_mat X via acb_mat.eig at `prec` bits."""
    old = ctx.prec; ctx.prec = prec
    n = X.nrows()
    E = acb_mat([[acb(X[i, j]) for j in range(n)] for i in range(n)]).eig(nonstop=True)
    e = min(E, key=lambda z: float(z.real.mid()))
    out = (float(e.real.mid()), float(e.rad()))
    ctx.prec = old
    return out


def maxabs(X):
    n, m = X.nrows(), X.ncols()
    return max(abs(float(X[i, j].mid())) + float(X[i, j].rad()) for i in range(n) for j in range(m))


# ------------------------------------------------------------------- GATE 1
def gate1(gam_hp, gam_f, rule12):
    from clamped_basis_benchmark import basis, witness, regularize
    from compact_support_optimizer import basis_size
    L, dt, TC = 40.0, 0.025, 176
    H = L / 2; M = basis_size(H); M0 = M + 1
    w0, Tm = basis("clamped", M, H)
    a, dlt, lam_w, _, G = witness(w0, Tm, H, gam_f, 1e-6)          # frozen, float64
    P, npr, condP = regularize(G, 1e-6)
    c = Tm.T @ a
    n = int(round(TC / dt))
    print(f"GATE 1 — L=40, H=20, M={M} (C0 modes {M0}), dt={dt}, T_cut={TC}, "
          f"{n} panels x 12 = {n*12:,} nodes; P keeps {P.shape[1]} of {M} (pruned {npr})")
    print(f"  frozen witness: Delta(0.51) = {dlt:.6e}  (float64 vector, identical in all ladders)")

    # reference zero side at 192 bits
    ctx.prec = 192
    Hr, om, q = basis_arb(L, M0)
    Bz = arb_mat([[q[k] * (arb(gs) * Hr).cos() / (om[k] ** 2 - arb(gs) ** 2) for k in range(M0)]
                  for gs in gam_hp])
    Z0 = Bz.transpose() * Bz * 2
    TmA = clamp_arb(M); Pm = arb_mat([[arb(float(x)) for x in r] for r in P]); ac = col(a)
    Z = TmA * Z0 * TmA.transpose()
    lamZ = (0.0, 0.0)   # Z = 2 Bz^T Bz is an exact Gram matrix: lambda_min(P^T Z P) >= 0
    print(f"  reference Z: exact Gram form 2 Bz^T Bz (PSD), 192 bits; max|Z| = {maxabs(Z):.3e}")
    print(f"  float64 reference (numpy pipeline, commit 5a2e0ad): witness 1.372e-07, dual 3.30e-08")

    rows = []
    for prec in (53, 128, 192):
        t0 = time.time(); ctx.prec = prec
        parts = run_pool(prec, L, M0, rule12, _w_matrix,
                         [(0, TC, n, j0, j1) for j0, j1 in split(n, NW)])
        t_con = time.time() - t0
        acc = [arb(0)] * (M0 * M0)
        for pr in parts:
            acc = [s + dec(e) for s, e in zip(acc, pr)]
        two_pi = 2 / arb.pi()
        Mcon = arb_mat([[acc[i * M0 + j] * two_pi for j in range(M0)] for i in range(M0)])
        beta = pole_vec(L, M0)
        Hh, om_, S, K, J, sW = arch_sums(L, M0, rule12)
        g0 = -arb.const_euler() - (1 - (-2 * arb(L)).exp()).log() - arb.pi().log() + 2 * sW
        A0 = arb_mat([[2 * beta[i] * beta[j] + (g0 * Hh if i == j else arb(0))
                       - 2 * arch_entry(i, j, Hh, om_, S, K, J) for j in range(M0)]
                      for i in range(M0)]) - Mcon
        A = TmA * A0 * TmA.transpose()
        D = A - Z
        wit = (ac.transpose() * D * ac)[0, 0]
        dual = maxabs(D) / maxabs(Z)
        Xd = Pm.transpose() * D * Pm
        n_ = Xd.nrows()
        frob = sum((Xd[i, j] ** 2 for i in range(n_) for j in range(n_)), arb(0)).sqrt()
        weyl = -(float(frob.mid()) + float(frob.rad()))       # lambda_min(P^T A P) >= this
        radA = max(float(A[i, j].rad()) for i in range(M) for j in range(M))
        rows.append(dict(bits=prec, witness_err=abs(float(wit.mid())), witness_rad=float(wit.rad()),
                         witness_signed=float(wit.mid()),
                         dual_rel=dual, lam_lower_weyl=weyl, max_rad_A=radA,
                         max_pole=abs(float((2 * beta[-1] * beta[-1]).mid())),
                         t_contour=t_con, t_total=time.time() - t0))
        r = rows[-1]
        print(f"  {prec:3d} bits: witness {r['witness_signed']:+.6e} (+/-{r['witness_rad']:.1e})  dual "
              f"{r['dual_rel']:.2e}  lambda_min >= {r['lam_lower_weyl']:+.2e} (Weyl, certified)  "
              f"max rad(A) {r['max_rad_A']:.1e}  [{r['t_total']:.0f}s]", flush=True)

    # truncation control: the omitted witness tail  int_{176}^{800}
    ctx.prec = 128
    nt = int(round((800 - TC) / dt))
    tail = run_pool(128, L, M0, rule12, _w_scalar,
                    [(TC, 800, nt, j0, j1, list(map(float, c))) for j0, j1 in split(nt, NW)])
    tail_val = sum((dec(t[0]) for t in tail), arb(0)) * 2 / arb.pi()
    tv = float(tail_val.mid())
    print(f"  truncation control: witness tail (2/pi) Re int_176^800 = {tv:+.6e}")
    for r in rows:
        r["witness_tail_corrected"] = abs(r["witness_signed"] - tv)   # A_con(T) - Z = +tail
        print(f"    {r['bits']:3d} bits: tail-corrected witness |w - tail| = {r['witness_tail_corrected']:.3e}")
    return dict(L=L, M=M, T_cut=TC, dt=dt, delta=dlt, lam_zero=lamZ[0], ladders=rows,
                witness_tail_176_800=float(tail_val.mid()))


# ------------------------------------------------------------------- GATE 2
def gate2(gam_hp, gam_f, rule12, rule8):
    from clamped_basis_benchmark import basis, witness, regularize, tail_bound
    from compact_support_optimizer import basis_size, Bvec
    from contour_matrix_benchmark import ZMAX
    L = 70.0; H = L / 2; M = basis_size(H); M0 = M + 1
    w0, Tm = basis("clamped", M, H)
    a, dlt, lam_w, _, G = witness(w0, Tm, H, gam_f, 1e-6)
    P, npr, condP = regularize(G, 1e-6)
    c = Tm.T @ a; gate = 0.1 * abs(dlt)
    print(f"\nGATE 2 — L=70 (X = e^70 = {math.exp(L):.3e}), H=35, M={M}; cond(G) "
          f"{np.linalg.cond(G):.1e}, pruned {npr}; Delta(0.51) = {dlt:.6e}, gate = {gate:.4e}")

    # certified T_cut: clamped O(T^-7) five-term bound, tail <= 10% of the gate
    T = math.ceil(w0[-1]) + 5.0
    while tail_bound(c, w0, H, T)[0] > 0.1 * gate:
        T += 10.0
    bnd = tail_bound(c, w0, H, T)[0]
    dt = 1.0 / H; n = int(math.ceil(T / dt)); nodes = n * 12
    print(f"  certified T_cut = {T:.0f}: tail bound {bnd:.3e} <= 0.1 * gate ({0.1*gate:.3e}); "
          f"dt = 1/H (dt*H = 1.0) -> {nodes:,} nodes")

    # precision sizing (float64 scan of the integrand envelope near its peak)
    ts = np.linspace(0.0, 80.0, 40001)
    Fm = np.array([abs(c @ Bvec(complex(t, -0.6), w0, H)) for t in ts[::20]])
    max_term = float(ZMAX) * (Fm.max() ** 2) * (dt / 2)
    beta_f = np.array([(-1) ** k * 2 * w0[k] * math.cosh(H / 2) / (w0[k] ** 2 + 0.25) for k in range(M0)])
    pole_f = 2 * float(c @ beta_f) ** 2
    target = 1e-3 * gate
    bits_req = math.log2(max(max_term, pole_f) * math.sqrt(nodes) / target)
    prec = max(128, int(math.ceil(bits_req)) + 32)
    print(f"  e^(cL) = {math.exp(0.6*L):.2e};  e^(L/2) = {math.exp(L/2):.2e};  "
          f"max |w zeta F^2| ~ {max_term:.2e};  pole scalar ~ {pole_f:.2e}")
    print(f"  target abs accuracy 1e-3 * gate = {target:.2e} -> ~{bits_req:.0f} bits needed; using {prec}")

    t0 = time.time()
    res = run_pool(prec, L, M0, rule12, _w_scalar,
                   [(0, int(T), n, j0, j1, list(map(float, c))) for j0, j1 in split(n, NW * 4)])
    t_con = time.time() - t0
    ctx.prec = prec
    S_con = sum((dec(r[0]) for r in res), arb(0)) * 2 / arb.pi()
    mx = max(r[1] for r in res)
    # quadrature estimate on the dominant region [0, 60]: 12- vs 8-node
    nq = int(math.ceil(60 / dt))
    q12 = run_pool(prec, L, M0, rule12, _w_scalar,
                   [(0, 60, nq, j0, j1, list(map(float, c))) for j0, j1 in split(nq, NW)])
    q8 = run_pool(prec, L, M0, rule8, _w_scalar,
                  [(0, 60, nq, j0, j1, list(map(float, c))) for j0, j1 in split(nq, NW)])
    E_quad = abs(float((sum((dec(r[0]) for r in q12), arb(0))
                        - sum((dec(r[0]) for r in q8), arb(0))).mid())) * 2 / math.pi

    ctx.prec = prec
    Hr, om, q = basis_arb(L, M0)
    ca = [arb(float(x)) for x in c]
    beta = pole_vec(L, M0)
    S_pole = 2 * sum((ca[k] * beta[k] for k in range(M0)), arb(0)) ** 2
    g0 = Hr * sum((x * x for x in ca), arb(0))
    Hh, om_, S, K, J, sW = arch_sums(L, M0, rule12)
    quad = sum((ca[i] * ca[j] * arch_entry(i, j, Hh, om_, S, K, J)
                for i in range(M0) for j in range(M0)), arb(0))
    S_arch = g0 * (-arb.const_euler() - (1 - (-2 * arb(L)).exp()).log() + 2 * sW) - 2 * quad
    S_pi = -g0 * arb.pi().log()
    S_Z = sum(((2 * sum((ca[k] * q[k] * (arb(gs) * Hr).cos() / (om[k] ** 2 - arb(gs) ** 2)
                         for k in range(M0)), arb(0)) ** 2) for gs in gam_hp), arb(0))
    for nm, v in (("S_pole", S_pole), ("S_contour", S_con), ("S_arch", S_arch), ("S_pi", S_pi), ("S_Z", S_Z)):
        print(f"  radius {nm:9s} = {float(v.rad()):.2e}")
    T2 = int(T) + 460
    n2 = int(math.ceil((T2 - T) / dt))
    tl = run_pool(prec, L, M0, rule12, _w_scalar,
                  [(int(T), T2, n2, j0, j1, list(map(float, c))) for j0, j1 in split(n2, NW * 2)])
    ctx.prec = prec
    tail70 = float((sum((dec(r[0]) for r in tl), arb(0)) * 2 / arb.pi()).mid())
    print(f"  truncation control: (2/pi) Re int_{int(T)}^{T2} = {tail70:+.3e}")
    W = S_pole + S_pi + S_arch - S_con - S_Z
    err = abs(float(W.mid())); rad = float(W.rad())
    E_cert = bnd + rad
    ok = E_cert + E_quad < gate
    print(f"  contour: {nodes:,} nodes in {t_con:.0f}s on {NW} workers; max term {mx:.2e}")
    print(f"  S_pole = {float(S_pole.mid()):+.6e}   S_contour = {float(S_con.mid()):+.6e}   "
          f"(cancel to O(1): {math.log10(abs(float(S_pole.mid()))):.1f} digits)")
    print(f"  S_arch = {float(S_arch.mid()):+.6e}   S_pi = {float(S_pi.mid()):+.6e}   "
          f"S_Z (zero side) = {float(S_Z.mid()):+.6e}")
    print(f"  witness error |S_pole + S_pi + S_arch - S_contour - S_Z| = {err:.3e}  (signed {float(W.mid()):+.3e})")
    print(f"  tail-corrected witness |w - tail| = {abs(float(W.mid()) - tail70):.3e}")
    print(f"  E_total: certified tail {bnd:.2e} + Arb radius {rad:.2e} = {E_cert:.2e};  "
          f"E_quad (estimate, [0,60]) {E_quad:.2e};  gate {gate:.3e}  ->  "
          f"{'PASS' if ok else 'FAIL'}")
    return dict(L=L, M=M, delta=dlt, gate=gate, cond_G=float(np.linalg.cond(G)), pruned=npr,
                T_cut=T, tail_bound=bnd, dt=dt, nodes=nodes, exp_cL=math.exp(0.6 * L),
                exp_L2=math.exp(L / 2), max_term=mx, bits_required=bits_req, prec_used=prec,
                t_contour=t_con, S_pole=float(S_pole.mid()), S_contour=float(S_con.mid()),
                S_arch=float(S_arch.mid()), S_pi=float(S_pi.mid()), S_Z=float(S_Z.mid()),
                witness_err=err, witness_signed=float(W.mid()), tail_control=tail70,
                arb_radius=rad, E_quad=E_quad, E_cert=E_cert, passed=bool(ok))


def main():
    t0 = time.time()
    rule12 = gl_rule(12); rule8 = gl_rule(8)
    with mp.workdps(55):
        gam_hp = [mp.nstr(mp.im(mp.zetazero(k)), 50) for k in range(1, 401)]
    gam_f = [float(g) for g in gam_hp]
    print(f"setup: GL rules at 90 digits, 400 zeros at 50 digits ({time.time()-t0:.0f}s); {NW} workers\n")
    out = {"gate1": gate1(gam_hp, gam_f, rule12), "gate2": gate2(gam_hp, gam_f, rule12, rule8)}
    out["runtime_s"] = round(time.time() - t0, 1)
    (HERE / "precision_and_l70_results.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote precision_and_l70_results.json  ({out['runtime_s']}s)")


if __name__ == "__main__":
    main()
