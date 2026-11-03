#!/bin/bash
# run_wide6.sh NAME T0 TLO THI H DELTA [CENTER] : v5z6 two-session wide window (THEORY_V5Z6.md):
#   1 pipeline: generator session (+ Turing grid in the same session) and the replay of record (driver stage 3, fresh process);
#   2 scan_turing5.py recount on RUN/turing_grid (the unchanged tool of record; no zfast call);
#   3 engine/regress_v1 turing_gate check (required gate, amendment A6).
# nice 19; ZFAST_THREADS = decomposition D (recorded), ZFAST_WORKERS = OS threads (output-free); RESUME=1 passes --resume.  Never deletes.
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z6; cd $Z; mkdir -p runs
N=$1; T0=$2; LO=$3; HI=$4; HH=$5; DD=$6; C=$7
export ZFAST_THREADS=${ZFAST_THREADS:-2}; export ZFAST_WORKERS=${ZFAST_WORKERS:-$ZFAST_THREADS}; export V4_LIM_GB=${V4_LIM_GB:-1.0}
unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT ZFAST_CKPT ZFAST_TURING_GRID
RA=""; [ "$RESUME" = "1" ] && RA="--resume"
[ -e runs/w$T0/$N ] && [ -z "$RA" ] && { echo "exists runs/w$T0/$N"; exit 1; }
CA=""; [ -n "$C" ] && CA="--zfast-center $C"
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T0 $LO $HI --name $N --zs-step 0.005 --gen-timeout 1209600 --wide --zfast-h $HH --zfast-delta $DD $CA --turing-grid $RA >> runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s D=$ZFAST_THREADS W=$ZFAST_WORKERS" >> runs/v5z6.log
R=runs/w$T0/$N; ULO=$($P -c "import json; print(json.load(open('$R/pieces.json'))['target'][0])"); UHI=$($P -c "import json; print(json.load(open('$R/pieces.json'))['target'][1])")
s=$(date +%s); nice -n 19 $P -B ../tools/scan_turing5.py recount $R/turing_grid $R/turing_recount.json --points $ULO,$UHI --win $ULO,$UHI > $R/turing_recount.log 2>&1; rc3=$?
echo "$N turing recount rc=$rc3 wall=$(( $(date +%s) - s ))s $(tail -1 $R/turing_recount.log | cut -c1-300)" >> runs/v5z6.log
( cd /Users/kiosk/atlas_mark2 && $P -B -m engine.regress_v1.turing_gate check $Z/$R $Z/$R/turing_recount.json > $Z/$R/turing_gate.log 2>&1 ); rc4=$?
echo "$N turing gate rc=$rc4 $(tail -1 $R/turing_gate.log)" >> runs/v5z6.log
echo "$N done" >> runs/v5z6.log
