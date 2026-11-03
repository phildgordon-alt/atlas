#!/bin/sh
# builds into ../bin/<name>.<version>  (never overwrites: refuses if the target exists)
set -e
V=${1:?usage: build.sh VERSION}
cd "$(dirname "$0")"; mkdir -p ../bin
OUT=../bin/zfast_cli.$V
[ -e "$OUT" ] && { echo "exists: $OUT"; exit 1; }
cc -O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -I/opt/homebrew/include -o "$OUT" zfast.c zfast_cli.c -L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm
shasum -a 256 "$OUT" zfast.c zfast.h zfast_cli.c > "$OUT.sha256"
echo built "$OUT"
