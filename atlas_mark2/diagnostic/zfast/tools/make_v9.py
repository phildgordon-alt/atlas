"""Generates src/v9/ from src/ (the M2 working copy, frozen as bin/src_dev8).  New files only.
v9 = dev8 + (a) choose_B cap on the 256-bit rounding-propagation term, (b) pthread ranges for the fast parts of Z and rows,
(c) zfast_api.c (shared-library entry points for ctypes)."""
import re, os, shutil
S = '/Users/kiosk/atlas_mark2/diagnostic/zfast/src/'
D = S + 'v9/'
src = open(S + 'zfast.c').read()
assert open(S + 'zfast.c').read() == open('/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/src_dev8/zfast.c').read()
hdr = open(S + 'zfast.h').read()

# ---- header: threads parameter
hdr = hdr.replace("    int verbose;\n} zf_params;", "    int verbose;\n    int threads;        /* worker threads for the fast part (v9) */\n} zf_params;")
src = src.replace("P->J = 12; P->bmax = 1L << 14; P->log2_interp = -72.0; P->kcorr = 0; P->verbose = 0;",
                  "P->J = 12; P->bmax = 1L << 14; P->log2_interp = -72.0; P->kcorr = 0; P->verbose = 0; P->threads = 1;")
src = src.replace('#include "zfast.h"', '#include <pthread.h>\n#include "zfast.h"', 1)

# ---- (a) choose_B cap
old_cb = src[src.index("static long choose_B("):src.index("/* section 5: E[0] = fx(Theta")]
new_cb = '''static long choose_B(long n0, int J, double log2tau, const zf_params *P, long nmax)
{
    double l2r = (P->log2_interp + log2((double)(J + 1)) - log2tau) / (J + 1);
    double Bd = (double)n0 * pow(2.0, l2r);
    long B = Bd > (double)P->bmax ? P->bmax : (long)Bd;
    long Bmin = 2 * (J + 1) > 32 ? 2 * (J + 1) : 32;
    /* v9 cap: the rounding-propagation term sum_{i<=J} C(B-1,i) 2^-257 must stay <= 2^-80 (heuristic estimate
       log2((J+1) C(B-1,J)); the bound actually used is still computed rigorously in block_setup) */
    while (B > Bmin && B - 1 >= 2 * J)
    {
        double l2 = log2((double)(J + 1)) + (lgamma((double)B) - lgamma((double)J + 1.0) - lgamma((double)(B - J))) / log(2.0);
        if (l2 - 257.0 <= -80.0) break;
        B = (B * 3) / 4;
    }
    /* absorb a short tail into this block (the bound used is computed for the actual B) */
    if (B > nmax - n0 + 1 || nmax - n0 + 1 - B < Bmin) B = nmax - n0 + 1;
    return B;
}

'''
src = src.replace(old_cb, new_cb)

