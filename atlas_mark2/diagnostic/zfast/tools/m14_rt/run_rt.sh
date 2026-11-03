#!/bin/bash
# tools/m14_rt/run_rt.sh SRCDIR OUTDIR [NR NW] : PERMANENT MJ-C1 round-trip regression (PREDICTIONS_M14 R1/R1n/R2).  Compiles rt_arb.c
# with the library source SRCDIR (production flags, one translation unit), extracts the v5z7 production checkpoint balls READ-ONLY,
# and runs.  Writes OUTDIR/rt.json (OUTDIR must not exist).  nice 19.  Exit = rt_arb's exit code.
set -e
export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1; unset PYTHONOPTIMIZE
SRC=${1:?srcdir}; OUT=${2:?outdir}; NR=${3:-300000}; NW=${4:-300000}
H=$(cd "$(dirname "$0")" && pwd); ZF=/Users/kiosk/atlas_mark2/diagnostic/zfast; PY=/Users/kiosk/projects/atlas-rerun/.venv/bin/python
mkdir "$OUT"
CF="-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math -Wall -Wno-unused-variable -Wno-unused-function -I$SRC -I/opt/homebrew/include"
nice -n 19 cc $CF -o "$OUT/rt_arb" "$H/rt_arb.c" -L/opt/homebrew/lib -lflint -lgmp -lmpfr -lm -lpthread 2>&1 | grep -v "built for newer" || true
CK=""
for r in w10000000000000000000000/wide7_1e22 w10000000000000000000000000/wide7_1e25 w100000000000000000000000000/wide7_1e26; do
  for f in zfast_ckpt_gen.txt zfast_ckpt_replay.txt; do [ -f "$ZF/atlas_v5z7/runs/$r/$f" ] && CK="$CK $ZF/atlas_v5z7/runs/$r/$f"; done
done
nice -n 19 $PY -B "$H/extract_balls.py" "$OUT/balls.txt" $CK > "$OUT/extract.json"
set +e
nice -n 19 "$OUT/rt_arb" "$NR" "$NW" "$OUT/balls.txt" > "$OUT/rt.json"; rc=$?
cat "$OUT/rt.json"; echo "rt_arb rc=$rc"
: > "$OUT/balls.txt"     # scratch copy of the extracted tokens emptied (the source checkpoints are untouched); counts in extract.json
exit $rc
