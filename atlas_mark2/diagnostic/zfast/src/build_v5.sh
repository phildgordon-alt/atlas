#!/bin/sh
# build_v5.sh SRCDIR VERSION : as build_v4.sh, but also snapshots *.inc files (v10+).  Never overwrites; stops on errors.
set -e
SD=${1:?srcdir}; V=${2:?version}
cd "$(dirname "$0")"; mkdir -p ../bin
SNAP=../bin/src_$V
[ -e "$SNAP" ] && { echo "exists: $SNAP"; exit 1; }
mkdir "$SNAP"; cp "$SD"/*.c "$SD"/*.h "$SNAP"/; cp "$SD"/*.inc "$SNAP"/ 2>/dev/null || true
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Wno-unused-variable -Werror=incompatible-pointer-types -I/opt/homebrew/include"
LF="-L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm -lpthread"
OUTS=""
for F in "$SNAP"/*.c; do
  P=$(basename "$F" .c)
  case $P in zfast|zfast_api*) continue;; esac
  O=../bin/$P.$V; [ -e "$O" ] && { echo "exists $O"; exit 1; }
  cc $CF -o "$O" "$SNAP"/zfast.c "$F" $LF 2> ../bin/build_$P.$V.log || { cat ../bin/build_$P.$V.log; echo BUILD FAILED; exit 1; }
  grep -v "built for newer version" ../bin/build_$P.$V.log || true
  OUTS="$OUTS $P.$V"
done
API=$(ls "$SNAP"/zfast_api*.c 2>/dev/null | tr '\n' ' ')
if [ -n "$API" ]; then
  O=../bin/libzfast.$V.dylib; [ -e "$O" ] && { echo "exists $O"; exit 1; }
  cc $CF -dynamiclib -o "$O" "$SNAP"/zfast.c $API $LF 2> ../bin/build_lib.$V.log || { cat ../bin/build_lib.$V.log; echo BUILD FAILED; exit 1; }
  OUTS="$OUTS libzfast.$V.dylib"
fi
( cd ../bin && shasum -a 256 $OUTS src_$V/* ) > ../bin/SHA256.$V
echo built $V