# ---- (b) Z: fast part as a range worker
i0 = src.index("    /* fast blocks */\n    t0 = now();\n    mag_zero(tot);")
i1 = src.index("    S->sec_fast = now() - t0;\n    S->blocks = nblocks;")
zbody = src[i0:i1]
zworker = '''typedef struct {
    const arb_struct *Theta, *tau; ulong n0, n1; slong wp; const zf_params *P;
    arb_t acc; mag_t tot; double maxph, nblocks;
} zrange_t;

/* fast blocks over [n0, n1] (n0 beyond the head); acc = sum of block sums, tot = sum of block bounds */
static void *z_range(void *arg)
{
    zrange_t *R = (zrange_t *)arg;
    const zf_params *P = R->P; int J = P->J; slong wp = R->wp;
    double log2tau = log2(arf_get_d(arb_midref(R->tau), ARF_RND_UP));
    arb_t x, L[JMAX + 1]; mag_t err, e1, tmp, tmp2, epsi[JMAX + 1]; fx E[JMAX + 1];
    arb_init(x); mag_init(err); mag_init(e1); mag_init(tmp); mag_init(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }
    arb_zero(R->acc); mag_zero(R->tot);
    double maxph = 0.0, nblocks = 0;
    const double u = 0x1p-53;
    ulong n = R->n0, N = R->n1;
    const arb_struct *Theta = R->Theta, *tau = R->tau;
    while (n <= N)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)N);
        if (B < J + 1) { fprintf(stderr, "block too short at n=%lu\\n", n); abort(); }
        block_setup(E, err, L, epsi, x, tmp, tmp2, Theta, tau, n, B, J, wp);
        double ph = mag_get_d(err);
        if (ph > maxph) maxph = ph;
        mag_mul_ui(e1, err, 7);
        mag_set_d(tmp, 3.03 * u + ZF_EC);
        mag_add(e1, e1, tmp);
        double ng = ceil((double)B / 16.0);
        mag_set_d(tmp, 15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.1 * u) + ng * ng * u * u * 2.0);
        mag_add(e1, e1, tmp);
        mag_set_ui(tmp, (ulong)B);
        mag_set_ui_lower(tmp2, n); mag_rsqrt(tmp2, tmp2);
        mag_mul(tmp, tmp, tmp2);
        mag_mul(e1, e1, tmp);
        mag_add(R->tot, R->tot, e1);
        double hi, lo;
        if (J == 12) block_kernel_Z12(&hi, &lo, E, (long)n, B);
        else block_kernel_Z(&hi, &lo, E, J, (long)n, B);
        arb_set_d(x, hi); arb_add(R->acc, R->acc, x, wp);
        arb_set_d(x, lo); arb_add(R->acc, R->acc, x, wp);
        n += (ulong)B;
        nblocks++;
    }
    R->maxph = maxph; R->nblocks = nblocks;
    arb_clear(x); mag_clear(err); mag_clear(e1); mag_clear(tmp); mag_clear(tmp2);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
    flint_cleanup();
    return NULL;
}

/* split [n0, N] into T contiguous ranges (each >= 4 bmax long) and run them */
static int split_ranges(ulong *lo, ulong *hi, ulong n0, ulong N, int T, long bmax)
{
    if (T < 1) T = 1;
    if (T > 16) T = 16;
    ulong len = N - n0 + 1;
    while (T > 1 && len / (ulong)T < (ulong)(4 * bmax)) T--;
    for (int i = 0; i < T; i++)
    {
        lo[i] = n0 + (len * (ulong)i) / (ulong)T;
        hi[i] = n0 + (len * (ulong)(i + 1)) / (ulong)T - 1;
    }
    return T;
}

'''
znew = '''    /* fast blocks (v9: T contiguous ranges, run in threads; each range is summed and bounded independently) */
    t0 = now();
    mag_zero(tot);
    double maxph = 0.0, nblocks = 0;
    if (n <= N)
    {
        ulong lo[16], hi[16];
        int T = split_ranges(lo, hi, n, N, P->threads, P->bmax);
        zrange_t R[16]; pthread_t th[16];
        for (int i = 0; i < T; i++)
        {
            R[i].Theta = Theta; R[i].tau = tau; R[i].n0 = lo[i]; R[i].n1 = hi[i]; R[i].wp = wp; R[i].P = P;
            arb_init(R[i].acc); mag_init(R[i].tot);
        }
        if (T == 1) z_range(&R[0]);
        else
        {
            for (int i = 0; i < T; i++) if (pthread_create(&th[i], NULL, z_range, &R[i])) { fprintf(stderr, "pthread_create\\n"); abort(); }
            for (int i = 0; i < T; i++) pthread_join(th[i], NULL);
        }
        for (int i = 0; i < T; i++)
        {
            arb_add(acc, acc, R[i].acc, wp); mag_add(tot, tot, R[i].tot);
            if (R[i].maxph > maxph) maxph = R[i].maxph;
            nblocks += R[i].nblocks;
            arb_clear(R[i].acc); mag_clear(R[i].tot);
        }
    }
'''
src = src[:i0] + znew + src[i1:]
src = src.replace("/* the main sum: res = sum_{n=1}^{N}", zworker + "/* the main sum: res = sum_{n=1}^{N}", 1)

