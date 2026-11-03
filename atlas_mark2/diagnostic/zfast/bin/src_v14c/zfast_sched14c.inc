/* ===================== v14c: work-queue scheduler (= v14) and checkpoint/resume v3 (review_v14b MJ1, mn1-mn7; PREDICTIONS_M13) =====================
   Included in zfast_m3b.inc just before zfm_build.  OUTPUT CONTRACT (bit-identity with v14 = v13b at equal D): unchanged from v14/v14b:
   - the items are EXACTLY v13b's (buckets in order, split_ranges(.., D, bmax)); item (b, i) runs mom_range on [lo_i, hi_i];
   - the merge is EXACTLY v13b's (per bucket, items in index order, the same acb_add / arb_add_error_mag / mag_add calls);
   - only WHO computes an item and WHEN changes (W workers, longest first).
   Everything of v14b (zfast_sched14b.inc) is kept (M1 prefast / environment pins, M2 role + nonce, m1 HMAC + strict parser + resume
   sample recompute, m2 index checks, m3 checked writes, m4 flock).  What v14c changes (PREDICTIONS_M13 section 0):
   MJ1 format ZFAST14C CKPT v3.  A new header carries a fresh random hnonce; header seal = HMAC(K, "ZF14C-HDR\0" || header_body); item
       line `I x b i lo hi ...` (x = global item index) seal = HMAC(K, "ZF14C-ITEM\0" || SHA-256(header_body) || u64be(x) || line_body),
       so a line authenticates only under the header (session file) and position it was written for.  Any second authenticated line for
       a loaded item is FATAL (identical or conflicting duplicate).  A new header under an existing key is allowed (the crash between key
       creation and header write recovers), is reported (key_reused_new_header, stderr) and cannot splice (fresh hnonce).
   mn1 the four arb tokens are pre-validated before arb_load_str (zero mantissa => exactly "0 0"; no leading zeros; unsigned radius).
   mn2 a flusher thread F_FULLFSYNCs every 1.0 s while lines are unsynced, independent of item completion; max_unsynced_s measured.
   mn3 header adds dyld shared-cache UUID, hw.model, LC_UUID of each loaded image (bin, flint, gmp, mpfr, libm) and the SHA-256 of the
       zfast image's in-memory __TEXT; any unavailable field refuses (no placeholder values).
   mn4 key creation temp + F_FULLFSYNC + renamex_np(RENAME_EXCL) + directory fsync; an existing key must be a regular, non-symlink,
       euid-owned, mode-0600-or-stricter, 32-byte file (a 0-byte key is refused with its own reason, never overwritten).
   mn5 worker write/fsync errors are kept in the session and surfaced in zfa14b_last_error on the creating thread.
   mn6 bounded line reader (overlong lines are skipped unstored and counted).
   (mn7 is the pipeline's verify default, atlas_v5z9.) */
#include <CommonCrypto/CommonDigest.h>
#include <CommonCrypto/CommonHMAC.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdarg.h>
#include <stdbool.h>
#include <dlfcn.h>
#include <libgen.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <sys/time.h>
#include <mach-o/loader.h>
#include <uuid/uuid.h>
#include <gmp.h>
#include <mpfr.h>
extern bool _dyld_get_shared_cache_uuid(uuid_t uuid);       /* libdyld (exported; declared in the private dyld_priv.h) */

#define ZF14B_LIB_ID "zfast-v14c(PREDICTIONS_M13)"
#ifdef ZF_TEST_HOOKS
#define ZF14B_HOOKS 1
#else
#define ZF14B_HOOKS 0
#endif

/* ---------- error reporting (per thread; read by zfa14b_last_error) ---------- */
static __thread char zf14b_err[2048];
static void zf14b_seterr(const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vsnprintf(zf14b_err, sizeof zf14b_err, fmt, ap); va_end(ap);
    fprintf(stderr, "zfast14b: %s\n", zf14b_err);
}
const char *zfm14b_last_error(void) { return zf14b_err; }
void zfm14c_set_error(const char *msg) { zf14b_seterr("%s", msg); }      /* v14c (mn5): lets the API set a reason (bad T0) */

typedef struct { const char *path, *role, *nonce, *keyfile; int verify_n; } zf_ckcfg_t;

typedef struct { slong b; int i, T; ulong lo, hi; mrange_t R; int done, loaded; } witem_t;

typedef struct {
    zfm_session *S; witem_t *it; long nit; long *order; long nord, next;
    int *left;                      /* per bucket: items not yet finished */
    long *first;                    /* per bucket: index of its first item (-1 if none) */
    pthread_mutex_t mu, io;
    int fd; unsigned char key[32]; long computed, exit_after, written, werr, syncs; double maxph, nblocks, last_sync;
    /* v14c */
    unsigned char hh[32];           /* MJ1: SHA-256 of this checkpoint's header body (binds every item line to it) */
    unsigned char *lhash;           /* MJ1: per item, SHA-256 of its loaded authenticated line body (duplicate classification) */
    char werrmsg[512];              /* mn5: first write/fsync error (any thread) */
    double dirty_since, max_unsynced;   /* mn2: write time of the oldest unsynced line (0 = clean); largest observed write-to-sync age */
    pthread_cond_t fcv; int fstop;  /* mn2: flusher thread */
} wq_t;

static void hex_of(char *out, const unsigned char *d, int n)
{
    static const char hx[] = "0123456789abcdef";
    for (int i = 0; i < n; i++) { out[2 * i] = hx[d[i] >> 4]; out[2 * i + 1] = hx[d[i] & 15]; }
    out[2 * n] = 0;
}

/* v14c (MJ1): domain-separated seals.  Header: HMAC(K, "ZF14C-HDR\0" || body).  Item: HMAC(K, "ZF14C-ITEM\0" || hh || u64be(x) || body). */
static void seal_hdr_hex(char *out, const unsigned char *key, const char *body, size_t len)
{
    unsigned char d[CC_SHA256_DIGEST_LENGTH]; CCHmacContext c; CCHmacInit(&c, kCCHmacAlgSHA256, key, 32);
    CCHmacUpdate(&c, "ZF14C-HDR", 10); CCHmacUpdate(&c, body, len); CCHmacFinal(&c, d); hex_of(out, d, CC_SHA256_DIGEST_LENGTH);
}
static void seal_item_hex(char *out, const unsigned char *key, const unsigned char *hh, unsigned long x, const char *body, size_t len)
{
    unsigned char d[CC_SHA256_DIGEST_LENGTH], xb[8]; for (int k = 0; k < 8; k++) xb[k] = (unsigned char)(x >> (56 - 8 * k));
    CCHmacContext c; CCHmacInit(&c, kCCHmacAlgSHA256, key, 32);
    CCHmacUpdate(&c, "ZF14C-ITEM", 11); CCHmacUpdate(&c, hh, 32); CCHmacUpdate(&c, xb, 8); CCHmacUpdate(&c, body, len);
    CCHmacFinal(&c, d); hex_of(out, d, CC_SHA256_DIGEST_LENGTH);
}
/* constant-time comparison of two 64-hex tags (review nit) */
static int tag_eq(const char *a, const char *b) { unsigned char v = 0; for (int k = 0; k < 64; k++) v |= (unsigned char)(a[k] ^ b[k]); return v == 0; }

