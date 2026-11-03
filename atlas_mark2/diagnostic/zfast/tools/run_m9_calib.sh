#!/bin/sh
# M9 calibration (PREDICTIONS_M9 S1-S3, I4): v14 sessions at 1e21 (H 61, Delta 0.012, centre 50, D 4), grid 3000 points from u = 0 step 0.004
# (= M8 calib_threads_m8.py), W = 1, 4, 8, one fresh process each, nice 19.  Appends JSON lines to runs/m9/calib/calib_v14.jsonl.
PY=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast; mkdir -p $Z/runs/m9/calib
for W in 8 4 1; do
  nice -n 19 $PY -B $Z/tools/m9_probe.py $Z/bin/libzfast.v14.dylib v14 1000000000000000000000 50.0 61.0 0.012 18 12 4 $W - 0.0 0.004 3000 >> $Z/runs/m9/calib/calib_v14.jsonl
done
