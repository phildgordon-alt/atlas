"""atlas_v5za Z / row provider (TRUSTED; PREDICTIONS_M14 / THEORY_V5ZA.md) = the v5z9 provider on libzfast.v14d (same ctypes API; exact
radius parse (MJ-C1), identical duplicates ignored, checkpoint I/O error => session aborted (CKPT-IO-ABORT)).  A refused checkpointed
session appends {t, pid, role, nonce, ckpt, lib_sha, error} to CKPT + '.refusals.jsonl' (read by the v5za driver); a session reporting
ckpt_write_errors > 0 raises.  Hook prefixes add ZFAST14D_TEST.  v5z9 docstring follows.
atlas_v5z9 Z / row provider (TRUSTED; PREDICTIONS_M13 / THEORY_V5Z9.md) = the v5z8 provider on libzfast.v14c (same ctypes API;
checkpoint format v3: header-bound, index-bound line seals, duplicates refused, atomic keys, no FLINT abort in the parser, time-based
fsync, environment identity without placeholders).  Hook prefixes add ZFAST14C_TEST.  v5z8 docstring follows.
atlas_v5z8 Z / row provider (TRUSTED; PREDICTIONS_M12 / THEORY_V5Z8.md) = the v5z6 provider on libzfast.v14b (compute path = v14 =
v13b at equal D; hardened checkpoint).  Checkpoints (strict mode only) need ZFAST_CKPT_ROLE (gen | replay), ZFAST_CKPT_NONCE (the run's
32-hex nonce) and ZFAST_CKPT_KEY (HMAC key file, created by libzfast for a new checkpoint); ZFAST_CKPT_VERIFY (default 8, >= 1) loaded items
are recomputed on resume.  A refused session raises with libzfast's reason.  D (ZFAST_THREADS) must be in [1, 16].  Importing this module
with any test-hook variable (ZFAST14_TEST*, ZFAST14B_TEST*, ZFAST14_GENERIC_KERNEL) set raises (review_m10 m8).  Every checkpointed
session appends one JSON record to CKPT + '.sessions.jsonl' (read by the v5z8 driver and replay_target).  v5z6 docstring follows.
atlas_v5z6 Z / row provider (TRUSTED; RESULTS_M9 / THEORY_V5Z6.md) = the v5z5 provider on libzfast.v14, whose sessions are
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
    raise SystemExit('atlas_v5za: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')
HOOK_PREFIXES = ('ZFAST14_TEST', 'ZFAST14B_TEST', 'ZFAST14C_TEST', 'ZFAST14D_TEST', 'ZFAST14_GENERIC_KERNEL')
if any(k.startswith(HOOK_PREFIXES) for k in os.environ):
    raise SystemExit('atlas_v5za zfast_provider: a libzfast test-hook variable is set (review_m10 m8): ' + ', '.join(k for k in os.environ if k.startswith(HOOK_PREFIXES)))

from flint import arb, ctx  # noqa: E402

LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v14d.dylib'
LIB_SHA = 'e0ed15f3cd4d62f887ab62cf6f6af0be5f378d356e35663ef9bafd432c425b81'
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
CK_ROLE = os.environ.get('ZFAST_CKPT_ROLE') or ''; CK_NONCE = os.environ.get('ZFAST_CKPT_NONCE') or ''; CK_KEY = os.environ.get('ZFAST_CKPT_KEY') or ''
CK_VERIFY = int(os.environ.get('ZFAST_CKPT_VERIFY') or '8')
if not 1 <= PARAMS['threads'] <= 16: raise ValueError(f'zfast_provider: decomposition D = ZFAST_THREADS {PARAMS["threads"]} outside [1, 16] (review_m10 m7)')
if CKPT and not (CK_ROLE in ('gen', 'replay') and len(CK_NONCE) == 32 and all(c in '0123456789abcdef' for c in CK_NONCE) and CK_KEY and CK_VERIFY >= 1):
    raise RuntimeError('zfast_provider: ZFAST_CKPT needs ZFAST_CKPT_ROLE (gen|replay), ZFAST_CKPT_NONCE (32 hex), ZFAST_CKPT_KEY and ZFAST_CKPT_VERIFY >= 1')
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
_L.zfa14b_new.restype = ctypes.c_void_p
_L.zfa14b_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                          ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
_L.zfa14b_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_L.zfa14b_last_error.argtypes = [ctypes.c_char_p, ctypes.c_int]
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
                center=os.environ.get('ZFAST_CENTER'), lib_sha=LIB_SHA, lib='v14d', workers=WORKERS, ckpt=CKPT or None,
                ckpt_role=CK_ROLE or None, ckpt_nonce=CK_NONCE or None, ckpt_verify=CK_VERIFY if CKPT else None)


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
        s = _L.zfa14b_new(str(T0).encode(), c, PARAMS['H'], PARAMS['Delta'], PARAMS['K'], PARAMS['J'], PARAMS['threads'], WORKERS, CKPT.encode(),
                          CK_ROLE.encode(), CK_NONCE.encode(), CK_KEY.encode(), CK_VERIFY)
        if not s:
            _L.zfa14b_last_error(_BUF, 4096); err = _BUF.value.decode()
            if CKPT:          # v5za (review_v14c mn-C4): the refusal reason is recorded for the driver
                import time as _t
                try:
                    with open(CKPT + '.refusals.jsonl', 'a') as _f:
                        _f.write(json.dumps(dict(t=_t.time(), pid=os.getpid(), role=CK_ROLE, nonce=CK_NONCE, ckpt=CKPT, lib_sha=LIB_SHA, error=err)) + '\n'); _f.flush(); os.fsync(_f.fileno())
                except OSError as ex:
                    print(f'zfast_provider: could not record the refusal ({ex})', file=sys.stderr, flush=True)
                if err.startswith('CKPT-IO-ABORT'):
                    print('zfast_provider: ==== CHECKPOINT I/O ERROR: SESSION ABORTED (CKPT-IO-ABORT) ====\n' + err, file=sys.stderr, flush=True)
            raise RuntimeError('zfa14b_new refused the session: ' + err)
        if _L.zfa14b_info(s, _BUF, 4096) != 0: raise RuntimeError('zfa14b_info failed')
        info = json.loads(_BUF.value.decode()); STATS['info'] = info
        if CKPT:
            import time as _t
            rec = dict(t=_t.time(), pid=os.getpid(), role=CK_ROLE, nonce=CK_NONCE, ckpt=CKPT, lib_sha=LIB_SHA, info=info)
            with open(CKPT + '.sessions.jsonl', 'a') as _f: _f.write(json.dumps(rec) + '\n'); _f.flush(); os.fsync(_f.fileno())
            if info.get('ckpt_write_errors'): raise RuntimeError(f'zfast_provider: CKPT-IO-ABORT: {info["ckpt_write_errors"]} checkpoint write error(s) in a returned session (v14d aborts on any; refusing)')
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
    rec = dict(tool='atlas_v5za zfast_provider.turing_grid (scan_turing5 scan logic; counts by scan_turing5.py recount)', T0=str(T0), lib=LIBPATH,
               lib_sha256=LIB_SHA, session=STATS.get('info'), session_params=dict(centre=c, H=PARAMS['H'], Delta=PARAMS['Delta'], K=PARAMS['K'],
               J=PARAMS['J'], threads=PARAMS['threads'], workers=WORKERS, u0=u0, n=n, step=step),
               grid=dict(points=len(u), step=step, undecided=int(np.sum(sg == 0)), seconds=round(time.time() - t0, 1), ends=[repr(float(u[0])), repr(float(u[-1]))]),
               zeros_found=len(fine), dips=len(dips), dip_zeros=len(extra), turing={})
    json.dump(rec, open(os.path.join(outdir, 'scan_turing.json'), 'w'), indent=1)
    json.dump(dict(intervals=fine), open(os.path.join(outdir, 'zeros_intervals.json'), 'w'))
    np.savez(os.path.join(outdir, 'grid.npz'), u=u, mid=m, rad=r)
    return dict(points=len(u), zeros_found=len(fine), undecided=rec['grid']['undecided'], dips=len(dips), seconds=rec['grid']['seconds'])
