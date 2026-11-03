/* rd3.c (review2, 2026-10-19): unit + end-to-end driver for zfast.  Compiled as ONE translation unit with a production or mutant
   copy of zfast.c:   cc ... -I<srcdir> rd2.c     (#include "zfast.c" below; static helpers become callable).
   -DV10B for the v10b sources (no zfm_new2 / zfm_row3).
   Commands (stdin, one per line); output one JSON line each:
     KER n seed                      kernel cs_core (via zf_cos2pi and cos2pi_only) vs Arb on n random + structured v
     PH T0 u n0 B J                  zf_phase_test: observed max phase error vs the bound E_ph (turns)
     WP T0 n0 B kind a nsamp         weight_poly kind 0/1/2 (n^-sigma, n^(sigma-1), log) or kind 3 = logL_poly (Lb = log c + 0.03):
                                     max |p_hat(k - X) - f(n0 + k)| over samples vs the bound e
     Z  T0 u J bmax log2i kcorr      single-point zf_Z
     SZ T0 u0 H Delta K J nu u...    kind-0 session: Z at the nu offsets u
     S3 T0 u0 H Delta K J a nu u...  kind-0 session: rows by complex shift (v12 zfm_row3), P and zeta, zeta'
     S1 T0 u0 H Delta K J a nu u...  kind-1 session (v10b rows), P and zeta, zeta'
     R1 T0 u a J                     single-point zf_row
*/
#include "zfast.c"
#include <inttypes.h>
static void arb_sub_d(arb_t r, const arb_t a, double d, slong prec) { arb_t t; arb_init(t); arb_set_d(t, d); arb_sub(r, a, t, prec); arb_clear(t); }

static void pb(const char *k, const arb_t x) { char *s = arb_get_str(x, 40, 0); printf("\"%s\": \"%s\"", k, s); flint_free(s); }
static void sigma_a(arb_t sig, double a)
{
    arb_t pi, h; arb_init(pi); arb_init(h);
    arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512);
    arb_set_d(h, 0.5); arb_add(sig, sig, h, 512); arb_clear(pi); arb_clear(h);
}
static uint64_t rng_s;
static uint64_t rnd(void) { rng_s ^= rng_s << 13; rng_s ^= rng_s >> 7; rng_s ^= rng_s << 17; return rng_s; }

static void cmd_ker(long n, uint64_t seed)
{
    rng_s = seed | 1; double mc = 0, ms = 0, mo = 0; arb_t x, r; arb_init(x); arb_init(r);
    for (long i = 0; i < n; i++)
    {
        uint64_t v;
        if (i < 64) { uint64_t q = (uint64_t)(i & 3); int64_t d[16] = {0, 1, -1, 2, -2, (int64_t)1 << 61, -((int64_t)1 << 61), ((int64_t)1 << 61) - 1, -(((int64_t)1 << 61) - 1), 7, -7, (int64_t)1 << 59, -((int64_t)1 << 59), 1000, -1000, 3}; v = (q << 62) + (uint64_t)d[(i >> 2) & 15]; }
        else if (i % 3 == 0) v = ((rnd() & 3) << 62) + (UINT64_C(1) << 61) - (rnd() >> 40);
        else v = rnd();
        double c, s; zf_cos2pi(&c, &s, v); double c2 = cos2pi_only(v);
        arb_set_ui(x, v); arb_mul_2exp_si(x, x, -63);
        arb_cos_pi(r, x, 128); arb_sub_d(r, r, c, 128); double e = arf_get_d(arb_midref(r), ARF_RND_UP); e = fabs(e) + mag_get_d(arb_radref(r)); if (e > mc) mc = e;
        arb_cos_pi(r, x, 128); arb_sub_d(r, r, c2, 128); e = fabs(arf_get_d(arb_midref(r), ARF_RND_UP)) + mag_get_d(arb_radref(r)); if (e > mo) mo = e;
        arb_sin_pi(r, x, 128); arb_sub_d(r, r, s, 128); e = fabs(arf_get_d(arb_midref(r), ARF_RND_UP)) + mag_get_d(arb_radref(r)); if (e > ms) ms = e;
    }
    printf("{\"cmd\": \"KER\", \"n\": %ld, \"max_cos\": %.6e, \"max_cos_only\": %.6e, \"max_sin\": %.6e, \"ZF_EC\": %.6e, \"ok\": %d}\n", n, mc, mo, ms, ZF_EC,
           mc <= ZF_EC && ms <= ZF_EC && mo <= ZF_EC);
    arb_clear(x); arb_clear(r);
}

