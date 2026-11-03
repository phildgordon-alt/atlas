/* zfast.c -- rigorous Z(t) = 2 sum_{n<=N} n^{-1/2} cos(theta - t log n) + 2 Re(e^{i theta} corr(t)) at exact t = T0 + u.
   THEORY_ZFAST.md is the specification; section numbers below refer to it.

   Trust split (section 2):
     * Arb (FLINT 3.6.0): theta(t), tau = t/2pi, the phase nodes tau*log(n0+m) of each block, the head terms n < n_head,
       the Riemann-Siegel correction and its remainder bound (Arias de Reyna Thm 4.2, acb_dirichlet_zeta_rs_bound).
     * This file: the fast part sum_{n_head <= n <= N} n^{-1/2} cos(2 pi (Theta - tau log n)), evaluated with
         - exact 256-bit fixed-point (mod 1) forward differences of the phase (section 4),
         - the cos/sin kernel of section 5 (bound E_c from tools/sincos_bound.py),
         - IEEE sqrt/division weights, grouped + TwoSum summation (section 6),
       and an a-priori bound accumulated per block in mag_t (upward-rounded) arithmetic.
   Compile with -ffp-contract=off. */
#include <math.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <flint/acb_dirichlet.h>
#include <flint/arb_hypgeom.h>
#include "zfast.h"

#if defined(__FP_FAST_FMA) && 0
#endif

static double now(void) { struct timespec a; clock_gettime(CLOCK_MONOTONIC, &a); return a.tv_sec + 1e-9 * a.tv_nsec; }

/* ---------------- section 5: cos(2 pi v / 2^64) ----------------
   coefficients: binary64 roundings of (-1)^j/(2j)! and (-1)^j/(2j+1)!, exactly as tools/sincos_bound.py (hex literals) */
static const double CC[9] = { 0x1.0000000000000p+0, -0x1.0000000000000p-1, 0x1.5555555555555p-5, -0x1.6c16c16c16c17p-10,
    0x1.a01a01a01a01ap-16, -0x1.27e4fb7789f5cp-22, 0x1.1eed8eff8d898p-29, -0x1.93974a8c07c9dp-37, 0x1.ae7f3e733b81fp-45 };
static const double SC[9] = { 0x1.0000000000000p+0, -0x1.5555555555555p-3, 0x1.1111111111111p-7, -0x1.a01a01a01a01ap-13,
    0x1.71de3a556c734p-19, -0x1.ae64567f544e4p-26, 0x1.6124613a86d09p-33, -0x1.ae7f3e733b81fp-41, 0x1.952c77030ad4ap-49 };
static const double KTURN = 0x1.921fb54442d18p-62;     /* fl(2 pi / 2^64) */
/* E_c: |computed - exact| for cos and sin, for every input v (tools/sincos_bound.py: 4.8731e-16; rounded up) */
#define ZF_EC 4.88e-16

static inline void cs_core(double *cy, double *sy, uint64_t v, uint64_t *qq)
{
    uint64_t q = (v + (UINT64_C(1) << 61)) >> 62;
    int64_t r = (int64_t)(v - (q << 62));
    double y = (double)r * KTURN;
    double z = y * y;
    double p = CC[8];
    p = fma(p, z, CC[7]); p = fma(p, z, CC[6]); p = fma(p, z, CC[5]); p = fma(p, z, CC[4]);
    p = fma(p, z, CC[3]); p = fma(p, z, CC[2]); p = fma(p, z, CC[1]);
    double c = fma(p, z, 1.0);
    double s2 = SC[8];
    s2 = fma(s2, z, SC[7]); s2 = fma(s2, z, SC[6]); s2 = fma(s2, z, SC[5]); s2 = fma(s2, z, SC[4]);
    s2 = fma(s2, z, SC[3]); s2 = fma(s2, z, SC[2]); s2 = fma(s2, z, SC[1]);
    double t = y * z;
    double s = fma(t, s2, y);
    *cy = c; *sy = s; *qq = q & 3;
}

