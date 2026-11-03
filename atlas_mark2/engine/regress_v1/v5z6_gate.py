"""engine/regress_v1 v5z6 / libzfast.v14 gate (new file; diagnostic/zfast/PREDICTIONS_M9.md).  Nothing in zfast.py / cli.py is changed: the
atlas_v5z6 tree is registered in zfast.TREES in memory only, by this module.
  python -m engine.regress_v1.v5z6_gate --identity        I: v14 vs the frozen libzfast.v13b dylib and vs ref13h (frozen v13b SOURCE + a state
                                                          hash): state hash, Z grid, Z balls, rows; D in {1,2,4}, W in {1,3,8}   (~10 min)
  python -m engine.regress_v1.v5z6_gate --w1e22 [--workers W]
                                                          G: v5z6 with wide_1e22's frozen session parameters (H 61, Delta 0.012, D 2)
                                                          regenerates atlas_v5z5 wide_1e22 identically                    (~15-30 min)
  python -m engine.regress_v1.v5z6_gate --ckpt            C: checkpoint/resume: test-hook exit and a real SIGKILL mid-session at 1e20,
                                                          resume -> identical state hash; a pipeline killed in its generator session
                                                          and resumed (--resume) gives the same window as an uninterrupted run (1e16)
Pass rules are in PREDICTIONS_M9.md section 2.  Writes engine/regress_v1/reports/v5z6_<kind>_<stamp>.json."""
import argparse, glob, json, os, signal, subprocess, sys, time
from pathlib import Path
from .common import HERE, WORK, PY, RegressError, guard, canon, sha256, guarded, env_base
from . import zfast
ZF = zfast.ZF
zfast.TREES.setdefault('atlas_v5z5', (ZF / 'atlas_v5z5', 'V5Z5_FREEZE.sha256'))     # in memory only
zfast.TREES.setdefault('atlas_v5z6', (ZF / 'atlas_v5z6', 'V5Z6_FREEZE.sha256'))     # in memory only
zfast.TREES.setdefault('atlas_v5z7', (ZF / 'atlas_v5z7', 'V5Z7_FREEZE.sha256'))     # in memory only (RESULTS_M9 F-M9b/c)
TREE = ['atlas_v5z6']   # --tree
REPORTS = HERE / 'reports'
PROBE = ZF / 'tools' / 'm9_probe.py'
LIB13 = ZF / 'bin' / 'libzfast.v13b.dylib'; LIB13_SHA = '82489d1a89e25bef117cd87f47d591d9426282c4b211f92ace12d097767dffca'
LIB14 = ZF / 'bin' / 'libzfast.v14.dylib'; LIB14_SHA = '7abaaa8aa0a913290cdb202a55d18c6c195130b20032614f3a60d07f0f10fa5b'
LIBREF = ZF / 'bin' / 'libzfast.ref13h.dylib'; LIBREF_SHA = 'd043813592f13072c0f71a03fb1aafc9d80f492d2875f3217112c7a3d175900c'
ALLOWED_PIECES_DIFF = {'z_provider', 'zfast_session'}


def _pins():
    for p, h in ((LIB13, LIB13_SHA), (LIB14, LIB14_SHA), (LIBREF, LIBREF_SHA)):
        if sha256(p) != h: raise RegressError(f'{p} sha mismatch')


def probe(lib, mode, T0, u0, H, Delta, D, W=0, ckpt='-', gu0=None, gstep=0.004, gn=1000, extra_env=None, tag='p'):
    gu0 = u0 - 0.9 * H if gu0 is None else gu0
    out = WORK / 'm9' / f'probe_{tag}_{mode}_{T0}_D{D}_W{W}_{time.strftime("%H%M%S")}.json'; out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [PY, '-B', str(PROBE), str(lib), mode, str(T0), repr(u0), repr(H), repr(Delta), '18', '12', str(D), str(W), str(ckpt), repr(gu0), repr(gstep), str(gn)]
    env = env_base(**(extra_env or {}))
    with open(out, 'w') as f:
        t0 = time.time(); p = subprocess.run(['nice', '-n', '19'] + cmd, env=env, stdout=f, stderr=subprocess.PIPE, text=True, timeout=7200)
    txt = open(out).read().strip().splitlines()
    rec = json.loads(txt[-1]) if txt else {}
    rec.update(rc=p.returncode, stderr=p.stderr[-400:], wall=round(time.time() - t0, 2), out=str(out))
    return rec


def _key(r): return (r.get('state_sha256'), r.get('grid', {}).get('sha256'), r.get('rows_sha256'), tuple(r.get('Z') or ()))


