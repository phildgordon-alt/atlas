/* zfast_api4.c (v12): kind-0 sessions; Z and rows (complex shift, THEORY_M5b) from the same Z moments. */
#include <stdio.h>
#include <string.h>
#include "zfast.h"
int zfm_row3(acb_t zeta, acb_t dzeta, zfm_session *S, const arb_t sigma, double u, zf_stats *St);

void *zfa4_new(const char *T0s, double u0, double H, double Delta, int K, int J, int threads)
{
    zf_params P; zf_params_default(&P); if (J > 0) P.J = J; if (threads > 0) P.threads = threads;
    fmpz_t T0; fmpz_init(T0);
    if (fmpz_set_str(T0, T0s, 10)) { fmpz_clear(T0); return NULL; }
    arb_t s; arb_init(s); arb_set_d(s, 0.5);
    zfm_session *S = zfm_new(T0, u0, H, 0, s, &P, Delta, K);
    arb_clear(s); fmpz_clear(T0);
    return S;
}

int zfa4_row(void *s, double u, double a, char *out, int outlen)
{
    arb_t sig, pi, h; arb_init(sig); arb_init(pi); arb_init(h);
    arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512); arb_set_d(h, 0.5); arb_add(sig, sig, h, 512);
    acb_t z, dz, q; acb_init(z); acb_init(dz); acb_init(q); zf_stats St; zf_stats_init(&St);
    int ok = zfm_row3(z, dz, (zfm_session *)s, sig, u, &St);
    acb_div(q, dz, z, 256); acb_neg(q, q);
    char *p = arb_get_str(acb_realref(q), 40, 0), *pm = arf_get_str(arb_midref(acb_realref(q)), 25);
    char *zr = arb_get_str(acb_realref(z), 30, 0), *zi = arb_get_str(acb_imagref(z), 30, 0), *dr = arb_get_str(acb_realref(dz), 30, 0), *di = arb_get_str(acb_imagref(dz), 30, 0);
    int n = snprintf(out, outlen, "{\"ok\": %d, \"P\": \"%s\", \"P_mid\": \"%s\", \"rad\": %.6e, \"zeta_re\": \"%s\", \"zeta_im\": \"%s\", \"dzeta_re\": \"%s\", \"dzeta_im\": \"%s\", \"N\": %lu, \"sec\": %.5f}",
                     ok, p, pm, mag_get_d(arb_radref(acb_realref(q))), zr, zi, dr, di, fmpz_get_ui(St.N), St.sec_total);
    flint_free(p); flint_free(pm); flint_free(zr); flint_free(zi); flint_free(dr); flint_free(di);
    zf_stats_clear(&St); acb_clear(z); acb_clear(dz); acb_clear(q); arb_clear(sig); arb_clear(pi); arb_clear(h);
    return n >= outlen ? -2 : (ok ? 0 : -3);
}
