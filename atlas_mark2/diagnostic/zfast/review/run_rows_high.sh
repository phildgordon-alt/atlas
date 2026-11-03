#!/bin/sh
# waits for run_high.sh to finish (one heavy job at a time), then runs rows_high.py
cd /Users/kiosk/atlas_mark2/diagnostic/zfast/review
while ! grep -q ALLDONE data/run_high.log; do sleep 30; done
nice -n 19 /Users/kiosk/projects/atlas-rerun/.venv/bin/python rows_high.py
echo ROWSDONE
