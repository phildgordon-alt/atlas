#!/bin/sh
# Atlas repository: re-verify the RH window certificates from the stored data in this repository.
#   PY=/path/to/python3 (with python-flint 0.9.0, numpy, scipy) ./verify/quick_verify.sh
# Optional:  ATLAS_AUDIT_BIN=/path/to/atlas_audit   (Lean audit step; otherwise atlas_mark2/formal/.lake/build/bin/atlas_audit if built)
#            WITH_OCTOBER=1                          (also unpack data_release/atlas_bundle_2026-10-08.tar.gz and run ITS quick_verify)
#            OUT=dir                                 (default ./verify_out; nothing is written anywhere else)
# One process at a time, nice 19, RSS watchdog 3 GB per child. Refuses python -O / PYTHONOPTIMIZE (Atlas safety checks are asserts).
set -u
B=$(cd "$(dirname "$0")/.." && pwd); cd "$B"
PY=${PY:-python3}; OUT=${OUT:-$B/verify_out}; mkdir -p "$OUT"
unset PYTHONOPTIMIZE; export PYTHONDONTWRITEBYTECODE=1
FAIL=0; ok() { echo "  OK   $1"; }; bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
T0=$(date +%s)

echo "[0] environment"
$PY -c "import flint, numpy, scipy, mpmath, sys, platform; print('  python', sys.version.split()[0], '| python-flint', flint.__version__, '| numpy', numpy.__version__, '| scipy', scipy.__version__, '| mpmath', mpmath.__version__, '|', platform.platform())" || { echo "python-flint/numpy/scipy/mpmath missing: set PY (see README)"; exit 2; }
$PY -c "import flint,sys; sys.exit(0 if flint.__version__=='0.9.0' else 1)" || echo "  WARN python-flint is not 0.9.0: bit-identity with the stored records is only claimed for 0.9.0 (FLINT 3.6.0)"

echo "[1] SHA256SUMS (every file in the repository)"
if command -v sha256sum >/dev/null 2>&1; then S="sha256sum -c --quiet"; else S="shasum -a 256 -c --quiet"; fi
if nice -n 19 $S SHA256SUMS >"$OUT/sha_check.txt" 2>&1; then ok "all files match SHA256SUMS ($(wc -l < SHA256SUMS | tr -d ' ') files)"; else bad "SHA256SUMS mismatch (see $OUT/sha_check.txt)"; fi

echo "[2] RH windows: frozen replay logic on every certificate (stored measurements), comparison with the stored replay records,"
echo "    exact tiling + claim (B), Arb/Turing cross-count, Turing recount from the stored grid; plus 2 negative controls"
if nice -n 19 $PY -B verify/verify_windows.py --set all --control --out "$OUT/windows" | tee "$OUT/windows.txt" | sed 's/^/  /'; then ok "all windows"; else bad "windows (see $OUT/windows.txt)"; fi

echo "[3] Lean: exact re-export of the certificate files must equal the stored Lean datasets; Lean audit if atlas_audit is built"
if nice -n 19 $PY -B verify/verify_lean.py "$OUT/lean" | tee "$OUT/lean.txt" | sed 's/^/  /'; then ok "Lean datasets"; else bad "Lean (see $OUT/lean.txt)"; fi

if [ "${WITH_OCTOBER:-0}" = "1" ]; then
  echo "[4] October 2026 bundle (atlas_v4 windows incl. Lehmer's pair, degree-2 L-functions, Tollis fields): its own quick_verify"
  mkdir -p "$OUT/october" && tar xzf data_release/atlas_bundle_2026-10-08.tar.gz -C "$OUT/october" \
    && (cd "$OUT/october/bundle" && PY=$PY OUT="$OUT/october/out" sh ./quick_verify.sh) > "$OUT/october.txt" 2>&1 \
    && ok "October bundle quick_verify: $(tail -1 "$OUT/october.txt")" || bad "October bundle (see $OUT/october.txt)"
fi

echo "done in $(( $(date +%s) - T0 )) s; failures: $FAIL; outputs in $OUT"
exit $FAIL
