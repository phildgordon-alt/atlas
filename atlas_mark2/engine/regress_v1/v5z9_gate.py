"""engine/regress_v1 v5z9 / libzfast.v14c gate (new file; diagnostic/zfast/PREDICTIONS_M13.md) = v5z8_gate.py with v14c / atlas_v5z9 /
tools/m13_probe.py (mode v14c), WORK/m13, the G2 generator verify check (default 64, review_v14b mn7) and the I2 fsync measurement
(max_unsynced_s, mn2).  Nothing in zfast.py / cli.py / v5z6_gate.py / v5z8_gate.py is changed: atlas_v5z9 is registered in
zfast.TREES in memory only, by this module.  v5z8_gate docstring follows (read v14b as v14c, v5z8 as v5z9, M12 as M13).
  python -m engine.regress_v1.v5z8_gate --identity     I1: v14b vs v14 (state hash, Z grid bytes, rows, Z strings); T in 1e12..1e20,
                                                         D in {1,2,3,5,7}, W in {1,3,8}; plus 1e16 legacy (H 4, Delta 0.15)
  python -m engine.regress_v1.v5z8_gate --ckpt         I2 (fresh checkpoint = no checkpoint), I3a (SIGKILL at 1e20 + resume W 8 -> 3),
                                                         I3b (test-hooks exit + resume), I4 (generic kernel), cost (v14 vs v14b checkpointed
                                                         build at 1e20), G2 (v5z8 pipeline 1e16: generator SIGKILLed in its session, --resume)
  python -m engine.regress_v1.v5z8_gate --n13          N13: generator checkpoint copied over the replay path before stage 3 (1e12 smoke):
                                                         v5z7 replay loads it silently; v5z8 replay refuses (window not closed)
  python -m engine.regress_v1.v5z8_gate --w1e22        G1: v5z8 regenerates atlas_v5z5 wide_1e22 (v5z6_gate.gate_w1e22 on the v5z8 tree)
Writes engine/regress_v1/reports/v5z8_<kind>_<stamp>.json."""
import argparse, glob, json, os, shutil, signal, subprocess, sys, time
from pathlib import Path
from .common import HERE, WORK, PY, RegressError, guard, sha256, guarded, env_base
from . import zfast
from . import v5z6_gate as G6
ZF = zfast.ZF
zfast.TREES.setdefault('atlas_v5z7', (ZF / 'atlas_v5z7', 'V5Z7_FREEZE.sha256'))     # in memory only
zfast.TREES.setdefault('atlas_v5z9', (ZF / 'atlas_v5z9', 'V5Z9_FREEZE.sha256'))     # in memory only (PREDICTIONS_M13)
REPORTS = HERE / 'reports'
PROBE = ZF / 'tools' / 'm13_probe.py'
LIB14 = ZF / 'bin' / 'libzfast.v14.dylib'; LIB14_SHA = '7abaaa8aa0a913290cdb202a55d18c6c195130b20032614f3a60d07f0f10fa5b'
LIB14B = ZF / 'bin' / 'libzfast.v14c.dylib'; LIB14B_SHA = '59883f5e2d83585b67c08a2e3816d180248cd760c705642f13b571b71ad37471'      # (name kept: the library under test, v14c)
LIBTH = ZF / 'bin' / 'libzfast.v14c_testhooks.dylib'; LIBTH_SHA = '9c0d4a9be470682b806688f4934c68c29e8df3754d5243781b54a351ddfd4a46'
HOOKS = ('ZFAST14_TEST', 'ZFAST14B_TEST', 'ZFAST14C_TEST', 'ZFAST14_GENERIC_KERNEL')


def _pins():
    for p, h in ((LIB14, LIB14_SHA), (LIB14B, LIB14B_SHA), (LIBTH, LIBTH_SHA)):
        if sha256(p) != h: raise RegressError(f'{p} sha mismatch')


def _env(extra=None):
    e = {k: v for k, v in env_base().items() if not k.startswith(HOOKS)}; e.update({k: str(v) for k, v in (extra or {}).items()})
    return e


