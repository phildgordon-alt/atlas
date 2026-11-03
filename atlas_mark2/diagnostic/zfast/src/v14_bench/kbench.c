/* M9 kernel microbenchmark + bitwise identity: v13b block_kernel_mom (generic) vs v14 block_kernel_mom_z20, same inputs. */
#include "../v14/zfast.c"
#include <stdint.h>
static uint64_t rs = 88172645463325252ULL;
static uint64_t xr(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
int main(int argc, char **argv)
{
    long B = argc > 1 ? atol(argv[1]) : 16384; int reps = argc > 2 ? atoi(argv[2]) : 200; long n0 = argc > 3 ? atol(argv[3]) : 4000000000L;
    double cx[7]; double cw[5][7]; double *cwt[5] = { cw[0], cw[1], cw[2], cw[3], cw[4] };
    double acc1[80], acc2[80]; long mism = 0; double t1 = 0, t2 = 0;
    for (int r = 0; r < reps; r++)
    {
        fx E0[13], Ea[13], Eb[13];
        for (int i = 0; i < 13; i++) for (int w = 0; w < 4; w++) E0[i].w[w] = xr();
        /* realistic small higher differences: sign-extended small values for i >= 3 */
        for (int i = 3; i < 13; i++) { int64_t v = (int64_t)(xr() >> (8 + 4 * i)); if (xr() & 1) v = -v; uint64_t ext = v < 0 ? ~0ULL : 0; E0[i].w[3] = ext; E0[i].w[2] = ext; E0[i].w[1] = (uint64_t)v; }
        double X = 0.5 * (double)(B - 1);
        cx[0] = ((double)(xr() >> 11) / 9007199254740992.0 - 0.5) * 0.006; cx[1] = 1.0 / (double)(n0 + X);
        for (int j = 2; j < 7; j++) cx[j] = cx[j - 1] / (double)(n0 + X) * (j % 2 ? 1 : -1) * (double)(j - 1) / j;
        memcpy(Ea, E0, sizeof E0); memcpy(Eb, E0, sizeof E0);
        double a = now(); block_kernel_mom(acc1, Ea, 12, n0, B, 1, 20, cwt, cx, 1); double b = now();
        block_kernel_mom_z20(acc2, Eb, n0, B, cx); double c = now();
        t1 += b - a; t2 += c - b;
        if (memcmp(acc1, acc2, sizeof(double) * 80) || memcmp(Ea, Eb, sizeof Ea)) mism++;
    }
    double terms = (double)B * reps;
    printf("{\"B\": %ld, \"reps\": %d, \"mismatch\": %ld, \"ns_per_term_v13b\": %.3f, \"ns_per_term_v14\": %.3f, \"speedup\": %.3f}\n", B, reps, mism, 1e9 * t1 / terms, 1e9 * t2 / terms, t1 / t2);
    return mism != 0;
}
