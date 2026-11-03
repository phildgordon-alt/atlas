"""engine/regress_v1 CLI.

  python -m engine.regress_v1 --freeze                 write FROZEN.json once (sha snapshot of every frozen certificate file)
  python -m engine.regress_v1 --tier 0                 integrity + stored-data re-verification of every family (minutes)
  python -m engine.regress_v1 --tier 1                 sampled regeneration (Z1, Z-X, G1, L1, K1)
  python -m engine.regress_v1 --controls               the pre-registered negative controls NC1-NC7 (each must FAIL)
  python -m engine.regress_v1 --list-tier2             list the expensive regenerations (never run by default)
Options: --only SUBSTR (restrict zfast runs), --tag T (tier-1 run tag, default r<timestamp>).
Writes engine/regress_v1/reports/<kind>_<stamp>.{json,md}.  Exit 0 iff every check passed (controls: iff every control was detected)."""
import argparse, json, os, shutil, sys, time
from pathlib import Path
from .common import HERE, WORK, RegressError, guard, canon, canon_sha, sha256
from . import zfast, integrity, lean, others

REPORTS = HERE / 'reports'
GOLDEN = HERE / 'GOLDEN_v1.json'
PREREG_SHA = '80774906223b4f8e59c96633191377c646fd8c322daf5645a7be75b2419ecabd'


def _stamp(): return time.strftime('%Y%m%d_%H%M%S')


def _check_prereg():
    if sha256(HERE / 'PREREG.md') != PREREG_SHA: raise RegressError('PREREG.md changed after registration (sha mismatch)')


def tier0(a, stamp):
    t0 = time.time(); S = WORK / f't0_{stamp}'; rep = dict(kind='tier0', stamp=stamp, prereg_sha256=PREREG_SHA, sections={})
    ts = time.time(); fr = integrity.check_frozen(); fr['seconds'] = round(time.time() - ts, 1); fr['ok'] = fr['n_mismatch'] == 0
    rep['sections']['frozen_integrity'] = fr
    ts = time.time(); mf = integrity.check_manifests(); mf['seconds'] = round(time.time() - ts, 1); mf['ok'] = mf['hard_mismatches'] == 0
    rep['sections']['historical_manifests'] = mf
    trees = [zfast.check_tree_freeze(t) for t in zfast.TREES]
    rep['sections']['zfast_tree_freeze'] = dict(trees=trees, ok=all(t['ok'] for t in trees))
    zr = []; gold = {}; ts = time.time()
    for r in zfast.runs():
        if a.only and a.only not in r['id']: continue
        res, g = zfast.tier0(r, S / 'zfast' / r['id'].replace('/', '_').replace(':', '_'))
        zr.append(res)
        if g is not None: gold[r['id']] = canon_sha(g)
        print(f"[t0 zfast] {r['id']:60s} ok={res['ok']} records={res.get('passed_records')}/{res.get('records')}", flush=True)
    rep['sections']['zfast_windows'] = dict(runs=zr, n=len(zr), passed=sum(x['ok'] for x in zr), ok=all(x['ok'] for x in zr), seconds=round(time.time() - ts, 1))
    if not a.only:
        ts = time.time(); L = lean.tier0(S / 'lean'); L['seconds'] = round(time.time() - ts, 1); rep['sections']['lean_audit'] = L
        gold['lean'] = canon_sha({k: v for k, v in L.items() if k not in ('seconds',)} | {'flagship': {k: v for k, v in L['flagship'].items() if k not in ('audit_seconds', 'audit_peak_gb')}})
        print(f"[t0 lean] ok={L['ok']}", flush=True)
        # A7 (F-M9a): Lean datasets of trees outside GOLDEN_v1 scope, skipped by lean.v5_datasets; reported here, outside the golden hash
        rep['lean_out_of_scope'] = [dict(d) for d in lean.SKIPPED_OUT_OF_SCOPE]
        print(f"[t0 lean] out of scope (gated by v5z5_gate/v5z6_gate/turing_gate): {[d['name'] for d in rep['lean_out_of_scope']]}", flush=True)
        ts = time.time(); A = others.artin_tier0(S / 'artin'); A['seconds'] = round(time.time() - ts, 1)
        gold['artin_sweep'] = canon_sha(A.pop('golden', None)); rep['sections']['artin_sweep'] = A
        print(f"[t0 artin] ok={A['ok']} theorem_C={A.get('theorem_C')} gaps={A.get('done_not_certified')}", flush=True)
    # golden identity (PREREG 1)
    if not a.only:
        if not GOLDEN.exists():
            json.dump(dict(created=stamp, prereg_sha256=PREREG_SHA, golden=gold), open(GOLDEN, 'w'), indent=1, sort_keys=True)
            rep['sections']['golden'] = dict(status='baseline written (first counted run)', entries=len(gold), ok=True)
        else:
            G = json.load(open(GOLDEN))['golden']; diff = sorted(k for k in set(G) | set(gold) if G.get(k) != gold.get(k))
            rep['sections']['golden'] = dict(status='compared', entries=len(gold), differing=diff, ok=not diff)
    rep['ok'] = all(v.get('ok') for v in rep['sections'].values()); rep['seconds'] = round(time.time() - t0, 1)
    return rep


