"""atlas_v5z generator-side Hardy Z (NOT trusted): zfast balls through lib/zfast_provider.py (prec ignored)."""
import zfast_provider as _zfp


def Z(base, w, prec=96):
    return _zfp.Zball(base, w)


def sgn(base, w):
    v = Z(base, w)
    if v.lower() > 0: return 1
    if v.upper() < 0: return -1
    return 0
