"""engine/regress_v1 Lean audit layer (PREREG 2.2): re-export into scratch (byte identity) + audit binary on stored exports (byte identity)."""
import glob, os, re, shutil, subprocess, time
from pathlib import Path
from .common import DIAG, ROOT, WORK, RegressError, sha256, guarded, env_base

FORMAL = ROOT / 'formal'
EXPORTER = FORMAL / 'export' / 'export_certs.py'
AUDIT_BIN = FORMAL / '.lake' / 'build' / 'bin' / 'atlas_audit'
PY3 = 'python3'          # the stored exports were made with `python3` (stdlib only), as in run_m6_stage2.sh / audit/RESULTS.md
BASE_LIST = ['deg2', 'ec37a', 'ec389a', 'tollis', 'tollis_extra', 'tollis_ext_unions', 'v4_acceptance', 'v4_other',
             'deg2_nc', 'ec37a_nc', 'ec389a_nc', 'tollis_nc']
TREE_OF_PREFIX = [('v5z7_', 'atlas_v5z7'), ('v5z6_', 'atlas_v5z6'), ('v5z5_', 'atlas_v5z5'),      # A7 (F-M9a): later trees named
                  ('v5z4_', 'atlas_v5z4'), ('v5z3_', 'atlas_v5z3'), ('v5z2_', 'atlas_v5z2'), ('v5z_', 'atlas_v5z'),
                  ('record_', 'record_heights'), ('v5_', 'atlas_v5')]
# A7 (F-M9a): Lean datasets of trees that are not in zfast.TREES (the GOLDEN_v1 / FROZEN.json scope: atlas_v5 .. atlas_v5z4) are out of
# tier-0 scope.  They are skipped and listed here (reported by cli.tier0 outside the golden hash); their gates are v5z5_gate.py,
# v5z6_gate.py and turing_gate.py.  A dataset name with no known prefix raises RegressError (before A7: a bare StopIteration crash).
SKIPPED_OUT_OF_SCOPE = []


def v5_datasets():
    """(dataset name, stored export, stored audit output or None, [run dirs in stored order])"""
    from .zfast import TREES
    out = []; del SKIPPED_OUT_OF_SCOPE[:]
    files = sorted(glob.glob(str(DIAG / 'zfast' / 'atlas_v5z*' / 'lean_audit' / '*.txt')) + glob.glob(str(DIAG / 'record_heights' / 'lean_audit' / '*.txt'))
                   + glob.glob(str(FORMAL / 'audit' / 'data_v5' / 'v5_*.txt')))
    for f in files:
        first = open(f).readline().split()
        if not first or first[0] != 'DATASET': continue
        name = first[1]; tree = next((t for p, t in TREE_OF_PREFIX if name.startswith(p)), None)
        if tree is None: raise RegressError(f'Lean dataset {name!r} ({f}) has no known tree prefix (lean.TREE_OF_PREFIX)')
        if tree not in TREES:
            SKIPPED_OUT_OF_SCOPE.append(dict(name=name, export=f, tree=tree)); continue
        runs = []
        for line in open(f):
            if line.startswith('CERT '):
                r = line.split()[1]
                if r not in runs: runs.append(r)
        root = TREES[tree][0] / 'runs'
        d = Path(f).parent
        aud = d / f'audit_{name}.txt'
        if not aud.exists() and name.startswith('record_'): aud = d / f'audit_{name[len("record_"):]}.txt'
        out.append(dict(name=name, export=f, audit=str(aud) if aud.exists() else None, runs=[str(root / r) for r in runs]))
    return out


def _run(cmd, cwd, log, timeout=600):
    return guarded(cmd, cwd, log, env=env_base(), timeout=timeout)


def audit_files(files, out):
    g = _run([str(AUDIT_BIN)] + [str(x) for x in files], FORMAL, out)
    return g, open(out, 'rb').read()


