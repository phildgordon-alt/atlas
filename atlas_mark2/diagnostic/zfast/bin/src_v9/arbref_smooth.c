/* arbref_smooth: Arb reference Z(T0+u) with low memory, for heights where stock Arb exceeds the 1 GB cap.
   Z = 2 Re( e^{i theta} ( acb_dirichlet_powsum_smooth(s, N) + corr ) ), s = 1/2 + it: the main sum is Arb's own
   (acb_dirichlet_powsum_smooth, prec 128 + bits(t)); theta = acb_dirichlet_hardy_theta; corr = zf_rs_corr (the copy of
   Arb's correction, validated against stock Arb at <= 1e15).  Lines "T0 u" on stdin. */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/resource.h>
#include <flint/acb_dirichlet.h>
#include "zfast.h"
int main(void)
{
    char T0s[200], us[200]; fmpz_t T0, N; fmpz_init(T0); fmpz_init(N);
    while (scanf("%199s %199s", T0s, us) == 2)
    {
        struct timespec a, b; clock_gettime(CLOCK_MONOTONIC, &a);
        fmpz_set_str(T0, T0s, 10); double u = strtod(us, 0);
        slong prec = 128 + fmpz_bits(T0);
        arb_t t; acb_t s, th, e, ps, corr; mag_t rb;
        arb_init(t); acb_init(s); acb_init(th); acb_init(e); acb_init(ps); acb_init(corr); mag_init(rb);
        zf_height(t, T0, u);
        acb_set_arb(s, t);
        acb_dirichlet_hardy_theta(th, s, NULL, NULL, 1, prec + 64);
        arb_sin_cos(acb_imagref(e), acb_realref(e), acb_realref(th), prec + 64);
        arb_set_d(acb_realref(s), 0.5); arb_set(acb_imagref(s), t);
        zf_rs_corr(corr, s, 8, 128, N, rb);
        acb_dirichlet_powsum_smooth(ps, s, fmpz_get_ui(N), 1, prec);
        acb_add(ps, ps, corr, prec);
        acb_mul(ps, ps, e, prec);
        arb_mul_2exp_si(acb_realref(ps), acb_realref(ps), 1);
        clock_gettime(CLOCK_MONOTONIC, &b);
        struct rusage ru; getrusage(RUSAGE_SELF, &ru);
        char *zs = arb_get_str(acb_realref(ps), 30, 0); char *mid = arf_get_str(arb_midref(acb_realref(ps)), 25);
        printf("{\"T0\": \"%s\", \"u\": \"%s\", \"Z\": \"%s\", \"Z_mid\": \"%s\", \"Z_rad\": %.6e, \"N\": %lu, \"sec\": %.3f, \"maxrss_mb\": %.1f, \"ref\": \"arb_powsum_smooth+zf_rs_corr\"}\n",
               T0s, us, zs, mid, mag_get_d(arb_radref(acb_realref(ps))), fmpz_get_ui(N), (b.tv_sec - a.tv_sec) + 1e-9 * (b.tv_nsec - a.tv_nsec), ru.ru_maxrss / 1048576.0);
        fflush(stdout); flint_free(zs); flint_free(mid);
        arb_clear(t); acb_clear(s); acb_clear(th); acb_clear(e); acb_clear(ps); acb_clear(corr); mag_clear(rb);
    }
    return 0;
}
