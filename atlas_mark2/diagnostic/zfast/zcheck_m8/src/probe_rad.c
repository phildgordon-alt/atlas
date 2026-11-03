/* M8 diagnostic probe: radius of stock acb_dirichlet_powsum_smooth(1/2 + i t, N) vs N, prec, t. Stock FLINT only. */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <flint/acb.h>
#include <flint/acb_dirichlet.h>
int main(int argc, char **argv)
{
    const char *T = argv[1]; ulong N = strtoul(argv[2], 0, 10); slong prec = atol(argv[3]); int which = argc > 4 ? atoi(argv[4]) : 0;
    fmpz_t T0; fmpz_init(T0); fmpz_set_str(T0, T, 10);
    acb_t s, r; acb_init(s); acb_init(r);
    arb_set_d(acb_realref(s), 0.5); arb_set_fmpz(acb_imagref(s), T0);
    struct timespec a, b; clock_gettime(CLOCK_MONOTONIC, &a);
    if (which == 0) acb_dirichlet_powsum_smooth(r, s, N, 1, prec);
    else acb_dirichlet_powsum_sieved(r, s, N, 1, prec);
    clock_gettime(CLOCK_MONOTONIC, &b);
    printf("T=%s N=%lu prec=%ld %s rad_re=%.3e mid_re=%.6e sec=%.2f\n", T, N, prec, which ? "sieved" : "smooth",
           mag_get_d(arb_radref(acb_realref(r))), arf_get_d(arb_midref(acb_realref(r)), ARF_RND_NEAR),
           (b.tv_sec - a.tv_sec) + 1e-9 * (b.tv_nsec - a.tv_nsec));
    return 0;
}
