#!/usr/bin/env python
"""
frequency_localized_sweep.py — Atlas Mark II, null-carrier single-kernel sweep at L = 70 (H = 35),
with a rigorous interval enclosure of J(beta, gamma) = W_bg + Q.

KERNEL  f_nu(u) = cos^2(pi u/2H) cos(nu u) on [-H,H]   (C^1: f, f' vanish at +-H)
        F_0(w) = a^2 sin(wH)/(w(a^2 - w^2)), a = pi/H;   F_nu(z) = [F_0(z-nu) + F_0(z+nu)]/2
        h = F_nu^2 >= 0 on R;  g(0) = ||f_nu||^2 in closed form;  g(t) closed form (3x3 cosines)

QUANTITIES (all divided by g(0))
  W_bg = [2F(i/2)^2 - g0 log pi + arch - S_con] / g0,   S_con = (2/pi) Re int_0^inf phi(t) dt,
         phi(t) = (-zeta'/zeta)(1/2 + c + it) F_nu(t - ic)^2,  c = 0.6
  Q    = 4 Re[F_nu(gamma + i delta)^2] / g0      (quartet at beta + i gamma added to the zero side)
  CERTIFIED  <=>  the upper endpoint u of the enclosure of J = W_bg + Q satisfies u < 0;  m_cert = -u.

WHAT IS ENCLOSED (every term below is an Arb ball or a rigorous Arb upper bound)
  * Gauss-Legendre rule: 12 nodes from Newton at 90 digits, each certified by a sign change of
    P_12 on [x - 1e-80, x + 1e-80] (12 disjoint intervals, 12 roots: exactly one each); weights
    evaluated on those balls.  The Arb sums therefore enclose the EXACT Gauss sums.
  * Quadrature remainder (Trefethen 2008, Thm 4.5): for f analytic in the Bernstein ellipse E_rho of
    a panel of half-width hp, |I - G_n| <= (64/15) hp M rho^{-2n} / (rho^2 - 1), M = sup_{E_rho}|f|,
    with M from an Arb evaluation on the enclosing rectangle.
      contour: phi analytic for Im t < 0.1 (pole of zeta'/zeta at s = 1 is t = 0.1i; zeros have
               Im t >= 0.1).  Ellipse half-height B = 0.09; on it Re s >= 1.01, so
               |zeta'/zeta| <= sum Lambda(n) n^{-1.01} = -zeta'/zeta(1.01)  (Arb).  rho ~ 12.7.
      arch:    integrand analytic for Re u > 0, |Im u| < pi, with a REMOVABLE singularity at u = 0
               that any ellipse around [0, w] would contain.  Hence a geometric mesh [w/2^k, w/2^(k-1)]
               (rho = 3, ellipses stay in Re u > 0), uniform panels beyond (rho = 5), and on [0, u0]:
               |psi| <= (2.5 g0 + sqrt(g0)(nu + a/2) sqrt(2H)) / (2 e^{-2 u0})  (mean value bound).
  * Tail t > T: |F_nu(t-ic)| <= a^2 cosh(cH)/(s(s^2-a^2)), s = t - nu, and |zeta'/zeta| <= -zeta'/zeta(1.1)
    (Arb, NOT a truncated float literal) => tail <= (2/pi) Z a^4 cosh^2(cH) kappa^2 / (5 s0^5).
  * Pole, g(0), Q and the archimedean closed forms: Arb balls.
NOT enclosed / NOT claimed: the zero-side sum (400 zeros) is used only to SELECT nu and as a cross-check.
"""
from __future__ import annotations
import json, math, os, sys, time
from pathlib import Path
from multiprocessing import get_context
import numpy as np, mpmath as mp
from flint import arb, acb, acb_series, ctx

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from precision_and_l70_analysis import gl_rule, enc, dec, split

L = 70.0; HF = L / 2; C_STR = "0.6"; PREC = 128
GAMMAS = (14.134725, 25.0, 50.0, 75.0, 100.0)
BETAS = ("0.501", "0.505", "0.51", "0.55", "0.60")
NPH = 35                       # contour panels per unit t (dt = 1/35, dt*H = 1)
B_CONTOUR = "0.09"             # Bernstein-ellipse half-height for the contour (< 0.1)
NG = 52                        # graded archimedean panels toward u = 0
NW = os.cpu_count() or 4
FROZEN = HERE / "frequency_localized_frozen_carriers.json"
_K: dict = {}


