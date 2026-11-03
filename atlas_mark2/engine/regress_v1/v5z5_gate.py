"""engine/regress_v1 v5z5 gate (new file; PREDICTIONS_M7.md section 1, sha 34b28157...).  Nothing in zfast.py / cli.py is changed: the
atlas_v5z5 tree is registered in zfast.TREES in memory only, by this module.

  python -m engine.regress_v1.v5z5_gate --strict     G4: strict-mode unit checks of the v5z5 provider (10^12 sessions, seconds)
  python -m engine.regress_v1.v5z5_gate --zx         G2: v5z5 code (legacy mode) regenerates v5z3 x_1e16           (~1 min)
  python -m engine.regress_v1.v5z5_gate --w1e22      G3: v5z5 code (legacy mode) regenerates v5z4 w_1e22  (tier 2, ~32 min)
  python -m engine.regress_v1.v5z5_gate --controls RUN   NC-W1..NC-W4 on a finished v5z5 run (stored data, copies only)

Pass rule (G2, G3): every certs/ and certs_np/ file canonically identical (volatile gen_seconds), zs.json and gen_measurements.json
canonically identical, pieces.json differing only in keys within {z_provider, zfast_session}, replay_check results and replay records
identical.  Writes engine/regress_v1/reports/v5z5_<kind>_<stamp>.json."""
import argparse, copy, glob, json, os, shutil, subprocess, sys, time
from pathlib import Path
from .common import HERE, WORK, PY, RegressError, guard, canon, sha256, guarded, env_base
from . import zfast

ZF = zfast.ZF
zfast.TREES.setdefault('atlas_v5z5', (ZF / 'atlas_v5z5', 'V5Z5_FREEZE.sha256'))     # in memory only
ALLOWED_PIECES_DIFF = {'z_provider', 'zfast_session'}
REPORTS = HERE / 'reports'


def _regen_v5z5(src, tag, center, threads=2, timeout=7200):
    """regenerate the frozen window `src` (a zfast.runs() record) with v5z5 code in legacy mode, recorded env (centre, threads)."""
    fr = zfast.check_tree_freeze('atlas_v5z5')
    if not fr['ok']: raise RegressError(f'atlas_v5z5 tree differs from V5Z5_FREEZE: {fr["mismatches"][:3]}')
    dst = zfast._copy_tree('atlas_v5z5'); a = dict(zfast._original_args(src))
    name = f"{a['name']}__{tag}"; sub = f"w{a['T0']:.2f}" if a['grid'] == 'v4' else f"w{a['T0']}"
    new = dst / 'runs' / sub / name
    if new.exists(): raise RegressError(f'{new} exists (never overwrite); use a new tag')
    cmd = [PY, '-u', '-B', 'atlas_v5.py', str(a['T0']), a['tlo'], a['thi'], '--name', name, '--grid', a['grid'], '--evaluator', a['evaluator'],
           '--pw', repr(a['pw']), '--wm', repr(a['wm']), '--zs-step', repr(a['zs_step']), '--zs-refine', repr(a['zs_refine']),
           '--gen-timeout', str(timeout - 300)]
    extra = dict(ZFAST_THREADS=threads)
    if center is not None: extra['ZFAST_CENTER'] = center
    g = guarded(cmd, dst, WORK / 'logs' / f'v5z5_{name}.log', env=env_base(**extra), timeout=timeout)
    g['zfast_env'] = extra
    return new, g


def _judge(src, new, g):
    c = zfast.compare_regenerated(src, new)
    old_p = json.load(open(Path(src['run']) / 'pieces.json')); new_p = json.load(open(new / 'pieces.json')) if (new / 'pieces.json').exists() else {}
    diff_keys = sorted(k for k in set(old_p) | set(new_p) if old_p.get(k) != new_p.get(k))
    ok = bool(g['rc'] == 0 and all(c[s]['canonical_identical'] == c[s]['frozen'] == c[s]['regenerated'] and c[s]['frozen'] > 0 for s in ('certs', 'certs_np'))
              and c['zs.json']['canonical_identical'] and c['gen_measurements.json']['canonical_identical'] and set(diff_keys) <= ALLOWED_PIECES_DIFF
              and c['replay_check']['identical'] and c['replay_records_identical'])
    return dict(frozen_run=src['id'], regenerated=str(new), process=g, compare=c, pieces_differing_keys=diff_keys,
                new_zfast_session=new_p.get('zfast_session'), ok=ok)


def gate_zx(tag):
    R = {r['id']: r for r in zfast.runs()}
    return dict(check='G2 v5z5 (legacy) regenerates v5z3 x_1e16', **_judge(R['atlas_v5z3:w10000000000000000/x_1e16'],
                *_regen_v5z5(R['atlas_v5z3:w10000000000000000/x_1e16'], tag + '_g2', '1.0', timeout=3600)))


