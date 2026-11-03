#!/bin/bash
# M14 reboot-resume rehearsal, STEP 2 (run AFTER the reboot).  usage: step2_resume_after_reboot.sh NAME [--no-reboot-smoke]
# 1 checks that a reboot happened since step 1 (kern.boottime) unless --no-reboot-smoke (script smoke test only; not the rehearsal),
#   and compares the environment fingerprint (an OS / library change means the library will refuse the resume BY DESIGN);
# 2 resumes the window with --resume (same nonce, key, checkpoint); 3 runs an uninterrupted reference window (fresh name) and compares
#   certificates, zs.json, measurements, Turing grid (engine/regress_v1 compare_regenerated); 4 writes runs/m14/reboot/NAME/result.json.
set -u; source "$(dirname "$0")/common.sh"
NAME=${1:?NAME from step 1}; SMOKE=${2:-}; D=$RR/$NAME; T0=$(cat $D/T0); RUN=$ZA/runs/w$T0/$NAME
no_production || exit 1
fingerprint > $D/fingerprint_after.txt
b0=$(grep '^boottime' $D/fingerprint_before.txt); b1=$(grep '^boottime' $D/fingerprint_after.txt); REBOOTED=$([ "$b0" != "$b1" ] && echo true || echo false)
if [ "$REBOOTED" != "true" ] && [ "$SMOKE" != "--no-reboot-smoke" ]; then echo "REFUSING: no reboot since step 1 ($b1). Reboot first (or pass --no-reboot-smoke for a script smoke test)."; exit 1; fi
diff <(grep -v '^date\|^boottime' $D/fingerprint_before.txt) <(grep -v '^date\|^boottime' $D/fingerprint_after.txt) > $D/fingerprint_diff.txt; FPSAME=$([ -s $D/fingerprint_diff.txt ] && echo false || echo true)
[ "$FPSAME" = "true" ] || { echo "NOTE: the environment changed since step 1 (see $D/fingerprint_diff.txt); the library is expected to REFUSE the resume."; }
s=$(date +%s); ( cd $ZA && nice -n 19 $PY -u -B $(drv_args $T0 $NAME --resume) > $D/pipeline_resume.out 2>&1 ); RC=$?; WR=$(( $(date +%s) - s ))
REF=${NAME}_ref; s=$(date +%s); ( cd $ZA && nice -n 19 $PY -u -B $(drv_args $T0 $REF) > $D/pipeline_ref.out 2>&1 ); RCR=$?; WF=$(( $(date +%s) - s ))
cd /Users/kiosk/atlas_mark2 && $PY -B - "$ZA/runs/w$T0/$REF" "$RUN" "$D" "$RC" "$RCR" "$REBOOTED" "$FPSAME" "$WR" "$WF" <<'PYEOF'
import json, sys, hashlib
from pathlib import Path
from engine.regress_v1 import zfast
A, B, D = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); rc, rcr = int(sys.argv[4]), int(sys.argv[5])
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
c = zfast.compare_regenerated(dict(run=str(A)), B)
grid = all((A / 'turing_grid' / f).exists() and (B / 'turing_grid' / f).exists() and sha(A / 'turing_grid' / f) == sha(B / 'turing_grid' / f) for f in ('grid.npz', 'zeros_intervals.json'))
sc = [json.loads(l) for l in open(B / 'zfast_ckpt_gen.txt.sessions.jsonl')] if (B / 'zfast_ckpt_gen.txt.sessions.jsonl').exists() else []
lines_at_kill = int([l.split()[1] for l in open(D / 'stopped.txt') if l.startswith('lines_at_kill')][0])
s = sc[-1]['info'] if sc else {}
ok = rc == 0 and rcr == 0 and c['identical'] and grid and s.get('items_loaded', 0) >= lines_at_kill - 2 and s.get('verified') == min(64, s.get('items_loaded') or 0)
res = dict(name=B.name, rebooted=sys.argv[6] == 'true', fingerprint_same=sys.argv[7] == 'true', resume_rc=rc, ref_rc=rcr, resume_wall_s=int(sys.argv[8]), ref_wall_s=int(sys.argv[9]),
           lines_at_kill=lines_at_kill, resumed_session=dict(items=s.get('items'), items_loaded=s.get('items_loaded'), verified=s.get('verified'), rejected=s.get('lines_rejected')),
           window_identical=c['identical'], turing_grid_identical=grid, PASS=bool(ok),
           kind='REHEARSAL across a reboot' if sys.argv[6] == 'true' else 'SCRIPT SMOKE TEST (no reboot): not the rehearsal')
json.dump(dict(res, compare=c), open(D / 'result.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1)); print('PASS' if ok else 'FAIL')
PYEOF
