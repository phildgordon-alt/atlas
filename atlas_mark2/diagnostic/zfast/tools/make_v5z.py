"""Builds atlas_v5z/ from atlas_v5z/frozen_ref/ (byte copies of frozen atlas_v5, V5_FREEZE 21/21 OK).  New files only.
Every change is listed here and in atlas_v5z/THEORY_V5Z.md section 2."""
import os, hashlib
Z = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z/'; F = Z + 'frozen_ref/'
LIB = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v10b.dylib'
LIB_SHA = hashlib.sha256(open(LIB, 'rb').read()).hexdigest()
def rd(f): return open(F + f).read()
def wr(path, s):
    assert not os.path.exists(Z + path), path
    open(Z + path, 'w').write(s)
def rep(s, old, new, count=1):
    assert s.count(old) == count, (old[:60], s.count(old)); return s.replace(old, new)

# 1. provider (new, trusted)
wr('lib/zfast_provider.py', f'''"""atlas_v5z Z / row provider (TRUSTED; THEORY_V5Z.md section 1): zfast M3 window sessions (THEORY_ZFAST.md, THEORY_M3.md) via
ctypes on the sha-pinned library {LIB}.
Zball(T0, u)    : ball containing Z(T0 + u)                                       (replaces Arb Zg / zfun5.Z)
Pball(a, xa, T0): ball containing Re(-zeta'/zeta)(1/2 + pi/(2a) + i xa), xa = exact ball T0 + u   (replaces Arb eng.mzl(...).real)
Sessions: centre c = 6 * round(u / 6) (an integer offset), half-width H = 3, so |u - c| <= 3 always; one session per (T0, kind, a, c).
Balls come back as Arb's printed enclosures (arb_get_str), parsed by arb(str): rigorous."""
import ctypes, json, hashlib, os, math
from fractions import Fraction
from flint import arb, ctx
LIBPATH = {LIB!r}
LIB_SHA = {LIB_SHA!r}
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
_S = {{}}
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
    if r != 0: raise RuntimeError(f'zfa_sess_Z {{r}}')
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
    if r != 0: raise RuntimeError(f'zfa_sess_row {{r}}')
    STATS['row_points'] += 1
    return _parse(json.loads(_BUF.value.decode())['P'])
''')

# 2. verifier: Zg from the provider (one function body changed, one import added)
v = rd('verify_zs5.py')
old_zg = v[v.index('def Zg(T0,t):'):v.index('def _ball(lo,hi):')]
new_zg = '''def Zg(T0,t):
    """v5z: Z(T0+t) as a rigorous ball from zfast (lib/zfast_provider.py, THEORY_V5Z section 1); memoised."""
    key=(T0,t)
    if key in _ZG:return _ZG[key]
    v=_zfp.Zball(T0,t)
    _ZG[key]=v
    return v
'''
v = rep(v, old_zg, new_zg)
v = rep(v, 'from flint import arb,acb,ctx\n', 'from flint import arb,acb,ctx\nimport zfast_provider as _zfp\n')
wr('lib/verify_zs5.py', v)
VSHA = hashlib.sha256(v.encode()).hexdigest()
wr('VERIFY_ZS5.sha256', VSHA + '  lib/verify_zs5.py\n')

# 3. rows: P0 from zfast
s = rd('sech5.py')
s = rep(s, "        P0 = eng.mzl(acb(arb(1) / 2 + S['b'], xa)).real\n", "        P0 = _zfp.Pball(a, xa, T0)                                 # v5z: zfast row (THEORY_V5Z section 1) replaces eng.mzl\n")
s = rep(s, 'import certify_sech_interferometer as eng\n', 'import certify_sech_interferometer as eng\nimport zfast_provider as _zfp\n')
wr('lib/sech5.py', s)

# 4. generator Z
wr('lib/zfun5.py', '''"""atlas_v5z generator-side Hardy Z (NOT trusted): zfast balls through lib/zfast_provider.py (prec ignored)."""
import zfast_provider as _zfp


def Z(base, w, prec=96):
    return _zfp.Zball(base, w)


def sgn(base, w):
    v = Z(base, w)
    if v.lower() > 0: return 1
    if v.upper() < 0: return -1
    return 0
''')

# 5. unchanged library files
for f in ['gen_target5.py', 'gen4.py', 'heights.py', 'lp.py', 'model5.py', 'replay5.py', 'verify.py', 'zs5.py', 'verify_zs.py']:
    wr('lib/' + f, rd(f))

# 6. driver: provider in GEN_LIB; no deletions; provider recorded in pieces.json
d = rd('atlas_v5.py')
d = rep(d, "GEN_LIB = ('gen_target5.py', 'gen4.py', 'model5.py', 'sech5.py', 'heights.py', 'zs5.py', 'zfun5.py', 'verify.py', 'lp.py')",
        "GEN_LIB = ('gen_target5.py', 'gen4.py', 'model5.py', 'sech5.py', 'heights.py', 'zs5.py', 'zfun5.py', 'verify.py', 'lp.py', 'zfast_provider.py')")
d = rep(d, """        shutil.rmtree(RUN / 'certs', ignore_errors=True)
        for f in ('gen.jsonl', 'gen.log', 'zs.json'): (RUN / f).unlink(missing_ok=True)
""", """        assert not any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')), 'v5z never deletes: use a fresh --name'
""")
d = rep(d, "              zs_step=a.zs_step, zs_refine=a.zs_refine, pieces=pieces)",
        "              zs_step=a.zs_step, zs_refine=a.zs_refine, pieces=pieces, z_provider='zfast libzfast.v10b (THEORY_V5Z)')")
d = rep(d, "    for f in GEN_LIB: shutil.copy(V4 / 'lib' / f, W / f)\n",
        "    for f in GEN_LIB:\n        if not (W / f).exists(): shutil.copy(V4 / 'lib' / f, W / f)\n        else: assert sha(W / f) == sha(V4 / 'lib' / f)\n")
d = rep(d, "    (W / 'farL.py').write_text(", "    if not (W / 'farL.py').exists(): (W / 'farL.py').write_text(")
wr('atlas_v5.py', d)

# 7. replay: provider copied; never deletes (fresh output dir required)
r = rd('replay_target5.py')
r = rep(r, "shutil.rmtree(R, ignore_errors=True); R.mkdir()", "R.mkdir()   # v5z: never deletes; the output dir must be new")
r = rep(r, "    for f in ('verify_zs5.py', 'model5.py', 'replay5.py', 'heights.py', 'sech5.py'): shutil.copy(V4 / 'lib' / f, R / f)",
        "    for f in ('verify_zs5.py', 'model5.py', 'replay5.py', 'heights.py', 'sech5.py', 'zfast_provider.py'): shutil.copy(V4 / 'lib' / f, R / f)")
wr('replay_target5.py', r)
wr('crosscheck.py', rd('crosscheck.py'))
os.makedirs(Z + 'nzeros', exist_ok=True); wr('nzeros/arb_nzeros.py', rd('arb_nzeros.py'))
print('verify_zs5 sha', VSHA, 'lib sha', LIB_SHA)