/* mn5: a checkpoint I/O error from any thread: stderr now, first message kept for the creating thread */
static void ck_err(wq_t *Q, const char *fmt, ...)
{
    char m[512]; va_list ap; va_start(ap, fmt); vsnprintf(m, sizeof m, fmt, ap); va_end(ap);
    fprintf(stderr, "zfast14c: %s\n", m);
    if (!Q->werrmsg[0]) snprintf(Q->werrmsg, sizeof Q->werrmsg, "%s", m);
}

/* growable string */
typedef struct { char *s; size_t n, cap; } sbuf_t;
static void sb_addn(sbuf_t *b, const char *t, size_t l)
{
    if (b->n + l + 1 > b->cap) { b->cap = 2 * (b->n + l + 1); b->s = flint_realloc(b->s, b->cap); }
    memcpy(b->s + b->n, t, l); b->n += l; b->s[b->n] = 0;
}
static void sb_add(sbuf_t *b, const char *t) { sb_addn(b, t, strlen(t)); }
static void sb_mag(sbuf_t *b, const mag_t m)
{
    char tmp[64]; char *e = fmpz_get_str(NULL, 16, MAG_EXPREF(m));
    snprintf(tmp, sizeof tmp, " %lx:", (unsigned long)MAG_MAN(m)); sb_add(b, tmp); sb_add(b, e); flint_free(e);
}

/* ---------- M1: pre-fast digest and environment identity ---------- */
static void mag_feed(CC_SHA256_CTX *c, const mag_t m)
{
    char *e = fmpz_get_str(NULL, 16, MAG_EXPREF(m)); char t[40]; snprintf(t, sizeof t, "%lx:", (unsigned long)MAG_MAN(m));
    CC_SHA256_Update(c, t, (CC_LONG)strlen(t)); CC_SHA256_Update(c, e, (CC_LONG)strlen(e)); CC_SHA256_Update(c, ";", 1); flint_free(e);
}
static void prefast_digest(const zfm_session *S, char *hex)
{
    CC_SHA256_CTX c; CC_SHA256_Init(&c); char t[160];
    snprintf(t, sizeof t, "prefast v1 nb=%ld Nw=%lu nhead=%lu wp=%ld K2=%d nw=%d;", (long)S->nb, (unsigned long)S->Nw, (unsigned long)S->nhead, (long)S->wp, S->K2, S->nw);
    CC_SHA256_Update(&c, t, (CC_LONG)strlen(t));
    CC_SHA256_Update(&c, S->nbeg, (CC_LONG)(sizeof(ulong) * (S->nb + 1)));
    CC_SHA256_Update(&c, S->Lb, (CC_LONG)(sizeof(double) * S->nb));
    for (slong b = 0; b < S->nb; b++) mag_feed(&c, S->Xb + b);
    char *ts = arb_dump_str(S->tau0); CC_SHA256_Update(&c, ts, (CC_LONG)strlen(ts)); flint_free(ts);
    unsigned char d[CC_SHA256_DIGEST_LENGTH]; CC_SHA256_Final(d, &c); hex_of(hex, d, CC_SHA256_DIGEST_LENGTH);
}

static int file_sha(const char *path, char *hex)
{
    int fd = open(path, O_RDONLY | O_CLOEXEC); if (fd < 0) return -1;
    CC_SHA256_CTX c; CC_SHA256_Init(&c); char *buf = flint_malloc(1 << 20); ssize_t r;
    while ((r = read(fd, buf, 1 << 20)) > 0) CC_SHA256_Update(&c, buf, (CC_LONG)r);
    flint_free(buf); close(fd);
    if (r < 0) return -1;
    unsigned char d[CC_SHA256_DIGEST_LENGTH]; CC_SHA256_Final(d, &c); hex_of(hex, d, CC_SHA256_DIGEST_LENGTH);
    return 0;
}

/* header-safe value: no space, '#', '=' or control characters */
static void sb_val(sbuf_t *h, const char *key, const char *v)
{
    sb_add(h, " "); sb_add(h, key); sb_add(h, "=");
    char tmp[512]; size_t n = 0;
    for (const char *p = v; *p && n < sizeof tmp - 1; p++) tmp[n++] = (*p == ' ' || *p == '#' || *p == '=' || (unsigned char)*p < 33) ? '_' : *p;
    tmp[n] = 0; sb_add(h, n ? tmp : "_");
}
/* v14c (mn3): every environment field is either determined or the checkpoint is refused; no placeholder value exists.
   Test-hooks build only: env ZFAST14C_TEST_ENVFAIL=<field> forces that field to be unavailable (A4). */