def gate_identity():
    _pins(); cases = []
    cfgs = [  # (T0, u0, H, Delta, D list, W list, run the frozen v13b dylib too)
        (10**12, 5.0, 91.0, 0.008, (1, 2, 4), (1, 3, 8), True),
        (10**16, 50.0, 61.0, 0.012, (1, 2, 4), (1, 3, 8), True),
        (10**16, 1.0, 4.0, 0.15, (2,), (1, 8), True),                 # legacy v5z4 session parameters
        (10**20, 50.0, 61.0, 0.012, (2,), (1, 3, 8), True),
        (10**20, 50.0, 61.0, 0.012, (4,), (8,), False),
    ]
    for T0, u0, H, Dl, Ds, Ws, with13 in cfgs:
        for D in Ds:
            ref = probe(LIBREF, 'ref13h', T0, u0, H, Dl, D, tag='I')
            c = dict(T0=str(T0), u0=u0, H=H, Delta=Dl, D=D, ref=dict(state=ref.get('state_sha256'), build=ref.get('build_wall'), rc=ref['rc']), v14=[])
            if with13 and D == Ds[0]:
                v13 = probe(LIB13, 'v13b', T0, u0, H, Dl, D, tag='I')
                c['v13b_dylib'] = dict(build=v13.get('build_wall'), rc=v13['rc'],
                                       grid_rows_Z_identical_to_ref=_key(v13)[1:] == _key(ref)[1:])
            for W in Ws:
                v = probe(LIB14, 'v14', T0, u0, H, Dl, D, W, tag='I')
                c['v14'].append(dict(W=W, build=v.get('build_wall'), cpu=v.get('cpu_user'), maxrss_mb=v.get('maxrss_mb'), rc=v['rc'],
                                     identical_to_ref=v['rc'] == 0 and _key(v) == _key(ref)))
            if T0 == 10**16 and H == 61.0 and D == 2:
                g = probe(LIB14, 'v14', T0, u0, H, Dl, D, 4, extra_env=dict(ZFAST14_GENERIC_KERNEL='1'), tag='Igen')
                c['v14_generic_kernel_W4_identical_to_ref'] = g['rc'] == 0 and _key(g) == _key(ref)
            c['ok'] = (ref['rc'] == 0 and all(x['identical_to_ref'] for x in c['v14']) and c.get('v13b_dylib', {}).get('grid_rows_Z_identical_to_ref', True)
                       and c.get('v14_generic_kernel_W4_identical_to_ref', True))
            cases.append(c); print(json.dumps(c), flush=True)
    # NC-I1: the hash must see the decomposition (D = 1 vs D = 2 at 1e16 must differ) and K (the probe's K is fixed: D differences suffice)
    s16 = {c['D']: c['ref']['state'] for c in cases if c['T0'] == str(10**16) and c['H'] == 61.0}
    nc = dict(NC_I1_D1_vs_D2_differ=s16.get(1) != s16.get(2) and None not in (s16.get(1), s16.get(2)))
    return dict(check='I: libzfast.v14 bit-identity with libzfast.v13b', cases=cases, controls=nc,
                ok=all(c['ok'] for c in cases) and all(nc.values()))


def gate_w1e22(tag, workers):
    fr = zfast.check_tree_freeze(TREE[0])
    if not fr['ok']: raise RegressError(f'{TREE[0]} tree differs from its FREEZE: {fr["mismatches"][:3]}')
    src = ZF / 'atlas_v5z5' / 'runs' / 'w10000000000000000000000' / 'wide_1e22'
    a = None
    for l in open(src / 'drive.jsonl'):
        x = json.loads(l)
        if x.get('stage') == 'start': a = x['args']; env0 = x['env']; break
    dst = zfast._copy_tree(TREE[0]); name = f"wide_1e22__{tag}"; new = dst / 'runs' / f"w{a['T0']}" / name
    if new.exists(): raise RegressError(f'{new} exists (never overwrite)')
    cmd = [PY, '-u', '-B', 'atlas_v5.py', str(a['T0']), a['tlo'], a['thi'], '--name', name, '--grid', a['grid'], '--evaluator', a['evaluator'],
           '--pw', repr(a['pw']), '--wm', repr(a['wm']), '--zs-step', repr(a['zs_step']), '--zs-refine', repr(a['zs_refine']),
           '--gen-timeout', '7000', '--wide', '--zfast-h', repr(a['zfast_h']), '--zfast-delta', repr(a['zfast_delta'])]
    extra = dict(ZFAST_THREADS=env0['ZFAST_THREADS'], ZFAST_WORKERS=workers, V4_LIM_GB=env0['V4_LIM_GB'])
    g = guarded(cmd, dst, WORK / 'logs' / f'v5z6_{name}.log', env=env_base(**extra), timeout=7200)
    c = zfast.compare_regenerated(dict(run=str(src)), new)
    old_p = json.load(open(src / 'pieces.json')); new_p = json.load(open(new / 'pieces.json')) if (new / 'pieces.json').exists() else {}
    diff_keys = sorted(k for k in set(old_p) | set(new_p) if old_p.get(k) != new_p.get(k))
    sess_core = {k: v for k, v in (new_p.get('zfast_session') or {}).items() if k in old_p['zfast_session']}
    summ = json.load(open(new / 'summary.json')) if (new / 'summary.json').exists() else {}
    ok = bool(g['rc'] == 0 and all(c[s]['canonical_identical'] == c[s]['frozen'] == c[s]['regenerated'] and c[s]['frozen'] > 0 for s in ('certs', 'certs_np'))
              and c['zs.json']['canonical_identical'] and c['gen_measurements.json']['canonical_identical'] and set(diff_keys) <= ALLOWED_PIECES_DIFF
              and sess_core == old_p['zfast_session'] and c['replay_check']['identical'] and c['replay_records_identical'])
    return dict(check='G: v5z6 (wide_1e22 frozen session parameters) regenerates atlas_v5z5 wide_1e22', frozen_run=str(src), regenerated=str(new),
                process=g, zfast_env=extra, compare=c, pieces_differing_keys=diff_keys, zfast_session_core_identical=sess_core == old_p['zfast_session'],
                new_zfast_session=new_p.get('zfast_session'), summary_wall=summ.get('wall_seconds'), generator_seconds=(summ.get('generator') or {}).get('seconds'),
                replay_seconds=(summ.get('replay') or {}).get('seconds'), ok=ok)


