/* tools/m14_rt/rt_arb.c -- PERMANENT regression test for review_v14c MJ-C1 (PREDICTIONS_M14 R1, R1c, R1n, R2).
   Compiled as ONE translation unit with the library source under test (-I SRC; #include "zfast.c"), so it calls that source's own
   static parse_arb_strict.  usage:  rt_arb N_RANDOM N_WIDTH [BALLFILE ...]
     random : N_RANDOM arb_randtest balls (prec 1-400, mag bits 1-60), finite only
     width  : N_WIDTH balls whose radius mantissa has width w = 1 + (k mod 30) bits (odd, random), random midpoints (10 % zero)
     files  : each line "midman midexp radman radexp" (honest arb_dump_str tokens extracted from production checkpoints)
     noncanon: fixed list of tokens that arb_dump_str never emits (must be refused, without a signal)
   For every ball: dump -> parse_arb_strict -> must return 1, arb_equal, and the re-dump must equal the dump.
   Prints one JSON line; exit 0 iff every case passed. */
#include "zfast.c"
#include <flint/fmpz.h>

/* the strict parser's documented range rule (v14b mag_valid): a radius exponent needs <= 40 bits; arb_randtest with mag bits up to 60
   produces balls outside it, which are refused BY DESIGN (honest moment radii have exponents of a few hundred).  Classified separately. */
static int out_of_range(const arb_t x) { return !mag_is_zero(arb_radref(x)) && fmpz_bits(MAG_EXPREF(arb_radref(x))) > 40; }

static int rt_one(const arb_t x, long *rad30, long *radnz)
{
    char *d = arb_dump_str(x); const char *p = d, *why = NULL; arb_t y; arb_init(y);
    int ok = parse_arb_strict(y, &p, &why) && *p == 0 && arb_equal(x, y);
    if (ok) { char *e = arb_dump_str(y); ok = !strcmp(d, e); flint_free(e); }
    if (!mag_is_zero(arb_radref(x)))
    {
        (*radnz)++;
        const char *t = d; for (int k = 0; k < 2; k++) { t = strchr(t, ' '); t++; }
        const char *te = strchr(t, ' '); long w = te - t;           /* hex digits of the radius mantissa token */
        char tmp[16]; if (w < 16) { memcpy(tmp, t, w); tmp[w] = 0; unsigned long m = strtoul(tmp, NULL, 16); if (m >> 29 == 1) (*rad30)++; }
    }
    flint_free(d); arb_clear(y); return ok;
}

