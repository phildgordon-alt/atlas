#!/usr/bin/env python
"""
certify_sech_interferometer.py -- one-sided strip-positivity ledger for the kernel h(r) = sech(a r): catalogue-free,
count-free certification of t-intervals free of zeros with beta != 1/2.
Input: primes only.  NO zero catalogue, NO Hardy-Z brackets, NO Gram points, NO Turing counts, NO Trudgian band.

Kernel (a = 2):  h(r) = sech(a r),  f(u) = (1/2a) sech(pi u / 2a) = (1/4) sech(pi u/4)   (h(r) = int f(u) e^{iur} du).
Centred at x:    h_x(r) = [h(r - x) + h(r + x)]/2  <->  f_x(u) = f(u) cos(x u).
Canonical explicit formula (EXPLICIT_FORMULA_CONVENTIONS.md; h analytic for |Im r| < pi/2a = 0.785 > 1/2, f(log n) = O(n^{-pi/4})):
  E(x) = h_x(i/2) + h_x(-i/2) - f(0) log pi + (1/2pi) int h_x(r) Re psi(1/4 + ir/2) dr - 2 sum_{n>=2} Lambda(n) n^{-1/2} f(log n) cos(x log n)
       = sum over all nontrivial zeros rho of h_x(gamma_rho).
Strip positivity: Re sech(a(t - i d)) = cosh(at) cos(ad) / |cosh(a(t - i d))|^2 >= 0 for |a d| <= pi/2 (here |d| < 1/2, a d < 1).
  Every zero contributes Re >= 0; a quartet at ordinate x (delta in (0, 1/2)) contributes >= 2 Re h(-i delta) = 2/cos(a delta) >= 2.
  Hence: if E(x) < 2, no zero rho = beta + i x with beta != 1/2.  [the allowance for other zeros is identically 0]
Certification of an interval [x - r, x + r]:  E_comp(x)_hi + Tail + L r < 2, where
  E_comp   = pole - f(0) log pi + arch - 2 sum_{n <= X} (...)  in 256-bit Arb; the prime table is float64 (exact dyadics) with a
             rigorous input-error ball  sum_n [|w_n - w~_n| + |w~_n| x_max |log n - l~_n|]  computed once in Arb;
  Tail     = 2 sum_{n > X} Lambda(n) n^{-1/2} f(log n) <= 2 * 1.03883 * alpha/(2(alpha - 1)) * X^{1 - alpha},  alpha = 1/2 + pi/(2a)
             (f(log x) x^{-1/2} <= (1/2) x^{-alpha}; partial summation; psi(x) < 1.03883 x, Rosser-Schoenfeld 1962 Thm 12);
  arch     = (1/2pi) int sech(a s) Re psi(1/4 + i(s + x)/2) ds: GL-12 panels of width 0.5 on |s| <= 40, Trefethen remainder on
             Bernstein rectangles of half-height 0.4 (< 0.785): |sech(az)| <= 1/sqrt(sinh^2(a s_min) + cos^2(a Y)), psi bound at 128 bits
             (psi_shift); tail |s| > 40 bounded analytically;
  L        = 2 sum_{n <= X} |w_n| log n  +  L_arch  +  L_pole   (sup |E_comp'| on the band; L_arch via |psi'(1/4 + iy)| <= 1/y^2 + pi/(2y)).
Ledger.  E_h(t) = sum_rho h_t(gamma_rho) = Q_h + U_h, U_h >= 0 (strip positivity; no upper bound needed); a candidate quartet at
  ordinate t contributes Q_h >= q_- = 2 (kernel centred at the candidate's own ordinate; inf over delta of 2/cos(a delta)).
  Per node x with cell radius r:  E_+ = mid(E) + rad(E) + Tail + Lip_ball,  Lip_ball = L r,  margin m = q_- - E_+.
  The tiler spends the slack on the ball (r maximal), so m ~ 1e-16 by construction; the informative slack is the centre margin
  m_0 = q_- - (E_hi + Tail) = L r (recorded as margin_center).
  Status: EXCLUDED (m > 0: every t in [x - r, x + r] has no zero off the line); RETAINED (E_lo >= 2 - Tail: this kernel cannot
  exclude; the skip r keeps E >= 2 - Tail on the cell); UNRESOLVED (E straddles the threshold, or rad(E) > 1e-3: precision abort).
Admissibility and poles.  h(r) = sech(a r) <-> f(u) = (1/2a) sech(pi u/2a) (h(r) = int f(u) e^{iur} du).  h is holomorphic for
  |Im r| < pi/(2a) (simple poles at r = +-i pi/(2a) (2k+1)); for a < pi this strictly contains |Im r| <= 1/2, i.e. every
  gamma_rho = gamma - i(beta - 1/2).  The terms h_t(i/2) + h_t(-i/2) are the canonical explicit-formula contributions of the poles
  of the completed zeta function at s = 1 and s = 0 (s - 1/2 = -+ i r at r = -+ i/2); they are evaluated here in closed form,
  sech(a(t - i/2)) + sech(a(t + i/2)) real part, with no contour shift (the prime side is summed directly, not by a contour).
Alternative evaluator (--evaluator zeta).  With b = pi/(2a) > 1/2 and sech(y) = 2 sum_k (-1)^k e^{-(2k+1)y}:
  -2 sum_n Lambda(n) n^{-1/2} f(log n) cos(x log n) = -(2/a) Re sum_{k>=0} (-1)^k (-zeta'/zeta)(1/2 + (2k+1) b + i x)
  (absolute convergence: every argument has real part > 1).  Truncating after k = K - 1 leaves at most
  R_K = (2/a) (-zeta'/zeta)(1/2 + (2K + 1) b) (alternating, decreasing in k for every n); K is the smallest with R_K <= target.
  This replaces the prime sum over n <= X AND its tail (the ledger's Tail becomes R_K; no float64 table, input error 0).
  |d/dx of that term| <= (2/a) [sum_{k<K} (-1)^k D(s_k) + D(s_K)],  D(s) = sum Lambda(n) log n n^{-s} = (zeta'/zeta)'(s).
  zeta via Arb (Euler-Maclaurin with rigorous remainder, Johansson 2015); ball enclosures are valid at any working precision.
Adaptive stepping per chunk: certified radius r = (2 - Tail - E_hi)/L (step r); otherwise skip (E_lo - (2 - Tail))/L when positive
(no certifiable point is skipped), with a minimum step.  Band [9950, 10050].  No statement about RH is made.
"""
from __future__ import annotations
import hashlib, json, math, os, subprocess, sys, time
from fractions import Fraction
from pathlib import Path
from multiprocessing import get_context
import numpy as np
from flint import arb, acb, acb_series, ctx

