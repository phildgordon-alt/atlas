#!/bin/bash
# run_m11.sh : PREDICTIONS_M11 (M10 X1-X13 carried to 1e26 on atlas_v5z7 / libzfast.v14).  Run only after PREDICTIONS_M11.sha256 exists.
# Sequential, nice 19.  1 run_wide7.sh (generator session + Turing grid, replay of record, scan_turing5 recount, REQUIRED turing gate)
# 2 crosscheck.py   3 Lean export + atlas_audit   4 tight_margin_v1 (diagnostic).  D=4 (ZFAST_THREADS, recorded), W=8 (ZFAST_WORKERS).
# The tree watchdog/monitor tools/m10_monitor.py (footprint <= 3 GB, disk >= 2 GB, projection STOP > 16 h) is started on this
# script's PID.  runs/m10/STOP stops between stages.  Never deletes.
set -u; unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT ZFAST_CKPT ZFAST_TURING_GRID
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; ZF=/Users/kiosk/atlas_mark2/diagnostic/zfast; Z=$ZF/atlas_v5z7
T0=100000000000000000000000000; HI=100000000000000000000000100; N=wide7_1e26; RD=$Z/runs/w$T0/$N
M=$ZF/runs/m11; L=$M/m11.log
stopchk() { [ -e $M/STOP ] && { echo "STOP file present before $1 $(date)" >> $L; exit 2; }; [ $(df -g /Users/kiosk | awk 'NR==2{print $4}') -lt 2 ] && { echo "disk floor before $1" >> $L; exit 1; }; }
envsnap() { { echo "env snapshot $(date)"; sw_vers; uname -a; shasum -a 256 $ZF/bin/libzfast.v14.dylib; for l in /opt/homebrew/opt/flint/lib/libflint.24.0.dylib /opt/homebrew/opt/gmp/lib/libgmp.10.dylib /opt/homebrew/opt/mpfr/lib/libmpfr.6.dylib; do echo "$l -> $(readlink -f $l)"; shasum -a 256 $(readlink -f $l); done; brew list --versions flint gmp mpfr 2>/dev/null; $P -c "import flint; print('python-flint', flint.__version__)"; } > $1 2>&1; }
[ -e $RD ] && { echo "exists $RD" >> $L; exit 1; }
cd $ZF && shasum -a 256 -c PREDICTIONS_M11.sha256 >> $L 2>&1 || { echo "PREDICTIONS_M11 hash check failed" >> $L; exit 1; }
(cd $Z && shasum -a 256 -c V5Z7_FREEZE.sha256 > $M/freeze_check.txt 2>&1) || { echo "V5Z7 freeze check failed" >> $L; exit 1; }
mkdir -p $M; envsnap $M/env_start.txt
export ZFAST_THREADS=4 ZFAST_WORKERS=8 V4_LIM_GB=1.0
echo "M11 start $(date) pid $$ ZFAST_THREADS=$ZFAST_THREADS ZFAST_WORKERS=$ZFAST_WORKERS V4_LIM_GB=$V4_LIM_GB load $(sysctl -n vm.loadavg) free_GB $(df -g /Users/kiosk | awk 'NR==2{print $4}')" >> $L
nice -n 19 $P -B $ZF/tools/m10_monitor.py $$ $RD $M/monitor.jsonl $M/STOP --lim-gb 3.0 --max-window-h 16 --disk-floor-gb 2 > $M/monitor.err 2>&1 &
stopchk pipeline
s=$(date +%s); bash $Z/run_wide7.sh $N $T0 $T0 $HI 91 0.008; echo "run_wide7 rc=$? wall=$(( $(date +%s) - s ))s $(date)" >> $L
tail -4 $Z/runs/v5z7.log >> $L
[ -e $RD/summary.json ] || { echo "no summary.json; stop" >> $L; exit 1; }
stopchk crosscheck
NLO=$($P -c "import json;r=json.load(open('$RD/turing_recount.json'))['turing']['0'];print(r['N_lower'] if r['N_lower']==r['N_upper'] else 'None')" 2>>$L)
NHI=$($P -c "import json;r=json.load(open('$RD/turing_recount.json'))['turing']['100'];print(r['N_lower'] if r['N_lower']==r['N_upper'] else 'None')" 2>>$L)
echo "Turing N_lo=$NLO N_hi=$NHI" >> $L
[ -n "$NLO" ] && [ -n "$NHI" ] && [ "$NLO" != "None" ] && [ "$NHI" != "None" ] && (cd $Z && nice -n 19 $P -B crosscheck.py runs/w$T0/$N $NLO $NHI >> $L 2>&1)
stopchk lean
mkdir -p $Z/lean_audit
s=$(date +%s); cd /Users/kiosk/atlas_mark2/formal/export && nice -n 19 python3 -B export_certs.py --v5 v5z7_$N $Z/lean_audit $RD > $Z/lean_audit/export_v5z7_$N.log 2>&1; echo "lean export rc=$? wall=$(( $(date +%s) - s ))s" >> $L
s=$(date +%s); cd /Users/kiosk/atlas_mark2/formal && nice -n 19 .lake/build/bin/atlas_audit $Z/lean_audit/v5z7_$N.txt > $Z/lean_audit/audit_v5z7_$N.txt 2>&1; echo "lean audit rc=$? wall=$(( $(date +%s) - s ))s $(grep 'TOTAL VIOLATIONS' $Z/lean_audit/audit_v5z7_$N.txt)" >> $L
stopchk tight
s=$(date +%s); nice -n 19 $P -B $ZF/tools/tight_margin_v1.py $RD/certs/cert_*.json > $M/tight_v1_wide7_1e26.jsonl 2> $M/tight_v1.err; echo "tight rc=$? wall=$(( $(date +%s) - s ))s $(date)" >> $L
envsnap $M/env_end.txt; cmp -s <(grep -v "env snapshot" $M/env_start.txt) <(grep -v "env snapshot" $M/env_end.txt) && echo "env snapshots identical" >> $L || echo "ENV SNAPSHOTS DIFFER" >> $L
echo "M11 done $(date)" >> $L