static int env_fail_hook(const char *field)
{
#ifdef ZF_TEST_HOOKS
    const char *g = getenv("ZFAST14C_TEST_ENVFAIL"); if (g && !strcmp(g, field)) return 1;
#endif
    (void)field; return 0;
}
static int env_unavail(char *why, size_t wl, const char *field, const char *what)
{
    snprintf(why, wl, "environment identity unavailable: %s (%s)", field, what); return -1;
}
/* LC_UUID of the loaded image containing sym */
static int image_uuid(const void *sym, char *out37, const struct mach_header_64 **mhp)
{
    Dl_info di; if (!dladdr(sym, &di) || !di.dli_fbase) return -1;
    const struct mach_header_64 *mh = (const struct mach_header_64 *)di.dli_fbase; if (mh->magic != MH_MAGIC_64) return -1;
    const char *p = (const char *)(mh + 1);
    for (uint32_t k = 0; k < mh->ncmds; k++)
    {
        const struct load_command *lc = (const struct load_command *)p;
        if (lc->cmd == LC_UUID) { uuid_unparse_lower(((const struct uuid_command *)lc)->uuid, out37); if (mhp) *mhp = mh; return 0; }
        p += lc->cmdsize;
    }
    return -1;
}
/* SHA-256 of the image's in-memory __TEXT segment (the code actually mapped in this process) */
static int image_text_sha(const struct mach_header_64 *mh, char *hex)
{
    const char *p = (const char *)(mh + 1);
    for (uint32_t k = 0; k < mh->ncmds; k++)
    {
        const struct load_command *lc = (const struct load_command *)p;
        if (lc->cmd == LC_SEGMENT_64 && !strncmp(((const struct segment_command_64 *)lc)->segname, "__TEXT", 16))
        {
            const struct segment_command_64 *sg = (const struct segment_command_64 *)lc;
            if (sg->fileoff != 0 || sg->filesize == 0) return -1;
            unsigned char d[CC_SHA256_DIGEST_LENGTH]; CC_SHA256((const void *)mh, (CC_LONG)sg->filesize, d); hex_of(hex, d, CC_SHA256_DIGEST_LENGTH);
            return 0;
        }
        p += lc->cmdsize;
    }
    return -1;
}
/* key_sha (file at the dladdr path), key_uuid (LC_UUID of the loaded image); file_too = 0 for images in the dyld shared cache */
static int sb_image(sbuf_t *h, const char *key, const void *sym, int file_too, char *why, size_t wl)
{
    Dl_info di; char hex[65], u[37], k2[64];
    if (env_fail_hook(key) || !dladdr(sym, &di) || !di.dli_fname || !di.dli_fname[0]) return env_unavail(why, wl, key, "dladdr");
    if (file_too)
    {
        if (file_sha(di.dli_fname, hex)) return env_unavail(why, wl, key, "image file unreadable");
        snprintf(k2, sizeof k2, "%s_sha", key); sb_val(h, k2, hex);
    }
    if (image_uuid(sym, u, NULL)) return env_unavail(why, wl, key, "no LC_UUID");
    snprintf(k2, sizeof k2, "%s_uuid", key); sb_val(h, k2, u);
    return 0;
}
static int ckpt_env_fields(sbuf_t *h, char *why, size_t wl)
{
    char tmp[256];
    snprintf(tmp, sizeof tmp, "%s/%s", ZF14B_LIB_ID, __VERSION__); sb_val(h, "lib", tmp);
    if (sb_image(h, "bin", (const void *)&zfm14b_last_error, 1, why, wl)) return -1;
    {
        char u[37], hx[65]; const struct mach_header_64 *mh = NULL;
        if (env_fail_hook("bin_text") || image_uuid((const void *)&zfm14b_last_error, u, &mh) || image_text_sha(mh, hx)) return env_unavail(why, wl, "bin_text", "__TEXT");
        sb_val(h, "bin_text_sha", hx);
    }
    sb_val(h, "flint", flint_version); if (sb_image(h, "flint", (const void *)&arb_add, 1, why, wl)) return -1;
    sb_val(h, "gmp", gmp_version); if (sb_image(h, "gmp", (const void *)&__gmpz_init, 1, why, wl)) return -1;
    sb_val(h, "mpfr", mpfr_get_version()); if (sb_image(h, "mpfr", (const void *)&mpfr_init2, 1, why, wl)) return -1;
    { double (*lg)(double) = log; if (sb_image(h, "libm", (const void *)lg, 0, why, wl)) return -1; }
    {
        uuid_t cu; char u[37];
        if (env_fail_hook("dyld_cache_uuid") || !_dyld_get_shared_cache_uuid(cu)) return env_unavail(why, wl, "dyld_cache_uuid", "_dyld_get_shared_cache_uuid");
        uuid_unparse_lower(cu, u); sb_val(h, "dyld_cache_uuid", u);
    }
    char os[128]; size_t ol = sizeof os;
    if (env_fail_hook("os") || sysctlbyname("kern.osversion", os, &ol, NULL, 0) || ol < 2) return env_unavail(why, wl, "os", "kern.osversion");
    sb_val(h, "os", os);
    char hw[128]; size_t hl = sizeof hw;
    if (env_fail_hook("hw_model") || sysctlbyname("hw.model", hw, &hl, NULL, 0) || hl < 2) return env_unavail(why, wl, "hw_model", "hw.model");
    sb_val(h, "hw_model", hw);
    snprintf(tmp, sizeof tmp, "%d", ZF14B_HOOKS); sb_val(h, "hooks", tmp);
    return 0;
}

/* the expected header body (without hnonce); -1 (why set) if the environment identity is unavailable */
static int ckpt_header(sbuf_t *h, const zfm_session *S, long nit, const zf_ckcfg_t *ck, char *why, size_t wl)
{
    char tmp[600]; char *t0 = fmpz_get_str(NULL, 10, S->T0); char pf[65]; prefast_digest(S, pf);
    snprintf(tmp, sizeof tmp, "ZFAST14C CKPT v3 role=%s nonce=%s T0=", ck->role, ck->nonce); sb_add(h, tmp); sb_add(h, t0); flint_free(t0);
    snprintf(tmp, sizeof tmp, " u0=%a H=%a Delta=%a K=%d J=%d D=%d kind=%d bmax=%ld interp=%a Nw=%lu nb=%ld nhead=%lu nitems=%ld wp=%ld prefast=%s",
             S->u0, S->H, S->Delta, S->K, S->P.J, S->P.threads, S->kind, S->P.bmax, S->P.log2_interp, (unsigned long)S->Nw, (long)S->nb,
             (unsigned long)S->nhead, nit, (long)S->wp, pf);
    sb_add(h, tmp);
    return ckpt_env_fields(h, why, wl);
}

/* compare a stored header with ours token by token; writes the mismatching keys into out; returns number of mismatches */
static int header_diff(const char *have, const char *want, char *out, size_t outlen)
{
    int nm = 0; out[0] = 0;
    const char *a = have, *b = want;
    for (int tok = 0; ; tok++)
    {
        while (*a == ' ') a++;
        while (*b == ' ') b++;
        if (!*a && !*b) break;
        const char *ae = a, *be = b; while (*ae && *ae != ' ') ae++;
        while (*be && *be != ' ') be++;
        if (ae - a != be - b || memcmp(a, b, ae - a))
        {
            const char *eq = memchr(b, '=', be - b); int kl = eq ? (int)(eq - b) : (int)(be - b);
            if (!*b || tok < 3) { snprintf(out, outlen, "format"); return 99; }
            if (strlen(out) + kl + 2 < outlen) { if (nm) strcat(out, ","); strncat(out, b, kl); }
            nm++;
        }
        a = ae; b = be;
        if (!*a != !*b) { if (strlen(out) + 12 < outlen) strcat(out, nm ? ",fieldcount" : "fieldcount"); return nm + 1; }
    }
    return nm;
}

/* ---------- item lines ---------- */
static void item_line(sbuf_t *L, const zfm_session *S, const witem_t *w, long x)
{
    char tmp[256]; int na = S->nw * S->K2;
    snprintf(tmp, sizeof tmp, "I %ld %ld %d %lu %lu %a %a", x, (long)w->b, w->i, (unsigned long)w->lo, (unsigned long)w->hi, w->R.nblocks, w->R.maxph);
    sb_add(L, tmp);
    for (int a = 0; a < na; a++)
    {
        char *r = arb_dump_str(acb_realref(w->R.M + a)), *im = arb_dump_str(acb_imagref(w->R.M + a));
        sb_add(L, " "); sb_add(L, r); sb_add(L, " "); sb_add(L, im); flint_free(r); flint_free(im);
    }
    for (int a = 0; a < na; a++) sb_mag(L, w->R.err + a);
    for (int j = 0; j < S->nw; j++) sb_mag(L, w->R.V + j);
}