# ------------------------------------------------ float64 model (carrier SELECTION only)
AF = math.pi / HF
def F0f(w):
    w = np.asarray(w, complex)
    return np.where(np.abs(w) < 1e-12, HF, AF * AF * np.sin(w * HF) / (w * (AF * AF - w * w)))
def Ff(z, nu): return 0.5 * (F0f(z - nu) + F0f(z + nu))
def Sf(x): return 2 * np.sin(x * HF) / x
def g0f(nu):
    return 3 * HF / 8 + (3 * Sf(2 * nu) + 2 * Sf(2 * nu + AF) + 2 * Sf(2 * nu - AF)
                         + 0.5 * Sf(2 * nu + 2 * AF) + 0.5 * Sf(2 * nu - 2 * AF)) / 16
def select_nu(gt, delta, gz, span=1.5, step=5e-4):
    nus = gt + np.arange(-span, span + step / 2, step); g0 = g0f(nus)
    J = (2 * np.abs(Ff(gz[:, None], nus[None, :])) ** 2).sum(axis=0) / g0 \
        + 4 * np.real(Ff(gt + 1j * delta, nus) ** 2) / g0
    i = int(np.argmin(J)); return float(nus[i]), float(J[i])


# ------------------------------------------------ Arb pieces
def consts():
    H = arb(L) / 2; return H, arb.pi() / H, arb(C_STR)
def F0a(w, H, a):
    # denominator factored: a^2 - w^2 = (a - w)(a + w).  Squaring a wide rectangular ball
    # overestimates enough to contain 0 near w ~ 0 (t ~ nu); the shifted factors do not.
    return a * a * (w * H).sin() / (w * (a - w) * (a + w))
def Fa(z, nu, H, a): return (F0a(z - nu, H, a) + F0a(z + nu, H, a)) / 2
def g0a(nu, H, a):
    S = lambda x: 2 * (x * H).sin() / x
    return 3 * H / 8 + (3 * S(2 * nu) + 2 * S(2 * nu + a) + 2 * S(2 * nu - a)
                        + S(2 * nu + 2 * a) / 2 + S(2 * nu - 2 * a) / 2) / 16
def Ccorr(t, n1, n2, H, same):
    lo, hi = t - H, H; S = n1 + n2
    t1 = ((S * hi - n2 * t).sin() - (S * lo - n2 * t).sin()) / S
    if same:                      # n1 - n1 is a ball [0 +/- r] in Arb, not an exact zero
        t2 = (hi - lo) * (n2 * t).cos()
    else:
        D = n1 - n2
        t2 = ((D * hi + n2 * t).sin() - (D * lo + n2 * t).sin()) / D
    return (t1 + t2) / 2
def ga(t, nu, H, a):
    ns = (nu, nu + a, nu - a); al = (arb(1) / 2, arb(1) / 4, arb(1) / 4)
    return sum((al[i] * al[j] * Ccorr(t, ns[i], ns[j], H, i == j) for i in range(3) for j in range(3)),
               arb(0))
def up(x):                        # rigorous float upper bound of a real ball
    return (float(x.mid()) + float(x.rad())) * (1 + 2e-15) + 1e-300
def ball(mid, halfwidth):         # real ball [mid - hw, mid + hw] with hw rounded up
    return mid + arb(0, repr(up(halfwidth)))
def zeta_logderiv_bound(sigma_str):
    old = ctx.prec; ctx.prec = 256
    c = acb_series([acb(arb(sigma_str)), 1]).zeta().coeffs(); v = (-c[1] / c[0]).real
    ctx.prec = old; return repr(up(v))


def gl_rule_certified(n):
    """Gauss-Legendre nodes/weights as Arb balls that provably contain the exact values."""
    xs, _ = gl_rule(n)
    old = ctx.prec; ctx.prec = 330
    def P(x):
        p0, p1 = arb(1), x
        for k in range(2, n + 1):
            p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
        return p0, p1
    eps = arb("1e-80"); X, W = [], []
    for s in xs:
        x = arb(s)
        assert (P(x - eps)[1] * P(x + eps)[1]) < 0, "node not isolated"
        xb = x + arb(0, "1e-80")
        p0, p1 = P(xb); dp = n * (xb * p1 - p0) / (xb * xb - 1)
        X.append(enc(xb)); W.append(enc(2 / ((1 - xb * xb) * dp * dp)))
    ctx.prec = old
    return X, W