DIAG = Path(__file__).resolve().parent; ROOT = DIAG.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(DIAG))
from frequency_localized_sweep import gl_rule_certified            # noqa: E402
from precision_and_l70_analysis import dec                         # noqa: E402

PREC = 256; A_ = 2; X = int(os.environ.get("SECH_X", 10 ** 8))
BAND = (9950.0, 10050.0); NCHUNK = 40; RMIN = 0.002
S0 = 40; PW = "0.5"; BB = "0.4"
TABLE = Path(os.environ.get("SECH_TABLE", "/private/tmp/claude-501/-Users-kiosk-atlas-mark2/3d68091a-0846-417b-8c52-0fd26569362a/scratchpad/sech_prime_table.npz"))
NW = int(os.environ.get("SECH_NW", 0)) or os.cpu_count() or 4
EVAL = "primes"; SER_TARGET = "1e-10"; ZPREC = 128
I1 = arb(0, 1)
_W: dict = {}


def configure(a=None, x=None, band=None, table=None, evaluator=None, target=None):
    """set kernel parameter a, aperture X, band, table path and prime-term evaluator (module globals)."""
    global A_, X, BAND, TABLE, EVAL, SER_TARGET
    if evaluator is not None: EVAL = evaluator
    if target is not None: SER_TARGET = str(target)
    if a is not None: A_ = a
    if x is not None: X = int(x)
    if band is not None: BAND = (float(band[0]), float(band[1]))
    if table is not None: TABLE = Path(table)


