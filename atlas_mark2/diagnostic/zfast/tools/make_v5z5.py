"""Builds atlas_v5z5/ from atlas_v5z4/ (new files only; v5z4 is never written).  PREDICTIONS_M7.md section 0, THEORY_V5Z5.md.
Byte copies of every v5z4 code file except: lib/zfast_provider.py (new source tools/v5z5_src/zfast_provider.py), atlas_v5.py and
replay_target5.py (scripted, counted replacements below), run scripts, THEORY_V5Z5.md.  Ends by writing V5Z5_FREEZE.sha256."""
import os, sys, shutil, hashlib
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
Z4 = ZF + 'atlas_v5z4/'; Z5 = ZF + 'atlas_v5z5/'; SRC = ZF + 'tools/v5z5_src/'
if os.path.exists(Z5): raise SystemExit(f'{Z5} exists: never overwrite (make a new version)')
os.makedirs(Z5 + 'lib'); os.makedirs(Z5 + 'nzeros'); os.makedirs(Z5 + 'runs')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rep(s, old, new, n=1):
    if s.count(old) != n: raise RuntimeError(f'replacement anchor found {s.count(old)} times (want {n}): {old[:80]!r}')
    return s.replace(old, new)


# 1 byte copies
for f in ['crosscheck.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py'] + ['lib/' + x for x in sorted(os.listdir(Z4 + 'lib')) if x.endswith('.py') and x != 'zfast_provider.py']:
    shutil.copyfile(Z4 + f, Z5 + f)
    if sha(Z4 + f) != sha(Z5 + f): raise RuntimeError(f'copy mismatch {f}')
# 2 provider (new source, same module name: the pinned verify_zs5.py imports `zfast_provider`)
shutil.copyfile(SRC + 'zfast_provider.py', Z5 + 'lib/zfast_provider.py')

# 3 driver
d = open(Z4 + 'atlas_v5.py').read()
d = rep(d, '''import argparse, json, os, re, shutil, subprocess, sys, time, hashlib, math
from pathlib import Path
''', '''import argparse, json, os, re, shutil, subprocess, sys, time, hashlib, math, platform
from pathlib import Path
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('atlas_v5z5: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')
''')
d = rep(d, '''Output runs/w{T0}/{NAME}/: pieces.json, zs.json, certs/, gen.jsonl, replay_check/, summary.json, drive.jsonl.  Exit 0 iff closed."""''',
'''Output runs/w{T0}/{NAME}/: pieces.json, zs.json, certs/, gen.jsonl, replay_check/, summary.json, drive.jsonl.  Exit 0 iff closed.

atlas_v5z5 (THEORY_V5Z5.md): the zfast session is configured explicitly and recorded.  pieces.json gets `zfast_session` (mode, centre,
H, Delta, K, J, strict, generator threads); drive.jsonl's start record gets `env` (every variable that can change an output).
  legacy (default): v5z4 behaviour exactly (H 4, Delta 0.15, K 18, J 12; centre from env ZFAST_CENTER as before; ZFAST_H/DELTA/K/J/STRICT
                    are removed from the child env);
  --wide          : one strict session for the whole run: centre = midpoint of the Z span (or --zfast-center), --zfast-h/--zfast-delta
                    explicit; the span (+0.02) must lie inside [centre - H, centre + H] before anything is computed."""''')
