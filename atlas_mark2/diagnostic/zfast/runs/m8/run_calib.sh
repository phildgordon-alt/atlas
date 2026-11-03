#!/bin/bash
# M8 thread calibration: waits for the zref job (one heavy job at a time), then 1e21 sessions at 4, 2, 1 threads (fresh process each)
set -u; unset PYTHONOPTIMIZE
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; ZF=/Users/kiosk/atlas_mark2/diagnostic/zfast; O=$ZF/runs/m8/calib
mkdir -p $O
while ! grep -q DONE $ZF/zcheck_m8/runs/zref.log; do sleep 30; done
echo "calib start $(date) load $(sysctl -n vm.loadavg)" >> $O/calib.log
for th in 4 2 1; do
  s=$(date +%s)
  nice -n 19 $ZF/tools/wd_run2.sh 3000 /dev/null $O/calib_1e21_t$th.out $P -B $ZF/tools/calib_threads_m8.py 1000000000000000000000 $th 3000 $O/calib.jsonl 2>> $O/calib.log
  echo "threads=$th wall=$(( $(date +%s) - s ))s $(date)" >> $O/calib.log
done
echo DONE >> $O/calib.log