def prime_table():
    sv = np.ones(X + 1, bool); sv[:2] = False
    for i in range(2, int(X ** 0.5) + 1):
        if sv[i]: sv[i * i::i] = False
    ps = np.nonzero(sv)[0].astype(np.int64)
    ns, lp = [ps], [ps]
    q = ps[ps <= int(X ** 0.5)]; pk = q * q
    while len(q):
        keep = pk <= X; q, pk = q[keep], pk[keep]
        if not len(q): break
        ns.append(pk.copy()); lp.append(q.copy()); pk = pk * q
    n = np.concatenate(ns); p = np.concatenate(lp); o = np.argsort(n)
    return n[o], p[o]


def build_table():
    """float64 table (w~, l~) plus rigorous Arb bounds: input-error ball, L_prime, sum|w|."""
    ctx.prec = PREC
    n, p = prime_table()
    a = arb(A_); pi4 = arb.pi() / (2 * a)
    wt = np.empty(len(n)); lt = np.empty(len(n))
    err_w = arb(0); sum_err_l = arb(0); Lp = arb(0); sabs = arb(0)
    for i in range(len(n)):
        N = int(n[i]); ln = arb(N).log(); w = arb(int(p[i])).log() / arb(N).sqrt() / (2 * a) / (pi4 * ln).cosh()
        wf = float(w.mid()); lf = float(ln.mid()); wt[i] = wf; lt[i] = lf
        err_w += abs(w - arb(wf)); ew = abs(ln - arb(lf)); sum_err_l += abs(arb(wf)) * ew
        Lp += (abs(arb(wf)) + abs(w - arb(wf))) * (arb(lf) + ew); sabs += abs(w)
    np.savez(TABLE, w=wt, l=lt)
    xmax = arb(BAND[1]) + 1
    inerr = (2 * (err_w + xmax * sum_err_l)).upper()                  # factor 2 of -2 sum
    return dict(count=len(n), input_error=inerr, L_prime=(2 * Lp).upper(), sum_abs_w=sabs.upper(),
                table_sha256=hashlib.sha256(TABLE.read_bytes()).hexdigest())


def mzl(s):
    """-zeta'/zeta(s) (Arb)."""
    c = acb_series([s, 1], 2).zeta().coeffs(); return -c[1] / c[0]            # length 2: the default cap (10) costs ~70x at t = 1e6


def dzl(sig):
    """D(sig) = sum Lambda(n) log n n^{-sig} = (zeta'/zeta)'(sig) = (2 c2 c0 - c1^2)/c0^2 for real sig > 1."""
    c = acb_series([acb(sig), 1], 3).zeta().coeffs(); return ((2 * c[2] * c[0] - c[1] ** 2) / c[0] ** 2).real


def series_consts():
    """K, certified remainder R_K and Lipschitz bound of the prime term for the zeta-series evaluator."""
    old = ctx.prec; ctx.prec = PREC
    a = arb(A_); b = arb.pi() / (2 * a); target = arb(SER_TARGET)
    K = 1
    while not (2 / a * mzl(acb(arb(1) / 2 + (2 * K + 1) * b)).real).upper() <= target: K += 1
    R = (2 / a * mzl(acb(arb(1) / 2 + (2 * K + 1) * b)).real).upper()
    Ls = sum(((-1) ** k * dzl(arb(1) / 2 + (2 * k + 1) * b) for k in range(K)), arb(0)) + dzl(arb(1) / 2 + (2 * K + 1) * b)
    ctx.prec = old
    return K, R, (2 / a * Ls).upper()


def prime_series(xa):
    """-(2/a) Re sum_{k<K} (-1)^k (-zeta'/zeta)(1/2 + (2k+1) b + i x) +- R_K."""
    g = _W; old = ctx.prec; ctx.prec = ZPREC
    tot = acb(0)
    for k in range(g["K"]):
        tot += (-1) ** k * mzl(acb(arb(1) / 2 + (2 * k + 1) * g["b"], xa))
    ctx.prec = old
    return -2 / g["a"] * tot.real + g["R"] * I1


def tail_bound():
    alpha = arb(1) / 2 + arb.pi() / (2 * arb(A_))
    return (2 * arb("1.03883") * alpha / (2 * (alpha - 1)) * arb(X) ** (1 - alpha)).upper()


