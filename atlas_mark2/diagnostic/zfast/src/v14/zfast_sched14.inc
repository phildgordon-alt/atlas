/* ===================== v14: work-queue scheduler and checkpoint/resume for the session moment pass =====================
   Included in zfast_m3b.inc just before zfm_new2.  OUTPUT CONTRACT (bit-identity with v13b):
   - the decomposition into work items is EXACTLY v13b's: buckets in order, each bucket's range [lo0, hi0] split by
     split_ranges(.., P->threads (= the decomposition D, a recorded session parameter), P->bmax); item (b, i) runs mom_range on
     [lo_i, hi_i] exactly as v13b's thread i did (same block boundaries, same per-range arithmetic);
   - the merge is EXACTLY v13b's: for each bucket b, items i = 0..T-1 in order, the same acb_add / arb_add_error_mag / mag_add calls
     on S->M[., b, .] and S->V[., b] (a bucket's merge touches only that bucket, so buckets may be merged in any order);
     maxph is a max and nblocks a sum of integers < 2^53 (both order-independent);
   - only WHO computes an item and WHEN changes: W worker threads (W independent of D) pull items in longest-first order from one
     queue, with no per-bucket barrier.  So the session is identical for every W, and identical to v13b with threads = D.
   Checkpoint (optional path): every finished item is appended as one text line (exact arb_dump_str of the moments, raw mag fields of
   the bounds) with a SHA-256 of the line; the header pins every parameter that determines the items.  On resume, valid lines whose
   (b, i, lo, hi) match an item are loaded instead of computed; the merge is unchanged, so a resumed session is identical to an
   uninterrupted one (tested: RESULTS_M9).  A line that fails its checksum or does not match is ignored (recomputed). */
#include <CommonCrypto/CommonDigest.h>
#include <unistd.h>
#include <fcntl.h>

typedef struct { slong b; int i, T; ulong lo, hi; mrange_t R; int done, loaded; } witem_t;

typedef struct {
    zfm_session *S; witem_t *it; long nit; long *order; long nord, next;
    int *left;                      /* per bucket: items not yet finished */
    long *first;                    /* per bucket: index of its first item (-1 if none) */
    pthread_mutex_t mu;
    FILE *ck; long computed, exit_after; double maxph, nblocks;
} wq_t;

static void sha256_hex(char *out, const char *buf, size_t len)
{
    unsigned char d[CC_SHA256_DIGEST_LENGTH]; CC_SHA256(buf, (CC_LONG)len, d);
    for (int i = 0; i < CC_SHA256_DIGEST_LENGTH; i++) sprintf(out + 2 * i, "%02x", d[i]);
    out[64] = 0;
}

/* growable string */
typedef struct { char *s; size_t n, cap; } sbuf_t;
static void sb_add(sbuf_t *b, const char *t)
{
    size_t l = strlen(t);
    if (b->n + l + 1 > b->cap) { b->cap = 2 * (b->n + l + 1); b->s = flint_realloc(b->s, b->cap); }
    memcpy(b->s + b->n, t, l + 1); b->n += l;
}
static void sb_mag(sbuf_t *b, const mag_t m)
{
    char tmp[64]; char *e = fmpz_get_str(NULL, 16, MAG_EXPREF(m));
    snprintf(tmp, sizeof tmp, " %lx:", (unsigned long)MAG_MAN(m)); sb_add(b, tmp); sb_add(b, e); flint_free(e);
}
static int parse_mag(mag_t m, char **p)
{
    while (**p == ' ') (*p)++;
    char *q; unsigned long man = strtoul(*p, &q, 16); if (q == *p || *q != ':') return 0;
    char *e0 = q + 1, *e1 = e0; while (*e1 && *e1 != ' ' && *e1 != '\n') e1++;
    char sv = *e1; *e1 = 0; int bad = fmpz_set_str(MAG_EXPREF(m), e0, 16); *e1 = sv;
    if (bad) return 0;
    MAG_MAN(m) = (mp_limb_t)man; *p = e1; return 1;
}

