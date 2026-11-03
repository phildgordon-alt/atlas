#!/bin/zsh
# review2 job queue: strictly one compute process at a time (nice 19, 1 thread). Logs to data/jobs3.log
R=/Users/kiosk/atlas_mark2/diagnostic/zfast/review2; PY=/Users/kiosk/projects/atlas-rerun/.venv/bin/python
cd $R/py
while pgrep -f "jobs.sh" >/dev/null; do sleep 20; done
echo "$(date) start prep" >> $R/data/jobs3.log
nice -n 19 $PY -P bat2_prep3.py > $R/data/bat2_prep3.log 2>&1; echo "$(date) prep rc=$?" >> $R/data/jobs3.log
nice -n 19 $PY -P bat2_ref.py > $R/data/bat2_ref.log 2>&1; echo "$(date) ref rc=$?" >> $R/data/jobs3.log
nice -n 19 $PY -P bat2_run.py $R/bin/rd4.v12a prod_v12a >> $R/data/bat2_runs3.log 2>&1; echo "$(date) prod v12a rc=$?" >> $R/data/jobs3.log
nice -n 19 $PY -P bat2_run.py $R/bin/rd4.v10b prod_v10b v10b >> $R/data/bat2_runs3.log 2>&1; echo "$(date) prod v10b rc=$?" >> $R/data/jobs3.log
nice -n 19 $PY -P bat2_run.py $R/bin/rd4.v12a prodlight_v12a light >> $R/data/bat2_runs3.log 2>&1
for m in ec phfloor interp fxeps roundZ sumZ trig7 rs wpoly hjet logp m3mom m3trig m3sum m3tay m3ctay Vb nozb bugquad bugtail bugws bughc bugconj; do
  nice -n 19 $PY -P bat2_run.py $R/bin/rd4.$m mut_$m light >> $R/data/bat2_runs3.log 2>&1; echo "$(date) mut $m rc=$?" >> $R/data/jobs3.log
done
F=/Users/kiosk/atlas_mark2/diagnostic/zfast/review/data
true
echo "$(date) high rc=$? ALLDONE" >> $R/data/jobs3.log