/* cos and sin of 2 pi v/2^64 (exact quadrant symmetries) */
void zf_cos2pi(double *c, double *s, uint64_t v)
{
    double cy, sy; uint64_t q;
    cs_core(&cy, &sy, v, &q);
    /* 2 pi x = q pi/2 + y */
    switch (q) {
        case 0: *c = cy;  *s = sy;  break;
        case 1: *c = -sy; *s = cy;  break;
        case 2: *c = -cy; *s = -sy; break;
        default: *c = sy; *s = -cy; break;
    }
}

static inline double cos2pi_only(uint64_t v)
{
    double cy, sy; uint64_t q;
    cs_core(&cy, &sy, v, &q);
    double r = (q & 1) ? sy : cy;
    return ((q + 1) & 2) ? -r : r;          /* q = 1, 2 negative */
}

/* ---------------- section 4: 256-bit fixed point mod 1 ---------------- */
#define JMAX 32
typedef struct { uint64_t w[4]; } fx;

static inline void fx_add(fx *a, const fx *b)
{
    unsigned __int128 s = (unsigned __int128)a->w[0] + b->w[0];
    a->w[0] = (uint64_t)s;
    s = (s >> 64) + (unsigned __int128)a->w[1] + b->w[1];
    a->w[1] = (uint64_t)s;
    s = (s >> 64) + (unsigned __int128)a->w[2] + b->w[2];
    a->w[2] = (uint64_t)s;
    a->w[3] = a->w[3] + b->w[3] + (uint64_t)(s >> 64);
}

/* fx = round(mid(x) 2^256) mod 2^256 ; err (turns) += rad(x) + 2^-257 */
static void fx_from_arb(fx *r, mag_t err, const arb_t x)
{
    arf_t m; fmpz_t z; ulong limbs[4];
    arf_init(m); fmpz_init(z);
    arf_mul_2exp_si(m, arb_midref(x), 256);
    arf_get_fmpz(z, m, ARF_RND_NEAR);
    fmpz_fdiv_r_2exp(z, z, 256);
    memset(limbs, 0, sizeof limbs);
    fmpz_get_ui_array(limbs, 4, z);
    for (int i = 0; i < 4; i++) r->w[i] = limbs[i];
    mag_set(err, arb_radref(x));
    mag_add_ui_2exp_si(err, err, 1, -257);
    arf_clear(m); fmpz_clear(z);
}

/* ---------------- parameters ---------------- */
void zf_params_default(zf_params *P)
{
    P->J = 12; P->bmax = 1L << 14; P->log2_interp = -72.0; P->kcorr = 0; P->verbose = 0;
}
void zf_stats_init(zf_stats *S) { memset(S, 0, sizeof *S); fmpz_init(S->N); }
void zf_stats_clear(zf_stats *S) { fmpz_clear(S->N); }

void zf_height(arb_t t, const fmpz_t T0, double u)
{
    arb_t a;
    arb_init(a);
    arb_set_fmpz(t, T0);
    arb_set_d(a, u);
    arb_add(t, t, a, ARF_PREC_EXACT);
    if (!arb_is_exact(t)) { fprintf(stderr, "zf_height: not exact\n"); abort(); }
    arb_clear(a);
}

/* ---------------- section 3: the RS correction (adapted from FLINT 3 acb_dirichlet_zeta_rs_r, LGPL, F. Johansson) ----
   res = (-1)^{N-1} U a^{-sigma} ( sum_{k=0}^{K} C_k(p)/a^k  +/- RS_K ),  RS_K bound = acb_dirichlet_zeta_rs_bound (Arias de Reyna
   Thm 4.2).  N = floor(a), a = sqrt(t/2pi), p = 1 - 2(a - N), U = exp(-i((t/2) log(t/2pi) - t/2 - pi/8)).  Requires t > 0, K >= 2.
   This is the R(s) - sum_{n<=N} n^{-s} of Arb's acb_dirichlet_zeta_rs_r, line by line. */
