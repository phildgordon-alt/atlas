/* zfast: rigorous fast evaluation of Hardy's Z(t) (and, later, zeta/zeta' rows) at exact heights t = T0 + u.
   Theory and every error bound: ../THEORY_ZFAST.md.  Compile with -ffp-contract=off (the error analysis assumes the
   floating-point operations exactly as written; fma() is used only where written). */
#ifndef ZFAST_H
#define ZFAST_H
#include <stdint.h>
#include <flint/fmpz.h>
#include <flint/arb.h>
#include <flint/acb.h>

typedef struct {
    int J;              /* interpolation degree of the phase (nodes 0..J) */
    long bmax;          /* maximum block length */
    double log2_interp; /* target log2 of the interpolation error per term (turns) */
    long kcorr;         /* RS correction terms K (0 = automatic) */
    int verbose;
    int threads;        /* worker threads for the fast part (v9) */
} zf_params;

typedef struct {
    /* error budget, all upper bounds (turns for phase, absolute for sums) */
    double head_terms, blocks, terms_fast;
    double max_phase_err;      /* max over blocks of the per-term phase error bound (turns) */
    double sum_err_fast;       /* rigorous bound for the fast part (absolute) */
    double corr_rad;           /* radius of the RS correction (incl. remainder) */
    double rs_bound;           /* Arias de Reyna Thm 4.2 bound used */
    long K;
    double sec_setup, sec_head, sec_fast, sec_total;
    fmpz_t N;
} zf_stats;

void zf_params_default(zf_params *P);
void zf_stats_init(zf_stats *S);
void zf_stats_clear(zf_stats *S);

/* exact height t = T0 + u as an exact arb ball */
void zf_height(arb_t t, const fmpz_t T0, double u);

/* Z(T0 + u): res is a rigorous ball. */
void zf_Z(arb_t res, const fmpz_t T0, double u, const zf_params *P, zf_stats *S);

/* the RS correction for Z only (testing): res = 2 Re(e^{i theta} corr) */
void zf_rs_corr(acb_t res, const acb_t s, slong K, slong prec, fmpz_t N, mag_t rsbound);

/* kernel self-test hooks */
void zf_cos2pi(double *c, double *s, uint64_t v);
void zf_phase_test(double *maxerr, double *bound, const fmpz_t T0, double u, ulong n0, long B, int J);
/* rows: zeta(s), zeta'(s) at s = sigma + i(T0+u) (THEORY section 10); returns 0 if a bound could not be established */
int zf_row(acb_t zeta, acb_t dzeta, const fmpz_t T0, double u, const arb_t sigma, const zf_params *P, zf_stats *S);
/* M3 window sessions (THEORY_M3.md): kind 0 = Z, kind 1 = rows at sigma */
typedef struct zfm_session zfm_session;
zfm_session *zfm_new(const fmpz_t T0, double u0, double H, int kind, const arb_t sigma, const zf_params *P, double Delta, int K);
void zfm_free(zfm_session *S);
void zfm_Z(arb_t res, zfm_session *S, double u, zf_stats *St);
int zfm_row(acb_t zeta, acb_t dzeta, zfm_session *S, double u, zf_stats *St);
void zfm_info(const zfm_session *S, double *sec_build, double *sec_head, double *sec_fast, double *nb, double *Nw, double *nhead, double *blocks, double *maxph);
#endif
