#!/bin/bash
# M14 reboot-resume rehearsal, STEP 1 (run BEFORE the reboot).  usage: step1_start_and_stop.sh [T0 (default 10^20, max 10^20)] [LINES (default 300)]
# Starts a checkpointed atlas_v5za window [T0, T0+10] (wide session, Turing grid; D4 W8; nice 19), waits until the generator checkpoint has
# >= LINES lines, then SIGKILLs the whole pipeline (driver + generator, as a power cut would), records an environment fingerprint and the
# checkpoint state in runs/m14/reboot/NAME/, and prints NAME.  Deletes nothing.
set -u; source "$(dirname "$0")/common.sh"
T0=${1:-100000000000000000000}; LINES=${2:-300}
[ "$(echo "$T0 > 100000000000000000000" | bc)" = "1" ] && { echo "REFUSING: T0 above 10^20 (M14 rule)"; exit 1; }
no_production || exit 1
NAME=rr_$(date +%Y%m%d_%H%M%S); D=$RR/$NAME; mkdir -p $D; RUN=$ZA/runs/w$T0/$NAME
echo "$T0" > $D/T0; echo "$NAME" > $D/NAME
fingerprint > $D/fingerprint_before.txt
( cd $ZA && exec nice -n 19 $PY -u -B $(drv_args $T0 $NAME) >> $D/pipeline_start.out 2>&1 ) & PPID_=$!
t0=$(date +%s)
while :; do
  n=$( [ -f $RUN/zfast_ckpt_gen.txt ] && wc -l < $RUN/zfast_ckpt_gen.txt || echo 0 ); n=${n// /}
  [ "$n" -ge "$LINES" ] && break
  kill -0 $PPID_ 2>/dev/null || { echo "FAILED: the pipeline ended before $LINES checkpoint lines (see $D/pipeline_start.out)"; exit 1; }
  [ $(( $(date +%s) - t0 )) -gt 3600 ] && { echo "FAILED: timeout"; exit 1; }
  sleep 0.2
done
G=$(pgrep -f "gen_target5.py $RUN"); kill -9 $G $PPID_ 2>/dev/null; pkill -9 -f "atlas_v5.py $T0 .* --name $NAME" 2>/dev/null; sleep 1
{ echo "killed_at $(date)"; echo "lines_at_kill $(wc -l < $RUN/zfast_ckpt_gen.txt)"; echo "ckpt_sha $(shasum -a 256 $RUN/zfast_ckpt_gen.txt | cut -d' ' -f1)"
  echo "zs_json_exists $([ -e $RUN/zs.json ] && echo yes || echo no)"; echo "nonce $(cat $RUN/zfast_ckpt_nonce.txt)"; } > $D/stopped.txt
head -c 1200 $RUN/zfast_ckpt_gen.txt | head -1 > $D/ckpt_header_before.txt
cat $D/stopped.txt; echo "STEP 1 DONE: $NAME.  Now reboot the Mac (Apple menu > Restart), log in, then run: $(dirname "$0")/step2_resume_after_reboot.sh $NAME"
