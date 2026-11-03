/* zfast_api14.c (v14, RESULTS_M9): ctypes API for v14 sessions.  Every v13b entry point (zfa3_*, zfa4_*) is kept unchanged in
   zfast_api3.c / zfast_api4.c; zfa4_new keeps v13b semantics (workers = threads, no checkpoint). */
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include "zfast.h"

/* threads = decomposition D (recorded session parameter; output depends on it exactly as in v13b); workers = OS threads (output does
   not depend on it); ckpt = checkpoint path or "" */
void *zfa14_new(const char *T0s, double u0, double H, double Delta, int K, int J, int threads, int workers, const char *ckpt)
{
    zf_params P; zf_params_default(&P); if (J > 0) P.J = J; if (threads > 0) P.threads = threads;
    fmpz_t T0; fmpz_init(T0);
    if (fmpz_set_str(T0, T0s, 10)) { fmpz_clear(T0); return NULL; }
    zfm_session *S = zfm_new14(T0, u0, H, &P, Delta, K, workers, ckpt);
    fmpz_clear(T0);
    return S;
}

int zfa14_info(void *s, char *out, int outlen)
{
    double sb, sh, sf, nb, Nw, nhd, bl, mp; zfm_info((zfm_session *)s, &sb, &sh, &sf, &nb, &Nw, &nhd, &bl, &mp);
    long it, il; int w, D, g; zfm_info14((zfm_session *)s, &it, &il, &w, &D, &g);
    int n = snprintf(out, outlen, "{\"sec_build\": %.4f, \"sec_head\": %.4f, \"sec_fast\": %.4f, \"buckets\": %.0f, \"Nw\": %.0f, \"nhead\": %.0f, \"blocks\": %.0f, \"max_phase_err\": %.3e, "
                     "\"D\": %d, \"workers\": %d, \"items\": %ld, \"items_loaded\": %ld, \"generic_kernel\": %d, \"lib\": \"v14\"}", sb, sh, sf, nb, Nw, nhd, bl, mp, D, w, it, il, g);
    return n >= outlen ? -2 : 0;
}

int zfa14_hash(void *s, char *out, int outlen)
{
    if (outlen < 65) return -2;
    return zfm_hash14((zfm_session *)s, out);
}

/* Z on a grid (exactly zfa3_Zgrid's per-point computation), points split over `workers` threads (k = t mod workers).  Each point is
   computed independently from the read-only session, so the output is identical to zfa3_Zgrid for every workers. */
typedef struct { zfm_session *S; double u_start, step; long n; double *mid, *rad, *uout; int t, W; } zg_t;
static void *zg_worker(void *arg)
{
    zg_t *G = (zg_t *)arg; arb_t Z; arb_init(Z);
    for (long k = G->t; k < G->n; k += G->W)
    {
        double u = G->u_start + (double)k * G->step; G->uout[k] = u;
        zf_stats St; zf_stats_init(&St);
        zfm_Z(Z, G->S, u, &St);
        double m = arf_get_d(arb_midref(Z), ARF_RND_NEAR);
        arb_t d; arb_init(d); arb_set_d(d, m); arb_sub(d, Z, d, 128);
        mag_t r; mag_init(r); arb_get_mag(r, d);
        G->mid[k] = m; G->rad[k] = mag_get_d(r);
        mag_clear(r); arb_clear(d); zf_stats_clear(&St);
    }
    arb_clear(Z); flint_cleanup();
    return NULL;
}
int zfa14_Zgrid(void *s, double u_start, double step, long n, double *mid, double *rad, double *uout, int workers)
{
    if (workers < 1) workers = 1;
    if (workers > 64) workers = 64;
    zg_t G[64]; pthread_t th[64];
    for (int t = 0; t < workers; t++) { G[t] = (zg_t){ (zfm_session *)s, u_start, step, n, mid, rad, uout, t, workers }; if (pthread_create(&th[t], NULL, zg_worker, &G[t])) return -1; }
    for (int t = 0; t < workers; t++) pthread_join(th[t], NULL);
    return 0;
}
