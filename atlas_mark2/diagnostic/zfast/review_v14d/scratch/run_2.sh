#!/bin/sh
cd "$(dirname "$0")"; P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python
echo "== fuzz start $(date +%T)"; nice -n 19 $P -B fuzz_rv.py out_fuzz 4242 300 > fuzz_rv.log 2>&1; echo "== fuzz rc=$? $(date +%T)"; tail -1 fuzz_rv.log
echo "== a14d start $(date +%T)"; nice -n 19 $P -B attack_v14d.py out_a14d > attack_v14d.log 2>&1; echo "== a14d rc=$? $(date +%T)"; tail -1 attack_v14d.log
echo "== drv start $(date +%T)"; nice -n 19 $P -B drv_v14d.py > drv_v14d.log 2>&1; echo "== drv rc=$? $(date +%T)"; tail -1 drv_v14d.log
echo ALLDONE