def L_arch(xmin):
    """sup_x |d/dx arch| <= (1/2pi)(1/2)[ (pi/a) max_{|s|<=x/2}|psi'| + psi'(1/4) * 4 e^{-a x/2}/a ]."""
    y = arb(xmin) / 4; a = arb(A_)
    ps1 = 1 / (y * y) + arb.pi() / (2 * y)
    psi1_max = arb(18)                                   # sup_y |psi'(1/4 + iy)| = psi'(1/4) = pi^2 + 8 G = 17.197... < 18
    return ((ps1 * arb.pi() / a + psi1_max * 4 * (-a * arb(xmin) / 2).exp() / a) / (4 * arb.pi())).upper()


def _init(cfg, bb=None):
    """worker initializer; cfg = (a, X, band, table, bernstein half-height) or the legacy ([], bb) form."""
    if isinstance(cfg, tuple) and len(cfg) >= 5:
        configure(cfg[0], cfg[1], cfg[2], cfg[3], *(cfg[5:7] if len(cfg) >= 7 else ())); bb = cfg[4]
    ctx.prec = PREC
    if EVAL == "zeta":
        K, R, _ = series_consts(); _W.update(K=K, R=R, b=arb.pi() / (2 * arb(A_)), w=None, l=None)
    else:
        d = np.load(TABLE); _W.update(w=d["w"], l=d["l"])
    X_, W_ = gl_rule_certified(12)
    _W.update(gx=[dec(x) for x in X_], gw=[dec(x) for x in W_], a=arb(A_))
    half = arb(PW) / 2; B = arb(bb); rho = (B + (B * B + half * half).sqrt()) / half
    _W.update(half=half, rho=rho, coef=(arb(64) / 15 * half * rho ** (-24) / (rho * rho - 1)).upper(),
              Xu=(half * (rho + 1 / rho) / 2).upper(), Yu=B)


def psi_shift(z):
    return (z + 12).digamma() - sum((1 / (z + j) for j in range(12)), acb(0))


def arch(x):
    g = _W; a = g["a"]; half = g["half"]; acc = arb(0); err = arb(0)
    n = int(2 * S0 / float(PW))
    for j in range(n):
        mid = arb(-S0) + half * (2 * j + 1)
        for gx, gw in zip(g["gx"], g["gw"]):
            s = mid + half * gx
            acc += half * gw * (1 / (a * s).cosh()) * acb(arb(1) / 4, (s + x) / 2).digamma().real
        ctx.prec = 128
        z = acb(mid + g["Xu"] * I1, g["Yu"] * I1)
        smin = abs(mid) - g["Xu"]; smin = smin.lower() if smin > 0 else arb(0)        # |cosh(u + iv)|^2 = sinh^2 u + cos^2 v
        sb = (1 / ((a * smin).sinh() ** 2 + (a * g["Yu"]).cos() ** 2).sqrt()).upper()   # a Yu = 0.8 < pi/2
        pb = abs((psi_shift(acb(arb(1) / 4) + acb(0, 1) * (z + x) / 2) + psi_shift(acb(arb(1) / 4) - acb(0, 1) * (z + x) / 2)) / 2)
        ctx.prec = PREC
        assert sb.is_finite() and pb.is_finite()
        err += g["coef"] * (sb * pb).upper()
    tail = (2 / arb.pi() * (-a * S0).exp() / a * ((arb(x) + S0 + 1).log() + 3)).upper()   # |s| > 40, both sides
    return acc / (2 * arb.pi()) + (err / (2 * arb.pi()) + tail) * I1


def E_parts(x):
    """itemized 256-bit Arb enclosures at the exact float64 point x: pole, -f(0) log pi, arch (incl. remainder and tail),
    prime = -2 sum_{n <= X} Lambda(n) n^{-1/2} f(log n) cos(x log n) (input-error ball added by the caller)."""
    g = _W; a = g["a"]; xa = arb(x)
    pole = (1 / (a * acb(-xa, arb(1) / 2)).cosh() + 1 / (a * acb(xa, arb(1) / 2)).cosh()).real
    const = -(1 / (2 * a)) * arb.pi().log()
    if EVAL == "zeta":
        return dict(pole=pole, const=const, arch=arch(xa), prime=prime_series(xa))
    ps = arb(0)
    for w, l in zip(g["w"].tolist(), g["l"].tolist()):
        ps += arb(w) * (xa * arb(l)).cos()
    return dict(pole=pole, const=const, arch=arch(xa), prime=-2 * ps)


