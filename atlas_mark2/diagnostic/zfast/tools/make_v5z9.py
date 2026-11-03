"""Builds atlas_v5z9/ from atlas_v5z8/ (new files only; v5z8 is never written).  PREDICTIONS_M13 (review_v14b; libzfast.v14c).  Byte
copies of every v5z8 file except (counted replacements below):
  lib/zfast_provider.py  libzfast.v14c (sha-pinned; same ctypes API as v14b); lib='v14c'; hook prefixes add ZFAST14C_TEST; tool names v5z9
  atlas_v5.py            hook prefixes add ZFAST14C_TEST; Z_PROVIDER / ZSESS lib v14c; the GENERATOR session's ZFAST_CKPT_VERIFY default
                         is 64 (review_v14b mn7; the replay stays 8; both overridable by ZFAST_CKPT_VERIFY); names v5z9
  replay_target5.py      names v5z9 only
  run_wide9.sh (from run_wide8.sh: tree path and log name), THEORY_V5Z9.md (new).  Ends by writing V5Z9_FREEZE.sha256."""
import os, sys, shutil, hashlib
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
Z8 = ZF + 'atlas_v5z8/'; Z9 = ZF + 'atlas_v5z9/'
LIB = ZF + 'bin/libzfast.v14c.dylib'; LIB_SHA = '59883f5e2d83585b67c08a2e3816d180248cd760c705642f13b571b71ad37471'
OLD_LIB_SHA = 'd77bf28f21752e7c90c9990221a1ff702e4227b1038a2fb4106fb5d9eb9e7d52'
if os.path.exists(Z9): raise SystemExit(f'{Z9} exists: never overwrite (make a new version)')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rep(s, old, new, n=1):
    if s.count(old) != n: raise RuntimeError(f'replacement anchor found {s.count(old)} times (want {n}): {old[:80]!r}')
    return s.replace(old, new)


if sha(LIB) != LIB_SHA: raise RuntimeError('libzfast.v14c sha mismatch')
for l in open(Z8 + 'V5Z8_FREEZE.sha256'):
    h, f = l.split()
    if sha(os.path.normpath(Z8 + f)) != h: raise RuntimeError(f'atlas_v5z8 differs from its freeze: {f}')
os.makedirs(Z9 + 'lib'); os.makedirs(Z9 + 'nzeros'); os.makedirs(Z9 + 'runs')
COPY = ['crosscheck.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py'] + ['lib/' + x for x in sorted(os.listdir(Z8 + 'lib')) if x.endswith('.py') and x != 'zfast_provider.py']
for f in COPY:
    shutil.copyfile(Z8 + f, Z9 + f)
    if sha(Z8 + f) != sha(Z9 + f): raise RuntimeError(f'copy mismatch {f}')

HOOKS_OLD = "HOOK_PREFIXES = ('ZFAST14_TEST', 'ZFAST14B_TEST', 'ZFAST14_GENERIC_KERNEL')"
HOOKS_NEW = "HOOK_PREFIXES = ('ZFAST14_TEST', 'ZFAST14B_TEST', 'ZFAST14C_TEST', 'ZFAST14_GENERIC_KERNEL')"