# ---- (b) rows: fast part as a range worker
r0 = src.index("    double nb = 0, maxph = 0;\n    while (n <= N)\n    {\n        long B = choose_B((long)n, J, log2tau, P, (long)N);\n        if (B < J + 1) { fprintf(stderr, \"row block too short")
r1 = src.index("    St->sec_fast = now() - t0; St->blocks = nb;")
rloop = src[r0:r1]
rloop_body = rloop.replace("    double nb = 0, maxph = 0;\n", "")
rworker = '''typedef struct {
    const arb_struct *sigma, *tau; ulong n0, n1; slong wp; const zf_params *P;
    arb_t accr[8]; mag_t tot[8]; double maxph, nb;
} rrange_t;

static void *row_range(void *arg)
{
    rrange_t *Rr = (rrange_t *)arg;
    const zf_params *P = Rr->P; int J = P->J; slong wp = Rr->wp;
    const arb_struct *sigma = Rr->sigma, *tau = Rr->tau;
    double log2tau = log2(arf_get_d(arb_midref(tau), ARF_RND_UP));
    arb_t x, zero, c, L[JMAX + 1];
    mag_t err, tmp, tmp2, epsi[JMAX + 1], eA, mA, eW, mW, eL, mL;
    mag_struct *tot = Rr->tot[0]; (void)tot;
    fx E[JMAX + 1];
    arb_init(x); arb_init(zero); arb_init(c);
    mag_init(err); mag_init(tmp); mag_init(tmp2); mag_init(eA); mag_init(mA); mag_init(eW); mag_init(mW); mag_init(eL); mag_init(mL);
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }
    const double u = 0x1p-53;
    double nb = 0, maxph = 0;
    ulong n = Rr->n0, N = Rr->n1;
#define accr (Rr->accr)
#define tot (Rr->tot)
''' + rloop_body + '''#undef accr
#undef tot
    Rr->maxph = maxph; Rr->nb = nb;
    arb_clear(x); arb_clear(zero); arb_clear(c);
    mag_clear(err); mag_clear(tmp); mag_clear(tmp2); mag_clear(eA); mag_clear(mA); mag_clear(eW); mag_clear(mW); mag_clear(eL); mag_clear(mL);
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
    flint_cleanup();
    return NULL;
}

'''
rnew = '''    double nb = 0, maxph = 0;
    if (n <= N)
    {
        ulong lo[16], hi[16];
        int T = split_ranges(lo, hi, n, N, P->threads, P->bmax);
        rrange_t *R = flint_malloc(16 * sizeof(rrange_t)); pthread_t th[16];
        for (int i = 0; i < T; i++)
        {
            R[i].sigma = sigma; R[i].tau = tau; R[i].n0 = lo[i]; R[i].n1 = hi[i]; R[i].wp = wp; R[i].P = P;
            for (int m = 0; m < 8; m++) { arb_init(R[i].accr[m]); mag_init(R[i].tot[m]); }
        }
        if (T == 1) row_range(&R[0]);
        else
        {
            for (int i = 0; i < T; i++) if (pthread_create(&th[i], NULL, row_range, &R[i])) { fprintf(stderr, "pthread_create\\n"); abort(); }
            for (int i = 0; i < T; i++) pthread_join(th[i], NULL);
        }
        for (int i = 0; i < T; i++)
        {
            for (int m = 0; m < 8; m++) { arb_add(accr[m], accr[m], R[i].accr[m], wp); mag_add(tot[m], tot[m], R[i].tot[m]); arb_clear(R[i].accr[m]); mag_clear(R[i].tot[m]); }
            if (R[i].maxph > maxph) maxph = R[i].maxph;
            nb += R[i].nb;
        }
        flint_free(R);
    }
'''
src = src[:r0] + rnew + src[r1:]
src = src.replace("/* rigorous main sums: S[0] = sum n^-s", rworker + "/* rigorous main sums: S[0] = sum n^-s", 1)
os.makedirs(D, exist_ok=True)
for f in ['zfast.c', 'zfast.h']:
    assert not os.path.exists(D + f)
open(D + 'zfast.c', 'w').write(src)
open(D + 'zfast.h', 'w').write(hdr)
print('ok', len(src))
