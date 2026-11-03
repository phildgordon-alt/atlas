"""Builds atlas_v5z8/ from atlas_v5z7/ (new files only; v5z7 is never written).  PREDICTIONS_M12 (review_m10 M1, M2, m3, m7, m8 at the
pipeline level; libzfast.v14b).  Byte copies of every v5z7 file except (counted replacements below):
  lib/zfast_provider.py  libzfast.v14b (sha-pinned) via zfa14b_new: checkpoint role / per-run nonce / HMAC key file / resume verify sample
                         (env ZFAST_CKPT_ROLE, ZFAST_CKPT_NONCE, ZFAST_CKPT_KEY, ZFAST_CKPT_VERIFY, default 8); refusal reason raised; D in
                         [1, 16]; refuses to import with any test-hook variable set (m8); each checkpointed session appends one record to
                         CKPT.sessions.jsonl (role, nonce, pid, info incl. items_loaded / verified / lines_rejected / ckpt_write_errors).
  atlas_v5.py            refuses to start with a test-hook variable set and strips them from every child env (m8); creates the run nonce
                         once (RUN/zfast_ckpt_nonce.txt, O_EXCL) and per-role key paths in diagnostic/zfast/ckpt_keys/ (0700, outside
                         RUN); passes role gen to the generator and role replay to the replay of record (M2); logs both sidecars.
  replay_target5.py      replay_check.json gets `zfast_ckpt` (every session record of this replay: role, nonce, items_loaded, verified,
                         lines_rejected, ckpt_write_errors); `passed` additionally requires every record to be role replay with this run's
                         nonce (M2: the replay of record refuses / fails on any file it did not create).
  run_wide8.sh, THEORY_V5Z8.md (new).  Ends by writing V5Z8_FREEZE.sha256."""
import os, sys, shutil, hashlib
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
Z7 = ZF + 'atlas_v5z7/'; Z8 = ZF + 'atlas_v5z8/'
LIB = ZF + 'bin/libzfast.v14b.dylib'; LIB_SHA = 'd77bf28f21752e7c90c9990221a1ff702e4227b1038a2fb4106fb5d9eb9e7d52'
if os.path.exists(Z8): raise SystemExit(f'{Z8} exists: never overwrite (make a new version)')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rep(s, old, new, n=1):
    if s.count(old) != n: raise RuntimeError(f'replacement anchor found {s.count(old)} times (want {n}): {old[:80]!r}')
    return s.replace(old, new)


if sha(LIB) != LIB_SHA: raise RuntimeError('libzfast.v14b sha mismatch')
for l in open(Z7 + 'V5Z7_FREEZE.sha256'):
    h, f = l.split()
    if sha(os.path.normpath(Z7 + f)) != h: raise RuntimeError(f'atlas_v5z7 differs from its freeze: {f}')
os.makedirs(Z8 + 'lib'); os.makedirs(Z8 + 'nzeros'); os.makedirs(Z8 + 'runs')
COPY = ['crosscheck.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py'] + ['lib/' + x for x in sorted(os.listdir(Z7 + 'lib')) if x.endswith('.py') and x != 'zfast_provider.py']
for f in COPY:
    shutil.copyfile(Z7 + f, Z8 + f)
    if sha(Z7 + f) != sha(Z8 + f): raise RuntimeError(f'copy mismatch {f}')

HOOKS_PY = "HOOK_PREFIXES = ('ZFAST14_TEST', 'ZFAST14B_TEST', 'ZFAST14_GENERIC_KERNEL')"