def E_comp(x):
    P = E_parts(x); return P["pole"] + P["const"] + P["arch"] + P["prime"]


def _chunk(args):
    ci, lo, hi, thr_s, L_s, inerr_s = args
    thr, L, inerr = arb(thr_s), arb(L_s), arb(inerr_s)
    tail = 2 - thr                                                         # >= Tail (thr was rounded down)
    x = lo; nodes = []
    while x < hi:
        P = E_parts(x)
        Es = (P["pole"] + P["const"] + P["arch"] + P["prime"] + inerr * I1).str(30)   # serialized (outward); radii derive from it
        E = arb(Es); Eh, El = E.upper(), E.lower()
        parts = {k: v.str(25) for k, v in P.items()}; parts["input_error"] = inerr.str(10)
        margin = thr - Eh
        if E.rad() > arb("1e-3"):
            nodes.append(dict(chunk=ci, x=x.hex(), E=Es, parts=parts, r=(0.0).hex(), status="UNRESOLVED", note="precision abort"))
            x = x + RMIN; continue
        if margin > 0:
            r = math.nextafter(float((margin / L).lower()), 0.0)          # float64 rounded toward 0: r <= (thr - E_hi)/L
            lip = (L * arb(r)).upper(); Ep = (Eh + tail + lip).upper()
            nodes.append(dict(chunk=ci, x=x.hex(), E=Es, parts=parts, r=r.hex(), status="EXCLUDED",
                              budget=dict(E_mid=E.mid().str(20, radius=False), E_rad=E.rad().str(5, radius=False), tail=tail.str(20),
                                          lip_ball=lip.str(20), E_plus=Ep.str(20), margin=(2 - Ep).str(20),
                                          margin_center=(2 - Eh - tail).str(20))))
            x = x + max(r, RMIN)
        else:
            sk = math.nextafter(float(((El - thr) / L).lower()), 0.0) if (El - thr) > 0 else 0.0
            Ep = (Eh + tail).upper()
            nodes.append(dict(chunk=ci, x=x.hex(), E=Es, parts=parts, r=sk.hex(), status="RETAINED" if sk > 0 else "UNRESOLVED",
                              budget=dict(E_mid=E.mid().str(20, radius=False), E_rad=E.rad().str(5, radius=False), tail=tail.str(20),
                                          lip_ball="0", E_plus=Ep.str(20), margin=(2 - Ep).str(20),
                                          margin_center=(2 - Ep).str(20))))
            x = x + max(sk, RMIN)
    return nodes


def merge(nodes):
    iv = []
    for d in nodes:
        if d["status"] not in ("certified", "EXCLUDED"): continue
        x = Fraction(float.fromhex(d["x"])); r = Fraction(float.fromhex(d["r"]))
        iv.append((x - r, x + r))
    iv.sort(); out = []
    for a_, b_ in iv:
        if out and a_ <= out[-1][1]: out[-1] = (out[-1][0], max(out[-1][1], b_))
        else: out.append((a_, b_))
    lo, hi = Fraction(BAND[0]), Fraction(BAND[1])
    return [(max(a_, lo), min(b_, hi)) for a_, b_ in out if b_ > lo and a_ < hi]


def finalize(path):
    """Re-derive every radius from the SERIALIZED enclosures (outward decimal balls), keeping the engine radius as r_engine.
    Needed for certificates produced before the engine derived radii from its serialized values (the stored 12-digit balls are
    ~1e-11 wider than the 256-bit enclosures the engine used, and the engine spent the full margin)."""
    ctx.prec = PREC
    d = json.loads(Path(path).read_text()); tail = arb(d["tail"]).upper(); L = arb(d["L"]).upper(); thr = (2 - tail).lower()
    for n in d["nodes"]:
        E = arb(n["E"]); n.setdefault("r_engine", n["r"])
        if n["status"] in ("certified", "EXCLUDED"):
            m = thr - E.upper()
            if m > 0: n["r"] = math.nextafter(float((m / L).lower()), 0.0).hex()
            else: n["r"] = (0.0).hex(); n["status"] = "unresolved"
        else:
            m = E.lower() - thr
            n["r"] = (math.nextafter(float((m / L).lower()), 0.0) if m > 0 else 0.0).hex()
    iv = merge(d["nodes"])
    d["certified_intervals"] = [[f"{a.numerator}/{a.denominator}", f"{b.numerator}/{b.denominator}"] for a, b in iv]
    d["certified_intervals_decimal"] = [[f"{float(a):.9f}", f"{float(b):.9f}"] for a, b in iv]
    d["coverage_fraction_engine"] = d.get("coverage_fraction_engine", d["coverage_fraction"])
    d["coverage_fraction"] = float(sum((b - a) for a, b in iv) / Fraction(d["band"][1] - d["band"][0]))
    d["finalized"] = "radii re-derived from serialized enclosures (finalize); engine radii kept as r_engine; steps used r_engine"
    Path(path).write_text(json.dumps(d, indent=1) + "\n")
    return len(iv), d["coverage_fraction"], d["coverage_fraction_engine"]


