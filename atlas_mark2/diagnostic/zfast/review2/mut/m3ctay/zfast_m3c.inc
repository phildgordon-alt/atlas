/* v12 (THEORY_M5b): rows from the Z moments (j = 0, weight n^{-1/2}) by the complex shift h' = h - i*ws*b, b = sigma - 1/2.
   ws = +1: weight n^{-sigma}; ws = -1: weight n^{sigma-1}.  Included after zfast_m3b.inc. */

static void zfm_sum_c(acb_t res, const zfm_session *S, const arb_t b, int ws, int deriv, double u, ulong Nt, slong prec)
{
    arb_t h, x; acb_t hc, mih, z, inner, mi, tmpc; mag_t hm, rem, q, ex, fac, zb;
    arb_init(h); arb_init(x); acb_init(hc); acb_init(mih); acb_init(z); acb_init(inner); acb_init(mi); acb_init(tmpc);
    mag_init(hm); mag_init(rem); mag_init(q); mag_init(ex); mag_init(fac); mag_init(zb);
    int K = S->K;
    if (S->kind == 1) { fprintf(stderr, "zfm_sum_c: needs Z moments\n"); abort(); }
    arb_set_d(h, u); arb_set_d(x, S->u0); arb_sub(h, h, x, ARF_PREC_EXACT);
    if (arf_cmpabs_d(arb_midref(h), S->H) > 0) { fprintf(stderr, "zfm: point outside session\n"); abort(); }
    /* hc = h - i ws b */
    arb_set(acb_realref(hc), h); arb_set(acb_imagref(hc), b); if (ws > 0) arb_neg(acb_imagref(hc), acb_imagref(hc));
    acb_get_mag(hm, hc);
    acb_mul_onei(mih, hc); acb_neg(mih, mih);                  /* -i hc */
    acb_ptr ck = _acb_vec_init(K + 1);
    acb_one(ck + 0);
    for (int k = 1; k <= K; k++) { acb_mul(ck + k, ck + k - 1, mih, prec); acb_div_ui(ck + k, ck + k, k, prec); }
    acb_zero(res); mag_zero(rem);
    for (slong bb = 0; bb < S->nb; bb++)
    {
        acb_srcptr Mb = S->M + midx(S, 0, bb, 0);
        if (!deriv) acb_dot(inner, NULL, 0, ck, 1, Mb, 1, K + 1, prec);
        else
        {
            acb_dot(inner, NULL, 0, ck, 1, Mb + 1, 1, K + 1, prec);
            acb_dot(mi, NULL, 0, ck, 1, Mb, 1, K + 1, prec);
            arb_set_d(x, S->Lb[bb]); acb_mul_arb(mi, mi, x, prec); acb_add(inner, inner, mi, prec);
        }
        arb_set_d(x, S->Lb[bb]); acb_mul_arb(z, mih, x, prec); acb_exp(z, z, prec);     /* e^{-i hc Lb} */
        acb_addmul(res, z, inner, prec);
        acb_get_mag(zb, z);
        mag_mul(q, hm, S->Xb + bb); mag_exp(ex, q); mag_pow_ui(q, q, K + 1); mag_rfac_ui(fac, K + 1);
        mag_mul(q, q, fac); mag_mul(q, q, ex); mag_mul(q, q, S->V + bb); mag_mul(q, q, zb); mag_div_ui(q, q, 10);
        if (deriv) { mag_t lx; mag_init(lx); mag_set_d(lx, fabs(S->Lb[bb])); mag_add(lx, lx, S->Xb + bb); mag_mul(q, q, lx); mag_clear(lx); }
        mag_add(rem, rem, q);
    }
    acb_add_error_mag(res, rem);
    _acb_vec_clear(ck, K + 1);
    if (Nt < S->Nw)
    {
        arb_t t, l, w, cc, ss, e; arb_init(t); arb_init(l); arb_init(w); arb_init(cc); arb_init(ss); arb_init(e);
        zf_height(t, S->T0, u);
        for (ulong n = Nt + 1; n <= S->Nw; n++)
        {
            arb_log_ui(l, n, S->wp);
            arb_mul(x, l, t, S->wp); arb_sin_cos(ss, cc, x, S->wp); arb_neg(ss, ss);
            arb_set(acb_realref(z), cc); arb_set(acb_imagref(z), ss);
            /* weight n^{-1/2 - ws b} */
            arb_set_d(e, 0.5); if (ws > 0) arb_add(e, e, b, S->wp); else arb_sub(e, e, b, S->wp);
            arb_mul(w, e, l, S->wp); arb_neg(w, w); arb_exp(w, w, S->wp);
            acb_mul_arb(z, z, w, S->wp);
            if (deriv) acb_mul_arb(z, z, l, S->wp);
            acb_sub(res, res, z, prec);
        }
        arb_clear(t); arb_clear(l); arb_clear(w); arb_clear(cc); arb_clear(ss); arb_clear(e);
    }
    arb_clear(h); arb_clear(x); acb_clear(hc); acb_clear(mih); acb_clear(z); acb_clear(inner); acb_clear(mi); acb_clear(tmpc);
    mag_clear(hm); mag_clear(rem); mag_clear(q); mag_clear(ex); mag_clear(fac); mag_clear(zb);
}

