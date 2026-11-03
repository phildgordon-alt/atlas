/* rv_ref.c (independent review, 2026-10-19): reference values that share NO code with zfast.
   Links stock FLINT 3.6.0 only.  Commands on stdin:
     AZ T0 u prec        stock Arb: acb_dirichlet_hardy_z (Arb picks Euler-Maclaurin or RS; RS main sum sieved or smooth)
     GZ T0 u prec sgn    Z = 2 Re(e^{i theta} powsum_smooth(1/2+it, N)) + (-1)^{N-1} a^{-1/2} (C0(p) + sgn * Psi'''(p)/(96 pi^2) / a)
                         +/- 0.053 t^{-5/4}   (Gabcke's R1 bound, t >= 200; quoted in Bober-Hiary 2018 eq. (6)-(8) and section 2)
                         a = sqrt(t/2pi), N = floor a, p = a - N, Psi(p) = cos(2 pi (p^2 - p - 1/16)) / cos(2 pi p).
                         The correction is computed independently of the Arias de Reyna / FLINT RS code that zfast copies.
     GC T0 u prec sgn    only the Gabcke correction ball (C0 + C1 term, +/- R1 bound), and theta, for diagnostics
     AR T0 u a prec      stock Arb jet: acb_dirichlet_zeta_jet(len 2) at s = 1/2 + pi/(2a) + it; prints P = Re(-zeta'/zeta) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/resource.h>
#include <flint/acb.h>
#include <flint/acb_dirichlet.h>
#include <flint/arb_poly.h>

static double now(void) { struct timespec a; clock_gettime(CLOCK_MONOTONIC, &a); return a.tv_sec + 1e-9 * a.tv_nsec; }
static void pball(const char *key, const arb_t x) { char *s = arb_get_str(x, 45, ARB_STR_MORE); printf("\"%s\": \"%s\"", key, s); flint_free(s); }
static double mrss(void) { struct rusage ru; getrusage(RUSAGE_SELF, &ru); return ru.ru_maxrss / 1048576.0; }

static void height(arb_t t, const fmpz_t T0, double u)
{
    arb_t a; arb_init(a); arb_set_fmpz(t, T0); arb_set_d(a, u); arb_add(t, t, a, ARF_PREC_EXACT);
    if (!arb_is_exact(t)) abort();
    arb_clear(a);
}

/* Gabcke correction: res = (-1)^{N-1} a^{-1/2} (C0 + sgn C1 / a) +/- 0.053 t^{-5/4}; also returns N */
static void gabcke(arb_t res, fmpz_t N, const arb_t t, int sgn, slong prec)
{
    arb_t a, p, pi, c, x; arb_poly_t q, num, den, psi;
    arb_init(a); arb_init(p); arb_init(pi); arb_init(c); arb_init(x);
    arb_poly_init(q); arb_poly_init(num); arb_poly_init(den); arb_poly_init(psi);
    arb_const_pi(pi, prec);
    arb_mul_2exp_si(a, pi, 1); arb_div(a, t, a, prec); arb_sqrt(a, a, prec);
    arb_floor(p, a, prec);
    if (!arb_get_unique_fmpz(N, p)) { fprintf(stderr, "N ambiguous\n"); abort(); }
    arb_sub_fmpz(p, a, N, prec);
    /* num argument 2 pi [ (p^2 - p - 1/16) + (2p - 1) x + x^2 ] */
    arb_mul(c, p, p, prec); arb_sub(c, c, p, prec); arb_set_d(x, 0.0625); arb_sub(c, c, x, prec);
    arb_mul(c, c, pi, prec); arb_mul_2exp_si(c, c, 1);
    arb_poly_set_coeff_arb(q, 0, c);
    arb_mul_2exp_si(c, p, 1); arb_sub_ui(c, c, 1, prec); arb_mul(c, c, pi, prec); arb_mul_2exp_si(c, c, 1);
    arb_poly_set_coeff_arb(q, 1, c);
    arb_mul_2exp_si(c, pi, 1); arb_poly_set_coeff_arb(q, 2, c);
    arb_poly_cos_series(num, q, 4, prec);
    arb_poly_zero(q);
    arb_mul(c, p, pi, prec); arb_mul_2exp_si(c, c, 1); arb_poly_set_coeff_arb(q, 0, c);
    arb_mul_2exp_si(c, pi, 1); arb_poly_set_coeff_arb(q, 1, c);
    arb_poly_cos_series(den, q, 4, prec);
    arb_poly_div_series(psi, num, den, 4, prec);
    /* C0 = psi_0 ; C1 = sgn * 6 psi_3 / (96 pi^2) = sgn * psi_3 / (16 pi^2) */
    arb_poly_get_coeff_arb(res, psi, 0);
    arb_poly_get_coeff_arb(c, psi, 3);
    arb_mul(x, pi, pi, prec); arb_mul_2exp_si(x, x, 4); arb_div(c, c, x, prec);
    if (sgn < 0) arb_neg(c, c);
    arb_div(c, c, a, prec);
    arb_add(res, res, c, prec);
    arb_rsqrt(x, a, prec); arb_mul(res, res, x, prec);
    if (fmpz_is_even(N)) arb_neg(res, res);           /* (-1)^{N-1} */
    /* R1 bound 0.053 t^{-5/4} */
    {
        arb_t r; mag_t m; arb_init(r); mag_init(m);
        arb_set_d(r, -1.25); arb_pow(r, t, r, prec); arb_mul_ui(r, r, 53, prec); arb_div_ui(r, r, 1000, prec);
        arb_get_mag(m, r); arb_add_error_mag(res, m);
        arb_clear(r); mag_clear(m);
    }
    arb_clear(a); arb_clear(p); arb_clear(pi); arb_clear(c); arb_clear(x);
    arb_poly_clear(q); arb_poly_clear(num); arb_poly_clear(den); arb_poly_clear(psi);
}