def annotate(path):
    """add the one-sided ledger fields to a certificate produced before they existed (no recomputation): per node E_mid, E_rad,
    Tail, Lip_ball = L r, E_+ and margin m = 2 - E_+, ledger status names; global error-budget components."""
    ctx.prec = PREC
    d = json.loads(Path(path).read_text()); tail = arb(d["tail"]).upper(); L = arb(d["L"]).upper()
    names = {"certified": "EXCLUDED", "not-certifiable": "RETAINED", "unresolved": "UNRESOLVED"}
    for n in d["nodes"]:
        E = arb(n["E"]); r = arb(float.fromhex(n["r"]))
        ex = n["status"] in ("certified", "EXCLUDED")
        lip = (L * r).upper() if ex else arb(0); Ep = (E.upper() + tail + lip).upper()
        n["ledger_status"] = names.get(n["status"], n["status"])
        n["budget"] = dict(E_mid=E.mid().str(20, radius=False), E_rad=E.rad().str(5, radius=False), tail=tail.str(20),
                           lip_ball=lip.str(20), E_plus=Ep.str(20), margin=(2 - Ep).str(20),
                           margin_center=(2 - E.upper() - tail).str(20))
    ms = [arb(n["budget"]["margin"]) for n in d["nodes"] if n["ledger_status"] == "EXCLUDED"]
    d["error_budget"] = dict(
        E_plus="mid(E) + rad(E) + Tail + Lip_ball per node; rad(E) includes the float64-input ball, the archimedean GL/Trefethen "
               "remainder and |s| > 40 tail, and Arb rounding of the direct prime sum over n <= X",
        tail_prime=d["tail"], input_error=d["input_error"], L=d["L"], L_prime=d["L_prime"], L_arch=d["L_arch"],
        per_node_component_split="not recorded in this run (added to the engine afterwards); totals E are recorded per node",
        min_margin_excluded=min(ms, key=lambda v: float(v.mid())).str(10) if ms else None)
    d["q_minus"] = "2 (quartet at the kernel centre: inf over delta in (0, 1/2) of 2/cos(a delta))"
    Path(path).write_text(json.dumps(d, indent=1) + "\n")
    return len(ms)