d = rep(d, '''LIM_GB = float(os.environ.get('V4_LIM_GB', '2.5')); H = 0.01
''', '''LIM_GB = float(os.environ.get('V4_LIM_GB', '2.5')); H = 0.01
Z_PROVIDER = 'zfast libzfast.v13b, provider v5z5 (configurable recorded session, THEORY_V5Z5); model5 fixed-precision N_win (v5z4)'
ENV_KEYS = ('ZFAST_CENTER', 'ZFAST_THREADS', 'ZFAST_H', 'ZFAST_DELTA', 'ZFAST_K', 'ZFAST_J', 'ZFAST_STRICT', 'CSTEP', 'CND', 'MINW_BINS',
            'ZS_REFINE', 'ZS_DIP', 'EPS', 'V4_LIM_GB', 'V4_TEST_SKIP_TIERS', 'V4_TEST_SPLIT', 'SECH_TABLE', 'OMP_NUM_THREADS',
            'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'PYTHONHASHSEED')
SESSION_KEYS = ('ZFAST_CENTER', 'ZFAST_H', 'ZFAST_DELTA', 'ZFAST_K', 'ZFAST_J', 'ZFAST_STRICT')
LEGACY = dict(H=4.0, Delta=0.15, K=18, J=12)


def env_record(env):
    import flint
    return dict({k: env.get(k) for k in ENV_KEYS}, python=sys.version.split()[0], flint=getattr(flint, '__version__', None),
                platform=platform.platform(), executable=sys.executable)


def session_env(zs):
    """child-process env entries for a zfast_session record (pieces.json)."""
    e = {'ZFAST_H': repr(zs['H']), 'ZFAST_DELTA': repr(zs['Delta']), 'ZFAST_K': str(zs['K']), 'ZFAST_J': str(zs['J']),
         'ZFAST_STRICT': '1' if zs['strict'] else '0'}
    if zs['center'] is not None: e['ZFAST_CENTER'] = zs['center']
    return e


def child_env(base, zs, **extra):
    e = dict(base)
    for k in SESSION_KEYS: e.pop(k, None)
    e.update(session_env(zs)); e.update(extra)
    return e
''')
d = rep(d, '''    ap.add_argument('--zs-step', type=float, default=0.005); ap.add_argument('--gen-timeout', type=float, default=7200)
    a = ap.parse_args(); t_start = time.time()''', '''    ap.add_argument('--zs-step', type=float, default=0.005); ap.add_argument('--gen-timeout', type=float, default=7200)
    ap.add_argument('--wide', action='store_true'); ap.add_argument('--zfast-center', type=float); ap.add_argument('--zfast-h', type=float)
    ap.add_argument('--zfast-delta', type=float); ap.add_argument('--zfast-k', type=int, default=18); ap.add_argument('--zfast-j', type=int, default=12)
    a = ap.parse_args(); t_start = time.time()
    if not a.wide and any(v is not None for v in (a.zfast_center, a.zfast_h, a.zfast_delta)):
        raise SystemExit('--zfast-center/--zfast-h/--zfast-delta need --wide (legacy mode is v5z4 exactly)')
    if a.wide and (a.zfast_h is None or a.zfast_delta is None): raise SystemExit('--wide needs explicit --zfast-h and --zfast-delta')''')
d = rep(d, '''    log(stage='start', args=vars(a), lim_gb=LIM_GB, lib_sha={f: sha(V4 / 'lib' / f) for f in GEN_LIB + ('verify_zs5.py', 'replay5.py')},
        driver_sha=sha(__file__), replay_target_sha=sha(V4 / 'replay_target5.py'))
    assert sha(V4 / 'lib' / 'verify_zs5.py') == VERIFY_ZS5_SHA
    # 1 pieces
    G = Grid(a.T0, a.grid); ulo, uhi, tnote = target_offsets(a.T0, a.tlo, a.thi, a.grid)
    k_lo, k_hi = hull_bins(G, ulo, uhi); e = G.edge''', '''    # 1 pieces (computed before the start record so that the session record can be logged and checked first)
    G = Grid(a.T0, a.grid); ulo, uhi, tnote = target_offsets(a.T0, a.tlo, a.thi, a.grid)
    k_lo, k_hi = hull_bins(G, ulo, uhi); e = G.edge
    wmb = round(a.wm / H); span = [e(k_lo - wmb), e(k_hi + wmb)]
    gen_threads = int(os.environ.get('ZFAST_THREADS', '2'))
    if a.wide:
        c = a.zfast_center if a.zfast_center is not None else (span[0] + span[1]) / 2
        if not (c - a.zfast_h <= span[0] - 0.02 and span[1] + 0.02 <= c + a.zfast_h):
            raise SystemExit(f'--wide: Z span {span} (+0.02) is not inside the session [{c} - {a.zfast_h}, {c} + {a.zfast_h}]')
        ZSESS = dict(mode='wide', center=repr(float(c)), H=float(a.zfast_h), Delta=float(a.zfast_delta), K=a.zfast_k, J=a.zfast_j, strict=True,
                     threads=gen_threads, z_span=span)
    else:
        ZSESS = dict(mode='legacy', center=os.environ.get('ZFAST_CENTER'), strict=False, threads=gen_threads, z_span=span, **LEGACY)
    log(stage='start', args=vars(a), lim_gb=LIM_GB, lib_sha={f: sha(V4 / 'lib' / f) for f in GEN_LIB + ('verify_zs5.py', 'replay5.py')},
        driver_sha=sha(__file__), replay_target_sha=sha(V4 / 'replay_target5.py'), env=env_record(os.environ), zfast_session=ZSESS)
    if sha(V4 / 'lib' / 'verify_zs5.py') != VERIFY_ZS5_SHA: raise RuntimeError('verify_zs5.py sha mismatch')''')
