/* v14: SHA-256 of a session's complete state that determines every Z value / row (identity tests only; RESULTS_M9).
   Hashes Nw, nb, nhead, nbeg[], Lb[] (raw binary64), Xb[] and V[] (raw mag fields), and every moment (exact arb_dump_str).
   Included in zfast_m3b.inc (v14) and in the reference build ref13h.c (frozen v13b source + this file), so both hash identically. */
#include <CommonCrypto/CommonDigest.h>
static void h14_mag(CC_SHA256_CTX *c, const mag_t m)
{
    char *e = fmpz_get_str(NULL, 16, MAG_EXPREF(m)); char t[40]; snprintf(t, sizeof t, "%lx:", (unsigned long)MAG_MAN(m));
    CC_SHA256_Update(c, t, (CC_LONG)strlen(t)); CC_SHA256_Update(c, e, (CC_LONG)strlen(e)); CC_SHA256_Update(c, ";", 1); flint_free(e);
}
int zfm_hash14(const zfm_session *S, char *hex)
{
    CC_SHA256_CTX c; CC_SHA256_Init(&c); char t[128];
    snprintf(t, sizeof t, "Nw=%lu nb=%ld nhead=%lu nw=%d K2=%d;", (unsigned long)S->Nw, (long)S->nb, (unsigned long)S->nhead, S->nw, S->K2);
    CC_SHA256_Update(&c, t, (CC_LONG)strlen(t));
    CC_SHA256_Update(&c, S->nbeg, (CC_LONG)(sizeof(ulong) * (S->nb + 1)));
    CC_SHA256_Update(&c, S->Lb, (CC_LONG)(sizeof(double) * S->nb));
    for (slong b = 0; b < S->nb; b++) h14_mag(&c, S->Xb + b);
    for (slong a = 0; a < (slong)S->nw * S->nb; a++) h14_mag(&c, S->V + a);
    for (slong a = 0; a < (slong)S->nw * S->nb * S->K2; a++)
    {
        char *r = arb_dump_str(acb_realref(S->M + a)), *i = arb_dump_str(acb_imagref(S->M + a));
        CC_SHA256_Update(&c, r, (CC_LONG)strlen(r)); CC_SHA256_Update(&c, "|", 1); CC_SHA256_Update(&c, i, (CC_LONG)strlen(i)); CC_SHA256_Update(&c, ";", 1);
        flint_free(r); flint_free(i);
    }
    unsigned char d[CC_SHA256_DIGEST_LENGTH]; CC_SHA256_Final(d, &c);
    for (int k = 0; k < CC_SHA256_DIGEST_LENGTH; k++) sprintf(hex + 2 * k, "%02x", d[k]);
    hex[64] = 0;
    return 0;
}
