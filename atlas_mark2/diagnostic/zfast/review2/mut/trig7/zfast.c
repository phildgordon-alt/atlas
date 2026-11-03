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
#include <pthread.h>
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
    P->J = 12; P->bmax = 1L << 14; P->log2_interp = -72.0; P->kcorr = 0; P->verbose = 0; P->threads = 1;
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
        if (!acb_is_exact(s)) break;          /* ball input (rows: sup bound over a disc): any enclosure is valid */
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
    /* v9 cap: the rounding-propagation term sum_{i<=J} C(B-1,i) 2^-257 must stay <= 2^-80 (heuristic estimate
       log2((J+1) C(B-1,J)); the bound actually used is still computed rigorously in block_setup) */
    while (B > Bmin && B - 1 >= 2 * J)
    {
        double l2 = log2((double)(J + 1)) + (lgamma((double)B) - lgamma((double)J + 1.0) - lgamma((double)(B - J))) / log(2.0);
        if (l2 - 257.0 <= -80.0) break;
        B = (B * 3) / 4;
    }
    /* absorb a short tail into this block (the bound used is computed for the actual B) */
    if (B > nmax - n0 + 1 || nmax - n0 + 1 - B < Bmin) B = nmax - n0 + 1;
    return B;
}

/* section 5: E[0] = fx(Theta - tau log n0), E[i] = fx(-Delta^i tau log(n0)); err = E_ph (turns) for block length B */
static void block_setup(fx *E, mag_t err, arb_t *L, mag_t *epsi, arb_t x, mag_t tmp, mag_t tmp2,
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

typedef struct {
    const arb_struct *Theta, *tau; ulong n0, n1; slong wp; const zf_params *P;
    arb_t acc; mag_t tot; double maxph, nblocks;
} zrange_t;

/* fast blocks over [n0, n1] (n0 beyond the head); acc = sum of block sums, tot = sum of block bounds */
static void *z_range(void *arg)
{
    zrange_t *R = (zrange_t *)arg;
    const zf_params *P = R->P; int J = P->J; slong wp = R->wp;
    double log2tau = log2(arf_get_d(arb_midref(R->tau), ARF_RND_UP));
    arb_t x, L[JMAX + 1]; mag_t err, e1, tmp, tmp2, epsi[JMAX + 1]; fx E[JMAX + 1];
    arb_init(x); mag_init(err); mag_init(e1); mag_init(tmp); mag_init(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }
    arb_zero(R->acc); mag_zero(R->tot);
    double maxph = 0.0, nblocks = 0;
    const double u = 0x1p-53;
    ulong n = R->n0, N = R->n1;
    const arb_struct *Theta = R->Theta, *tau = R->tau;
    while (n <= N)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)N);
        if (B < J + 1) { fprintf(stderr, "block too short at n=%lu\n", n); abort(); }
        block_setup(E, err, L, epsi, x, tmp, tmp2, Theta, tau, n, B, J, wp);
        double ph = mag_get_d(err);
        if (ph > maxph) maxph = ph;
        mag_mul_ui(e1, err, 7); mag_div_ui(e1, e1, 10);
        mag_set_d(tmp, 3.03 * u + ZF_EC);
        mag_add(e1, e1, tmp);
        double ng = ceil((double)B / 16.0);
        mag_set_d(tmp, 15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.1 * u) + ng * ng * u * u * 2.0);
        mag_add(e1, e1, tmp);
        mag_set_ui(tmp, (ulong)B);
        mag_set_ui_lower(tmp2, n); mag_rsqrt(tmp2, tmp2);
        mag_mul(tmp, tmp, tmp2);
        mag_mul(e1, e1, tmp);
        mag_add(R->tot, R->tot, e1);
        double hi, lo;
        if (J == 12) block_kernel_Z12(&hi, &lo, E, (long)n, B);
        else block_kernel_Z(&hi, &lo, E, J, (long)n, B);
        arb_set_d(x, hi); arb_add(R->acc, R->acc, x, wp);
        arb_set_d(x, lo); arb_add(R->acc, R->acc, x, wp);
        n += (ulong)B;
        nblocks++;
    }
    R->maxph = maxph; R->nblocks = nblocks;
    arb_clear(x); mag_clear(err); mag_clear(e1); mag_clear(tmp); mag_clear(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
    flint_cleanup();
    return NULL;
}

