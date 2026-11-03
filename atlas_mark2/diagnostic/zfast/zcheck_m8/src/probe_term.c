/* M8 diagnostic: radius of one stock powsum term (and of arb_log_ui_from_prev) at k, prec, t = T. */
#include <stdio.h>
#include <stdlib.h>
#include <flint/acb.h>
#include <flint/acb_dirichlet.h>
int main(int argc, char **argv)
{
    fmpz_t T0; fmpz_init(T0); fmpz_set_str(T0, argv[1], 10); slong prec = atol(argv[2]);
    acb_t s, r; arb_t lp, l2; acb_init(s); acb_init(r); arb_init(lp); arb_init(l2);
    arb_set_d(acb_realref(s), 0.5); arb_set_fmpz(acb_imagref(s), T0);
    for (int i = 3; i < argc; i++) {
        ulong k = strtoul(argv[i], 0, 10), prev = k - 2;
        arb_log_ui(lp, prev, prec);
        acb_dirichlet_powsum_term(r, lp, &prev, s, k, 0, 1, 1, prec);
        arb_log_ui(l2, k, prec);
        printf("k=%lu prec=%ld term_rad=%.3e log_rad(from_prev)=%.3e log_rad(direct)=%.3e\n", k, prec,
               mag_get_d(arb_radref(acb_realref(r))), mag_get_d(arb_radref(lp)), mag_get_d(arb_radref(l2)));
    }
    return 0;
}