# ------------------------------------------------ workers
def _init(prec, X, W, nus, zb_str):
    ctx.prec = prec
    H, a, c = consts()
    hp = arb(1) / (2 * NPH); Bc = arb(B_CONTOUR)
    q = 2 * Bc / hp; rho = (q + (q * q + 4).sqrt()) / 2          # rho - 1/rho = 2B/hp
    _K.update(H=H, a=a, c=c, hc=arb(1) / 2 + c, X=[dec(x) for x in X], W=[dec(w) for w in W],
              nus=[arb(float(v)) for v in nus], hp=hp, Bc=Bc, Ac=hp * (rho + 1 / rho) / 2,
              coefC=arb(64) / 15 * hp * rho ** (-24) / (rho * rho - 1) * arb(zb_str), rho=rho)


def _w_contour(args):
    j0, j1, cut = args
    g = _K; H, a = g["H"], g["a"]; nk = len(g["nus"])
    sums = [acb(0)] * nk
    for j in range(j0, j1):
        act = [k for k in range(nk) if j < cut[k]]
        if not act:
            continue
        mid = (arb(2 * j + 1)) / (2 * NPH); hp = g["hp"]
        for x, w in zip(g["X"], g["W"]):
            t = mid + hp * x
            zc = acb_series([acb(g["hc"], t), 1]).zeta().coeffs(); zl = -zc[1] / zc[0]
            z = acb(t, -g["c"]); wz = hp * w * zl
            for k in act:
                F = Fa(z, g["nus"][k], H, a); sums[k] += wz * F * F
    return [enc(s_.real) for s_ in sums]


def contour_quad_bound(nu, cut, zb_str):
    """
    Rigorous Gauss-Legendre remainder for the contour, summed over panels j < cut.
    Per panel, sup |phi| over the rectangle enclosing the Bernstein ellipse is bounded ANALYTICALLY:
      |zeta'/zeta| <= Z_B (Re s >= 1.01 there);  F_0(w) = a^2 sin(wH)/(w (a-w)(a+w)) with
      |sin(wH)| <= cosh(H max|Im w|) and each factor >= distance from the rectangle to 0, a, -a.
    (Arb evaluation of F on the wide rectangle overestimates by ~1e9 and can contain 0.)
    Float arithmetic with explicit outward margins; transcendental constants from Arb.
    """
    hp = 1.0 / (2 * NPH); B = float(B_CONTOUR); q = 2 * B / hp
    rho = (q + math.sqrt(q * q + 4)) / 2 * (1 - 1e-12)             # lower bound on rho
    Ac = hp * (rho / (1 - 1e-12) + 1 / rho) / 2 * (1 + 1e-12)      # rectangle half-width (up)
    old = ctx.prec; ctx.prec = 128
    H, a, c = consts()
    ch = up((H * (c + arb(B_CONTOUR))).cosh()); a2 = up(a * a); af = float(a.mid())
    ctx.prec = old
    ylo = 0.6 - B - 1e-12                                           # min |Im w| (>= 0.51)
    tm = (2 * np.arange(cut) + 1) / (2 * NPH)
    def Fbound(center):                                             # w-rectangle [center +- Ac] x [-c +- B]
        def dist(p):
            dx = np.maximum(0.0, np.maximum((center - Ac) - p, p - (center + Ac)))
            dx = np.maximum(0.0, dx - 1e-9)
            return np.sqrt(dx * dx + ylo * ylo) * (1 - 1e-12)
        return a2 * ch / (dist(0.0) * dist(af) * dist(-af)) * (1 + 1e-12)
    Fb = 0.5 * (Fbound(tm - nu) + Fbound(tm + nu))
    coef = 64.0 / 15.0 * hp * rho ** (-24) / (rho * rho - 1) * float(zb_str)
    return float(np.sum(coef * Fb * Fb)) * (1 + 1e-9)


