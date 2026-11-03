"""Builds atlas_v5za/ from atlas_v5z9/ (new files only; v5z9 is never written).  PREDICTIONS_M14 (review_v14c; libzfast.v14d).  Byte
copies of every v5z9 file except (counted replacements below):
  lib/zfast_provider.py  libzfast.v14d (sha-pinned; same ctypes API); lib='v14d'; hook prefixes add ZFAST14D_TEST; a refused checkpointed
                         session appends its reason to CKPT + '.refusals.jsonl' (CKPT-IO-ABORT banner on stderr); a session reporting
                         ckpt_write_errors > 0 raises (mn-C4); names v5za
  atlas_v5.py            hook prefixes; lib v14d; (mn-C4) a CKPT-IO-ABORT refusal of the generator or replay session -> stage ckpt_io_abort,
                         banner, exit 3; (mn-C3) --resume after the session build (outputs moved to RUN/gen_postbuild.attempt<k>/, never
                         deleted); the generator counts as finished only with gen_done AND (if requested) its turing_grid stage;
                         ckpt_sessions_gen records key_created / key_reused_new_header / lines_nul / ckpt_dir_synced; names v5za
  replay_target5.py      names v5za only
  run_wideA.sh (from run_wide9.sh: tree path, log name, stop on rc 3), THEORY_V5ZA.md (new).  Ends by writing V5ZA_FREEZE.sha256."""
import os, sys, shutil, hashlib
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
Z9 = ZF + 'atlas_v5z9/'; ZA = ZF + 'atlas_v5za/'
LIB = ZF + 'bin/libzfast.v14d.dylib'; LIB_SHA = 'e0ed15f3cd4d62f887ab62cf6f6af0be5f378d356e35663ef9bafd432c425b81'
OLD_LIB_SHA = '59883f5e2d83585b67c08a2e3816d180248cd760c705642f13b571b71ad37471'
if os.path.exists(ZA): raise SystemExit(f'{ZA} exists: never overwrite (make a new version)')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rep(s, old, new, n=1):
    if s.count(old) != n: raise RuntimeError(f'replacement anchor found {s.count(old)} times (want {n}): {old[:80]!r}')
    return s.replace(old, new)


if sha(LIB) != LIB_SHA: raise RuntimeError('libzfast.v14d sha mismatch')
for l in open(Z9 + 'V5Z9_FREEZE.sha256'):
    h, f = l.split()
    if sha(os.path.normpath(Z9 + f)) != h: raise RuntimeError(f'atlas_v5z9 differs from its freeze: {f}')
os.makedirs(ZA + 'lib'); os.makedirs(ZA + 'nzeros'); os.makedirs(ZA + 'runs')
COPY = ['crosscheck.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py'] + ['lib/' + x for x in sorted(os.listdir(Z9 + 'lib')) if x.endswith('.py') and x != 'zfast_provider.py']
for f in COPY:
    shutil.copyfile(Z9 + f, ZA + f)
    if sha(Z9 + f) != sha(ZA + f): raise RuntimeError(f'copy mismatch {f}')

HOOKS_OLD = "HOOK_PREFIXES = ('ZFAST14_TEST', 'ZFAST14B_TEST', 'ZFAST14C_TEST', 'ZFAST14_GENERIC_KERNEL')"
HOOKS_NEW = "HOOK_PREFIXES = ('ZFAST14_TEST', 'ZFAST14B_TEST', 'ZFAST14C_TEST', 'ZFAST14D_TEST', 'ZFAST14_GENERIC_KERNEL')"

