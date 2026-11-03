"""M5 scan + Turing count (v2 of scan_turing.py: exact integer extraction; grid saved).   (THEORY_M5 sections 3-4).  scan_turing.py T0 OUTDIR [--threads n] [--extra k1,k2,...]
One kind-0 zfast session (libzfast.v12a) centred at T0 + 1, H = 61, Delta = 0.012, K = 18; Z on u = -60 + k*0.004 (k = 0..30500).
(a) zeros located by certified sign changes (|mid| > rad on both sides); dips refined on a 10x finer grid;
(b) closest pair (normalized gap) among zeros with midpoint in [-20, 22]  -> pair window [k, k+2], k = floor(mid) - 1;
(c) Turing count (Lemma T, separate method) of N(T0 + v) for v in {0, 2} and the pair window ends, Delta_T = 40 (or less if the
    grid does not reach), with Arb theta integrals and Bober-Hiary's bound B(x) = 0.128 log x + 2.30."""
import ctypes, json, math, sys, time, os
import numpy as np
from flint import arb, acb, acb_series, ctx
LIB = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v12a.dylib'
L = ctypes.CDLL(LIB)
L.zfa4_new.restype = ctypes.c_void_p
L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
L.zfa3_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
L.zfa3_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
BUF = ctypes.create_string_buffer(4096)
T0 = int(sys.argv[1]); OUT = sys.argv[2]; TH = int(sys.argv[sys.argv.index('--threads') + 1]) if '--threads' in sys.argv else 1
os.makedirs(OUT, exist_ok=False)
t_start = time.time()
S = L.zfa4_new(str(T0).encode(), 1.0, 61.0, 0.012, 18, 12, TH)
L.zfa3_info(S, BUF, 4096); info = json.loads(BUF.value.decode())
def grid(u0, step, n):
    mid = (ctypes.c_double * n)(); rad = (ctypes.c_double * n)(); uu = (ctypes.c_double * n)()
    L.zfa3_Zgrid(S, u0, step, n, mid, rad, uu)
    return np.array(uu[:]), np.array(mid[:]), np.array(rad[:])
t1 = time.time()
u, m, r = grid(-60.0, 0.004, 30501)
t_grid = time.time() - t1
def sgn(mm, rr): return np.where(np.abs(mm) > rr, np.sign(mm), 0)
s = sgn(m, r)
def zeros_from(u, s):
    idx = np.nonzero(s)[0]; out = []
    for a, b in zip(idx, idx[1:]):
        if s[a] != s[b]: out.append((float(u[a]), float(u[b])))
    return out
Z = zeros_from(u, s)
# dips: local minima of |m| with no sign change among 3 consecutive certified-sign points, |m| < 0.05 * neighbours' max
dips = []
for i in range(1, len(m) - 1):
    if s[i - 1] == s[i] == s[i + 1] != 0 and abs(m[i]) < abs(m[i - 1]) and abs(m[i]) < abs(m[i + 1]) and abs(m[i]) < 0.05 * max(abs(m[i - 1]), abs(m[i + 1])):
        dips.append(i)
extra = []
for i in dips:
    uu, mm, rr = grid(float(u[i - 1]), 0.0004, 21)
    zz = zeros_from(uu, sgn(mm, rr))
    extra += zz
allZ = sorted(set(Z) | set(extra))
# remove coarse intervals that contain refined ones (keep disjoint, finest)
fine = []
for a, b in allZ:
    if any(a <= c and d <= b and (c, d) != (a, b) for c, d in allZ): continue
    fine.append((a, b))
fine = sorted(fine)
assert all(fine[i][1] <= fine[i + 1][0] for i in range(len(fine) - 1)), 'intervals not disjoint'
mean = 2 * math.pi / math.log(T0 / (2 * math.pi))
mids = [(a + b) / 2 for a, b in fine]
cand = [(mids[i + 1] - mids[i], i) for i in range(len(mids) - 1) if -20 <= mids[i] and mids[i + 1] <= 22]
gmin, gi = min(cand)
pair = dict(z1=fine[gi], z2=fine[gi + 1], gap_mid=gmin, delta_mid=gmin / mean, gap_lower=fine[gi + 1][0] - fine[gi][1], gap_upper=fine[gi + 1][1] - fine[gi][0])
pmid = (mids[gi] + mids[gi + 1]) / 2; k = math.floor(pmid) - 1
if pmid - k < 0.5: k -= 1
if pmid - k > 1.5: k += 1
pair['window_offsets'] = [k, k + 2]
# ---- Turing count (Lemma T) ----
ctx.prec = 300
def hx(u):
    from fractions import Fraction
    f = Fraction(T0) + Fraction(u); return arb(f.numerator) / arb(f.denominator)
