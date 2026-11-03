#!/bin/bash
# run_m7.sh : PREDICTIONS_M7 section 2, run only after the gate passed.  Sequential (one heavy job at a time), nice 19, 2 threads.
# 1 wide window [1e22, 1e22+100] (generator + replay + independent replay)   2 Turing count (scan_turing4, separate method)
set -u; unset PYTHONOPTIMIZE
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; ZF=/Users/kiosk/atlas_mark2/diagnostic/zfast; T0=10000000000000000000000
L=$ZF/runs/m7.log; mkdir -p $ZF/runs/m7
[ $(df -g / | awk 'NR==2{print $4}') -lt 2 ] && { echo "disk floor" >> $L; exit 1; }
echo "M7 start $(date)" >> $L
cd $ZF/atlas_v5z5 && ZFAST_THREADS=2 V4_LIM_GB=1.0 ./run_wide.sh wide_1e22 $T0 $T0 10000000000000000000100 61 0.012
echo "wide_1e22 finished $(date)" >> $L
s=$(date +%s)
nice -n 19 $ZF/tools/wd_run2.sh 1000 /dev/null $ZF/runs/m7/scan4_1e22.log $P -B $ZF/tools/scan_turing4.py $T0 $ZF/runs/m7/scan4_1e22 --centre 50 --H 91 --delta 0.008 --u0 -40 --n 45001 --points 0,100 --threads 2 2> $ZF/runs/m7/scan4_1e22.wd.log
echo "scan4_1e22 rc=$? wall=$(( $(date +%s) - s ))s" >> $L
echo "M7 done $(date)" >> $L
