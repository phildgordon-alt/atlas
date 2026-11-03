#!/bin/sh
# build_v7.sh SRCDIR VERSION : build_v6.sh exactly (same flags, snapshot bin/src_VERSION, CLIs + libzfast.VERSION.dylib, SHA256.VERSION),
# plus a SEPARATE test-hooks library libzfast.VERSION_testhooks.dylib from the same snapshot with -DZF_TEST_HOOKS (env test hooks compiled
# in; never used by a pipeline; its checkpoints are refused by the production library because its image SHA differs).  Never overwrites.
set -e
SD=${1:?srcdir}; V=${2:?version}
cd "$(dirname "$0")"
sh ./build_v6.sh "$SD" "$V"
SNAP=../bin/src_$V
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Wno-unused-variable -Werror=incompatible-pointer-types -I/opt/homebrew/include"
LF="-L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm -lpthread"
API=$(ls "$SNAP"/zfast_api*.c 2>/dev/null | tr '\n' ' ')
O=../bin/libzfast.${V}_testhooks.dylib; [ -e "$O" ] && { echo "exists $O"; exit 1; }
cc $CF -DZF_TEST_HOOKS -dynamiclib -o "$O" "$SNAP"/zfast.c $API $LF 2> ../bin/build_lib.${V}_testhooks.log || { cat ../bin/build_lib.${V}_testhooks.log; echo BUILD FAILED; exit 1; }
( cd ../bin && shasum -a 256 libzfast.${V}_testhooks.dylib ) >> ../bin/SHA256.$V
echo built ${V}_testhooks
