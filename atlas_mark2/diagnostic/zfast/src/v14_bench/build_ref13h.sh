#!/bin/sh
# test-only reference: FROZEN v13b source (src/v13b, included unmodified; sha-checked against bin/SHA256.v13b) + the v14 snapshot's hash.
set -e; cd "$(dirname "$0")"; O=../../bin/libzfast.ref13h.dylib; [ -e $O ] && { echo "exists $O"; exit 1; }
( cd ../../bin && for f in zfast.c zfast_m3b.inc zfast_m3c.inc zfast_api3.c zfast_api4.c zfast.h; do a=$(shasum -a 256 src_v13b/$f | cut -c1-64); b=$(shasum -a 256 ../src/v13b/$f | cut -c1-64); [ "$a" = "$b" ] || { echo "v13b source differs from snapshot: $f"; exit 1; }; done )
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Wno-unused-variable -Werror=incompatible-pointer-types -I/opt/homebrew/include"
cc $CF -dynamiclib -o $O ref13h.c ../v13b/zfast_api3.c ../v13b/zfast_api4.c -L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm -lpthread 2>&1 | grep -v "built for newer" || true
shasum -a 256 $O ref13h.c > ../../bin/SHA256.ref13h; cat ../../bin/SHA256.ref13h