def gate_w1e22(tag):
    R = {r['id']: r for r in zfast.runs()}; src = R['atlas_v5z4:w10000000000000000000000/w_1e22']
    # recorded env: atlas_v5z4/run_y34.sh exports ZFAST_THREADS=2 and passes centre 1.0 to run_window.sh (ZFAST_CENTER)
    return dict(check='G3 v5z5 (legacy) regenerates v5z4 w_1e22 (tier 2)', **_judge(src, *_regen_v5z5(src, tag + '_g3', '1.0', threads=2, timeout=7200)))


STRICT_PROBE = r'''
import os, sys, json
sys.path.insert(0, sys.argv[1]); case = sys.argv[2]
import zfast_provider as P
T0 = 10**12
try:
    if case == 'outside': P.Zball(T0, 0.5); P.Zball(T0, 10.0)
    elif case == 'second':
        P._S[(T0, 99.0)] = object(); P.Zball(T0, 0.5)
    elif case == 'ok': v = P.Zball(T0, 0.5); print(json.dumps(dict(ok=True, Z=str(v), cfg=P.config(), stats=P.STATS))); sys.exit(0)
    print(json.dumps(dict(raised=False))); sys.exit(3)
except RuntimeError as e:
    print(json.dumps(dict(raised=True, error=str(e)))); sys.exit(0)
'''


def gate_strict():
    fr = zfast.check_tree_freeze('atlas_v5z5')
    if not fr['ok']: raise RegressError('atlas_v5z5 tree differs from V5Z5_FREEZE')
    lib = str(ZF / 'atlas_v5z5' / 'lib'); out = []
    base = env_base(ZFAST_THREADS=1, ZFAST_STRICT='1', ZFAST_CENTER='0.0', ZFAST_H='4.0', ZFAST_DELTA='0.15')
    def run(case, env, flags=()):
        p = subprocess.run([PY, '-B', *flags, '-c', STRICT_PROBE, lib, case], env=env, capture_output=True, text=True, timeout=300)
        return p.returncode, (p.stdout.strip().splitlines() or [''])[-1], p.stderr.strip()[-300:]
    rc, o, e = run('ok', base); out.append(dict(case='strict mode, point inside', rc=rc, out=o, expect='value', ok=rc == 0 and '"ok": true' in o))
    rc, o, e = run('outside', base); out.append(dict(case='point outside session', rc=rc, out=o, expect='raise', ok=rc == 0 and '"raised": true' in o))
    rc, o, e = run('second', base); out.append(dict(case='second session', rc=rc, out=o, expect='raise', ok=rc == 0 and '"raised": true' in o))
    nc = dict(base); nc.pop('ZFAST_CENTER')
    rc, o, e = run('ok', nc); out.append(dict(case='strict without centre', rc=rc, err=e, expect='refuse at import', ok=rc != 0 and 'ZFAST_CENTER is required' in e))
    rc, o, e = run('ok', dict(base, PYTHONOPTIMIZE='1')); out.append(dict(case='PYTHONOPTIMIZE=1', rc=rc, err=e, expect='refuse', ok=rc != 0 and 'PYTHONOPTIMIZE' in e))
    rc, o, e = run('ok', base, ('-O',)); out.append(dict(case='python -O', rc=rc, err=e, expect='refuse', ok=rc != 0 and 'PYTHONOPTIMIZE' in e))
    return dict(check='G4 strict-mode unit checks', cases=out, ok=all(x['ok'] for x in out))


def _t0_worker(tree, run, out, flag=None):
    cmd = [PY, '-B', str(HERE / 'zfast_t0_worker.py'), str(tree), str(run), str(out)] + ([flag] if flag else [])
    g = guarded(cmd, HERE, WORK / 'logs' / f'v5z5_nc_{Path(out).stem}.log', env=env_base(), timeout=3600)
    recs = json.load(open(out))['records'] if Path(out).exists() else []
    main = [r for r in recs if r['mode'] == 'main']
    by = {}
    for r in main: by.setdefault(r['cert'], []).append(r['passed'])
    return dict(process=g, records=len(recs), passed=sum(r['passed'] for r in recs), main_records=len(main),
                main_passed=sum(r['passed'] for r in main), main_certs_failing_both=sum(1 for v in by.values() if not any(v)),
                main_certs_failing_any=sum(1 for v in by.values() if not all(v)), main_certs=len(by))


