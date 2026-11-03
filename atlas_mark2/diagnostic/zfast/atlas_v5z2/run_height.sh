#!/bin/bash
# run_height.sh E : scan + Turing count (separate method) at T = 10^E, then v5z2 windows [T, T+2] and the closest-pair window.
cd /Users/kiosk/atlas_mark2/diagnostic/zfast; E=$1; T=$(python3 -c "print(10**$E)")
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; export ZFAST_THREADS=${ZFAST_THREADS:-1}
s=$(date +%s); nice -n 19 $P -B tools/scan_turing2.py $T runs/m5/scan2_1e$E --threads $ZFAST_THREADS > runs/m5/scan2_1e$E.log 2>&1
echo "scan_1e$E rc=$? wall=$(( $(date +%s) - s ))s" >> atlas_v5z2/runs/v5z.log
K=$(python3 -c "import json;print(json.load(open('runs/m5/scan2_1e$E/scan_turing.json'))['closest_pair']['window_offsets'][0])")
cd atlas_v5z2
./run_window.sh h_1e$E $T $T $(python3 -c "print(10**$E+2)") 0.005 - - 1.0
./run_window.sh hp_1e$E $T $(python3 -c "print(10**$E+$K)") $(python3 -c "print(10**$E+$K+2)") 0.005 - - $(python3 -c "print($K+1.0)")
echo "HEIGHT $E DONE (pair window offset $K)" >> runs/v5z.log
