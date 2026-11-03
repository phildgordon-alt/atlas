#!/bin/bash
# run_m8.sh : PREDICTIONS_M8 section 2 (run only after PREDICTIONS_M8.sha256 exists).  Sequential (one heavy job at a time), nice 19.
# 1 wide window [1e25, 1e25+100] with atlas_v5z5 (frozen tree, unmodified): same commands as atlas_v5z5/run_wide.sh except
#   --gen-timeout 57600 (run_wide.sh hard-codes 21600 s, below the 1e25 session cost at 4 threads; the timeout enters no certificate)
# 2 independent replay   3 Turing count (scan_turing5, separate method)   4 crosscheck + REQUIRED Turing gate   5 Lean export + audit
# 6 tight margins (diagnostic).  STOP files: runs/m8/STOP stops between stages.
set -u; unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; ZF=/Users/kiosk/atlas_mark2/diagnostic/zfast; Z=$ZF/atlas_v5z5
T0=10000000000000000000000000; HI=10000000000000000000000100; N=wide_1e25; RD=$Z/runs/w$T0/$N
L=$ZF/runs/m8/m8.log; M=$ZF/runs/m8; export ZFAST_THREADS=${ZFAST_THREADS:-4}; export V4_LIM_GB=${V4_LIM_GB:-1.0}
stopchk() { [ -e $M/STOP ] && { echo "STOP file present before $1 $(date)" >> $L; exit 2; }; [ $(df -g / | awk 'NR==2{print $4}') -lt 2 ] && { echo "disk floor before $1" >> $L; exit 1; }; }
[ -e $RD ] && { echo "exists $RD" >> $L; exit 1; }
sha256sum() { shasum -a 256 "$@"; }
shasum -a 256 -c $ZF/PREDICTIONS_M8.sha256 >> $L 2>&1 || { echo "PREDICTIONS_M8 hash check failed" >> $L; exit 1; }
echo "M8 start $(date) ZFAST_THREADS=$ZFAST_THREADS V4_LIM_GB=$V4_LIM_GB load $(sysctl -n vm.loadavg)" >> $L
stopchk generator
cd $Z; s=$(date +%s)
nice -n 19 $P -u -B atlas_v5.py $T0 $T0 $HI --name $N --zs-step 0.005 --gen-timeout 57600 --wide --zfast-h 61 --zfast-delta 0.012 > runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s threads=$ZFAST_THREADS $(date)" >> $L
[ -e $RD/summary.json ] || { echo "no summary.json; stop" >> $L; exit 1; }
stopchk independent
s=$(date +%s); nice -n 19 $P -B replay_target5.py $RD replay_check_independent > $RD/replay_target_independent.log 2>&1; rc2=$?
echo "$N independent replay rc=$rc2 wall=$(( $(date +%s) - s ))s $(tail -1 $RD/replay_target_independent.log) $(date)" >> $L
stopchk turing
s=$(date +%s)
nice -n 19 $ZF/tools/wd_fp_m8.sh 3000 $M/scan5_1e25.log $P -B $ZF/tools/scan_turing5.py scan $T0 $M/scan5_1e25 --centre 50 --H 91 --delta 0.008 --u0 -40 --n 45001 --points 0,100 --win 0,100 --DT 40 --threads $ZFAST_THREADS 2> $M/scan5_1e25.wd.log
echo "scan5_1e25 rc=$? wall=$(( $(date +%s) - s ))s $(date)" >> $L
NLO=$($P -c "import json;print(json.load(open('$M/scan5_1e25/scan_turing.json'))['turing']['0']['N'])"); NHI=$($P -c "import json;print(json.load(open('$M/scan5_1e25/scan_turing.json'))['turing']['100']['N'])")
echo "Turing N_lo=$NLO N_hi=$NHI" >> $L
[ "$NLO" != "None" ] && [ "$NHI" != "None" ] && (cd $Z && $P -B crosscheck.py runs/w$T0/$N $NLO $NHI >> $L 2>&1)
cd /Users/kiosk/atlas_mark2 && nice -n 19 $P -B -m engine.regress_v1.turing_gate check $RD $M/scan5_1e25/scan_turing.json > $M/turing_gate_1e25.out 2>&1; echo "turing gate rc=$? $(tail -1 $M/turing_gate_1e25.out)" >> $L
cd /Users/kiosk/atlas_mark2/formal/export && nice -n 19 $P -B export_certs.py --v5 v5z5_$N $Z/lean_audit $RD > $Z/lean_audit/export_v5z5_$N.log 2>&1
cd /Users/kiosk/atlas_mark2/formal && nice -n 19 .lake/build/bin/atlas_audit $Z/lean_audit/v5z5_$N.txt > $Z/lean_audit/audit_v5z5_$N.txt 2>&1; echo "lean audit rc=$? $(grep 'TOTAL VIOLATIONS' $Z/lean_audit/audit_v5z5_$N.txt)" >> $L
nice -n 19 $P -B $ZF/tools/tight_margin_v1.py $RD/certs/cert_*.json > $M/tight_v1_wide_1e25.jsonl 2> $M/tight_v1.err; echo "tight rc=$? $(date)" >> $L
echo "M8 done $(date)" >> $L