/* split [n0, N] into T contiguous ranges (each >= 4 bmax long) and run them */
static int split_ranges(ulong *lo, ulong *hi, ulong n0, ulong N, int T, long bmax)
{
    if (T < 1) T = 1;
    if (T > 16) T = 16;
    ulong len = N - n0 + 1;
    while (T > 1 && len / (ulong)T < (ulong)(4 * bmax)) T--;
    for (int i = 0; i < T; i++)
    {
        lo[i] = n0 + (len * (ulong)i) / (ulong)T;
        hi[i] = n0 + (len * (ulong)(i + 1)) / (ulong)T - 1;
    }
    return T;
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

    /* fast blocks (v9: T contiguous ranges, run in threads; each range is summed and bounded independently) */
    t0 = now();
    mag_zero(tot);
    double maxph = 0.0, nblocks = 0;
    if (n <= N)
    {
        ulong lo[16], hi[16];
        int T = split_ranges(lo, hi, n, N, P->threads, P->bmax);
        zrange_t R[16]; pthread_t th[16];
        for (int i = 0; i < T; i++)
        {
            R[i].Theta = Theta; R[i].tau = tau; R[i].n0 = lo[i]; R[i].n1 = hi[i]; R[i].wp = wp; R[i].P = P;
            arb_init(R[i].acc); mag_init(R[i].tot);
        }
        if (T == 1) z_range(&R[0]);
        else
        {
            for (int i = 0; i < T; i++) if (pthread_create(&th[i], NULL, z_range, &R[i])) { fprintf(stderr, "pthread_create\n"); abort(); }
            for (int i = 0; i < T; i++) pthread_join(th[i], NULL);
        }
        for (int i = 0; i < T; i++)
        {
            arb_add(acc, acc, R[i].acc, wp); mag_add(tot, tot, R[i].tot);
            if (R[i].maxph > maxph) maxph = R[i].maxph;
            nblocks += R[i].nblocks;
            arb_clear(R[i].acc); mag_clear(R[i].tot);
        }
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
        {   /* exact reduction: x = ref - nearest integer to mid(ref) (fmpz, no double rounding) */
            fmpz_t zi; fmpz_init(zi);
            arf_get_fmpz(zi, arb_midref(ref), ARF_RND_NEAR);
            arb_sub_fmpz(x, ref, zi, wp);
            fmpz_clear(zi);
        }
        double e = mag_get_d(arb_radref(x)) + fabs(arf_get_d(arb_midref(x), ARF_RND_UP));
        if (e > mx) mx = e;
        for (int i = 0; i < J; i++) fx_add(&E[i], &E[i + 1]);
    }
    *maxerr = mx;
    arb_clear(t); arb_clear(tau); arb_clear(Theta); arb_clear(pi2); arb_clear(x); arb_clear(ref);
    acb_clear(s); acb_clear(th); mag_clear(err); mag_clear(tmp); mag_clear(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
}

/* ======================= section 10: rows, zeta(s) and zeta'(s) at s = sigma + it ======================= */
#define RDEG 6      /* weight polynomial degree */

/* Taylor data of a weight at centre c (Arb), rounded to binary64, with: e = |p_hat(x) - f(c + x)| bound for |x| <= X (excluding
   nothing: remainder + coefficient rounding + Horner rounding), mx = bound on |p_hat(x)| and |f(c+x)|. kind 0: z^{-sigma},
   1: z^{sigma-1}, 2: log z. */
static void weight_poly(double *co, mag_t e, mag_t mx, int kind, const arb_t c, const arb_t sigma, double X, slong prec)
{
    arb_t a, q, ex; mag_t M, r, tmp, sumabs, rnd;
    arb_init(a); arb_init(q); arb_init(ex); mag_init(M); mag_init(r); mag_init(tmp); mag_init(sumabs); mag_init(rnd);
    const double u = 0x1p-53;
    /* coefficients a_j */
    if (kind == 0) { arb_neg(ex, sigma); arb_pow(a, c, ex, prec); }
    else if (kind == 1) { arb_sub_ui(ex, sigma, 1, prec); arb_pow(a, c, ex, prec); }
    else arb_log(a, c, prec);
    mag_zero(sumabs); mag_zero(rnd);
    for (int j = 0; j <= RDEG; j++)
    {
        if (j > 0)
        {
            if (kind == 2)
            {   /* l_j = (-1)^{j+1} / (j c^j) */
                arb_pow_ui(q, c, j, prec); arb_mul_ui(q, q, j, prec); arb_inv(a, q, prec);
                if (j % 2 == 0) arb_neg(a, a);
            }
            else
            {   /* a_j = a_{j-1} (ex - j + 1) / (j c) */
                arb_sub_ui(q, ex, j - 1, prec); arb_mul(a, a, q, prec); arb_div_ui(a, a, j, prec); arb_div(a, a, c, prec);
            }
        }
        co[j] = arf_get_d(arb_midref(a), ARF_RND_NEAR);
        /* |co_j - a_j| <= rad + |mid - co_j| */
        arb_t d; arb_init(d); arb_set_d(d, co[j]); arb_sub(d, d, a, prec); arb_get_mag(tmp, d); arb_clear(d);
        mag_set_d(r, X); mag_pow_ui(r, r, j);
        mag_mul(tmp, tmp, r); mag_add(rnd, rnd, tmp);
        mag_set_d(tmp, fabs(co[j])); mag_mul(tmp, tmp, r); mag_add(sumabs, sumabs, tmp);
    }
    /* Taylor remainder (Cauchy on |z - c| <= R = c/2): M (X/R)^{D+1} / (1 - X/R) */
    arb_get_mag_lower(r, c); mag_mul_2exp_si(r, r, -1);                 /* R lower */
    if (kind == 0) { mag_t cl; mag_init(cl); arb_get_mag_lower(cl, c); mag_mul_2exp_si(cl, cl, -1); /* |z| >= c/2 */
        arb_t sl; arb_init(sl); arb_set(sl, sigma); arf_t lo; arf_init(lo); arb_get_lbound_arf(lo, sl, 64);
        /* M = (c/2)^{-sigma_lo} >= |z^{-sigma}| since |z| >= c/2 >= 1 */
        arb_set_arf(ex, lo); arb_neg(ex, ex); arb_set_ui(q, 0); arf_set_mag(arb_midref(q), cl); arb_pow(q, q, ex, prec); arb_get_mag(M, q);
        arf_clear(lo); arb_clear(sl); mag_clear(cl); }
    else if (kind == 1) { /* |z^{sigma-1}| <= (3c/2)^{sigma-1} for sigma >= 1 (|z| <= 3c/2) */
        arb_mul_ui(q, c, 3, prec); arb_mul_2exp_si(q, q, -1); arb_sub_ui(ex, sigma, 1, prec);
        arb_get_ubound_arf(arb_midref(ex), ex, 64); mag_zero(arb_radref(ex));
        arb_pow(q, q, ex, prec); arb_get_mag(M, q); }
    else { /* |log z| <= log(3c/2) + pi/6 */
        arb_mul_ui(q, c, 3, prec); arb_mul_2exp_si(q, q, -1); arb_log(q, q, prec);
        arb_t pp; arb_init(pp); arb_const_pi(pp, prec); arb_div_ui(pp, pp, 6, prec); arb_add(q, q, pp, prec); arb_clear(pp);
        arb_get_mag(M, q); }
    mag_t xr; mag_init(xr); mag_set_d(xr, X); mag_div(xr, xr, r);          /* X/R upper */
    if (mag_cmp_2exp_si(xr, -1) > 0) { mag_inf(e); mag_inf(mx); goto done; }
    mag_pow_ui(tmp, xr, RDEG + 1); mag_mul(tmp, tmp, M);
    mag_one(r); mag_sub_lower(r, r, xr); mag_div(tmp, tmp, r);             /* / (1 - X/R) */
    mag_add(e, tmp, rnd);
    /* Horner (fma) rounding: gamma_{D+1} sum |co_j| X^j */
    mag_set_d(tmp, (RDEG + 1) * u / (1 - (RDEG + 1) * u)); mag_mul(tmp, tmp, sumabs);
    mag_add(e, e, tmp);
    mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);       /* |p_hat| <= sumabs + e, |f| <= |p_hat| + e */
done:
    mag_clear(xr);
    arb_clear(a); arb_clear(q); arb_clear(ex); mag_clear(M); mag_clear(r); mag_clear(tmp); mag_clear(sumabs); mag_clear(rnd);
}

