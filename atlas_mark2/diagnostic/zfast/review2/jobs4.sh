#!/bin/zsh
R=/Users/kiosk/atlas_mark2/diagnostic/zfast/review2; PY=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; cd $R
FP_MB=800 RSS_KB=800000 TL=7200 /Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh $PY sess_points.py v12a 100000000000000000000 5.0 data/ep_hp1e20.txt data/v12a_hp1e20_endpoints.jsonl > data/v12a_hp1e20.log 2>&1
echo "S3 100000000000000000000 1.0 4 0.15 18 12 2.8 3 0.37 1.5 -0x1.3f5c28f5c28f6p-2
S3 100000000000000000000 1.0 4 0.15 18 12 1.6 3 0.37 1.5 -0x1.3f5c28f5c28f6p-2
S1 100000000000000000000 1.0 3 0.2 16 12 2.8 3 0.37 1.5 -0x1.3f5c28f5c28f6p-2
S1 100000000000000000000 1.0 3 0.2 16 12 1.6 3 0.37 1.5 -0x1.3f5c28f5c28f6p-2
R1 100000000000000000000 0x1.7ae147ae147aep-2 2.8 12
R1 100000000000000000000 0x1.7ae147ae147aep-2 1.6 12" > data/rows1e20.in
FP_MB=800 RSS_KB=800000 TL=14400 /Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh bin/rd4.v12a < data/rows1e20.in > data/rows1e20.jsonl 2> data/rows1e20.err
echo J4DONE >> data/rows1e20.err