/* strict tokenizer: single spaces between tokens; returns token length (0 at end) */
static size_t next_tok(const char **p, const char **start)
{
    const char *s = *p;
    if (*s == ' ') s++;
    *start = s; while (*s && *s != ' ') s++;
    *p = s; return (size_t)(s - *start);
}
static int is_hex(const char *s, size_t n, int allow_sign)
{
    if (n && allow_sign && s[0] == '-') { s++; n--; }
    if (!n) return 0;
    for (size_t i = 0; i < n; i++) if (!((s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'f'))) return 0;
    return 1;
}
static int parse_dec_ul(const char *s, size_t n, unsigned long *v)
{
    if (!n || n > 20) return 0;
    unsigned long x = 0;
    for (size_t i = 0; i < n; i++) { if (s[i] < '0' || s[i] > '9') return 0; unsigned d = s[i] - '0'; if (x > (ULONG_MAX - d) / 10) return 0; x = 10 * x + d; }
    if (n > 1 && s[0] == '0') return 0;
    *v = x; return 1;
}
static int parse_hexdouble(const char *s, size_t n, double *v)
{
    char t[64]; if (!n || n >= sizeof t) return 0;
    memcpy(t, s, n); t[n] = 0; char *e; double x = strtod(t, &e);
    if (*e || !isfinite(x) || x < 0) return 0;
    char c[64]; snprintf(c, sizeof c, "%a", x); if (strcmp(c, t)) return 0;     /* canonical */
    *v = x; return 1;
}
/* a normalised finite mag: zero (man 0, exp 0) or 2^(MAG_BITS-1) <= man < 2^MAG_BITS, |exp| < 2^40 */
static int mag_valid(const mag_t m)
{
    if (MAG_MAN(m) == 0) return fmpz_is_zero(MAG_EXPREF(m));
    if (MAG_MAN(m) < (UWORD(1) << (MAG_BITS - 1)) || MAG_MAN(m) >= (UWORD(1) << MAG_BITS)) return 0;
    return fmpz_bits(MAG_EXPREF(m)) <= 40;
}
static int parse_mag_strict(mag_t m, const char **p)
{
    const char *s; size_t n = next_tok(p, &s);
    const char *colon = memchr(s, ':', n); if (!colon) return 0;
    size_t nm = colon - s, ne = n - nm - 1;
    if (!is_hex(s, nm, 0) || nm > 16 || !is_hex(colon + 1, ne, 1)) return 0;
    char t[80]; if (ne >= sizeof t) return 0;
    memcpy(t, s, nm); t[nm] = 0; unsigned long man = strtoul(t, NULL, 16);
    memcpy(t, colon + 1, ne); t[ne] = 0; if (fmpz_set_str(MAG_EXPREF(m), t, 16)) return 0;
    MAG_MAN(m) = (mp_limb_t)man;
    if (!mag_valid(m)) return 0;
    sbuf_t c = { 0 }; sb_mag(&c, m); int ok = c.n == n + 1 && !memcmp(c.s + 1, s, n); flint_free(c.s);    /* canonical */
    return ok;
}
/* v14c (mn1): a hex integer token in canonical form: optional '-' (only if allow_sign), no leading zero, "-0" not allowed */
static int canon_hex_int(const char *s, size_t n, int allow_sign)
{
    if (n && s[0] == '-') { if (!allow_sign) return 0; s++; n--; if (n == 1 && s[0] == '0') return 0; }
    if (!is_hex(s, n, 0)) return 0;
    return !(n > 1 && s[0] == '0');
}
/* arb_dump_str = 4 hex tokens (mid man, mid exp, rad man, rad exp); must be finite and canonical.
   v14c (mn1): the tokens are pre-validated BEFORE arb_load_str, which aborts the process (FLINT exception in
   arf_set_fmpz_2exp_dump) on a zero mantissa with an exponent other than 0..3: a zero mantissa must come with exponent exactly 0 (a
   finite zero), the radius mantissa is unsigned, and every token is a canonical hex integer. */
static int parse_arb_strict(arb_t x, const char **p, const char **why)
{
    const char *s0 = NULL, *s, *ts[4]; size_t tot = 0, tn[4];
    for (int t = 0; t < 4; t++)
    {
        size_t n = next_tok(p, &s); if (!n || !is_hex(s, n, 1)) return 0;
        ts[t] = s; tn[t] = n;
        if (t == 0) s0 = s;
        tot = (size_t)(s + n - s0);
    }
    if (!canon_hex_int(ts[0], tn[0], 1) || !canon_hex_int(ts[1], tn[1], 1) || !canon_hex_int(ts[2], tn[2], 0) || !canon_hex_int(ts[3], tn[3], 1))
    { *why = "arb token not a canonical hex integer (mn1 pre-validation)"; return 0; }
    for (int t = 0; t < 4; t += 2)
        if (tn[t] == 1 && ts[t][0] == '0' && !(tn[t + 1] == 1 && ts[t + 1][0] == '0'))
        { *why = "arb zero mantissa with a nonzero exponent (mn1 pre-validation; not a finite zero)"; return 0; }
    /* v14c (mn1, second class found by the M13 fuzz of the first v14c build): FLINT's loader also aborts (mag_set_arf_dump) on a radius
       mantissa that a mag cannot hold exactly (e.g. 7fffffff).  arb_load_str is therefore NOT called: the ball is built from the four
       tokens with arf_set_fmpz_2exp (exact) and mag_set_fmpz_2exp_fmpz (an upper bound; total functions without an abort path), and the
       canonical re-serialisation check below then accepts exactly the values whose dump equals the tokens (so a loaded honest ball equals
       the dumped one bit for bit). */
    char *buf = flint_malloc(tot + 1); memcpy(buf, s0, tot); buf[tot] = 0;
    fmpz_t f[4]; char tb[4][128]; int ok = 1;
    for (int t = 0; t < 4; t++) fmpz_init(f[t]);
    for (int t = 0; t < 4 && ok; t++)
    {
        char *tt = tn[t] < sizeof tb[t] ? tb[t] : flint_malloc(tn[t] + 1);
        memcpy(tt, ts[t], tn[t]); tt[tn[t]] = 0; ok = fmpz_set_str(f[t], tt, 16) == 0;
        if (tt != tb[t]) flint_free(tt);
    }
    if (ok)
    {
        if (fmpz_is_zero(f[0])) arf_zero(arb_midref(x)); else arf_set_fmpz_2exp(arb_midref(x), f[0], f[1]);
        if (fmpz_is_zero(f[2])) mag_zero(arb_radref(x)); else mag_set_fmpz_2exp_fmpz(arb_radref(x), f[2], f[3]);
    }
    for (int t = 0; t < 4; t++) fmpz_clear(f[t]);
    ok = ok && arb_is_finite(x) && mag_valid(arb_radref(x));
    if (ok) { char *c = arb_dump_str(x); ok = !strcmp(c, buf); flint_free(c); }
    if (!ok && !*why) *why = "arb value not canonical / not finite / radius not a valid mag";
    flint_free(buf);
    return ok;
}

/* parse an authenticated item line (`I x b i lo hi nbk mph ...`, seal already checked for index x) into item storage of Q;
   returns 1 loaded, 0 invalid or duplicate (fatal; why set).  v14c (MJ1 b): any second authenticated line for a loaded item is fatal. */
