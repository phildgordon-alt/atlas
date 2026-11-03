/* ===================== M3: window sessions by bucketed Taylor moments (THEORY_M3.md) =====================
   Included at the end of zfast.c (v10); uses the static helpers of zfast.c. */

#define ZFM_KMAX 40

struct zfm_session {
    fmpz_t T0; double u0, H, Delta; int kind, nw, K, K2; slong nb, wp;
    arb_t sigma, t0, tau0;
    ulong Nw, nhead;
    ulong *nbeg;            /* bucket b = [nbeg[b], nbeg[b+1]) */
    double *Lb; mag_struct *Xb;
    acb_ptr M;              /* index ((j * nb + b) * K2 + k) */
    mag_struct *V;          /* index (j * nb + b) */
    zf_params P;
    double sec_build, sec_head, sec_fast, blocks, max_phase_err;
};

static inline long midx(const zfm_session *S, int j, slong b, int k) { return ((long)j * S->nb + b) * S->K2 + k; }

/* log(c + x) - Lb as a degree-RDEG polynomial in x, |x| <= X (cf. weight_poly kind 2): error e, magnitude bound mx */
static void logL_poly(double *co, mag_t e, mag_t mx, const arb_t c, double Lb, double X, slong prec)
{
    arb_t a, q, Lba; mag_t M, r, tmp, sumabs, rnd, xr;
    arb_init(a); arb_init(q); arb_init(Lba); mag_init(M); mag_init(r); mag_init(tmp); mag_init(sumabs); mag_init(rnd); mag_init(xr);
    const double u = 0x1p-53;
    arb_set_d(Lba, Lb);
    mag_zero(sumabs); mag_zero(rnd);
    for (int j = 0; j <= RDEG; j++)
    {
        if (j == 0) { arb_log(a, c, prec); arb_sub(a, a, Lba, prec); }
        else { arb_pow_ui(q, c, j, prec); arb_mul_ui(q, q, j, prec); arb_inv(a, q, prec); if (j % 2 == 0) arb_neg(a, a); }
        co[j] = arf_get_d(arb_midref(a), ARF_RND_NEAR);
        arb_t d; arb_init(d); arb_set_d(d, co[j]); arb_sub(d, d, a, prec); arb_get_mag(tmp, d); arb_clear(d);
        mag_set_d(r, X); mag_pow_ui(r, r, j);
        mag_mul(tmp, tmp, r); mag_add(rnd, rnd, tmp);
        mag_set_d(tmp, fabs(co[j])); mag_mul(tmp, tmp, r); mag_add(sumabs, sumabs, tmp);
    }
    /* Cauchy on |z - c| <= R = c/2: |log z - Lb| <= max(|log(c/2) - Lb|, |log(3c/2) - Lb|) + pi/6 */
    arb_get_mag_lower(r, c); mag_mul_2exp_si(r, r, -1);
    {
        arb_t p1, p2, pp; arb_init(p1); arb_init(p2); arb_init(pp);
        arb_mul_2exp_si(p1, c, -1); arb_log(p1, p1, prec); arb_sub(p1, p1, Lba, prec); arb_abs(p1, p1);
        arb_mul_ui(p2, c, 3, prec); arb_mul_2exp_si(p2, p2, -1); arb_log(p2, p2, prec); arb_sub(p2, p2, Lba, prec); arb_abs(p2, p2);
        arb_max(p1, p1, p2, prec);
        arb_const_pi(pp, prec); arb_div_ui(pp, pp, 6, prec); arb_add(p1, p1, pp, prec);
        arb_get_mag(M, p1);
        arb_clear(p1); arb_clear(p2); arb_clear(pp);
    }
    mag_set_d(xr, X); mag_div(xr, xr, r);
    if (mag_cmp_2exp_si(xr, -1) > 0) { mag_inf(e); mag_inf(mx); goto done; }
    mag_pow_ui(tmp, xr, RDEG + 1); mag_mul(tmp, tmp, M);
    mag_one(r); mag_sub_lower(r, r, xr); mag_div(tmp, tmp, r);
    mag_add(e, tmp, rnd);
    mag_set_d(tmp, (RDEG + 1) * u / (1 - (RDEG + 1) * u)); mag_mul(tmp, tmp, sumabs);
    mag_add(e, e, tmp);
    mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);
