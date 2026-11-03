"""atlas_v5z Z / row provider (TRUSTED; THEORY_V5Z.md section 1): zfast M3 window sessions (THEORY_ZFAST.md, THEORY_M3.md) via
ctypes on the sha-pinned library /Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v10b.dylib.
Zball(T0, u)    : ball containing Z(T0 + u)                                       (replaces Arb Zg / zfun5.Z)
Pball(a, xa, T0): ball containing Re(-zeta'/zeta)(1/2 + pi/(2a) + i xa), xa = exact ball T0 + u   (replaces Arb eng.mzl(...).real)
Sessions: centre c = 6 * round(u / 6) (an integer offset), half-width H = 3, so |u - c| <= 3 always; one session per (T0, kind, a, c).
Balls come back as Arb's printed enclosures (arb_get_str), parsed by arb(str): rigorous."""
import ctypes, json, hashlib, os, math
from fractions import Fraction
from flint import arb, ctx
LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v10b.dylib'
LIB_SHA = '3daa33d516c062364ff7b5a7cb078ae3b9921483d20646d8587c392c246ef6f8'
assert hashlib.sha256(open(LIBPATH, 'rb').read()).hexdigest() == LIB_SHA, 'libzfast sha mismatch'
PARAMS = dict(H=3.0, Delta=0.2, K=16, J=12, threads=int(os.environ.get('ZFAST_THREADS', '2')))
_L = ctypes.CDLL(LIBPATH)
_L.zfa_sess_new.restype = ctypes.c_void_p
_L.zfa_sess_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
for _f in (_L.zfa_sess_Z, _L.zfa_sess_row, _L.zfa_sess_info):
    _f.restype = ctypes.c_int
_L.zfa_sess_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
_L.zfa_sess_row.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
_L.zfa_sess_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_BUF = ctypes.create_string_buffer(4096)
_S = {}
STATS = dict(sessions=0, build_seconds=0.0, z_points=0, row_points=0)


def _session(T0, kind, a, u):
    assert isinstance(T0, int) and not isinstance(T0, bool) and T0 >= 0 and math.isfinite(u)
    c = 6.0 * round(u / 6.0)
    key = (T0, kind, a, c)
    if key not in _S:
        s = _L.zfa_sess_new(str(T0).encode(), c, PARAMS['H'], kind, float(a), PARAMS['Delta'], PARAMS['K'], PARAMS['J'], PARAMS['threads'])
        if not s: raise RuntimeError('zfa_sess_new failed')
        _L.zfa_sess_info(s, _BUF, 4096); info = json.loads(_BUF.value.decode())
        STATS['sessions'] += 1; STATS['build_seconds'] += info['sec_build']
        _S[key] = s
    assert abs(u - c) <= PARAMS['H']
    return _S[key]


def _parse(s):
    old = ctx.prec; ctx.prec = max(old, 256)
    try: return arb(s)
    finally: ctx.prec = old


def Zball(T0, u):
    u = float(u); s = _session(T0, 0, 0.0, u)
    r = _L.zfa_sess_Z(s, u, _BUF, 4096)
    if r != 0: raise RuntimeError(f'zfa_sess_Z {r}')
    STATS['z_points'] += 1
    return _parse(json.loads(_BUF.value.decode())['Z'])


def offset_of(xa, T0):
    """the binary64 u with xa = T0 + u exactly (asserted)"""
    old = ctx.prec; ctx.prec = max(old, 64 + int(T0).bit_length() + 1100)
    try: d = xa - arb(T0)
    finally: ctx.prec = old
    assert d.rad() == 0
    m, e = d.mid().man_exp(); f = Fraction(int(m)) * Fraction(2) ** int(e)
    u = float(f); assert Fraction(u) == f, 'row height is not T0 + binary64'
    return u


def Pball(a, xa, T0):
    u = offset_of(xa, T0); s = _session(T0, 1, float(a), u)
    r = _L.zfa_sess_row(s, u, _BUF, 4096)
    if r != 0: raise RuntimeError(f'zfa_sess_row {r}')
    STATS['row_points'] += 1
    return _parse(json.loads(_BUF.value.decode())['P'])
