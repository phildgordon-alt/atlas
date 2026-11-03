/* Throughput microbenchmark (NOT rigorous, NOT a Z evaluator): per-term cost floor of a double-double Riemann-Siegel main sum,
   sum_n n^{-1/2} cos(theta - t log n), with t = T0 + u split as a DD number, log n in DD (double log + one DD Newton correction
   using exp), DD product, reduction mod 2pi in DD, then double sincos.  Estimates the ns/term of option (b) in COST.md. */
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <time.h>
typedef struct { double hi, lo; } dd;
static inline dd two_prod(double a, double b) { dd r; r.hi = a * b; r.lo = fma(a, b, -r.hi); return r; }
static inline dd two_sum(double a, double b) { dd r; r.hi = a + b; double bb = r.hi - a; r.lo = (a - (r.hi - bb)) + (b - bb); return r; }
static inline dd dd_mul(dd a, dd b) { dd p = two_prod(a.hi, b.hi); p.lo += a.hi * b.lo + a.lo * b.hi; return two_sum(p.hi, p.lo); }
static inline dd dd_add(dd a, dd b) { dd s = two_sum(a.hi, b.hi); s.lo += a.lo + b.lo; return two_sum(s.hi, s.lo); }
int main(int argc, char **argv) {
  long N = atol(argv[1]); double T0 = atof(argv[2]);
  dd t = { T0, 0.505 }; dd twopi = { 6.283185307179586, 2.4492935982947064e-16 }; dd inv2pi = { 0.15915494309189535, -9.4287217655798e-18 };
  double acc = 0; struct timespec a, b; clock_gettime(CLOCK_MONOTONIC, &a);
  for (long n = 1; n <= N; n++) {
    double x = (double)n, y = log(x);
    double e = exp(y); dd ln = two_sum(y, (x - e) / e);       /* one Newton step: log n ~ y + (n - e^y)/e^y  (cost proxy) */
    dd ph = dd_mul(t, ln);
    double k = nearbyint(ph.hi * inv2pi.hi); dd kk = two_prod(k, twopi.hi); kk.lo += k * twopi.lo;
    dd r = dd_add(ph, (dd){ -kk.hi, -kk.lo });
    acc += cos(r.hi + r.lo) / sqrt(x);
  }
  clock_gettime(CLOCK_MONOTONIC, &b); double s = (b.tv_sec - a.tv_sec) + 1e-9 * (b.tv_nsec - a.tv_nsec);
  printf("{\"N\": %ld, \"seconds\": %.3f, \"ns_per_term\": %.2f, \"acc\": %.6f}\n", N, s, 1e9 * s / N, acc);
}
