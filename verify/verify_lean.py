"""Lean-side checks of the RH window certificates (repository-only wrapper; NOT a frozen pipeline file).

(a) Re-export identity: the unchanged exact exporter atlas_mark2/formal/export/export_certs.py (binary64 -> exact rationals) is run on
    the certificate files of this repository and its output must be byte-identical to the stored Lean dataset (stored .txt or .txt.xz).
(b) Lean audit (only if an atlas_audit executable is available: $ATLAS_AUDIT_BIN, or atlas_mark2/formal/.lake/build/bin/atlas_audit
    after `lake build atlas_audit`): every stored dataset is audited again and the report must be identical to the stored report,
    with "VIOLATIONS 0".
usage: python -B verify/verify_lean.py OUTDIR"""
import glob, json, lzma, os, re, subprocess, sys, hashlib
from pathlib import Path

if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')
REPO = Path(__file__).resolve().parent.parent; A = REPO / 'atlas_mark2'; ZF = A / 'diagnostic' / 'zfast'
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
DIRS = {'atlas_v5z': ZF / 'atlas_v5z', 'atlas_v5z2': ZF / 'atlas_v5z2', 'atlas_v5z3': ZF / 'atlas_v5z3', 'atlas_v5z4': ZF / 'atlas_v5z4',
        'atlas_v5z5': ZF / 'atlas_v5z5', 'atlas_v5z7': ZF / 'atlas_v5z7', 'record_heights': A / 'diagnostic' / 'record_heights'}
RUNROOT = {k: (v / 'v5run' if k == 'record_heights' else v) for k, v in DIRS.items()}
BIN = os.environ.get('ATLAS_AUDIT_BIN') or str(A / 'formal' / '.lake' / 'build' / 'bin' / 'atlas_audit')
env = dict(os.environ, ATLAS_REPO=str(REPO), PYTHONPATH=str(REPO / 'verify' / 'boot'), PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONOPTIMIZE', None)


def stored_bytes(p):
    return lzma.open(p).read() if str(p).endswith('.xz') else open(p, 'rb').read()


def run_for(tree, name):
    tag, _, rest = name.partition('_')
    cands = [rest, 'z_' + rest, 'big_' + rest, rest.replace('record_', '')]
    for c in cands:
        hits = glob.glob(str(RUNROOT[tree] / 'runs' / 'w*' / c))
        if len(hits) == 1 and Path(hits[0], 'certs').is_dir(): return Path(hits[0])
    if tree == 'record_heights':
        hits = glob.glob(str(RUNROOT[tree] / 'runs' / 'w*' / ('big_' + name.split('_', 1)[1])))
        hits = hits or glob.glob(str(RUNROOT[tree] / 'runs' / 'w*' / name.split('_', 1)[1]))
        if len(hits) == 1: return Path(hits[0])
    return None


rows = []; fails = 0
have_bin = os.path.exists(BIN)
for tree, d in DIRS.items():
    for f in sorted(glob.glob(str(d / 'lean_audit' / '*.txt')) + glob.glob(str(d / 'lean_audit' / '*.txt.xz'))):
        base = os.path.basename(f).replace('.txt.xz', '').replace('.txt', '')
        if base.startswith('audit_') or base.startswith('export_'): continue
        rep = d / 'lean_audit' / f'audit_{base}.txt'
        if not rep.exists(): rep = d / 'lean_audit' / f"audit_{base.replace('record_', '')}.txt"
        row = dict(tree=tree, dataset=base, stored=os.path.relpath(f, REPO))
        stored = stored_bytes(f); work = OUT / f'{base}.txt'; open(work, 'wb').write(stored)
        run = run_for(tree, base)
        if run is not None:
            od = OUT / 'reexport'; od.mkdir(exist_ok=True)
            p = subprocess.run(['nice', '-n', '19', sys.executable, '-B', str(REPO / 'verify' / 'run_rewritten.py'),
                                str(A / 'formal' / 'export' / 'export_certs.py'), '--v5', base, str(od), str(run)],
                               capture_output=True, text=True, env=env)
            new = od / f'{base}.txt'
            row['reexport_identical'] = bool(p.returncode == 0 and new.exists() and open(new, 'rb').read() == stored)
            if new.exists(): new.unlink()
        else:
            row['reexport_identical'] = None          # dataset spans several runs or has an irregular name: audit only
        if have_bin and rep.exists():
            p = subprocess.run(['nice', '-n', '19', BIN, str(work)], capture_output=True, text=True, cwd=str(A / 'formal'))
            out = p.stdout + p.stderr
            row['audit_identical'] = (out == open(rep).read())
            m = re.search(r'TOTAL VIOLATIONS \(non-control datasets\): (\d+)', out); row['violations'] = int(m.group(1)) if m else None
        work.unlink()
        ok = row['reexport_identical'] is not False and (not have_bin or not rep.exists() or (row['audit_identical'] and row['violations'] == 0))
        row['ok'] = ok; fails += not ok; rows.append(row)
        print(f"{'OK  ' if ok else 'FAIL'} {tree:15s} {base:28s} re-export identical: {row['reexport_identical']}"
              + (f" | Lean audit identical: {row.get('audit_identical')}, violations {row.get('violations')}" if have_bin else ' | Lean audit: SKIPPED (atlas_audit not built)'), flush=True)
bsha = hashlib.sha256(open(BIN, 'rb').read()).hexdigest() if have_bin else None
json.dump(dict(atlas_audit=BIN if have_bin else None, atlas_audit_sha256=bsha, rows=rows), open(OUT / 'verify_lean.json', 'w'), indent=1)
print(f'Lean datasets: {len(rows) - fails}/{len(rows)} OK; atlas_audit: {BIN if have_bin else "not built (audit skipped)"}' + (f' sha256 {bsha[:16]}...' if bsha else ''))
sys.exit(1 if fails else 0)