d = rep(d, '''zs_step=a.zs_step, zs_refine=a.zs_refine, pieces=pieces, z_provider='zfast libzfast.v13b, provider v5z3; model5 fixed-precision N_win (v5z4)')
    if not (RUN / 'pieces.json').exists(): json.dump(PJ, open(RUN / 'pieces.json', 'w'), indent=1)
    else: assert json.load(open(RUN / 'pieces.json')) == json.loads(json.dumps(PJ)), 'run dir has different pieces\'''',
'''zs_step=a.zs_step, zs_refine=a.zs_refine, pieces=pieces, z_provider=Z_PROVIDER, zfast_session=ZSESS)
    if not (RUN / 'pieces.json').exists(): json.dump(PJ, open(RUN / 'pieces.json', 'w'), indent=1)
    elif json.load(open(RUN / 'pieces.json')) != json.loads(json.dumps(PJ)): raise RuntimeError('run dir has different pieces')''')
d = rep(d, '''        else: assert sha(W / f) == sha(V4 / 'lib' / f)''', '''        elif sha(W / f) != sha(V4 / 'lib' / f): raise RuntimeError(f'work copy {f} differs from lib')''')
d = rep(d, '''    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', EPS='', CSTEP=os.environ.get('CSTEP', '0.005'), CND=os.environ.get('CND', '10'))''',
'''    env = child_env(os.environ, ZSESS, PYTHONDONTWRITEBYTECODE='1', EPS='', CSTEP=os.environ.get('CSTEP', '0.005'), CND=os.environ.get('CND', '10'))''')
d = rep(d, '''        assert not any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')), 'v5z never deletes: use a fresh --name\'''',
'''        if any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')): raise RuntimeError('v5z never deletes: use a fresh --name')''')
d = rep(d, '''                test_hooks={k: os.environ[k] for k in ('V4_TEST_SKIP_TIERS', 'V4_TEST_SPLIT') if os.environ.get(k)},''',
'''                test_hooks={k: os.environ[k] for k in ('V4_TEST_SKIP_TIERS', 'V4_TEST_SPLIT') if os.environ.get(k)}, zfast_session=ZSESS,''')
if 'assert ' in d.replace("'assert", ''): raise RuntimeError('driver still contains an assert')
open(Z5 + 'atlas_v5.py', 'w').write(d)

# 4 replay_target5
r = open(Z4 + 'replay_target5.py').read()
r = rep(r, '''import json, sys, os, shutil, hashlib, importlib.util, glob, time
''', '''import json, sys, os, shutil, hashlib, importlib.util, glob, time
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('atlas_v5z5: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')
''')
r = rep(r, '''Writes replay_check/replay_check.json; exit 0 iff everything passes."""''', '''Writes replay_check/replay_check.json; exit 0 iff everything passes.
atlas_v5z5: the zfast session of the replay process is configured from pieces.json's `zfast_session` record (centre, H, Delta, K, J, strict),
never from the caller's ZFAST_CENTER/ZFAST_H/...; the replay env is recorded in replay_check.json (`zfast_env`)."""''')
r = rep(r, '''    assert D.sha(R / 'verify_zs5.py') == D.VERIFY_ZS5_SHA
    P = json.load(open(RUN / 'pieces.json')); T0 = P['T0']; assert isinstance(T0, int) and P['format'] == 'atlas_v5'
    G = Grid(T0, P['grid']); e = G.edge
    tlo, thi, tnote = D.target_offsets(T0, P['target_input'][0], P['target_input'][1], P['grid']); assert [tlo, thi] == P['target']''',
'''    if D.sha(R / 'verify_zs5.py') != D.VERIFY_ZS5_SHA: raise RuntimeError('verify_zs5.py sha mismatch')
    P = json.load(open(RUN / 'pieces.json')); T0 = P['T0']
    if not (isinstance(T0, int) and P['format'] == 'atlas_v5'): raise RuntimeError('pieces.json is not atlas_v5 format')
    if 'zfast_session' not in P: raise RuntimeError('pieces.json has no zfast_session record (not a v5z5 run)')
    ZSESS = P['zfast_session']; RENV = D.child_env(os.environ, ZSESS, VERIFY_ZS5_SHA=D.VERIFY_ZS5_SHA, PYTHONDONTWRITEBYTECODE='1')
    G = Grid(T0, P['grid']); e = G.edge
    tlo, thi, tnote = D.target_offsets(T0, P['target_input'][0], P['target_input'][1], P['grid'])
    if [tlo, thi] != P['target']: raise RuntimeError('target offsets differ from pieces.json')''')
