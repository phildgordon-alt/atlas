/* zfast_api2.c (v10b): ctypes entry points for M3 window sessions.  Balls are printed by arb_get_str (40 digits), which Arb guarantees
   to be enclosures; parsing them back with python-flint arb(str) is rigorous. */
#include <stdio.h>
#include <string.h>
#include "zfast.h"

void *zfa_sess_new(const char *T0s, double u0, double H, int kind, double a, double Delta, int K, int J, int threads)
{
    zf_params P; zf_params_default(&P); if (J > 0) P.J = J; if (threads > 0) P.threads = threads;
    fmpz_t T0; fmpz_init(T0);
    if (fmpz_set_str(T0, T0s, 10)) { fmpz_clear(T0); return NULL; }
    arb_t sig, pi, h; arb_init(sig); arb_init(pi); arb_init(h);
    if (kind == 1)
    {
        arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512);
        arb_set_d(h, 0.5); arb_add(sig, sig, h, 512);
    }
    zfm_session *S = zfm_new(T0, u0, H, kind, sig, &P, Delta, K);
    arb_clear(sig); arb_clear(pi); arb_clear(h); fmpz_clear(T0);
    return S;
}

int zfa_sess_info(void *s, char *out, int outlen)
{
    double sb, sh, sf, nb, Nw, nhd, bl, mp; zfm_info((zfm_session *)s, &sb, &sh, &sf, &nb, &Nw, &nhd, &bl, &mp);
    int n = snprintf(out, outlen, "{\"sec_build\": %.4f, \"buckets\": %.0f, \"Nw\": %.0f, \"nhead\": %.0f, \"blocks\": %.0f, \"max_phase_err\": %.3e}", sb, nb, Nw, nhd, bl, mp);
    return n >= outlen ? -2 : 0;
}

int zfa_sess_Z(void *s, double u, char *out, int outlen)
{
    arb_t Z; arb_init(Z); zf_stats St; zf_stats_init(&St);
    zfm_Z(Z, (zfm_session *)s, u, &St);
    char *zs = arb_get_str(Z, 40, 0);
    int n = snprintf(out, outlen, "{\"Z\": \"%s\", \"rad\": %.6e, \"N\": %lu}", zs, mag_get_d(arb_radref(Z)), fmpz_get_ui(St.N));
    flint_free(zs); zf_stats_clear(&St); arb_clear(Z);
    return n >= outlen ? -2 : 0;
}

int zfa_sess_row(void *s, double u, char *out, int outlen)
{
    acb_t z, dz, q; acb_init(z); acb_init(dz); acb_init(q); zf_stats St; zf_stats_init(&St);
    int ok = zfm_row(z, dz, (zfm_session *)s, u, &St);
    acb_div(q, dz, z, 256); acb_neg(q, q);
    char *p = arb_get_str(acb_realref(q), 40, 0);
    int n = snprintf(out, outlen, "{\"ok\": %d, \"P\": \"%s\", \"rad\": %.6e, \"N\": %lu}", ok, p, mag_get_d(arb_radref(acb_realref(q))), fmpz_get_ui(St.N));
    flint_free(p); zf_stats_clear(&St); acb_clear(z); acb_clear(dz); acb_clear(q);
    return n >= outlen ? -2 : (ok ? 0 : -3);
}

void zfa_sess_free(void *s) { zfm_free((zfm_session *)s); }