done:
    arb_clear(a); arb_clear(q); arb_clear(Lba); mag_clear(M); mag_clear(r); mag_clear(tmp); mag_clear(sumabs); mag_clear(rnd); mag_clear(xr);
}

/* moment kernel: acc[((j*K2 + k)*2 + re/im)*2 + hi/lo] */
static void block_kernel_mom(double *acc, fx *E, int J, long n0, long B, int nw, int K2, double *const *cwt, const double *cx)
{
    enum { MAXA = 2 * (ZFM_KMAX + 2) * 2 };
    double hi[MAXA], lo[MAXA], g[MAXA];
    int na = nw * K2 * 2;
    for (int a = 0; a < na; a++) { hi[a] = 0.0; lo[a] = 0.0; }
    double xc = 0.5 * (double)(B - 1);
    long k = 0;
    while (k < B)
    {
        long kend = k + 16 < B ? k + 16 : B;
        for (int a = 0; a < na; a++) g[a] = 0.0;
        for (; k < kend; k++)
        {
            double c, s; zf_cos2pi(&c, &s, E[0].w[3]);
            double xx = (double)k - xc;
            double x = horner6(cx, xx);
            for (int j = 0; j < nw; j++)
            {
                double w = cwt ? horner6(cwt[j], xx) : 1.0 / sqrt((double)(n0 + k));
                double pr = w * c, pi = w * s;
                double *gg = g + j * K2 * 2;
                for (int m = 0; m < K2; m++)
                {
                    gg[2 * m] = gg[2 * m] + pr; gg[2 * m + 1] = gg[2 * m + 1] + pi;
                    pr = pr * x; pi = pi * x;
                }
            }
            for (int i = 0; i < J; i++) fx_add(&E[i], &E[i + 1]);
        }
        for (int a = 0; a < na; a++)
        {
            double sh = hi[a] + g[a], bb = sh - hi[a];
            double ee = (hi[a] - (sh - bb)) + (g[a] - bb);
            hi[a] = sh; lo[a] = lo[a] + ee;
        }
    }
    for (int a = 0; a < na; a++) { acc[2 * a] = hi[a]; acc[2 * a + 1] = lo[a]; }
}

typedef struct {
    zfm_session *S; slong b; ulong n0, n1;
    acb_ptr M;          /* nw * K2 local moments */
    mag_struct *err;    /* nw * K2 */
    mag_struct *V;      /* nw */
    double maxph, nblocks;
} mrange_t;

