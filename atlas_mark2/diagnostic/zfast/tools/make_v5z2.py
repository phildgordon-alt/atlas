"""Builds atlas_v5z2/ from atlas_v5z/ (new files only).  Only the provider changes (THEORY_M5 section 1, THEORY_M5b):
one kind-0 zfast session per (T0, centre) answers both Z and rows (complex shift); centre from env ZFAST_CENTER when it covers the
query, else c = 8 round(u/8); H = 4, Delta = 0.15, K = 18.  Driver: provenance string only."""
import os, hashlib, shutil
Z1 = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z/'; Z2 = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z2/'
LIB = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v12a.dylib'; LIB_SHA = hashlib.sha256(open(LIB, 'rb').read()).hexdigest()
os.makedirs(Z2 + 'lib'); os.makedirs(Z2 + 'nzeros')
def cp(f):
    assert not os.path.exists(Z2 + f); shutil.copyfile(Z1 + f, Z2 + f)
for f in ['crosscheck.py', 'replay_target5.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py'] + ['lib/' + x for x in os.listdir(Z1 + 'lib') if x.endswith('.py') and x != 'zfast_provider.py']:
    cp(f)
d = open(Z1 + 'atlas_v5.py').read()
assert d.count("z_provider='zfast libzfast.v10b (THEORY_V5Z)'") == 1
d = d.replace("z_provider='zfast libzfast.v10b (THEORY_V5Z)'", "z_provider='zfast libzfast.v12a, provider v5z2 (THEORY_M5, THEORY_M5b)'")
open(Z2 + 'atlas_v5.py', 'w').write(d)
open(Z2 + 'lib/zfast_provider.py', 'w').write(f'''"""atlas_v5z2 Z / row provider (TRUSTED; THEORY_M5 section 1, THEORY_M5b): one zfast kind-0 session per (T0, centre) gives
Z (THEORY_M3) and the rows Re(-zeta'/zeta)(1/2 + pi/(2a) + i x) (complex shift of the Z moments, THEORY_M5b), via ctypes on the
sha-pinned {LIB}.
Centre: env ZFAST_CENTER (offset) if |u - centre| <= H, else c = 8 round(u/8).  H = 4, Delta = 0.15, K = 18.
Balls come back as Arb-printed enclosures (arb_get_str) parsed by arb(str): rigorous."""
import ctypes, json, hashlib, os, math
from fractions import Fraction
from flint import arb, ctx
LIBPATH = {LIB!r}
LIB_SHA = {LIB_SHA!r}
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
_S = {{}}
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
    if r != 0: raise RuntimeError(f'zfa3_Z {{r}}')
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
    if r != 0: raise RuntimeError(f'zfa4_row {{r}}')
    STATS['row_points'] += 1
    return _parse(json.loads(_BUF.value.decode())['P'])
''')
open(Z2 + 'THEORY_V5Z2.md', 'w').write('''# atlas_v5z2 = atlas_v5z with provider v5z2 (2026-10-19)

The only change from atlas_v5z (THEORY_V5Z.md, whose trust-base description applies) is `lib/zfast_provider.py`:
- one kind-0 zfast session (libzfast.v12a) per process answers both Z (THEORY_M3) and the rows, via the complex shift of the Z moments
  (THEORY_M5b);
- the session centre comes from env ZFAST_CENTER (the run script sets the target centre), and the rule c = 8 round(u/8) is the
  fallback;
- H = 4, Δ = 0.15, K = 18.

The driver changes only its provenance string. Every other file is a byte copy of atlas_v5z. Acceptance (PREDICTIONS_M5 V2): the
six original windows and v5z's 10¹⁷/10¹⁸ windows must be reproduced with identical intervals.
''')
print('lib sha', LIB_SHA)
