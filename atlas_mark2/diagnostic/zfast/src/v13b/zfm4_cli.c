/* zfm4_cli (v12): kind-0 session; stdin "z u" | "r a u".  zfm4_cli T0 u0 H Delta K threads J */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include "zfast.h"
void *zfa4_new(const char *T0s, double u0, double H, double Delta, int K, int J, int threads);
int zfa4_row(void *s, double u, double a, char *out, int outlen);
int zfa3_Z(void *s, double u, char *out, int outlen);
int zfa3_info(void *s, char *out, int outlen);
int main(int argc, char **argv)
{
    if (argc < 8) { fprintf(stderr, "usage\n"); return 2; }
    void *S = zfa4_new(argv[1], strtod(argv[2], 0), strtod(argv[3], 0), strtod(argv[4], 0), atoi(argv[5]), atoi(argv[7]), atoi(argv[6]));
    char buf[4096]; zfa3_info(S, buf, 4096);
    struct rusage ru; getrusage(RUSAGE_SELF, &ru);
    printf("{\"session\": %s, \"T0\": \"%s\", \"maxrss_mb\": %.1f}\n", buf, argv[1], ru.ru_maxrss / 1048576.0); fflush(stdout);
    char cmd[16], a[200], b[200];
    while (scanf("%15s", cmd) == 1)
    {
        if (!strcmp(cmd, "z")) { if (scanf("%199s", a) != 1) break; zfa3_Z(S, strtod(a, 0), buf, 4096); printf("{\"T0\": \"%s\", \"u\": \"%s\", \"res\": %s}\n", argv[1], a, buf); }
        else { if (scanf("%199s %199s", b, a) != 2) break; zfa4_row(S, strtod(a, 0), strtod(b, 0), buf, 4096); printf("{\"T0\": \"%s\", \"u\": \"%s\", \"a\": \"%s\", \"res\": %s}\n", argv[1], a, b, buf); }
        fflush(stdout);
    }
    return 0;
}
