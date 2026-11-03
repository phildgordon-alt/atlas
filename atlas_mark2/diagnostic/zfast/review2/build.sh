#!/bin/sh
# build.sh OUT SRC... : production flags (bin/build_v6.sh), never overwrites
set -e
O=$1; shift
[ -e "$O" ] && { echo "exists $O"; exit 1; }
cc -O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Wno-unused-variable -Wno-unused-function -I/opt/homebrew/include "$@" -o "$O" -L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm -lpthread 2>&1 | grep -v "newer version" || true
[ -x "$O" ] || { echo BUILD FAILED; exit 1; }
echo built $O