# ---------------- provider ----------------
p = open(Z7 + 'lib/zfast_provider.py').read()
p = rep(p, '"""atlas_v5z6 Z / row provider (TRUSTED;', '''"""atlas_v5z8 Z / row provider (TRUSTED; PREDICTIONS_M12 / THEORY_V5Z8.md) = the v5z6 provider on libzfast.v14b (compute path = v14 =
v13b at equal D; hardened checkpoint).  Checkpoints (strict mode only) need ZFAST_CKPT_ROLE (gen | replay), ZFAST_CKPT_NONCE (the run's
32-hex nonce) and ZFAST_CKPT_KEY (HMAC key file, created by libzfast for a new checkpoint); ZFAST_CKPT_VERIFY (default 8, >= 1) loaded items
are recomputed on resume.  A refused session raises with libzfast's reason.  D (ZFAST_THREADS) must be in [1, 16].  Importing this module
with any test-hook variable (ZFAST14_TEST*, ZFAST14B_TEST*, ZFAST14_GENERIC_KERNEL) set raises (review_m10 m8).  Every checkpointed
session appends one JSON record to CKPT + '.sessions.jsonl' (read by the v5z8 driver and replay_target).  v5z6 docstring follows.
atlas_v5z6 Z / row provider (TRUSTED;''')
p = rep(p, "    raise SystemExit('atlas_v5z6: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "    raise SystemExit('atlas_v5z8: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')\n" + HOOKS_PY + "\n"
        "if any(k.startswith(HOOK_PREFIXES) for k in os.environ):\n"
        "    raise SystemExit('atlas_v5z8 zfast_provider: a libzfast test-hook variable is set (review_m10 m8): ' + ', '.join(k for k in os.environ if k.startswith(HOOK_PREFIXES)))")
p = rep(p, "LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v14.dylib'\nLIB_SHA = '7abaaa8aa0a913290cdb202a55d18c6c195130b20032614f3a60d07f0f10fa5b'",
        f"LIBPATH = '{LIB}'\nLIB_SHA = '{LIB_SHA}'")
p = rep(p, "CKPT = os.environ.get('ZFAST_CKPT') or ''\n",
        "CKPT = os.environ.get('ZFAST_CKPT') or ''\n"
        "CK_ROLE = os.environ.get('ZFAST_CKPT_ROLE') or ''; CK_NONCE = os.environ.get('ZFAST_CKPT_NONCE') or ''; CK_KEY = os.environ.get('ZFAST_CKPT_KEY') or ''\n"
        "CK_VERIFY = int(os.environ.get('ZFAST_CKPT_VERIFY') or '8')\n"
        "if not 1 <= PARAMS['threads'] <= 16: raise ValueError(f'zfast_provider: decomposition D = ZFAST_THREADS {PARAMS[\"threads\"]} outside [1, 16] (review_m10 m7)')\n"
        "if CKPT and not (CK_ROLE in ('gen', 'replay') and len(CK_NONCE) == 32 and all(c in '0123456789abcdef' for c in CK_NONCE) and CK_KEY and CK_VERIFY >= 1):\n"
        "    raise RuntimeError('zfast_provider: ZFAST_CKPT needs ZFAST_CKPT_ROLE (gen|replay), ZFAST_CKPT_NONCE (32 hex), ZFAST_CKPT_KEY and ZFAST_CKPT_VERIFY >= 1')\n")
p = rep(p, "_L.zfa14_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]\n",
        "_L.zfa14_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]\n"
        "_L.zfa14b_new.restype = ctypes.c_void_p\n"
        "_L.zfa14b_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,\n"
        "                          ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]\n"
        "_L.zfa14b_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]\n"
        "_L.zfa14b_last_error.argtypes = [ctypes.c_char_p, ctypes.c_int]\n")
p = rep(p, """        s = _L.zfa14_new(str(T0).encode(), c, PARAMS['H'], PARAMS['Delta'], PARAMS['K'], PARAMS['J'], PARAMS['threads'], WORKERS, CKPT.encode())
        if not s: raise RuntimeError('zfa14_new failed (a checkpoint of a different session, or bad parameters)')
        _L.zfa14_info(s, _BUF, 4096); info = json.loads(_BUF.value.decode()); STATS['info'] = info""",
        """        s = _L.zfa14b_new(str(T0).encode(), c, PARAMS['H'], PARAMS['Delta'], PARAMS['K'], PARAMS['J'], PARAMS['threads'], WORKERS, CKPT.encode(),
                          CK_ROLE.encode(), CK_NONCE.encode(), CK_KEY.encode(), CK_VERIFY)
        if not s:
            _L.zfa14b_last_error(_BUF, 4096)
            raise RuntimeError('zfa14b_new refused the session: ' + _BUF.value.decode())
        if _L.zfa14b_info(s, _BUF, 4096) != 0: raise RuntimeError('zfa14b_info failed')
        info = json.loads(_BUF.value.decode()); STATS['info'] = info
        if CKPT:
            import time as _t
            rec = dict(t=_t.time(), pid=os.getpid(), role=CK_ROLE, nonce=CK_NONCE, ckpt=CKPT, lib_sha=LIB_SHA, info=info)
            with open(CKPT + '.sessions.jsonl', 'a') as _f: _f.write(json.dumps(rec) + '\\n'); _f.flush(); os.fsync(_f.fileno())
            if info.get('ckpt_write_errors'): print(f'zfast_provider WARNING: {info["ckpt_write_errors"]} checkpoint write error(s); this session is NOT resumable', file=sys.stderr, flush=True)""")