static void *mom_range(void *arg)
{
    mrange_t *R = (mrange_t *)arg; zfm_session *S = R->S;
    const zf_params *P = &S->P; int J = P->J; slong wp = S->wp; int nw = S->nw, K2 = S->K2;
    double log2tau = log2(arf_get_d(arb_midref(S->tau0), ARF_RND_UP));
    arb_t x, zero, c, L[JMAX + 1];
    mag_t err, tmp, tmp2, epsi[JMAX + 1], ex, mxx, ew[2], mw[2], Xp, trig, sumc, term, kXe;
    fx E[JMAX + 1];
    arb_init(x); arb_init(zero); arb_init(c);
    mag_init(err); mag_init(tmp); mag_init(tmp2); mag_init(ex); mag_init(mxx); mag_init(Xp); mag_init(trig); mag_init(sumc); mag_init(term); mag_init(kXe);
    for (int j = 0; j < 2; j++) { mag_init(ew[j]); mag_init(mw[j]); }
    for (int i = 0; i <= JMAX; i++) { arb_init(L[i]); mag_init(epsi[i]); }
    const double u = 0x1p-53;
    double *acc = flint_malloc(sizeof(double) * nw * K2 * 4);
    double cwbuf[2][RDEG + 1], cx[RDEG + 1]; double *cwt[2] = { cwbuf[0], cwbuf[1] };
    double maxph = 0, nbk = 0;
    ulong n = R->n0, N = R->n1; slong b = R->b;
    for (int a = 0; a < nw * K2; a++) { acb_zero(R->M + a); mag_zero(R->err + a); }
    for (int j = 0; j < nw; j++) mag_zero(R->V + j);
    while (n <= N)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)N);
        if (B < J + 1) { fprintf(stderr, "mom block too short\n"); abort(); }
        block_setup(E, err, L, epsi, x, tmp, tmp2, zero, S->tau0, n, B, J, wp);
        double ph = mag_get_d(err); if (ph > maxph) maxph = ph;
        double X = 0.5 * (double)(B - 1);
        arb_set_ui(c, n); arb_set_d(x, X); arb_add(c, c, x, wp);
        logL_poly(cx, ex, mxx, c, S->Lb[b], X, wp);
        if (S->kind == 0)
        {
            mag_set_ui_lower(mw[0], n); mag_rsqrt(mw[0], mw[0]);
            mag_set_d(tmp, 2.01 * u); mag_mul(ew[0], mw[0], tmp);
        }
        else
        {
            weight_poly(cwbuf[0], ew[0], mw[0], 0, c, S->sigma, X, wp);
            weight_poly(cwbuf[1], ew[1], mw[1], 1, c, S->sigma, X, wp);
        }
        block_kernel_mom(acc, E, J, (long)n, B, nw, K2, S->kind == 0 ? NULL : cwt, cx);
        /* bounds (Lemma M2 + summation): X = X_b + e_x */
        mag_add(Xp, S->Xb + b, ex);
        mag_mul_ui(trig, err, 7); mag_set_d(tmp, ZF_EC); mag_add(trig, trig, tmp);
        double ng = ceil((double)B / 16.0);
        for (int j = 0; j < nw; j++)
        {
            for (int k = 0; k < K2; k++)
            {
                mag_t Xk, Xk1; mag_init(Xk); mag_init(Xk1);
                mag_pow_ui(Xk, Xp, k);
                if (k > 0) mag_pow_ui(Xk1, Xp, k - 1); else mag_zero(Xk1);
                /* m_w [ trig X^k + k X^{k-1} e_x + ((1+u)^{k+1} - 1)(1+E_c) X^k ] + e_w X^k */
                mag_mul(term, trig, Xk);
                mag_mul(kXe, Xk1, ex); mag_mul_ui(kXe, kXe, k); mag_add(term, term, kXe);
                mag_set_d(tmp, ((k + 1) * u * 1.0001) * (1.0 + ZF_EC)); mag_mul(tmp, tmp, Xk); mag_add(term, term, tmp);
                mag_mul(term, term, mw[j]);
                mag_mul(tmp, ew[j], Xk); mag_add(term, term, tmp);
                /* summation: (gamma_15 + 2 ng^2 u^2) m_w (1 + E_c) X^k (1+u)^{k+2} */
                mag_set_d(sumc, (15.0 * u / (1.0 - 15.0 * u) + 2.0 * ng * ng * u * u) * (1.0 + ZF_EC) * (1.0 + (k + 3) * u));
                mag_mul(tmp, sumc, mw[j]); mag_mul(tmp, tmp, Xk); mag_add(term, term, tmp);
                mag_mul_ui(term, term, (ulong)B);
                mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);
                mag_clear(Xk); mag_clear(Xk1);
                /* accumulate hi + lo */
                double *q = acc + ((j * K2 + k) * 2) * 2;
                arb_set_d(x, q[0]); arb_add(acb_realref(R->M + j * K2 + k), acb_realref(R->M + j * K2 + k), x, wp);
                arb_set_d(x, q[1]); arb_add(acb_realref(R->M + j * K2 + k), acb_realref(R->M + j * K2 + k), x, wp);
                arb_set_d(x, q[2]); arb_add(acb_imagref(R->M + j * K2 + k), acb_imagref(R->M + j * K2 + k), x, wp);
                arb_set_d(x, q[3]); arb_add(acb_imagref(R->M + j * K2 + k), acb_imagref(R->M + j * K2 + k), x, wp);
            }
            mag_mul_ui(tmp, mw[j], (ulong)B); mag_add(R->V + j, R->V + j, tmp);
        }
        n += (ulong)B; nbk++;
    }
    R->maxph = maxph; R->nblocks = nbk;
    flint_free(acc);
    arb_clear(x); arb_clear(zero); arb_clear(c);
    mag_clear(err); mag_clear(tmp); mag_clear(tmp2); mag_clear(ex); mag_clear(mxx); mag_clear(Xp); mag_clear(trig); mag_clear(sumc); mag_clear(term); mag_clear(kXe);
    for (int j = 0; j < 2; j++) { mag_clear(ew[j]); mag_clear(mw[j]); }
    for (int i = 0; i <= JMAX; i++) { arb_clear(L[i]); mag_clear(epsi[i]); }
    flint_cleanup();
    return NULL;
}

