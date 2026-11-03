#!/bin/bash
# run_wide.sh NAME T0 TLO THI H DELTA [CENTER] : v5z5 wide-session window (one strict zfast session per process; THEORY_V5Z5.md):
# pipeline (generator + replay) + independent replay, nice 19, driver footprint kill V4_LIM_GB (default 1.0 GB), threads ZFAST_THREADS.
# CENTER defaults to the midpoint of the Z span.  Never deletes (fresh NAME required).  Log runs/v5z5.log.
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z5; cd $Z; mkdir -p runs
N=$1; T0=$2; LO=$3; HI=$4; HH=$5; DD=$6; C=$7
export ZFAST_THREADS=${ZFAST_THREADS:-2}; export V4_LIM_GB=${V4_LIM_GB:-1.0}; unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT
[ -e runs/w$T0/$N ] && { echo "exists runs/w$T0/$N"; exit 1; }
CA=""; [ -n "$C" ] && CA="--zfast-center $C"
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T0 $LO $HI --name $N --zs-step 0.005 --gen-timeout 21600 --wide --zfast-h $HH --zfast-delta $DD $CA > runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s threads=$ZFAST_THREADS" >> runs/v5z5.log
s=$(date +%s); nice -n 19 $P -B replay_target5.py runs/w$T0/$N replay_check_independent > runs/w$T0/$N/replay_target_independent.log 2>&1; rc2=$?
echo "$N independent replay rc=$rc2 wall=$(( $(date +%s) - s ))s $(tail -1 runs/w$T0/$N/replay_target_independent.log)" >> runs/v5z5.log
echo "$N done" >> runs/v5z5.log
