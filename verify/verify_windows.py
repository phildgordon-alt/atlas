"""Atlas repository verifier for the RH window certificates (repository-only wrapper; NOT a frozen pipeline file).

For every selected window run directory it does, from the STORED files of this repository only:
  (1) frozen replay logic of the run's own code tree, plain + hardened, on every main and S-layer certificate
      (atlas_mark2/engine/regress_v1/zfast_t0_worker.py, unchanged): model rebuild, outward hardening, the sha-pinned
      verify_zs5 checker, Arb bisection.  Row measurements are read from the run's stored gen_measurements.json and the Z
      sign-change re-evaluation is skipped (that needs a zfast session at height T0: hours to days, see README);
  (2) pass/fail and min_candidate_lower compared, record by record, with the stored replay-of-record (or independent replay)
      records; they must be bit-identical;
  (3) exact rational tiling of hull and target x [0, 1/2] (pinned external/exact_tiling_check.py), the d = 0 sweep and claim (B)
      coverage, recomputed from the certificates this verifier just passed; number of certified sign changes in the target;
  (4) agreement with the stored Arb/Turing cross-count (crosscheck.json);
  (5) if the run stored its Turing grid (atlas_v5z7 wide windows): the Turing count is recomputed from the stored grid with the
      unchanged tool of record (tools/scan_turing5.py recount, no zfast call) and must equal the stored record and the number of
      certified sign changes (the required count-equality gate, engine/regress_v1/turing_gate.py G-T2/G-T4..G-T6).
The comparison logic follows engine/regress_v1/zfast.py tier0() and turing_gate.py gate(); those modules hard-code host paths, so
the relevant logic is restated here.  Writes only under --out.

usage: python -B verify/verify_windows.py [--set quick|all|RUN_ID ...] [--out DIR] [--control]"""
import argparse, glob, json, os, subprocess, sys, time, importlib.util, hashlib, shutil
from fractions import Fraction as Fr
from pathlib import Path

if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule: safety checks are asserts)')

REPO = Path(__file__).resolve().parent.parent
A = REPO / 'atlas_mark2'; ZF = A / 'diagnostic' / 'zfast'
WORKER = A / 'engine' / 'regress_v1' / 'zfast_t0_worker.py'
BOOT = REPO / 'verify' / 'boot'
TILING = REPO / 'external' / 'exact_tiling_check.py'
TILING_SHA = '0868990ee2027ba493593d514607acc0aad729ed94c7cf61b1cf3d1f22a08b45'
LIM_GB = float(os.environ.get('ATLAS_LIM_GB', '3.0'))     # memory watchdog per child (RSS)

TREES = {'record_heights': A / 'diagnostic' / 'record_heights' / 'v5run', 'atlas_v5z': ZF / 'atlas_v5z', 'atlas_v5z2': ZF / 'atlas_v5z2',
         'atlas_v5z3': ZF / 'atlas_v5z3', 'atlas_v5z4': ZF / 'atlas_v5z4', 'atlas_v5z5': ZF / 'atlas_v5z5', 'atlas_v5z7': ZF / 'atlas_v5z7'}
# one headline window per height (the claim-bearing window of README section "Results"), plus the recorded fail-closed 10^23 run
QUICK = ['atlas_v5z:w1000000000000000/z_1e15', 'atlas_v5z:w10000000000000000/z_1e16', 'atlas_v5z:w100000000000000000/z_1e17',
         'atlas_v5z:w1000000000000000000/z_1e18', 'atlas_v5z2:w100000000000000000000/h_1e20', 'atlas_v5z2:w1000000000000000000000/h_1e21',
         'atlas_v5z4:w100000000000000000000000/w_1e23', 'atlas_v5z3:w100000000000000000000000/h_1e23',
         'atlas_v5z4:w1000000000000000000000000/w_1e24', 'atlas_v5z7:w10000000000000000000000/wide7_1e22',
         'atlas_v5z7:w10000000000000000000000000/wide7_1e25', 'atlas_v5z7:w100000000000000000000000000/wide7_1e26']


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def runs():
    out = {}
    for tree, root in TREES.items():
        for d in sorted(glob.glob(str(root / 'runs' / 'w*' / '*'))):
            d = Path(d)
            if (d / 'pieces.json').exists() and (d / 'certs').is_dir():
                s = json.load(open(d / 'summary.json')) if (d / 'summary.json').exists() else {}
                out[f'{tree}:{d.parent.name}/{d.name}'] = dict(tree=tree, run=d, recorded_closed=bool(s.get('all_closed')))
    return out