# ---------------- provider ----------------
p = open(Z9 + 'lib/zfast_provider.py').read()
p = rep(p, '"""atlas_v5z9 Z / row provider (TRUSTED;', '''"""atlas_v5za Z / row provider (TRUSTED; PREDICTIONS_M14 / THEORY_V5ZA.md) = the v5z9 provider on libzfast.v14d (same ctypes API; exact
radius parse (MJ-C1), identical duplicates ignored, checkpoint I/O error => session aborted (CKPT-IO-ABORT)).  A refused checkpointed
session appends {t, pid, role, nonce, ckpt, lib_sha, error} to CKPT + '.refusals.jsonl' (read by the v5za driver); a session reporting
ckpt_write_errors > 0 raises.  Hook prefixes add ZFAST14D_TEST.  v5z9 docstring follows.
atlas_v5z9 Z / row provider (TRUSTED;''')
p = rep(p, "    raise SystemExit('atlas_v5z9: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "    raise SystemExit('atlas_v5za: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
p = rep(p, HOOKS_OLD, HOOKS_NEW)
p = rep(p, "raise SystemExit('atlas_v5z9 zfast_provider: a libzfast test-hook variable is set", "raise SystemExit('atlas_v5za zfast_provider: a libzfast test-hook variable is set")
p = rep(p, "LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v14c.dylib'\nLIB_SHA = '" + OLD_LIB_SHA + "'",
        f"LIBPATH = '{LIB}'\nLIB_SHA = '{LIB_SHA}'")
p = rep(p, "lib_sha=LIB_SHA, lib='v14c', workers=WORKERS", "lib_sha=LIB_SHA, lib='v14d', workers=WORKERS")
p = rep(p, """        if not s:
            _L.zfa14b_last_error(_BUF, 4096)
            raise RuntimeError('zfa14b_new refused the session: ' + _BUF.value.decode())""",
        """        if not s:
            _L.zfa14b_last_error(_BUF, 4096); err = _BUF.value.decode()
            if CKPT:          # v5za (review_v14c mn-C4): the refusal reason is recorded for the driver
                import time as _t
                try:
                    with open(CKPT + '.refusals.jsonl', 'a') as _f:
                        _f.write(json.dumps(dict(t=_t.time(), pid=os.getpid(), role=CK_ROLE, nonce=CK_NONCE, ckpt=CKPT, lib_sha=LIB_SHA, error=err)) + '\\n'); _f.flush(); os.fsync(_f.fileno())
                except OSError as ex:
                    print(f'zfast_provider: could not record the refusal ({ex})', file=sys.stderr, flush=True)
                if err.startswith('CKPT-IO-ABORT'):
                    print('zfast_provider: ==== CHECKPOINT I/O ERROR: SESSION ABORTED (CKPT-IO-ABORT) ====\\n' + err, file=sys.stderr, flush=True)
            raise RuntimeError('zfa14b_new refused the session: ' + err)""")
p = rep(p, """            if info.get('ckpt_write_errors'): print(f'zfast_provider WARNING: {info["ckpt_write_errors"]} checkpoint write error(s); this session is NOT resumable', file=sys.stderr, flush=True)""",
        """            if info.get('ckpt_write_errors'): raise RuntimeError(f'zfast_provider: CKPT-IO-ABORT: {info["ckpt_write_errors"]} checkpoint write error(s) in a returned session (v14d aborts on any; refusing)')""")
p = rep(p, "rec = dict(tool='atlas_v5z9 zfast_provider.turing_grid", "rec = dict(tool='atlas_v5za zfast_provider.turing_grid")
if 'assert ' in p: raise RuntimeError('provider contains an assert')
if 'v14c.dylib' in p: raise RuntimeError('provider still names libzfast.v14c')
open(ZA + 'lib/zfast_provider.py', 'w').write(p)

# ---------------- driver ----------------
d = open(Z9 + 'atlas_v5.py').read()
d = rep(d, "raise SystemExit('atlas_v5z9: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "raise SystemExit('atlas_v5za: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
d = rep(d, HOOKS_OLD, HOOKS_NEW)
d = rep(d, "raise SystemExit('atlas_v5z9: refusing to start with a libzfast test-hook variable set", "raise SystemExit('atlas_v5za: refusing to start with a libzfast test-hook variable set")
d = rep(d, "  recomputes ZFAST_CKPT_VERIFY = 64 loaded items on resume by default (mn7; the replay stays 8).\"\"\"",
        "  recomputes ZFAST_CKPT_VERIFY = 64 loaded items on resume by default (mn7; the replay stays 8).\n"
        "atlas_v5za (PREDICTIONS_M14, THEORY_V5ZA.md): libzfast.v14d.  (mn-C4) a checkpoint I/O error aborts the zfast session; the driver then\n"
        "  logs stage ckpt_io_abort, prints a banner and exits 3 (fix the cause, then --resume).  (mn-C3) --resume also after the generator's\n"
        "  session build: while the replay has not started, the run's generator checkpoint and nonce exist and the generator sidecar holds a\n"
        "  gen-role record of this nonce, every generator output is MOVED to RUN/gen_postbuild.attempt<k>/ and the generator re-runs on the\n"
        "  complete checkpoint (same nonce and key).  The generator counts as finished only with gen_done and, if requested, its turing_grid.\"\"\"")
d = rep(d, "Z_PROVIDER = 'zfast libzfast.v14c (= v14 = v13b bit-identically at equal D; checkpoint v3), provider v5z9 (THEORY_V5Z9); model5 fixed-precision N_win (v5z4)'",
        "Z_PROVIDER = 'zfast libzfast.v14d (= v14 = v13b bit-identically at equal D; checkpoint v3), provider v5za (THEORY_V5ZA); model5 fixed-precision N_win (v5z4)'")
d = rep(d, "        ZSESS.update(lib='v14c')       # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS); v5z9: libzfast.v14c",
        "        ZSESS.update(lib='v14d')       # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS); v5za: libzfast.v14d")
# helpers (module level, before main)
d = rep(d, "def main():\n", '''POSTBUILD = ('zs.json', 'certs', 'certs_np', 'gen_measurements.json', 'turing_grid')     # v5za (mn-C3): generator outputs after its session build


def gen_finished(RUN, want_tg):
    """v5za: the generator finished = gen_done AND (if a Turing grid was requested) its turing_grid stage (gen_done is logged before it)."""
    if not (RUN / 'gen.jsonl').exists(): return False
    st = {json.loads(l).get('stage') for l in open(RUN / 'gen.jsonl') if l.strip()}
    return 'gen_done' in st and (not want_tg or 'turing_grid' in st)


def io_abort(ckpt, t_since, logf=None):
    """v5za (mn-C4): the CKPT-IO-ABORT refusal recorded by this attempt's zfast session (refusal sidecar; the process log as fallback)."""
    p = Path(str(ckpt) + '.refusals.jsonl')
    if p.exists():
        for l in open(p):
            try: x = json.loads(l)
            except ValueError: continue
            if x.get('t', 0) >= t_since and str(x.get('error', '')).startswith('CKPT-IO-ABORT'): return x['error']
    if logf is not None and Path(logf).exists():
        tail = open(logf, errors='replace').read()[-20000:]
        if 'CKPT-IO-ABORT' in tail: return tail[tail.rindex('CKPT-IO-ABORT'):][:600]
    return None


def io_abort_exit(log, RUN, role, err):
    log(stage='ckpt_io_abort', role=role, error=err)
    print('\\n==== ATLAS v5za: CHECKPOINT I/O ERROR, zfast SESSION ABORTED (CKPT-IO-ABORT), role ' + role + ' ====\\n' + err +
          f'\\nThe checkpoint {RUN}/zfast_ckpt_{role}.txt is valid up to the error.  Fix the cause (e.g. free disk space), then re-run the\\n'
          'same command with --resume (run_wideA.sh: RESUME=1).  Nothing was deleted.\\n', file=sys.stderr, flush=True)
    sys.exit(3)


def main():
''')
d = rep(d, """    done = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))
    if not done:
        if any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')):
            if not (a.resume and a.wide and not (RUN / 'zs.json').exists() and not (RUN / 'turing_grid').exists()
                    and not any((RUN / 'certs').glob('*')) and not (RUN / 'certs_np').exists()):
                raise RuntimeError('v5z never deletes: use a fresh --name (--resume only while the generator session is being built)')
            k = 1
            while any((RUN / f'{f}.attempt{k}').exists() for f in ('gen.log', 'gen.jsonl')): k += 1
            for f in ('gen.log', 'gen.jsonl'):
                if (RUN / f).exists(): (RUN / f).rename(RUN / f'{f}.attempt{k}')
            log(stage='resume_generator', attempt=k, ckpt=v6.get('ZFAST_CKPT'))
        g = guarded([PY, '-u', '-B', 'gen_target5.py', str(RUN)], W, RUN / 'gen.log', env=env, timeout=a.gen_timeout)
    else: g = dict(resumed=True)
    log(stage='generator', **g)""",
"""    want_tg = bool(ZSESS.get('turing_grid'))
    done = gen_finished(RUN, want_tg)
    if not done:
        post = [f for f in POSTBUILD if (RUN / f).exists() and (f != 'certs' or any((RUN / 'certs').glob('*')))]
        if post:      # v5za (review_v14c mn-C3): the generator died after its session build
            why = None
            if not (a.resume and a.wide): why = 'the generator died after its session build: re-run with --resume (wide runs only)'
            elif (RUN / 'replay_check').exists() or (RUN / 'zfast_ckpt_replay.txt').exists(): why = 'the replay has already started'
            elif not (RUN / 'zfast_ckpt_gen.txt').exists(): why = 'no generator checkpoint'
            else:
                sc = RUN / 'zfast_ckpt_gen.txt.sessions.jsonl'
                recs = [json.loads(l) for l in open(sc) if l.strip()] if sc.exists() else []
                if not any(x.get('role') == 'gen' and x.get('nonce') == nonce for x in recs): why = 'no generator session record of this run nonce (zfast_ckpt_gen.txt.sessions.jsonl)'
            if why: raise RuntimeError(f'v5z never deletes: {why}; otherwise use a fresh --name (generator outputs present: {post})')
            k = 1
            while (RUN / f'gen_postbuild.attempt{k}').exists(): k += 1
            dk = RUN / f'gen_postbuild.attempt{k}'; dk.mkdir()
            moved = [f for f in POSTBUILD + ('gen.log', 'gen.jsonl') if (RUN / f).exists()]
            for f in moved: (RUN / f).rename(dk / f)
            (dk / 'README.txt').write_text(f'atlas_v5za --resume after the generator session build (review_v14c mn-C3): the outputs of the interrupted generator attempt, moved here\\n'
                                           f'(never deleted) before the generator re-ran on the complete checkpoint {RUN}/zfast_ckpt_gen.txt (same nonce and key). Not used by any later stage.\\n')
            log(stage='resume_generator_postbuild', attempt=k, moved=moved, ckpt=v6.get('ZFAST_CKPT'))
        elif any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')):
            if not (a.resume and a.wide):
                raise RuntimeError('v5z never deletes: use a fresh --name (--resume only while the generator session is being built)')
            k = 1
            while any((RUN / f'{f}.attempt{k}').exists() for f in ('gen.log', 'gen.jsonl')): k += 1
            for f in ('gen.log', 'gen.jsonl'):
                if (RUN / f).exists(): (RUN / f).rename(RUN / f'{f}.attempt{k}')
            log(stage='resume_generator', attempt=k, ckpt=v6.get('ZFAST_CKPT'))
        t_gen = time.time()
        g = guarded([PY, '-u', '-B', 'gen_target5.py', str(RUN)], W, RUN / 'gen.log', env=env, timeout=a.gen_timeout)
        if a.wide and g.get('rc') != 0:
            err = io_abort(RUN / 'zfast_ckpt_gen.txt', t_gen - 1, RUN / 'gen.log')
            if err: log(stage='generator', **g); io_abort_exit(log, RUN, 'gen', err)
    else: g = dict(resumed=True)
    log(stage='generator', **g)""")
d = rep(d, "('items', 'items_loaded', 'verified', 'lines_rejected', 'lines_duplicate', 'lines_written', 'ckpt_write_errors', 'created')})",
        "('items', 'items_loaded', 'verified', 'lines_rejected', 'lines_duplicate', 'lines_written', 'ckpt_write_errors', 'created',\n"
        "                    'key_created', 'key_reused_new_header', 'lines_nul', 'ckpt_dir_synced')})")
d = rep(d, "    gen_ok = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))",
        "    gen_ok = gen_finished(RUN, want_tg)        # v5za: gen_done and (if requested) the turing_grid stage")
d = rep(d, """        r = guarded([PY, '-u', '-B', str(V4 / 'replay_target5.py'), str(RUN)], V4, RUN / 'replay_target.log', env=renv)
    log(stage='replay_target', **r)""",
"""        t_rep = time.time()
        r = guarded([PY, '-u', '-B', str(V4 / 'replay_target5.py'), str(RUN)], V4, RUN / 'replay_target.log', env=renv)
        if a.wide:
            err = io_abort(RUN / 'zfast_ckpt_replay.txt', t_rep - 1)
            if err: log(stage='replay_target', **r); io_abort_exit(log, RUN, 'replay', err)
    log(stage='replay_target', **r)""")
if 'assert ' in d: raise RuntimeError('driver contains an assert')
open(ZA + 'atlas_v5.py', 'w').write(d)

# ---------------- replay_target ----------------
r = open(Z9 + 'replay_target5.py').read()
r = rep(r, "    raise SystemExit('atlas_v5z9: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "    raise SystemExit('atlas_v5za: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
open(ZA + 'replay_target5.py', 'w').write(r)

# ---------------- run script ----------------
w = open(Z9 + 'run_wide9.sh').read()
w = rep(w, "# run_wide9.sh NAME T0 TLO THI H DELTA [CENTER] : v5z9 (= v5z8 on libzfast.v14c, checkpoint v3; THEORY_V5Z9) two-session wide window:",
        "# run_wideA.sh NAME T0 TLO THI H DELTA [CENTER] : v5za (= v5z9 on libzfast.v14d; THEORY_V5ZA) two-session wide window.  Pipeline rc 3 =\n"
        "#   CKPT-IO-ABORT (checkpoint I/O error): the script STOPS (no recount / gate); fix the cause and re-run with RESUME=1.\n"
        "# v5z9 header follows:")
w = rep(w, "Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z9;", "Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5za;")
w = rep(w, "runs/v5z9.log", "runs/v5za.log", 4)
w = rep(w, """echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s D=$ZFAST_THREADS W=$ZFAST_WORKERS" >> runs/v5za.log""",
        """echo "$N pipeline rc=$rc wall=$(( $(date +%s) - s ))s D=$ZFAST_THREADS W=$ZFAST_WORKERS" >> runs/v5za.log
if [ "$rc" = "3" ]; then echo "$N STOPPED: CKPT-IO-ABORT (checkpoint I/O error; see runs/$N.out). Fix the cause, then RESUME=1 $0 $*" | tee -a runs/v5za.log >&2; exit 3; fi""")
open(ZA + 'run_wideA.sh', 'w').write(w); os.chmod(ZA + 'run_wideA.sh', 0o755)

open(ZA + 'THEORY_V5ZA.md', 'w').write('''# atlas_v5za = atlas_v5z9 on libzfast.v14d (PREDICTIONS_M14, review_v14c)

**What changed.** Every file is a byte copy of atlas_v5z9 except `lib/zfast_provider.py`, `atlas_v5.py` and `replay_target5.py`
(counted replacements in `tools/make_v5za.py`), plus `run_wideA.sh`. THEORY_V5Z6 to THEORY_V5Z9 still apply. Certificate content is
unchanged.

**The engine.** libzfast.v14d's compute path is v14's (= v13b at equal D) byte for byte; only the checkpoint layer
(`zfast_sched14d.inc`) changed. Checkpoint format v3 as in v14c, with:
- **MJ-C1.** Honest balls whose radius mantissa has 30 bits now load (exact radius construction); v14c refused them, which would have
  made a 10^28 checkpoint unresumable.
- **mn-C1.** A byte-identical copy of an authentic line is ignored and counted (`lines_duplicate`); a conflicting duplicate refuses.
- **mn-C4 (abort policy).** Any checkpoint write or fsync error aborts the zfast session (`CKPT-IO-ABORT`). The checkpoint stays valid up
  to the error. The provider records the reason in `<ckpt>.refusals.jsonl`; the driver logs `stage=ckpt_io_abort`, prints a banner and
  exits 3; `run_wideA.sh` stops. Recovery: fix the cause (e.g. free disk), then `RESUME=1 run_wideA.sh <same args>`. Chosen over
  "continue unprotected" because days of unprotected compute are the failure the checkpoint exists to prevent; the abort costs at most
  the items in flight.
- **mn-C3 (post-build resume).** `--resume` also works after the generator's session build (zs.json, certs, Turing grid ...): while the
  replay has not started, the generator checkpoint and the run nonce exist and the generator sidecar holds a gen-role record of this
  nonce, the interrupted attempt's outputs are MOVED to `RUN/gen_postbuild.attempt<k>/` (never deleted) and the generator re-runs on the
  complete checkpoint with the same nonce and key (generator verify 64). The generator counts as finished only with `gen_done` and, if
  requested, its `turing_grid` stage (gen_done is logged before the grid). All library refusals are unchanged.
- **Nits.** FIFO/non-regular key or checkpoint path refused (no hang); NUL bytes never authenticated; the header must match byte for
  byte; the directory of a new checkpoint is fsynced.

**Operational (review_v14c section 3).** Keep macOS automatic and security updates off and run no `brew` command during a multi-day
window (any OS or library change refuses a resume by design); run on this Mac only. `V4_LIM_GB` (default 1.0 in run_wideA.sh) kills a
stage that exceeds it; after mn-C3 such a kill is resumable, but set it with margin for the 10^28 certificate stage.

Do not delete `ckpt_keys/`. Keys are not certificate inputs; losing them costs only recomputation.
''')

files = ['atlas_v5.py', 'replay_target5.py', 'crosscheck.py', 'THEORY_V5ZA.md', 'VERIFY_ZS5.sha256', 'run_wideA.sh'] + \
        ['lib/' + x for x in sorted(os.listdir(ZA + 'lib')) if x.endswith('.py')] + ['nzeros/arb_nzeros.py']
lines = [f'{sha(ZA + f)}  {f}' for f in files]
lines.append(f'{LIB_SHA}  ../bin/libzfast.v14d.dylib')
for l in open(ZF + 'bin/SHA256.v14d'):
    h, f = l.split()
    if f.startswith('src_v14d/'): lines.append(f'{h}  ../bin/{f}')
lines.append(f'{sha(ZF + "tools/make_v5za.py")}  ../tools/make_v5za.py')
for t in ('atlas_v5z6/THEORY_V5Z6.md', 'atlas_v5z7/THEORY_V5Z7.md', 'atlas_v5z8/THEORY_V5Z8.md', 'atlas_v5z9/THEORY_V5Z9.md'): lines.append(f'{sha(ZF + t)}  ../{t}')
for l in lines:
    h, f = l.split(); p_ = os.path.normpath(ZA + f)
    if sha(p_) != h: raise RuntimeError(f'freeze sha mismatch {f}')
open(ZA + 'V5ZA_FREEZE.sha256', 'w').write('\n'.join(lines) + '\n')
print('ok', len(lines), 'files frozen')