r = rep(r, '''                  env=dict(os.environ, VERIFY_ZS5_SHA=D.VERIFY_ZS5_SHA, PYTHONDONTWRITEBYTECODE='1')) if certs else''',
'''                  env=RENV) if certs else''')
r = rep(r, '''               claim_B=claimB,
               seconds=round(time.time() - t0, 2))''', '''               claim_B=claimB, zfast_session=ZSESS, zfast_env=D.env_record(RENV),
               seconds=round(time.time() - t0, 2))''')
if 'assert ' in r: raise RuntimeError('replay_target still contains an assert')
open(Z5 + 'replay_target5.py', 'w').write(r)

# 5 run scripts
open(Z5 + 'run_window.sh', 'w').write('''#!/bin/bash
# run_window.sh NAME T0 TLO THI STEP NLO NHI CENTER : v5z5 legacy-mode window (= v5z4 run_window.sh, own log runs/v5z5.log) + independent
# replay + optional crosscheck.  ZFAST_THREADS from the caller (recorded by the driver).  Never deletes (fresh NAME required).
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z5; cd $Z; mkdir -p runs
N=$1; T0=$2; LO=$3; HI=$4; ST=$5; NLO=$6; NHI=$7; export ZFAST_CENTER=$8; export ZFAST_THREADS=${ZFAST_THREADS:-2}; unset PYTHONOPTIMIZE
[ -e runs/w$T0/$N ] && { echo "exists runs/w$T0/$N"; exit 1; }
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T0 $LO $HI --name $N --zs-step $ST --gen-timeout 21600 > runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s threads=$ZFAST_THREADS" >> runs/v5z5.log
s=$(date +%s); nice -n 19 $P -B replay_target5.py runs/w$T0/$N replay_check_independent > runs/w$T0/$N/replay_target_independent.log 2>&1; rc2=$?
echo "$N independent replay rc=$rc2 wall=$(( $(date +%s) - s ))s $(tail -1 runs/w$T0/$N/replay_target_independent.log)" >> runs/v5z5.log
if [ "$NLO" != "-" ]; then $P -B crosscheck.py runs/w$T0/$N $NLO $NHI >> runs/v5z5.log 2>&1; fi
echo "$N done" >> runs/v5z5.log
''')
open(Z5 + 'run_wide.sh', 'w').write('''#!/bin/bash
# run_wide.sh NAME T0 TLO THI H DELTA [CENTER] : v5z5 wide-session window (one strict zfast session per process; THEORY_V5Z5.md):
# pipeline (generator + replay) + independent replay, nice 19, driver footprint kill V4_LIM_GB (default 1.0 GB), threads ZFAST_THREADS.
# CENTER defaults to the midpoint of the Z span.  Never deletes (fresh NAME required).  Log runs/v5z5.log.
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z5; cd $Z; mkdir -p runs
N=$1; T0=$2; LO=$3; HI=$4; HH=$5; DD=$6; C=$7
export ZFAST_THREADS=${ZFAST_THREADS:-2}; export V4_LIM_GB=${V4_LIM_GB:-1.0}; unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT
[ -e runs/w$T0/$N ] && { echo "exists runs/w$T0/$N"; exit 1; }
CA=""; [ -n "$C" ] && CA="--zfast-center $C"
s=$(date +%s); nice -n 19 $P -u -B atlas_v5.py $T0 $LO $HI --name $N --zs-step 0.005 --gen-timeout 21600 --wide --zfast-h $HH --zfast-delta $DD $CA > runs/$N.out 2>&1; rc=$?
echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s threads=$ZFAST_THREADS" >> runs/v5z5.log
s=$(date +%s); nice -n 19 $P -B replay_target5.py runs/w$T0/$N replay_check_independent > runs/w$T0/$N/replay_target_independent.log 2>&1; rc2=$?
echo "$N independent replay rc=$rc2 wall=$(( $(date +%s) - s ))s $(tail -1 runs/w$T0/$N/replay_target_independent.log)" >> runs/v5z5.log
echo "$N done" >> runs/v5z5.log
''')
for f in ('run_window.sh', 'run_wide.sh'): os.chmod(Z5 + f, 0o755)