static inline double horner6(const double *c, double x)
{
    double p = c[6];
    p = fma(p, x, c[5]); p = fma(p, x, c[4]); p = fma(p, x, c[3]); p = fma(p, x, c[2]); p = fma(p, x, c[1]); p = fma(p, x, c[0]);
    return p;
}

/* the 8 row sums of one block; acc[2m], acc[2m+1] = hi, lo of sum m:
   0 A c, 1 A s, 2 A l c, 3 A l s, 4 W c, 5 W s, 6 W l c, 7 W l s   (A = n^-sigma, W = n^(sigma-1), l = log n,
   c + i s = e^{-i t log n}) */
static void block_kernel_row(double *acc, fx *E, int J, long B, const double *ca, const double *cw, const double *cl)
{
    double hi[8] = {0}, lo[8] = {0}, g[8];
    double xc = 0.5 * (double)(B - 1);
    long k = 0;
    while (k < B)
    {
        long kend = k + 16 < B ? k + 16 : B;
        for (int m = 0; m < 8; m++) g[m] = 0.0;
        for (; k < kend; k++)
        {
            double c, s; zf_cos2pi(&c, &s, E[0].w[3]);
            double x = (double)k - xc;
            double A = horner6(ca, x), W = horner6(cw, x), l = horner6(cl, x);
            double Al = A * l, Wl = W * l;
            g[0] = g[0] + A * c;  g[1] = g[1] + A * s;  g[2] = g[2] + Al * c; g[3] = g[3] + Al * s;
            g[4] = g[4] + W * c;  g[5] = g[5] + W * s;  g[6] = g[6] + Wl * c; g[7] = g[7] + Wl * s;
            for (int i = 0; i < J; i++) fx_add(&E[i], &E[i + 1]);
        }
        for (int m = 0; m < 8; m++)
        {
            double sh = hi[m] + g[m], bb = sh - hi[m];
            double ee = (hi[m] - (sh - bb)) + (g[m] - bb);
            hi[m] = sh; lo[m] = lo[m] + ee;
        }
    }
    for (int m = 0; m < 8; m++) { acc[2 * m] = hi[m]; acc[2 * m + 1] = lo[m]; }
}