def run(out_path, chunks=None, quiet=False):
    t0 = time.time(); ctx.prec = PREC
    nch = chunks or NCHUNK
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    committed = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "diagnostic/certify_sech_interferometer.py"], cwd=ROOT).returncode == 0
    if EVAL == "zeta":
        K, R, Ls = series_consts()
        tb = dict(count=0, input_error=arb(0), L_prime=Ls, sum_abs_w=arb(0), table_sha256=None); t_table = time.time() - t0
        tail = R                                                            # the ledger's Tail term is the series remainder
    else:
        tb = build_table(); t_table = time.time() - t0
        tail = tail_bound()
    La = L_arch(BAND[0]); L = (tb["L_prime"] + La + arb("1e-100")).upper()
    thr = (2 - tail).lower()
    print(f"prime powers <= {X:.0e}: {tb['count']:,} [{t_table:.0f}s];  input-error ball {tb['input_error'].str(3)};  sum|w| {tb['sum_abs_w'].str(6)}")
    print(f"Tail(X) <= {tail.str(6)};  threshold 2 - Tail = {thr.str(8)};  L = {L.str(6)} (prime {tb['L_prime'].str(6)}, arch {La.str(3)})", flush=True)
    edges = np.linspace(BAND[0], BAND[1], nch + 1)
    tasks = [(i, float(edges[i]), float(edges[i + 1]), thr.str(40, radius=False), L.str(40, radius=False), tb["input_error"].str(40, radius=False))
             for i in range(nch)]
    ts = time.time()
    with get_context("spawn").Pool(NW, _init, ((A_, X, BAND, str(TABLE), BB, EVAL, SER_TARGET),)) as pool:
        parts = pool.map(_chunk, tasks, chunksize=1)
    nodes = [d for p in parts for d in p]
    iv = merge(nodes); cov = sum((b - a) for a, b in iv); frac = float(cov / Fraction(BAND[1] - BAND[0]))
    Emin = min(nodes, key=lambda d: float(arb(d["E"]).mid()))
    print(f"evaluations {len(nodes):,} [{time.time() - ts:.0f}s];  certified intervals {len(iv)};  coverage {frac * 100:.2f}% of the band;  "
          f"minimum E {arb(Emin['E']).str(8)} at x = {float.fromhex(Emin['x']):.4f}")
    out = dict(script="diagnostic/certify_sech_interferometer.py", generating_commit=head, code_committed_at_run=committed,
               code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), precision_bits=PREC,
               inputs="primes only: no zero catalogue, brackets, Gram points, Turing counts or N(T) band",
               kernel=dict(a=A_, h="sech(a r)", f="(1/2a) sech(pi u/2a)"), X=X, evaluator=EVAL,
               series=(dict(K=K, remainder=R.str(20), target=SER_TARGET, zeta_precision_bits=ZPREC) if EVAL == "zeta" else None), prime_powers=tb["count"], table_sha256=tb["table_sha256"],
               band=list(BAND), chunks=nch, rmin=RMIN, arch=dict(S0=S0, panel_width=PW, bernstein_half_height=BB),
               tail=tail.str(30), threshold=thr.str(30), L=L.str(30), L_prime=tb["L_prime"].str(30), L_arch=La.str(30),
               input_error=tb["input_error"].str(30), sum_abs_w=tb["sum_abs_w"].str(30),
               criterion="EXCLUDED iff m = q_- - E_+ > 0 with q_- = 2, E_+ = E_hi(x) + Tail + L r: no zero beta + i t with beta != 1/2 for t in [x - r, x + r]",
               q_minus="2", statuses=dict(EXCLUDED=sum(1 for n in nodes if n["status"] == "EXCLUDED"),
                                          RETAINED=sum(1 for n in nodes if n["status"] == "RETAINED"),
                                          UNRESOLVED=sum(1 for n in nodes if n["status"] == "UNRESOLVED")),
               nodes=nodes, certified_intervals=[[a.numerator.__str__() + "/" + a.denominator.__str__(), b.numerator.__str__() + "/" + b.denominator.__str__()] for a, b in iv],
               certified_intervals_decimal=[[f"{float(a):.9f}", f"{float(b):.9f}"] for a, b in iv], coverage_fraction=frac,
               E_min=dict(x=float.fromhex(Emin["x"]), E=Emin["E"]), runtime=round(time.time() - t0, 1))
    Path(out_path).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {out_path} ({out['runtime']}s)")
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--finalize"); ap.add_argument("--annotate")
    ap.add_argument("--a", type=float); ap.add_argument("--X", type=float); ap.add_argument("--band", type=float, nargs=2)
    ap.add_argument("--table"); ap.add_argument("--chunks", type=int); ap.add_argument("--evaluator", choices=("primes", "zeta"))
    ap.add_argument("--series-target"); ap.add_argument("--out", default=str(DIAG / "sech_certificate_10k.json"))
    a = ap.parse_args()
    if a.finalize:
        n_, c, c0 = finalize(a.finalize); print(f"finalized: {n_} intervals, coverage {c * 100:.6f}% (engine {c0 * 100:.6f}%)"); return
    if a.annotate:
        k = annotate(a.annotate); print(f"annotated {a.annotate}: {k} EXCLUDED nodes with ledger fields"); return
    configure(a.a, a.X, a.band, a.table, a.evaluator, a.series_target)
    run(a.out, a.chunks)


if __name__ == "__main__":
    main()
