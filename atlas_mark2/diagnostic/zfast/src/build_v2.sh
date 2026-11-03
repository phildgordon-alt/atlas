#!/bin/sh
# build_v2.sh VERSION : builds ../bin/{zfast_cli,zfast_selftest}.<VERSION>, snapshots the exact sources into ../bin/src_<VERSION>/,
# fails on any compile error.  Never overwrites (refuses if a target exists).  (build_v.sh: same, but did not stop on errors.)
set -e
V=${1:?usage: build_v2.sh VERSION}
cd "$(dirname "$0")"; mkdir -p ../bin
SNAP=../bin/src_$V
[ -e "$SNAP" ] && { echo "exists: $SNAP"; exit 1; }
for P in zfast_cli zfast_selftest; do [ -e ../bin/$P.$V ] && { echo "exists: $P.$V"; exit 1; }; done
mkdir "$SNAP"; cp zfast.c zfast.h zfast_cli.c zfast_selftest.c "$SNAP"/
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Werror=incompatible-pointer-types -I/opt/homebrew/include"
LF="-L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm"
for P in zfast_cli zfast_selftest; do
  cc $CF -o ../bin/$P.$V "$SNAP"/zfast.c "$SNAP"/$P.c $LF 2> ../bin/build_$P.$V.log || { cat ../bin/build_$P.$V.log; echo BUILD FAILED; exit 1; }
done
( cd ../bin && shasum -a 256 zfast_cli.$V zfast_selftest.$V src_$V/* ) > ../bin/SHA256.$V
echo built $V; cat ../bin/SHA256.$V