def theta(t): return (acb(arb(1) / 4, t / 2).lgamma()).imag - t / 2 * arb.pi().log()
def theta2_ball(a, b):
    c = (a + b) / 2; rr = (b - a) / 2; t = c + arb(0, rr.upper())
    co = acb_series([acb(arb(1) / 4, t / 2), acb(0, arb(1) / 2)], 3).lgamma().coeffs(); return 2 * co[2].imag
def int_theta_pi_plus1(ua, ub):
    """ball containing integral_{T0+ua}^{T0+ub} (theta/pi + 1)"""
    a, b = hx(ua), hx(ub); w = b - a
    I = w * (theta(a) + theta(b)) / 2 - w ** 3 / 12 * theta2_ball(a, b)
    return I / arb.pi() + w
def B(x): return arb('0.128') * x.log() + arb('2.30')
def Zsign(uv):
    L.zfa3_Z(S, uv, BUF, 4096); d = json.loads(BUF.value.decode()); z = arb(d['Z'])
    return (1 if z > 0 else -1 if z < 0 else 0), d
def turing(v, D=40.0):
    sg, zd = Zsign(v)
    D = min(D, v - (-60.0), 62.0 - v - 1e-9)
    up = [(a, b) for a, b in fine if a >= v and b <= v + D]
    lo = [(a, b) for a, b in fine if b <= v and a >= v - D]
    Ip = int_theta_pi_plus1(v, v + D); Im = int_theta_pi_plus1(v - D, v)
    U = (B(hx(v + D)) + Ip - sum((hx(v + D) - hx(b) for a, b in up), arb(0))) / arb(D)
    Lb = (Im + sum((hx(a) - hx(v - D) for a, b in lo), arb(0)) - B(hx(v))) / arb(D)
    lo_i = int(arb(Lb.lower()).ceil().unique_fmpz()); hi_i = int(arb(U.upper()).floor().unique_fmpz())   # exact (v2)
    return dict(N_lower=lo_i, N_upper=hi_i, v=v, Z_sign=sg, Z=zd['Z'][:30], Delta=D, U=U.str(12, radius=False), L=Lb.str(12, radius=False), U_minus_L=float((U - Lb).upper()),
                zeros_up=len(up), zeros_down=len(lo), pinned=(lo_i == hi_i and sg != 0), N=(lo_i if lo_i == hi_i and sg != 0 else None))
pts = sorted(set([0.0, 2.0, float(k), float(k + 2)] + [float(x) for x in (sys.argv[sys.argv.index('--extra') + 1].split(',') if '--extra' in sys.argv else [])]))
TC = {str(v): turing(v) for v in pts}
cnt = lambda a, b: (TC[str(b)]['N'] - TC[str(a)]['N']) if TC[str(a)]['N'] is not None and TC[str(b)]['N'] is not None else None
res = dict(T0=str(T0), session=info, grid=dict(points=len(u), step=0.004, undecided=int(np.sum(s == 0)), seconds=round(t_grid, 1)),
           zeros_found=len(fine), dips=len(dips), dip_zeros=len(extra), mean_spacing=mean, closest_pair=pair, turing=TC,
           count_window_0_2=cnt(0.0, 2.0), count_pair_window=cnt(float(k), float(k + 2)),
           sign_changes_in_0_2=sum(1 for a, b in fine if a >= 0 and b <= 2), sign_changes_in_pair_window=sum(1 for a, b in fine if a >= k and b <= k + 2),
           wall=round(time.time() - t_start, 1))
json.dump(res, open(OUT + '/scan_turing.json', 'w'), indent=1)
json.dump(dict(intervals=fine), open(OUT + '/zeros_intervals.json', 'w'))
np.savez(OUT + '/grid.npz', u=u, mid=m, rad=r)
print(json.dumps({k2: v2 for k2, v2 in res.items() if k2 not in ('turing',)}, indent=1)); print(json.dumps(TC, indent=1))
