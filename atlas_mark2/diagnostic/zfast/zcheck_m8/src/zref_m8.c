/* zref_m8.c (M8, 2026-11-01): code-independent rigorous reference for Z(T0 + u) at large height.  Shares NO code with zfast
   (links stock FLINT 3.6.0 only; written from the Riemann-Siegel formula, FLINT's documented powsum_smooth algorithm and
   review2/src/rv_ref_copy.c's independent Gabcke correction, which is copied verbatim below).

   Z(t) = 2 Re( e^{i theta(t)} S(t) ) + (-1)^{N-1} a^{-1/2} (C0(p) - C1(p)/a) +/- 0.053 t^{-5/4},   S(t) = sum_{n<=N} n^{-1/2 - i t},
   a = sqrt(t/2pi), N = floor a, p = a - N (Gabcke's R1 bound for t >= 200, quoted in Bober-Hiary 2018 (6)-(8); sgn = -1 as rv_ref GZ).

   WHY THIS EXISTS (diagnosis of the M6 1e24 ball of radius 4.27e91): stock acb_dirichlet_powsum_smooth accumulates ~0.27 N terms
   sequentially into ONE ball.  Once a term's radius is below one ulp of the running radius (mag_t has a 30-bit mantissa, always
   rounded up), every arb_add multiplies the running radius by about (1 + 2^-29.6): the radius grows like exp(c n), c ~ 1.2e-9
   measured (zcheck_m8/bin/probe_mag2).  At 1e24, n ~ 1.06e11 adds => exp(~130 or more): a useless ball, independent of prec.  At 1e21
   (3.4e9 adds) the factor is only ~e^4 which is why 1e20/1e21 agreed.  Fix: identical mathematics, BLOCKED accumulation - each
   accumulator receives at most 2^16 adds before being flushed into a higher level (and per-thread totals are combined at the end),
   so no ball sees more than ~1e5 sequential adds (growth factor < 1 + 2e-4).  Ball arithmetic stays rigorous in any summation order.

   Algorithm (FLINT powsum_smooth structure): for n <= N coprime to 30, term_j(n) = n^{-1/2} e^{-i t_j log n} is added to
   sums_j[m] for every 5-smooth m <= N/n (all n = m * n', n' coprime to 30, n' >= 7 or n' = 1); finally S_j = sum_m m^{-1/2 - i t_j} sums_j[m]
   with m^{-s} evaluated directly (arb_log_ui, arb_sin_cos, arb_rsqrt_ui).  n' = 1 contributes 1 to every sums_j[m].
   Threads split the n' range in interleaved chunks; per-thread sums are combined at the end.  Several points per pass share log n.

   usage: zref_m8 T0 PREC THREADS u1 [u2 ...]   (u as C double literals, hex allowed; exact t = T0 + u checked)
   output: one JSON line per point. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <sys/resource.h>
#include <flint/acb.h>
#include <flint/arb_poly.h>
#include <flint/acb_dirichlet.h>

#define MAXP 16
#define CHUNK (1UL << 18)      /* n' values per chunk; <= CHUNK*4/15 ~ 7e4 adds into one partial accumulator */
static double now(void) { struct timespec a; clock_gettime(CLOCK_MONOTONIC, &a); return a.tv_sec + 1e-9 * a.tv_nsec; }

static void height(arb_t t, const fmpz_t T0, double u)
{
    arb_t a; arb_init(a); arb_set_fmpz(t, T0); arb_set_d(a, u); arb_add(t, t, a, ARF_PREC_EXACT);
    if (!arb_is_exact(t)) { fprintf(stderr, "height not exact\n"); exit(2); }
    arb_clear(a);
}