def tier1(a, stamp):
    t0 = time.time(); tag = a.tag or f'r{stamp}'; rep = dict(kind='tier1', stamp=stamp, tag=tag, prereg_sha256=PREREG_SHA, sections={})
    z = []
    for r in zfast.runs():
        if zfast.tier_of(r) != 1 or (a.only and a.only not in r['id']): continue
        new, g, args = zfast.regenerate(r, tag)
        c = zfast.compare_regenerated(r, new) if new.exists() else dict(identical=False, error='no output')
        z.append(dict(id=r['id'], process=g, identical=c['identical'], compare=c, ok=bool(c['identical'] and g['rc'] == 0)))
        print(f"[t1 Z1] {r['id']:60s} identical={c['identical']} {g['seconds']}s", flush=True)
    rep['sections']['Z1'] = dict(runs=z, n=len(z), passed=sum(x['ok'] for x in z), ok=all(x['ok'] for x in z))
    if not a.only:
        rep['sections']['Z-X'] = zx(tag)
        print(f"[t1 Z-X] ok={rep['sections']['Z-X']['ok']}", flush=True)
        for f, key in ((others.g1, 'G1'), (others.l1, 'L1'), (others.k1, 'K1')):
            x = f(WORK / f't1_{stamp}' / key); rep['sections'][key] = x
            print(f"[t1 {key}] ok={x['ok']} {x['process']['seconds']}s", flush=True)
    rep['ok'] = all(v.get('ok') for v in rep['sections'].values()); rep['seconds'] = round(time.time() - t0, 1)
    return rep


def zx(tag):
    """Z-X: v5z4 (current production) code regenerates v5z3's x_1e16; compared with the frozen v5z3 files."""
    R = {r['id']: r for r in zfast.runs()}; src = R['atlas_v5z3:w10000000000000000/x_1e16']
    as_v5z4 = dict(src, tree='atlas_v5z4')
    new, g, args = zfast.regenerate(as_v5z4, tag + '_zx')
    c = zfast.compare_regenerated(src, new)
    old_p = json.load(open(Path(src['run']) / 'pieces.json')); new_p = json.load(open(new / 'pieces.json'))
    diff_keys = sorted(k for k in set(old_p) | set(new_p) if old_p.get(k) != new_p.get(k))
    ok = bool(g['rc'] == 0 and all(c[s]['canonical_identical'] == c[s]['frozen'] == c[s]['regenerated'] for s in ('certs', 'certs_np'))
              and c['zs.json']['canonical_identical'] and c['gen_measurements.json']['canonical_identical'] and diff_keys in ([], ['z_provider'])
              and c['replay_check']['identical'] and c['replay_records_identical'])
    return dict(id='Z-X v5z4 code on v5z3 x_1e16', process=g, compare=c, pieces_differing_keys=diff_keys, ok=ok)


