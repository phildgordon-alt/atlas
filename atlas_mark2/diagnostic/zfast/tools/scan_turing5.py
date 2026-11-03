"""M8 scan + Turing count, v5 (new file; scan_turing2/3/4 and turing_extra/2 are untouched).  Diagnostic, NOT part of any certificate.

Fixes F-M7a (RESULTS_M7 section 3): in v2-v4 Lemma T integrated theta/pi + 1 over [v, fl(v + Delta_T)] but divided by arb(Delta_T); with a
non-integer clipped Delta_T those differ.  Here every Turing quantity is EXACT RATIONAL: v and Delta_T are Fractions (v from the decimal
string given, Delta_T an integer or exact rational), the integration interval is exactly [T0 + v, T0 + v + Delta_T] (resp. [v - D, v]),
the divisor is exactly Delta_T, and the zero-interval selection compares exact Fractions.  Delta_T rule: D = min(DT, floor(v - ulo),
floor(uhi - v)) with ulo/uhi the exact grid ends (DT = 40 default) -> 40 / 36 / 38 exactly where v2-v4 used them; never a clipped float.
Formulas otherwise identical to scan_turing2/3/4 (Arb theta integrals: trapezoid minus the theta'' ball term; Bober-Hiary bound
B(x) = 0.128 log x + 2.30; integer extraction of ceil(L) / floor(U)).  Explicit raises (no asserts); refuses -O / PYTHONOPTIMIZE.

  scan_turing5.py scan T0 OUTDIR --centre C --H H --delta D --u0 U0 --n N --points v1,v2,... [--step 0.004] [--DT 40] [--threads n]
      one kind-0 zfast session (libzfast.v13b), K = 18, J = 12; Z on u = U0 + k*step (k < N); certified sign changes (|mid| > rad both
      sides), dips refined on a 10x finer grid; Turing count at each v.  Writes OUTDIR/{scan_turing.json, zeros_intervals.json, grid.npz}.
  scan_turing5.py recount SCANDIR OUTJSON --points v1,v2,... [--DT 40] [--win a,b ...]
      no zfast call: Turing count from a SAVED scan (grid.npz + zeros_intervals.json + scan_turing.json of scan_turing2/3/4/5).
      sign of Z(T0 + v) from the grid point u_k == v (exact), else from the zfast ball recorded at v in scan_turing.json, else raise."""
import ctypes, json, math, sys, time, os, hashlib
from fractions import Fraction as F
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'): raise SystemExit('refusing to run under -O / PYTHONOPTIMIZE')
import numpy as np
from flint import arb, acb, acb_series, ctx
import flint
LIB = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v13b.dylib'
TOOL_SHA = hashlib.sha256(open(__file__, 'rb').read()).hexdigest()


class TuringError(RuntimeError):
    pass


def _arg(argv, k, f, default=None):
    if k not in argv:
        if default is None: raise TuringError(f'missing {k}')
        return default
    return f(argv[argv.index(k) + 1])


# ---------------------------------------------------------------- Lemma T, exact rational bookkeeping
ctx.prec = 300


def hx(T0, v):
    f = F(T0) + F(v); return arb(f.numerator) / arb(f.denominator)


def theta(t): return (acb(arb(1) / 4, t / 2).lgamma()).imag - t / 2 * arb.pi().log()


def theta2_ball(a, b):
    c = (a + b) / 2; rr = (b - a) / 2; t = c + arb(0, rr.upper())
    co = acb_series([acb(arb(1) / 4, t / 2), acb(0, arb(1) / 2)], 3).lgamma().coeffs(); return 2 * co[2].imag


def int_theta_pi_plus1(T0, ua, ub):
    """ball containing integral_{T0+ua}^{T0+ub} (theta/pi + 1); ua, ub exact Fractions"""
    a, b = hx(T0, ua), hx(T0, ub); w = b - a
    I = w * (theta(a) + theta(b)) / 2 - w ** 3 / 12 * theta2_ball(a, b)
    return I / arb.pi() + w


