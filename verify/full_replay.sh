#!/bin/sh
# Full independent replay of ONE stored RH window, recomputing everything the certificates use (Z sign changes and explicit-formula
# rows from fresh zfast sessions, models, LP checks in Arb, exact tiling, claim (B)), on a scratch COPY of the run directory.
#   PY=... ./verify/full_replay.sh TREE RUNSUB [OUT]
#   e.g. ./verify/full_replay.sh atlas_v5z w100000000000000000/z_1e17            (about 1 min)
#        ./verify/full_replay.sh atlas_v5z7 w10000000000000000000000/wide7_1e22   (about 10 min on 8 cores)
#        ./verify/full_replay.sh atlas_v5z7 w100000000000000000000000000/wide7_1e26  (about 4.5 h on 8 cores, 0.3 GB)
# Needs the zfast library: atlas_mark2/diagnostic/zfast/bin/libzfast.v*.dylib is macOS arm64 linked against Homebrew FLINT 3.6.0 /
# GMP / MPFR (/opt/homebrew/opt/...). The sha-pinned provider refuses any other library build. The stored replay records are compared
# with the new ones afterwards (pass/fail and min_candidate_lower per certificate, replay_check.json verdicts).
set -u
B=$(cd "$(dirname "$0")/.." && pwd); PY=${PY:-python3}
TREE=$1; SUB=$2; OUT=${3:-$B/verify_out/full_replay}
case "$TREE" in record_heights) TD=$B/atlas_mark2/diagnostic/record_heights/v5run;; *) TD=$B/atlas_mark2/diagnostic/zfast/$TREE;; esac
SRC=$TD/runs/$SUB; [ -f "$SRC/pieces.json" ] || { echo "no run $SRC"; exit 2; }
W=$OUT/$TREE/$SUB; [ -e "$W" ] && { echo "$W exists (never overwrite)"; exit 2; }
mkdir -p "$W"; cp -R "$SRC/certs" "$SRC/certs_np" "$SRC/pieces.json" "$W/"
unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT ZFAST_CKPT
export ATLAS_REPO=$B PYTHONPATH=$B/verify/boot ATLAS_REWRITE_DIRS=$OUT PYTHONDONTWRITEBYTECODE=1
export ZFAST_THREADS=$($PY -c "import json; print((json.load(open('$SRC/pieces.json')).get('zfast_session') or {}).get('threads') or 2)")
export ZFAST_WORKERS=${ZFAST_WORKERS:-$ZFAST_THREADS}
s=$(date +%s)
(cd "$TD" && nice -n 19 $PY -u -B "$B/verify/run_rewritten.py" "$TD/replay_target5.py" "$W" > "$W/replay_target.log" 2>&1); rc=$?
echo "replay rc=$rc wall=$(( $(date +%s) - s )) s (ZFAST_THREADS=$ZFAST_THREADS ZFAST_WORKERS=$ZFAST_WORKERS)"
$PY - "$SRC" "$W" <<'PYEOF'
import json, sys, os
src, new = sys.argv[1], sys.argv[2]
def load(d, sub):
    p = os.path.join(d, sub, 'replay.jsonl')
    return {(os.path.basename(json.loads(l)['cert']), os.path.basename(os.path.dirname(json.loads(l)['cert'])), json.loads(l)['hardened']): json.loads(l) for l in open(p)} if os.path.exists(p) else {}
S = load(src, 'replay_check_independent') or load(src, 'replay_check'); N = load(new, 'replay_check')
same = sum(1 for k in N if k in S and S[k].get('passed') == N[k].get('passed') and S[k].get('min_candidate_lower') == N[k].get('min_candidate_lower'))
rc = json.load(open(os.path.join(new, 'replay_check', 'replay_check.json')))
print(f"new replay: passed (claim A) {rc.get('passed')}, passed_B {rc.get('passed_B')}; records {len(N)}, identical to stored {same}/{len(S)}")
sys.exit(0 if rc.get('passed') and rc.get('passed_B') and same == len(S) == len(N) else 1)
PYEOF
