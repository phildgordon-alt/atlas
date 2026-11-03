#!/bin/bash
set -u; unset PYTHONOPTIMIZE
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; ZF=/Users/kiosk/atlas_mark2/diagnostic/zfast; O=$ZF/runs/m8/fresh
for spec in 10000000000000:1 100000000000000:1 1000000000000000:1 1000000000000000:287 10000000000000000:1 100000000000000000:1 1000000000000000000:1; do
  T=${spec%%:*}; C=${spec##*:}; a=$((C-1)); b=$((C+1)); n=s5_${T}_c$C
  s=$(date +%s)
  nice -n 19 $ZF/tools/wd_run2.sh 3000 /dev/null $O/$n.log $P -B $ZF/tools/scan_turing5.py scan $T $O/$n --centre $C --H 61 --delta 0.012 --u0 $((C-60)) --n 30001 --points $a,$b --win $a,$b --threads 2 2> $O/$n.wd.log
  echo "$n rc=$? wall=$(( $(date +%s) - s ))s" >> $O/fresh.log
done
echo DONE >> $O/fresh.log