def B(x): return arb('0.128') * x.log() + arb('2.30')


def arbF(q): q = F(q); return arb(q.numerator) / arb(q.denominator)


def choose_D(v, ulo, uhi, DT):
    """largest D = min(DT, floor(v - ulo), floor(uhi - v)) (exact); DT itself may be any exact rational"""
    DT = F(DT); m = min(DT, F(math.floor(v - ulo)), F(math.floor(uhi - v)))
    if m < 1: raise TuringError(f'v = {v}: grid does not reach 1 unit on both sides (ulo {ulo}, uhi {uhi})')
    return m


def turing(T0, v, D, fine, sign):
    """Lemma T at T0 + v with exact Delta_T = D.  fine: disjoint certified sign-change intervals (float pairs, u-offsets).
    sign: (+1/-1/0, record) of Z(T0 + v).  Returns the record; N is set iff both bounds give the same integer and the sign is decided."""
    v = F(v); D = F(D)
    if D <= 0: raise TuringError('Delta_T must be positive')
    vp, vm = v + D, v - D                                   # exact
    up = [(a, b) for a, b in fine if F(a) >= v and F(b) <= vp]
    lo = [(a, b) for a, b in fine if F(b) <= v and F(a) >= vm]
    Ip = int_theta_pi_plus1(T0, v, vp); Im = int_theta_pi_plus1(T0, vm, v)
    Hp = hx(T0, vp); Hm = hx(T0, vm)
    U = (B(Hp) + Ip - sum((Hp - hx(T0, F(b)) for a, b in up), arb(0))) / arbF(D)
    Lb = (Im + sum((hx(T0, F(a)) - Hm for a, b in lo), arb(0)) - B(hx(T0, v))) / arbF(D)
    lo_i = int(arb(Lb.lower()).ceil().unique_fmpz()); hi_i = int(arb(U.upper()).floor().unique_fmpz())
    sg, zrec = sign
    pinned = (lo_i == hi_i and sg != 0)
    return dict(v=float(v), v_exact=str(v), Delta=float(D), Delta_exact=str(D), N_lower=lo_i, N_upper=hi_i, Z_sign=sg, Z_src=zrec,
                U=U.str(12, radius=False), L=Lb.str(12, radius=False), U_minus_L=float((U - Lb).upper()),
                zeros_up=len(up), zeros_down=len(lo), pinned=pinned, N=(lo_i if pinned else None))


def check_disjoint(fine):
    for i in range(len(fine) - 1):
        if not fine[i][1] <= fine[i + 1][0]: raise TuringError(f'intervals not disjoint at {fine[i]} {fine[i + 1]}')


def windows_report(TC, fine, wins):
    out = {}
    for a, b in wins:
        ka, kb = str(F(a)), str(F(b)); Na, Nb = TC[ka]['N'], TC[kb]['N']
        out[f'{a},{b}'] = dict(count=(Nb - Na) if Na is not None and Nb is not None else None,
                               sign_changes_in_window=sum(1 for x, y in fine if F(x) >= F(a) and F(y) <= F(b)),
                               straddling=[[x, y] for x, y in fine if F(x) < F(a) < F(y) or F(x) < F(b) < F(y)])
    return out


def parse_points(s): return [F(x) for x in s.split(',')]