static void cmd_wp(const fmpz_t T0, ulong n0, long B, int kind, double a, long nsamp)
{
    slong wp = 330 + fmpz_bits(T0) + 4;
    arb_t c, x, sig, f, Lb; mag_t e, mx; double co[RDEG + 1];
    arb_init(c); arb_init(x); arb_init(sig); arb_init(f); arb_init(Lb); mag_init(e); mag_init(mx);
    sigma_a(sig, a);
    double X = 0.5 * (double)(B - 1);
    arb_set_ui(c, n0); arb_set_d(x, X); arb_add(c, c, x, wp);
    double Lbd = 0;
    if (kind <= 2) weight_poly(co, e, mx, kind, c, sig, X, wp);
    else { arb_log(Lb, c, 128); Lbd = arf_get_d(arb_midref(Lb), ARF_RND_NEAR) + 0.03; logL_poly(co, e, mx, c, Lbd, X, wp); }
    double mxo = 0, mag = 0;
    for (long i = 0; i < nsamp; i++)
    {
        long k = (nsamp >= B) ? i % B : (i < 2 ? (i == 0 ? 0 : B - 1) : (long)(rnd() % (uint64_t)B));
        if (nsamp >= B && i >= B) break;
        double xx = (double)k - X, p = horner6(co, xx);
        arb_set_ui(f, n0 + (ulong)k);
        if (kind == 0) { arb_neg(x, sig); arb_pow(f, f, x, wp); }
        else if (kind == 1) { arb_sub_ui(x, sig, 1, wp); arb_pow(f, f, x, wp); }
        else if (kind == 2) arb_log(f, f, wp);
        else { arb_log(f, f, wp); arb_set_d(x, Lbd); arb_sub(f, f, x, wp); }
        arb_sub_d(f, f, p, wp);
        double d = fabs(arf_get_d(arb_midref(f), ARF_RND_UP)) + mag_get_d(arb_radref(f));
        if (d > mxo) mxo = d;
        if (fabs(p) > mag) mag = fabs(p);
    }
    double eb = mag_get_d(e);
    printf("{\"cmd\": \"WP\", \"n0\": %lu, \"B\": %ld, \"kind\": %d, \"a\": %.3f, \"obs\": %.6e, \"bound\": %.6e, \"ratio\": %.4f, \"maxabs\": %.6e, \"mx\": %.6e, \"ok\": %d}\n",
           n0, B, kind, a, mxo, eb, eb > 0 ? mxo / eb : 0.0, mag, mag_get_d(mx), mxo <= eb && mag <= mag_get_d(mx));
    arb_clear(c); arb_clear(x); arb_clear(sig); arb_clear(f); arb_clear(Lb); mag_clear(e); mag_clear(mx);
}

static void prow(acb_t z, acb_t dz, int ok, double u)
{
    acb_t q; acb_init(q); acb_div(q, dz, z, 256); acb_neg(q, q);
    printf("{\"u\": \"%a\", \"ok\": %d, ", u, ok); pb("P", acb_realref(q)); printf(", ");
    pb("zr", acb_realref(z)); printf(", "); pb("zi", acb_imagref(z)); printf(", "); pb("dzr", acb_realref(dz)); printf(", "); pb("dzi", acb_imagref(dz));
    printf("}");
    acb_clear(q);
}