static void ckpt_header(sbuf_t *h, const zfm_session *S, long nit)
{
    char tmp[512]; char *t0 = fmpz_get_str(NULL, 10, S->T0);
    sb_add(h, "ZFAST14CKPT v1 T0="); sb_add(h, t0); flint_free(t0);
    snprintf(tmp, sizeof tmp, " u0=%a H=%a Delta=%a K=%d J=%d D=%d kind=%d bmax=%ld interp=%a Nw=%lu nb=%ld nhead=%lu nitems=%ld wp=%ld",
             S->u0, S->H, S->Delta, S->K, S->P.J, S->P.threads, S->kind, S->P.bmax, S->P.log2_interp, (unsigned long)S->Nw, (long)S->nb,
             (unsigned long)S->nhead, nit, (long)S->wp);
    sb_add(h, tmp);
}

static void item_line(sbuf_t *L, const zfm_session *S, const witem_t *w)
{
    char tmp[256]; int na = S->nw * S->K2;
    snprintf(tmp, sizeof tmp, "I %ld %d %lu %lu %a %a", (long)w->b, w->i, (unsigned long)w->lo, (unsigned long)w->hi, w->R.nblocks, w->R.maxph);
    sb_add(L, tmp);
    for (int a = 0; a < na; a++)
    {
        char *r = arb_dump_str(acb_realref(w->R.M + a)), *im = arb_dump_str(acb_imagref(w->R.M + a));
        sb_add(L, " "); sb_add(L, r); sb_add(L, " "); sb_add(L, im); flint_free(r); flint_free(im);
    }
    for (int a = 0; a < na; a++) sb_mag(L, w->R.err + a);
    for (int j = 0; j < S->nw; j++) sb_mag(L, w->R.V + j);
}