# ---------------------------------------------------------------- mode: recount (no zfast call)
def recount(argv):
    SCAN, OUT = argv[0], argv[1]
    if os.path.exists(OUT): raise TuringError(f'{OUT} exists (never overwrite)')
    pts = parse_points(_arg(argv, '--points', str)); DT = _arg(argv, '--DT', F, F(40))
    wins = [tuple(F(y) for y in argv[i + 1].split(',')) for i, x in enumerate(argv) if x == '--win']
    st = json.load(open(SCAN + '/scan_turing.json')); T0 = int(st['T0'])
    fine = sorted(tuple(x) for x in json.load(open(SCAN + '/zeros_intervals.json'))['intervals']); check_disjoint(fine)
    g = np.load(SCAN + '/grid.npz'); u, m, r = g['u'], g['mid'], g['rad']
    ulo, uhi = F(float(u[0])), F(float(u[-1]))
    def zsign(v):
        k = np.nonzero(u == float(v))[0]
        if len(k) == 1 and F(float(u[int(k[0])])) == v:
            k = int(k[0]); mid, rad = float(m[k]), float(r[k])
            return ((1 if mid > 0 else -1) if abs(mid) > rad else 0), dict(source='grid', k=k, mid=mid, rad=rad)
        rec = st.get('turing', {}).get(str(float(v)))
        if rec and F(rec.get('v', float(v))) == v and 'Z' in rec:
            z = arb(rec['Z']); return (1 if z > 0 else -1 if z < 0 else 0), dict(source='scan_turing.json zfast ball', Z=rec['Z'])
        raise TuringError(f'no decided Z value at v = {v} in the saved scan')
    allp = sorted(set(pts) | {x for w in wins for x in w})
    TC = {}
    for v in allp:
        D = choose_D(v, ulo, uhi, DT); TC[str(v)] = turing(T0, v, D, fine, zsign(v))
    res = dict(tool='scan_turing5.py recount', tool_sha256=TOOL_SHA, T0=str(T0), scan=os.path.abspath(SCAN), DT=str(DT),
               grid_ends=[str(ulo), str(uhi)], zeros_in_scan=len(fine), turing=TC, windows=windows_report(TC, fine, wins),
               flint=flint.__version__)
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps(res['windows']), json.dumps({k: (v['N'], v['pinned'], round(v['U_minus_L'], 3), v['Delta_exact']) for k, v in TC.items()}))