p = rep(p, "center=os.environ.get('ZFAST_CENTER'), lib_sha=LIB_SHA, lib='v14', workers=WORKERS, ckpt=CKPT or None)",
        "center=os.environ.get('ZFAST_CENTER'), lib_sha=LIB_SHA, lib='v14b', workers=WORKERS, ckpt=CKPT or None,\n"
        "                ckpt_role=CK_ROLE or None, ckpt_nonce=CK_NONCE or None, ckpt_verify=CK_VERIFY if CKPT else None)")
p = rep(p, "rec = dict(tool='atlas_v5z6 zfast_provider.turing_grid", "rec = dict(tool='atlas_v5z8 zfast_provider.turing_grid")
if 'assert ' in p: raise RuntimeError('provider contains an assert')
open(Z8 + 'lib/zfast_provider.py', 'w').write(p)

# ---------------- driver ----------------
d = open(Z7 + 'atlas_v5.py').read()
d = rep(d, "raise SystemExit('atlas_v5z7: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "raise SystemExit('atlas_v5z8: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')\n" + HOOKS_PY + "\n"
        "if any(k.startswith(HOOK_PREFIXES) for k in os.environ):\n"
        "    raise SystemExit('atlas_v5z8: refusing to start with a libzfast test-hook variable set (review_m10 m8): ' + ', '.join(k for k in os.environ if k.startswith(HOOK_PREFIXES)))\n"
        "KEYDIR = Path('/Users/kiosk/atlas_mark2/diagnostic/zfast/ckpt_keys')        # v5z8: HMAC keys live OUTSIDE every run directory")
d = rep(d, "atlas_v5z7 (RESULTS_M9 F-M9b, F-M9c): W not in pieces.json; no replay unless the generator finished; --resume reuses only a passed replay.\"\"\"",
        "atlas_v5z7 (RESULTS_M9 F-M9b, F-M9c): W not in pieces.json; no replay unless the generator finished; --resume reuses only a passed replay.\n"
        "atlas_v5z8 (PREDICTIONS_M12, THEORY_V5Z8.md): libzfast.v14b; per-run nonce RUN/zfast_ckpt_nonce.txt; role-tagged, HMAC-sealed checkpoints\n"
        "  (keys in diagnostic/zfast/ckpt_keys/, outside RUN); the replay of record refuses any checkpoint it did not create; test hooks refused.\"\"\"")
d = rep(d, "Z_PROVIDER = 'zfast libzfast.v14 (= v13b bit-identically at equal D), provider v5z6 (THEORY_V5Z6); model5 fixed-precision N_win (v5z4)'",
        "Z_PROVIDER = 'zfast libzfast.v14b (= v14 = v13b bit-identically at equal D; hardened checkpoint), provider v5z8 (THEORY_V5Z8); model5 fixed-precision N_win (v5z4)'")
d = rep(d, "            'ZFAST14_GENERIC_KERNEL', 'ZFAST14_TEST_EXIT_AFTER')",
        "            'ZFAST14_GENERIC_KERNEL', 'ZFAST14_TEST_EXIT_AFTER', 'ZFAST_CKPT_ROLE', 'ZFAST_CKPT_NONCE', 'ZFAST_CKPT_KEY', 'ZFAST_CKPT_VERIFY',\n"
        "            'ZFAST14B_TEST_LBSHIFT', 'ZFAST14B_TEST_ZGRID_FAIL_AT')")