def controls(run, stamp):
    run = Path(run).resolve(); tree = ZF / 'atlas_v5z5'; S = WORK / f'v5z5_nc_{stamp}'; S.mkdir(parents=True)
    res = {}
    res['baseline'] = _t0_worker(tree, run, S / 'baseline.json')
    res['NC-W1 w x 1.10'] = _t0_worker(tree, run, S / 'ncw1.json', '--tamper-cert')
    res['NC-W2 swapped interval'] = _t0_worker(tree, run, S / 'ncw2.json', '--swap-interval')
    def copy_run(name):
        d = S / name; d.mkdir()
        for f in ('pieces.json', 'gen_measurements.json'): shutil.copy2(run / f, d / f)
        shutil.copytree(run / 'certs', d / 'certs'); (d / 'certs_np').mkdir()
        return d
    d3 = copy_run('ncw3')
    for f in sorted((d3 / 'certs').glob('cert_*.json')):
        c = json.load(open(f)); c['w'] = [float(v) * (1 + 1e-3) for v in c['w']]; json.dump(c, open(f, 'w'))
    res['NC-W3 w x (1+1e-3)'] = _t0_worker(tree, d3, S / 'ncw3.json')
    d4 = copy_run('ncw4'); f4 = sorted((d4 / 'certs').glob('cert_*.json'))[len(list((d4 / 'certs').glob('cert_*.json'))) // 2]
    c = json.load(open(f4)); x0, x1 = c['regions'][0][:2]
    k = next(i for i, (a, b) in enumerate(c['zs_intervals']) if x0 <= a and b <= x1)
    deleted = c['zs_intervals'][k]; del c['zs_intervals'][k]; del c['w'][k]; json.dump(c, open(f4, 'w'))
    res['NC-W4 deleted interval'] = dict(_t0_worker(tree, d4, S / 'ncw4.json'), cert=f4.name, deleted=deleted)
    # count check for NC-W4: certified sign changes inside the target from the mutated main certificates
    P = json.load(open(run / 'pieces.json')); ulo, uhi = P['target']
    def count(d):
        iv = set()
        for f in sorted((d / 'certs').glob('cert_*.json')):
            for a, b in json.load(open(f))['zs_intervals']:
                if ulo <= a and b <= uhi: iv.add((a, b))
        return len(iv)
    res['NC-W4 deleted interval']['count_original'] = count(run); res['NC-W4 deleted interval']['count_mutated'] = count(d4)
    b = res['baseline']
    det = {'NC-W1 w x 1.10': res['NC-W1 w x 1.10']['main_passed'] == 0,
           'NC-W2 swapped interval': res['NC-W2 swapped interval']['main_certs_failing_any'] >= 1,
           'NC-W3 w x (1+1e-3)': res['NC-W3 w x (1+1e-3)']['main_certs_failing_both'] >= 1,
           'NC-W4 deleted interval': (res['NC-W4 deleted interval']['main_passed'] < res['NC-W4 deleted interval']['main_records']) or
                                     (res['NC-W4 deleted interval']['count_mutated'] != res['NC-W4 deleted interval']['count_original'])}
    return dict(check='NC-W controls on ' + str(run), results=res, detected=det,
                baseline_ok=b['passed'] == b['records'] and b['records'] > 0, ok=all(det.values()) and b['passed'] == b['records'])


def main():
    guard()
    ap = argparse.ArgumentParser(prog='python -m engine.regress_v1.v5z5_gate')
    ap.add_argument('--zx', action='store_true'); ap.add_argument('--w1e22', action='store_true'); ap.add_argument('--strict', action='store_true')
    ap.add_argument('--controls'); ap.add_argument('--tag')
    a = ap.parse_args(); stamp = time.strftime('%Y%m%d_%H%M%S'); tag = a.tag or f'v5z5_{stamp}'; REPORTS.mkdir(exist_ok=True)
    if a.strict: rep, kind = gate_strict(), 'strict'
    elif a.zx: rep, kind = gate_zx(tag), 'zx'
    elif a.w1e22: rep, kind = gate_w1e22(tag), 'w1e22'
    elif a.controls: rep, kind = controls(a.controls, stamp), 'controls'
    else: ap.error('choose --strict, --zx, --w1e22 or --controls RUN')
    rep.update(stamp=stamp, predictions='diagnostic/zfast/PREDICTIONS_M7.md sha 34b281570dc2415757d5d3d93f1331031c3d30c48a585c4dca7fa31f58d3c5b6')
    p = REPORTS / f'v5z5_{kind}_{stamp}.json'; json.dump(rep, open(p, 'w'), indent=1, default=str)
    print(json.dumps({k: v for k, v in rep.items() if k in ('check', 'ok', 'pieces_differing_keys', 'detected', 'cases')}, default=str, indent=1))
    print(f'REPORT {p}: {"PASS" if rep["ok"] else "FAIL"}', flush=True)
    sys.exit(0 if rep['ok'] else 1)


if __name__ == '__main__':
    main()
