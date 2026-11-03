/* zfast_selftest: THEORY_ZFAST section 11.1 (kernel) and 11.2 (phase).
   zfast_selftest kernel NRAND SEED
   zfast_selftest phase T0 u n0 B J */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "zfast.h"

static uint64_t sm(uint64_t *x) { uint64_t z = (*x += 0x9e3779b97f4a7c15ULL); z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL; z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL; return z ^ (z >> 31); }

static double errv(arb_t ref, double comp, arb_t tmp)
{
    arb_set_d(tmp, comp); arb_sub(tmp, tmp, ref, 128);
    mag_t m; mag_init(m); arb_get_mag(m, tmp); double d = mag_get_d(m); mag_clear(m); return d;
}

int main(int argc, char **argv)
{
    if (argc >= 4 && !strcmp(argv[1], "kernel"))
    {
        long nr = atol(argv[2]); uint64_t seed = strtoull(argv[3], 0, 10);
        arb_t x, c, s, tmp; arb_init(x); arb_init(c); arb_init(s); arb_init(tmp);
        double mc = 0, ms = 0; uint64_t vc = 0, vs = 0; long cnt = 0;
        /* boundary patterns */
        int64_t offs[] = { 0, 1, -1, 2, -2, (INT64_C(1) << 61), -(INT64_C(1) << 61), (INT64_C(1) << 61) - 1, -(INT64_C(1) << 61) + 1,
                           (INT64_C(1) << 60), -(INT64_C(1) << 60), (INT64_C(1) << 61) - 2, 12345, -12345 };
        long nb = sizeof offs / sizeof offs[0];
        for (long i = 0; i < 4 * nb + nr; i++)
        {
            uint64_t v;
            if (i < 4 * nb) v = ((uint64_t)(i / nb) << 62) + (uint64_t)offs[i % nb];
            else if (i < 4 * nb + nr / 4) { int64_t r = (int64_t)(sm(&seed) >> 2) - (INT64_C(1) << 61); v = (sm(&seed) & (UINT64_C(3) << 62)) + (uint64_t)((r >> (sm(&seed) % 60))); }
            else v = sm(&seed);
            double cc, ss; zf_cos2pi(&cc, &ss, v);
            /* x = 2 v / 2^64 = v / 2^63 ; cos(pi x) = cos(2 pi v/2^64) */
            arb_set_ui(x, v); arb_mul_2exp_si(x, x, -63);
            arb_sin_cos_pi(s, c, x, 128);
            double ec = errv(c, cc, tmp), es = errv(s, ss, tmp);
            if (ec > mc) { mc = ec; vc = v; }
            if (es > ms) { ms = es; vs = v; }
            cnt++;
        }
        printf("{\"test\": \"kernel\", \"count\": %ld, \"max_err_cos\": %.4e, \"argmax_cos\": \"%llu\", \"max_err_sin\": %.4e, \"argmax_sin\": \"%llu\", \"E_c\": 4.88e-16, \"pass\": %s}\n",
               cnt, mc, (unsigned long long)vc, ms, (unsigned long long)vs, (mc <= 4.88e-16 && ms <= 4.88e-16) ? "true" : "false");
        return 0;
    }
    if (argc >= 7 && !strcmp(argv[1], "phase"))
    {
        fmpz_t T0; fmpz_init(T0); fmpz_set_str(T0, argv[2], 10);
        double u = strtod(argv[3], 0); ulong n0 = strtoul(argv[4], 0, 10); long B = atol(argv[5]); int J = atoi(argv[6]);
        double mx, bd; zf_phase_test(&mx, &bd, T0, u, n0, B, J);
        printf("{\"test\": \"phase\", \"T0\": \"%s\", \"u\": %s, \"n0\": %lu, \"B\": %ld, \"J\": %d, \"max_err_turns\": %.4e, \"bound_turns\": %.4e, \"pass\": %s}\n",
               argv[2], argv[3], n0, B, J, mx, bd, mx <= bd ? "true" : "false");
        return 0;
    }
    fprintf(stderr, "usage\n"); return 2;
}
