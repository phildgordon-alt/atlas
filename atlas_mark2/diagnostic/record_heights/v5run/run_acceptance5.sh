#!/bin/bash
# atlas_v5 step 1 (THEORY_V5 section 9): re-run the atlas_v4 acceptance targets with exact heights, grid v4, evaluator zeta; compare with v4.
# Serial, nice 19 (the driver's 2.5 GB watchdog applies to every child process).
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; V5=/Users/kiosk/atlas_mark2/diagnostic/atlas_v5; V4=/Users/kiosk/atlas_mark2/diagnostic/atlas_v4
cd $V5; LOG=$V5/runs/acceptance5.log; echo "start $(date)" >> $LOG
run() { nice -n 19 $P -u -B atlas_v5.py "$@" --grid v4 --evaluator zeta > /dev/null 2>&1; echo "$5 rc=$?" >> $LOG; }
run 9000 9000 9010 --name v1_9000
run 7000 7005.06 7005.10 --name lehmer
run 7000 7002.48 7002.49 --name c7002
run 6820046 6820050.98 6820052.15 --name rosser
run 663310 663318.4 663318.6 --name t2_663318
run 7000 7005.0 7005.2 --name lehmer_full_pair
run 10000000 10000000 10000002 --name t4v4_10000000
for t in w9000.00/v1_9000 w7000.00/lehmer w7000.00/c7002 w6820046.00/rosser w663310.00/t2_663318 w7000.00/lehmer_full_pair w10000000.00/t4v4_10000000; do
  $P -B compare_v4.py $V4/runs/$t runs/$t >> $LOG 2>&1; echo "compare $t rc=$?" >> $LOG
  nice -n 19 $P -B replay_target5.py runs/$t replay_check_independent > runs/$t/replay_target_independent.log 2>&1
  echo "independent replay $t rc=$? $(tail -1 runs/$t/replay_target_independent.log)" >> $LOG
done
echo "done $(date)" >> $LOG
