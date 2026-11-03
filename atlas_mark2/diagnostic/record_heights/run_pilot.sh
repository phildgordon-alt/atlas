#!/bin/bash
# record_heights pilot: v5 run_big.sh logic, in v5run/ (frozen copy).  usage: run_pilot.sh EXP STEP TIMEOUT
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; V5=/Users/kiosk/atlas_mark2/diagnostic/record_heights/v5run; cd $V5
E=$1; T=$(python3 -c "print(10**$E)"); T2=$(python3 -c "print(10**$E+2)")
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T $T $T2 --name big_1e$E --zs-step $2 --gen-timeout $3 > runs_big_1e$E.out 2>&1; rc=$?
echo "big_1e$E rc=$rc wall=$(( $(date +%s) - s ))s" >> pilot.log
s=$(date +%s); TL=21600 FP_MB=2500 RSS_KB=2500000 /Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh $P -B replay_target5.py runs/w$T/big_1e$E replay_check_independent > runs/w$T/big_1e$E/replay_target_independent.log 2>&1
echo "big_1e$E independent replay rc=$? wall=$(( $(date +%s) - s ))s $(grep -v '^WD' runs/w$T/big_1e$E/replay_target_independent.log | tail -1) $(grep '^WD' runs/w$T/big_1e$E/replay_target_independent.log)" >> pilot.log
