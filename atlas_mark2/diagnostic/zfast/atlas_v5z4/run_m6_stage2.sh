#!/bin/bash
# run_m6_stage2.sh : M6 stage 2 (after stage 1): [10^24, +2] (w_1e24) and the 10^24 scan's closest-pair window (wp_1e24), then two
# more close-pair windows at 10^23 from scan2_1e23 (wq_1e23 = [-24, -22], wr_1e23 = [-2, 0]); each via run_window_m6.sh (v5z4
# pipeline + independent replay), then pair_gap2, provenance_m6, and the Lean export + atlas_audit into atlas_v5z4/lean_audit/.
# ONE zfast thread, nice 19.  New names only; nothing deleted.
cd /Users/kiosk/atlas_mark2/diagnostic/zfast || exit 1
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z4; export ZFAST_THREADS=1; L=$Z/runs/m6.log
T24=1000000000000000000000000; T23=100000000000000000000000
K=$(python3 -c "import json;print(json.load(open('runs/m6/scan3_1e24/scan_turing.json'))['closest_pair']['window_offsets'][0])") || { echo "no scan" >> $L; exit 1; }
echo "STAGE2 start $(date) pair window offset K=$K" >> $L
post() {  # post NAME T0
  R=$Z/runs/w$2/$1
  $P -B tools/pair_gap2.py $R > $R/pair_gap2.json 2>> $L
  ZFAST_THREADS=1 python3 -B tools/provenance_m6.py $R >> $L 2>&1
  ( cd /Users/kiosk/atlas_mark2/formal && python3 export/export_certs.py --v5 v5z4_$1 $Z/lean_audit $R > $Z/lean_audit/export_v5z4_$1.log 2>&1 \
    && .lake/build/bin/atlas_audit $Z/lean_audit/v5z4_$1.txt > $Z/lean_audit/audit_v5z4_$1.txt 2>&1 )
  echo "$1 lean: $(grep -h 'TOTAL VIOLATIONS\|certificates' $Z/lean_audit/audit_v5z4_$1.txt | tr '\n' ' ')" >> $L
}
cd $Z
./run_window_m6.sh w_1e24 $T24 $T24 $(python3 -c "print($T24+2)") 0.005 - - 1.0;            post w_1e24 $T24
./run_window_m6.sh wp_1e24 $T24 $(python3 -c "print($T24+$K)") $(python3 -c "print($T24+$K+2)") 0.005 - - $(python3 -c "print($K+1.0)");  post wp_1e24 $T24
./run_window_m6.sh wq_1e23 $T23 $(python3 -c "print($T23-24)") $(python3 -c "print($T23-22)") 0.005 - - -23.0;  post wq_1e23 $T23
./run_window_m6.sh wr_1e23 $T23 $(python3 -c "print($T23-2)") $T23 0.005 - - -1.0;                               post wr_1e23 $T23
echo "STAGE2 DONE $(date)" >> $L
