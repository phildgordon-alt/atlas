/* timing-only ablations of the z20 kernel (NOT correct kernels; used to locate cost) */
#include "../v14/zfast.c"
#define V(NAME, DOFX, DOG, DOCS) static double NAME(fx *E, long n0, long B, const double *cx) { fx e[13]; memcpy(e, E, sizeof e); \
  float64x2_t G[20]; for (int m = 0; m < 20; m++) G[m] = vdupq_n_f64(0); double xc = 0.5*(double)(B-1); double sink = 0; \
  for (long k = 0; k < B; k++) { double c = 1, s = 0.5; if (DOCS) zf_cos2pi(&c, &s, e[0].w[3]); else { c = (double)(e[0].w[3] >> 11); } \
    double x = horner6(cx, (double)k - xc); double w = 1.0 / sqrt((double)(n0 + k)); float64x2_t P = { w * c, w * s }; \
    if (DOG) { _Pragma("clang loop unroll(full)") for (int m = 0; m < 20; m++) { G[m] = vaddq_f64(G[m], P); P = vmulq_n_f64(P, x); } } else G[0] = vaddq_f64(G[0], P); \
    if (DOFX) { fx_add(&e[0], &e[1]); fx_add(&e[1], &e[2]); fx_add(&e[2], &e[3]); fx_add(&e[3], &e[4]); fx_add(&e[4], &e[5]); fx_add(&e[5], &e[6]); \
      fx_add(&e[6], &e[7]); fx_add(&e[7], &e[8]); fx_add(&e[8], &e[9]); fx_add(&e[9], &e[10]); fx_add(&e[10], &e[11]); fx_add(&e[11], &e[12]); } else e[0].w[3] += e[1].w[3]; } \
  for (int m = 0; m < 20; m++) sink += vgetq_lane_f64(G[m], 0); memcpy(E, e, sizeof e); return sink; }
V(full, 1, 1, 1) V(nofx, 0, 1, 1) V(nog, 1, 0, 1) V(nocs, 1, 1, 0) V(only_cs, 0, 0, 1)
int main(void) { fx E[13]; for (int i = 0; i < 13; i++) for (int w = 0; w < 4; w++) E[i].w[w] = 0x9e3779b97f4a7c15ULL * (i * 4 + w + 1);
  double cx[7] = {0.001, 2e-10, -1e-20, 1e-30, 0, 0, 0}; long B = 16384; int R = 300; double s = 0;
  double (*f[5])(fx *, long, long, const double *) = { full, nofx, nog, nocs, only_cs }; const char *nm[5] = { "full", "no_fx", "no_g", "no_cos", "cos_only" };
  for (int i = 0; i < 5; i++) { double a = now(); for (int r = 0; r < R; r++) s += f[i](E, 4000000000L, B, cx); printf("%s %.2f ns/term\n", nm[i], 1e9 * (now() - a) / (B * (double)R)); }
  return s == 12345.0; }