typedef struct {
    const arb_struct *sigma, *tau; ulong n0, n1; slong wp; const zf_params *P;
    arb_t accr[8]; mag_t tot[8]; double maxph, nb;
} rrange_t;

static void *row_range(void *arg)
{
    rrange_t *Rr = (rrange_t *)arg;
    const zf_params *P = Rr->P; int J = P->J; slong wp = Rr->wp;
    const arb_struct *sigma = Rr->sigma, *tau = Rr->tau;
    double log2tau = log2(arf_get_d(arb_midref(tau), ARF_RND_UP));
    arb_t x, zero, c, L[JMAX + 1];
    mag_t err, tmp, tmp2, epsi[JMAX + 1], eA, mA, eW, mW, eL, mL;
    mag_struct *tot = Rr->tot[0]; (void)tot;
    fx E[JMAX + 1];
    arb_init(x); arb_init(zero); arb_init(c);
    mag_init(err); mag_init(tmp); mag_init(tmp2); mag_init(eA); mag_init(mA); mag_init(eW); mag_init(mW); mag_init(eL); mag_init(mL);
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }
    const double u = 0x1p-53;
    double nb = 0, maxph = 0;
    ulong n = Rr->n0, N = Rr->n1;
#define accr (Rr->accr)
#define tot (Rr->tot)
    while (n <= N)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)N);
        if (B < J + 1) { fprintf(stderr, "row block too short\n"); abort(); }
        block_setup(E, err, L, epsi, x, tmp, tmp2, zero, tau, n, B, J, wp);
        double ph = mag_get_d(err); if (ph > maxph) maxph = ph;
        /* weights at centre c = n + (B-1)/2, |x| <= X = (B-1)/2 */
        double X = 0.5 * (double)(B - 1);
        arb_set_ui(c, n); arb_set_d(x, X); arb_add(c, c, x, wp);
        double ca[RDEG + 1], cw[RDEG + 1], cl[RDEG + 1];
        weight_poly(ca, eA, mA, 0, c, sigma, X, wp);
        weight_poly(cw, eW, mW, 1, c, sigma, X, wp);
        weight_poly(cl, eL, mL, 2, c, sigma, X, wp);
        double acc[16];
        block_kernel_row(acc, E, J, B, ca, cw, cl);
        /* bounds per sum (section 10 / 7): weight bounds (max, err) for A, A l, W, W l */
        mag_t wm[4], we[4], trig, sumc, term; for (int m = 0; m < 4; m++) { mag_init(wm[m]); mag_init(we[m]); }
        mag_init(trig); mag_init(sumc); mag_init(term);
        mag_set(wm[0], mA); mag_set(we[0], eA); mag_set(wm[2], mW); mag_set(we[2], eW);
        for (int m = 0; m < 2; m++)
        {   /* product W l (computed fl(W_hat l_hat)): e <= Xmax eL + Lmax eX + u Xmax Lmax ; |W l| (both) <= Xmax Lmax (1 + 2^-50) */
            mag_struct *Xm = (m == 0) ? mA : mW, *Xe = (m == 0) ? eA : eW;
            mag_mul(tmp, Xm, eL); mag_mul(tmp2, mL, Xe); mag_add(tmp, tmp, tmp2);
            mag_mul(tmp2, Xm, mL);
            mag_mul_2exp_si(wm[2 * m + 1], tmp2, -50); mag_add(wm[2 * m + 1], wm[2 * m + 1], tmp2);
            mag_mul_2exp_si(tmp2, tmp2, -53); mag_add(we[2 * m + 1], tmp, tmp2);
        }
        /* trig error: E_c + 2 pi E_ph */
        mag_mul_ui(trig, err, 7); mag_set_d(tmp, ZF_EC); mag_add(trig, trig, tmp);
        double ng = ceil((double)B / 16.0);
        mag_set_d(sumc, 15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.0 * u) + 2.0 * ng * ng * u * u + 1.01 * u);
        for (int m = 0; m < 4; m++)
        {   /* per term: Wmax trig + We + u Wmax (1+Ec) ; summation: sumc Wmax ; times B */
            mag_mul(term, wm[m], trig); mag_add(term, term, we[m]);
            mag_mul(tmp, wm[m], sumc); mag_add(term, term, tmp);
            mag_mul_ui(term, term, (ulong)B);
            mag_add(tot[2 * m], tot[2 * m], term); mag_add(tot[2 * m + 1], tot[2 * m + 1], term);
        }
        for (int m = 0; m < 4; m++) { mag_clear(wm[m]); mag_clear(we[m]); }
        mag_clear(trig); mag_clear(sumc); mag_clear(term);
        for (int m = 0; m < 8; m++) { arb_set_d(x, acc[2 * m]); arb_add(accr[m], accr[m], x, wp); arb_set_d(x, acc[2 * m + 1]); arb_add(accr[m], accr[m], x, wp); }
        n += (ulong)B; nb++;
    }
