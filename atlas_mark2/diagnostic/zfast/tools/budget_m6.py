"""M6: explicit zfast error budget at T = 10^E (E = 23 calibration, E = 24 target).  Pure arithmetic on the bound formulas that
libzfast.v13b evaluates per block (THEORY_ZFAST sections 5-7, THEORY_M3 section 3, zfast_m3b.inc mom_range); no zfast call.
Prints: N, the 2^52 and binary64 guards, wp, block lengths, the per-term bound constants, the a-priori session radius for the
production session (H = 4, Delta = 0.15, K = 18) and the scan session (H = 61, Delta = 0.012, K = 18), the RS remainder at K = 2..6,
and the N_win enclosure error of model5.count_upper5 (256 + bitlen T0).   usage: budget_m6.py E [E ...]"""
import math, sys, json
u = 2.0 ** -53; EC = 4.88e-16; J = 12; BMAX = 1 << 14; LOG2_INTERP = -72.0

def choose_B(n0, log2tau):
    l2r = (LOG2_INTERP + math.log2(J + 1) - log2tau) / (J + 1)
    Bd = n0 * 2.0 ** l2r; B = BMAX if Bd > BMAX else int(Bd)
    Bmin = max(2 * (J + 1), 32)
    while B > Bmin and B - 1 >= 2 * J:
        l2 = math.log2(J + 1) + (math.lgamma(B) - math.lgamma(J + 1.0) - math.lgamma(B - J)) / math.log(2.0)
        if l2 - 257.0 <= -80.0: break
        B = (B * 3) // 4
    return B

def budget(E, H, Delta, K):
    T = 10 ** E; tau = T / (2 * math.pi); N = int(math.isqrt(int((T + H) // 1) * 10 ** 6 // int(2 * math.pi * 10 ** 6)))  # floor sqrt((T+H)/2pi), integer arithmetic
    N = math.isqrt(int((T + H) / (2 * math.pi)))
    bits = T.bit_length(); wp = 330 + bits + 4
    log2tau = math.log2(tau)
    # n_head: first n where choose_B >= max(2(J+1), 32) = 32
    nhead = 1
    while choose_B(nhead, log2tau) < 32: nhead *= 2
    lo = nhead // 2; hi = nhead
    while hi - lo > 1:
        m = (lo + hi) // 2
        if choose_B(m, log2tau) >= 32: hi = m
        else: lo = m
    nhead = hi
    # phase bound E_ph per block ~ 2^-64 + 2^-72 (interp) + 2^-80 (propagation) ; the code's actual per-block max at 1e23 was 5.8e-19
    Eph = 2.0 ** -64 + 2.0 ** -72 + 2.0 ** -80
    trig = 7 * Eph + EC
    # per-term bound for moment k (Lemma M2 + summation), weight Z: m_w = n^-1/2, e_w = 2.01 u m_w, e_x ~ u X (small; counted as 0.01 X u)
    ng = math.ceil(BMAX / 16.0); gam15 = 15 * u / (1 - 15 * u)
    def c_k(k, X):
        return (trig * X ** k + k * X ** (k - 1) * (0.01 * u * X if k > 0 else 0) + (k + 1) * u * 1.0001 * (1 + EC) * X ** k) + 2.01 * u * X ** k \
               + (gam15 + 2 * ng * ng * u * u) * (1 + EC) * (1 + (k + 3) * u) * X ** k
    # sum over terms of m_w = sum n^-1/2 over n <= N  ~ 2 sqrt(N)
    S = 2 * math.sqrt(N)
    X = Delta / 2 * 1.0001
    # point evaluation: |Z| radius ~ 2 * sum_b sum_k |h|^k/k! rad(M_bk) <= 2 * S * sum_k H^k/k! c_k(X)  (worst point h = H)
    rad = 2 * S * sum(H ** k / math.factorial(k) * c_k(k, X) for k in range(K + 1))
    taylor = 2 * S * (H * X) ** (K + 1) / math.factorial(K + 1) * math.exp(H * X)
    # RS remainder (FLINT zeta_rs_bound, sigma = 1/2): max(1/2, 2^((3*1+1)/2)/7) (1.1 sqrt(2pi/t))^(K+1) floor(K/2)!
    rs = {k: max(0.5, 2 ** 2 / 7) * (1.1 * math.sqrt(2 * math.pi / T)) ** (k + 1) * math.factorial(k // 2) for k in (2, 4, 6)}
    theta = T / 2 * math.log(T / (2 * math.pi)) - T / 2  # leading term
    nwin_err = 2.0 ** (math.log2(theta) - (256 + bits))
    return dict(E=E, H=H, Delta=Delta, K=K, N=N, N_lt_2p52=N < 2 ** 52, n_exact_binary64=N < 2 ** 53, bitlen_T0=bits, wp=wp, log2tau=round(log2tau, 2),
                n_head=nhead, B_at_1e6=choose_B(10 ** 6, log2tau), B_at_1e8=choose_B(10 ** 8, log2tau), blocks_approx=int(N / BMAX),
                sum_weights_2sqrtN=S, per_term_k0=c_k(0, X), Z_radius_apriori=rad, taylor_remainder=taylor, rs_remainder_bound=rs,
                nwin_enclosure_err=nwin_err, hX=H * X)

for E in map(int, sys.argv[1:]):
    for (H, D, K, name) in ((4.0, 0.15, 18, 'production H=4'), (61.0, 0.012, 18, 'scan H=61')):
        b = budget(E, H, D, K); b['session'] = name
        print(json.dumps(b))
