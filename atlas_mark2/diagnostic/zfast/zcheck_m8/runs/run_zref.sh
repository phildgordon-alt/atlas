#!/bin/bash
# M8 step 2: code-independent Z check (zref_m8, stock FLINT only) at zfast grid points; sequential, nice 19, 4 threads, RSS watchdog 3 GB
set -u; unset PYTHONOPTIMIZE
D=/Users/kiosk/atlas_mark2/diagnostic/zfast/zcheck_m8; W=/Users/kiosk/atlas_mark2/diagnostic/zfast/tools/wd_run2.sh
echo "start $(date)" >> $D/runs/zref.log
s=$(date +%s); nice -n 19 $W 3000 /dev/null $D/runs/zref_1e20.jsonl $D/bin/zref_m8 100000000000000000000 192 4 0x1.5604189374bd0p+2 0x1.0000000000000p+1 2>> $D/runs/zref.log
echo "1e20 wall=$(( $(date +%s) - s ))s $(date)" >> $D/runs/zref.log
s=$(date +%s); nice -n 19 $W 3000 /dev/null $D/runs/zref_1e22.jsonl $D/bin/zref_m8 10000000000000000000000 192 4 0x1.052b020c49ba6p+6 2>> $D/runs/zref.log
echo "1e22 wall=$(( $(date +%s) - s ))s $(date)" >> $D/runs/zref.log
echo DONE >> $D/runs/zref.log