void zf_rs_corr(acb_t res, const acb_t s, slong K, slong prec, fmpz_t N, mag_t err)
{
    arb_ptr dk, pipow;
    acb_ptr Fp;
    arb_t a, p, api2, api2pow;
    acb_t U, S, u, v;
    slong j, k, wp;

    acb_dirichlet_zeta_rs_bound(err, s, K);
    if (!mag_is_finite(err) || K < 2) { acb_indeterminate(res); return; }

    arb_init(a); arb_init(p); arb_init(api2); arb_init(api2pow);
    acb_init(U); acb_init(S); acb_init(u); acb_init(v);
    dk = _arb_vec_init((3 * K) / 2 + 2);
    Fp = _acb_vec_init(3 * K + 1);
    pipow = _arb_vec_init((3 * K) / 2 + 2);

    for (wp = 2 * prec; ; wp *= 2)
    {
        arb_const_pi(a, wp); arb_mul_2exp_si(a, a, 1);
        arb_div(a, acb_imagref(s), a, wp);
        arb_sqrt(a, a, wp);
        arb_floor(p, a, wp);
        if (!arb_get_unique_fmpz(N, p))
        {
            if (wp > 64 * prec) { acb_indeterminate(res); goto cleanup; }
            continue;
        }
        arb_sub_fmpz(p, a, N, wp);
        arb_neg(p, p);
        arb_mul_2exp_si(p, p, 1);
        arb_add_ui(p, p, 1, wp);
        acb_dirichlet_zeta_rs_f_coeffs(Fp, p, 3 * K + 1, wp);
        if (acb_rel_accuracy_bits(Fp + 3 * K) >= prec) break;
        if (wp > 64 * prec) break;
    }

    wp = prec + 10 + 3 * fmpz_bits(N);
    wp = FLINT_MAX(wp, prec + 10);
    wp = wp + FLINT_BIT_COUNT(K);

    acb_zero(S);
    arb_const_pi(api2, wp);
    _arb_vec_set_powers(pipow, api2, (3 * K) / 2 + 2, wp);
    arb_mul(api2, api2, api2, wp);
    arb_mul(api2, api2, a, wp);
    arb_inv(api2, api2, wp);
    arb_one(api2pow);

    for (k = 0; k <= K; k++)
    {
        acb_dirichlet_zeta_rs_d_coeffs(dk, acb_realref(s), k, wp);
        acb_zero(u);
        for (j = 0; j <= (3 * k) / 2; j++)
        {
            arb_mul(acb_realref(v), pipow + j, dk + j, wp);
            arb_mul_2exp_si(acb_realref(v), acb_realref(v), -j);
            arb_zero(acb_imagref(v));
            if (j % 4 == 1) acb_div_onei(v, v);
            else if (j % 4 == 2) acb_neg(v, v);
            else if (j % 4 == 3) acb_mul_onei(v, v);
            acb_addmul(u, v, Fp + 3 * k - 2 * j, wp);
        }
        acb_addmul_arb(S, u, api2pow, wp);
        arb_mul(api2pow, api2pow, api2, wp);
    }
    acb_add_error_mag(S, err);

    arb_log(acb_realref(u), a, wp);
    arb_mul_2exp_si(acb_realref(u), acb_realref(u), 1);
    arb_sub_ui(acb_realref(u), acb_realref(u), 1, wp);
    arb_mul(acb_realref(u), acb_realref(u), acb_imagref(s), wp);
    arb_mul_2exp_si(acb_realref(u), acb_realref(u), -1);
    arb_const_pi(acb_imagref(u), wp);
    arb_mul_2exp_si(acb_imagref(u), acb_imagref(u), -3);
    arb_sub(acb_realref(u), acb_realref(u), acb_imagref(u), wp);
    arb_neg(acb_realref(u), acb_realref(u));
    arb_sin_cos(acb_imagref(U), acb_realref(U), acb_realref(u), wp);

    acb_mul(S, S, U, wp);
    arb_neg(acb_realref(u), acb_realref(s));
    arb_pow(acb_realref(u), a, acb_realref(u), wp);
    acb_mul_arb(S, S, acb_realref(u), wp);
    if (fmpz_is_even(N)) acb_neg(S, S);
    acb_set(res, S);

cleanup:
    _arb_vec_clear(dk, (3 * K) / 2 + 2);
    _acb_vec_clear(Fp, 3 * K + 1);
    _arb_vec_clear(pipow, (3 * K) / 2 + 2);
    arb_clear(a); arb_clear(p); arb_clear(api2); arb_clear(api2pow);
    acb_clear(U); acb_clear(S); acb_clear(u); acb_clear(v);
}

