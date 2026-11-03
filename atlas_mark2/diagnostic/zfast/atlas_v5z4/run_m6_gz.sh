#!/bin/bash
# run_m6_gz.sh : M6 code-independent reference at 10^24: review2/bin/ref (stock FLINT 3.6.0 only: acb_dirichlet_powsum_smooth main
# sum + Gabcke C0, C1 with the R1 bound) on the 3 GZ lines chosen by tools/gz_points_m6.py, ONE process, nice 19, 950 MB watchdog
# (tools/wd_run2.sh).  Output runs/m6/gz_1e24.jsonl (new file).  Expected ~2 days per point.
cd /Users/kiosk/atlas_mark2/diagnostic/zfast || exit 1
L=atlas_v5z4/runs/m6.log
[ -e runs/m6/gz_1e24.jsonl ] && { echo "exists runs/m6/gz_1e24.jsonl" | tee -a $L; exit 1; }
[ -s runs/m6/gz_1e24.in ] || { echo "no runs/m6/gz_1e24.in" | tee -a $L; exit 1; }
echo "GZ start $(date): $(cat runs/m6/gz_1e24.in | tr '\n' ';')" >> $L
s=$(date +%s)
nice -n 19 sh tools/wd_run2.sh 950 runs/m6/gz_1e24.in runs/m6/gz_1e24.jsonl review2/bin/ref 2> runs/m6/gz_1e24.wd.log
echo "GZ done wall=$(( $(date +%s) - s ))s $(cat runs/m6/gz_1e24.wd.log | tr '\n' ' ')" >> $L