def probe(lib, mode, T0, u0, H, Delta, D, W, ckpt='-', role='gen', nonce='c' * 32, key='-', vn=8, gn=1000, extra_env=None, tag='p'):
    out = WORK / 'm13' / f'probe_{tag}_{mode}_{T0}_D{D}_W{W}_{time.strftime("%H%M%S")}_{os.getpid()}.json'; out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [PY, '-B', str(PROBE), str(lib), mode, str(T0), repr(u0), repr(H), repr(Delta), '18', '12', str(D), str(W), str(ckpt),
           repr(u0 - 0.9 * H), '0.004', str(gn), role, nonce, str(key), str(vn)]
    with open(out, 'w') as f:
        t0 = time.time(); p = subprocess.run(['nice', '-n', '19'] + cmd, env=_env(extra_env), stdout=f, stderr=subprocess.PIPE, text=True, timeout=7200)
    txt = open(out).read().strip().splitlines()
    rec = json.loads(txt[-1]) if txt else {}
    rec.update(rc=p.returncode, stderr=p.stderr[-400:], wall=round(time.time() - t0, 2), out=str(out))
    return rec


def _key(r): return (r.get('state_sha256'), (r.get('grid') or {}).get('sha256'), r.get('rows_sha256'), tuple(r.get('Z') or ()))


def gate_identity():
    _pins(); cases = []
    cfgs = [(10**12, 50.0, 61.0, 0.012), (10**14, 50.0, 61.0, 0.012), (10**16, 50.0, 61.0, 0.012), (10**18, 50.0, 61.0, 0.012), (10**20, 50.0, 61.0, 0.012)]
    for T0, u0, H, Dl in cfgs:
        for D in (1, 2, 3, 5, 7):
            ref = probe(LIB14, 'v14', T0, u0, H, Dl, D, 8, tag='I1')
            c = dict(T0=str(T0), H=H, Delta=Dl, D=D, v14=dict(state=ref.get('state_sha256'), build=ref.get('build_wall'), rc=ref['rc']), v14c=[])
            for W in (1, 3, 8):
                v = probe(LIB14B, 'v14c', T0, u0, H, Dl, D, W, tag='I1')
                c['v14c'].append(dict(W=W, build=v.get('build_wall'), rc=v['rc'], identical=v['rc'] == 0 and ref['rc'] == 0 and _key(v) == _key(ref)))
            c['ok'] = all(x['identical'] for x in c['v14c']); cases.append(c); print(json.dumps(c), flush=True)
    for W in (1, 8):     # legacy v5z4 session parameters
        ref = probe(LIB14, 'v14', 10**16, 1.0, 4.0, 0.15, 2, W, tag='I1L'); v = probe(LIB14B, 'v14c', 10**16, 1.0, 4.0, 0.15, 2, W, tag='I1L')
        c = dict(T0=str(10**16), H=4.0, Delta=0.15, D=2, W=W, ok=ref['rc'] == 0 and v['rc'] == 0 and _key(v) == _key(ref)); cases.append(c); print(json.dumps(c), flush=True)
    s16 = {c['D']: c['v14']['state'] for c in cases if c['T0'] == str(10**16) and c['H'] == 61.0 and 'v14' in c}
    nc = dict(NC_D1_vs_D2_differ=s16.get(1) != s16.get(2) and None not in (s16.get(1), s16.get(2)))
    return dict(check='I1: libzfast.v14c bit-identity with libzfast.v14', cases=cases, controls=nc, ok=all(c['ok'] for c in cases) and all(nc.values()))


def _lines(p): return sum(1 for _ in open(p)) if os.path.exists(p) else 0


def _pipeline(dst, name, T0, lo, hi, extra, resume=False, log='x', popen=False):
    cmd = [PY, '-u', '-B', 'atlas_v5.py', str(T0), lo, hi, '--name', name, '--zs-step', '0.005', '--gen-timeout', '3000',
           '--wide', '--zfast-h', '91.0', '--zfast-delta', '0.008', '--turing-grid'] + (['--resume'] if resume else [])
    if popen:
        (WORK / 'logs').mkdir(parents=True, exist_ok=True)
        lf = open(WORK / 'logs' / f'v5z9_{name}_{log}.log', 'a')
        return subprocess.Popen(['nice', '-n', '19'] + cmd, cwd=str(dst), env=_env(extra), stdout=lf, stderr=subprocess.STDOUT)
    return guarded(cmd, dst, WORK / 'logs' / f'v5z9_{name}_{log}.log', env=_env(extra), timeout=3600)