/* ---------------- section 4/6: one block ----------------
   E[0] = Theta - tau log n0 (mod 1), E[i] = -Delta^i (tau log n)(n0) (mod 1); after k steps E[0] = Theta - p(k) (mod 1).
   Returns the block sum as hi + lo (exact relation documented in section 6). */
static void block_kernel_Z(double *hi_out, double *lo_out, fx *E, int J, long n0, long B)
{
    double hi = 0.0, lo = 0.0, g = 0.0;
    long k = 0;
    while (k < B)
    {
        long kend = k + 16 < B ? k + 16 : B;
        g = 0.0;
        for (; k < kend; k++)
        {
            double c = cos2pi_only(E[0].w[3]);
            double w = 1.0 / sqrt((double)(n0 + k));
            g = g + w * c;
            for (int i = 0; i < J; i++) fx_add(&E[i], &E[i + 1]);
        }
        /* TwoSum(hi, g) */
        double sh = hi + g;
        double bb = sh - hi;
        double e = (hi - (sh - bb)) + (g - bb);
        hi = sh;
        lo = lo + e;
    }
    *hi_out = hi; *lo_out = lo;
}

/* specialised J = 12 (unrolled by the compiler) */
static void block_kernel_Z12(double *hi_out, double *lo_out, fx *E, long n0, long B)
{
    fx e[13];
    memcpy(e, E, sizeof e);
    double hi = 0.0, lo = 0.0, g;
    long k = 0;
    while (k < B)
    {
        long kend = k + 16 < B ? k + 16 : B;
        g = 0.0;
        for (; k < kend; k++)
        {
            double c = cos2pi_only(e[0].w[3]);
            double w = 1.0 / sqrt((double)(n0 + k));
            g = g + w * c;
            fx_add(&e[0], &e[1]); fx_add(&e[1], &e[2]); fx_add(&e[2], &e[3]); fx_add(&e[3], &e[4]);
            fx_add(&e[4], &e[5]); fx_add(&e[5], &e[6]); fx_add(&e[6], &e[7]); fx_add(&e[7], &e[8]);
            fx_add(&e[8], &e[9]); fx_add(&e[9], &e[10]); fx_add(&e[10], &e[11]); fx_add(&e[11], &e[12]);
        }
        double sh = hi + g;
        double bb = sh - hi;
        double ee = (hi - (sh - bb)) + (g - bb);
        hi = sh;
        lo = lo + ee;
    }
    memcpy(E, e, sizeof e);
    *hi_out = hi; *lo_out = lo;
}

/* choose the block length at n0 (heuristic only: the bound actually used is computed rigorously afterwards) */
static long choose_B(long n0, int J, double log2tau, const zf_params *P, long nmax)
{
    double l2r = (P->log2_interp + log2((double)(J + 1)) - log2tau) / (J + 1);
    double Bd = (double)n0 * pow(2.0, l2r);
    long B = Bd > (double)P->bmax ? P->bmax : (long)Bd;
    long Bmin = 2 * (J + 1) > 32 ? 2 * (J + 1) : 32;
    /* absorb a short tail into this block (the bound used is computed for the actual B) */
    if (B > nmax - n0 + 1 || nmax - n0 + 1 - B < Bmin) B = nmax - n0 + 1;
    return B;
}