def tier0(scratch, mutate_one=None):
    S = Path(scratch); S.mkdir(parents=True, exist_ok=True); res = dict(audit_bin_sha256=sha256(AUDIT_BIN), exporter_sha256=sha256(EXPORTER))
    # (a) v5 datasets
    v5 = []; data_v5_files = []
    for ds in v5_datasets():
        od = S / 'v5' / ds['name']; od.mkdir(parents=True, exist_ok=True)
        g = _run([PY3, '-B', str(EXPORTER), '--v5', ds['name'], str(od)] + ds['runs'], FORMAL, od / 'export.log')
        new = od / f"{ds['name']}.txt"
        ex_ok = new.exists() and sha256(new) == sha256(ds['export'])
        rec = dict(name=ds['name'], runs=len(ds['runs']), export_rc=g['rc'], export_identical=ex_ok)
        if ds['export'].startswith(str(FORMAL / 'audit' / 'data_v5')):
            data_v5_files.append(ds['export'])
        else:
            ga, out = audit_files([ds['export']], od / 'audit.out')
            rec.update(audit_rc=ga['rc'], audit_identical=(None if ds['audit'] is None else out == open(ds['audit'], 'rb').read()),
                       stored_audit=ds['audit'] is not None,
                       zero_violations=b'TOTAL VIOLATIONS (non-control datasets): 0' in out)
        v5.append(rec)
    if data_v5_files:
        stored = FORMAL / 'audit' / 'data_v5' / 'audit_output_v5.txt'
        order = [str(FORMAL / 'audit' / 'data_v5' / f'{n}.txt') for n in ('v5_acceptance', 'v5_big')]
        ga, out = audit_files(order, S / 'v5' / 'data_v5_audit.out')
        res['data_v5_audit'] = dict(rc=ga['rc'], identical=(stored.exists() and out == stored.read_bytes()),
                                    zero_violations=b'TOTAL VIOLATIONS (non-control datasets): 0' in out)
    res['v5'] = v5
    # (b) base export + audit
    bd = S / 'base'; bd.mkdir(exist_ok=True)
    g = _run([PY3, '-B', str(EXPORTER), str(bd)], FORMAL, S / 'base_export.log')
    cmp = {}
    for f in sorted(glob.glob(str(FORMAL / 'audit' / 'data' / '*.txt'))):
        n = Path(f).name
        if n == 'tollis_ext_unions.txt': continue
        cmp[n] = (bd / n).exists() and sha256(bd / n) == sha256(f)
    ga, out = audit_files([FORMAL / 'audit' / 'data' / f'{n}.txt' for n in BASE_LIST], S / 'base_audit.out')
    res['base'] = dict(export_rc=g['rc'], export_identical=cmp, audit_rc=ga['rc'],
                       audit_identical=out == (FORMAL / 'audit' / 'audit_output.txt').read_bytes())
    # (c) flagship
    fd = S / 'flagship'; fd.mkdir(exist_ok=True)
    g = _run([PY3, '-B', str(FORMAL / 'audit' / 'export_flagship.py'), str(fd)], FORMAL, S / 'flagship_export.log')
    fc = {}
    for f in sorted(glob.glob(str(FORMAL / 'audit' / 'data_flagship' / '*'))):
        n = Path(f).name; fc[n] = (fd / n).exists() and sha256(fd / n) == sha256(f)
    ga, out = audit_files([FORMAL / 'audit' / 'data_flagship' / 'flagship_K23.txt', FORMAL / 'audit' / 'data_flagship' / 'flagship_K23_nc.txt'],
                          S / 'flagship_audit.out', )
    res['flagship'] = dict(export_rc=g['rc'], export_identical=fc, audit_rc=ga['rc'], audit_seconds=ga['seconds'], audit_peak_gb=ga['peak_gb'],
                           audit_identical=out == (FORMAL / 'audit' / 'audit_output_flagship.txt').read_bytes())
    ok_v5 = all(r['export_identical'] and r.get('audit_identical') is not False and r.get('zero_violations', True) for r in v5)
    ok = (ok_v5 and res.get('data_v5_audit', {}).get('identical', False) and all(cmp.values()) and res['base']['audit_identical']
          and all(fc.values()) and res['flagship']['audit_identical'])
    res['ok'] = bool(ok)
    return res


def nc7(scratch):
    """NC7: a copy of the stored w_1e24 export with one interval endpoint altered must change the audit output / raise violations."""
    S = Path(scratch); S.mkdir(parents=True, exist_ok=True)
    src = DIAG / 'zfast' / 'atlas_v5z4' / 'lean_audit' / 'v5z4_w_1e24.txt'
    lines = open(src).read().split('\n'); k = next(i for i, l in enumerate(lines) if l.startswith('IV '))
    p = lines[k].split(); num, den = p[1].split('/'); p[1] = f'{int(num) + 10 ** 6 * int(den)}/{den}'   # left endpoint moved by +1e6
    lines[k] = ' '.join(p); bad = S / 'v5z4_w_1e24_nc7.txt'; bad.write_text('\n'.join(lines))
    g, out = audit_files([bad], S / 'nc7_audit.out')
    stored = (DIAG / 'zfast' / 'atlas_v5z4' / 'lean_audit' / 'audit_v5z4_w_1e24.txt').read_bytes()
    m = re.search(rb'TOTAL VIOLATIONS \(non-control datasets\): (\d+)', out)
    return dict(control='NC7', changed_line=k, audit_rc=g['rc'], output_differs=out != stored,
                violations=int(m.group(1)) if m else None, detected=bool(out != stored and (m is None or int(m.group(1)) > 0)))