def _w_arch(args):
    k, width = args
    g = _K; H, a = g["H"], g["a"]; nu = g["nus"][k]; Lr = arb(L)
    g0 = g0a(nu, H, a)
    def psi(u):
        e2 = (-2 * u).exp()
        return (e2 * g0 - (-u / 2).exp() * ga(u, nu, H, a)) / (1 - e2)
    def panel(lo, hi, rho):
        half = (hi - lo) / 2; mid = (lo + hi) / 2
        s = sum((half * w * psi(mid + half * x) for x, w in zip(g["X"], g["W"])), arb(0))
        ub = acb(ball(mid, half * (rho + 1 / rho) / 2), ball(arb(0), half * (rho - 1 / rho) / 2))
        e = arb(64) / 15 * half * abs(psi(ub)) * rho ** (-24) / (rho * rho - 1)
        return s, e
    w = arb(width); acc = arb(0); err = arb(0)
    for kk in range(1, NG + 1):                                     # graded toward u = 0
        s, e = panel(w / arb(2) ** kk, w / arb(2) ** (kk - 1), arb(3)); acc += s; err += e
    n = int(math.ceil((L - float(width)) / float(width)))
    for j in range(n):                                              # uniform on [w, L]
        s, e = panel(w + (Lr - w) * j / n, w + (Lr - w) * (j + 1) / n, arb(5)); acc += s; err += e
    u0 = w / arb(2) ** NG
    e0 = u0 * (arb(5) / 2 * g0 + g0.sqrt() * (nu + a / 2) * (2 * H).sqrt()) / (2 * (-2 * u0).exp())
    arch = -arb.const_euler() * g0 + 2 * acc - g0 * (1 - (-2 * Lr).exp()).log()
    return enc(arch), repr(up(2 * (err + e0))), repr(up(2 * e0))


def pool(X, W, nus, zb, fn, tasks):
    with get_context("spawn").Pool(NW, _init, (PREC, X, W, nus, zb)) as p:
        return p.map(fn, tasks)


def tail_raw(nu, T, zmax_str):
    H, a, c = consts()
    s0 = arb(T) - arb(float(nu)); kap = 1 / (1 - a * a / (s0 * s0))
    return 2 / arb.pi() * arb(zmax_str) * a ** 4 * (c * H).cosh() ** 2 * kap ** 2 / (5 * s0 ** 5)