# 6 theory note
open(Z5 + 'THEORY_V5Z5.md', 'w').write('''# atlas_v5z5 = atlas_v5z4 with configurable, recorded zfast sessions (wide-session windows) (2026-11-01)

**Why.** At height T one zfast session costs an O(√T) moment pass (about 960 s at 10²² and 20,000 s at 10²⁴ on 2/1 threads) and then
milliseconds per point. v5z4 fixed the session half-width at H = 4, so a run covered a 2-unit target. A session of half-width H ≈ 61
costs the same pass (the 10²²–10²⁴ scans use exactly that), so one generator/replay process can serve a 100-unit target.

**What changed (the only trusted change is the provider's configuration; no inequality, model, verifier or tiling code changed).**
- `lib/zfast_provider.py`: H, Δ, K, J from env (defaults are v5z4's: 4, 0.15, 18, 12), centre rule unchanged in legacy mode.
  Strict mode (wide runs): the centre is required, a point outside [c − H, c + H] raises, a second session in one process raises.
  Explicit raises instead of asserts; refuses python -O.
- `atlas_v5.py`: `--wide --zfast-h H --zfast-delta Δ [--zfast-center c]`; the session record `zfast_session` goes into pieces.json,
  the full env (ZFAST_CENTER, ZFAST_THREADS, …) into drive.jsonl (regress_v1 finding F-A4); legacy mode strips ZFAST_H/Δ/K/J/STRICT
  from the child env so it is v5z4 exactly.
- `replay_target5.py`: the replay's session comes from pieces.json, never from the caller's env; recorded in replay_check.json.

**Soundness.** THEORY_M5 §1: every Z value and row is a ball from a session whose validity range contains the point; which session answers
is a matter of cost only. THEORY_M5b Lemma M1c: the Taylor remainder (|h′|X_b)^{K+1}/(K+1)!·e^{|h′|X_b} is a valid bound for complex h′
and any H, Δ, and is evaluated in Arb per block by libzfast.v13b (unchanged, sha 82489d1a…). With H = 61, Δ = 0.012, K = 18:
|h′|X_b ≤ 0.37, remainder ≈ 5·10⁻²⁶. The certificate claim, the verifier (verify_zs5.py sha 79ca5b16…) and the replay are unchanged.

**Regression.** Legacy mode must regenerate v5z4/v5z3 windows canonically identically (pieces.json may differ only in z_provider and the
new zfast_session record): engine/regress_v1/v5z5_gate.py, PREDICTIONS_M7 §1.
''')

# 7 freeze
files = ['atlas_v5.py', 'replay_target5.py', 'crosscheck.py', 'THEORY_V5Z5.md', 'VERIFY_ZS5.sha256', 'run_window.sh', 'run_wide.sh'] + \
        ['lib/' + x for x in sorted(os.listdir(Z5 + 'lib')) if x.endswith('.py')] + ['nzeros/arb_nzeros.py']
lines = [f'{sha(Z5 + f)}  {f}' for f in files]
for l in open(Z4 + 'V5Z4_FREEZE.sha256'):
    if l.split()[1].startswith('../bin/'): lines.append(l.rstrip('\n'))
lines.append(f'{sha(ZF + "tools/make_v5z5.py")}  ../tools/make_v5z5.py')
lines.append(f'{sha(SRC + "zfast_provider.py")}  ../tools/v5z5_src/zfast_provider.py')
for l in lines:
    h, f = l.split(); p = os.path.normpath(Z5 + f)
    if sha(p) != h: raise RuntimeError(f'freeze sha mismatch {f}')
open(Z5 + 'V5Z5_FREEZE.sha256', 'w').write('\n'.join(lines) + '\n')
print('ok', len(lines), 'files frozen')
