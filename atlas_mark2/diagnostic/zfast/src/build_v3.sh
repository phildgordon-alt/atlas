#!/bin/sh
# build_v3.sh VERSION : builds ../bin/{zfast_cli,zfast_selftest,zfast_row_cli,arbref_smooth}.<VERSION>; snapshots sources into
# ../bin/src_<VERSION>/ ; stops on any compile error; never overwrites.
set -e
V=${1:?usage: build_v3.sh VERSION}
cd "$(dirname "$0")"; mkdir -p ../bin
PROGS="zfast_cli zfast_selftest zfast_row_cli arbref_smooth"
SNAP=../bin/src_$V
[ -e "$SNAP" ] && { echo "exists: $SNAP"; exit 1; }
for P in $PROGS; do [ -e ../bin/$P.$V ] && { echo "exists: $P.$V"; exit 1; }; done
mkdir "$SNAP"; cp zfast.c zfast.h $(for P in $PROGS; do echo $P.c; done) "$SNAP"/
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Werror=incompatible-pointer-types -I/opt/homebrew/include"
LF="-L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm"
for P in $PROGS; do
  cc $CF -o ../bin/$P.$V "$SNAP"/zfast.c "$SNAP"/$P.c $LF 2> ../bin/build_$P.$V.log || { cat ../bin/build_$P.$V.log; echo BUILD FAILED; exit 1; }
  grep -v "built for newer version" ../bin/build_$P.$V.log || true
done
( cd ../bin && shasum -a 256 $(for P in $PROGS; do echo $P.$V; done) src_$V/* ) > ../bin/SHA256.$V
echo built $V; cat ../bin/SHA256.$V
