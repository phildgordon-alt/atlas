#!/bin/zsh
R=/Users/kiosk/atlas_mark2/diagnostic/zfast/review2; cd $R
while pgrep -f "sess_points.py v12a 100000000000000000000 5.0" > /dev/null; do sleep 15; done
FP_MB=800 RSS_KB=800000 TL=14400 /Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh ./run_rd.sh bin/rd4.v12a data/rows1e20.in data/rows1e20b.jsonl > data/rows1e20b.log 2>&1
echo J5DONE >> data/rows1e20b.log