static int load_line(wq_t *Q, const char *line, unsigned long xs, const char **why)
{
    zfm_session *S = Q->S; const char *p = line, *s; size_t n; unsigned long v[5]; double nbk, mph;
    n = next_tok(&p, &s); if (n != 1 || s[0] != 'I') { *why = "not an item line"; return 0; }
    for (int k = 0; k < 5; k++) { n = next_tok(&p, &s); if (!parse_dec_ul(s, n, v + k)) { *why = "bad integer field"; return 0; } }
    n = next_tok(&p, &s); if (!parse_hexdouble(s, n, &nbk)) { *why = "bad nblocks"; return 0; }
    n = next_tok(&p, &s); if (!parse_hexdouble(s, n, &mph)) { *why = "bad maxph"; return 0; }
    unsigned long xt = v[0], b = v[1], i = v[2], lo = v[3], hi = v[4];
    if (xt != xs) { *why = "item index token differs from the sealed index"; return 0; }
    if (b >= (unsigned long)S->nb || Q->first[b] < 0) { *why = "bucket out of range"; return 0; }
    witem_t *w0 = Q->it + Q->first[b];
    if (i >= (unsigned long)w0->T) { *why = "item index out of range"; return 0; }     /* m2: checked before index arithmetic */
    long x = Q->first[b] + (long)i; witem_t *w = Q->it + x;
    if ((unsigned long)x != xt) { *why = "item index x does not equal first[b] + i"; return 0; }
    if (w->b != (slong)b || w->i != (int)i || w->lo != lo || w->hi != hi) { *why = "item (b, i, lo, hi) does not match this session"; return 0; }
    if (w->done)
    {
        unsigned char d[32]; CC_SHA256(line, (CC_LONG)strlen(line), d);
        *why = memcmp(d, Q->lhash + 32 * x, 32) ? "conflicting duplicate: a second authenticated line for an already loaded item, with different contents (MJ1)"
                                                 : "identical duplicate: a second authenticated line for an already loaded item (an honest writer never emits one; MJ1)";
        return 0;
    }
    int na = S->nw * S->K2, good = 1; const char *aw = NULL;
    for (int a = 0; a < na && good; a++) good = parse_arb_strict(acb_realref(w->R.M + a), &p, &aw) && parse_arb_strict(acb_imagref(w->R.M + a), &p, &aw);
    for (int a = 0; a < na && good; a++) good = parse_mag_strict(w->R.err + a, &p);
    for (int j = 0; j < S->nw && good; j++) good = parse_mag_strict(w->R.V + j, &p);
    if (!good || *p) { *why = good ? "trailing data" : (aw ? aw : "invalid moment / bound value"); return 0; }
    w->R.nblocks = nbk; w->R.maxph = mph; w->done = 1; w->loaded = 1;
    CC_SHA256(line, (CC_LONG)strlen(line), Q->lhash + 32 * x);
    return 1;
}

/* m3: one checked append per line (caller holds Q->io, or no other thread exists).  v14c (mn2): F_FULLFSYNC (fallback fsync), checked,
   after the header, by the flusher thread every 1.0 s while unsynced lines exist (independent of item completion), and at session end.
   True bound: a line whose write(2) returned at time t is on stable storage by t + 1 s + one F_FULLFSYNC duration, unless a write/fsync
   error is reported; max_unsynced (write-to-sync age) is measured.  A crash or power loss loses at most that unsynced tail, which is
   torn/missing and recomputed on resume. */
static void ck_sync(wq_t *Q)
{
    if (Q->fd < 0 || Q->dirty_since == 0) return;
    if (fcntl(Q->fd, F_FULLFSYNC) == -1 && fsync(Q->fd) != 0)
    { ck_err(Q, "checkpoint fsync failed (%s); checkpointing stopped, the session continues", strerror(errno)); Q->werr++; close(Q->fd); Q->fd = -1; return; }
    double t = now(); if (t - Q->dirty_since > Q->max_unsynced) Q->max_unsynced = t - Q->dirty_since;
    Q->dirty_since = 0; Q->last_sync = t; Q->syncs++;
}
/* returns 0 if the bytes were written */
static int ck_write(wq_t *Q, const char *s, size_t n)
{
    if (Q->fd < 0) return -1;
    size_t off = 0;
    while (off < n)
    {
        ssize_t r = write(Q->fd, s + off, n - off);
        if (r < 0 && errno == EINTR) continue;
        if (r <= 0) { ck_err(Q, "checkpoint write failed (%s); checkpointing stopped, the session continues", r < 0 ? strerror(errno) : "short write"); Q->werr++; close(Q->fd); Q->fd = -1; return -1; }
        off += (size_t)r;
    }
    if (Q->dirty_since == 0) Q->dirty_since = now();
    return 0;
}
static void ck_seal_write_hdr(wq_t *Q, sbuf_t *L)
{
    char h[65]; seal_hdr_hex(h, Q->key, L->s, L->n);
    sb_add(L, " #"); sb_add(L, h); sb_add(L, "\n");
    if (!ck_write(Q, L->s, L->n)) Q->written++;
}
static void ck_seal_write_item(wq_t *Q, sbuf_t *L, long x)
{
    char h[65]; seal_item_hex(h, Q->key, Q->hh, (unsigned long)x, L->s, L->n);
    sb_add(L, " #"); sb_add(L, h); sb_add(L, "\n");
    if (!ck_write(Q, L->s, L->n)) Q->written++;
}
/* mn2: the flusher thread (no FLINT calls; touches only the fd under Q->io) */
static void *ck_flusher(void *arg)
{
    wq_t *Q = (wq_t *)arg;
    pthread_mutex_lock(&Q->io);
    while (!Q->fstop)
    {
        struct timespec ts = { 1, 0 };          /* 1.0 s, relative (immune to wall-clock steps) */
        pthread_cond_timedwait_relative_np(&Q->fcv, &Q->io, &ts);
        if (!Q->fstop) ck_sync(Q);
    }
    pthread_mutex_unlock(&Q->io);
    return NULL;
}

static void merge_bucket(wq_t *Q, slong b)
{
    zfm_session *S = Q->S; slong wp = S->wp, nb = S->nb;
    for (long x = Q->first[b]; x < Q->nit && Q->it[x].b == b; x++)
    {
        witem_t *w = Q->it + x; mrange_t *R = &w->R;
        for (int j = 0; j < S->nw; j++)
        {
            for (int k = 0; k < S->K2; k++)
            {
                acb_ptr m = S->M + midx(S, j, b, k);
                acb_add(m, m, R->M + j * S->K2 + k, wp);
                arb_add_error_mag(acb_realref(m), R->err + j * S->K2 + k);
                arb_add_error_mag(acb_imagref(m), R->err + j * S->K2 + k);
            }
            mag_add(S->V + j * nb + b, S->V + j * nb + b, R->V + j);
        }
        if (R->maxph > Q->maxph) Q->maxph = R->maxph;
        Q->nblocks += R->nblocks;
        _acb_vec_clear(R->M, S->nw * S->K2); _mag_vec_clear(R->err, S->nw * S->K2); _mag_vec_clear(R->V, S->nw);
        R->M = NULL; R->err = NULL; R->V = NULL;
    }
}

static void *wq_worker(void *arg)
{
    wq_t *Q = (wq_t *)arg; zfm_session *S = Q->S;
    for (;;)
    {
        pthread_mutex_lock(&Q->mu);
        long x = Q->next < Q->nord ? Q->order[Q->next++] : -1;
        pthread_mutex_unlock(&Q->mu);
        if (x < 0) break;
        witem_t *w = Q->it + x;
        mom_range(&w->R);
        pthread_mutex_lock(&Q->io); int ck_on = Q->fd >= 0; pthread_mutex_unlock(&Q->io);
        if (ck_on)          /* the line is built before the item can be merged (merge needs this item's decrement below) */
        {
            sbuf_t L = { 0 }; item_line(&L, S, w, x);
            pthread_mutex_lock(&Q->io); ck_seal_write_item(Q, &L, x); pthread_mutex_unlock(&Q->io);
            flint_free(L.s);
        }
        pthread_mutex_lock(&Q->mu);
        w->done = 1;
        Q->computed++;
        if (--Q->left[w->b] == 0) merge_bucket(Q, w->b);
#ifdef ZF_TEST_HOOKS
        if (Q->exit_after > 0 && Q->computed >= Q->exit_after) { fprintf(stderr, "zfast14b: test hook ZFAST14_TEST_EXIT_AFTER reached\n"); _exit(77); }
#endif
        pthread_mutex_unlock(&Q->mu);
    }
    return NULL;
}

