#!/bin/sh
# build_rv.sh SRCDIR TAG : builds review/bin/rv_drv.TAG from SRCDIR/zfast.c (+ its zfast_m3.inc) with the production flags of
# build_v5.sh.  Never overwrites (refuses if the output exists).
set -e
SD=${1:?srcdir}; TAG=${2:?tag}
cd "$(dirname "$0")"
O=bin/rv_drv.$TAG; [ -e "$O" ] && { echo "exists $O"; exit 1; }
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Wno-unused-variable -Werror=incompatible-pointer-types -I/opt/homebrew/include"
LF="-L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm -lpthread"
cc $CF -I"$SD" -o "$O" "$SD"/zfast.c src/rv_drv.c $LF 2>&1 | grep -v "newer version" || true
[ -x "$O" ] || { echo BUILD FAILED; exit 1; }
echo built $O
