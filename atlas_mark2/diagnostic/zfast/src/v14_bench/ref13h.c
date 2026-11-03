/* reference build for M9 identity tests: the FROZEN v13b source (included unmodified) + zfast_hash14.inc (hash only) */
#include "/Users/kiosk/atlas_mark2/diagnostic/zfast/src/v13b/zfast.c"
#include "/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/src_v14/zfast_hash14.inc"
int zfa13h_hash(void *s, char *out, int outlen) { if (outlen < 65) return -2; return zfm_hash14((zfm_session *)s, out); }