static int cmp_len_desc(void *ctx, const void *a, const void *b)      /* macOS qsort_r: thunk first */
{
    const witem_t *it = (const witem_t *)ctx; long x = *(const long *)a, y = *(const long *)b;
    ulong lx = it[x].hi - it[x].lo, ly = it[y].hi - it[y].lo;
    if (lx != ly) return lx > ly ? -1 : 1;
    return x < y ? -1 : (x > y);
}

/* ---------- m1 (b): resume verification by recomputation of a random sample of loaded items ---------- */
typedef struct { wq_t *Q; long *sel; long nsel, next; int bad; long bad_x; pthread_mutex_t mu; } vq_t;
static void *vq_worker(void *arg)
{
    vq_t *V = (vq_t *)arg; wq_t *Q = V->Q; zfm_session *S = Q->S; int na = S->nw * S->K2;
    for (;;)
    {
        pthread_mutex_lock(&V->mu); long k = V->bad ? V->nsel : V->next++; pthread_mutex_unlock(&V->mu);
        if (k >= V->nsel) break;
        witem_t *w = Q->it + V->sel[k];
        mrange_t R = w->R; R.M = _acb_vec_init(na); R.err = _mag_vec_init(na); R.V = _mag_vec_init(S->nw);
        mom_range(&R);
        int same = !memcmp(&R.nblocks, &w->R.nblocks, sizeof(double)) && !memcmp(&R.maxph, &w->R.maxph, sizeof(double));
        for (int a = 0; a < na && same; a++) same = arb_equal(acb_realref(R.M + a), acb_realref(w->R.M + a)) && arb_equal(acb_imagref(R.M + a), acb_imagref(w->R.M + a))
                                                  && mag_equal(R.err + a, w->R.err + a);
        for (int j = 0; j < S->nw && same; j++) same = mag_equal(R.V + j, w->R.V + j);
        _acb_vec_clear(R.M, na); _mag_vec_clear(R.err, na); _mag_vec_clear(R.V, S->nw);
        if (!same) { pthread_mutex_lock(&V->mu); if (!V->bad) { V->bad = 1; V->bad_x = V->sel[k]; } pthread_mutex_unlock(&V->mu); }
    }
    return NULL;
}
static int verify_sample(wq_t *Q, int verify_n, int workers, long *n_verified)
{
    long nl = 0; for (long x = 0; x < Q->nit; x++) nl += Q->it[x].loaded;
    *n_verified = 0;
    if (nl == 0 || verify_n <= 0) return 0;
    long *pool = flint_malloc(sizeof(long) * nl); long m = 0;
    for (long x = 0; x < Q->nit; x++) if (Q->it[x].loaded) pool[m++] = x;
    long ns = verify_n < nl ? verify_n : nl;
    for (long k = 0; k < ns; k++) { long r = k + (long)arc4random_uniform((uint32_t)(nl - k)); long t = pool[k]; pool[k] = pool[r]; pool[r] = t; }
    vq_t V; memset(&V, 0, sizeof V); V.Q = Q; V.sel = pool; V.nsel = ns; pthread_mutex_init(&V.mu, NULL);
    int nt = workers < ns ? workers : (int)ns; if (nt < 1) nt = 1;
    pthread_t th[64]; int started = 0;
    for (int t = 0; t < nt; t++) { if (pthread_create(&th[t], NULL, vq_worker, &V)) { fprintf(stderr, "pthread_create\n"); abort(); } started++; }
    for (int t = 0; t < started; t++) pthread_join(th[t], NULL);
    pthread_mutex_destroy(&V.mu);
    int rc = 0;
    if (V.bad) { witem_t *w = Q->it + V.bad_x; zf14b_seterr("resume verification FAILED: item (b=%ld, i=%d) recomputed differs from the checkpoint (refusing)", (long)w->b, w->i); rc = -1; }
    *n_verified = ns; flint_free(pool);
    return rc;
}

static void items_free(witem_t *it, long nit, int nw, int K2)
{
    for (long x = 0; x < nit; x++)
        if (it[x].R.M) { _acb_vec_clear(it[x].R.M, nw * K2); _mag_vec_clear(it[x].R.err, nw * K2); _mag_vec_clear(it[x].R.V, nw); }
    flint_free(it);
}

static int nonce_ok(const char *s) { if (!s || strlen(s) != 32) return 0; return is_hex(s, 32, 0); }

/* v14c (mn4): key file.  An existing key must be a regular, non-symlink file owned by the euid, mode & 077 == 0, exactly 32 bytes.
   A missing key is created (only when allowed) atomically: temp file (O_EXCL | O_NOFOLLOW, 0600) -> 32 random bytes -> F_FULLFSYNC ->
   renamex_np(RENAME_EXCL) (never replaces an existing key) -> fsync of the key directory.  A crash leaves either no key (a stray temp
   file that is never read) or a complete one.  *created = 1 if this call created the key.  Test-hooks build: env
   ZFAST14C_TEST_KEYCRASH=1 exits (rc 78) after the temp key is durable and before the rename (A3b). */
static int key_load(unsigned char *key, const char *path, int may_create, int *created)
{
    *created = 0;
    int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd >= 0)
    {
        struct stat st; ssize_t r = -1;
        if (fstat(fd, &st)) { close(fd); zf14b_seterr("checkpoint key %s: fstat failed (refusing)", path); return -1; }
        if (!S_ISREG(st.st_mode)) { close(fd); zf14b_seterr("checkpoint key %s is not a regular file (refusing)", path); return -1; }
        if (st.st_uid != geteuid()) { close(fd); zf14b_seterr("checkpoint key %s is not owned by this user (refusing)", path); return -1; }
        if (st.st_mode & 077) { close(fd); zf14b_seterr("checkpoint key %s has group/other permissions (mode %o; must be 0600 or stricter) (refusing)", path, (unsigned)(st.st_mode & 0777)); return -1; }
        if (st.st_size == 0) { close(fd); zf14b_seterr("checkpoint key %s is a 0-byte file (an interrupted pre-v14c key creation); it is neither reused nor overwritten: start a fresh run name (refusing)", path); return -1; }
        if (st.st_size == 32) { size_t got = 0; while (got < 32) { r = read(fd, key + got, 32 - got); if (r < 0 && errno == EINTR) continue; if (r <= 0) break; got += (size_t)r; } r = (ssize_t)got; }
        close(fd);
        if (r != 32) { zf14b_seterr("checkpoint key %s is not a 32-byte key file (refusing)", path); return -1; }
        return 0;
    }
    if (errno == ELOOP) { zf14b_seterr("checkpoint key %s is a symbolic link (refusing)", path); return -1; }
    if (errno != ENOENT || !may_create) { zf14b_seterr("checkpoint key %s missing or unreadable (%s) for an existing checkpoint (refusing)", path, strerror(errno)); return -1; }
    char tmp[4096]; unsigned char rb[4]; arc4random_buf(rb, 4); char rh[9]; hex_of(rh, rb, 4);
    if (snprintf(tmp, sizeof tmp, "%s.tmp.%d.%s", path, (int)getpid(), rh) >= (int)sizeof tmp) { zf14b_seterr("checkpoint key path too long"); return -1; }
    fd = open(tmp, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) { zf14b_seterr("cannot create checkpoint key temp file %s (%s)", tmp, strerror(errno)); return -1; }
    arc4random_buf(key, 32);
    int ok = write(fd, key, 32) == 32 && (fcntl(fd, F_FULLFSYNC) != -1 || fsync(fd) == 0);
    close(fd);
    if (!ok) { zf14b_seterr("cannot write checkpoint key temp file %s (left in place, never read)", tmp); return -1; }
