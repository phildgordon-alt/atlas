"""Builds atlas_v5z6/ from atlas_v5z5/ (new files only; v5z5 is never written).  OPTIMIZE_M9.md section 3, PREDICTIONS_M9.md, THEORY_V5Z6.md.
Byte copies of every v5z5 code file except: lib/zfast_provider.py (new source tools/v5z6_src/zfast_provider.py: libzfast.v14), atlas_v5.py
and lib/gen_target5.py (scripted, counted replacements below), run_wide6.sh (new), THEORY_V5Z6.md (new).  replay_target5.py, every verifier,
model, LP, row and tiling file is a byte copy.  Ends by writing V5Z6_FREEZE.sha256."""
import os, sys, shutil, hashlib
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
Z5 = ZF + 'atlas_v5z5/'; Z6 = ZF + 'atlas_v5z6/'; SRC = ZF + 'tools/v5z6_src/'
if os.path.exists(Z6): raise SystemExit(f'{Z6} exists: never overwrite (make a new version)')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rep(s, old, new, n=1):
    if s.count(old) != n: raise RuntimeError(f'replacement anchor found {s.count(old)} times (want {n}): {old[:80]!r}')
    return s.replace(old, new)


# check the v5z5 tree is the frozen one before copying anything
for l in open(Z5 + 'V5Z5_FREEZE.sha256'):
    h, f = l.split()
    if sha(os.path.normpath(Z5 + f)) != h: raise RuntimeError(f'atlas_v5z5 differs from its freeze: {f}')
os.makedirs(Z6 + 'lib'); os.makedirs(Z6 + 'nzeros'); os.makedirs(Z6 + 'runs')

# 1 byte copies
for f in ['crosscheck.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py', 'replay_target5.py'] + \
         ['lib/' + x for x in sorted(os.listdir(Z5 + 'lib')) if x.endswith('.py') and x not in ('zfast_provider.py', 'gen_target5.py')]:
    shutil.copyfile(Z5 + f, Z6 + f)
    if sha(Z5 + f) != sha(Z6 + f): raise RuntimeError(f'copy mismatch {f}')
# 2 provider (new source, same module name)
shutil.copyfile(SRC + 'zfast_provider.py', Z6 + 'lib/zfast_provider.py')

# 3 generator: one added DIAGNOSTIC stage after gen_done (the generator is untrusted; the stage writes no certificate)
g = open(Z5 + 'lib/gen_target5.py').read()
g = rep(g, '''log(stage='gen_done', certificates=len(done), np_certificates=nnp, np_intervals=len(ivs), measurements=len(MEAS), meas_seconds=round(TM[0], 2))
print('DONE', flush=True)''', '''log(stage='gen_done', certificates=len(done), np_certificates=nnp, np_intervals=len(ivs), measurements=len(MEAS), meas_seconds=round(TM[0], 2))
# atlas_v5z6 (THEORY_V5Z6.md): the Turing grid from THIS process's single zfast session (diagnostic; counted by scan_turing5.py recount)
if os.environ.get('ZFAST_TURING_GRID'):
    import zfast_provider as ZP
    TGS = json.loads(os.environ['ZFAST_TURING_GRID']); ts = time.time()
    tg = ZP.turing_grid(T0, TGS['outdir'], TGS['u0'], TGS['step'], TGS['n'])
    log(stage='turing_grid', spec=TGS, wall=round(time.time() - ts, 2), **tg)
print('DONE', flush=True)''')
open(Z6 + 'lib/gen_target5.py', 'w').write(g)

# 4 driver
d = open(Z5 + 'atlas_v5.py').read()
d = rep(d, '''                    explicit; the span (+0.02) must lie inside [centre - H, centre + H] before anything is computed."""''',
'''                    explicit; the span (+0.02) must lie inside [centre - H, centre + H] before anything is computed.

atlas_v5z6 (THEORY_V5Z6.md, RESULTS_M9): libzfast.v14 (sessions bit-identical to v13b at equal decomposition D = zfast_session.threads),
  ZFAST_WORKERS OS threads (output-free; recorded), per-role checkpoints in wide mode (RUN/zfast_ckpt_gen.txt, RUN/zfast_ckpt_replay.txt;
  the replay never reads the generator's), the replay's D from pieces.json;
  --turing-grid : the generator's session also covers [lo - 40, hi + 40] and saves the scan_turing5 grid in RUN/turing_grid (diagnostic);
  --resume      : continue a run whose generator (or replay) died while its session was being built: only while zs.json does not exist
                  and certs/ is empty (resp. replay_check/replay_check.json does not exist); earlier logs/dirs are RENAMED *.attemptN
                  (never deleted); the session resumes from its checkpoint, bit-identically.
  The replay of record is the driver's stage 3 (a fresh process, replay_target5.py byte copy); v5z6 runs no second replay."""''')