/* section 5: E[0] = fx(Theta - tau log n0), E[i] = fx(-Delta^i tau log(n0)); err = E_ph (turns) for block length B */
static void block_setup(fx *E, mag_t err, arb_struct *L, mag_struct *epsi, arb_t x, mag_t tmp, mag_t tmp2,
                        const arb_t Theta, const arb_t tau, ulong n, long B, int J, slong wp)
{
    /* nodes L[m] = tau log(n+m), m = 0..J; forward differences in place: L[i] := Delta^i L(0) */
    for (int m = 0; m <= J; m++) { arb_log_ui(L[m], n + m, wp); arb_mul(L[m], L[m], tau, wp); }
    for (int i = 1; i <= J; i++)
        for (int m = J; m >= i; m--) arb_sub(L[m], L[m], L[m - 1], wp);
    /* E[0] = Theta - L[0], E[i] = -L[i] */
    arb_sub(x, Theta, L[0], wp);
    fx_from_arb(&E[0], epsi[0], x);
    for (int i = 1; i <= J; i++) { arb_neg(x, L[i]); fx_from_arb(&E[i], epsi[i], x); }
    /* phase error bound (turns), section 4:  sum_i C(B-1,i) eps_i  +  tau (B-1)^{J+1} / ((J+1) n^{J+1})  +  2^-64 */
    mag_zero(err);
    for (int i = 0; i <= J; i++) { mag_bin_uiui(tmp, (ulong)(B - 1), (ulong)i); mag_mul(tmp, tmp, epsi[i]); mag_add(err, err, tmp); }
    arb_get_mag(tmp, tau);
    mag_set_ui(tmp2, (ulong)(B - 1)); mag_pow_ui(tmp2, tmp2, J + 1); mag_mul(tmp, tmp, tmp2);
    mag_set_ui_lower(tmp2, n); mag_pow_ui_lower(tmp2, tmp2, J + 1); mag_mul_ui_lower(tmp2, tmp2, J + 1);
    mag_div(tmp, tmp, tmp2);
    mag_add(err, err, tmp);
    mag_add_ui_2exp_si(err, err, 1, -64);
}

/* the main sum: res = sum_{n=1}^{N} n^{-1/2} cos(2 pi (Theta - tau log n)), rigorous ball */
static void main_sum_Z(arb_t res, const arb_t Theta, const arb_t tau, ulong N, slong wp, const zf_params *P, zf_stats *S)
{
    int J = P->J;
    double log2tau = arf_get_d(arb_midref(tau), ARF_RND_UP);
    log2tau = log2(log2tau);
    long Bmin = 2 * (J + 1) > 32 ? 2 * (J + 1) : 32;
    arb_t x, acc, L[JMAX + 1];
    mag_t err, e1, tot, tmp, tmp2, epsi[JMAX + 1];
    fx E[JMAX + 1];
    arb_init(x); arb_init(acc);
    mag_init(err); mag_init(e1); mag_init(tot); mag_init(tmp); mag_init(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }

    /* head: n < n_head, directly in Arb */
    double t0 = now();
    ulong n = 1;
    arb_zero(acc);
    while (n <= N)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)N);
        if (B >= Bmin || (B >= J + 1 && (long)(N - n + 1) == B)) break;
        arb_log_ui(x, n, wp);
        arb_mul(x, x, tau, wp);
        arb_sub(x, Theta, x, wp);
        arb_mul_2exp_si(x, x, 1);
        arb_cos_pi(x, x, wp);
        arb_t r; arb_init(r);
        arb_set_ui(r, n); arb_rsqrt(r, r, wp);
        arb_addmul(acc, x, r, wp);
        arb_clear(r);
        n++;
    }
    S->head_terms = (double)(n - 1);
    S->sec_head = now() - t0;

    /* fast blocks */
    t0 = now();
    mag_zero(tot);
    double maxph = 0.0, nblocks = 0;
    const double u = 0x1p-53;
    while (n <= N)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)N);
        if (B < J + 1) { fprintf(stderr, "block too short at n=%lu\n", n); abort(); }
        block_setup(E, err, L, epsi, x, tmp, tmp2, Theta, tau, n, B, J, wp);
        double ph = mag_get_d(err);
        if (ph > maxph) maxph = ph;
        /* per-term coefficient (section 6): 3.03u + E_c + 2pi E_ph ; times sum w* <= B / sqrt(n) */
        mag_mul_ui(e1, err, 7);                       /* 2 pi < 7 (loose) */
        mag_set_d(tmp, 3.03 * u + ZF_EC);
        mag_add(e1, e1, tmp);
        /* summation: groups of <= 16 sequential adds: gamma_15 * sum|t| ; sum|t| <= (1 + E_c)(1 + 3.1u) B/sqrt(n);
           TwoSum lo-accumulation rounding <= ngroups^2 u^2 sum|t| */
        double ng = ceil((double)B / 16.0);
        mag_set_d(tmp, 15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.1 * u) + ng * ng * u * u * 2.0);
        mag_add(e1, e1, tmp);
        mag_set_ui(tmp, (ulong)B);
        mag_set_ui_lower(tmp2, n); mag_rsqrt(tmp2, tmp2);   /* upper bound of 1/sqrt(n) */
        mag_mul(tmp, tmp, tmp2);
        mag_mul(e1, e1, tmp);
        mag_add(tot, tot, e1);
        /* run */
        double hi, lo;
        if (J == 12) block_kernel_Z12(&hi, &lo, E, (long)n, B);
        else block_kernel_Z(&hi, &lo, E, J, (long)n, B);
        arb_set_d(x, hi); arb_add(acc, acc, x, wp);
        arb_set_d(x, lo); arb_add(acc, acc, x, wp);
        n += (ulong)B;
        nblocks++;
    }
    S->sec_fast = now() - t0;
    S->blocks = nblocks;
    S->terms_fast = (double)N - S->head_terms;
    S->max_phase_err = maxph;
    S->sum_err_fast = mag_get_d(tot);
    arb_add_error_mag(acc, tot);
    arb_set(res, acc);

    arb_clear(x); arb_clear(acc);
    mag_clear(err); mag_clear(e1); mag_clear(tot); mag_clear(tmp); mag_clear(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
}

