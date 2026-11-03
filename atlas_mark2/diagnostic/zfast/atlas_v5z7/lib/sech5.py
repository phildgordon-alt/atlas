"""atlas_v5 'dirichlet' evaluator of the sech-row quantity E_a(x) (THEORY_V5.md section 5).  TRUSTED (new in v5).

E_a(x) = pole + const + arch + prime, exactly as certify_sech_interferometer.E_parts (pole/const lines copied verbatim; arch called
unchanged), except the prime term:
  prime(x) = -(2/a) [ Re(-zeta'/zeta)(1/2 + b + i x) - S_M(x) ]  +-  (2/a) R_M,      b = pi/(2a),
  S_M(x)   = sum_{n <= M} c_n cos(x log n),  c_n = Lambda(n) n^{-1/2-3b} / (1 + n^{-2b}),
  R_M      = 1.03883 * s3/(s3 - 1) * M^{1 - s3},  s3 = 1/2 + 3b   (Lemma D: psi(y) < 1.03883 y, Rosser-Schoenfeld 1962 Thm 12).
The k = 0 term is ONE Arb jet (certify_sech_interferometer.mzl, precision ZPREC = 128, as v4); S_M is summed in Arb at precision
128 + bitlen(T0) (x exact).  x is an exact Arb ball of the absolute height (heights.hx)."""
import numpy as np
from flint import arb, acb, ctx
import certify_sech_interferometer as eng
import zfast_provider as _zfp

M_DEFAULT = 10 ** 6
I1 = arb(0, 1)
_S = {}


def prime_powers(M):
    """sorted list of (n, p) for prime powers n = p^k <= M (exact sieve)"""
    sv = np.ones(M + 1, bool); sv[:2] = False
    for i in range(2, int(M ** 0.5) + 1):
        if sv[i]: sv[i * i::i] = False
    out = []
    for p in np.nonzero(sv)[0].tolist():
        q = p
        while q <= M: out.append((q, p)); q *= p
    out.sort()
    return out


def setup(a, M=M_DEFAULT, prec=256):
    """coefficients c_n, log n (Arb) and the tail R_M for kernel a.  Cached per (a, M)."""
    key = (a, M)
    if key in _S: return _S[key]
    old = ctx.prec; ctx.prec = prec
    try:
        A = arb(a); b = arb.pi() / (2 * A); s3 = arb(1) / 2 + 3 * b
        assert 0 < a < 3.14159 and (s3 > 1)
        pp = prime_powers(M); cs = []; ls = []
        for n, p in pp:
            N = arb(n); c = arb(p).log() * (-s3 * N.log()).exp() / (1 + (-2 * b * N.log()).exp())
            cs.append(c); ls.append(N.log())
        R = (arb('1.03883') * s3 / (s3 - 1) * (arb(M) ** (1 - s3))).upper()
    finally:
        ctx.prec = old
    _S[key] = dict(A=A, b=b, s3=s3, c=cs, l=ls, R=R, M=M, count=len(pp))
    return _S[key]


def prime_dirichlet(a, xa, T0, M=M_DEFAULT):
    """enclosure of prime(x) for kernel a at the exact ball xa (absolute height; T0 only sets the summation precision)."""
    S = setup(a, M); old = ctx.prec
    try:
        ctx.prec = 128                                            # = certify_sech_interferometer.ZPREC (v4 jet precision)
        P0 = _zfp.Pball(a, xa, T0)                                 # v5z: zfast row (THEORY_V5Z section 1) replaces eng.mzl
        ctx.prec = 128 + T0.bit_length()
        s = arb(0)
        for c, l in zip(S['c'], S['l']): s += c * (xa * l).cos()
        ctx.prec = old
        return -2 / S['A'] * (P0 - s) + (2 / S['A'] * S['R']).upper() * I1
    finally:
        ctx.prec = old


def E_parts5(a, xa, T0, M=M_DEFAULT):
    """itemized enclosures (as eng.E_parts) with the dirichlet prime term.  Requires eng configured/_init'ed for kernel a (as model5)."""
    g = eng._W; assert float(g['a'].mid()) == a
    A = g['a']
    pole = (1 / (A * acb(-xa, arb(1) / 2)).cosh() + 1 / (A * acb(xa, arb(1) / 2)).cosh()).real      # verbatim from E_parts
    const = -(1 / (2 * A)) * arb.pi().log()                                                          # verbatim from E_parts
    return dict(pole=pole, const=const, arch=eng.arch(xa), prime=prime_dirichlet(a, xa, T0, M))


def E5(a, xa, T0, M=M_DEFAULT):
    P = E_parts5(a, xa, T0, M); return P['pole'] + P['const'] + P['arch'] + P['prime']
