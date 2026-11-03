"""Independent review of zfast's cos/sin kernel (THEORY_ZFAST section 6, Lemma 3; zfast.c cs_core).
Part A: an independent rigorous bound, derived here from scratch with a different method from tools/sincos_bound.py:
        the computed-y range [0, Y] is cut into NSUB pieces; on each piece the fma-Horner running error is propagated with interval
        magnitude enclosures (not global sums), the argument error uses |sin| on the piece and the exact relative error of fl(2 pi),
        and the Taylor/coefficient term uses the piece's upper end.  Odd/even symmetry (fl(-r) = -fl(r), RN symmetric) => y >= 0.
Part B: empirical test of the production kernel (zf_cos2pi in the sha-pinned libzfast.v10b.dylib) against Arb (200 bits):
        random v, the 56 boundary patterns, and dense adversarial sweeps near |y| = pi/4 and near y = 0.
Writes data/kernel_review.json.  Nothing else is touched."""
import ctypes, json, math, random, sys, time, hashlib
from flint import arb, ctx, fmpq

ctx.prec = 200
u = arb(2) ** -53
DEG = 8
cc_exact = [arb(fmpq((-1) ** j, math.factorial(2 * j))) for j in range(DEG + 1)]
sc_exact = [arb(fmpq((-1) ** j, math.factorial(2 * j + 1))) for j in range(DEG + 1)]
# the literals in zfast.c (copied from the source text, not from tools/)
CC = [float.fromhex(h) for h in "0x1.0000000000000p+0 -0x1.0000000000000p-1 0x1.5555555555555p-5 -0x1.6c16c16c16c17p-10 0x1.a01a01a01a01ap-16 -0x1.27e4fb7789f5cp-22 0x1.1eed8eff8d898p-29 -0x1.93974a8c07c9dp-37 0x1.ae7f3e733b81fp-45".split()]
SC = [float.fromhex(h) for h in "0x1.0000000000000p+0 -0x1.5555555555555p-3 0x1.1111111111111p-7 -0x1.a01a01a01a01ap-13 0x1.71de3a556c734p-19 -0x1.ae64567f544e4p-26 0x1.6124613a86d09p-33 -0x1.ae7f3e733b81fp-41 0x1.952c77030ad4ap-49".split()]
KTURN = float.fromhex("0x1.921fb54442d18p-62")
# check: the literals are the binary64 roundings of the exact coefficients and of 2 pi / 2^64
for j in range(DEG + 1):
    assert float(cc_exact[j]) == CC[j] and float(sc_exact[j]) == SC[j], j
twopi64 = 2 * arb.pi() / arb(2) ** 64
assert float(twopi64) == KTURN
kap = abs(arb(KTURN) - twopi64) / twopi64              # exact relative error of the constant (about 0.35 u)
dely = (1 + u) ** 2 * (1 + kap) - 1                    # y = y* (1 + eta), |eta| <= dely   (fl(r): u, product: u)
Ystar = arb.pi() / 4
Y = Ystar * (1 + dely)


def iv(lo, hi):
    lo, hi = arb(lo), arb(hi)
    return (lo + hi) / 2 + arb(0, ((hi - lo) / 2).upper())


def horner(coef, Z, zmax):
    """fma Horner coef[8], coef[7..1] at computed z in Z.  returns (enclosure of p_hat, err bound vs exact poly at the same z)"""
    P = arb(coef[DEG]); err = arb(0)
    for j in range(DEG - 1, 0, -1):
        ex = P * Z + arb(coef[j])                       # exact fma operand enclosure (P encloses p_hat_{j+1})
        err = zmax * err + u * abs(ex).upper()
        P = ex * (1 + arb(0, u))                        # rounded value enclosure
    return P, err