def controls(a, stamp):
    S = WORK / f'nc_{stamp}'; out = []
    R = {r['id']: r for r in zfast.runs()}
    z12 = R['atlas_v5z:w1000000000000/z_1e12']; z24 = R['atlas_v5z4:w1000000000000000000000000/w_1e24']
    # NC1: 1-ulp tamper of a copy; integrity + golden must fail
    import math
    cp = S / 'NC1' / 'z_1e12'; shutil.copytree(z12['run'], cp, ignore=shutil.ignore_patterns('work', 'replay_check*'))
    shutil.copytree(Path(z12['run']) / 'replay_check_independent', cp / 'replay_check_independent')
    f = cp / 'certs' / 'cert_p0_100.json'; c = json.load(open(f)); c['y'][0] = math.nextafter(c['y'][0], math.inf); json.dump(c, open(f, 'w'))
    F = json.load(open(integrity.FROZEN))['files']; orig = str(Path(z12['run']) / 'certs' / 'cert_p0_100.json')
    sha_detect = F[orig]['sha256'] != sha256(f)
    r_copy = dict(z12, run=str(cp)); res, g = zfast.tier0(r_copy, S / 'NC1' / 't0')
    _, g0 = zfast.tier0(z12, S / 'NC1' / 't0_ref')
    golden_detect = canon_sha(g) != canon_sha(g0) if g is not None else True
    out.append(dict(control='NC1 1-ulp tampered y (copy)', sha_detected=sha_detect, golden_detected=golden_detect,
                    math_still_certifies=res['ok'], detected=bool(sha_detect and golden_detect)))
    for flag, name in (('--tamper-cert', 'NC2 w x 1.10'), ('--perturb-meas', 'NC3 Ehi - 1e-3'), ('--wrong-y', 'NC4 wrong y'),
                       ('--swap-interval', 'NC5 swapped zero interval')):
        for r in (z12, z24):
            res, _ = zfast.tier0(r, S / name.split()[0] / r['id'].split('/')[-1], control=flag)
            out.append(dict(control=f'{name} on {r["id"]}', passed_records=f"{res.get('passed_records')}/{res.get('records')}",
                            closed_A=res.get('geometry', {}).get('closed_A'), claim_B=res.get('geometry', {}).get('claim_B'),
                            detected=not res['ok']))
    # NC6: regeneration with zs_step x 2 must not be identical
    new, g, args = zfast.regenerate(z12, f'nc6_{stamp}', perturb='zs_step'); c = zfast.compare_regenerated(z12, new)
    out.append(dict(control='NC6 regeneration with zs_step x2 (z_1e12)', process=g, identical=c['identical'], detected=not c['identical']))
    # NC7: Lean
    out.append(lean.nc7(S / 'NC7'))
    for x in out: print(f"[NC] {x['control']:70s} detected={x['detected']}", flush=True)
    return dict(kind='controls', stamp=stamp, prereg_sha256=PREREG_SHA, controls=out, ok=all(x['detected'] for x in out))


def tier2_list():
    return [dict(id=r['id'], recorded_wall_s=r['recorded_wall'], recorded_closed=r['recorded_closed']) for r in zfast.runs() if zfast.tier_of(r) == 2]


def md(rep):
    L = [f"# regress_v1 {rep['kind']} {rep['stamp']}: {'PASS' if rep['ok'] else 'FAIL'}", '', f"prereg sha256 {rep['prereg_sha256']}", '']
    if rep['kind'] == 'controls':
        L += ['| control | detected |', '|---|---|'] + [f"| {x['control']} | {x['detected']} |" for x in rep['controls']]
        return '\n'.join(L) + '\n'
    for k, v in rep['sections'].items():
        L.append(f"## {k}: {'PASS' if v.get('ok') else 'FAIL'}")
        if k in ('zfast_windows', 'Z1'):
            L += ['| run | ok | detail |', '|---|---|---|']
            for x in v['runs']:
                det = (f"{x.get('passed_records')}/{x.get('records')} records; mcl {x.get('min_candidate_lower')}; same mcl as stored "
                       f"{x.get('stored_replay', {}).get('identical_min_candidate_lower')}/{x.get('stored_replay', {}).get('matched')}"
                       if k == 'zfast_windows' else f"{x['process']['seconds']} s; certs {x['compare']['certs']['canonical_identical']}/{x['compare']['certs']['frozen']}, np {x['compare']['certs_np']['canonical_identical']}/{x['compare']['certs_np']['frozen']}")
                L.append(f"| {x['id']} | {x['ok']} | {det} |")
        else:
            s = json.dumps({kk: vv for kk, vv in v.items() if kk not in ('detail', 'runs', 'golden')}, default=str)
            L.append('```\n' + (s[:3000] + (' ...' if len(s) > 3000 else '')) + '\n```')
        L.append('')
    L.append(f"total {rep['seconds']} s")
    return '\n'.join(L) + '\n'


def main():
    guard()
    ap = argparse.ArgumentParser(prog='python -m engine.regress_v1')
    ap.add_argument('--tier', type=int, choices=(0, 1)); ap.add_argument('--freeze', action='store_true')
    ap.add_argument('--controls', action='store_true'); ap.add_argument('--list-tier2', action='store_true')
    ap.add_argument('--only'); ap.add_argument('--tag')
    a = ap.parse_args(); _check_prereg(); stamp = _stamp(); REPORTS.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    if a.freeze: print(json.dumps(integrity.freeze())); return
    if a.list_tier2: print(json.dumps(tier2_list(), indent=1)); return
    if a.controls: rep = controls(a, stamp)
    elif a.tier == 0: rep = tier0(a, stamp)
    elif a.tier == 1: rep = tier1(a, stamp)
    else: ap.error('choose --tier 0|1, --controls, --freeze or --list-tier2')
    base = REPORTS / f"{rep['kind']}_{stamp}"
    json.dump(rep, open(str(base) + '.json', 'w'), indent=1, default=str); open(str(base) + '.md', 'w').write(md(rep))
    print(f"REPORT {base}.json / .md : {'PASS' if rep['ok'] else 'FAIL'}", flush=True)
    sys.exit(0 if rep['ok'] else 1)
