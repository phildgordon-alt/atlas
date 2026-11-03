/* zfm2_cli (v11): combined session.  zfm2_cli T0 u0 H a1 a2 Delta K threads J ; stdin lines: "z u" | "r which u" */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include "zfast.h"
int zfa3_Z(void *s, double u, char *out, int outlen);
int zfa3_row(void *s, double u, int which, char *out, int outlen);
void *zfa3_new(const char *T0s, double u0, double H, double a1, double a2, double Delta, int K, int J, int threads);
int zfa3_info(void *s, char *out, int outlen);
int main(int argc, char **argv)
{
    if (argc < 10) { fprintf(stderr, "usage\n"); return 2; }
    void *S = zfa3_new(argv[1], strtod(argv[2], 0), strtod(argv[3], 0), strtod(argv[4], 0), strtod(argv[5], 0), strtod(argv[6], 0), atoi(argv[7]), atoi(argv[9]), atoi(argv[8]));
    char buf[4096]; zfa3_info(S, buf, 4096);
    struct rusage ru; getrusage(RUSAGE_SELF, &ru);
    printf("{\"session\": %s, \"T0\": \"%s\", \"maxrss_mb\": %.1f}\n", buf, argv[1], ru.ru_maxrss / 1048576.0); fflush(stdout);
    char cmd[16], a[200], b[200];
    while (scanf("%15s", cmd) == 1)
    {
        if (!strcmp(cmd, "z")) { if (scanf("%199s", a) != 1) break; zfa3_Z(S, strtod(a, 0), buf, 4096); printf("{\"T0\": \"%s\", \"u\": \"%s\", \"res\": %s}\n", argv[1], a, buf); }
        else { if (scanf("%199s %199s", b, a) != 2) break; zfa3_row(S, strtod(a, 0), atoi(b), buf, 4096); printf("{\"T0\": \"%s\", \"u\": \"%s\", \"which\": %s, \"res\": %s}\n", argv[1], a, b, buf); }
        fflush(stdout);
    }
    return 0;
}
