#!/bin/sh
cd /Users/kiosk/atlas_mark2/diagnostic/zfast
nice -n 19 /Users/kiosk/projects/atlas-rerun/.venv/bin/python -B tools/arb_ref.py < runs/m2/sign_points_1e15.txt > runs/m2/sign_arb_1e15.jsonl
nice -n 19 ./bin/arbref_smooth.dev4 < runs/m2/sign_points_1e16.txt > runs/m2/sign_arbsmooth_1e16.jsonl
echo done > runs/m2/run_sign_ref.done
