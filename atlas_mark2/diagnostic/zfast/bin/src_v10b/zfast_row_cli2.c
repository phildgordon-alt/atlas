/* zfast_row_cli: lines "T0 u a" -> zeta, zeta' at s = 1/2 + pi/(2a) + i(T0+u) and P = Re(-zeta'/zeta) (atlas_v5 row jet). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include "zfast.h"
int main(int argc, char **argv)
{
    zf_params P; zf_params_default(&P);
    for (int i = 1; i < argc; i++) { if (!strcmp(argv[i], "--J") && i + 1 < argc) P.J = atoi(argv[++i]); else if (!strcmp(argv[i], "--threads") && i + 1 < argc) P.threads = atoi(argv[++i]); else { fprintf(stderr, "?\n"); return 2; } }
    char T0s[200], us[200], as[200]; fmpz_t T0; fmpz_init(T0);
    while (scanf("%199s %199s %199s", T0s, us, as) == 3)
    {
        fmpz_set_str(T0, T0s, 10); double u = strtod(us, 0), a = strtod(as, 0);
        arb_t sig, pi; arb_init(sig); arb_init(pi); acb_t z, dz, q; acb_init(z); acb_init(dz); acb_init(q);
        arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512);
        arb_t h; arb_init(h); arb_set_d(h, 0.5); arb_add(sig, sig, h, 512); arb_clear(h);
        zf_stats S; zf_stats_init(&S);
        int ok = zf_row(z, dz, T0, u, sig, &P, &S);
        acb_div(q, dz, z, 256); acb_neg(q, q);
        char *pm = arf_get_str(arb_midref(acb_realref(q)), 25), *dm1 = arf_get_str(arb_midref(acb_realref(dz)), 25), *dm2 = arf_get_str(arb_midref(acb_imagref(dz)), 25);
        struct rusage ru; getrusage(RUSAGE_SELF, &ru);
        char *s1 = arb_get_str(acb_realref(z), 25, 0), *s1i = arb_get_str(acb_imagref(z), 25, 0), *s2 = arb_get_str(acb_realref(dz), 25, 0), *s2i = arb_get_str(acb_imagref(dz), 25, 0), *s3 = arb_get_str(acb_realref(q), 25, 0);
        printf("{\"T0\": \"%s\", \"u\": \"%s\", \"a\": \"%s\", \"ok\": %d, \"zeta_re\": \"%s\", \"zeta_im\": \"%s\", \"dzeta_re\": \"%s\", \"dzeta_im\": \"%s\", \"P\": \"%s\", \"P_rad\": %.4e, \"P_mid\": \"%s\", \"dzeta_re_mid\": \"%s\", \"dzeta_im_mid\": \"%s\", "
               "\"N\": %lu, \"K\": %ld, \"head_terms\": %.0f, \"blocks\": %.0f, \"max_phase_err\": %.3e, \"sum_err_fast0\": %.3e, \"sec_setup\": %.4f, \"sec_fast\": %.4f, \"sec_total\": %.4f, \"maxrss_mb\": %.1f}\n",
               T0s, us, as, ok, s1, s1i, s2, s2i, s3, mag_get_d(arb_radref(acb_realref(q))), pm, dm1, dm2, fmpz_get_ui(S.N), S.K, S.head_terms, S.blocks, S.max_phase_err, S.sum_err_fast,
               S.sec_setup, S.sec_fast, S.sec_total, ru.ru_maxrss / 1048576.0);
        fflush(stdout); flint_free(s1); flint_free(s1i); flint_free(s2); flint_free(s2i); flint_free(s3); flint_free(pm); flint_free(dm1); flint_free(dm2);
        zf_stats_clear(&S); arb_clear(sig); arb_clear(pi); acb_clear(z); acb_clear(dz); acb_clear(q);
    }
    return 0;
}
