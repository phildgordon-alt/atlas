"""Builds atlas_v5z7/ from atlas_v5z6/ (new files only; v5z6 is never written).  RESULTS_M9 findings F-M9b, F-M9c (both fail-safe resume defects
of the v5z6 DRIVER).  Byte copies of every v5z6 file (provider, generator, replay, verifiers, libzfast.v14) except atlas_v5.py (three
counted replacements below), run_wide7.sh and THEORY_V5Z7.md.  Ends by writing V5Z7_FREEZE.sha256.
  F-M9b: v5z6 wrote gen_workers (W, output-free) into pieces.json's zfast_session, so --resume with another ZFAST_WORKERS was refused.
         v5z7 records W only in drive.jsonl (env ZFAST_WORKERS), not in pieces.json.
  F-M9c: v5z6 ran stage 3 (replay) even when the generator had died; that replay wrote replay_check.json (passed = false) and --resume
         then reused it, so a resumed window ended "not closed".  v5z7 skips the replay unless gen_done is logged, and on --resume reuses
         a replay only if its replay_check.json has passed = true (otherwise it is renamed *.attemptN and rerun)."""
import os, sys, shutil, hashlib
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
Z6 = ZF + 'atlas_v5z6/'; Z7 = ZF + 'atlas_v5z7/'
if os.path.exists(Z7): raise SystemExit(f'{Z7} exists: never overwrite (make a new version)')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rep(s, old, new, n=1):
    if s.count(old) != n: raise RuntimeError(f'replacement anchor found {s.count(old)} times (want {n}): {old[:80]!r}')
    return s.replace(old, new)


for l in open(Z6 + 'V5Z6_FREEZE.sha256'):
    h, f = l.split()
    if sha(os.path.normpath(Z6 + f)) != h: raise RuntimeError(f'atlas_v5z6 differs from its freeze: {f}')
os.makedirs(Z7 + 'lib'); os.makedirs(Z7 + 'nzeros'); os.makedirs(Z7 + 'runs')
for f in ['crosscheck.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py', 'replay_target5.py'] + ['lib/' + x for x in sorted(os.listdir(Z6 + 'lib')) if x.endswith('.py')]:
    shutil.copyfile(Z6 + f, Z7 + f)
    if sha(Z6 + f) != sha(Z7 + f): raise RuntimeError(f'copy mismatch {f}')

d = open(Z6 + 'atlas_v5.py').read()
d = rep(d, "        ZSESS.update(lib='v14', gen_workers=int(os.environ.get('ZFAST_WORKERS') or gen_threads))",
        "        ZSESS.update(lib='v14')        # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS)")
d = rep(d, "    if (RUN / 'replay_check' / 'replay_check.json').exists() and a.resume: r = dict(resumed=True, seconds=None, peak_gb=0)\n    else:",
        "    gen_ok = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))\n"
        "    rprev = json.load(open(RUN / 'replay_check' / 'replay_check.json')) if (RUN / 'replay_check' / 'replay_check.json').exists() else None\n"
        "    if not gen_ok: r = dict(skipped='generator did not finish (v5z7, F-M9c): no replay', seconds=None, peak_gb=0)\n"
        "    elif a.resume and rprev is not None and rprev.get('passed') is True: r = dict(resumed=True, seconds=None, peak_gb=0)\n"
        "    else:")
d = rep(d, "raise SystemExit('atlas_v5z6: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')",
        "raise SystemExit('atlas_v5z7: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')")
d = rep(d, "  The replay of record is the driver's stage 3 (a fresh process, replay_target5.py byte copy); v5z6 runs no second replay.\"\"\"",
        "  The replay of record is the driver's stage 3 (a fresh process, replay_target5.py byte copy); v5z6 runs no second replay.\n"
        "atlas_v5z7 (RESULTS_M9 F-M9b, F-M9c): W not in pieces.json; no replay unless the generator finished; --resume reuses only a passed replay.\"\"\"")
if 'assert ' in d.replace("'assert", ''): raise RuntimeError('driver contains an assert')
open(Z7 + 'atlas_v5.py', 'w').write(d)

w = open(Z6 + 'run_wide6.sh').read()
w = rep(w, 'Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z6', 'Z=/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z7')
w = rep(w, '# run_wide6.sh NAME T0 TLO THI H DELTA [CENTER] : v5z6 two-session wide window (THEORY_V5Z6.md):',
        '# run_wide7.sh NAME T0 TLO THI H DELTA [CENTER] : v5z7 (= v5z6 with the F-M9b/c driver fixes) two-session wide window (THEORY_V5Z6/7):')
w = rep(w, 'runs/v5z6.log', 'runs/v5z7.log', n=4)
open(Z7 + 'run_wide7.sh', 'w').write(w); os.chmod(Z7 + 'run_wide7.sh', 0o755)

open(Z7 + 'THEORY_V5Z7.md', 'w').write('''# atlas_v5z7 = atlas_v5z6 with two fail-safe resume defects of the driver fixed (2026-11-01; RESULTS_M9 F-M9b, F-M9c)

Every file is a byte copy of atlas_v5z6 (THEORY_V5Z6.md applies unchanged: libzfast.v14, provider, generator + Turing grid stage,
replay, verifiers) except `atlas_v5.py`:
- F-M9b: the worker count W (output-free) is no longer written into pieces.json's `zfast_session` (v5z6 refused a `--resume` with a
  different ZFAST_WORKERS); it is recorded in drive.jsonl's env.
- F-M9c: stage 3 (the replay of record) runs only if the generator logged `gen_done`; on `--resume` an existing replay is reused only if
  its replay_check.json has passed = true, otherwise it is renamed `*.attemptN` and rerun (v5z6 reused the failed replay of a run whose
  generator had died, so the resumed window ended "not closed").
Both v5z6 defects failed safe (refusal / "not closed"); neither could produce a false PASS. No certificate-relevant code changed.
''')

files = ['atlas_v5.py', 'replay_target5.py', 'crosscheck.py', 'THEORY_V5Z7.md', 'VERIFY_ZS5.sha256', 'run_wide7.sh'] + \
        ['lib/' + x for x in sorted(os.listdir(Z7 + 'lib')) if x.endswith('.py')] + ['nzeros/arb_nzeros.py']
lines = [f'{sha(Z7 + f)}  {f}' for f in files]
for l in open(Z6 + 'V5Z6_FREEZE.sha256'):
    if l.split()[1].startswith('../bin/') or l.split()[1] == '../tools/v5z6_src/zfast_provider.py': lines.append(l.rstrip('\n'))
lines.append(f'{sha(ZF + "tools/make_v5z7.py")}  ../tools/make_v5z7.py')
lines.append(f'{sha(Z6 + "THEORY_V5Z6.md")}  ../atlas_v5z6/THEORY_V5Z6.md')
for l in lines:
    h, f = l.split(); p = os.path.normpath(Z7 + f)
    if sha(p) != h: raise RuntimeError(f'freeze sha mismatch {f}')
open(Z7 + 'V5Z7_FREEZE.sha256', 'w').write('\n'.join(lines) + '\n')
print('ok', len(lines), 'files frozen')
