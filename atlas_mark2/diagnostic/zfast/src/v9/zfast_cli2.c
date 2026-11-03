/* zfast_cli: evaluate Z at exact heights.  Input lines on stdin: "T0 u" (T0 decimal integer, u a decimal or hex binary64 that
   strtod parses exactly, e.g. Python repr(float)).  Output: one JSON object per line.
   Options: --J j  --bmax b  --interp l2  --K k */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include "zfast.h"

int main(int argc, char **argv)
{
    zf_params P; zf_params_default(&P);
    for (int i = 1; i < argc; i++)
    {
        if (!strcmp(argv[i], "--J") && i + 1 < argc) P.J = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--bmax") && i + 1 < argc) P.bmax = atol(argv[++i]);
        else if (!strcmp(argv[i], "--interp") && i + 1 < argc) P.log2_interp = atof(argv[++i]);
        else if (!strcmp(argv[i], "--K") && i + 1 < argc) P.kcorr = atol(argv[++i]);
        else if (!strcmp(argv[i], "--threads") && i + 1 < argc) P.threads = atoi(argv[++i]);
        else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    char T0s[200], us[200];
    fmpz_t T0; fmpz_init(T0);
    arb_t Z; arb_init(Z);
    while (scanf("%199s %199s", T0s, us) == 2)
    {
        if (fmpz_set_str(T0, T0s, 10)) { fprintf(stderr, "bad T0\n"); return 2; }
        char *end; double u = strtod(us, &end);
        if (*end) { fprintf(stderr, "bad u\n"); return 2; }
        zf_stats S; zf_stats_init(&S);
        zf_Z(Z, T0, u, &P, &S);
        char *zs = arb_get_str(Z, 30, 0);
        char *mid = arf_get_str(arb_midref(Z), 25);
        struct rusage ru; getrusage(RUSAGE_SELF, &ru);
        printf("{\"T0\": \"%s\", \"u\": \"%s\", \"u_hex\": \"%a\", \"Z\": \"%s\", \"Z_mid\": \"%s\", \"Z_rad\": %.6e, "
               "\"N\": %lu, \"J\": %d, \"threads\": %d, \"bmax\": %ld, \"head_terms\": %.0f, \"blocks\": %.0f, \"terms_fast\": %.0f, "
               "\"max_phase_err\": %.3e, \"sum_err_fast\": %.3e, \"corr_rad\": %.3e, \"rs_bound\": %.3e, \"K\": %ld, "
               "\"sec_setup\": %.4f, \"sec_head\": %.4f, \"sec_fast\": %.4f, \"sec_total\": %.4f, \"ns_per_term_fast\": %.2f, \"maxrss_mb\": %.1f}\n",
               T0s, us, u, zs, mid, mag_get_d(arb_radref(Z)), fmpz_get_ui(S.N), P.J, P.threads, P.bmax, S.head_terms, S.blocks, S.terms_fast,
               S.max_phase_err, S.sum_err_fast, S.corr_rad, S.rs_bound, S.K, S.sec_setup, S.sec_head, S.sec_fast, S.sec_total,
               S.terms_fast > 0 ? 1e9 * S.sec_fast / S.terms_fast : 0.0, ru.ru_maxrss / 1048576.0);
        fflush(stdout);
        flint_free(zs); flint_free(mid);
        zf_stats_clear(&S);
    }
    arb_clear(Z); fmpz_clear(T0);
    flint_cleanup();
    return 0;
}
