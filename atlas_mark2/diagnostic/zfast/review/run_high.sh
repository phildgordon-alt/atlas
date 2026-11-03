#!/bin/sh
# background pipeline for the high-height comparisons (one heavy process at a time, nice 19, watchdog 800 MB on references)
set -e
cd /Users/kiosk/atlas_mark2/diagnostic/zfast/review
PY=/Users/kiosk/projects/atlas-rerun/.venv/bin/python
nice -n 19 $PY run_points_high.py
$PY -c "
import json
p=json.load(open('data/points_high.json')); s=[]
cnt={}
for x in p:
    e=len(str(x['T0']))
    if x['cls']=='rand' and cnt.get(e,0) < (1 if e==20 else 2) and e>=18:
        s.append(x); cnt[e]=cnt.get(e,0)+1
json.dump(s, open('data/points_highaz.json','x'), indent=0); print(len(s))
"
nice -n 19 $PY run_ref.py high GZ
nice -n 19 $PY run_ref.py highaz AZ 200
echo ALLDONE