# ---------------------------------------------------------------- mode: scan (one zfast session)
def scan(argv):
    T0 = int(argv[0]); OUT = argv[1]; TH = _arg(argv, '--threads', int, 1)
    CEN = _arg(argv, '--centre', float); HH = _arg(argv, '--H', float); DEL = _arg(argv, '--delta', float)
    U0 = _arg(argv, '--u0', float); NG = _arg(argv, '--n', int); STEP = _arg(argv, '--step', float, 0.004)
    pts = parse_points(_arg(argv, '--points', str)); DT = _arg(argv, '--DT', F, F(40))
    wins = [tuple(F(y) for y in argv[i + 1].split(',')) for i, x in enumerate(argv) if x == '--win']
    UHI = U0 + (NG - 1) * STEP
    if not (CEN - HH <= U0 and UHI <= CEN + HH): raise TuringError('grid outside the session')
    os.makedirs(OUT, exist_ok=False)
    L = ctypes.CDLL(LIB)
    L.zfa4_new.restype = ctypes.c_void_p
    L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    L.zfa3_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
    L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
    L.zfa3_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    BUF = ctypes.create_string_buffer(4096)
    t_start = time.time()
    S = L.zfa4_new(str(T0).encode(), CEN, HH, DEL, 18, 12, TH)
    if not S: raise TuringError('zfa4_new failed')
    L.zfa3_info(S, BUF, 4096); info = json.loads(BUF.value.decode()); t_build = time.time() - t_start
    def grid(u0, step, n):
        mid = (ctypes.c_double * n)(); rad = (ctypes.c_double * n)(); uu = (ctypes.c_double * n)()
        L.zfa3_Zgrid(S, u0, step, n, mid, rad, uu)
        return np.array(uu[:]), np.array(mid[:]), np.array(rad[:])
    t1 = time.time(); u, m, r = grid(U0, STEP, NG); t_grid = time.time() - t1
    def sgn(mm, rr): return np.where(np.abs(mm) > rr, np.sign(mm), 0)
    s = sgn(m, r)
    def zeros_from(u, s):
        idx = np.nonzero(s)[0]; out = []
        for a, b in zip(idx, idx[1:]):
            if s[a] != s[b]: out.append((float(u[a]), float(u[b])))
        return out
    Z = zeros_from(u, s)
    dips = [i for i in range(1, len(m) - 1) if s[i - 1] == s[i] == s[i + 1] != 0 and abs(m[i]) < abs(m[i - 1]) and abs(m[i]) < abs(m[i + 1])
            and abs(m[i]) < 0.05 * max(abs(m[i - 1]), abs(m[i + 1]))]
    extra = []
    for i in dips:
        uu, mm, rr = grid(float(u[i - 1]), STEP / 10, 21); extra += zeros_from(uu, sgn(mm, rr))
    allZ = sorted(set(Z) | set(extra))
    fine = sorted((a, b) for a, b in allZ if not any(a <= c and d <= b and (c, d) != (a, b) for c, d in allZ))
    check_disjoint(fine)
    ulo, uhi = F(float(u[0])), F(float(u[-1]))
    def zsign(v):
        k = np.nonzero(u == float(v))[0]
        if len(k) == 1 and F(float(u[int(k[0])])) == v:
            k = int(k[0]); mid, rad = float(m[k]), float(r[k])
            return ((1 if mid > 0 else -1) if abs(mid) > rad else 0), dict(source='grid', k=k, mid=mid, rad=rad)
        if F(float(v)) != v: raise TuringError(f'v = {v} not a binary64 number; cannot evaluate zfast there')
        L.zfa3_Z(S, float(v), BUF, 4096); d = json.loads(BUF.value.decode()); z = arb(d['Z'])
        return (1 if z > 0 else -1 if z < 0 else 0), dict(source='zfast ball', Z=d['Z'])
    allp = sorted(set(pts) | {x for w in wins for x in w})
    TC = {}
    for v in allp:
        D = choose_D(v, ulo, uhi, DT); TC[str(v)] = turing(T0, v, D, fine, zsign(v))
    res = dict(tool='scan_turing5.py scan', tool_sha256=TOOL_SHA, T0=str(T0), lib=LIB,
               lib_sha256=hashlib.sha256(open(LIB, 'rb').read()).hexdigest(), session=info,
               session_params=dict(centre=CEN, H=HH, Delta=DEL, K=18, J=12, threads=TH, u0=U0, n=NG, step=STEP),
               grid=dict(points=len(u), step=STEP, undecided=int(np.sum(s == 0)), seconds=round(t_grid, 1), ends=[str(ulo), str(uhi)]),
               zeros_found=len(fine), dips=len(dips), dip_zeros=len(extra), DT=str(DT), turing=TC, windows=windows_report(TC, fine, wins),
               build_seconds=round(t_build, 1), wall=round(time.time() - t_start, 1), flint=flint.__version__,
               env={k: os.environ.get(k) for k in ('ZFAST_THREADS', 'OMP_NUM_THREADS')})
    json.dump(res, open(OUT + '/scan_turing.json', 'w'), indent=1)
    json.dump(dict(intervals=fine), open(OUT + '/zeros_intervals.json', 'w'))
    np.savez(OUT + '/grid.npz', u=u, mid=m, rad=r)
    print(json.dumps({k2: v2 for k2, v2 in res.items() if k2 not in ('turing', 'session')}, indent=1))
    print(json.dumps({k: (v['N'], v['pinned'], round(v['U_minus_L'], 3), v['Delta_exact']) for k, v in TC.items()}))


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('scan', 'recount'): raise SystemExit(__doc__)
    try:
        (scan if sys.argv[1] == 'scan' else recount)(sys.argv[2:])
    except TuringError as e:
        raise SystemExit(f'scan_turing5: {e}')