def gate_ckpt(tag):
    _pins(); res = {}; ck = WORK / 'm13' / f'ckpt_{tag}'; ck.mkdir(parents=True); kd = ck / 'keys'; kd.mkdir(mode=0o700)
    T20 = 10**20; A = (T20, 50.0, 61.0, 0.012)
    nonce = 'd' * 32; kp = lambda n: str(kd / f'{n}.key')
    # I2: fresh checkpoint, uninterrupted == no checkpoint (v14 reference)
    r14 = probe(LIB14, 'v14', *A, 2, 8, tag='I2ref'); r14_14 = probe(LIB14, 'v14', 10**14, 50.0, 61.0, 0.012, 2, 1, tag='I2ref14')
    b20 = probe(LIB14B, 'v14c', *A, 2, 8, ckpt=ck / 'i2_20.txt', nonce=nonce, key=kp('i2_20'), tag='I2')
    b14 = probe(LIB14B, 'v14c', 10**14, 50.0, 61.0, 0.012, 2, 1, ckpt=ck / 'i2_14.txt', nonce=nonce, key=kp('i2_14'), tag='I2')
    res['I2 fresh checkpoint == no checkpoint'] = dict(e20=b20['rc'] == 0 and _key(b20) == _key(r14), e14=b14['rc'] == 0 and _key(b14) == _key(r14_14),
                                                      written20=(b20.get('info') or {}).get('lines_written'), items20=(b20.get('info') or {}).get('items'),
                                                      syncs20=(b20.get('info') or {}).get('ckpt_syncs'), max_unsynced_s20=(b20.get('info') or {}).get('max_unsynced_s'),
                                                      sec_fast20=(b20.get('info') or {}).get('sec_fast'))
    # cost: v14 with a checkpoint vs v14b with a checkpoint at 1e20 D 2 W 8
    c14 = probe(LIB14, 'v14', *A, 2, 8, ckpt=ck / 'cost14.txt', tag='cost')
    res['cost 1e20 D2 W8 (checkpointed build seconds)'] = dict(v14=c14.get('build_wall'), v14b=b20.get('build_wall'),
                                                              ratio=round(b20['build_wall'] / c14['build_wall'], 4) if c14.get('build_wall') else None)
    # I3a: real SIGKILL once >= 300 lines, resume with W 3
    c2 = ck / 'i3a.txt'
    cmd = [PY, '-B', str(PROBE), str(LIB14B), 'v14c', str(T20), '50.0', '61.0', '0.012', '18', '12', '2', '8', str(c2), '-5.0', '0.004', '1000', 'gen', nonce, kp('i3a'), '8']
    p = subprocess.Popen(['nice', '-n', '19'] + cmd, env=_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); t0 = time.time()
    while p.poll() is None and _lines(c2) < 300 and time.time() - t0 < 900: time.sleep(0.2)
    nk = _lines(c2); os.kill(p.pid, signal.SIGKILL) if p.poll() is None else None; p.wait()
    t1 = time.time(); r2 = probe(LIB14B, 'v14c', *A, 2, 3, ckpt=c2, nonce=nonce, key=kp('i3a'), tag='I3a'); tres = time.time() - t1
    i2 = r2.get('info') or {}
    res['I3a SIGKILL + resume (W 8 -> 3)'] = dict(killed_rc=p.returncode, lines_at_kill=nk, loaded=i2.get('items_loaded'), verified=i2.get('verified'),
                                                 rejected=i2.get('lines_rejected'), resume_wall=round(tres, 1),
                                                 identical=r2['rc'] == 0 and _key(r2) == _key(r14) and (i2.get('items_loaded') or 0) >= 290 and i2.get('verified') == 8)
    # I3b: test-hooks lib exit after 120 items, resume with the same lib
    th_ref = probe(LIBTH, 'v14c', *A, 2, 8, tag='I3bref')
    c3 = ck / 'i3b.txt'
    e3 = probe(LIBTH, 'v14c', *A, 2, 8, ckpt=c3, nonce=nonce, key=kp('i3b'), extra_env=dict(ZFAST14_TEST_EXIT_AFTER='120'), tag='I3b_exit')
    r3 = probe(LIBTH, 'v14c', *A, 2, 8, ckpt=c3, nonce=nonce, key=kp('i3b'), tag='I3b_resume')
    res['I3b test-hook exit + resume'] = dict(exit_rc=e3['rc'], loaded=(r3.get('info') or {}).get('items_loaded'), verified=(r3.get('info') or {}).get('verified'),
                                             identical=e3['rc'] == 77 and r3['rc'] == 0 and _key(r3) == _key(th_ref) == _key(r14))
    # I4: generic kernel (test-hooks lib) == production
    g4 = probe(LIBTH, 'v14c', 10**16, 50.0, 61.0, 0.012, 2, 4, extra_env=dict(ZFAST14_GENERIC_KERNEL='1'), tag='I4')
    p4 = probe(LIB14B, 'v14c', 10**16, 50.0, 61.0, 0.012, 2, 4, tag='I4ref')
    res['I4 generic kernel == production'] = dict(generic=(g4.get('info') or {}).get('generic_kernel'), identical=g4['rc'] == 0 and _key(g4) == _key(p4))
    # G2: pipeline 1e16: generator SIGKILLed after >= 50 checkpoint lines, then --resume; vs an uninterrupted v5z8 run
    fr = zfast.check_tree_freeze('atlas_v5z9')
    if not fr['ok']: raise RegressError('atlas_v5z9 tree differs from V5Z9_FREEZE')
    dst = zfast._copy_tree('atlas_v5z9'); T16 = 10**16; lo, hi = str(T16), str(T16 + 10)
    ext = dict(ZFAST_THREADS='2', ZFAST_WORKERS='4', V4_LIM_GB='1.0')
    gA = _pipeline(dst, f'ck16_ref_{tag}', T16, lo, hi, ext, log='ref')
    runB = dst / 'runs' / f'w{T16}' / f'ck16_res_{tag}'
    pB = _pipeline(dst, f'ck16_res_{tag}', T16, lo, hi, ext, log='kill', popen=True); t0 = time.time(); killed = None
    while pB.poll() is None and time.time() - t0 < 1800:
        if _lines(runB / 'zfast_ckpt_gen.txt') >= 50:
            q = subprocess.run(['pgrep', '-f', f'gen_target5.py {runB}'], capture_output=True, text=True).stdout.split()
            if q: killed = int(q[0]); os.kill(killed, signal.SIGKILL); break
        time.sleep(0.2)
    pB.wait(); nk = _lines(runB / 'zfast_ckpt_gen.txt')
    gl = [json.loads(l) for l in open(runB / 'gen.jsonl')] if (runB / 'gen.jsonl').exists() else []
    killed_ok = killed is not None and not (runB / 'zs.json').exists() and not any(x.get('stage') == 'gen_done' for x in gl)
    gB2 = _pipeline(dst, f'ck16_res_{tag}', T16, lo, hi, dict(ext, ZFAST_WORKERS='8'), resume=True, log='resume')
    runA = dst / 'runs' / f'w{T16}' / f'ck16_ref_{tag}'
    c = zfast.compare_regenerated(dict(run=str(runA)), runB)
    gridsame = all(sha256(runA / 'turing_grid' / f) == sha256(runB / 'turing_grid' / f) for f in ('grid.npz', 'zeros_intervals.json'))
    sc = [json.loads(l) for l in open(runB / 'zfast_ckpt_gen.txt.sessions.jsonl')] if (runB / 'zfast_ckpt_gen.txt.sessions.jsonl').exists() else []
    rcj = json.load(open(runB / 'replay_check' / 'replay_check.json')) if (runB / 'replay_check' / 'replay_check.json').exists() else {}
    res['G2 pipeline: generator SIGKILLed in its session, --resume'] = dict(
        ref_rc=gA['rc'], killed_pid=killed, lines_at_kill=nk, killed_before_zs=killed_ok, resume_rc=gB2['rc'], compare=c, turing_grid_identical=gridsame,
        gen_sessions=[dict(pid=x['pid'], loaded=x['info'].get('items_loaded'), verified=x['info'].get('verified'), rejected=x['info'].get('lines_rejected')) for x in sc],
        replay_zfast_ckpt=rcj.get('zfast_ckpt'),
        identical=gA['rc'] == 0 and gB2['rc'] == 0 and killed_ok and c['identical'] and gridsame and (rcj.get('zfast_ckpt') or {}).get('ok') is True
                  and len(sc) == 1 and (sc[0]['info'].get('items_loaded') or 0) > 0
                  and sc[0]['info'].get('verified') == min(64, sc[0]['info'].get('items_loaded') or 0) and sc[0]['info'].get('verify_n') == 64)
    ok = (res['I2 fresh checkpoint == no checkpoint']['e20'] and res['I2 fresh checkpoint == no checkpoint']['e14']
          and res['I3a SIGKILL + resume (W 8 -> 3)']['identical'] and res['I3a SIGKILL + resume (W 8 -> 3)']['lines_at_kill'] >= 300
          and res['I3b test-hook exit + resume']['identical'] and res['I4 generic kernel == production']['identical']
          and res['G2 pipeline: generator SIGKILLed in its session, --resume']['identical'])
    return dict(check='I2/I3/I4/G2: v14b checkpoint/resume identity', results=res, ok=ok)


