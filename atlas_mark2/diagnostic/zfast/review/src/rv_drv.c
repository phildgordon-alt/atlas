/* rv_drv.c (independent review, 2026-10-19): test driver for a zfast build (production v10b sources or a mutant copy).
   Commands on stdin, one per line; JSON lines on stdout.  Balls are printed with arb_get_str (enclosures).
     Z   T0 u J bmax kcorr log2interp threads       single-point zf_Z with explicit params (u as C float literal, hex ok)
     PH  T0 u n0 B J                                 zf_phase_test (observed max phase error vs bound, turns)
     SN  T0 u0 H kind a Delta K J threads            new session (kind 0 = Z, 1 = rows at sigma = 1/2 + pi/(2a)); prints id
     SZ  id u                                        session Z
     SR  id u                                        session row: P = Re(-zeta'/zeta), zeta, zeta'
     ROW T0 u a J threads                            single-point zf_row
     CS  v                                           kernel cos/sin of 2 pi v/2^64 (v decimal uint64), printed as hex doubles */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include "zfast.h"

static void pball(const char *key, const arb_t x) { char *s = arb_get_str(x, 45, ARB_STR_MORE); printf("\"%s\": \"%s\"", key, s); flint_free(s); }
static void sigma_of(arb_t sig, double a)
{
    arb_t pi, h; arb_init(pi); arb_init(h);
    arb_const_pi(pi, 512); arb_set_d(sig, a); arb_mul_2exp_si(sig, sig, 1); arb_div(sig, pi, sig, 512);
    arb_set_d(h, 0.5); arb_add(sig, sig, h, 512); arb_clear(pi); arb_clear(h);
}
static void prow(const acb_t z, const acb_t dz)
{
    acb_t q; acb_init(q); acb_div(q, dz, z, 256); acb_neg(q, q);
    pball("P", acb_realref(q)); printf(", "); pball("zr", acb_realref(z)); printf(", "); pball("zi", acb_imagref(z)); printf(", ");
    pball("dzr", acb_realref(dz)); printf(", "); pball("dzi", acb_imagref(dz));
    acb_clear(q);
}

