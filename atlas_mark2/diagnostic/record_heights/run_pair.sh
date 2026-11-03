#!/bin/bash
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; V5=/Users/kiosk/atlas_mark2/diagnostic/record_heights/v5run; cd $V5
T=1000000000000000; s=$(date +%s)
nice -n 19 $P -u -B atlas_v5.py $T 1000000000000286 1000000000000288 --name pair_1e15_286 --zs-step 0.01 --gen-timeout 21600 > runs_pair_1e15_286.out 2>&1; rc=$?
echo "pair_1e15_286 rc=$rc wall=$(( $(date +%s) - s ))s" >> pilot.log
s=$(date +%s); TL=21600 FP_MB=2500 RSS_KB=2500000 /Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh $P -B replay_target5.py runs/w$T/pair_1e15_286 replay_check_independent > runs/w$T/pair_1e15_286/replay_target_independent.log 2>&1
echo "pair_1e15_286 independent replay wall=$(( $(date +%s) - s ))s $(grep -v '^WD' runs/w$T/pair_1e15_286/replay_target_independent.log | tail -1) $(grep '^WD' runs/w$T/pair_1e15_286/replay_target_independent.log)" >> pilot.log