int main(int argc, char **argv)
{
    char line[4096], cmd[16], T0s[256], us[64];
    /* argv[1] = input file, argv[2] = output file (append): lets the footprint watchdog monitor this process directly */
    if (argc > 1 && !freopen(argv[1], "r", stdin)) { perror("in"); return 1; }
    if (argc > 2 && !freopen(argv[2], "a", stdout)) { perror("out"); return 1; }
    fmpz_t T0, N; fmpz_init(T0); fmpz_init(N);
    while (fgets(line, sizeof line, stdin))
    {
        if (sscanf(line, "%15s", cmd) != 1) continue;
        double t0 = now();
        if (!strcmp(cmd, "AZ"))
        {
            long prec;
            if (sscanf(line, "%*s %255s %63s %ld", T0s, us, &prec) != 3) continue;
            fmpz_set_str(T0, T0s, 10);
            arb_t t; acb_t s, z; arb_init(t); acb_init(s); acb_init(z);
            height(t, T0, strtod(us, 0)); acb_set_arb(s, t);
            acb_dirichlet_hardy_z(z, s, NULL, NULL, 1, prec);
            printf("{\"cmd\": \"AZ\", \"T0\": \"%s\", \"u\": \"%s\", ", T0s, us); pball("Z", acb_realref(z));
            printf(", \"rad\": %.4e, \"sec\": %.2f, \"maxrss_mb\": %.1f}\n", mag_get_d(arb_radref(acb_realref(z))), now() - t0, mrss());
            arb_clear(t); acb_clear(s); acb_clear(z);
        }
        else if (!strcmp(cmd, "GZ") || !strcmp(cmd, "GC"))
        {
            long prec; int sgn;
            if (sscanf(line, "%*s %255s %63s %ld %d", T0s, us, &prec, &sgn) != 4) continue;
            fmpz_set_str(T0, T0s, 10);
            arb_t t, corr, Z; acb_t s, th, e, ps; arb_init(t); arb_init(corr); arb_init(Z); acb_init(s); acb_init(th); acb_init(e); acb_init(ps);
            height(t, T0, strtod(us, 0));
            gabcke(corr, N, t, sgn, prec);
            acb_set_arb(s, t);
            acb_dirichlet_hardy_theta(th, s, NULL, NULL, 1, prec + 64);
            if (!strcmp(cmd, "GC"))
            {
                printf("{\"cmd\": \"GC\", \"T0\": \"%s\", \"u\": \"%s\", \"N\": %lu, ", T0s, us, fmpz_get_ui(N)); pball("corr", corr); printf(", "); pball("theta", acb_realref(th)); printf("}\n");
            }
            else
            {
                arb_sin_cos(acb_imagref(e), acb_realref(e), acb_realref(th), prec + 64);
                arb_set_d(acb_realref(s), 0.5); arb_set(acb_imagref(s), t);
                acb_dirichlet_powsum_smooth(ps, s, fmpz_get_ui(N), 1, prec);
                acb_mul(ps, ps, e, prec);
                arb_mul_2exp_si(Z, acb_realref(ps), 1);
                arb_add(Z, Z, corr, prec);
                printf("{\"cmd\": \"GZ\", \"T0\": \"%s\", \"u\": \"%s\", \"N\": %lu, ", T0s, us, fmpz_get_ui(N)); pball("Z", Z);
                printf(", \"rad\": %.4e, \"corr_rad\": %.4e, \"sec\": %.2f, \"maxrss_mb\": %.1f}\n", mag_get_d(arb_radref(Z)), mag_get_d(arb_radref(corr)), now() - t0, mrss());
            }
            arb_clear(t); arb_clear(corr); arb_clear(Z); acb_clear(s); acb_clear(th); acb_clear(e); acb_clear(ps);
        }
        else if (!strcmp(cmd, "AR"))
        {
            long prec; double a;
            if (sscanf(line, "%*s %255s %63s %lf %ld", T0s, us, &a, &prec) != 4) continue;
            fmpz_set_str(T0, T0s, 10);
            arb_t t, pi, h; acb_t s, q; acb_ptr z = _acb_vec_init(2);
            arb_init(t); arb_init(pi); arb_init(h); acb_init(s); acb_init(q);
            height(t, T0, strtod(us, 0));
            arb_const_pi(pi, 512); arb_set_d(h, a); arb_mul_2exp_si(h, h, 1); arb_div(acb_realref(s), pi, h, 512);
            arb_set_d(h, 0.5); arb_add(acb_realref(s), acb_realref(s), h, 512);
            arb_set(acb_imagref(s), t);
            acb_dirichlet_zeta_jet(z, s, 0, 2, prec);
            acb_div(q, z + 1, z, prec); acb_neg(q, q);
            printf("{\"cmd\": \"AR\", \"T0\": \"%s\", \"u\": \"%s\", \"a\": %.17g, ", T0s, us, a); pball("P", acb_realref(q)); printf(", ");
            pball("zr", acb_realref(z)); printf(", "); pball("zi", acb_imagref(z)); printf(", "); pball("dzr", acb_realref(z + 1)); printf(", "); pball("dzi", acb_imagref(z + 1));
            printf(", \"sec\": %.2f, \"maxrss_mb\": %.1f}\n", now() - t0, mrss());
            arb_clear(t); arb_clear(pi); arb_clear(h); acb_clear(s); acb_clear(q); _acb_vec_clear(z, 2);
        }
        fflush(stdout);
    }
    return 0;
}