void zf_Z(arb_t res, const fmpz_t T0, double u, const zf_params *P, zf_stats *S)
{
    double t0 = now(), t1;
    slong bits = fmpz_bits(T0) + 4;
    slong wp = 330 + bits;                 /* nodes/phases: absolute 2^-260 at |tau log n| < 2^(bits+3) */
    arb_t t, tau, Theta, pi2, ms;
    acb_t s, th, corr, eith;
    mag_t rsb;
    arb_init(t); arb_init(tau); arb_init(Theta); arb_init(pi2); arb_init(ms);
    acb_init(s); acb_init(th); acb_init(corr); acb_init(eith);
    mag_init(rsb);

    if (P->J < 2 || P->J > JMAX) { fprintf(stderr, "J out of range\n"); abort(); }
    zf_height(t, T0, u);
    if (!(arf_cmp_si(arb_midref(t), 1000) > 0)) { fprintf(stderr, "t too small\n"); abort(); }
    arb_const_pi(pi2, wp); arb_mul_2exp_si(pi2, pi2, 1);
    arb_div(tau, t, pi2, wp);
    /* theta(t) (Arb) and Theta = theta/2pi */
    acb_set_arb(s, t);
    acb_dirichlet_hardy_theta(th, s, NULL, NULL, 1, wp);
    arb_div(Theta, acb_realref(th), pi2, wp);

    /* RS correction at s = 1/2 + it */
    arb_set_d(acb_realref(s), 0.5);
    arb_set(acb_imagref(s), t);
    slong K = P->kcorr;
    if (K <= 0)
    {
        /* smallest K >= 2 with Thm 4.2 bound < 2^-100 (or K = 40) */
        for (K = 2; K < 40; K++) { acb_dirichlet_zeta_rs_bound(rsb, s, K); if (mag_cmp_2exp_si(rsb, -100) < 0) break; }
    }
    zf_rs_corr(corr, s, K, 128, S->N, rsb);
    S->K = K;
    S->rs_bound = mag_get_d(rsb);
    /* e^{i theta} corr, real part, times 2 */
    arb_sin_cos(acb_imagref(eith), acb_realref(eith), acb_realref(th), wp);
    acb_mul(corr, corr, eith, wp);
    S->corr_rad = mag_get_d(arb_radref(acb_realref(corr)));
    t1 = now(); S->sec_setup = t1 - t0;

    if (!fmpz_abs_fits_ui(S->N)) { fprintf(stderr, "N too large\n"); abort(); }
    ulong N = fmpz_get_ui(S->N);
    if (N >= (UINT64_C(1) << 52)) { fprintf(stderr, "N >= 2^52\n"); abort(); }
    main_sum_Z(ms, Theta, tau, N, wp, P, S);

    arb_mul_2exp_si(ms, ms, 1);
    arb_mul_2exp_si(acb_realref(corr), acb_realref(corr), 1);
    arb_add(res, ms, acb_realref(corr), wp);
    S->sec_total = now() - t0;

    arb_clear(t); arb_clear(tau); arb_clear(Theta); arb_clear(pi2); arb_clear(ms);
    acb_clear(s); acb_clear(th); acb_clear(corr); acb_clear(eith);
    mag_clear(rsb);
}