#undef accr
#undef tot
    Rr->maxph = maxph; Rr->nb = nb;
    arb_clear(x); arb_clear(zero); arb_clear(c);
    mag_clear(err); mag_clear(tmp); mag_clear(tmp2); mag_clear(eA); mag_clear(mA); mag_clear(eW); mag_clear(mW); mag_clear(eL); mag_clear(mL);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
    flint_cleanup();
    return NULL;
}

/* rigorous main sums: S[0] = sum n^-s, S[1] = -sum log n n^-s, S[2] = sum n^{s-1}, S[3] = sum log n n^{s-1}, n = 1..N */
static void main_sums_row(acb_ptr S, const arb_t sigma, const arb_t t, const arb_t tau, ulong N, slong wp, const zf_params *P, zf_stats *St)
{
    int J = P->J;
    double log2tau = log2(arf_get_d(arb_midref(tau), ARF_RND_UP));
    long Bmin = 2 * (J + 1) > 32 ? 2 * (J + 1) : 32;
    arb_t x, l, w, zero, c, cc, ss, L[JMAX + 1];
    mag_t err, tmp, tmp2, epsi[JMAX + 1], eA, mA, eW, mW, eL, mL, tot[8];
    fx E[JMAX + 1];
    arb_init(x); arb_init(l); arb_init(w); arb_init(zero); arb_init(c); arb_init(cc); arb_init(ss);
    mag_init(err); mag_init(tmp); mag_init(tmp2); mag_init(eA); mag_init(mA); mag_init(eW); mag_init(mW); mag_init(eL); mag_init(mL);
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }
    for (int m = 0; m < 8; m++) mag_init(tot[m]);
    arb_t accr[8]; for (int m = 0; m < 8; m++) { arb_init(accr[m]); arb_zero(accr[m]); }
    const double u = 0x1p-53;
    double t0 = now();
    /* head in Arb: terms with A = n^-sigma, W = n^{sigma-1}, cos/sin of t log n */
    ulong n = 1;
    while (n <= N)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)N);
        if (B >= Bmin || (B >= J + 1 && (long)(N - n + 1) == B)) break;
        arb_log_ui(l, n, wp);
        arb_mul(x, l, tau, wp); arb_mul_2exp_si(x, x, 1);
        arb_sin_cos_pi(ss, cc, x, wp);
        arb_neg(ss, ss);                                   /* e^{-i t log n} = cc + i ss */
        arb_mul(w, sigma, l, wp); arb_neg(w, w); arb_exp(w, w, wp);   /* A */
        arb_addmul(accr[0], w, cc, wp); arb_addmul(accr[1], w, ss, wp);
        arb_mul(w, w, l, wp);
        arb_addmul(accr[2], w, cc, wp); arb_addmul(accr[3], w, ss, wp);
        arb_sub_ui(x, sigma, 1, wp); arb_mul(w, x, l, wp); arb_exp(w, w, wp);  /* W */
        arb_addmul(accr[4], w, cc, wp); arb_addmul(accr[5], w, ss, wp);
        arb_mul(w, w, l, wp);
        arb_addmul(accr[6], w, cc, wp); arb_addmul(accr[7], w, ss, wp);
        n++;
    }
    St->head_terms = (double)(n - 1); St->sec_head = now() - t0; t0 = now();
    double nb = 0, maxph = 0;
    if (n <= N)
    {
        ulong lo[16], hi[16];
        int T = split_ranges(lo, hi, n, N, P->threads, P->bmax);
        rrange_t *R = flint_malloc(16 * sizeof(rrange_t)); pthread_t th[16];
        for (int i = 0; i < T; i++)
        {
            R[i].sigma = sigma; R[i].tau = tau; R[i].n0 = lo[i]; R[i].n1 = hi[i]; R[i].wp = wp; R[i].P = P;
            for (int m = 0; m < 8; m++) { arb_init(R[i].accr[m]); mag_init(R[i].tot[m]); }
        }
        if (T == 1) row_range(&R[0]);
        else
        {
            for (int i = 0; i < T; i++) if (pthread_create(&th[i], NULL, row_range, &R[i])) { fprintf(stderr, "pthread_create\n"); abort(); }
            for (int i = 0; i < T; i++) pthread_join(th[i], NULL);
        }
        for (int i = 0; i < T; i++)
        {
            for (int m = 0; m < 8; m++) { arb_add(accr[m], accr[m], R[i].accr[m], wp); mag_add(tot[m], tot[m], R[i].tot[m]); arb_clear(R[i].accr[m]); mag_clear(R[i].tot[m]); }
            if (R[i].maxph > maxph) maxph = R[i].maxph;
            nb += R[i].nb;
        }
        flint_free(R);
    }
    St->sec_fast = now() - t0; St->blocks = nb; St->terms_fast = (double)N - St->head_terms; St->max_phase_err = maxph;
    for (int m = 0; m < 8; m++) arb_add_error_mag(accr[m], tot[m]);
    St->sum_err_fast = mag_get_d(tot[0]);
    /* S0 = sum A (c + i s) ; S1 = -sum A l (c + i s) ; S2 = sum W (c - i s) ; S3 = sum W l (c - i s) */
    arb_set(acb_realref(S + 0), accr[0]); arb_set(acb_imagref(S + 0), accr[1]);
    arb_neg(acb_realref(S + 1), accr[2]); arb_neg(acb_imagref(S + 1), accr[3]);
    arb_set(acb_realref(S + 2), accr[4]); arb_neg(acb_imagref(S + 2), accr[5]);
    arb_set(acb_realref(S + 3), accr[6]); arb_neg(acb_imagref(S + 3), accr[7]);
    for (int m = 0; m < 8; m++) { arb_clear(accr[m]); mag_clear(tot[m]); }
    arb_clear(x); arb_clear(l); arb_clear(w); arb_clear(zero); arb_clear(c); arb_clear(cc); arb_clear(ss);
    mag_clear(err); mag_clear(tmp); mag_clear(tmp2); mag_clear(eA); mag_clear(mA); mag_clear(eW); mag_clear(mW); mag_clear(eL); mag_clear(mL);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
}