def env():
    e = {k: v for k, v in os.environ.items() if not k.startswith('ZFAST_')}
    e.pop('PYTHONOPTIMIZE', None)
    e.update(ATLAS_REPO=str(REPO), PYTHONPATH=str(BOOT), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1')
    return e


def guarded(cmd, log, extra_env=None, timeout=7200):
    """nice 19 child with an RSS watchdog (kills above LIM_GB); returns rc, wall, peak_gb."""
    e = env(); e.update(extra_env or {})
    t0 = time.time(); peak = 0.0
    with open(log, 'w') as fh:
        p = subprocess.Popen(['nice', '-n', '19'] + cmd, stdout=fh, stderr=subprocess.STDOUT, env=e, start_new_session=True)
        while p.poll() is None:
            time.sleep(1.0)
            try:
                rss = sum(int(x) for x in subprocess.run(['ps', '-o', 'rss=', '-g', str(p.pid)], capture_output=True, text=True).stdout.split()) / 1e6
            except Exception:
                rss = 0.0
            peak = max(peak, rss)
            if rss > LIM_GB or time.time() - t0 > timeout:
                p.kill(); p.wait(); return dict(rc=-9, wall=round(time.time() - t0, 1), peak_gb=round(peak, 3), killed='watchdog')
    return dict(rc=p.returncode, wall=round(time.time() - t0, 1), peak_gb=round(peak, 3))


def tiling():
    if sha256(TILING) != TILING_SHA: raise SystemExit('pinned external/exact_tiling_check.py sha256 mismatch')
    sp = importlib.util.spec_from_file_location('tl_repo', TILING); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


def sweep(a, b, ivs):
    gaps = []; cur = a
    for x0, x1 in sorted(ivs):
        if x1 < cur: continue
        if x0 > cur: gaps.append([float(cur), float(x0)])
        cur = max(cur, x1)
        if cur >= b: break
    if cur < b: gaps.append([float(cur), float(b)])
    return gaps


def geometry(d, recs, scratch, TL):
    """as engine/regress_v1/zfast.py geometry(): tiling, d = 0 sweep, claim (B) coverage from the certificates passed here."""
    P = json.load(open(d / 'pieces.json')); passed = {}
    for x in recs: passed.setdefault(x['cert'], []).append(bool(x.get('passed')))
    ok = {c for c, v in passed.items() if len(v) == 2 and all(v)}
    mains = sorted(c for c in ok if c.startswith('certs/')); nps = sorted(c for c in ok if c.startswith('certs_np/'))
    RD = Path(scratch); RD.mkdir(parents=True, exist_ok=True); rects = []; d0 = []
    for c in mains:
        for i, rg in enumerate(json.load(open(d / c))['regions']):
            q = RD / f'{Path(c).stem}_{i}.json'; json.dump(dict(region=rg), open(q, 'w')); rects.append(q)
            if rg[2] == 0.0: d0.append((Fr(rg[0]), Fr(rg[1])))
    h0, h1 = P['hull']; t0, t1 = P['target']
    _, s_h = TL.check('hull', [(Fr(h0), Fr(h1), Fr(0), Fr(0.5))], rects)
    _, s_t = TL.check('target', [(Fr(t0), Fr(t1), Fr(0), Fr(0.5))], rects)
    g0 = sweep(Fr(h0), Fr(h1), d0)
    segs = [(Fr(rg[0]), Fr(rg[1])) for c in nps for rg in json.load(open(d / c))['regions']]; unc = []; nseg = 0
    for c in mains:
        cc = json.load(open(d / c)); x0, x1 = cc['regions'][0][:2]
        for a, b in cc['zs_intervals']:
            if a <= x1 and b >= x0:
                nseg += 1; gp = sweep(Fr(max(a, x0)), Fr(min(b, x1)), segs)
                if gp: unc.append(dict(cert=c, interval=[a, b], gaps=gp))
    n_main = len(glob.glob(str(d / 'certs' / 'cert_*.json'))); n_np = len(glob.glob(str(d / 'certs_np' / 'cert_*.json')))
    closed = bool(n_main and len(mains) == n_main and not s_h and not s_t and not g0)
    ivs = set()
    for c in glob.glob(str(d / 'certs' / 'cert_*.json')):
        for a, b in json.load(open(c))['zs_intervals']: ivs.add((a, b))
    inside = sorted((a, b) for a, b in ivs if t0 <= a and b <= t1)
    straddle = sorted((a, b) for a, b in ivs if (a < t0 < b) or (a < t1 < b))
    return dict(main_passed=f'{len(mains)}/{n_main}', np_passed=f'{len(nps)}/{n_np}', seams_hull=len(s_h), seams_target=len(s_t),
                gaps_d0=len(g0), closed_A=closed, claim_B=bool(closed and not unc and len(nps) == n_np), uncovered=len(unc),
                sign_changes_in_target=len(inside), straddling=len(straddle),
                disjoint=all(inside[i][1] <= inside[i + 1][0] for i in range(len(inside) - 1)))


def stored_replay(d):
    for sub in ('replay_check_independent', 'replay_check'):
        if (d / sub / 'replay.jsonl').exists():
            recs = [json.loads(l) for l in open(d / sub / 'replay.jsonl')]
            rc = json.load(open(d / sub / 'replay_check.json')) if (d / sub / 'replay_check.json').exists() else {}
            return sub, recs, rc
    return None, [], {}


def turing(d, out):
    """recount from the stored grid with the unchanged tool of record; compare with the stored record and the certified count."""
    if not (d / 'turing_grid' / 'grid.npz').exists() or not (d / 'turing_recount.json').exists(): return None
    stored = json.load(open(d / 'turing_recount.json'))
    keys = list(stored['turing'].keys()); pts = ','.join(keys)
    newj = out / 'turing_recount.json'
    g = guarded([sys.executable, '-B', str(REPO / 'verify' / 'run_rewritten.py'), str(ZF / 'tools' / 'scan_turing5.py'), 'recount',
                 str(d / 'turing_grid'), str(newj), '--points', pts, '--win', pts], out / 'turing_recount.log', timeout=3600)
    if g['rc'] != 0 or not newj.exists(): return dict(ok=False, process=g, error='recount failed')
    new = json.load(open(newj))
    vol = {'seconds', 'wall_seconds', 'out', 'scandir', 'argv', 'started', 'finished', 'tool_path', 'path'}
    def strip(o):
        if isinstance(o, dict): return {k: strip(v) for k, v in o.items() if k not in vol}
        if isinstance(o, list): return [strip(v) for v in o]
        return o
    same = all(json.dumps(strip(new.get(k)), sort_keys=True) == json.dumps(strip(stored.get(k)), sort_keys=True) for k in ('turing', 'windows', 'T0', 'DT', 'grid_ends', 'zeros_in_scan', 'tool_sha256'))
    lo, hi = new['turing'][keys[0]], new['turing'][keys[1]]
    pinned = bool(lo['N_lower'] == lo['N_upper'] and hi['N_lower'] == hi['N_upper'])
    cnt = (hi['N_lower'] - lo['N_lower']) if pinned else None
    return dict(ok=bool(same and pinned), identical_to_stored=same, pinned=pinned, N_lo=lo['N_lower'], N_hi=hi['N_lower'], turing_count=cnt,
                tool_sha256=new.get('tool_sha256'), process=g)


def verify(rid, r, out, TL, control=None):
    d = r['run']; o = out / rid.replace(':', '__').replace('/', '__'); o.mkdir(parents=True, exist_ok=True)
    wj = o / 'worker.json'; boot = o / 'boot_modules.tsv'
    if boot.exists(): boot.unlink()
    g = guarded([sys.executable, '-B', str(WORKER), str(TREES[r['tree']]), str(d), str(wj)] + ([control] if control else []),
                o / 'worker.log', extra_env=dict(ATLAS_BOOT_LOG=str(boot)))
    if g['rc'] != 0 or not wj.exists(): return dict(id=rid, ok=False, error='worker failed', process=g)
    W = json.load(open(wj)); recs = W['records']
    outside = [l for l in open(boot).read().splitlines() if l.endswith('\tOUTSIDE')] if boot.exists() else ['no boot log']
    geo = geometry(d, recs, o / 'rects', TL)
    sub, srecs, src = stored_replay(d)
    sidx = {(os.path.relpath(x['cert'], d) if os.path.isabs(x['cert']) else x['cert'], x['hardened']): x for x in srecs}
    same_pass = same_mcl = matched = 0
    for x in recs:
        s = sidx.get((x['cert'], x['hardened']))
        if s is None:
            # stored replay records may carry absolute host paths: match on the path relative to the run directory name
            s = next((v for (k, h), v in sidx.items() if h == x['hardened'] and k.endswith('/' + x['cert'])), None)
        if s is None: continue
        matched += 1; same_pass += (bool(s.get('passed')) == bool(x.get('passed'))); same_mcl += (s.get('min_candidate_lower') == x.get('min_candidate_lower'))
    cc = json.load(open(d / 'crosscheck.json')) if (d / 'crosscheck.json').exists() else None
    n_all = len(recs); n_pass = sum(bool(x.get('passed')) for x in recs)
    errors = sum('error' in x for x in recs)
    mm = sum(1 for x in recs if 'model_match' in x and not all(x['model_match'].values()))
    res = dict(id=rid, control=control, records=n_all, passed_records=n_pass, errors=errors, model_mismatch=mm,
               missing_measurements=len(W['missing_measurements']), geometry=geo, modules_outside_repo=outside,
               stored_replay=dict(source=sub, matched=matched, same_passed=same_pass, identical_min_candidate_lower=same_mcl,
                                  stored_closed=src.get('passed'), stored_claim_B=src.get('passed_B')),
               crosscheck=None if cc is None else dict(arb_count=cc.get('arb_count'), stored_in_target=cc.get('atlas_sign_changes_in_target'),
                                                     agree=(cc.get('arb_count') == geo['sign_changes_in_target'] == cc.get('atlas_sign_changes_in_target'))),
               min_candidate_lower=min([x['min_candidate_lower'] for x in recs if x.get('min_candidate_lower') is not None and x['cert'].startswith('certs/')], default=None),
               process=g)
    res['turing'] = turing(d, o) if not control else None
    if control:
        res['ok'] = not (n_pass == n_all and geo['closed_A'] and geo['claim_B'])          # a tampered run must NOT verify
        res['expected'] = 'negative control: must fail'
    elif r['recorded_closed']:
        res['ok'] = bool(n_pass == n_all and not errors and not mm and not W['missing_measurements'] and geo['closed_A'] and geo['claim_B']
                         and geo['disjoint'] and geo['straddling'] == 0 and matched == n_all and same_pass == matched and same_mcl == matched
                         and (cc is None or res['crosscheck']['agree']) and not outside
                         and (res['turing'] is None or (res['turing']['ok'] and res['turing']['turing_count'] == geo['sign_changes_in_target'])))
    else:
        res['ok'] = bool(not geo['closed_A'] and src.get('passed') is False and not outside)
        res['expected'] = 'recorded NOT closed (failed closed, not claim-bearing): must also be found NOT closed'
    return res


def line(x):
    g = x.get('geometry') or {}; t = x.get('turing') or {}
    s = (f"{'OK  ' if x['ok'] else 'FAIL'} {x['id']:58s} records {x.get('passed_records')}/{x.get('records')} "
         f"main {g.get('main_passed')} S-layer {g.get('np_passed')} closed_A={g.get('closed_A')} claim_B={g.get('claim_B')} "
         f"sign_changes={g.get('sign_changes_in_target')}")
    if x.get('stored_replay'): s += f" | identical to stored replay {x['stored_replay']['identical_min_candidate_lower']}/{x['stored_replay']['matched']}"
    if x.get('crosscheck'): s += f" | Arb/Turing cross-count {x['crosscheck']['arb_count']}"
    if t: s += f" | Turing recount {t.get('turing_count')} (identical to stored: {t.get('identical_to_stored')})"
    if x.get('expected'): s += f" [{x['expected']}]"
    s += f" | {x['process']['wall']} s, peak {x['process']['peak_gb']} GB"
    return s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--set', nargs='+', default=['quick']); ap.add_argument('--out', default=str(REPO / 'verify_out'))
    ap.add_argument('--control', action='store_true', help='also run the tamper negative control on the 10^17 window')
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    R = runs(); TL = tiling()
    ids = list(R) if a.set == ['all'] else QUICK if a.set == ['quick'] else a.set
    res = []
    for rid in ids:
        if rid not in R: print(f'FAIL {rid}: no such run'); res.append(dict(id=rid, ok=False)); continue
        x = verify(rid, R[rid], out, TL); res.append(x); print(line(x), flush=True)
    if a.control:
        for ctl in ('--tamper-cert', '--wrong-y'):
            x = verify('atlas_v5z:w100000000000000000/z_1e17', R['atlas_v5z:w100000000000000000/z_1e17'], out / f'control{ctl}', TL, control=ctl)
            x['id'] = f'NEGATIVE CONTROL {ctl} on z_1e17'; res.append(x); print(line(x), flush=True)
    json.dump(res, open(out / 'verify_windows.json', 'w'), indent=1, default=str)
    nf = sum(not x['ok'] for x in res)
    print(f'windows verified: {sum(x["ok"] for x in res)}/{len(res)}; failures {nf}; details {out}/verify_windows.json')
    sys.exit(1 if nf else 0)


if __name__ == '__main__':
    main()
