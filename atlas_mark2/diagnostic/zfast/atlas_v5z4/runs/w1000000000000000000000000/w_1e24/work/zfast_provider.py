"""atlas_v5z3 Z / row provider (= v5z2 provider re-pinned to libzfast.v13b) (TRUSTED; THEORY_M5 section 1, THEORY_M5b): one zfast kind-0 session per (T0, centre) gives
Z (THEORY_M3) and the rows Re(-zeta'/zeta)(1/2 + pi/(2a) + i x) (complex shift of the Z moments, THEORY_M5b), via ctypes on the
sha-pinned /Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v13b.dylib.
Centre: env ZFAST_CENTER (offset) if |u - centre| <= H, else c = 8 round(u/8).  H = 4, Delta = 0.15, K = 18.
Balls come back as Arb-printed enclosures (arb_get_str) parsed by arb(str): rigorous."""
import ctypes, json, hashlib, os, math
from fractions import Fraction
from flint import arb, ctx
LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v13b.dylib'
LIB_SHA = '82489d1a89e25bef117cd87f47d591d9426282c4b211f92ace12d097767dffca'
assert hashlib.sha256(open(LIBPATH, 'rb').read()).hexdigest() == LIB_SHA, 'libzfast sha mismatch'
PARAMS = dict(H=4.0, Delta=0.15, K=18, J=12, threads=int(os.environ.get('ZFAST_THREADS', '2')))
ROW_A = (2.8, 1.6)
_L = ctypes.CDLL(LIBPATH)
_L.zfa4_new.restype = ctypes.c_void_p
_L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
for _f in (_L.zfa3_Z, _L.zfa4_row, _L.zfa3_info):
    _f.restype = ctypes.c_int
_L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
_L.zfa4_row.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
_L.zfa3_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_BUF = ctypes.create_string_buffer(4096)
_S = {}
STATS = dict(sessions=0, build_seconds=0.0, z_points=0, row_points=0)


def _centre(u):
    c = os.environ.get('ZFAST_CENTER')
    if c is not None:
        c = float(c)
        if abs(u - c) <= PARAMS['H']: return c
    return 8.0 * round(u / 8.0)


def _session(T0, u):
    assert isinstance(T0, int) and not isinstance(T0, bool) and T0 >= 0 and math.isfinite(u)
    c = _centre(u); key = (T0, c)
    if key not in _S:
        s = _L.zfa4_new(str(T0).encode(), c, PARAMS['H'], PARAMS['Delta'], PARAMS['K'], PARAMS['J'], PARAMS['threads'])
        if not s: raise RuntimeError('zfa4_new failed')
        _L.zfa3_info(s, _BUF, 4096); info = json.loads(_BUF.value.decode())
        STATS['sessions'] += 1; STATS['build_seconds'] += info['sec_build']
        _S[key] = s
    assert abs(u - c) <= PARAMS['H']
    return _S[key]


def _parse(s):
    old = ctx.prec; ctx.prec = max(old, 256)
    try: return arb(s)
    finally: ctx.prec = old


def Zball(T0, u):
    u = float(u); s = _session(T0, u)
    r = _L.zfa3_Z(s, u, _BUF, 4096)
    if r != 0: raise RuntimeError(f'zfa3_Z {r}')
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
    assert float(a) in ROW_A, 'v5z2 provider: rows only for a in (2.8, 1.6)'
    u = offset_of(xa, T0); s = _session(T0, u)
    r = _L.zfa4_row(s, u, float(a), _BUF, 4096)
    if r != 0: raise RuntimeError(f'zfa4_row {r}')
    STATS['row_points'] += 1
    return _parse(json.loads(_BUF.value.decode())['P'])
