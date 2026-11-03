#!/bin/sh
# review_v14d: own differential, kill/resume, attack, fuzz suites on libzfast.v14d (sequential, nice 19)
cd "$(dirname "$0")"; P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python
for s in diff kill attack fuzz; do
  echo "== $s start $(date +%T)"; nice -n 19 $P -B ${s}_rv.py out_$s > ${s}_rv.log 2>&1; echo "== $s rc=$? end $(date +%T)"; tail -1 ${s}_rv.log
done