/* weight j at n (Arb): Z: n^{-1/2}; rows: j=0 n^{-sigma}, j=1 n^{sigma-1} ; l = log n given */
static void weight_arb(arb_t w, const zfm_session *S, int j, const arb_t l, ulong n, slong prec)
{
    if (S->kind == 0) { arb_set_ui(w, n); arb_rsqrt(w, w, prec); return; }
    if (j == 0) { arb_mul(w, S->sigma, l, prec); arb_neg(w, w); arb_exp(w, w, prec); }
    else { arb_sub_ui(w, S->sigma, 1, prec); arb_mul(w, w, l, prec); arb_exp(w, w, prec); }
}

zfm_session *zfm_new(const fmpz_t T0, double u0, double H, int kind, const arb_t sigma, const zf_params *P, double Delta, int K)
{
    double tb = now();
    zfm_session *S = flint_calloc(1, sizeof(zfm_session));
    fmpz_init_set(S->T0, T0); S->u0 = u0; S->H = H; S->Delta = Delta; S->kind = kind; S->nw = kind == 0 ? 1 : 2;
    if (K < 2 || K + 2 > ZFM_KMAX + 2) { fprintf(stderr, "zfm: K out of range\n"); abort(); }
    S->K = K; S->K2 = K + 2; S->P = *P;
    slong bits = fmpz_bits(T0) + 4; S->wp = 330 + bits; slong wp = S->wp;
    arb_init(S->sigma); arb_init(S->t0); arb_init(S->tau0);
    if (kind == 1) arb_set(S->sigma, sigma); else arb_set_d(S->sigma, 0.5);
    zf_height(S->t0, T0, u0);
    arb_t pi2, x, l, w, tt; arb_init(pi2); arb_init(x); arb_init(l); arb_init(w); arb_init(tt);
    arb_const_pi(pi2, wp); arb_mul_2exp_si(pi2, pi2, 1); arb_div(S->tau0, S->t0, pi2, wp);
    /* Nw = floor(sqrt((t0 + H)/2pi)) */
    arb_set_d(x, H); arb_add(tt, S->t0, x, wp); arb_div(tt, tt, pi2, wp); arb_sqrt(tt, tt, wp); arb_floor(tt, tt, wp);
    { fmpz_t f; fmpz_init(f); if (!arb_get_unique_fmpz(f, tt)) { fprintf(stderr, "zfm: Nw not unique\n"); abort(); } S->Nw = fmpz_get_ui(f); fmpz_clear(f); }
    /* buckets */
    slong cap = 64; S->nbeg = flint_malloc(sizeof(ulong) * (cap + 1)); slong nb = 0; ulong nn = 1;
    while (nn <= S->Nw)
    {
        if (nb + 2 > cap) { cap *= 2; S->nbeg = flint_realloc(S->nbeg, sizeof(ulong) * (cap + 1)); }
        S->nbeg[nb++] = nn;
        double nx = ceil((double)nn * exp(Delta));
        ulong nxt = (ulong)nx; if (nxt <= nn) nxt = nn + 1;
        if (nxt > S->Nw + 1) nxt = S->Nw + 1;
        nn = nxt;
    }
    S->nbeg[nb] = S->Nw + 1; S->nb = nb;
    S->Lb = flint_malloc(sizeof(double) * nb); S->Xb = _mag_vec_init(nb);
    for (slong b = 0; b < nb; b++)
    {
        ulong a0 = S->nbeg[b], a1 = S->nbeg[b + 1] - 1;
        S->Lb[b] = 0.5 * (log((double)a0) + log((double)a1));
        arb_t e0, e1; arb_init(e0); arb_init(e1);
        arb_log_ui(e0, a0, 128); arb_set_d(x, S->Lb[b]); arb_sub(e0, e0, x, 128); arb_abs(e0, e0);
        arb_log_ui(e1, a1, 128); arb_sub(e1, e1, x, 128); arb_abs(e1, e1);
        arb_max(e0, e0, e1, 128); arb_get_mag(S->Xb + b, e0);
        arb_clear(e0); arb_clear(e1);
    }
    S->M = _acb_vec_init(S->nw * nb * S->K2); S->V = _mag_vec_init(S->nw * nb);
    /* head: n < nhead (Z section 8 rule at t0) */
    double t0 = now();
    int J = P->J; long Bmin = 2 * (J + 1) > 32 ? 2 * (J + 1) : 32;
    double log2tau = log2(arf_get_d(arb_midref(S->tau0), ARF_RND_UP));
    ulong n = 1; slong b = 0;
    acb_t p, e; acb_init(p); acb_init(e);
    arb_t cc, ss, xb; arb_init(cc); arb_init(ss); arb_init(xb);
    mag_t mg; mag_init(mg);
    while (n <= S->Nw)
    {
        long B = choose_B((long)n, J, log2tau, P, (long)S->Nw);
        if (B >= Bmin) break;
        while (n >= S->nbeg[b + 1]) b++;
        arb_log_ui(l, n, wp);
        arb_mul(x, l, S->tau0, wp); arb_mul_2exp_si(x, x, 1); arb_sin_cos_pi(ss, cc, x, wp); arb_neg(ss, ss);
        arb_set(acb_realref(e), cc); arb_set(acb_imagref(e), ss);          /* e^{-i t0 log n} */
        arb_set_d(xb, S->Lb[b]); arb_sub(xb, l, xb, wp);                     /* log n - Lb */
        for (int j = 0; j < S->nw; j++)
        {
            weight_arb(w, S, j, l, n, wp);
            acb_mul_arb(p, e, w, wp);
            for (int k = 0; k < S->K2; k++) { acb_add(S->M + midx(S, j, b, k), S->M + midx(S, j, b, k), p, wp); acb_mul_arb(p, p, xb, wp); }
            arb_get_mag(mg, w); mag_add(S->V + j * nb + b, S->V + j * nb + b, mg);
        }
        n++;
    }
    S->nhead = n - 1; S->sec_head = now() - t0; t0 = now();
    /* fast part: bucket by bucket; long buckets split across threads */
    double maxph = 0, nblocks = 0;
    for (b = 0; b < nb && n <= S->Nw; b++)
    {
        ulong lo0 = S->nbeg[b] > n ? S->nbeg[b] : n, hi0 = S->nbeg[b + 1] - 1;
        if (lo0 > hi0) continue;
        ulong lo[16], hi[16];
        int T = split_ranges(lo, hi, lo0, hi0, P->threads, P->bmax);
        mrange_t R[16]; pthread_t th[16];
        for (int i = 0; i < T; i++)
        {
            R[i].S = S; R[i].b = b; R[i].n0 = lo[i]; R[i].n1 = hi[i];
            R[i].M = _acb_vec_init(S->nw * S->K2); R[i].err = _mag_vec_init(S->nw * S->K2); R[i].V = _mag_vec_init(S->nw);
        }
        if (T == 1) mom_range(&R[0]);
        else
        {
            for (int i = 0; i < T; i++) if (pthread_create(&th[i], NULL, mom_range, &R[i])) { fprintf(stderr, "pthread_create\n"); abort(); }
            for (int i = 0; i < T; i++) pthread_join(th[i], NULL);
        }
        for (int i = 0; i < T; i++)
        {
            for (int j = 0; j < S->nw; j++)
            {
                for (int k = 0; k < S->K2; k++)
                {
                    acb_ptr m = S->M + midx(S, j, b, k);
                    acb_add(m, m, R[i].M + j * S->K2 + k, wp);
                    arb_add_error_mag(acb_realref(m), R[i].err + j * S->K2 + k);
                    arb_add_error_mag(acb_imagref(m), R[i].err + j * S->K2 + k);
                }
                mag_add(S->V + j * nb + b, S->V + j * nb + b, R[i].V + j);
            }
            if (R[i].maxph > maxph) maxph = R[i].maxph;
            nblocks += R[i].nblocks;
            _acb_vec_clear(R[i].M, S->nw * S->K2); _mag_vec_clear(R[i].err, S->nw * S->K2); _mag_vec_clear(R[i].V, S->nw);
        }
        n = hi0 + 1;
    }
    S->sec_fast = now() - t0; S->blocks = nblocks; S->max_phase_err = maxph;
    acb_clear(p); acb_clear(e); arb_clear(cc); arb_clear(ss); arb_clear(xb); mag_clear(mg);
    arb_clear(pi2); arb_clear(x); arb_clear(l); arb_clear(w); arb_clear(tt);
    S->sec_build = now() - tb;
    return S;
}