/* H(z) = R(z) - sum_{n<=N} n^{-z} for the fixed N (z exact or a ball); mirror = 1: Htilde(z) = conj(H(1 - conj z)) */
static int Hfun(acb_t res, const acb_t z, const fmpz_t N, slong K, slong prec, int mirror)
{
    acb_t w; fmpz_t Nz; mag_t rb;
    acb_init(w); fmpz_init(Nz); mag_init(rb);
    acb_set(w, z);
    if (mirror) { acb_conj(w, w); acb_neg(w, w); acb_add_ui(w, w, 1, prec); }     /* 1 - conj z */
    zf_rs_corr(res, w, K, prec, Nz, rb);
    int ok = acb_is_finite(res);
    if (ok && !fmpz_equal(Nz, N))
    {   /* H = sum_{N < n <= Nz} n^{-w} + corr_{Nz}  (or minus the sum if Nz < N) */
        acb_t term, nn; acb_init(term); acb_init(nn);
        fmpz_t lo, hi; fmpz_init(lo); fmpz_init(hi);
        int sgn = fmpz_cmp(Nz, N) > 0 ? 1 : -1;
        if (sgn > 0) { fmpz_add_ui(lo, N, 1); fmpz_set(hi, Nz); } else { fmpz_add_ui(lo, Nz, 1); fmpz_set(hi, N); }
        {
            ulong a0 = fmpz_get_ui(lo), a1 = fmpz_get_ui(hi);
            if (a1 - a0 > 1000) ok = 0;
            for (ulong m = a0; ok && m <= a1; m++)
            {
                acb_set_ui(nn, m); acb_neg(term, w); acb_pow(term, nn, term, prec);
                if (sgn > 0) acb_add(res, res, term, prec); else acb_sub(res, res, term, prec);
            }
        }
        fmpz_clear(lo); fmpz_clear(hi); acb_clear(term); acb_clear(nn);
    }
    if (mirror) acb_conj(res, res);
    acb_clear(w); fmpz_clear(Nz); mag_clear(rb);
    return ok;
}