#ifdef ZF_TEST_HOOKS
    { const char *g = getenv("ZFAST14C_TEST_KEYCRASH"); if (g && g[0] == '1') { fprintf(stderr, "zfast14c: test hook ZFAST14C_TEST_KEYCRASH\n"); _exit(78); } }
#endif
    if (renamex_np(tmp, path, RENAME_EXCL))
    { zf14b_seterr("cannot install checkpoint key %s (%s; temp %s left in place, never read) (refusing)", path, strerror(errno), tmp); return -1; }
    char dcopy[4096]; snprintf(dcopy, sizeof dcopy, "%s", path); const char *dir = dirname(dcopy);
    int dfd = dir ? open(dir, O_RDONLY | O_CLOEXEC) : -1;
    int dok = dfd >= 0 && (fcntl(dfd, F_FULLFSYNC) != -1 || fsync(dfd) == 0);
    if (dfd >= 0) close(dfd);
    if (!dok) { zf14b_seterr("checkpoint key %s installed but its directory could not be fsynced (refusing; the key is kept)", path); return -1; }
    *created = 1;
    return 0;
}

typedef struct { long loaded, items, lines_read, rejected, dup, verified, written, werr, overlong, syncs; int created, key_created, key_reused;
                 double max_unsynced; char werrmsg[512]; } ck_stats_t;

/* v14c (mn6): bounded line reader.  Reads one line (without '\n') into buf (cap bytes + NUL).  Returns its length, or -1 at EOF with
   nothing read, or -2 for an overlong line (skipped to its newline / EOF, nothing stored).  *nl = 1 if the line ended in '\n'. */
static long read_line_bounded(FILE *f, char *buf, size_t cap, int *nl)
{
    size_t n = 0; int c, over = 0; *nl = 0;
    while ((c = getc_unlocked(f)) != EOF)
    {
        if (c == '\n') { *nl = 1; break; }
        if (n < cap) buf[n++] = (char)c; else over = 1;
    }
    buf[n < cap ? n : cap] = 0;
    if (over) return -2;
    if (c == EOF && n == 0) return -1;
    return (long)n;
}