def piece(a, b):
    """bounds on [a, b] (computed |y|), returns (cos_err, sin_err)"""
    Yi = iv(a, b)
    Z = iv(arb(a) ** 2 * (1 - u), arb(b) ** 2 * (1 + u))       # computed z
    zmax = arb(b) ** 2 * (1 + u)
    # ---- cos: c = fma(Q_hat, z, 1)
    Q, eq = horner(CC, Z, zmax)
    fin = Q * Z + 1
    e_eval = zmax * eq + u * abs(fin).upper()
    Cp = sum(j * arb(CC[j]) * Z ** (j - 1) for j in range(1, DEG + 1))     # C'(z) enclosure on Z
    e_z = abs(Cp).upper() * u * arb(b) ** 2
    e_tay = sum(abs(arb(CC[j]) - cc_exact[j]) * arb(b) ** (2 * j) for j in range(DEG + 1)) + arb(b) ** (2 * DEG + 2) / math.factorial(2 * DEG + 2)
    ystar_max = arb(b) / (1 - dely)
    e_arg = abs((ystar_max * (1 + dely)).sin()) * dely * ystar_max       # |cos y - cos y*| <= max|sin| |y - y*|
    E_cos = e_eval + e_z + e_tay + e_arg
    # ---- sin: t = fl(y z), s = fma(t, Qs_hat, y)
    Qs, es = horner(SC, Z, zmax)
    T = Yi * Z * (1 + arb(0, u))
    tmax = arb(b) * zmax * (1 + u)
    fin = T * Qs + Yi
    e_eval_s = tmax * es + abs(Qs).upper() * u * arb(b) * zmax + u * abs(fin).upper()
    gp = sum(j * arb(SC[j]) * Z ** (j - 1) for j in range(1, DEG + 1))     # d/dw [w Q(w)]
    e_z_s = arb(b) * abs(gp).upper() * u * arb(b) ** 2
    e_tay_s = sum(abs(arb(SC[j]) - sc_exact[j]) * arb(b) ** (2 * j + 1) for j in range(DEG + 1)) + arb(b) ** (2 * DEG + 3) / math.factorial(2 * DEG + 3)
    e_arg_s = dely * ystar_max                                             # |cos| <= 1
    E_sin = e_eval_s + e_z_s + e_tay_s + e_arg_s
    return E_cos.upper(), E_sin.upper()


def part_a(nsub=2048):
    ec = es = arb(0); worst = None
    yb = Y.upper()
    for i in range(nsub):
        a = yb * i / nsub; b = yb * (i + 1) / nsub
        c, s = piece(a, b)
        if c > ec: ec = c; worst = ('cos', i)
        if s > es: es = s
    return dict(nsub=nsub, E_cos=float(ec.upper()), E_sin=float(es.upper()), E_cos_over_u=float((ec / u).upper()),
                E_sin_over_u=float((es / u).upper()), worst_piece=worst, kappa_over_u=float((kap / u).upper()))


# ---------------- Part B: empirical ----------------
LIB = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v10b.dylib'
LIB_SHA = '3daa33d516c062364ff7b5a7cb078ae3b9921483d20646d8587c392c246ef6f8'


def part_b(nrand, seed=20261019):
    assert hashlib.sha256(open(LIB, 'rb').read()).hexdigest() == LIB_SHA
    L = ctypes.CDLL(LIB)
    L.zf_cos2pi.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint64]
    c = ctypes.c_double(); s = ctypes.c_double()
    ctx.prec = 128
    two64 = arb(2) ** 64; tp = 2 * arb.pi()
    worst = dict(cos=(0.0, None), sin=(0.0, None)); n = 0
    def test(v):
        nonlocal n
        L.zf_cos2pi(ctypes.byref(c), ctypes.byref(s), v)
        x = tp * arb(v) / two64
        ec = abs(arb(c.value) - x.cos()); es = abs(arb(s.value) - x.sin())
        n += 1
        e1 = float(ec.upper()); e2 = float(es.upper())
        if e1 > worst['cos'][0]: worst['cos'] = (e1, v)
        if e2 > worst['sin'][0]: worst['sin'] = (e2, v)
    M = 1 << 64
    # boundary patterns (as THEORY 11.1) + extremes
    for q in range(4):
        for d in [0, 1, -1, 2, -2, 1 << 61, -(1 << 61), (1 << 61) - 1, -((1 << 61) - 1), (1 << 60), -(1 << 60), 3, -3, 1 << 30]:
            test((q * (1 << 62) + d) % M)
    rng = random.Random(seed)
    # dense sweeps near |y| = pi/4 (largest argument error) and near quadrant centres, all four quadrants
    for q in range(4):
        base = q * (1 << 62)
        for k in range(20000):
            test((base + (1 << 61) - 1 - rng.randrange(1 << 40)) % M)
            test((base - (1 << 61) + rng.randrange(1 << 40)) % M)
            test((base + rng.randrange(-(1 << 61), 1 << 61)) % M)
    for k in range(nrand):
        test(rng.randrange(M))
    return dict(n=n, max_cos_err=worst['cos'][0], v_cos=str(worst['cos'][1]), max_sin_err=worst['sin'][0], v_sin=str(worst['sin'][1]))


if __name__ == '__main__':
    t0 = time.time()
    A = part_a(int(sys.argv[1]) if len(sys.argv) > 1 else 2048)
    tA = time.time() - t0
    B = part_b(int(sys.argv[2]) if len(sys.argv) > 2 else 400000)
    out = dict(part_a_independent_bound=A, zfast_claimed_E_c=4.88e-16, zfast_tool_values=dict(E_cos=4.8731e-16, E_sin=3.9094e-16),
               part_b_empirical=B, sec_a=tA, sec_total=time.time() - t0)
    json.dump(out, open('/Users/kiosk/atlas_mark2/diagnostic/zfast/review/data/kernel_review.json', 'x'), indent=1)
    print(json.dumps(out, indent=1))