/* H(s) and H'(s) (THEORY 10): central difference with step h = 2^-40 along i, Cauchy remainder with M = sup |H| on the box
   s + [-rho, rho] + i[-rho, rho] (rho = 1/32, halved until the RS correction is defined there). */
static int Hjet(acb_t H0, acb_t H1, const acb_t s, const fmpz_t N, slong K, slong prec, int mirror)
{
    acb_t zp, zm, hp, hm, box; mag_t M, rho, hr, e1;
    acb_init(zp); acb_init(zm); acb_init(hp); acb_init(hm); acb_init(box); mag_init(M); mag_init(rho); mag_init(hr); mag_init(e1);
    int ok = 1;
    const slong hexp = -40;
    if (!Hfun(H0, s, N, K, prec, mirror)) ok = 0;
    acb_set(zp, s); acb_set(zm, s);
    arb_t hh; arb_init(hh); arb_one(hh); arb_mul_2exp_si(hh, hh, hexp);
    arb_add(acb_imagref(zp), acb_imagref(zp), hh, ARF_PREC_EXACT);
    arb_sub(acb_imagref(zm), acb_imagref(zm), hh, ARF_PREC_EXACT);
    if (!Hfun(hp, zp, N, K, prec, mirror) || !Hfun(hm, zm, N, K, prec, mirror)) ok = 0;
    acb_sub(H1, hp, hm, prec);
    acb_mul_2exp_si(H1, H1, -hexp - 1);
    acb_div_onei(H1, H1);
    /* sup bound */
    int got = 0;
    for (int r = -5; r >= -20 && ok; r--)
    {
        mag_set_ui_2exp_si(rho, 1, r);
        acb_set(box, s);
        mag_add(arb_radref(acb_realref(box)), arb_radref(acb_realref(box)), rho);
        mag_add(arb_radref(acb_imagref(box)), arb_radref(acb_imagref(box)), rho);
        acb_t hb; acb_init(hb);
        int okb = Hfun(hb, box, N, K, 64, mirror);
        if (okb) { acb_get_mag(M, hb); got = 1; }
        acb_clear(hb);
        if (got) break;
    }
    if (!got) ok = 0;
    else
    {   /* |err| <= (M/rho)(h/rho)^2 / (1 - (h/rho)^2) */
        mag_set_ui_2exp_si(hr, 1, hexp); mag_div(hr, hr, rho); mag_mul(hr, hr, hr);
        mag_div(e1, M, rho); mag_mul(e1, e1, hr);
        mag_t one; mag_init(one); mag_one(one); mag_sub_lower(one, one, hr); mag_div(e1, e1, one); mag_clear(one);
        acb_add_error_mag(H1, e1);
    }
    arb_clear(hh);
    acb_clear(zp); acb_clear(zm); acb_clear(hp); acb_clear(hm); acb_clear(box); mag_clear(M); mag_clear(rho); mag_clear(hr); mag_clear(e1);
    return ok;
}

