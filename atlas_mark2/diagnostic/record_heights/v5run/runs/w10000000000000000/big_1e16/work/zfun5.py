"""atlas_v5 Hardy Z at exact heights (generator side; NOT trusted -- every interval is re-verified by verify_zs5 at replay).
Same formula as atlas_v4 zfun.Z (lgamma form); the height is base + w exactly (heights.hx); precision raised by bitlen(base)."""
from flint import arb, acb, ctx
from heights import hx


def Z(base, w, prec=96):
    old = ctx.prec; ctx.prec = prec + base.bit_length()
    try:
        T = hx(base, w); th = (acb(arb(1) / 4, T / 2).lgamma()).imag - T / 2 * arb.pi().log()
        z = acb(arb(1) / 2, T).zeta(); v = (acb(th.cos(), th.sin()) * z).real
    finally: ctx.prec = old
    return v


def sgn(base, w):
    for p in (96, 160, 256):
        v = Z(base, w, p)
        if v.lower() > 0: return 1
        if v.upper() < 0: return -1
    return 0
