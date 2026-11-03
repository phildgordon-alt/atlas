/* zfast_api14b.c (v14d, PREDICTIONS_M14: only "lib": "v14d" changes.)
   v14c, PREDICTIONS_M13: unchanged names and signatures; bad T0 now sets the error (mn5); info "lib": "v14c").
   v14b, PREDICTIONS_M12: ctypes API for v14b sessions with the hardened checkpoint (review_m10 M1, M2, m1-m4, m7).
   zfa14b_new: as zfa14_new plus role ("gen" | "replay"), a per-run nonce (32 lowercase hex), the HMAC key file path (created by the
   library for a new checkpoint, O_EXCL 0600; required for an existing one) and verify_n (loaded items recomputed on resume).
   NULL on any refusal; the reason is returned by zfa14b_last_error (same thread). */
#include <stdio.h>
#include <string.h>
#include "zfast.h"
void zfm_info(const zfm_session *S, double *sec_build, double *sec_head, double *sec_fast, double *nb, double *Nw, double *nhead, double *blocks, double *maxph);

void *zfa14b_new(const char *T0s, double u0, double H, double Delta, int K, int J, int threads, int workers, const char *ckpt,
                 const char *role, const char *nonce, const char *keyfile, int verify_n)
{
    zf_params P; zf_params_default(&P); if (J > 0) P.J = J;
    P.threads = threads;                                   /* v14b: no silent default / clamp (m7); zfm_new14b checks [1, 16] */
    fmpz_t T0; fmpz_init(T0);
    if (!T0s || fmpz_set_str(T0, T0s, 10) || fmpz_sgn(T0) < 0) { fmpz_clear(T0); zfm14c_set_error("T0 is not a non-negative decimal integer (refusing)"); return NULL; }
    zfm_session *S = zfm_new14b(T0, u0, H, &P, Delta, K, workers, ckpt, role, nonce, keyfile, verify_n);
    fmpz_clear(T0);
    return S;
}

int zfa14b_last_error(char *out, int outlen)
{
    int n = snprintf(out, outlen, "%s", zfm14b_last_error());
    return n >= outlen ? -2 : 0;
}

int zfa14b_info(void *s, char *out, int outlen)
{
    double sb, sh, sf, nb, Nw, nhd, bl, mp; zfm_info((zfm_session *)s, &sb, &sh, &sf, &nb, &Nw, &nhd, &bl, &mp);
    long it, il; int w, D, g; zfm_info14((zfm_session *)s, &it, &il, &w, &D, &g);
    char ck[2048]; if (zfm_info14b_ck((zfm_session *)s, ck, sizeof ck)) return -2;
    int n = snprintf(out, outlen, "{\"sec_build\": %.4f, \"sec_head\": %.4f, \"sec_fast\": %.4f, \"buckets\": %.0f, \"Nw\": %.0f, \"nhead\": %.0f, \"blocks\": %.0f, \"max_phase_err\": %.3e, "
                     "\"D\": %d, \"workers\": %d, \"items\": %ld, \"items_loaded\": %ld, \"generic_kernel\": %d, \"lib\": \"v14d\", %s}", sb, sh, sf, nb, Nw, nhd, bl, mp, D, w, it, il, g, ck);
    return n >= outlen ? -2 : 0;
}