d = rep(d, """def child_env(base, zs, **extra):
    e = dict(base)
    for k in SESSION_KEYS: e.pop(k, None)""", """def child_env(base, zs, **extra):
    e = {k: v for k, v in base.items() if not k.startswith(HOOK_PREFIXES)}       # v5z8 (m8): test hooks never reach a child
    for k in SESSION_KEYS: e.pop(k, None)""")
d = rep(d, "    for k in ('ZFAST_CKPT', 'ZFAST_TURING_GRID'): os.environ.pop(k, None)      # v5z6: role-specific, set below per child only",
        "    for k in ('ZFAST_CKPT', 'ZFAST_TURING_GRID', 'ZFAST_CKPT_ROLE', 'ZFAST_CKPT_NONCE', 'ZFAST_CKPT_KEY'): os.environ.pop(k, None)      # v5z6/v5z8: role-specific, set below per child only")
d = rep(d, "        ZSESS.update(lib='v14')        # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS)",
        "        ZSESS.update(lib='v14b')       # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS); v5z8: libzfast.v14b")
d = rep(d, """    v6 = {}
    if a.wide:
        v6['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_gen.txt')""", """    v6 = {}; nonce = None
    if a.wide:
        # v5z8 (M2): one nonce per run, created once (O_EXCL) and reused on --resume; per-role HMAC key files outside RUN
        nf = RUN / 'zfast_ckpt_nonce.txt'
        if not nf.exists():
            import secrets
            fd = os.open(nf, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644); os.write(fd, (secrets.token_hex(16) + '\\n').encode()); os.fsync(fd); os.close(fd)
        nonce = nf.read_text().strip()
        if not (len(nonce) == 32 and all(ch in '0123456789abcdef' for ch in nonce)): raise RuntimeError(f'{nf} is not a 32-hex nonce')
        KEYDIR.mkdir(mode=0o700, exist_ok=True)
        if KEYDIR.stat().st_mode & 0o077: raise RuntimeError(f'{KEYDIR} must be mode 0700')
        log(stage='ckpt_nonce', nonce=nonce, keydir=str(KEYDIR))
        v6.update(ZFAST_CKPT_ROLE='gen', ZFAST_CKPT_NONCE=nonce, ZFAST_CKPT_KEY=str(KEYDIR / f'{nonce}_gen.key'),
                  ZFAST_CKPT_VERIFY=os.environ.get('ZFAST_CKPT_VERIFY') or '8')
        v6['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_gen.txt')""")
d = rep(d, """    else: g = dict(resumed=True)
    log(stage='generator', **g)""", """    else: g = dict(resumed=True)
    log(stage='generator', **g)
    def sidecar(p):
        return [json.loads(l) for l in open(p)] if p.exists() else []
    if a.wide: log(stage='ckpt_sessions_gen', records=[dict(t=x['t'], pid=x['pid'], role=x['role'], nonce=x['nonce'], **{k: x['info'].get(k) for k in
                   ('items', 'items_loaded', 'verified', 'lines_rejected', 'lines_duplicate', 'lines_written', 'ckpt_write_errors', 'created')})
                   for x in sidecar(RUN / 'zfast_ckpt_gen.txt.sessions.jsonl')])""")
d = rep(d, """    renv = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if a.wide: renv['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_replay.txt')         # the replay's own checkpoint, never the generator's""",
        """    renv = dict({k: v for k, v in os.environ.items() if not k.startswith(HOOK_PREFIXES)}, PYTHONDONTWRITEBYTECODE='1')     # v5z8 (m8)
    if a.wide:
        renv['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_replay.txt')         # the replay's own checkpoint, never the generator's
        renv.update(ZFAST_CKPT_ROLE='replay', ZFAST_CKPT_NONCE=nonce, ZFAST_CKPT_KEY=str(KEYDIR / f'{nonce}_replay.key'),
                    ZFAST_CKPT_VERIFY=os.environ.get('ZFAST_CKPT_VERIFY') or '8')      # v5z8 (M2): role replay, the run's nonce, the replay's key""")
d = rep(d, "                sessions_per_window=2 if a.wide else None,",
        "                sessions_per_window=2 if a.wide else None, zfast_ckpt_replay=rc.get('zfast_ckpt'),")
