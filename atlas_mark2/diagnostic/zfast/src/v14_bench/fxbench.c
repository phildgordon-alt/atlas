#include "../v14/zfast.c"
int main(void) { fx E[13], F[13]; for (int i = 0; i < 13; i++) for (int w = 0; w < 4; w++) E[i].w[w] = 0x9e3779b97f4a7c15ULL * (i * 4 + w + 1);
  memcpy(F, E, sizeof E); long N = 50000000; uint64_t s1 = 0, s2 = 0;
  double a = now(); for (long k = 0; k < N; k++) { s1 += E[0].w[3]; fx_add(&E[0], &E[1]); fx_add(&E[1], &E[2]); fx_add(&E[2], &E[3]); fx_add(&E[3], &E[4]);
      fx_add(&E[4], &E[5]); fx_add(&E[5], &E[6]); fx_add(&E[6], &E[7]); fx_add(&E[7], &E[8]); fx_add(&E[8], &E[9]); fx_add(&E[9], &E[10]); fx_add(&E[10], &E[11]); fx_add(&E[11], &E[12]); }
  double b = now(); for (long k = 0; k < N; k += 2) { s2 += F[0].w[3]; s2 += fx12_step2(F); } double c = now();
  printf("old %.2f ns/step, step2 %.2f ns/step, identical %d\n", 1e9 * (b - a) / N, 1e9 * (c - b) / N, s1 == s2 && !memcmp(E, F, sizeof E)); return 0; }
