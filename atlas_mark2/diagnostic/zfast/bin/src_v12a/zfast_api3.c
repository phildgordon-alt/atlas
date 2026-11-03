/* zfast_api3.c (v11): ctypes API for combined sessions (kind 2: Z + rows at a1, a2) and Z grids.  Balls are Arb-printed enclosures. */
#include <stdio.h>
#include <string.h>
#include "zfast.h"

static void sigma_of(arb_t sig, double a)
{
    arb_t pi, h; arb_init(pi); arb_init(h);
    arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512);
    arb_set_d(h, 0.5); arb_add(sig, sig, h, 512);
    arb_clear(pi); arb_clear(h);
}

void *zfa3_new(const char *T0s, double u0, double H, double a1, double a2, double Delta, int K, int J, int threads)
{
    zf_params P; zf_params_default(&P); if (J > 0) P.J = J; if (threads > 0) P.threads = threads;
    fmpz_t T0; fmpz_init(T0);
    if (fmpz_set_str(T0, T0s, 10)) { fmpz_clear(T0); return NULL; }
    arb_t s1, s2; arb_init(s1); arb_init(s2); sigma_of(s1, a1); sigma_of(s2, a2);
    zfm_session *S = zfm_new2(T0, u0, H, 2, s1, s2, &P, Delta, K);
    arb_clear(s1); arb_clear(s2); fmpz_clear(T0);
    return S;
}

int zfa3_info(void *s, char *out, int outlen)
{
    double sb, sh, sf, nb, Nw, nhd, bl, mp; zfm_info((zfm_session *)s, &sb, &sh, &sf, &nb, &Nw, &nhd, &bl, &mp);
    int n = snprintf(out, outlen, "{\"sec_build\": %.4f, \"sec_head\": %.4f, \"sec_fast\": %.4f, \"buckets\": %.0f, \"Nw\": %.0f, \"nhead\": %.0f, \"blocks\": %.0f, \"max_phase_err\": %.3e}", sb, sh, sf, nb, Nw, nhd, bl, mp);
    return n >= outlen ? -2 : 0;
}

int zfa3_Z(void *s, double u, char *out, int outlen)
{
    arb_t Z; arb_init(Z); zf_stats St; zf_stats_init(&St);
    zfm_Z(Z, (zfm_session *)s, u, &St);
    char *zs = arb_get_str(Z, 40, 0), *mid = arf_get_str(arb_midref(Z), 25);
    int n = snprintf(out, outlen, "{\"Z\": \"%s\", \"Z_mid\": \"%s\", \"rad\": %.6e, \"N\": %lu}", zs, mid, mag_get_d(arb_radref(Z)), fmpz_get_ui(St.N));
    flint_free(zs); flint_free(mid); zf_stats_clear(&St); arb_clear(Z);
    return n >= outlen ? -2 : 0;
}

/* which = 0 (a1) or 1 (a2): P = Re(-zeta'/zeta) */
int zfa3_row(void *s, double u, int which, char *out, int outlen)
{
    acb_t z, dz, q; acb_init(z); acb_init(dz); acb_init(q); zf_stats St; zf_stats_init(&St);
    int ok = zfm_row2(z, dz, (zfm_session *)s, which, u, &St);
    acb_div(q, dz, z, 256); acb_neg(q, q);
    char *p = arb_get_str(acb_realref(q), 40, 0), *pm = arf_get_str(arb_midref(acb_realref(q)), 25);
    char *zr = arb_get_str(acb_realref(z), 30, 0), *zi = arb_get_str(acb_imagref(z), 30, 0), *dr = arb_get_str(acb_realref(dz), 30, 0), *di = arb_get_str(acb_imagref(dz), 30, 0);
    int n = snprintf(out, outlen, "{\"ok\": %d, \"P\": \"%s\", \"P_mid\": \"%s\", \"rad\": %.6e, \"zeta_re\": \"%s\", \"zeta_im\": \"%s\", \"dzeta_re\": \"%s\", \"dzeta_im\": \"%s\", \"N\": %lu}",
                     ok, p, pm, mag_get_d(arb_radref(acb_realref(q))), zr, zi, dr, di, fmpz_get_ui(St.N));
    flint_free(p); flint_free(pm); flint_free(zr); flint_free(zi); flint_free(dr); flint_free(di);
    zf_stats_clear(&St); acb_clear(z); acb_clear(dz); acb_clear(q);
    return n >= outlen ? -2 : (ok ? 0 : -3);
}

/* Z on a grid u_k = u_start + k*step (k = 0..n-1; u_k formed in binary64): midpoints and radii (upper bounds) as doubles.
   For scans and the Turing count: sign(Z) is certified where |mid| > rad (mid rounded to double: rad_out includes that rounding). */
int zfa3_Zgrid(void *s, double u_start, double step, long n, double *mid, double *rad, double *uout)
{
    arb_t Z; arb_init(Z);
    for (long k = 0; k < n; k++)
    {
        double u = u_start + (double)k * step; uout[k] = u;
        zf_stats St; zf_stats_init(&St);
        zfm_Z(Z, (zfm_session *)s, u, &St);
        double m = arf_get_d(arb_midref(Z), ARF_RND_NEAR);
        arb_t d; arb_init(d); arb_set_d(d, m); arb_sub(d, Z, d, 128);
        mag_t r; mag_init(r); arb_get_mag(r, d);           /* |Z - m| <= r for all Z in the ball */
        mid[k] = m; rad[k] = mag_get_d(r);
        mag_clear(r); arb_clear(d); zf_stats_clear(&St);
    }
    arb_clear(Z);
    return 0;
}

void zfa3_free(void *s) { zfm_free((zfm_session *)s); }