# ---------------- provider ----------------
p = open(Z8 + 'lib/zfast_provider.py').read()
p = rep(p, '"""atlas_v5z8 Z / row provider (TRUSTED;', '''"""atlas_v5z9 Z / row provider (TRUSTED; PREDICTIONS_M13 / THEORY_V5Z9.md) = the v5z8 provider on libzfast.v14c (same ctypes API;
checkpoint format v3: header-bound, index-bound line seals, duplicates refused, atomic keys, no FLINT abort in the parser, time-based
fsync, environment identity without placeholders).  Hook prefixes add ZFAST14C_TEST.  v5z8 docstring follows.
atlas_v5z8 Z / row provider (TRUSTED;''')
p = rep(p, "    raise SystemExit('atlas_v5z8: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "    raise SystemExit('atlas_v5z9: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
p = rep(p, HOOKS_OLD, HOOKS_NEW)
p = rep(p, "raise SystemExit('atlas_v5z8 zfast_provider: a libzfast test-hook variable is set", "raise SystemExit('atlas_v5z9 zfast_provider: a libzfast test-hook variable is set")
p = rep(p, "LIBPATH = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v14b.dylib'\nLIB_SHA = '" + OLD_LIB_SHA + "'",
        f"LIBPATH = '{LIB}'\nLIB_SHA = '{LIB_SHA}'")
p = rep(p, "lib_sha=LIB_SHA, lib='v14b', workers=WORKERS", "lib_sha=LIB_SHA, lib='v14c', workers=WORKERS")
p = rep(p, "rec = dict(tool='atlas_v5z8 zfast_provider.turing_grid", "rec = dict(tool='atlas_v5z9 zfast_provider.turing_grid")
if 'assert ' in p: raise RuntimeError('provider contains an assert')
if 'v14b.dylib' in p: raise RuntimeError('provider still names libzfast.v14b')
open(Z9 + 'lib/zfast_provider.py', 'w').write(p)

# ---------------- driver ----------------
d = open(Z8 + 'atlas_v5.py').read()
d = rep(d, "raise SystemExit('atlas_v5z8: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "raise SystemExit('atlas_v5z9: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
d = rep(d, HOOKS_OLD, HOOKS_NEW)
d = rep(d, "raise SystemExit('atlas_v5z8: refusing to start with a libzfast test-hook variable set", "raise SystemExit('atlas_v5z9: refusing to start with a libzfast test-hook variable set")
d = rep(d, "  (keys in diagnostic/zfast/ckpt_keys/, outside RUN); the replay of record refuses any checkpoint it did not create; test hooks refused.\"\"\"",
        "  (keys in diagnostic/zfast/ckpt_keys/, outside RUN); the replay of record refuses any checkpoint it did not create; test hooks refused.\n"
        "atlas_v5z9 (PREDICTIONS_M13, THEORY_V5Z9.md): libzfast.v14c (checkpoint format v3, review_v14b MJ1/mn1-mn6); the generator session\n"
        "  recomputes ZFAST_CKPT_VERIFY = 64 loaded items on resume by default (mn7; the replay stays 8).\"\"\"")
d = rep(d, "Z_PROVIDER = 'zfast libzfast.v14b (= v14 = v13b bit-identically at equal D; hardened checkpoint), provider v5z8 (THEORY_V5Z8); model5 fixed-precision N_win (v5z4)'",
        "Z_PROVIDER = 'zfast libzfast.v14c (= v14 = v13b bit-identically at equal D; checkpoint v3), provider v5z9 (THEORY_V5Z9); model5 fixed-precision N_win (v5z4)'")
d = rep(d, "        ZSESS.update(lib='v14b')       # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS); v5z8: libzfast.v14b",
        "        ZSESS.update(lib='v14c')       # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS); v5z9: libzfast.v14c")
d = rep(d, """        v6.update(ZFAST_CKPT_ROLE='gen', ZFAST_CKPT_NONCE=nonce, ZFAST_CKPT_KEY=str(KEYDIR / f'{nonce}_gen.key'),
                  ZFAST_CKPT_VERIFY=os.environ.get('ZFAST_CKPT_VERIFY') or '8')""",
        """        v6.update(ZFAST_CKPT_ROLE='gen', ZFAST_CKPT_NONCE=nonce, ZFAST_CKPT_KEY=str(KEYDIR / f'{nonce}_gen.key'),
                  ZFAST_CKPT_VERIFY=os.environ.get('ZFAST_CKPT_VERIFY') or '64')      # v5z9 (review_v14b mn7): generator verify default 64""")
if 'assert ' in d: raise RuntimeError('driver contains an assert')
open(Z9 + 'atlas_v5.py', 'w').write(d)

# ---------------- replay_target ----------------
r = open(Z8 + 'replay_target5.py').read()
r = rep(r, "    raise SystemExit('atlas_v5z8: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "    raise SystemExit('atlas_v5z9: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
open(Z9 + 'replay_target5.py', 'w').write(r)

# ---------------- run script ----------------
w = open(Z8 + 'run_wide8.sh').read()
w = rep(w, "# run_wide8.sh NAME T0 TLO THI H DELTA [CENTER] : v5z8 (= v5z7 on libzfast.v14b, hardened checkpoints; THEORY_V5Z8) two-session wide window:",
        "# run_wide9.sh NAME T0 TLO THI H DELTA [CENTER] : v5z9 (= v5z8 on libzfast.v14c, checkpoint v3; THEORY_V5Z9) two-session wide window:")
w = rep(w, "Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z8;", "Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z9;")
w = rep(w, "runs/v5z8.log", "runs/v5z9.log", 4)
open(Z9 + 'run_wide9.sh', 'w').write(w); os.chmod(Z9 + 'run_wide9.sh', 0o755)

open(Z9 + 'THEORY_V5Z9.md', 'w').write('''# atlas_v5z9 = atlas_v5z8 on libzfast.v14c (checkpoint format v3; PREDICTIONS_M13, review_v14b)

**What changed.** Every file is a byte copy of atlas_v5z8 except `lib/zfast_provider.py`, `atlas_v5.py` and `replay_target5.py`
(counted replacements in `tools/make_v5z9.py`), plus `run_wide9.sh`. THEORY_V5Z6, THEORY_V5Z7 and THEORY_V5Z8 still apply.

**The engine.** libzfast.v14c's compute path is v14's (= v13b at equal D), byte for byte; only the checkpoint layer
(`zfast_sched14c.inc`) and its wiring changed, so an uninterrupted v5z9 window equals a v5z8/v5z7 window bit for bit
(PREDICTIONS_M13 I1, G1). The ctypes API (`zfa14b_new`, `zfa14b_info`, `zfa14b_last_error`) is unchanged.

**Checkpoint v3 (review_v14b).**
- **MJ1.** Every item line is sealed as HMAC(K, "ZF14C-ITEM\\0" || SHA-256(header body) || u64be(item index) || line body), and every
  new header carries a fresh random `hnonce`. A line therefore authenticates only in the file (header) and at the index it was written
  for: a line from another session, run, recreated file or position is ignored (never loaded) even under the same key. A second
  authenticated line for a loaded item refuses the session (identical or conflicting duplicate). A new header under an existing key
  is allowed (crash recovery), reported (`key_reused_new_header`) and cannot be spliced.
- **mn1.** The arb parser builds each ball from its tokens with exact FLINT setters (no `arb_load_str`, which aborts the process on
  some malformed inputs) and accepts only canonical values: malformed authenticated input refuses with a reason.
- **mn2.** A flusher thread F_FULLFSYNCs every 1.0 s while lines are unsynced: a line is durable within 1 s + one F_FULLFSYNC of its
  write (measured: `max_unsynced_s`).
- **mn3.** The header pins the dyld shared-cache UUID, hw.model, LC_UUIDs of all loaded images and the in-memory `__TEXT` hash of
  libzfast; an unavailable field refuses (no placeholders). Consequence: a resume after ANY OS update (including a background security
  update that changes the shared cache) or on another Mac is refused; keep automatic OS updates off during a multi-day run.
- **mn4.** Keys are created atomically (temp, F_FULLFSYNC, renamex_np(RENAME_EXCL), directory fsync); an existing key must be a
  regular, non-symlink, user-owned, 0600-or-stricter, 32-byte file. A 0-byte key (from a pre-v14c crash) refuses.
- **mn5/mn6.** Worker write errors reach `zfa14b_last_error`; overlong lines are skipped without being stored.
- **mn7 (this tree).** The generator session recomputes 64 random loaded items on every resume (replay: 8). For k forged-but-authentic
  items among N loaded the detection probability per resume is 1 - C(N-k, 64)/C(N, 64) (= 64/N for k = 1). The key holder is
  trusted, as before.

Do not delete `ckpt_keys/`. Keys are not certificate inputs; losing them costs only recomputation.
''')

files = ['atlas_v5.py', 'replay_target5.py', 'crosscheck.py', 'THEORY_V5Z9.md', 'VERIFY_ZS5.sha256', 'run_wide9.sh'] + \
        ['lib/' + x for x in sorted(os.listdir(Z9 + 'lib')) if x.endswith('.py')] + ['nzeros/arb_nzeros.py']
lines = [f'{sha(Z9 + f)}  {f}' for f in files]
lines.append(f'{LIB_SHA}  ../bin/libzfast.v14c.dylib')
for l in open(ZF + 'bin/SHA256.v14c'):
    h, f = l.split()
    if f.startswith('src_v14c/'): lines.append(f'{h}  ../bin/{f}')
lines.append(f'{sha(ZF + "tools/make_v5z9.py")}  ../tools/make_v5z9.py')
for t in ('atlas_v5z6/THEORY_V5Z6.md', 'atlas_v5z7/THEORY_V5Z7.md', 'atlas_v5z8/THEORY_V5Z8.md'): lines.append(f'{sha(ZF + t)}  ../{t}')
for l in lines:
    h, f = l.split(); p_ = os.path.normpath(Z9 + f)
    if sha(p_) != h: raise RuntimeError(f'freeze sha mismatch {f}')
open(Z9 + 'V5Z9_FREEZE.sha256', 'w').write('\n'.join(lines) + '\n')
print('ok', len(lines), 'files frozen')