static int rt_str(const char *s, long *nz)
{
    const char *p = s, *why = NULL; arb_t y; arb_init(y);
    int ok = parse_arb_strict(y, &p, &why) && *p == 0;
    if (ok) { char *e = arb_dump_str(y); ok = !strcmp(s, e); flint_free(e); }
    if (ok && !mag_is_zero(arb_radref(y))) (*nz)++;
    arb_clear(y); return ok;
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: rt_arb N_RANDOM N_WIDTH [BALLFILE ...]\n"); return 2; }
    long NR = atol(argv[1]), NW = atol(argv[2]);
    flint_rand_t st; flint_rand_init(st); arb_t x; arb_init(x);
    long r_range = 0, r_n = 0, r_bad = 0, r_30 = 0, r_nz = 0, w_n = 0, w_bad = 0, w_30 = 0, w_nz = 0, wbad_by[31] = { 0 }, wn_by[31] = { 0 };
    char firstbad[600] = "";
    for (long k = 0; k < NR; k++)
    {
        arb_randtest(x, st, 1 + n_randint(st, 400), 1 + n_randint(st, 60)); if (!arb_is_finite(x)) continue;
        r_n++; int okx = rt_one(x, &r_30, &r_nz); if (!okx && out_of_range(x)) { r_range++; continue; }
        if (!okx) { if (!r_bad) { char *d = arb_dump_str(x); snprintf(firstbad, sizeof firstbad, "random: %s", d); flint_free(d); } r_bad++; }
    }
    fmpz_t m, e; fmpz_init(m); fmpz_init(e);
    for (long k = 0; k < NW; k++)
    {
        int w = 1 + (int)(k % 30);
        if (n_randint(st, 10) == 0) arf_zero(arb_midref(x));
        else
        {
            fmpz_randbits(m, st, 1 + n_randint(st, 400)); if (fmpz_is_zero(m)) fmpz_one(m);
            fmpz_set_si(e, (slong)n_randint(st, 4001) - 2000); arf_set_fmpz_2exp(arb_midref(x), m, e);
        }
        ulong rm = (w == 1) ? 1 : ((UWORD(1) << (w - 1)) | (n_randlimb(st) & ((UWORD(1) << (w - 1)) - 1)) | 1);
        slong re = (slong)n_randint(st, 4001) - 2000 - (slong)(n_randint(st, 2));
        mag_set_ui_2exp_si(arb_radref(x), rm, re);
        w_n++; wn_by[w]++;
        if (!rt_one(x, &w_30, &w_nz)) { if (!w_bad) { char *d = arb_dump_str(x); snprintf(firstbad, sizeof firstbad, "width %d: %s", w, d); flint_free(d); } w_bad++; wbad_by[w]++; }
    }
    /* files of honest production dumps */
    long f_n = 0, f_bad = 0, f_nz = 0;
    for (int a = 3; a < argc; a++)
    {
        FILE *f = fopen(argv[a], "r"); if (!f) { fprintf(stderr, "cannot open %s\n", argv[a]); return 2; }
        char *line = NULL; size_t cap = 0; ssize_t len;
        while ((len = getline(&line, &cap, f)) > 0)
        {
            if (line[len - 1] == '\n') line[--len] = 0;
            if (!len) continue;
            f_n++;
            if (!rt_str(line, &f_nz)) { if (!f_bad) snprintf(firstbad, sizeof firstbad, "file %s: %.400s", argv[a], line); f_bad++; }
        }
        free(line); fclose(f);
    }
    /* non-canonical tokens: never emitted by arb_dump_str; must be refused (return 0), no signal */
    const char *nc[] = { "1 0 7fffffff -20", "1 0 40000000 0", "1 0 2 -5", "1 0 -1 0", "1 0 01 0", "1 0 0 5", "0 5 0 0", "2 0 0 0",
                         "1 0 ffffffffffffffff 0", "1 0 1ffffffff 0", "-1 0 3fffffff2 -1f4", NULL };
    long nc_n = 0, nc_bad = 0; char ncbad[300] = "";
    for (int k = 0; nc[k]; k++)
    {
        const char *p = nc[k], *why = NULL; arb_t y; arb_init(y); int ok = parse_arb_strict(y, &p, &why) && *p == 0;
        if (ok) { char *d = arb_dump_str(y); ok = !strcmp(d, nc[k]); flint_free(d); }
        nc_n++; if (ok) { nc_bad++; snprintf(ncbad, sizeof ncbad, "%s", nc[k]); }
        arb_clear(y);
    }
    char big[6000]; snprintf(big, sizeof big, "1 0 "); for (int k = 0; k < 5000; k++) strcat(big, "f"); strcat(big, " 0");
    { const char *p = big, *why = NULL; arb_t y; arb_init(y); int ok = parse_arb_strict(y, &p, &why); nc_n++; if (ok) { nc_bad++; snprintf(ncbad, sizeof ncbad, "5000-digit radius"); } arb_clear(y); }
    printf("{\"random\": {\"n\": %ld, \"fail\": %ld, \"refused_radius_exponent_over_40_bits\": %ld, \"nonzero_radius\": %ld, \"rad30\": %ld}, \"width\": {\"n\": %ld, \"fail\": %ld, \"nonzero_radius\": %ld, \"rad30\": %ld, \"fail_by_width\": [",
           r_n, r_bad, r_range, r_nz, r_30, w_n, w_bad, w_nz, w_30);
    for (int w = 1; w <= 30; w++) printf("%s%ld", w > 1 ? ", " : "", wbad_by[w]);
    printf("], \"n_by_width\": [");
    for (int w = 1; w <= 30; w++) printf("%s%ld", w > 1 ? ", " : "", wn_by[w]);
    printf("]}, \"files\": {\"n\": %ld, \"fail\": %ld, \"nonzero_radius\": %ld}, \"noncanonical\": {\"n\": %ld, \"accepted\": %ld, \"first_accepted\": \"%s\"}, \"first_fail\": \"%.300s\"}\n",
           f_n, f_bad, f_nz, nc_n, nc_bad, ncbad, firstbad);
    fmpz_clear(m); fmpz_clear(e); arb_clear(x); flint_rand_clear(st);
    return (r_bad || w_bad || f_bad || nc_bad) ? 1 : 0;
}