int main(void)
{
    char line[1 << 16];
    fmpz_t T0; fmpz_init(T0);
    while (fgets(line, sizeof line, stdin))
    {
        char cmd[8], T0s[64]; int off = 0;
        if (sscanf(line, "%7s%n", cmd, &off) != 1) continue;
        char *p = line + off; int o2;
        if (!strcmp(cmd, "KER")) { long n; unsigned long long sd; sscanf(p, "%ld %llu", &n, &sd); cmd_ker(n, sd); }
        else if (!strcmp(cmd, "PH"))
        {
            char us[64]; ulong n0; long B; int J; sscanf(p, "%63s %63s %lu %ld %d", T0s, us, &n0, &B, &J); fmpz_set_str(T0, T0s, 10);
            double mx, bd; zf_phase_test(&mx, &bd, T0, strtod(us, 0), n0, B, J);
            printf("{\"cmd\": \"PH\", \"T0\": \"%s\", \"n0\": %lu, \"B\": %ld, \"J\": %d, \"obs\": %.6e, \"bound\": %.6e, \"ratio\": %.4f, \"ok\": %d}\n", T0s, n0, B, J, mx, bd, mx / bd, mx <= bd);
        }
        else if (!strcmp(cmd, "WP"))
        {
            ulong n0; long B, ns; int kind; double a; sscanf(p, "%63s %lu %ld %d %lf %ld", T0s, &n0, &B, &kind, &a, &ns); fmpz_set_str(T0, T0s, 10);
            rng_s = 12345 + n0; cmd_wp(T0, n0, B, kind, a, ns);
        }
        else if (!strcmp(cmd, "Z"))
        {
            char us[64]; zf_params P; zf_params_default(&P); long bm; double l2; long kc;
            sscanf(p, "%63s %63s %d %ld %lf %ld", T0s, us, &P.J, &bm, &l2, &kc); P.bmax = bm; P.log2_interp = l2; P.kcorr = kc;
            fmpz_set_str(T0, T0s, 10); double u = strtod(us, 0);
            arb_t Z; arb_init(Z); zf_stats S; zf_stats_init(&S); zf_Z(Z, T0, u, &P, &S);
            printf("{\"cmd\": \"Z\", \"T0\": \"%s\", \"u\": \"%a\", ", T0s, u); pb("Z", Z); printf(", \"rad\": %.4e, \"K\": %ld, \"N\": %lu}\n", mag_get_d(arb_radref(Z)), (long)S.K, fmpz_get_ui(S.N));
            zf_stats_clear(&S); arb_clear(Z);
        }
        else if (!strcmp(cmd, "SZ") || !strcmp(cmd, "S3") || !strcmp(cmd, "S1"))
        {
            char us[64]; double H, D, a = 0; int K, J, nu; zf_params P; zf_params_default(&P);
            if (!strcmp(cmd, "SZ")) { sscanf(p, "%63s %63s %lf %lf %d %d %d%n", T0s, us, &H, &D, &K, &J, &nu, &o2); }
            else { sscanf(p, "%63s %63s %lf %lf %d %d %lf %d%n", T0s, us, &H, &D, &K, &J, &a, &nu, &o2); }
            p += o2; P.J = J; fmpz_set_str(T0, T0s, 10); double u0 = strtod(us, 0);
            arb_t sig; arb_init(sig); sigma_a(sig, a > 0 ? a : 1.0);
            arb_t half; arb_init(half); arb_set_d(half, 0.5);
            zfm_session *S = zfm_new(T0, u0, H, !strcmp(cmd, "S1") ? 1 : 0, !strcmp(cmd, "S1") ? sig : half, &P, D, K);
            printf("{\"cmd\": \"%s\", \"T0\": \"%s\", \"u0\": \"%a\", \"H\": %g, \"Delta\": %g, \"K\": %d, \"J\": %d, \"a\": %g, \"Nw\": %lu, \"nhead\": %lu, \"sec_build\": %.3f, \"pts\": [", cmd, T0s, u0, H, D, K, J, a, S->Nw, S->nhead, S->sec_build);
            for (int i = 0; i < nu; i++)
            {
                char ub[64]; int o3; if (sscanf(p, "%63s%n", ub, &o3) != 1) break; p += o3; double u = strtod(ub, 0);
                zf_stats St; zf_stats_init(&St);
                if (i) printf(", ");
                if (!strcmp(cmd, "SZ"))
                {
                    arb_t Z; arb_init(Z); zfm_Z(Z, S, u, &St);
                    printf("{\"u\": \"%a\", ", u); pb("Z", Z); printf(", \"N\": %lu}", fmpz_get_ui(St.N)); arb_clear(Z);
                }
                else
                {
                    acb_t z, dz; acb_init(z); acb_init(dz); int ok;
#ifndef V10B
                    if (!strcmp(cmd, "S3")) ok = zfm_row3(z, dz, S, sig, u, &St); else
#endif
                    ok = zfm_row(z, dz, S, u, &St);
                    prow(z, dz, ok, u); acb_clear(z); acb_clear(dz);
                }
                zf_stats_clear(&St); fflush(stdout);
            }
            printf("]}\n");
            zfm_free(S); arb_clear(sig); arb_clear(half);
        }
        else if (!strcmp(cmd, "R1"))
        {
            char us[64]; double a; int J; sscanf(p, "%63s %63s %lf %d", T0s, us, &a, &J); fmpz_set_str(T0, T0s, 10);
            zf_params P; zf_params_default(&P); P.J = J; arb_t sig; arb_init(sig); sigma_a(sig, a);
            acb_t z, dz; acb_init(z); acb_init(dz); zf_stats St; zf_stats_init(&St);
            double u = strtod(us, 0); int ok = zf_row(z, dz, T0, u, sig, &P, &St);
            printf("{\"cmd\": \"R1\", \"T0\": \"%s\", \"a\": %g, \"pt\": ", T0s, a); prow(z, dz, ok, u); printf("}\n");
            acb_clear(z); acb_clear(dz); zf_stats_clear(&St); arb_clear(sig);
        }
        fflush(stdout);
    }
    return 0;
}
