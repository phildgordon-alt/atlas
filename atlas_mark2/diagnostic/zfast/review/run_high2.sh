#!/bin/sh
# trimmed high-height references (replaces the stopped run_high.sh; its 6 finished 1e17 references are kept and used)
cd /Users/kiosk/atlas_mark2/diagnostic/zfast/review
PY=/Users/kiosk/projects/atlas-rerun/.venv/bin/python
nice -n 19 $PY run_ref.py high2 GZ
nice -n 19 $PY run_ref.py high2az AZ 200
echo ALLDONE
nice -n 19 $PY rows_high.py
echo ROWSDONE
