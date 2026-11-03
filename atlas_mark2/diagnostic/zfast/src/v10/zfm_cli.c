/* zfm_cli (M3): build one window session and evaluate points.
   zfm_cli T0 u0 H kind(z|row) a Delta K threads J   ; stdin: one offset u per line ; stdout: JSON per point (first line: session info) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include "zfast.h"
int main(int argc, char **argv)
{
    if (argc < 10) { fprintf(stderr, "usage: zfm_cli T0 u0 H z|row a Delta K threads J\n"); return 2; }
    fmpz_t T0; fmpz_init(T0); fmpz_set_str(T0, argv[1], 10);
    double u0 = strtod(argv[2], 0), H = strtod(argv[3], 0), a = strtod(argv[5], 0), Delta = strtod(argv[6], 0);
    int kind = !strcmp(argv[4], "row"), K = atoi(argv[7]);
    zf_params P; zf_params_default(&P); P.threads = atoi(argv[8]); P.J = atoi(argv[9]);
    arb_t sig, pi, h; arb_init(sig); arb_init(pi); arb_init(h);
    arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512); arb_set_d(h, 0.5); arb_add(sig, sig, h, 512);
    zfm_session *S = zfm_new(T0, u0, H, kind, sig, &P, Delta, K);
    double sb, sh, sf, nb, Nw, nhd, bl, mp; zfm_info(S, &sb, &sh, &sf, &nb, &Nw, &nhd, &bl, &mp);
    struct rusage ru; getrusage(RUSAGE_SELF, &ru);
    printf("{\"session\": 1, \"T0\": \"%s\", \"u0\": %s, \"H\": %g, \"kind\": \"%s\", \"a\": %g, \"Delta\": %g, \"K\": %d, \"threads\": %d, \"J\": %d, "
           "\"sec_build\": %.4f, \"sec_head\": %.4f, \"sec_fast\": %.4f, \"buckets\": %.0f, \"Nw\": %.0f, \"nhead\": %.0f, \"blocks\": %.0f, \"max_phase_err\": %.3e, \"maxrss_mb\": %.1f}\n",
           argv[1], argv[2], H, kind ? "row" : "z", a, Delta, K, P.threads, P.J, sb, sh, sf, nb, Nw, nhd, bl, mp, ru.ru_maxrss / 1048576.0);
    fflush(stdout);
    char us[200];
    arb_t Z; acb_t z, dz, q; arb_init(Z); acb_init(z); acb_init(dz); acb_init(q);
    while (scanf("%199s", us) == 1)
    {
        double u = strtod(us, 0);
        zf_stats St; zf_stats_init(&St);
        if (!kind)
        {
            zfm_Z(Z, S, u, &St);
            char *zs = arb_get_str(Z, 30, 0), *mid = arf_get_str(arb_midref(Z), 25);
            printf("{\"T0\": \"%s\", \"u\": \"%s\", \"Z\": \"%s\", \"Z_mid\": \"%s\", \"Z_rad\": %.6e, \"N\": %lu, \"sec_total\": %.5f, \"maxrss_mb\": 0}\n",
                   argv[1], us, zs, mid, mag_get_d(arb_radref(Z)), fmpz_get_ui(St.N), St.sec_total);
            flint_free(zs); flint_free(mid);
        }
        else
        {
            int ok = zfm_row(z, dz, S, u, &St);
            acb_div(q, dz, z, 256); acb_neg(q, q);
            char *s1 = arb_get_str(acb_realref(z), 25, 0), *s1i = arb_get_str(acb_imagref(z), 25, 0), *s2 = arb_get_str(acb_realref(dz), 25, 0), *s2i = arb_get_str(acb_imagref(dz), 25, 0), *s3 = arb_get_str(acb_realref(q), 25, 0);
            char *pm = arf_get_str(arb_midref(acb_realref(q)), 25);
            printf("{\"T0\": \"%s\", \"u\": \"%s\", \"a\": \"%s\", \"ok\": %d, \"zeta_re\": \"%s\", \"zeta_im\": \"%s\", \"dzeta_re\": \"%s\", \"dzeta_im\": \"%s\", \"P\": \"%s\", \"P_mid\": \"%s\", \"P_rad\": %.4e, \"N\": %lu, \"sec_total\": %.5f, \"maxrss_mb\": 0}\n",
                   argv[1], us, argv[5], ok, s1, s1i, s2, s2i, s3, pm, mag_get_d(arb_radref(acb_realref(q))), fmpz_get_ui(St.N), St.sec_total);
            flint_free(s1); flint_free(s1i); flint_free(s2); flint_free(s2i); flint_free(s3); flint_free(pm);
        }
        fflush(stdout); zf_stats_clear(&St);
    }
    zfm_free(S);
    return 0;
}