if 'assert ' in d.replace("'assert", ''): raise RuntimeError('driver contains an assert')
open(Z8 + 'atlas_v5.py', 'w').write(d)

# ---------------- replay_target ----------------
r = open(Z7 + 'replay_target5.py').read()
r = rep(r, "    raise SystemExit('atlas_v5z5: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "    raise SystemExit('atlas_v5z8: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
r = rep(r, "the replay env is recorded in replay_check.json (`zfast_env`).\"\"\"",
        "the replay env is recorded in replay_check.json (`zfast_env`).\n"
        "atlas_v5z8 (PREDICTIONS_M12, M2): with ZFAST_CKPT set, replay_check.json gets `zfast_ckpt` (the session records this replay process wrote to\n"
        "ZFAST_CKPT.sessions.jsonl) and `passed` requires at least one record, every one role replay with the run's nonce (RUN/zfast_ckpt_nonce.txt).\"\"\"")
r = rep(r, """    res = dict(run=str(RUN), hull_ok=hull_ok,""", """    # v5z8 (M2): the replay's zfast session(s) must have used only a replay-role checkpoint of THIS run
    ckp = os.environ.get('ZFAST_CKPT'); ckrec = None; ck_ok = True
    if ckp:
        nf = RUN / 'zfast_ckpt_nonce.txt'; run_nonce = nf.read_text().strip() if nf.exists() else None
        sc = Path(ckp + '.sessions.jsonl'); recs_ck = [json.loads(l) for l in open(sc)] if sc.exists() else []
        mine = [x for x in recs_ck if x['t'] >= t0]
        ck_ok = bool(mine) and run_nonce is not None and all(x['role'] == 'replay' and x['nonce'] == run_nonce == os.environ.get('ZFAST_CKPT_NONCE') for x in mine)
        ckrec = dict(path=ckp, run_nonce=run_nonce, ok=ck_ok, sessions=[dict(pid=x['pid'], role=x['role'], nonce=x['nonce'], **{k: x['info'].get(k) for k in
                     ('items', 'items_loaded', 'verified', 'lines_rejected', 'lines_duplicate', 'lines_written', 'ckpt_write_errors', 'created')}) for x in mine])
    res = dict(run=str(RUN), hull_ok=hull_ok, zfast_ckpt=ckrec,""")
r = rep(r, "               passed=bool(hull_ok and certs and len(passed) == len(certs) and not s_h and not s_t and not g0 and til['tiling_sha_ok']),",
        "               passed=bool(hull_ok and certs and len(passed) == len(certs) and not s_h and not s_t and not g0 and til['tiling_sha_ok'] and ck_ok),")
if 'assert ' in r: raise RuntimeError('replay_target contains an assert')
open(Z8 + 'replay_target5.py', 'w').write(r)

# ---------------- run script ----------------
w = open(Z7 + 'run_wide7.sh').read()
w = rep(w, 'Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z7', 'Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z8')
w = rep(w, '# run_wide7.sh NAME T0 TLO THI H DELTA [CENTER] : v5z7 (= v5z6 with the F-M9b/c driver fixes) two-session wide window (THEORY_V5Z6/7):',
        '# run_wide8.sh NAME T0 TLO THI H DELTA [CENTER] : v5z8 (= v5z7 on libzfast.v14b, hardened checkpoints; THEORY_V5Z8) two-session wide window:')
w = rep(w, 'runs/v5z7.log', 'runs/v5z8.log', n=4)
w = rep(w, 'unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT ZFAST_CKPT ZFAST_TURING_GRID',
        'unset PYTHONOPTIMIZE ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT ZFAST_CKPT ZFAST_TURING_GRID ZFAST_CKPT_ROLE ZFAST_CKPT_NONCE ZFAST_CKPT_KEY')
open(Z8 + 'run_wide8.sh', 'w').write(w); os.chmod(Z8 + 'run_wide8.sh', 0o755)

open(Z8 + 'THEORY_V5Z8.md', 'w').write('''# atlas_v5z8 = atlas_v5z7 on libzfast.v14b (hardened checkpoints; PREDICTIONS_M12, review_m10)

**What changed.** Every file is a byte copy of atlas_v5z7 except `lib/zfast_provider.py`, `atlas_v5.py` and `replay_target5.py`
(counted replacements in `tools/make_v5z8.py`), plus `run_wide8.sh`. THEORY_V5Z6 and THEORY_V5Z7 still apply: provider, generator +
Turing grid stage, replay, verifiers.

**The engine.** libzfast.v14b's compute path is v14's (= v13b at equal D). Only the checkpoint layer and the API guards changed, so an
uninterrupted v5z8 window equals a v5z7 window bit for bit (PREDICTIONS_M12 I1, G1). In detail:

- **M1.** The checkpoint header pins the pre-fast session state (`prefast`: nbeg, Lb, Xb, tau0), the library image, the
  FLINT/GMP/MPFR versions and dylib hashes, and the OS build. A resume across any change refuses, naming the field.
- **M2.** Headers carry role (gen | replay) and the run's nonce, and must match the caller's.
  - The driver creates the nonce once per run (`RUN/zfast_ckpt_nonce.txt`).
  - It gives the generator role gen and the replay of record role replay, with per-role key files.
  - `replay_target5.py` fails (`passed` false) unless every zfast session of the replay process is recorded with role replay and the
    run's nonce. It records items_loaded / verified / lines_rejected in `replay_check.json` (`zfast_ckpt`).
- **m1. Every checkpoint line is HMAC-SHA256 sealed.**
  - The per-run, per-role 32-byte key is created by libzfast (O_EXCL, 0600) in `diagnostic/zfast/ckpt_keys/` (0700), outside every
    run directory.
  - Authenticated lines are strictly validated. A resume recomputes `ZFAST_CKPT_VERIFY` (default 8) random loaded items, which must
    be bit-identical.
  - **Trust model.** The key gives authenticity against everything that lacks it: copies, misrouting, plain-SHA reseals and other
    tools. It gives none against a key holder, who is trusted like the code.
  - The sample recompute is an independent, probabilistic content check. For a single forged item among N loaded items, the detection
    probability per resume is 8/N.
- **m3.** Write and fsync errors are checked and reported (provider warning + sidecar). The session continues, unaffected but not
  resumable.
- **m4.** flock.
- **m7.** D in [1, 16].
- **m8.** The production dylib has no env test hooks. The provider refuses to import, and the driver refuses to start, with any
  test-hook variable set. The driver strips them from every child env.

**Operating rule.** The interim rule from review_m10 ("never resume across an OS/Homebrew/library change") is now enforced by the
library: such a resume is refused. The remedy is to start a fresh run name.

Do not delete `ckpt_keys/`: a run's checkpoints cannot be resumed without its keys. Keys are not certificate inputs; losing them
costs only recomputation.
''')

files = ['atlas_v5.py', 'replay_target5.py', 'crosscheck.py', 'THEORY_V5Z8.md', 'VERIFY_ZS5.sha256', 'run_wide8.sh'] + \
        ['lib/' + x for x in sorted(os.listdir(Z8 + 'lib')) if x.endswith('.py')] + ['nzeros/arb_nzeros.py']
lines = [f'{sha(Z8 + f)}  {f}' for f in files]
lines.append(f'{LIB_SHA}  ../bin/libzfast.v14b.dylib')
for l in open(ZF + 'bin/SHA256.v14b'):
    h, f = l.split()
    if f.startswith('src_v14b/'): lines.append(f'{h}  ../bin/{f}')
lines.append(f'{sha(ZF + "tools/make_v5z8.py")}  ../tools/make_v5z8.py')
for t in ('THEORY_V5Z6.md',): lines.append(f'{sha(ZF + "atlas_v5z6/" + t)}  ../atlas_v5z6/{t}')
lines.append(f'{sha(Z7 + "THEORY_V5Z7.md")}  ../atlas_v5z7/THEORY_V5Z7.md')
for l in lines:
    h, f = l.split(); p_ = os.path.normpath(Z8 + f)
    if sha(p_) != h: raise RuntimeError(f'freeze sha mismatch {f}')
open(Z8 + 'V5Z8_FREEZE.sha256', 'w').write('\n'.join(lines) + '\n')
print('ok', len(lines), 'files frozen')
