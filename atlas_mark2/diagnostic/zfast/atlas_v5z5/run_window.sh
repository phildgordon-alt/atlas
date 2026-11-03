#!/bin/bash
# run_window.sh NAME T0 TLO THI STEP NLO NHI CENTER : v5z5 legacy-mode window (= v5z4 run_window.sh, own log runs/v5z5.log) + independent
# replay + optional crosscheck.  ZFAST_THREADS from the caller (recorded by the driver).  Never deletes (fresh NAME required).
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z5; cd $Z; mkdir -p runs
N=$1; T0=$2; LO=$3; HI=$4; ST=$5; NLO=$6; NHI=$7; export ZFAST_CENTER=$8; export ZFAST_THREADS=${ZFAST_THREADS:-2}; unset PYTHONOPTIMIZE
[ -e runs/w$T0/$N ] && { echo "exists runs/w$T0/$N"; exit 1; }
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T0 $LO $HI --name $N --zs-step $ST --gen-timeout 21600 > runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s threads=$ZFAST_THREADS" >> runs/v5z5.log
s=$(date +%s); nice -n 19 $P -B replay_target5.py runs/w$T0/$N replay_check_independent > runs/w$T0/$N/replay_target_independent.log 2>&1; rc2=$?
echo "$N independent replay rc=$rc2 wall=$(( $(date +%s) - s ))s $(tail -1 runs/w$T0/$N/replay_target_independent.log)" >> runs/v5z5.log
if [ "$NLO" != "-" ]; then $P -B crosscheck.py runs/w$T0/$N $NLO $NHI >> runs/v5z5.log 2>&1; fi
echo "$N done" >> runs/v5z5.log