/* ---- verbatim from review2/src/rv_ref_copy.c (independent of zfast) ---- */
static void gabcke(arb_t res, fmpz_t N, const arb_t t, int sgn, slong prec)
{
    arb_t a, p, pi, c, x; arb_poly_t q, num, den, psi;
    arb_init(a); arb_init(p); arb_init(pi); arb_init(c); arb_init(x);
    arb_poly_init(q); arb_poly_init(num); arb_poly_init(den); arb_poly_init(psi);
    arb_const_pi(pi, prec);
    arb_mul_2exp_si(a, pi, 1); arb_div(a, t, a, prec); arb_sqrt(a, a, prec);
    arb_floor(p, a, prec);
    if (!arb_get_unique_fmpz(N, p)) { fprintf(stderr, "N ambiguous\n"); abort(); }
    arb_sub_fmpz(p, a, N, prec);
    arb_mul(c, p, p, prec); arb_sub(c, c, p, prec); arb_set_d(x, 0.0625); arb_sub(c, c, x, prec);
    arb_mul(c, c, pi, prec); arb_mul_2exp_si(c, c, 1);
    arb_poly_set_coeff_arb(q, 0, c);
    arb_mul_2exp_si(c, p, 1); arb_sub_ui(c, c, 1, prec); arb_mul(c, c, pi, prec); arb_mul_2exp_si(c, c, 1);
    arb_poly_set_coeff_arb(q, 1, c);
    arb_mul_2exp_si(c, pi, 1); arb_poly_set_coeff_arb(q, 2, c);
    arb_poly_cos_series(num, q, 4, prec);
    arb_poly_zero(q);
    arb_mul(c, p, pi, prec); arb_mul_2exp_si(c, c, 1); arb_poly_set_coeff_arb(q, 0, c);
    arb_mul_2exp_si(c, pi, 1); arb_poly_set_coeff_arb(q, 1, c);
    arb_poly_cos_series(den, q, 4, prec);
    arb_poly_div_series(psi, num, den, 4, prec);
    arb_poly_get_coeff_arb(res, psi, 0);
    arb_poly_get_coeff_arb(c, psi, 3);
    arb_mul(x, pi, pi, prec); arb_mul_2exp_si(x, x, 4); arb_div(c, c, x, prec);
    if (sgn < 0) arb_neg(c, c);
    arb_div(c, c, a, prec);
    arb_add(res, res, c, prec);
    arb_rsqrt(x, a, prec); arb_mul(res, res, x, prec);
    if (fmpz_is_even(N)) arb_neg(res, res);
    {
        arb_t r; mag_t m; arb_init(r); mag_init(m);
        arb_set_d(r, -1.25); arb_pow(r, t, r, prec); arb_mul_ui(r, r, 53, prec); arb_div_ui(r, r, 1000, prec);
        arb_get_mag(m, r); arb_add_error_mag(res, m);
        arb_clear(r); mag_clear(m);
    }
    arb_clear(a); arb_clear(p); arb_clear(pi); arb_clear(c); arb_clear(x);
    arb_poly_clear(q); arb_poly_clear(num); arb_poly_clear(den); arb_poly_clear(psi);
}
/* ---- end verbatim ---- */

static ulong *SM; static slong NSM; static ulong NN; static int NP; static arb_struct TT[MAXP]; static slong PREC; static int NTH;
static ulong NCHUNK;

static int cmpu(const void *a, const void *b) { ulong x = *(const ulong *) a, y = *(const ulong *) b; return x < y ? -1 : x > y; }

typedef struct { int id; acb_ptr tot; double sec; ulong terms; } job_t;

static void *worker(void *arg)
{
    job_t *J = arg; double t0 = now();
    acb_ptr part = _acb_vec_init(NP * NSM);           /* partial (per chunk) accumulators */
    acb_t term; arb_t lg, w, rs; acb_init(term); arb_init(lg); arb_init(w); arb_init(rs);
    for (ulong c = J->id; c < NCHUNK; c += NTH)
    {
        ulong lo = c * CHUNK + 1, hi = lo + CHUNK - 1; if (hi > NN) hi = NN;
        slong used = 0;
        for (ulong n = lo; n <= hi; n++)
        {
            if (n % 2 == 0 || n % 3 == 0 || n % 5 == 0) continue;
            if (n == 1) continue;                      /* n' = 1 handled exactly at the end */
            ulong lim = NN / n; slong k = 0; while (k < NSM && SM[k] <= lim) k++;
            if (k == 0) continue;
            if (k > used) used = k;
            arb_log_ui(lg, n, PREC); arb_rsqrt_ui(rs, n, PREC);
            for (int j = 0; j < NP; j++)
            {
                arb_mul(w, lg, TT + j, PREC);
                arb_sin_cos(acb_imagref(term), acb_realref(term), w, PREC);
                arb_neg(acb_imagref(term), acb_imagref(term));
                acb_mul_arb(term, term, rs, PREC);
                for (slong i = 0; i < k; i++) acb_add(part + j * NSM + i, part + j * NSM + i, term, PREC);
            }
            J->terms++;
        }
        for (int j = 0; j < NP; j++) for (slong i = 0; i < used; i++)
        {
            acb_add(J->tot + j * NSM + i, J->tot + j * NSM + i, part + j * NSM + i, PREC); acb_zero(part + j * NSM + i);
        }
    }
    _acb_vec_clear(part, NP * NSM); acb_clear(term); arb_clear(lg); arb_clear(w); arb_clear(rs);
    J->sec = now() - t0; return NULL;
}

