#!/bin/bash
# run_m6_stage1.sh : M6 stage 1 = scan + Turing cross-count at 10^24 (tools/scan_turing3.py, libzfast.v13b, ONE thread, nice 19,
# 500 MB watchdog), then the GZ reference-point selection and the budget record.  New dirs/files only (runs/m6/, atlas_v5z4/runs/m6.log).
cd /Users/kiosk/atlas_mark2/diagnostic/zfast || exit 1
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; export ZFAST_THREADS=1; mkdir -p runs/m6 atlas_v5z4/runs; L=atlas_v5z4/runs/m6.log
T=1000000000000000000000000
[ -e runs/m6/scan3_1e24 ] && { echo "exists runs/m6/scan3_1e24" | tee -a $L; exit 1; }
echo "STAGE1 start $(date) T=$T threads=1" >> $L
s=$(date +%s)
nice -n 19 sh tools/wd_run2.sh 500 /dev/null runs/m6/scan3_1e24.log $P -B tools/scan_turing3.py $T runs/m6/scan3_1e24 --threads 1 2> runs/m6/scan3_1e24.wd.log
echo "scan3_1e24 wall=$(( $(date +%s) - s ))s $(cat runs/m6/scan3_1e24.wd.log | tr '\n' ' ')" >> $L
python3 -B tools/budget_m6.py 23 24 > runs/m6/budget_m6.jsonl 2>&1
$P -B tools/gz_points_m6.py select runs/m6/scan3_1e24 runs/m6/gz_1e24.in runs/m6/gz_1e24_points.json >> $L 2>&1
$P -B tools/turing_extra.py runs/m5/scan2_1e23 runs/m6/turing_extra_1e23.json -24,-22 -2,0 0,2 >> $L 2>&1
echo "STAGE1 DONE $(date)" >> $L