void zfm_free(zfm_session *S)
{
    fmpz_clear(S->T0); arb_clear(S->sigma); arb_clear(S->t0); arb_clear(S->tau0);
    flint_free(S->nbeg); flint_free(S->Lb); _mag_vec_clear(S->Xb, S->nb);
    _acb_vec_clear(S->M, S->nw * S->nb * S->K2); _mag_vec_clear(S->V, S->nw * S->nb);
    flint_free(S);
}

/* F_j(t) (deriv = 0) or G_j(t) (deriv = 1) for all n <= N(t), at t = T0 + u (h = u - u0, |h| <= H required) */
static void zfm_sum(acb_t res, const zfm_session *S, int j, int deriv, double u, ulong Nt, slong prec)
{
    arb_t h, ab, x; acb_t c, z, inner, tmpc, mi; mag_t hm, rem, q, ex, fac;
    arb_init(h); arb_init(ab); arb_init(x); acb_init(c); acb_init(z); acb_init(inner); acb_init(tmpc); acb_init(mi);
    mag_init(hm); mag_init(rem); mag_init(q); mag_init(ex); mag_init(fac);
    int K = S->K;
    arb_set_d(h, u); arb_set_d(x, S->u0); arb_sub(h, h, x, ARF_PREC_EXACT);
    arb_get_mag(hm, h);
    if (mag_cmp_2exp_si(hm, 1000) > 0 || arf_cmpabs_d(arb_midref(h), S->H) > 0) { fprintf(stderr, "zfm: point outside session\n"); abort(); }
    /* coefficients c_k = (-i h)^k / k! */
    acb_ptr ck = _acb_vec_init(K + 1);
    acb_one(ck + 0);
    acb_set_arb(tmpc, h); acb_mul_onei(tmpc, tmpc); acb_neg(tmpc, tmpc);          /* -i h */
    for (int k = 1; k <= K; k++) { acb_mul(ck + k, ck + k - 1, tmpc, prec); acb_div_ui(ck + k, ck + k, k, prec); }
    acb_zero(res); mag_zero(rem);
    for (slong b = 0; b < S->nb; b++)
    {
        acb_srcptr Mb = S->M + midx(S, j, b, 0);
        if (!deriv) acb_dot(inner, NULL, 0, ck, 1, Mb, 1, K + 1, prec);
        else
        {
            acb_dot(inner, NULL, 0, ck, 1, Mb + 1, 1, K + 1, prec);
            acb_dot(mi, NULL, 0, ck, 1, Mb, 1, K + 1, prec);
            arb_set_d(x, S->Lb[b]); acb_mul_arb(mi, mi, x, prec); acb_add(inner, inner, mi, prec);
        }
        /* e^{-i h Lb} */
        arb_set_d(x, S->Lb[b]); arb_mul(ab, h, x, prec);
        arb_sin_cos(acb_imagref(z), acb_realref(z), ab, prec); acb_conj(z, z);
        acb_addmul(res, z, inner, prec);
        /* remainder V (|h| X)^{K+1}/(K+1)! e^{|h|X} [ * (|Lb| + X) ] */
        mag_mul(q, hm, S->Xb + b);
        mag_exp(ex, q);
        mag_pow_ui(q, q, K + 1);
        mag_rfac_ui(fac, K + 1);
        mag_mul(q, q, fac); mag_mul(q, q, ex); mag_mul(q, q, S->V + j * S->nb + b);
        if (deriv) { mag_t lx; mag_init(lx); mag_set_d(lx, fabs(S->Lb[b])); mag_add(lx, lx, S->Xb + b); mag_mul(q, q, lx); mag_clear(lx); }
        mag_add(rem, rem, q);
    }
    acb_add_error_mag(res, rem);
    _acb_vec_clear(ck, K + 1);
    /* subtract n in (Nt, Nw] */
    if (Nt < S->Nw)
    {
        arb_t t, l, w, cc, ss; arb_init(t); arb_init(l); arb_init(w); arb_init(cc); arb_init(ss);
        zf_height(t, S->T0, u);
        for (ulong n = Nt + 1; n <= S->Nw; n++)
        {
            arb_log_ui(l, n, S->wp);
            arb_mul(x, l, t, S->wp); arb_sin_cos(ss, cc, x, S->wp); arb_neg(ss, ss);
            arb_set(acb_realref(z), cc); arb_set(acb_imagref(z), ss);
            weight_arb(w, S, j, l, n, S->wp);
            acb_mul_arb(z, z, w, S->wp);
            if (deriv) acb_mul_arb(z, z, l, S->wp);
            acb_sub(res, res, z, prec);
        }
        arb_clear(t); arb_clear(l); arb_clear(w); arb_clear(cc); arb_clear(ss);
    }
    arb_clear(h); arb_clear(ab); arb_clear(x); acb_clear(c); acb_clear(z); acb_clear(inner); acb_clear(tmpc); acb_clear(mi);
    mag_clear(hm); mag_clear(rem); mag_clear(q); mag_clear(ex); mag_clear(fac);
}