def gate_n13(tag):
    """N13 on both trees: honest run A, then run B = copy of A without its replay outputs, with the generator checkpoint copied to the
    replay checkpoint path, finished by --resume (stage 3 only)."""
    out = {}
    for tree in ('atlas_v5z7', 'atlas_v5z9'):
        fr = zfast.check_tree_freeze(tree)
        if not fr['ok']: raise RegressError(f'{tree} tree differs from its FREEZE')
        dst = zfast._copy_tree(tree); T12 = 10**12; lo, hi = str(T12), str(T12 + 10)
        ext = dict(ZFAST_THREADS='2', ZFAST_WORKERS='4', V4_LIM_GB='1.0')
        nA, nB = f'n13A_{tag}', f'n13B_{tag}'; base = dst / 'runs' / f'w{T12}'
        gA = _pipeline(dst, nA, T12, lo, hi, ext, log='A')
        A, B = base / nA, base / nB
        shutil.copytree(A, B, ignore=shutil.ignore_patterns('replay_check', 'replay_target.log', 'summary.json', 'zfast_ckpt_replay.txt*', 'drive.jsonl'))
        shutil.copyfile(A / 'zfast_ckpt_gen.txt', B / 'zfast_ckpt_replay.txt')         # the misrouting
        before = sha256(B / 'zfast_ckpt_replay.txt')
        gB = _pipeline(dst, nB, T12, lo, hi, ext, resume=True, log='B')
        rc = json.load(open(B / 'replay_check' / 'replay_check.json')) if (B / 'replay_check' / 'replay_check.json').exists() else {}
        after = sha256(B / 'zfast_ckpt_replay.txt') if (B / 'zfast_ckpt_replay.txt').exists() else None
        out[tree] = dict(A_rc=gA['rc'], B_rc=gB['rc'], B_replay_passed=rc.get('passed'), B_replay_zfast_ckpt=rc.get('zfast_ckpt'),
                         generator_items_reused_silently=bool(rc.get('passed') and before == after),
                         replay_log_tail=open(B / 'replay_check' / 'replay5.log').read()[-600:] if (B / 'replay_check' / 'replay5.log').exists() else None)
    ok = out['atlas_v5z7']['generator_items_reused_silently'] and out['atlas_v5z9']['B_replay_passed'] is False and out['atlas_v5z9']['B_rc'] != 0
    return dict(check='N13: generator checkpoint misrouted to the replay', results=out, ok=bool(ok))