def _pipeline(dst, name, T0, lo, hi, extra, resume=False, log='x'):
    cmd = [PY, '-u', '-B', 'atlas_v5.py', str(T0), lo, hi, '--name', name, '--zs-step', '0.005', '--gen-timeout', '3000',
           '--wide', '--zfast-h', '91.0', '--zfast-delta', '0.008', '--turing-grid'] + (['--resume'] if resume else [])
    return guarded(cmd, dst, WORK / 'logs' / f'v5z6_{name}_{log}.log', env=env_base(**extra), timeout=3600)


def gate_ckpt(tag):
    _pins(); res = {}; T0 = 10**20; ck = WORK / 'm9' / f'ckpt_{tag}'; ck.mkdir(parents=True)
    base = probe(LIB14, 'v14', T0, 50.0, 61.0, 0.012, 2, 8, tag='Cbase')
    # C1: test hook exit after 120 items, then resume
    c1 = ck / 'c1.txt'
    e1 = probe(LIB14, 'v14', T0, 50.0, 61.0, 0.012, 2, 8, ckpt=c1, extra_env=dict(ZFAST14_TEST_EXIT_AFTER='120'), tag='C1a')
    r1 = probe(LIB14, 'v14', T0, 50.0, 61.0, 0.012, 2, 8, ckpt=c1, tag='C1b')
    res['C1 test-hook exit + resume'] = dict(exit_rc=e1['rc'], resumed_items_loaded=(r1.get('info') or {}).get('items_loaded'), items=(r1.get('info') or {}).get('items'),
                                            identical=r1['rc'] == 0 and _key(r1) == _key(base), resumed_build=r1.get('build_wall'), base_build=base.get('build_wall'))
    # C2: real SIGKILL once the checkpoint holds >= 300 lines, then resume with a different worker count
    c2 = ck / 'c2.txt'
    cmd = [PY, '-B', str(PROBE), str(LIB14), 'v14', str(T0), '50.0', '61.0', '0.012', '18', '12', '2', '8', str(c2), '-5.0', '0.004', '1000']
    p = subprocess.Popen(['nice', '-n', '19'] + cmd, env=env_base(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); t0 = time.time()
    while p.poll() is None and (not c2.exists() or sum(1 for _ in open(c2)) < 300) and time.time() - t0 < 600: time.sleep(0.2)
    lines_at_kill = sum(1 for _ in open(c2)) if c2.exists() else 0
    os.kill(p.pid, signal.SIGKILL) if p.poll() is None else None; p.wait()
    r2 = probe(LIB14, 'v14', T0, 50.0, 61.0, 0.012, 2, 3, ckpt=c2, tag='C2b')
    res['C2 SIGKILL + resume (W 8 -> 3)'] = dict(killed_rc=p.returncode, lines_at_kill=lines_at_kill, resumed_items_loaded=(r2.get('info') or {}).get('items_loaded'),
                                                 identical=r2['rc'] == 0 and _key(r2) == _key(base))
    # C3 (control): a checkpoint of a different session must be refused
    r3 = probe(LIB14, 'v14', T0, 50.0, 60.0, 0.012, 2, 8, ckpt=c1, tag='C3')
    res['C3 control: foreign checkpoint refused'] = dict(rc=r3['rc'], refused=r3['rc'] != 0 and r3.get('ok') is False)
    # C4: pipeline-level: generator killed mid-session (test hook), driver --resume, vs an uninterrupted run (1e16, target [0, 10])
    fr = zfast.check_tree_freeze(TREE[0])
    if not fr['ok']: raise RegressError('atlas_v5z6 tree differs from V5Z6_FREEZE')
    dst = zfast._copy_tree(TREE[0]); T16 = 10**16; lo, hi = str(T16), str(T16 + 10)
    ext = dict(ZFAST_THREADS='2', ZFAST_WORKERS='4', V4_LIM_GB='1.0')
    gA = _pipeline(dst, f'ck16_ref_{tag}', T16, lo, hi, ext, log='ref')
    gB1 = _pipeline(dst, f'ck16_res_{tag}', T16, lo, hi, dict(ext, ZFAST14_TEST_EXIT_AFTER='200'), log='kill')
    runB = dst / 'runs' / f'w{T16}' / f'ck16_res_{tag}'
    gl = [json.loads(l) for l in open(runB / 'gen.jsonl')] if (runB / 'gen.jsonl').exists() else []
    killed_ok = not (runB / 'zs.json').exists() and not any(x.get('stage') == 'gen_done' for x in gl)
    # v5z6 refuses a resume with another ZFAST_WORKERS (F-M9b, fail-safe); v5z7 must accept it
    gB2 = _pipeline(dst, f'ck16_res_{tag}', T16, lo, hi, ext if TREE[0] == 'atlas_v5z6' else dict(ext, ZFAST_WORKERS='8'), resume=True, log='resume')
    runA = dst / 'runs' / f'w{T16}' / f'ck16_ref_{tag}'
    c = zfast.compare_regenerated(dict(run=str(runA)), runB)
    gridsame = all(sha256(runA / 'turing_grid' / f) == sha256(runB / 'turing_grid' / f) for f in ('grid.npz', 'zeros_intervals.json'))
    attempts = sorted(os.path.basename(x) for x in glob.glob(str(runB / '*.attempt*')))
    ckl = sum(1 for _ in open(runB / 'zfast_ckpt_gen.txt'))
    res['C4 pipeline: generator killed in its session, --resume'] = dict(ref_rc=gA['rc'], killed_rc=gB1['rc'], killed_before_zs=killed_ok, resume_rc=gB2['rc'],
                                                                       renamed=attempts, ckpt_lines=ckl, compare=c, turing_grid_identical=gridsame,
                                                                       identical=gA['rc'] == 0 and gB2['rc'] == 0 and killed_ok and c['identical'] and gridsame)
    ok = (res['C1 test-hook exit + resume']['identical'] and res['C1 test-hook exit + resume']['exit_rc'] == 77
          and res['C2 SIGKILL + resume (W 8 -> 3)']['identical'] and res['C2 SIGKILL + resume (W 8 -> 3)']['lines_at_kill'] >= 300
          and res['C3 control: foreign checkpoint refused']['refused'] and res['C4 pipeline: generator killed in its session, --resume']['identical'])
    return dict(check='C: checkpoint/resume identity', base=dict(state=base.get('state_sha256'), build=base.get('build_wall')), results=res, ok=ok)


def main():
    guard()
    ap = argparse.ArgumentParser(prog='python -m engine.regress_v1.v5z6_gate')
    ap.add_argument('--identity', action='store_true'); ap.add_argument('--w1e22', action='store_true'); ap.add_argument('--ckpt', action='store_true')
    ap.add_argument('--workers', default='8'); ap.add_argument('--tag'); ap.add_argument('--tree', default='atlas_v5z6', choices=('atlas_v5z6', 'atlas_v5z7'))
    a = ap.parse_args(); TREE[0] = a.tree; stamp = time.strftime('%Y%m%d_%H%M%S'); tag = a.tag or f'{a.tree[6:]}_{stamp}'; REPORTS.mkdir(exist_ok=True)
    if a.identity: rep, kind = gate_identity(), 'identity'
    elif a.w1e22: rep, kind = gate_w1e22(tag, a.workers), 'w1e22'
    elif a.ckpt: rep, kind = gate_ckpt(tag), 'ckpt'
    else: ap.error('choose --identity, --w1e22 or --ckpt')
    rep.update(tree=TREE[0], stamp=stamp, predictions='diagnostic/zfast/PREDICTIONS_M9.md (sha in PREDICTIONS_M9.sha256)')
    p = REPORTS / f'v5z6_{kind}_{stamp}.json'; json.dump(rep, open(p, 'w'), indent=1, default=str)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('cases', 'results', 'compare', 'process')}, default=str, indent=1)[:3000])
    print(f'REPORT {p}: {"PASS" if rep["ok"] else "FAIL"}', flush=True)
    sys.exit(0 if rep['ok'] else 1)


if __name__ == '__main__':
    main()