/* zeta(s), zeta'(s) at s = sigma + i(T0+u) from the Z moments of a kind-0 (or kind-2) session; assembly as zfm_row2 */
int zfm_row3(acb_t zeta, acb_t dzeta, zfm_session *S, const arb_t sigma, double u, zf_stats *St)
{
    double tt0 = now();
    slong wp = S->wp, prec = 192;
    arb_t t, b; acb_t s, chi, dchi, a, bb, H0, H1, G0, G1; acb_ptr Sm = _acb_vec_init(4);
    arb_init(t); arb_init(b); acb_init(s); acb_init(chi); acb_init(dchi); acb_init(a); acb_init(bb);
    acb_init(H0); acb_init(H1); acb_init(G0); acb_init(G1);
    if (!(arf_cmp_si(arb_midref(sigma), 1) > 0)) { fprintf(stderr, "zfm_row3: sigma > 1 required\n"); abort(); }
    arb_set_d(b, 0.5); arb_sub(b, sigma, b, 512);
    zf_height(t, S->T0, u);
    arb_set(acb_realref(s), sigma); arb_set(acb_imagref(s), t);
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
        acb_lgamma(g2, h, wp); acb_digamma(bb, h, wp);
        acb_set_d(h, 0.5); acb_sub(h, s, h, wp); acb_mul(h, h, lp, wp);
        acb_add(h, h, g1, wp); acb_sub(h, h, g2, wp); acb_exp(chi, h, wp);
        acb_add(a, a, bb, wp); acb_mul_2exp_si(a, a, -1); acb_sub(a, lp, a, wp);
        acb_mul(dchi, chi, a, wp);
        acb_clear(lp); acb_clear(g1); acb_clear(g2); acb_clear(h);
    }
    ulong Nt = fmpz_get_ui(St->N);
    if (Nt > S->Nw) { fprintf(stderr, "zfm_row3: N(t) > Nw\n"); abort(); }
    zfm_sum_c(Sm + 0, S, b, +1, 0, u, Nt, prec);
    zfm_sum_c(Sm + 1, S, b, +1, 1, u, Nt, prec); acb_neg(Sm + 1, Sm + 1);
    zfm_sum_c(Sm + 2, S, b, -1, 0, u, Nt, prec); acb_conj(Sm + 2, Sm + 2);
    zfm_sum_c(Sm + 3, S, b, -1, 1, u, Nt, prec); acb_conj(Sm + 3, Sm + 3);
    acb_add(a, Sm + 2, G0, wp);
    acb_mul(bb, chi, a, wp); acb_add(zeta, Sm + 0, H0, wp); acb_add(zeta, zeta, bb, wp);
    acb_mul(bb, dchi, a, wp); acb_add(dzeta, Sm + 1, H1, wp); acb_add(dzeta, dzeta, bb, wp);
    acb_add(a, Sm + 3, G1, wp); acb_mul(bb, chi, a, wp); acb_add(dzeta, dzeta, bb, wp);
    St->sec_total = now() - tt0;
    mag_clear(rb); acb_clear(sm);
    arb_clear(t); arb_clear(b); acb_clear(s); acb_clear(chi); acb_clear(dchi); acb_clear(a); acb_clear(bb);
    acb_clear(H0); acb_clear(H1); acb_clear(G0); acb_clear(G1); _acb_vec_clear(Sm, 4);
    return ok;
}
