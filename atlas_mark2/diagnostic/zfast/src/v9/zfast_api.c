/* zfast_api.c (v9): shared-library entry points for Python ctypes.  Results are JSON strings; balls are printed with arb_get_str
   (40 digits), which Arb guarantees to be enclosures, so parsing them back with arb(str) is rigorous. */
#include <stdio.h>
#include <string.h>
#include "zfast.h"

int zfa_Z(const char *T0s, double u, int J, int threads, char *out, int outlen)
{
    zf_params P; zf_params_default(&P); if (J > 0) P.J = J; if (threads > 0) P.threads = threads;
    fmpz_t T0; fmpz_init(T0);
    if (fmpz_set_str(T0, T0s, 10)) { fmpz_clear(T0); return -1; }
    arb_t Z; arb_init(Z); zf_stats S; zf_stats_init(&S);
    zf_Z(Z, T0, u, &P, &S);
    char *zs = arb_get_str(Z, 40, 0);
    int n = snprintf(out, outlen, "{\"Z\": \"%s\", \"rad\": %.6e, \"N\": %lu, \"sec\": %.4f}", zs, mag_get_d(arb_radref(Z)), fmpz_get_ui(S.N), S.sec_total);
    flint_free(zs); zf_stats_clear(&S); arb_clear(Z); fmpz_clear(T0);
    return (n >= outlen) ? -2 : 0;
}

/* row: sigma = 1/2 + pi/(2a); zeta, zeta', P = Re(-zeta'/zeta) */
int zfa_row(const char *T0s, double u, double a, int J, int threads, char *out, int outlen)
{
    zf_params P; zf_params_default(&P); if (J > 0) P.J = J; if (threads > 0) P.threads = threads;
    fmpz_t T0; fmpz_init(T0);
    if (fmpz_set_str(T0, T0s, 10)) { fmpz_clear(T0); return -1; }
    arb_t sig, pi, h; acb_t z, dz, q; arb_init(sig); arb_init(pi); arb_init(h); acb_init(z); acb_init(dz); acb_init(q);
    arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512);
    arb_set_d(h, 0.5); arb_add(sig, sig, h, 512);
    zf_stats S; zf_stats_init(&S);
    int ok = zf_row(z, dz, T0, u, sig, &P, &S);
    acb_div(q, dz, z, 256); acb_neg(q, q);
    char *p = arb_get_str(acb_realref(q), 40, 0), *zr = arb_get_str(acb_realref(z), 40, 0), *zi = arb_get_str(acb_imagref(z), 40, 0);
    int n = snprintf(out, outlen, "{\"ok\": %d, \"P\": \"%s\", \"zeta_re\": \"%s\", \"zeta_im\": \"%s\", \"N\": %lu, \"sec\": %.4f}",
                     ok, p, zr, zi, fmpz_get_ui(S.N), S.sec_total);
    flint_free(p); flint_free(zr); flint_free(zi);
    zf_stats_clear(&S); arb_clear(sig); arb_clear(pi); arb_clear(h); acb_clear(z); acb_clear(dz); acb_clear(q); fmpz_clear(T0);
    return (n >= outlen) ? -2 : (ok ? 0 : -3);
}