/* zeta(s), zeta'(s) at s = sigma + i(T0 + u) */
int zf_row(acb_t zeta, acb_t dzeta, const fmpz_t T0, double u, const arb_t sigma, const zf_params *P, zf_stats *S)
{
    double t0 = now();
    slong bits = fmpz_bits(T0) + 4, wp = 330 + bits;
    if (!arb_is_finite(sigma) || !(arf_cmp_si(arb_midref(sigma), 1) > 0) || mag_cmp_2exp_si(arb_radref(sigma), -100) > 0)
    { fprintf(stderr, "zf_row: needs a narrow ball sigma > 1\n"); abort(); }
    arb_t t, tau, pi2; acb_t s, chi, dchi, a, b, H0, H1, G0, G1; acb_ptr Sm = _acb_vec_init(4);
    arb_init(t); arb_init(tau); arb_init(pi2); acb_init(s); acb_init(chi); acb_init(dchi); acb_init(a); acb_init(b);
    acb_init(H0); acb_init(H1); acb_init(G0); acb_init(G1);
    zf_height(t, T0, u);
    arb_const_pi(pi2, wp); arb_mul_2exp_si(pi2, pi2, 1); arb_div(tau, t, pi2, wp);
    arb_set(acb_realref(s), sigma); arb_set(acb_imagref(s), t);
    /* K: Thm 4.2 bound at sigma and 1 - sigma below 2^-200 */
    mag_t rb; mag_init(rb);
    slong K;
    acb_t sm; acb_init(sm); acb_set(sm, s); acb_conj(sm, sm); acb_neg(sm, sm); acb_add_ui(sm, sm, 1, wp);
    for (K = 3; K < 60; K++)
    {
        mag_t r2; mag_init(r2);
        acb_dirichlet_zeta_rs_bound(rb, s, K); acb_dirichlet_zeta_rs_bound(r2, sm, K);
        int good = mag_cmp_2exp_si(rb, -200) < 0 && mag_cmp_2exp_si(r2, -200) < 0;
        mag_clear(r2);
        if (good) break;
    }
    S->K = K;
    /* N from the correction at s */
    zf_rs_corr(H0, s, K, 256, S->N, rb);
    S->rs_bound = mag_get_d(rb);
    int ok = Hjet(H0, H1, s, S->N, K, 256, 0) && Hjet(G0, G1, s, S->N, K, 256, 1);
    /* chi and chi'/chi:  log chi = (s - 1/2) log pi + lgamma((1-s)/2) - lgamma(s/2) */
    {
        acb_t lp, g1, g2, h; acb_init(lp); acb_init(g1); acb_init(g2); acb_init(h);
        acb_const_pi(lp, wp); acb_log(lp, lp, wp);
        acb_sub_ui(h, s, 1, wp); acb_neg(h, h); acb_mul_2exp_si(h, h, -1);     /* (1-s)/2 */
        acb_lgamma(g1, h, wp); acb_digamma(a, h, wp);
        acb_mul_2exp_si(h, s, -1);
        acb_lgamma(g2, h, wp); acb_digamma(b, h, wp);
        acb_set_d(h, 0.5); acb_sub(h, s, h, wp); acb_mul(h, h, lp, wp);
        acb_add(h, h, g1, wp); acb_sub(h, h, g2, wp); acb_exp(chi, h, wp);
        acb_add(a, a, b, wp); acb_mul_2exp_si(a, a, -1); acb_sub(a, lp, a, wp);  /* chi'/chi */
        acb_mul(dchi, chi, a, wp);
        acb_clear(lp); acb_clear(g1); acb_clear(g2); acb_clear(h);
    }
    double t1 = now(); S->sec_setup = t1 - t0;
    ulong N = fmpz_get_ui(S->N);
    main_sums_row(Sm, sigma, t, tau, N, wp, P, S);
    /* zeta = S0 + H + chi (S2 + G) ; zeta' = S1 + H' + chi'(S2 + G) + chi (S3 + G') */
    acb_add(a, Sm + 2, G0, wp);
    acb_mul(b, chi, a, wp); acb_add(zeta, Sm + 0, H0, wp); acb_add(zeta, zeta, b, wp);
    acb_mul(b, dchi, a, wp); acb_add(dzeta, Sm + 1, H1, wp); acb_add(dzeta, dzeta, b, wp);
    acb_add(a, Sm + 3, G1, wp); acb_mul(b, chi, a, wp); acb_add(dzeta, dzeta, b, wp);
    S->corr_rad = mag_get_d(arb_radref(acb_realref(H1)));
    S->sec_total = now() - t0;
    mag_clear(rb); acb_clear(sm);
    arb_clear(t); arb_clear(tau); arb_clear(pi2); acb_clear(s); acb_clear(chi); acb_clear(dchi); acb_clear(a); acb_clear(b);
    acb_clear(H0); acb_clear(H1); acb_clear(G0); acb_clear(G1);
    _acb_vec_clear(Sm, 4);
    return ok;
}

#include "zfast_m3b.inc"
#include "zfast_m3c.inc"