/* the fast part from n (first n beyond the head); returns 0 on success, -1 on a refusal (message in zfm14b_last_error) */
static int zfm_fast14b(zfm_session *S, ulong n, int workers, const zf_ckcfg_t *ck, ck_stats_t *cs)
{
    const zf_params *P = &S->P; slong nb = S->nb;
    memset(cs, 0, sizeof *cs);
    if (workers < 1) workers = 1;
    if (workers > 64) workers = 64;
    /* 1. the items, exactly v13b's decomposition */
    long cap = 64, nit = 0; witem_t *it = flint_malloc(sizeof(witem_t) * cap);
    for (slong b = 0; b < nb && n <= S->Nw; b++)
    {
        ulong lo0 = S->nbeg[b] > n ? S->nbeg[b] : n, hi0 = S->nbeg[b + 1] - 1;
        if (lo0 > hi0) continue;
        ulong lo[16], hi[16];
        int T = split_ranges(lo, hi, lo0, hi0, P->threads, P->bmax);
        for (int i = 0; i < T; i++)
        {
            if (nit == cap) { cap *= 2; it = flint_realloc(it, sizeof(witem_t) * cap); }
            witem_t *w = it + nit++; memset(w, 0, sizeof *w);
            w->b = b; w->i = i; w->T = T; w->lo = lo[i]; w->hi = hi[i];
            w->R.S = S; w->R.b = b; w->R.n0 = lo[i]; w->R.n1 = hi[i];
            w->R.M = _acb_vec_init(S->nw * S->K2); w->R.err = _mag_vec_init(S->nw * S->K2); w->R.V = _mag_vec_init(S->nw);
        }
        n = hi0 + 1;
    }
    wq_t Q; memset(&Q, 0, sizeof Q); Q.S = S; Q.it = it; Q.nit = nit; Q.fd = -1;
    Q.left = flint_calloc(nb, sizeof(int)); Q.first = flint_malloc(sizeof(long) * nb);
    for (slong b = 0; b < nb; b++) Q.first[b] = -1;
    for (long x = 0; x < nit; x++) { if (Q.first[it[x].b] < 0) Q.first[it[x].b] = x; Q.left[it[x].b]++; }
    pthread_mutex_init(&Q.mu, NULL); pthread_mutex_init(&Q.io, NULL); pthread_cond_init(&Q.fcv, NULL);
#ifdef ZF_TEST_HOOKS
    { const char *e = getenv("ZFAST14_TEST_EXIT_AFTER"); Q.exit_after = e ? atol(e) : 0; }
#endif
    cs->items = nit;
    int rc = 0, ck_on = 0; pthread_t fth; int fstarted = 0;
#define REFUSE(...) do { zf14b_seterr(__VA_ARGS__); rc = -1; goto done; } while (0)
    /* 2. checkpoint: lock, authenticate + verify header, load authenticated valid items, verify a sample, open for append */
    if (ck && ck->path && ck->path[0])
    {
        ck_on = 1;
        Q.lhash = flint_calloc(nit > 0 ? nit : 1, 32);
        int fd = open(ck->path, O_RDWR | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
        if (fd < 0) REFUSE("cannot open checkpoint %s (%s)", ck->path, strerror(errno));
        if (flock(fd, LOCK_EX | LOCK_NB)) { int e = errno; close(fd); REFUSE("checkpoint %s is locked by another process (%s) (refusing)", ck->path, strerror(e)); }
        Q.fd = fd;
        struct stat st; if (fstat(fd, &st)) REFUSE("fstat checkpoint failed");
        int empty = st.st_size == 0;
        char ewhy[256]; sbuf_t h = { 0 };
        if (ckpt_header(&h, S, nit, ck, ewhy, sizeof ewhy)) { flint_free(h.s); REFUSE("checkpoint %s: %s (refusing; mn3)", ck->path, ewhy); }
        if (key_load(Q.key, ck->keyfile, empty, &cs->key_created)) { flint_free(h.s); rc = -1; goto done; }
        /* mn6: line cap = 2 x a generous estimate of the longest item line + 4096, at least 64 KiB */
        size_t na = (size_t)S->nw * S->K2, per_arb = 2 * ((size_t)S->wp / 4 + 32) + 2 * 24 + 4;
        size_t lcap = 2 * (256 + 2 * na * per_arb + (na + (size_t)S->nw) * 48) + 4096; if (lcap < 65536) lcap = 65536;
        if (!empty)
        {
            int dfd = dup(fd); FILE *f = dfd >= 0 ? fdopen(dfd, "r") : NULL;
            if (!f) { if (dfd >= 0) close(dfd); flint_free(h.s); REFUSE("cannot read checkpoint %s", ck->path); }
            char *line = flint_malloc(lcap + 1); long len; int first = 1, lastnl = 1, nl = 0; long ln = 0;
            const char *why = NULL; int fatal = 0; char diff[512];
            while ((len = read_line_bounded(f, line, lcap, &nl)) != -1)
            {
                ln++; lastnl = nl;
                if (len == -2)      /* overlong: never stored, never authenticated */
                {
                    if (first) { why = "header line is overlong (not a checkpoint written by this library)"; fatal = 1; break; }
                    cs->lines_read++; cs->rejected++; cs->overlong++; continue;
                }
                int auth = 0; unsigned long xs = 0;
                if (len > 66 && line[len - 66] == ' ' && line[len - 65] == '#')
                {
                    char want[65];
                    if (first) { seal_hdr_hex(want, Q.key, line, (size_t)(len - 66)); auth = tag_eq(want, line + len - 64); }
                    else if (line[0] == 'I' && line[1] == ' ')
                    {
                        const char *q = line + 2; size_t xl = 0; while (q[xl] >= '0' && q[xl] <= '9' && xl < 21) xl++;
                        if (q[xl] == ' ' && parse_dec_ul(q, xl, &xs))
                        { seal_item_hex(want, Q.key, Q.hh, xs, line, (size_t)(len - 66)); auth = tag_eq(want, line + len - 64); }
                    }
                    if (auth) line[len - 66] = 0;
                }
                if (first)
                {
                    first = 0;
                    if (!auth) { why = "header line is not authenticated under this run's key (a foreign, tampered, v14/v14b-format or differently keyed checkpoint)"; fatal = 1; break; }
                    size_t hl = strlen(line);
                    if (hl < 40 || memcmp(line + hl - 40, " hnonce=", 8) || !nonce_ok(line + hl - 32)) { snprintf(diff, sizeof diff, "hnonce"); fatal = 2; break; }
                    CC_SHA256(line, (CC_LONG)hl, Q.hh);          /* MJ1: the stored header body, hnonce included */
                    line[hl - 40] = 0;
                    if (header_diff(line, h.s, diff, sizeof diff)) { fatal = 2; break; }
                    continue;
                }
                cs->lines_read++;
                if (!auth) { cs->rejected++; continue; }
                int r = load_line(&Q, line, xs, &why);
                if (r == 0) { fatal = 3; break; }
                cs->loaded++;
            }
            flint_free(line); fclose(f);
            if (fatal == 1) { flint_free(h.s); REFUSE("checkpoint %s: %s (refusing)", ck->path, why); }
            if (fatal == 2) { flint_free(h.s); REFUSE("checkpoint %s: header mismatch in field(s) [%s] (refusing; M1/M2: a different session, role, run, library or environment)", ck->path, diff); }
            if (fatal == 3) { flint_free(h.s); REFUSE("checkpoint %s line %ld: authenticated but invalid: %s (refusing)", ck->path, ln, why); }
            if (first) { flint_free(h.s); REFUSE("checkpoint %s: no header line (refusing)", ck->path); }
            if (!lastnl) ck_write(&Q, "\n", 1);                 /* newline repair of a torn tail; not counted as a line */
        }
        else
        {
            if (!cs->key_created)
            {
                cs->key_reused = 1;
                fprintf(stderr, "zfast14c: note: new checkpoint %s under the EXISTING key %s; its lines are bound to the new header's fresh hnonce (MJ1)\n", ck->path, ck->keyfile);
            }
            unsigned char hn[16]; char hnx[33]; arc4random_buf(hn, 16); hex_of(hnx, hn, 16);
            sbuf_t L = { 0 }; sb_addn(&L, h.s, h.n); sb_add(&L, " hnonce="); sb_add(&L, hnx);
            CC_SHA256(L.s, (CC_LONG)L.n, Q.hh);
            ck_seal_write_hdr(&Q, &L); flint_free(L.s); cs->created = 1; ck_sync(&Q);
            if (Q.fd < 0) { flint_free(h.s); REFUSE("cannot write the checkpoint header to %s: %s", ck->path, Q.werrmsg); }
        }
        flint_free(h.s);
        if (verify_sample(&Q, ck->verify_n, workers, &cs->verified)) { rc = -1; goto done; }
    }
    /* 3. merge buckets that are complete from the checkpoint; order the rest longest first */
    for (slong b = 0; b < nb; b++)
        if (Q.first[b] >= 0)
        {
            int nl = 0; for (long x = Q.first[b]; x < nit && it[x].b == b; x++) nl += it[x].done;
            Q.left[b] -= nl;
            if (Q.left[b] == 0) merge_bucket(&Q, b);
        }
    Q.order = flint_malloc(sizeof(long) * (nit + 1));
    for (long x = 0; x < nit; x++) if (!it[x].done) Q.order[Q.nord++] = x;
    qsort_r(Q.order, Q.nord, sizeof(long), it, cmp_len_desc);
    /* 4. run (v14c: with the mn2 flusher thread while a checkpoint is open) */
    if (ck_on && Q.fd >= 0) { if (pthread_create(&fth, NULL, ck_flusher, &Q)) { fprintf(stderr, "pthread_create\n"); abort(); } fstarted = 1; }
    {
        pthread_t th[64]; int nt = 0;
        for (int t = 0; t < workers; t++) { if (pthread_create(&th[t], NULL, wq_worker, &Q)) { fprintf(stderr, "pthread_create\n"); abort(); } nt++; }
        for (int t = 0; t < nt; t++) pthread_join(th[t], NULL);
    }
    for (slong b = 0; b < nb; b++) if (Q.left[b] != 0) { fprintf(stderr, "zfast14b: bucket %ld unfinished\n", (long)b); abort(); }
    S->blocks = Q.nblocks; S->max_phase_err = Q.maxph;
done:
#undef REFUSE
    if (fstarted) { pthread_mutex_lock(&Q.io); Q.fstop = 1; pthread_cond_signal(&Q.fcv); pthread_mutex_unlock(&Q.io); pthread_join(fth, NULL); }
    if (rc == 0) ck_sync(&Q);
    if (Q.fd >= 0) close(Q.fd);        /* releases the flock */
    cs->written = Q.written; cs->werr = Q.werr; cs->syncs = Q.syncs; cs->max_unsynced = Q.max_unsynced;
    snprintf(cs->werrmsg, sizeof cs->werrmsg, "%s", Q.werrmsg);
    if (rc == 0 && Q.werr) zf14b_seterr("checkpoint write error (the session result is unaffected; this checkpoint is not resumable past it): %s", Q.werrmsg);  /* mn5 */
    pthread_mutex_destroy(&Q.mu); pthread_mutex_destroy(&Q.io); pthread_cond_destroy(&Q.fcv);
    flint_free(Q.order); flint_free(Q.left); flint_free(Q.first); flint_free(Q.lhash); items_free(it, nit, S->nw, S->K2);
    return rc;
}
