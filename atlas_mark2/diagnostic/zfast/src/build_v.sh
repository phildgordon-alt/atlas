#!/bin/sh
# build_v.sh VERSION [extra .c files] : builds ../bin/<prog>.<VERSION> for zfast_cli and zfast_selftest, and snapshots the exact
# sources into ../bin/src_<VERSION>/ .  Refuses to overwrite anything.
set -e
V=${1:?usage: build_v.sh VERSION}
cd "$(dirname "$0")"; mkdir -p ../bin
SNAP=../bin/src_$V
[ -e "$SNAP" ] && { echo "exists: $SNAP"; exit 1; }
mkdir "$SNAP"; cp zfast.c zfast.h zfast_cli.c zfast_selftest.c "$SNAP"/ 2>/dev/null || cp zfast.c zfast.h zfast_cli.c "$SNAP"/
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -I/opt/homebrew/include"
LF="-L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm"
for P in zfast_cli zfast_selftest; do
  [ -e $P.c ] || continue
  OUT=../bin/$P.$V; [ -e "$OUT" ] && { echo "exists: $OUT"; exit 1; }
  cc $CF -o "$OUT" "$SNAP"/zfast.c "$SNAP"/$P.c $LF 2>&1 | grep -v "built for newer version" || true
done
( cd ../bin && shasum -a 256 *.$V src_$V/* ) > ../bin/SHA256.$V
echo built $V; cat ../bin/SHA256.$V