/* phase test hook (THEORY section 11.2): runs the production block setup and iteration at (T0+u, n0, B, J) and compares the top
   limb with Arb's (Theta - tau log(n0+k)) mod 1 at every k.  maxerr: observed max (turns), bound: E_ph. */
void zf_phase_test(double *maxerr, double *bound, const fmpz_t T0, double u, ulong n0, long B, int J)
{
    slong wp = 330 + fmpz_bits(T0) + 4;
    arb_t t, tau, Theta, pi2, x, ref, L[JMAX + 1];
    acb_t s, th;
    mag_t err, tmp, tmp2, epsi[JMAX + 1];
    fx E[JMAX + 1];
    arb_init(t); arb_init(tau); arb_init(Theta); arb_init(pi2); arb_init(x); arb_init(ref);
    acb_init(s); acb_init(th); mag_init(err); mag_init(tmp); mag_init(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }
    zf_height(t, T0, u);
    arb_const_pi(pi2, wp); arb_mul_2exp_si(pi2, pi2, 1);
    arb_div(tau, t, pi2, wp);
    acb_set_arb(s, t);
    acb_dirichlet_hardy_theta(th, s, NULL, NULL, 1, wp);
    arb_div(Theta, acb_realref(th), pi2, wp);
    block_setup(E, err, L, epsi, x, tmp, tmp2, Theta, tau, n0, B, J, wp);
    *bound = mag_get_d(err);
    double mx = 0.0;
    for (long k = 0; k < B; k++)
    {
        /* ref = (Theta - tau log(n0+k)) - v/2^64, reduced to [-1/2, 1/2] */
        arb_log_ui(ref, n0 + k, wp); arb_mul(ref, ref, tau, wp); arb_sub(ref, Theta, ref, wp);
        arb_set_ui(x, E[0].w[3]); arb_mul_2exp_si(x, x, -64);
        arb_sub(ref, ref, x, wp);
        arb_set_round(x, ref, wp);
        arf_t f; arf_init(f); arf_set_round(f, arb_midref(ref), 64, ARF_RND_NEAR);
        double d = arf_get_d(f, ARF_RND_NEAR); arf_clear(f);
        d = d - nearbyint(d);
        /* refine: error = |ref - round(ref)|; computed in Arb */
        arb_set_d(x, nearbyint(arf_get_d(arb_midref(ref), ARF_RND_NEAR)));
        arb_sub(x, ref, x, wp);
        double e = mag_get_d(arb_radref(x)) + fabs(arf_get_d(arb_midref(x), ARF_RND_UP));
        if (e > mx) mx = e;
        for (int i = 0; i < J; i++) fx_add(&E[i], &E[i + 1]);
    }
    *maxerr = mx;
    arb_clear(t); arb_clear(tau); arb_clear(Theta); arb_clear(pi2); arb_clear(x); arb_clear(ref);
    acb_clear(s); acb_clear(th); mag_clear(err); mag_clear(tmp); mag_clear(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
}
