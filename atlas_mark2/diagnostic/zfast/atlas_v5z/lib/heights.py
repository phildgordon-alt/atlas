"""atlas_v5 exact heights (THEORY_V5.md sections 1-2).  A height is (T0, u): T0 a Python int, u a binary64 offset; value T0 + u exactly.

hx(T0, u)       exact Arb ball (radius 0) of T0 + u, at any T0 (precision raised as needed, asserted exact)
exact(T0, u)    Fraction T0 + u
Grid(T0, kind)  bin edges / sech centres as offsets.  kind 'v5': u_k = fl(k*0.01); kind 'v4' (compatibility): u_k = fl(T0 + k*0.01) - T0.
                Work coordinates of the (untrusted) generator: 'v4' -> absolute binary64 (base 0, exactly v4's arithmetic), 'v5' -> offsets
                (base T0).  to_off / from_off convert exactly (asserted)."""
from fractions import Fraction
from flint import arb, ctx

H = 0.01


def exact(T0, u):
    assert isinstance(T0, int) and not isinstance(T0, bool)
    return Fraction(T0) + Fraction(u)


def hx(T0, u):
    """exact Arb value of T0 + u (u binary64 or int).  Raises the working precision only for the construction."""
    f = exact(T0, u); p, q = f.numerator, f.denominator
    assert q & (q - 1) == 0, 'not dyadic'
    old = ctx.prec; ctx.prec = max(old, abs(p).bit_length() + q.bit_length() + 8)
    try: v = arb(p) / arb(q)
    finally: ctx.prec = old
    assert v.rad() == 0 and v.mid() == v, 'height not exact'
    return v


def as_float_exact(f):
    """Fraction -> binary64, asserting exactness"""
    x = float(f); assert Fraction(x) == f, f'not a binary64: {f}'
    return x


class Grid:
    def __init__(self, T0, kind):
        assert isinstance(T0, int) and kind in ('v4', 'v5')
        if kind == 'v4': assert T0 < 2 ** 52
        self.T0, self.kind = T0, kind
        self.base = 0 if kind == 'v4' else T0          # work coordinate w denotes base + w

    # ---- offsets (the certificate / replay coordinates) ----
    def edge(self, k):
        if self.kind == 'v5': return k * H
        return as_float_exact(Fraction(self.T0 + k * H) - self.T0)      # float(T0) + k*H in binary64 (v4 expression), minus T0 exactly

    def centre(self, m):
        if self.kind == 'v5': return (m + 0.5) * H
        return as_float_exact(Fraction(self.T0 + (m + 0.5) * H) - self.T0)

    # ---- work coordinates (generator only) ----
    def w_edge(self, k): return self.T0 + k * H if self.kind == 'v4' else k * H          # v4: identical float expression to model4.edge
    def w_centre(self, m): return self.T0 + (m + 0.5) * H if self.kind == 'v4' else (m + 0.5) * H

    def to_off(self, w):
        """work coordinate -> offset (exact)"""
        return as_float_exact(Fraction(self.base) + Fraction(w) - self.T0)

    def from_off(self, u):
        return as_float_exact(Fraction(self.T0) + Fraction(u) - self.base)

    def w_to_abs(self, w): return Fraction(self.base) + Fraction(w)