int main(int argc, char **argv)
{
    if (argc < 5) { fprintf(stderr, "usage: zref_m8 T0 PREC THREADS u1 [u2 ...]\n"); return 1; }
    fmpz_t T0, N, N1; fmpz_init(T0); fmpz_init(N); fmpz_init(N1);
    if (fmpz_set_str(T0, argv[1], 10)) return 1;
    PREC = atol(argv[2]); NTH = atoi(argv[3]); NP = argc - 4;
    if (NP > MAXP || NTH < 1 || NTH > 8) { fprintf(stderr, "bad args\n"); return 1; }
    double us[MAXP]; arb_t corr[MAXP];
    for (int j = 0; j < NP; j++)
    {
        char *e; us[j] = strtod(argv[4 + j], &e); if (*e) { fprintf(stderr, "bad u\n"); return 1; }
        arb_init(TT + j); height(TT + j, T0, us[j]); arb_init(corr[j]);
        gabcke(corr[j], j ? N1 : N, TT + j, -1, PREC);
        if (j && !fmpz_equal(N, N1)) { fprintf(stderr, "points have different N; run separately\n"); return 3; }
    }
    if (!fmpz_abs_fits_ui(N)) { fprintf(stderr, "N too large\n"); return 1; }
    NN = fmpz_get_ui(N);
    /* 5-smooth numbers <= N, sorted */
    slong cap = 64; SM = malloc(cap * sizeof(ulong)); NSM = 0;
    for (ulong a = 1; a <= NN; a *= 2) { for (ulong b = a; b <= NN; b *= 3) { for (ulong c = b; c <= NN; c *= 5)
    { if (NSM == cap) { cap *= 2; SM = realloc(SM, cap * sizeof(ulong)); } SM[NSM++] = c; if (c > NN / 5) break; } if (b > NN / 3) break; } if (a > NN / 2) break; }
    qsort(SM, NSM, sizeof(ulong), cmpu);
    NCHUNK = (NN + CHUNK - 1) / CHUNK;
    double t0 = now();
    pthread_t th[8]; job_t jb[8];
    for (int i = 0; i < NTH; i++) { jb[i].id = i; jb[i].tot = _acb_vec_init(NP * NSM); jb[i].terms = 0; pthread_create(th + i, 0, worker, jb + i); }
    for (int i = 0; i < NTH; i++) pthread_join(th[i], 0);
    double tmain = now() - t0; ulong terms = 0; for (int i = 0; i < NTH; i++) terms += jb[i].terms;
    for (int j = 0; j < NP; j++)
    {
        acb_t S, ms, x; arb_t lg, w, rs; acb_init(S); acb_init(ms); acb_init(x); arb_init(lg); arb_init(w); arb_init(rs);
        acb_ptr tot = _acb_vec_init(NSM);
        for (int i = 0; i < NTH; i++) for (slong k = 0; k < NSM; k++) acb_add(tot + k, tot + k, jb[i].tot + j * NSM + k, PREC);
        for (slong k = 0; k < NSM; k++)
        {
            acb_add_ui(tot + k, tot + k, 1, PREC);                         /* n' = 1 */
            ulong m = SM[k];
            if (m == 1) acb_one(ms);
            else
            {
                arb_log_ui(lg, m, PREC); arb_mul(w, lg, TT + j, PREC);
                arb_sin_cos(acb_imagref(ms), acb_realref(ms), w, PREC); arb_neg(acb_imagref(ms), acb_imagref(ms));
                arb_rsqrt_ui(rs, m, PREC); acb_mul_arb(ms, ms, rs, PREC);
            }
            acb_mul(x, tot + k, ms, PREC); acb_add(S, S, x, PREC);
        }
        acb_t th_, e; acb_init(th_); acb_init(e);
        acb_set_arb(th_, TT + j);
        acb_dirichlet_hardy_theta(th_, th_, NULL, NULL, 1, PREC + 64);
        arb_sin_cos(acb_imagref(e), acb_realref(e), acb_realref(th_), PREC + 64);
        acb_mul(S, S, e, PREC);
        arb_t Z; arb_init(Z); arb_mul_2exp_si(Z, acb_realref(S), 1); arb_add(Z, Z, corr[j], PREC);
        struct rusage ru; getrusage(RUSAGE_SELF, &ru);
        char *zs = arb_get_str(Z, 30, ARB_STR_MORE); char *mid = arf_get_str(arb_midref(Z), 25);
        printf("{\"tool\": \"zref_m8\", \"T0\": \"%s\", \"u\": \"%a\", \"u_dec\": \"%.17g\", \"N\": %lu, \"Z\": \"%s\", \"Z_mid\": \"%s\", \"Z_rad\": %.6e, "
               "\"corr_rad\": %.3e, \"theta_rad\": %.3e, \"smooth\": %ld, \"terms\": %lu, \"prec\": %ld, \"threads\": %d, \"points_in_pass\": %d, "
               "\"main_sec\": %.2f, \"maxrss_mb\": %.1f}\n",
               argv[1], us[j], us[j], NN, zs, mid, mag_get_d(arb_radref(Z)), mag_get_d(arb_radref(corr[j])), mag_get_d(arb_radref(acb_realref(th_))),
               NSM, terms, PREC, NTH, NP, tmain, ru.ru_maxrss / 1048576.0);
        fflush(stdout); flint_free(zs); flint_free(mid);
        _acb_vec_clear(tot, NSM); acb_clear(S); acb_clear(ms); acb_clear(x); arb_clear(lg); arb_clear(w); arb_clear(rs);
        acb_clear(th_); acb_clear(e); arb_clear(Z);
    }
    return 0;
}
