#!/bin/bash
# atlas_v5 steps 3-4 (PREDICTIONS.md): one target per call, serial.  usage: run_big.sh EXP STEP TIMEOUT
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; V5=/Users/kiosk/atlas_mark2/diagnostic/atlas_v5; cd $V5
E=$1; T=$(python3 -c "print(10**$E)"); T2=$(python3 -c "print(10**$E+2)")
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T $T $T2 --name big_1e$E --zs-step $2 --gen-timeout $3 > runs/big_1e$E.out 2>&1; rc=$?
echo "big_1e$E rc=$rc wall=$(( $(date +%s) - s ))s" >> runs/big.log
s=$(date +%s); nice -n 19 $P -B replay_target5.py runs/w$T/big_1e$E replay_check_independent > runs/w$T/big_1e$E/replay_target_independent.log 2>&1
echo "big_1e$E independent replay rc=$? wall=$(( $(date +%s) - s ))s $(tail -1 runs/w$T/big_1e$E/replay_target_independent.log)" >> runs/big.log
