"""atlas_v5z6 Z / row provider (TRUSTED; RESULTS_M9 / THEORY_V5Z6.md) = the v5z5 provider on libzfast.v14, whose sessions are
bit-identical to libzfast.v13b at equal decomposition D (= ZFAST_THREADS, recorded as zfast_session.threads).  New, output-free: ZFAST_WORKERS
(OS threads of the moment pass and of turing_grid; default = ZFAST_THREADS), ZFAST_CKPT (checkpoint file of this process's single strict
session; strict mode only).  New diagnostic (NOT a certificate input): turing_grid() saves a scan_turing5-format scan from this session.
v5z5 docstring follows.
atlas_v5z5 Z / row provider (TRUSTED; THEORY_M5 section 1, THEORY_M5b, THEORY_V5Z5.md) = the v5z3/v5z4 provider with configurable,
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
    raise SystemExit('atlas_v5z6: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')

from flint import arb, ctx  # noqa: E402

LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v14.dylib'
LIB_SHA = '7abaaa8aa0a913290cdb202a55d18c6c195130b20032614f3a60d07f0f10fa5b'
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
WORKERS = int(os.environ.get('ZFAST_WORKERS') or PARAMS['threads'])
CKPT = os.environ.get('ZFAST_CKPT') or ''
if not 1 <= WORKERS <= 64: raise ValueError(f'zfast_provider: ZFAST_WORKERS out of range {WORKERS}')
if CKPT and not STRICT: raise RuntimeError('zfast_provider: ZFAST_CKPT needs strict mode (one session per process)')
if not (PARAMS['H'] > 0 and 0 < PARAMS['Delta'] <= 1.0 and PARAMS['K'] >= 1 and PARAMS['J'] >= 1 and PARAMS['threads'] >= 1):
    raise ValueError(f'zfast_provider: session parameters out of range {PARAMS}')
if STRICT and os.environ.get('ZFAST_CENTER') in (None, ''):
    raise RuntimeError('zfast_provider strict mode: ZFAST_CENTER is required')
ROW_A = (2.8, 1.6)
_L = ctypes.CDLL(LIBPATH)
_L.zfa4_new.restype = ctypes.c_void_p
_L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_L.zfa14_new.restype = ctypes.c_void_p
_L.zfa14_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
_L.zfa14_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_L.zfa14_hash.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_DP = ctypes.POINTER(ctypes.c_double)
_L.zfa14_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, _DP, _DP, _DP, ctypes.c_int]
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
                center=os.environ.get('ZFAST_CENTER'), lib_sha=LIB_SHA, lib='v14', workers=WORKERS, ckpt=CKPT or None)


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
        s = _L.zfa14_new(str(T0).encode(), c, PARAMS['H'], PARAMS['Delta'], PARAMS['K'], PARAMS['J'], PARAMS['threads'], WORKERS, CKPT.encode())
        if not s: raise RuntimeError('zfa14_new failed (a checkpoint of a different session, or bad parameters)')
        _L.zfa14_info(s, _BUF, 4096); info = json.loads(_BUF.value.decode()); STATS['info'] = info
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


def state_sha256(T0, u):
    """SHA-256 of the complete state of the session serving (T0, u) (identity tests)."""
    s = _session(T0, float(u))
    if _L.zfa14_hash(s, _BUF, 4096) != 0: raise RuntimeError('zfa14_hash failed')
    return _BUF.value.decode()


def turing_grid(T0, outdir, u0, step, n):
    """DIAGNOSTIC (not a certificate input): Z on u_k = u0 + k*step (k < n) from this process's session, sign changes, dips refined on a
    10x finer 21-point grid, the minimal disjoint intervals -- exactly scan_turing5.py's `scan` logic (grid, sgn, zeros_from, dips,
    fine, check_disjoint) -- saved as OUTDIR/{scan_turing.json, zeros_intervals.json, grid.npz}, the format `scan_turing5.py recount`
    reads (it then computes the Turing counts; that tool is the record).  Points from zfa14_Zgrid (identical to zfa3_Zgrid)."""
    import numpy as np, time
    u0 = float(u0); step = float(step); n = int(n)
    if not STRICT: raise RuntimeError('turing_grid: strict mode only (one session)')
    if os.path.exists(outdir): raise RuntimeError(f'turing_grid: {outdir} exists (never overwrite)')
    s = _session(T0, u0); c = float(os.environ['ZFAST_CENTER']); uend = u0 + (n - 1) * step
    if not (c - PARAMS['H'] <= u0 and uend <= c + PARAMS['H']): raise RuntimeError(f'turing_grid: grid [{u0}, {uend}] outside the session')
    t0 = time.time()

    def grid(a, st, m):
        mid = (ctypes.c_double * m)(); rad = (ctypes.c_double * m)(); uu = (ctypes.c_double * m)()
        if _L.zfa14_Zgrid(s, a, st, m, mid, rad, uu, WORKERS) != 0: raise RuntimeError('zfa14_Zgrid failed')
        return np.array(uu[:]), np.array(mid[:]), np.array(rad[:])
    u, m, r = grid(u0, step, n)
    def sgn(mm, rr): return np.where(np.abs(mm) > rr, np.sign(mm), 0)
    sg = sgn(m, r)
    def zeros_from(uu, ss):
        idx = np.nonzero(ss)[0]; out = []
        for a, b in zip(idx, idx[1:]):
            if ss[a] != ss[b]: out.append((float(uu[a]), float(uu[b])))
        return out
    Z = zeros_from(u, sg)
    dips = [i for i in range(1, len(m) - 1) if sg[i - 1] == sg[i] == sg[i + 1] != 0 and abs(m[i]) < abs(m[i - 1]) and abs(m[i]) < abs(m[i + 1])
            and abs(m[i]) < 0.05 * max(abs(m[i - 1]), abs(m[i + 1]))]
    extra = []
    for i in dips:
        uu, mm, rr = grid(float(u[i - 1]), step / 10, 21); extra += zeros_from(uu, sgn(mm, rr))
    allZ = sorted(set(Z) | set(extra))
    fine = sorted((a, b) for a, b in allZ if not any(a <= cc and d <= b and (cc, d) != (a, b) for cc, d in allZ))
    for i in range(len(fine) - 1):
        if not fine[i][1] <= fine[i + 1][0]: raise RuntimeError(f'turing_grid: intervals not disjoint at {fine[i]} {fine[i + 1]}')
    os.makedirs(outdir)
    rec = dict(tool='atlas_v5z6 zfast_provider.turing_grid (scan_turing5 scan logic; counts by scan_turing5.py recount)', T0=str(T0), lib=LIBPATH,
               lib_sha256=LIB_SHA, session=STATS.get('info'), session_params=dict(centre=c, H=PARAMS['H'], Delta=PARAMS['Delta'], K=PARAMS['K'],
               J=PARAMS['J'], threads=PARAMS['threads'], workers=WORKERS, u0=u0, n=n, step=step),
               grid=dict(points=len(u), step=step, undecided=int(np.sum(sg == 0)), seconds=round(time.time() - t0, 1), ends=[repr(float(u[0])), repr(float(u[-1]))]),
               zeros_found=len(fine), dips=len(dips), dip_zeros=len(extra), turing={})
    json.dump(rec, open(os.path.join(outdir, 'scan_turing.json'), 'w'), indent=1)
    json.dump(dict(intervals=fine), open(os.path.join(outdir, 'zeros_intervals.json'), 'w'))
    np.savez(os.path.join(outdir, 'grid.npz'), u=u, mid=m, rad=r)
    return dict(points=len(u), zeros_found=len(fine), undecided=rec['grid']['undecided'], dips=len(dips), seconds=rec['grid']['seconds'])