d = rep(d, "raise SystemExit('atlas_v5z5: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "raise SystemExit('atlas_v5z6: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
d = rep(d, "Z_PROVIDER = 'zfast libzfast.v13b, provider v5z5 (configurable recorded session, THEORY_V5Z5); model5 fixed-precision N_win (v5z4)'",
        "Z_PROVIDER = 'zfast libzfast.v14 (= v13b bit-identically at equal D), provider v5z6 (THEORY_V5Z6); model5 fixed-precision N_win (v5z4)'")
d = rep(d, "            'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'PYTHONHASHSEED')",
        "            'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'PYTHONHASHSEED', 'ZFAST_WORKERS', 'ZFAST_CKPT', 'ZFAST_TURING_GRID',\n"
        "            'ZFAST14_GENERIC_KERNEL', 'ZFAST14_TEST_EXIT_AFTER')")
d = rep(d, '''    e = {'ZFAST_H': repr(zs['H']), 'ZFAST_DELTA': repr(zs['Delta']), 'ZFAST_K': str(zs['K']), 'ZFAST_J': str(zs['J']),
         'ZFAST_STRICT': '1' if zs['strict'] else '0'}''', '''    e = {'ZFAST_H': repr(zs['H']), 'ZFAST_DELTA': repr(zs['Delta']), 'ZFAST_K': str(zs['K']), 'ZFAST_J': str(zs['J']),
         'ZFAST_STRICT': '1' if zs['strict'] else '0', 'ZFAST_THREADS': str(zs['threads'])}      # v5z6: D from the record''')
d = rep(d, '''    ap.add_argument('--zfast-delta', type=float); ap.add_argument('--zfast-k', type=int, default=18); ap.add_argument('--zfast-j', type=int, default=12)
    a = ap.parse_args(); t_start = time.time()''', '''    ap.add_argument('--zfast-delta', type=float); ap.add_argument('--zfast-k', type=int, default=18); ap.add_argument('--zfast-j', type=int, default=12)
    ap.add_argument('--turing-grid', action='store_true'); ap.add_argument('--resume', action='store_true')
    a = ap.parse_args(); t_start = time.time()
    for k in ('ZFAST_CKPT', 'ZFAST_TURING_GRID'): os.environ.pop(k, None)      # v5z6: role-specific, set below per child only
    if a.turing_grid and not a.wide: raise SystemExit('--turing-grid needs --wide')''')
d = rep(d, '''        ZSESS = dict(mode='wide', center=repr(float(c)), H=float(a.zfast_h), Delta=float(a.zfast_delta), K=a.zfast_k, J=a.zfast_j, strict=True,
                     threads=gen_threads, z_span=span)''', '''        ZSESS = dict(mode='wide', center=repr(float(c)), H=float(a.zfast_h), Delta=float(a.zfast_delta), K=a.zfast_k, J=a.zfast_j, strict=True,
                     threads=gen_threads, z_span=span)
        ZSESS.update(lib='v14', gen_workers=int(os.environ.get('ZFAST_WORKERS') or gen_threads))
        if a.turing_grid:
            TG = dict(u0=float(ulo) - 40.0, step=0.004, n=int(round((float(uhi) - float(ulo) + 80.0) / 0.004)) + 1)
            gend = TG['u0'] + (TG['n'] - 1) * TG['step']
            if not (c - a.zfast_h <= TG['u0'] and gend <= c + a.zfast_h):
                raise SystemExit(f'--turing-grid: grid [{TG["u0"]}, {gend}] is not inside the session [{c} - {a.zfast_h}, {c} + {a.zfast_h}]')
            ZSESS['turing_grid'] = TG''')
d = rep(d, '''    env = child_env(os.environ, ZSESS, PYTHONDONTWRITEBYTECODE='1', EPS='', CSTEP=os.environ.get('CSTEP', '0.005'), CND=os.environ.get('CND', '10'))
    done = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))
    if not done:
        if any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')): raise RuntimeError('v5z never deletes: use a fresh --name')''',
'''    v6 = {}
    if a.wide:
        v6['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_gen.txt')
        if ZSESS.get('turing_grid'): v6['ZFAST_TURING_GRID'] = json.dumps(dict(ZSESS['turing_grid'], outdir=str(RUN / 'turing_grid')))
    env = child_env(os.environ, ZSESS, PYTHONDONTWRITEBYTECODE='1', EPS='', CSTEP=os.environ.get('CSTEP', '0.005'), CND=os.environ.get('CND', '10'), **v6)
    done = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))
    if not done:
        if any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')):
            if not (a.resume and a.wide and not (RUN / 'zs.json').exists() and not (RUN / 'turing_grid').exists()
                    and not any((RUN / 'certs').glob('*')) and not (RUN / 'certs_np').exists()):
                raise RuntimeError('v5z never deletes: use a fresh --name (--resume only while the generator session is being built)')
            k = 1
            while any((RUN / f'{f}.attempt{k}').exists() for f in ('gen.log', 'gen.jsonl')): k += 1
            for f in ('gen.log', 'gen.jsonl'):
                if (RUN / f).exists(): (RUN / f).rename(RUN / f'{f}.attempt{k}')
            log(stage='resume_generator', attempt=k, ckpt=v6.get('ZFAST_CKPT'))''')
d = rep(d, '''    r = guarded([PY, '-u', '-B', str(V4 / 'replay_target5.py'), str(RUN)], V4, RUN / 'replay_target.log', env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    log(stage='replay_target', **r)''', '''    renv = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if a.wide: renv['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_replay.txt')         # the replay's own checkpoint, never the generator's
    if (RUN / 'replay_check' / 'replay_check.json').exists() and a.resume: r = dict(resumed=True, seconds=None, peak_gb=0)
    else:
        if (RUN / 'replay_check').exists():
            if not a.resume: raise RuntimeError('replay_check exists: use --resume (v5z never deletes)')
            k = 1
            while (RUN / f'replay_check.attempt{k}').exists(): k += 1
            (RUN / 'replay_check').rename(RUN / f'replay_check.attempt{k}')
            if (RUN / 'replay_target.log').exists(): (RUN / 'replay_target.log').rename(RUN / f'replay_target.log.attempt{k}')
            log(stage='resume_replay', attempt=k, ckpt=renv.get('ZFAST_CKPT'))
        r = guarded([PY, '-u', '-B', str(V4 / 'replay_target5.py'), str(RUN)], V4, RUN / 'replay_target.log', env=renv)
    log(stage='replay_target', **r)''')
d = rep(d, "                replay=dict(seconds=r['seconds'], peak_gb=r['peak_gb'], min_candidate_lower=rc.get('min_candidate_lower')),",
        "                replay=dict(seconds=r['seconds'], peak_gb=r['peak_gb'], min_candidate_lower=rc.get('min_candidate_lower')),\n"
        "                sessions_per_window=2 if a.wide else None, turing_grid=next((x for x in gl if x['stage'] == 'turing_grid'), None),")
if 'assert ' in d.replace("'assert", ''): raise RuntimeError('driver contains an assert')
open(Z6 + 'atlas_v5.py', 'w').write(d)

# 5 run script
open(Z6 + 'run_wide6.sh', 'w').write('''#!/bin/bash
# run_wide6.sh NAME T0 TLO THI H DELTA [CENTER] : v5z6 two-session wide window (THEORY_V5Z6.md):
#   1 pipeline: generator session (+ Turing grid in the same session) and the replay of record (driver stage 3, fresh process);
#   2 scan_turing5.py recount on RUN/turing_grid (the unchanged tool of record; no zfast call);
#   3 engine/regress_v1 turing_gate check (required gate, amendment A6).
# nice 19; ZFAST_THREADS = decomposition D (recorded), ZFAST_WORKERS = OS threads (output-free); RESUME=1 passes --resume.  Never deletes.
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z6; cd $Z; mkdir -p runs
N=$1; T0=$2; LO=$3; HI=$4; HH=$5; DD=$6; C=$7
export ZFAST_THREADS=${ZFAST_THREADS:-2}; export ZFAST_WORKERS=${ZFAST_WORKERS:-$ZFAST_THREADS}; export V4_LIM_GB=${V4_LIM_GB:-1.0}
unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT ZFAST_CKPT ZFAST_TURING_GRID
RA=""; [ "$RESUME" = "1" ] && RA="--resume"
[ -e runs/w$T0/$N ] && [ -z "$RA" ] && { echo "exists runs/w$T0/$N"; exit 1; }
CA=""; [ -n "$C" ] && CA="--zfast-center $C"
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T0 $LO $HI --name $N --zs-step 0.005 --gen-timeout 1209600 --wide --zfast-h $HH --zfast-delta $DD $CA --turing-grid $RA >> runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s D=$ZFAST_THREADS W=$ZFAST_WORKERS" >> runs/v5z6.log
R=runs/w$T0/$N; ULO=$($P -c "import json; print(json.load(open('$R/pieces.json'))['target'][0])"); UHI=$($P -c "import json; print(json.load(open('$R/pieces.json'))['target'][1])")
s=$(date +%s); nice -n 19 $P -B ../tools/scan_turing5.py recount $R/turing_grid $R/turing_recount.json --points $ULO,$UHI --win $ULO,$UHI > $R/turing_recount.log 2>&1; rc3=$?
echo "$N turing recount rc=$rc3 wall=$(( $(date +%s) - s ))s $(tail -1 $R/turing_recount.log | cut -c1-300)" >> runs/v5z6.log
( cd /Users/kiosk/atlas_mark2 && $P -B -m engine.regress_v1.turing_gate check $Z/$R $Z/$R/turing_recount.json > $Z/$R/turing_gate.log 2>&1 ); rc4=$?
echo "$N turing gate rc=$rc4 $(tail -1 $R/turing_gate.log)" >> runs/v5z6.log
echo "$N done" >> runs/v5z6.log
''')
os.chmod(Z6 + 'run_wide6.sh', 0o755)

# 6 theory note
open(Z6 + 'THEORY_V5Z6.md', 'w').write('''# atlas_v5z6 = atlas_v5z5 on libzfast.v14, two sessions per wide window (2026-11-01; OPTIMIZE_M9 / RESULTS_M9)

**Why.** At 10²⁵ a v5z5 window costs 4 O(√T) session passes (generator, inline replay, independent replay, Turing scan), ≈ 22 h at 4
threads (RESULTS_M8 §5). v5z6 needs 2, and each pass is faster (libzfast.v14).

**What changed. No inequality, model, verifier, LP, row, replay or tiling code changed** (byte copies; V5Z6_FREEZE.sha256).
- `lib/zfast_provider.py`: libzfast.v14 (sha-pinned). Its sessions are **bit-identical** to libzfast.v13b's at equal decomposition
  D (= ZFAST_THREADS = pieces.json `zfast_session.threads`): same work items (bucket ranges from v13b's split_ranges), same per-item
  arithmetic (a kernel performing the same IEEE operations in the same order; exact integer phase updates), same per-bucket merge
  order. Only who computes an item and when changes (ZFAST_WORKERS threads, longest item first, no per-bucket barrier). Optional
  checkpoint (ZFAST_CKPT, strict mode only): every finished item is stored exactly (arb_dump_str, raw mag fields, SHA-256 per line;
  header = every parameter defining the items); resume loads matching valid lines, merges unchanged, so a resumed session equals an
  uninterrupted one. `turing_grid()` saves scan_turing5's grid format from the process's session (diagnostic only).
- `atlas_v5.py`: `--turing-grid`, `--resume`; the replay's D comes from pieces.json (child env); role-specific checkpoints; one replay
  (the driver's stage 3, a fresh process running the byte-copied replay_target5.py — the same program and isolation as v5z5's
  "independent replay", which v5z5 ran a second time).
- `lib/gen_target5.py`: after `gen_done`, the Turing grid stage (untrusted generator; writes no certificate).
- `run_wide6.sh`: pipeline → `scan_turing5.py recount` (the unchanged tool of record) → `turing_gate check` (required, A6).

**Soundness.** Unchanged from v5z5 (THEORY_V5Z5): every Z value and row is a ball from a session whose validity range contains the point;
THEORY_M5b Lemma M1c holds for every H, Δ (production H = 91, Δ = 0.008: |h′|X_b ≤ 0.364, as scan4_1e22). The certificates never
contain or depend on the Turing count, which is a separate-method diagnostic made a required gate (A6).

**Review flags.** (1) v14's kernel and scheduler are new trusted code; bit-identity is confirmed mechanically (RESULTS_M9) but the code
needs review2-style review. (2) The checkpoint load path is a new input path into a session (protected by header equality and per-line
SHA-256; a resumed replay of record should be disclosed as such).

**Regression.** v5z6 with wide_1e22's frozen session parameters must regenerate it identically (certs, certs_np, zs.json,
gen_measurements.json, replay records): engine/regress_v1/v5z6_gate.py, PREDICTIONS_M9.
''')

# 7 freeze
files = ['atlas_v5.py', 'replay_target5.py', 'crosscheck.py', 'THEORY_V5Z6.md', 'VERIFY_ZS5.sha256', 'run_wide6.sh'] + \
        ['lib/' + x for x in sorted(os.listdir(Z6 + 'lib')) if x.endswith('.py')] + ['nzeros/arb_nzeros.py']
lines = [f'{sha(Z6 + f)}  {f}' for f in files]
for l in open(ZF + 'bin/SHA256.v14'):
    h, f = l.split()
    if f == 'libzfast.v14.dylib' or f.startswith('src_v14/'): lines.append(f'{h}  ../bin/{f}')
lines.append(f'{sha(ZF + "tools/make_v5z6.py")}  ../tools/make_v5z6.py')
lines.append(f'{sha(SRC + "zfast_provider.py")}  ../tools/v5z6_src/zfast_provider.py')
for l in lines:
    h, f = l.split(); p = os.path.normpath(Z6 + f)
    if sha(p) != h: raise RuntimeError(f'freeze sha mismatch {f}')
open(Z6 + 'V5Z6_FREEZE.sha256', 'w').write('\n'.join(lines) + '\n')
print('ok', len(lines), 'files frozen')
