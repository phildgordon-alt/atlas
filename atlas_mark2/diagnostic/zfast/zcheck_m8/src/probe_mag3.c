/* M8 diagnostic: growth of an arb sum's radius over n sequential arb_add of terms with small radius (mag_t rounds up). */
#include <stdio.h>
#include <stdlib.h>
#include <flint/arb.h>
int main(int argc, char **argv)
{
    long n = atol(argv[1]); slong prec = atol(argv[2]); double trad = atof(argv[3]);
    arb_t s, t; arb_init(s); arb_init(t); arb_set_d(s, 1000.0); mag_set_d(arb_radref(s), 1e-30);
    flint_rand_t st; flint_rand_init(st);
    for (long i = 1; i <= n; i++) {
        arb_const_pi(t, prec); arb_mul_si(t, t, (i % 7 - 3), prec); arb_mul_2exp_si(t, t, -20); mag_set_d(arb_radref(t), trad);
        arb_add(s, s, t, prec);
        if ((i & (i - 1)) == 0 && i >= (1L << 20)) printf("adds=%ld rad=%.4e  rad/(adds*trad)=%.4e\n", i, mag_get_d(arb_radref(s)), mag_get_d(arb_radref(s)) / (i * trad));
    }
    printf("final adds=%ld rad=%.4e predicted_linear=%.4e\n", n, mag_get_d(arb_radref(s)), n * trad);
    return 0;
}
