"""atlas_v5z5 Z / row provider (TRUSTED; THEORY_M5 section 1, THEORY_M5b, THEORY_V5Z5.md) = the v5z3/v5z4 provider with configurable,
recorded session parameters.  One zfast kind-0 session per (T0, centre) gives Z (THEORY_M3) and the rows Re(-zeta'/zeta)(1/2 + pi/(2a) + i x)
(complex shift of the Z moments, THEORY_M5b), via ctypes on the sha-pinned libzfast.v13b.dylib.

Session parameters (env; defaults = v5z4 exactly):  ZFAST_H (4.0), ZFAST_DELTA (0.15), ZFAST_K (18), ZFAST_J (12), ZFAST_THREADS (2).
Centre, legacy mode (ZFAST_STRICT unset/0; byte-for-byte the v5z4 rule): env ZFAST_CENTER (offset) if |u - centre| <= H, else 8 round(u/8).
Strict mode (ZFAST_STRICT=1; every wide run): ZFAST_CENTER is required; a point with |u - centre| > H raises; a second session in the same
process raises.  So a strict process makes exactly one O(sqrt T) moment pass.
Soundness does not depend on any of this: every value is a ball from a session whose validity range contains the point (checked here by an
explicit raise, and again inside libzfast, which aborts on a point outside the session); THEORY_M5b Lemma M1c holds for every H, Delta.
Balls come back as Arb-printed enclosures (arb_get_str) parsed by arb(str): rigorous."""
import ctypes, json, hashlib, os, sys, math
from fractions import Fraction

if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('atlas_v5z5: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')

from flint import arb, ctx  # noqa: E402

LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v13b.dylib'
LIB_SHA = '82489d1a89e25bef117cd87f47d591d9426282c4b211f92ace12d097767dffca'
if hashlib.sha256(open(LIBPATH, 'rb').read()).hexdigest() != LIB_SHA:
    raise RuntimeError('libzfast sha mismatch')


def _env_float(k, d):
    v = os.environ.get(k)
    return d if v is None or v == '' else float(v)


def _env_int(k, d):
    v = os.environ.get(k)
    return d if v is None or v == '' else int(v)


PARAMS = dict(H=_env_float('ZFAST_H', 4.0), Delta=_env_float('ZFAST_DELTA', 0.15), K=_env_int('ZFAST_K', 18), J=_env_int('ZFAST_J', 12),
              threads=int(os.environ.get('ZFAST_THREADS', '2')))
STRICT = os.environ.get('ZFAST_STRICT', '0') == '1'
if not (PARAMS['H'] > 0 and 0 < PARAMS['Delta'] <= 1.0 and PARAMS['K'] >= 1 and PARAMS['J'] >= 1 and PARAMS['threads'] >= 1):
    raise ValueError(f'zfast_provider: session parameters out of range {PARAMS}')
if STRICT and os.environ.get('ZFAST_CENTER') in (None, ''):
    raise RuntimeError('zfast_provider strict mode: ZFAST_CENTER is required')
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
STATS = dict(sessions=0, build_seconds=0.0, z_points=0, row_points=0, session_keys=[])


def config():
    """the provider configuration of this process (recorded by the driver / replay)."""
    return dict(H=PARAMS['H'], Delta=PARAMS['Delta'], K=PARAMS['K'], J=PARAMS['J'], threads=PARAMS['threads'], strict=STRICT,
                center=os.environ.get('ZFAST_CENTER'), lib_sha=LIB_SHA)


def _centre(u):
    c = os.environ.get('ZFAST_CENTER')
    if c is not None:
        c = float(c)
        if abs(u - c) <= PARAMS['H']: return c
        if STRICT: raise RuntimeError(f'zfast_provider strict mode: point u={u!r} outside session [{c} - {PARAMS["H"]}, {c} + {PARAMS["H"]}]')
    return 8.0 * round(u / 8.0)


def _session(T0, u):
    if not (isinstance(T0, int) and not isinstance(T0, bool) and T0 >= 0 and math.isfinite(u)):
        raise ValueError(f'zfast_provider: bad point T0={T0!r} u={u!r}')
    c = _centre(u); key = (T0, c)
    if key not in _S:
        if STRICT and _S: raise RuntimeError(f'zfast_provider strict mode: a second session {key} was requested (have {list(_S)})')
        s = _L.zfa4_new(str(T0).encode(), c, PARAMS['H'], PARAMS['Delta'], PARAMS['K'], PARAMS['J'], PARAMS['threads'])
        if not s: raise RuntimeError('zfa4_new failed')
        _L.zfa3_info(s, _BUF, 4096); info = json.loads(_BUF.value.decode())
        STATS['sessions'] += 1; STATS['build_seconds'] += info['sec_build']; STATS['session_keys'].append([str(T0), c])
        _S[key] = s
    if not abs(u - c) <= PARAMS['H']: raise RuntimeError(f'zfast_provider: point u={u!r} outside session centre {c} H {PARAMS["H"]}')
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
    """the binary64 u with xa = T0 + u exactly (checked)"""
    old = ctx.prec; ctx.prec = max(old, 64 + int(T0).bit_length() + 1100)
    try: d = xa - arb(T0)
    finally: ctx.prec = old
    if d.rad() != 0: raise ValueError('row height offset is not exact')
    m, e = d.mid().man_exp(); f = Fraction(int(m)) * Fraction(2) ** int(e)
    u = float(f)
    if Fraction(u) != f: raise ValueError('row height is not T0 + binary64')
    return u


def Pball(a, xa, T0):
    if float(a) not in ROW_A: raise ValueError('v5z2+ provider: rows only for a in (2.8, 1.6)')
    u = offset_of(xa, T0); s = _session(T0, u)
    r = _L.zfa4_row(s, u, float(a), _BUF, 4096)
    if r != 0: raise RuntimeError(f'zfa4_row {r}')
    STATS['row_points'] += 1
    return _parse(json.loads(_BUF.value.decode())['P'])