int main(void)
{
    char line[4096], cmd[16], T0s[256];
    zfm_session *sess[256]; int ns = 0;
    fmpz_t T0; fmpz_init(T0);
    while (fgets(line, sizeof line, stdin))
    {
        if (sscanf(line, "%15s", cmd) != 1) continue;
        if (!strcmp(cmd, "Z"))
        {
            char us[64]; int J, th; long bmax, kc; double l2;
            if (sscanf(line, "%*s %255s %63s %d %ld %ld %lf %d", T0s, us, &J, &bmax, &kc, &l2, &th) != 7) { printf("{\"err\": \"parse\"}\n"); continue; }
            double u = strtod(us, 0); fmpz_set_str(T0, T0s, 10);
            zf_params P; zf_params_default(&P); P.J = J; P.bmax = bmax; P.kcorr = kc; P.log2_interp = l2; P.threads = th;
            zf_stats S; zf_stats_init(&S); arb_t Z; arb_init(Z);
            zf_Z(Z, T0, u, &P, &S);
            printf("{\"cmd\": \"Z\", \"T0\": \"%s\", \"u\": \"%s\", ", T0s, us); pball("Z", Z);
            printf(", \"rad\": %.6e, \"N\": %lu, \"K\": %ld, \"rs_bound\": %.3e, \"maxph\": %.3e, \"sumerr\": %.3e, \"sec\": %.3f}\n",
                   mag_get_d(arb_radref(Z)), fmpz_get_ui(S.N), S.K, S.rs_bound, S.max_phase_err, S.sum_err_fast, S.sec_total);
            arb_clear(Z); zf_stats_clear(&S);
        }
        else if (!strcmp(cmd, "PH"))
        {
            char us[64]; unsigned long n0; long B; int J; double mx, bd;
            if (sscanf(line, "%*s %255s %63s %lu %ld %d", T0s, us, &n0, &B, &J) != 5) { printf("{\"err\": \"parse\"}\n"); continue; }
            fmpz_set_str(T0, T0s, 10);
            zf_phase_test(&mx, &bd, T0, strtod(us, 0), n0, B, J);
            printf("{\"cmd\": \"PH\", \"T0\": \"%s\", \"u\": \"%s\", \"n0\": %lu, \"B\": %ld, \"J\": %d, \"maxerr\": %.6e, \"bound\": %.6e}\n", T0s, us, n0, B, J, mx, bd);
        }
        else if (!strcmp(cmd, "SN"))
        {
            char us[64]; double H, a, D; int kind, K, J, th;
            if (sscanf(line, "%*s %255s %63s %lf %d %lf %lf %d %d %d", T0s, us, &H, &kind, &a, &D, &K, &J, &th) != 9) { printf("{\"err\": \"parse\"}\n"); continue; }
            fmpz_set_str(T0, T0s, 10);
            zf_params P; zf_params_default(&P); P.J = J; P.threads = th;
            arb_t sig; arb_init(sig); if (kind == 1) sigma_of(sig, a);
            sess[ns] = zfm_new(T0, strtod(us, 0), H, kind, sig, &P, D, K);
            double sb, sh, sf, nb, Nw, nhd, bl, mp; zfm_info(sess[ns], &sb, &sh, &sf, &nb, &Nw, &nhd, &bl, &mp);
            printf("{\"cmd\": \"SN\", \"id\": %d, \"sec_build\": %.3f, \"buckets\": %.0f, \"Nw\": %.0f, \"nhead\": %.0f, \"maxph\": %.3e}\n", ns, sb, nb, Nw, nhd, mp);
            ns++; arb_clear(sig);
        }
        else if (!strcmp(cmd, "SZ"))
        {
            int id; char us[64];
            if (sscanf(line, "%*s %d %63s", &id, us) != 2) { printf("{\"err\": \"parse\"}\n"); continue; }
            arb_t Z; arb_init(Z); zf_stats St; zf_stats_init(&St);
            zfm_Z(Z, sess[id], strtod(us, 0), &St);
            printf("{\"cmd\": \"SZ\", \"id\": %d, \"u\": \"%s\", ", id, us); pball("Z", Z);
            printf(", \"rad\": %.6e, \"N\": %lu}\n", mag_get_d(arb_radref(Z)), fmpz_get_ui(St.N));
            arb_clear(Z); zf_stats_clear(&St);
        }
        else if (!strcmp(cmd, "SR"))
        {
            int id; char us[64];
            if (sscanf(line, "%*s %d %63s", &id, us) != 2) { printf("{\"err\": \"parse\"}\n"); continue; }
            acb_t z, dz; acb_init(z); acb_init(dz); zf_stats St; zf_stats_init(&St);
            int ok = zfm_row(z, dz, sess[id], strtod(us, 0), &St);
            printf("{\"cmd\": \"SR\", \"id\": %d, \"u\": \"%s\", \"ok\": %d, ", id, us, ok); prow(z, dz); printf(", \"N\": %lu}\n", fmpz_get_ui(St.N));
            acb_clear(z); acb_clear(dz); zf_stats_clear(&St);
        }
        else if (!strcmp(cmd, "ROW"))
        {
            char us[64]; double a; int J, th;
            if (sscanf(line, "%*s %255s %63s %lf %d %d", T0s, us, &a, &J, &th) != 5) { printf("{\"err\": \"parse\"}\n"); continue; }
            fmpz_set_str(T0, T0s, 10);
            zf_params P; zf_params_default(&P); P.J = J; P.threads = th;
            arb_t sig; arb_init(sig); sigma_of(sig, a);
            acb_t z, dz; acb_init(z); acb_init(dz); zf_stats S; zf_stats_init(&S);
            int ok = zf_row(z, dz, T0, strtod(us, 0), sig, &P, &S);
            printf("{\"cmd\": \"ROW\", \"T0\": \"%s\", \"u\": \"%s\", \"a\": %.17g, \"ok\": %d, ", T0s, us, a, ok); prow(z, dz); printf(", \"N\": %lu}\n", fmpz_get_ui(S.N));
            acb_clear(z); acb_clear(dz); zf_stats_clear(&S); arb_clear(sig);
        }
        else if (!strcmp(cmd, "CS"))
        {
            unsigned long long v; double c, s;
            if (sscanf(line, "%*s %llu", &v) != 1) { printf("{\"err\": \"parse\"}\n"); continue; }
            zf_cos2pi(&c, &s, (uint64_t)v);
            printf("{\"cmd\": \"CS\", \"v\": \"%llu\", \"c\": \"%a\", \"s\": \"%a\"}\n", v, c, s);
        }
        fflush(stdout);
    }
    fmpz_clear(T0);
    return 0;
}