# ------------------------------------------------ main
def main():
    t_all = time.time(); ctx.prec = PREC
    X, W = gl_rule_certified(12)
    zmax = zeta_logderiv_bound("1.1"); zb = zeta_logderiv_bound(str(1.1 - float(B_CONTOUR)))
    print(f"GL-12 nodes certified (sign change of P_12, radius 1e-80); "
          f"-zeta'/zeta(1.1) <= {float(zmax):.9f}, -zeta'/zeta(1.01) <= {float(zb):.6f}")
    with mp.workdps(55):
        gz_hp = [mp.nstr(mp.im(mp.zetazero(k)), 50) for k in range(1, 401)]
    gz = np.array([float(x) for x in gz_hp])

    if FROZEN.exists():
        kers = json.loads(FROZEN.read_text())["kernels"]
        print(f"carriers frozen from {FROZEN.name} ({len(kers)} kernels)")
    else:                                                        # (first run only)
        kers = [dict(kind="centered", gamma=g, beta=None, nu=g) for g in GAMMAS]
        for g in GAMMAS:
            for b in BETAS:
                nu, J = select_nu(g, float(b) - 0.5, gz)
                kers.append(dict(kind="optimised", gamma=g, beta=b, nu=nu, J_est=J))
        raise SystemExit("no frozen carriers; run selection first")
    nus = [k["nu"] for k in kers]; nmax = max(k["cut"] for k in kers)
    print(f"shared contour grid: dt = 1/{NPH}, T_max = {nmax/NPH:.0f}, {nmax*12:,} nodes; "
          f"Bernstein half-height {B_CONTOUR}\n")

    t0 = time.time()
    parts = pool(X, W, nus, zb, _w_contour,
                 [(j0, j1, [k["cut"] for k in kers]) for j0, j1 in split(nmax, NW * 6)])
    t_con = time.time() - t0
    arch = pool(X, W, nus, zb, _w_arch,
                [(i, min(0.1, 1.5 / max(k["nu"], 1.0))) for i, k in enumerate(kers)])
    print(f"contour {t_con:.0f}s, archimedean {time.time()-t0-t_con:.0f}s\n")

    ctx.prec = PREC
    H, a, c = consts()
    for i, k in enumerate(kers):
        nu = arb(float(k["nu"])); g0 = g0a(nu, H, a)
        S_con = sum((dec(p[i]) for p in parts), arb(0)) * 2 / arb.pi()
        Eq_con = 2 / arb.pi() * arb(repr(contour_quad_bound(k["nu"], k["cut"], zb)))
        Etail = tail_raw(k["nu"], k["T"], zmax)
        arch_b, Eq_arch, E0 = dec(arch[i][0]), arb(arch[i][1]), arb(arch[i][2])
        pole = 2 * Fa(acb(0, arb(1) / 2), nu, H, a).real ** 2
        R_con = up(Eq_con + Etail); R_arch = up(Eq_arch)
        W_b = (pole - g0 * arb.pi().log() + arch_b + arb(0, repr(R_arch))
               - (S_con + arb(0, repr(R_con)))) / g0
        k.update(g0=float(g0.mid()), E_tail=up(Etail / g0), E_quad_contour=up(Eq_con / g0),
                 E_quad_arch=up(Eq_arch / g0), E_u0=up(E0 / g0), arith_rad=float(S_con.rad()),
                 W_bg=float(W_b.mid()), W_rad=float(W_b.rad()),
                 S_con=float(S_con.mid()), S_con_rad=float(S_con.rad()),
                 arch=float(arch_b.mid()), pole=float(pole.mid()))
        Wz = sum((2 * Fa(acb(arb(s)), nu, H, a).real ** 2 for s in gz_hp), arb(0)) / g0
        k["W_zero"] = float(Wz.mid())
        k["cells"] = {}
        for b in (BETAS if k["kind"] == "centered" else (k["beta"],)):
            Fz = Fa(acb(arb(float(k["gamma"])), arb(b) - arb(1) / 2), nu, H, a)
            Q = 4 * (Fz * Fz).real / g0
            J = W_b + Q
            lo = float(J.mid()) - float(J.rad()) * (1 + 2e-15); u_ = up(J)
            k["cells"][b] = dict(Q=float(Q.mid()), J_lo=lo, J_hi=u_,
                                 status="CERTIFIED" if u_ < 0 else "UNRESOLVED",
                                 m_cert=(-u_ if u_ < 0 else None))

    opt = {(k["gamma"], k["beta"]): k for k in kers if k["kind"] == "optimised"}
    cen = {k["gamma"]: k for k in kers if k["kind"] == "centered"}
    print("ENCLOSURE of J = W_bg + Q  (null-carrier kernels; CERTIFIED iff upper endpoint < 0)")
    print(f"  {'gamma':>9s} {'beta':>6s} {'nu-gamma':>9s} {'J lower':>12s} {'J upper':>12s} "
          f"{'status':>10s} {'m_cert':>10s} {'T_cut':>6s} {'E_tail':>8s} {'Eq_con':>8s} "
          f"{'Eq_arch':>8s} {'arith rad':>9s}")
    ncert = 0
    for g in GAMMAS:
        for b in BETAS:
            k = opt[(g, b)]; cl = k["cells"][b]; ncert += cl["status"] == "CERTIFIED"
            mc = f"{cl['m_cert']:.3e}" if cl["m_cert"] else "—"
            print(f"  {g:9.4f} {b:>6s} {k['nu']-g:+9.5f} {cl['J_lo']:+12.4e} {cl['J_hi']:+12.4e} "
                  f"{cl['status']:>10s} {mc:>10s} {k['T']:6.0f} {k['E_tail']:8.1e} "
                  f"{k['E_quad_contour']:8.1e} {k['E_quad_arch']:8.1e} {k['arith_rad']:9.1e}")
    print(f"\n  {ncert}/25 CERTIFIED.")
    worst = max(max(abs(k['W_bg'] - k['W_zero']) for k in kers), 0)
    print(f"  cross-check W_bg (enclosed, arithmetic) vs zero side (400 zeros): max |diff| = {worst:.1e}")
    print("\nCentered carriers (as specified) — J LOWER endpoints (all > 0 => nothing certifiable):")
    for g in GAMMAS:
        print(f"  gamma {g:9.4f}: " + "  ".join(f"{cen[g]['cells'][b]['J_lo']:+.3e}" for b in BETAS)
              )
    out = dict(L=L, c=C_STR, prec=PREC, B_contour=B_CONTOUR, zeta_bound_1_1=zmax, zeta_bound_1_01=zb,
               t_contour=t_con, runtime=round(time.time() - t_all, 1), kernels=kers)
    (HERE / "frequency_localized_results.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote frequency_localized_results.json ({out['runtime']}s)")


if __name__ == "__main__":
    main()