def main():
    guard()
    ap = argparse.ArgumentParser(prog='python -m engine.regress_v1.v5z9_gate')
    for k in ('identity', 'ckpt', 'n13', 'w1e22'): ap.add_argument('--' + k, action='store_true')
    ap.add_argument('--workers', default='8'); ap.add_argument('--tag')
    a = ap.parse_args(); stamp = time.strftime('%Y%m%d_%H%M%S'); tag = a.tag or f'z9_{stamp}'; REPORTS.mkdir(exist_ok=True)
    if a.identity: rep, kind = gate_identity(), 'identity'
    elif a.ckpt: rep, kind = gate_ckpt(tag), 'ckpt'
    elif a.n13: rep, kind = gate_n13(tag), 'n13'
    elif a.w1e22:
        G6.TREE[0] = 'atlas_v5z9'; rep, kind = G6.gate_w1e22(tag, a.workers), 'w1e22'
    else: ap.error('choose --identity, --ckpt, --n13 or --w1e22')
    rep.update(tree='atlas_v5z9', stamp=stamp, predictions='diagnostic/zfast/PREDICTIONS_M13.md (sha in PREDICTIONS_M13.sha256)')
    p = REPORTS / f'v5z9_{kind}_{stamp}.json'; json.dump(rep, open(p, 'w'), indent=1, default=str)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('cases', 'results', 'compare', 'process')}, default=str, indent=1)[:3000])
    print(f'REPORT {p}: {"PASS" if rep["ok"] else "FAIL"}', flush=True)
    sys.exit(0 if rep['ok'] else 1)


if __name__ == '__main__':
    main()