/* Z(T0 + u) from a kind-0 session */
void zfm_Z(arb_t res, zfm_session *S, double u, zf_stats *St)
{
    double tt0 = now();
    slong wp = S->wp, prec = 192;
    arb_t t, pi2, Theta; acb_t s, th, corr, eith, F; mag_t rsb;
    arb_init(t); arb_init(pi2); arb_init(Theta); acb_init(s); acb_init(th); acb_init(corr); acb_init(eith); acb_init(F); mag_init(rsb);
    if (S->kind != 0) { fprintf(stderr, "zfm_Z: not a Z session\n"); abort(); }
    zf_height(t, S->T0, u);
    acb_set_arb(s, t);
    acb_dirichlet_hardy_theta(th, s, NULL, NULL, 1, wp);
    arb_set_d(acb_realref(s), 0.5); arb_set(acb_imagref(s), t);
    slong K;
    for (K = 2; K < 40; K++) { acb_dirichlet_zeta_rs_bound(rsb, s, K); if (mag_cmp_2exp_si(rsb, -100) < 0) break; }
    zf_rs_corr(corr, s, K, 128, St->N, rsb);
    ulong Nt = fmpz_get_ui(St->N);
    if (Nt > S->Nw) { fprintf(stderr, "zfm_Z: N(t) > Nw\n"); abort(); }
    zfm_sum(F, S, 0, 0, u, Nt, prec);
    acb_add(F, F, corr, wp);
    arb_sin_cos(acb_imagref(eith), acb_realref(eith), acb_realref(th), wp);
    acb_mul(F, F, eith, wp);
    arb_mul_2exp_si(res, acb_realref(F), 1);
    St->K = K; St->rs_bound = mag_get_d(rsb); St->sec_total = now() - tt0;
    arb_clear(t); arb_clear(pi2); arb_clear(Theta); acb_clear(s); acb_clear(th); acb_clear(corr); acb_clear(eith); acb_clear(F); mag_clear(rsb);
}