/* arb_dump_str is 4 space-separated hex tokens */
static int parse_arb(arb_t x, char **p)
{
    char *s = *p; while (*s == ' ') s++;
    char *e = s; for (int t = 0; t < 4; t++) { while (*e && *e != ' ' && *e != '\n') e++; if (t < 3) { if (*e != ' ') return 0; e++; } }
    char sv = *e; *e = 0; int bad = arb_load_str(x, s); *e = sv;
    if (bad) return 0;
    *p = e; return 1;
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
        pthread_mutex_lock(&Q->mu);
        w->done = 1;
        if (Q->ck)
        {
            sbuf_t L = { 0 }; item_line(&L, S, w); char h[65]; sha256_hex(h, L.s, L.n);
            fprintf(Q->ck, "%s #%s\n", L.s, h); fflush(Q->ck); fsync(fileno(Q->ck)); flint_free(L.s);
        }
        Q->computed++;
        if (--Q->left[w->b] == 0) merge_bucket(Q, w->b);
        if (Q->exit_after > 0 && Q->computed >= Q->exit_after) { fprintf(stderr, "zfast14: test hook ZFAST14_TEST_EXIT_AFTER reached\n"); _exit(77); }
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

/* the fast part from n (first n beyond the head); returns 0 on success, -1 on a checkpoint error (header mismatch / IO) */
static int zfm_fast14(zfm_session *S, ulong n, int workers, const char *ckpt, long *n_loaded, long *n_items)
{
    const zf_params *P = &S->P; slong nb = S->nb;
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
    wq_t Q; memset(&Q, 0, sizeof Q); Q.S = S; Q.it = it; Q.nit = nit;
    Q.left = flint_calloc(nb, sizeof(int)); Q.first = flint_malloc(sizeof(long) * nb);
    for (slong b = 0; b < nb; b++) Q.first[b] = -1;
    for (long x = 0; x < nit; x++) { if (Q.first[it[x].b] < 0) Q.first[it[x].b] = x; Q.left[it[x].b]++; }
    pthread_mutex_init(&Q.mu, NULL);
    { const char *e = getenv("ZFAST14_TEST_EXIT_AFTER"); Q.exit_after = e ? atol(e) : 0; }
    *n_loaded = 0; *n_items = nit;
    /* 2. checkpoint: verify header, load valid matching items, open for append */
    if (ckpt && ckpt[0])
    {
        sbuf_t h = { 0 }; ckpt_header(&h, S, nit); char hs[65]; sha256_hex(hs, h.s, h.n);
        FILE *f = fopen(ckpt, "r");
        if (f)
        {
            size_t lcap = 1 << 16; char *line = flint_malloc(lcap); ssize_t len; int first = 1, ok = 1, lastnl = 1;
            while ((len = getline(&line, &lcap, f)) > 0)
            {
                lastnl = line[len - 1] == '\n';
                char *hash = strrchr(line, '#');
                if (!hash || hash == line || hash[-1] != ' ') { if (first) { ok = 0; break; } continue; }
                char got[65]; snprintf(got, sizeof got, "%.64s", hash + 1);
                hash[-1] = 0; char want[65]; sha256_hex(want, line, strlen(line));
                if (strcmp(got, want)) { if (first) { ok = 0; break; } continue; }
                if (first) { first = 0; if (strcmp(line, h.s)) { ok = 0; break; } continue; }
                long b, i; unsigned long lo, hi; double nbk, mph; int pos = 0;
                if (sscanf(line, "I %ld %ld %lu %lu %la %la%n", &b, &i, &lo, &hi, &nbk, &mph, &pos) != 6) continue;
                if (b < 0 || b >= nb || Q.first[b] < 0) continue;
                long x = Q.first[b] + i;
                if (i < 0 || x >= nit || it[x].b != b || it[x].i != i || it[x].lo != lo || it[x].hi != hi || it[x].done) continue;
                char *p = line + pos; int na = S->nw * S->K2, good = 1;
                for (int a = 0; a < na && good; a++) good = parse_arb(acb_realref(it[x].R.M + a), &p) && parse_arb(acb_imagref(it[x].R.M + a), &p);
                for (int a = 0; a < na && good; a++) good = parse_mag(it[x].R.err + a, &p);
                for (int j = 0; j < S->nw && good; j++) good = parse_mag(it[x].R.V + j, &p);
                while (good && *p == ' ') p++;
                if (!good || *p) continue;
                it[x].R.nblocks = nbk; it[x].R.maxph = mph; it[x].done = 1; it[x].loaded = 1; (*n_loaded)++;
            }
            flint_free(line); fclose(f);
            if (!ok) { fprintf(stderr, "zfast14: checkpoint %s: invalid header or a different session (refusing)\n", ckpt); return -1; }
            Q.ck = fopen(ckpt, "a"); if (!Q.ck) return -1;
            if (!lastnl) fputc('\n', Q.ck);
            if (first) { fprintf(Q.ck, "%s #%s\n", h.s, hs); fflush(Q.ck); fsync(fileno(Q.ck)); }     /* empty file: write the header */
        }
        else
        {
            Q.ck = fopen(ckpt, "w"); if (!Q.ck) return -1;
            fprintf(Q.ck, "%s #%s\n", h.s, hs); fflush(Q.ck); fsync(fileno(Q.ck));
        }
        flint_free(h.s);
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
    /* 4. run */
    if (workers < 1) workers = 1;
    if (workers > 64) workers = 64;
    pthread_t th[64]; int nt = 0;
    for (int t = 0; t < workers; t++) { if (pthread_create(&th[t], NULL, wq_worker, &Q)) { fprintf(stderr, "pthread_create\n"); abort(); } nt++; }
    for (int t = 0; t < nt; t++) pthread_join(th[t], NULL);
    for (slong b = 0; b < nb; b++) if (Q.left[b] != 0) { fprintf(stderr, "zfast14: bucket %ld unfinished\n", (long)b); abort(); }
    if (Q.ck) fclose(Q.ck);
    S->blocks = Q.nblocks; S->max_phase_err = Q.maxph;
    pthread_mutex_destroy(&Q.mu);
    flint_free(Q.order); flint_free(Q.left); flint_free(Q.first); flint_free(it);
    return 0;
}
