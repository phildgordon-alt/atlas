#!/bin/bash
# run_window_m6.sh NAME T0 TLO THI STEP NLO NHI CENTER : M6 copy of run_window.sh (unchanged pipeline: atlas_v5.py + independent
# replay + optional crosscheck) with (a) its own log runs/m6.log, (b) --gen-timeout 172800 (the 10^24 generator needs ~5 h on one
# thread), (c) V4_LIM_GB=0.5 so the driver kills any stage above the M6 footprint cap.  Never deletes (fresh NAME required).
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z4; cd $Z; mkdir -p runs
N=$1; T0=$2; LO=$3; HI=$4; ST=$5; NLO=$6; NHI=$7; export ZFAST_CENTER=$8; export ZFAST_THREADS=${ZFAST_THREADS:-1}; export V4_LIM_GB=0.5
L=runs/m6.log
[ -e runs/w$T0/$N ] && { echo "exists runs/w$T0/$N" | tee -a $L; exit 1; }
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T0 $LO $HI --name $N --zs-step $ST --gen-timeout 172800 > runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s threads=$ZFAST_THREADS" >> $L
s=$(date +%s); nice -n 19 $P -B replay_target5.py runs/w$T0/$N replay_check_independent > runs/w$T0/$N/replay_target_independent.log 2>&1; rc2=$?
echo "$N independent replay rc=$rc2 wall=$(( $(date +%s) - s ))s $(tail -1 runs/w$T0/$N/replay_target_independent.log)" >> $L
if [ "$NLO" != "-" ]; then python3 -B crosscheck.py runs/w$T0/$N $NLO $NHI >> $L 2>&1; fi
echo "$N done" >> $L