/* zeta(s), zeta'(s) at s = sigma + i(T0 + u) from a kind-1 session (assembly exactly as zf_row) */
int zfm_row(acb_t zeta, acb_t dzeta, zfm_session *S, double u, zf_stats *St)
{
    double tt0 = now();
    slong wp = S->wp, prec = 192;
    arb_t t; acb_t s, chi, dchi, a, b, H0, H1, G0, G1; acb_ptr Sm = _acb_vec_init(4);
    arb_init(t); acb_init(s); acb_init(chi); acb_init(dchi); acb_init(a); acb_init(b);
    acb_init(H0); acb_init(H1); acb_init(G0); acb_init(G1);
    if (S->kind != 1) { fprintf(stderr, "zfm_row: not a row session\n"); abort(); }
    zf_height(t, S->T0, u);
    arb_set(acb_realref(s), S->sigma); arb_set(acb_imagref(s), t);
    mag_t rb; mag_init(rb); slong K;
    acb_t sm; acb_init(sm); acb_set(sm, s); acb_conj(sm, sm); acb_neg(sm, sm); acb_add_ui(sm, sm, 1, wp);
    for (K = 3; K < 60; K++)
    {
        mag_t r2; mag_init(r2);
        acb_dirichlet_zeta_rs_bound(rb, s, K); acb_dirichlet_zeta_rs_bound(r2, sm, K);
        int good = mag_cmp_2exp_si(rb, -200) < 0 && mag_cmp_2exp_si(r2, -200) < 0;
        mag_clear(r2);
        if (good) break;
    }
    St->K = K;
    zf_rs_corr(H0, s, K, 256, St->N, rb);
    St->rs_bound = mag_get_d(rb);
    int ok = Hjet(H0, H1, s, St->N, K, 256, 0) && Hjet(G0, G1, s, St->N, K, 256, 1);
    {
        acb_t lp, g1, g2, h; acb_init(lp); acb_init(g1); acb_init(g2); acb_init(h);
        acb_const_pi(lp, wp); acb_log(lp, lp, wp);
        acb_sub_ui(h, s, 1, wp); acb_neg(h, h); acb_mul_2exp_si(h, h, -1);
        acb_lgamma(g1, h, wp); acb_digamma(a, h, wp);
        acb_mul_2exp_si(h, s, -1);
        acb_lgamma(g2, h, wp); acb_digamma(b, h, wp);
        acb_set_d(h, 0.5); acb_sub(h, s, h, wp); acb_mul(h, h, lp, wp);
        acb_add(h, h, g1, wp); acb_sub(h, h, g2, wp); acb_exp(chi, h, wp);
        acb_add(a, a, b, wp); acb_mul_2exp_si(a, a, -1); acb_sub(a, lp, a, wp);
        acb_mul(dchi, chi, a, wp);
        acb_clear(lp); acb_clear(g1); acb_clear(g2); acb_clear(h);
    }
    ulong Nt = fmpz_get_ui(St->N);
    if (Nt > S->Nw) { fprintf(stderr, "zfm_row: N(t) > Nw\n"); abort(); }
    /* S0 = F_A, S1 = -G_A, S2 = conj F_W, S3 = conj G_W */
    zfm_sum(Sm + 0, S, 0, 0, u, Nt, prec);
    zfm_sum(Sm + 1, S, 0, 1, u, Nt, prec); acb_neg(Sm + 1, Sm + 1);
    zfm_sum(Sm + 2, S, 1, 0, u, Nt, prec); acb_conj(Sm + 2, Sm + 2);
    zfm_sum(Sm + 3, S, 1, 1, u, Nt, prec); acb_conj(Sm + 3, Sm + 3);
    acb_add(a, Sm + 2, G0, wp);
    acb_mul(b, chi, a, wp); acb_add(zeta, Sm + 0, H0, wp); acb_add(zeta, zeta, b, wp);
    acb_mul(b, dchi, a, wp); acb_add(dzeta, Sm + 1, H1, wp); acb_add(dzeta, dzeta, b, wp);
    acb_add(a, Sm + 3, G1, wp); acb_mul(b, chi, a, wp); acb_add(dzeta, dzeta, b, wp);
    St->sec_total = now() - tt0;
    mag_clear(rb); acb_clear(sm);
    arb_clear(t); acb_clear(s); acb_clear(chi); acb_clear(dchi); acb_clear(a); acb_clear(b);
    acb_clear(H0); acb_clear(H1); acb_clear(G0); acb_clear(G1); _acb_vec_clear(Sm, 4);
    return ok;
}

void zfm_info(const zfm_session *S, double *sec_build, double *sec_head, double *sec_fast, double *nb, double *Nw, double *nhead, double *blocks, double *maxph)
{
    *sec_build = S->sec_build; *sec_head = S->sec_head; *sec_fast = S->sec_fast; *nb = (double)S->nb; *Nw = (double)S->Nw;
    *nhead = (double)S->nhead; *blocks = S->blocks; *maxph = S->max_phase_err;
}
