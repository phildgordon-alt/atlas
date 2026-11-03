"""engine/regress_v1: the atlas_v5-format RH window family (atlas_v5 originals, record_heights v5run, zfast atlas_v5z .. v5z4).

tier 0  per run: (a) sha256 of every stored certificate/measurement/replay file against FROZEN.json; (b) frozen replay logic with
        stored measurements, plain + hardened (zfast_t0_worker.py); (c) exact tiling of hull/target and claim (B) coverage recomputed
        from the tier-0-passed certificates with the pinned exact_tiling_check.py; (d) consistency with the stored crosscheck.json
        (Arb Turing count) and with the stored replay records; (e) golden identity (canonical JSON) on every run after the baseline.
tier 1  regeneration of a cheap window from a byte copy of its own frozen code tree (sha-checked against the tree's FREEZE file),
        run under engine/regress_v1/work/, then canonical identity of every certificate file, zs.json, gen_measurements.json,
        pieces.json and the replay results.
tier 2  the same as tier 1 for expensive windows: listed, never run by default."""
import glob, importlib.util, json, os, shutil
from fractions import Fraction as Fr
from pathlib import Path
from .common import DIAG, HERE, WORK, PY, RegressError, sha256, canon, canon_sha, strip_keys, guarded, env_base

ZF = DIAG / 'zfast'
TREES = {
    'atlas_v5': (DIAG / 'atlas_v5', 'V5_FREEZE.sha256'),
    'record_heights': (DIAG / 'record_heights' / 'v5run', 'V5_FREEZE.sha256'),
    'atlas_v5z': (ZF / 'atlas_v5z', 'V5Z_FREEZE.sha256'),
    'atlas_v5z2': (ZF / 'atlas_v5z2', 'V5Z2_FREEZE.sha256'),
    'atlas_v5z3': (ZF / 'atlas_v5z3', 'V5Z3_FREEZE.sha256'),
    'atlas_v5z4': (ZF / 'atlas_v5z4', 'V5Z4_FREEZE.sha256'),
}
TILING = '/Users/kiosk/atlas/workbench/math_ablation_20260928/audit_20261004/exact_tiling_check.py'
TILING_SHA = '0868990ee2027ba493593d514607acc0aad729ed94c7cf61b1cf3d1f22a08b45'
RUN_FILES = ('pieces.json', 'zs.json', 'gen_measurements.json', 'summary.json', 'crosscheck.json',
             'replay_check/replay_check.json', 'replay_check/replay.jsonl', 'replay_check/exact_heights.json',
             'replay_check_independent/replay_check.json', 'replay_check_independent/replay.jsonl',
             'replay_check_independent/exact_heights.json')
# A4: zfast row enclosures depend (in the last ulp) on the thread count of the session.  Regenerate with the count the tree's
# own run script exported: atlas_v5z2 run_v2.sh exports ZFAST_THREADS=${ZFAST_THREADS:-1}; atlas_v5z run_window.sh sets none (provider
# default 2); atlas_v5z3 run_x56.sh (x_1e16) exports 2.  atlas_v5 / record_heights do not use zfast.
RECORDED_THREADS = {'atlas_v5z2': 1}
# A4: the env the original run scripts exported (run_window.sh's 8th argument -> ZFAST_CENTER, the session centre).
# atlas_v5z2 run_v2.sh: every y_* window with centre 1.0, the pair window with 287.0; atlas_v5z3 run_x56.sh: x_1e16 with 1.0.
# atlas_v5z run_window.sh exports no centre.
RECORDED_CENTER = {**{f'atlas_v5z2:{w}/{n}': '1.0' for w, n in (('w1000000000000', 'y_1e12'), ('w10000000000000', 'y_1e13'),
                      ('w100000000000000', 'y_1e14'), ('w1000000000000000', 'y_1e15'), ('w10000000000000000', 'y_1e16'),
                      ('w100000000000000000', 'y_1e17'), ('w1000000000000000000', 'y_1e18'))},
                   'atlas_v5z2:w1000000000000000/y_pair_1e15_286': '287.0', 'atlas_v5z3:w10000000000000000/x_1e16': '1.0'}
TIER1_MAX_WALL = 120.0       # PREREG section 3: tier 1 = every window whose recorded wall time is <= 120 s
VOLATILE = {'seconds', 'gen_seconds', 't', 'cert', 'run', 'replay_process', 'peak_gb', 'replay_peak_gb', 'source',
            'tiling_script', 'tiling_sha256', 'wall_seconds'}


def runs():
    out = []
    for tree, (root, _) in TREES.items():
        for d in sorted(glob.glob(str(root / 'runs' / 'w*' / '*'))):
            d = Path(d)
            if (d / 'pieces.json').exists() and (d / 'certs').is_dir():
                s = json.load(open(d / 'summary.json')) if (d / 'summary.json').exists() else {}
                out.append(dict(family='zfast_windows', id=f'{tree}:{d.parent.name}/{d.name}', tree=tree, run=str(d),
                                T0=json.load(open(d / 'pieces.json'))['T0'], recorded_closed=s.get('all_closed'),
                                recorded_wall=s.get('wall_seconds'), recorded_gen=(s.get('generator') or {}).get('seconds')))
    return out


def frozen_files(r):
    d = Path(r['run'])
    fs = sorted(glob.glob(str(d / 'certs' / '*.json'))) + sorted(glob.glob(str(d / 'certs_np' / '*.json')))
    fs += [str(d / f) for f in RUN_FILES if (d / f).exists()]
    return fs


def tree_code_files(tree):
    root, ff = TREES[tree]
    out = {}
    for line in open(root / ff):
        if line.strip():
            h, p = line.split(None, 1); out[str((root / p.strip()).resolve())] = h
    out[str((root / ff).resolve())] = None
    return out


def check_tree_freeze(tree):
    """every file of the tree's own FREEZE manifest still has its frozen sha256"""
    bad = []
    for p, h in tree_code_files(tree).items():
        if h is None: continue
        if not os.path.exists(p): bad.append(dict(file=p, problem='missing'))
        elif sha256(p) != h: bad.append(dict(file=p, problem='sha256 differs from FREEZE'))
    return dict(tree=tree, files=len(tree_code_files(tree)) - 1, mismatches=bad, ok=not bad)


def _tiling_module():
    if sha256(TILING) != TILING_SHA: raise RegressError('pinned exact_tiling_check.py sha256 mismatch')
    sp = importlib.util.spec_from_file_location('tl_regress', TILING); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
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


def geometry(r, recs, scratch):
    """tiling of hull/target x [0,1/2], d = 0 sweep and claim (B) coverage from the tier-0-passed certificates (replay_target5 steps 3-4)."""
    d = Path(r['run']); P = json.load(open(d / 'pieces.json'))
    passed = {}
    for x in recs:
        passed.setdefault(x['cert'], []).append(bool(x.get('passed')))
    ok = {c for c, v in passed.items() if len(v) == 2 and all(v)}
    mains = sorted(c for c in ok if c.startswith('certs/')); nps = sorted(c for c in ok if c.startswith('certs_np/'))
    TL = _tiling_module(); RD = Path(scratch); RD.mkdir(parents=True, exist_ok=True); rects = []; d0 = []
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
    return dict(main_passed=f'{len(mains)}/{n_main}', np_passed=f'{len(nps)}/{n_np}', seams_hull=len(s_h), seams_target=len(s_t),
                gaps_d0=len(g0), closed_A=closed, claim_B=bool(closed and not unc and len(nps) == n_np), intervals_to_cover=nseg,
                uncovered=len(unc), sign_changes_in_target=len(inside),
                disjoint=all(inside[i][1] <= inside[i + 1][0] for i in range(len(inside) - 1)))


def stored_replay(r):
    d = Path(r['run'])
    for sub in ('replay_check_independent', 'replay_check'):
        if (d / sub / 'replay.jsonl').exists():
            recs = [json.loads(l) for l in open(d / sub / 'replay.jsonl')]
            rc = json.load(open(d / sub / 'replay_check.json')) if (d / sub / 'replay_check.json').exists() else {}
            return sub, recs, rc
    return None, [], {}


def tier0(r, scratch, control=None):
    """returns (result dict, golden payload)"""
    out = Path(scratch) / 'worker.json'; out.parent.mkdir(parents=True, exist_ok=True)
    root = TREES[r['tree']][0]
    cmd = [PY, '-B', str(HERE / 'zfast_t0_worker.py'), str(root), r['run'], str(out)] + ([control] if control else [])
    g = guarded(cmd, HERE, Path(scratch) / 'worker.log', timeout=3600)
    if g['rc'] != 0 or not out.exists():
        return dict(id=r['id'], ok=False, error='worker failed', process=g), None
    W = json.load(open(out)); recs = W['records']
    geo = geometry(r, recs, Path(scratch) / 'rects')
    # comparison with the stored replay records (same certificate, same mode)
    sub, srecs, src = stored_replay(r); d = Path(r['run'])
    sidx = {(os.path.relpath(x['cert'], d) if os.path.isabs(x['cert']) else x['cert'], x['hardened']): x for x in srecs}
    same_pass = 0; same_mcl = 0; diffs = []
    for x in recs:
        s = sidx.get((x['cert'], x['hardened']))
        if s is None: continue
        same_pass += (bool(s.get('passed')) == bool(x.get('passed')))
        if s.get('min_candidate_lower') == x.get('min_candidate_lower'): same_mcl += 1
        else: diffs.append(abs((s.get('min_candidate_lower') or 0) - (x.get('min_candidate_lower') or 0)))
    cc = json.load(open(d / 'crosscheck.json')) if (d / 'crosscheck.json').exists() else None
    n_all = len(recs); n_pass = sum(bool(x.get('passed')) for x in recs)
    errors = [x for x in recs if 'error' in x]
    mm = [x for x in recs if 'model_match' in x and not all(x['model_match'].values())]
    expect_closed = bool(r['recorded_closed'])
    res = dict(id=r['id'], T0=r['T0'], control=control, records=n_all, passed_records=n_pass, errors=len(errors),
               model_mismatch=len(mm), missing_measurements=len(W['missing_measurements']), geometry=geo,
               stored_replay=dict(source=sub, matched=len(sidx), same_passed=same_pass, identical_min_candidate_lower=same_mcl,
                                  max_abs_diff_min_candidate_lower=max(diffs, default=0.0),
                                  stored_closed=src.get('passed'), stored_claim_B=src.get('passed_B')),
               crosscheck=None if cc is None else dict(arb_count=cc.get('arb_count'), stored_in_target=cc.get('atlas_sign_changes_in_target'),
                                                     tier0_in_target=geo['sign_changes_in_target'],
                                                     agree=(cc.get('arb_count') == geo['sign_changes_in_target'] == cc.get('atlas_sign_changes_in_target'))),
               min_candidate_lower=min([x['min_candidate_lower'] for x in recs if x.get('min_candidate_lower') is not None and x['cert'].startswith('certs/')], default=None),
               worker_seconds=W['seconds'], process=g)
    if expect_closed:
        res['ok'] = bool(n_pass == n_all and not errors and not mm and not W['missing_measurements'] and geo['closed_A'] and geo['claim_B']
                         and (cc is None or res['crosscheck']['agree']) and same_pass == len(sidx))
    else:   # runs recorded as NOT closed (failed closed, not claim-bearing): PREREG 2.1(f): tier 0 must also find NOT closed.
        # Per-record agreement with the stored replay is reported only: the v5z3 N_win depended on the ambient precision (the
        # documented determinism bug fixed in v5z4), so the stored per-certificate outcome depends on process history.
        res['ok'] = bool(not geo['closed_A'] and src.get('passed') is False)
        res['expected'] = 'recorded NOT closed (failed closed); tier 0 must also find NOT closed'
    golden = dict(records=strip_keys(recs, VOLATILE), geometry=geo)
    return res, golden


# ---------------- tier 1 / tier 2: regeneration ----------------
def tier_of(r):
    w = r.get('recorded_wall') or 1e9
    return 1 if w <= TIER1_MAX_WALL else 2


def _copy_tree(tree):
    """byte copy of the tree's FREEZE-listed code (+ VERIFY_ZS5.sha256) into work/trees/<tree>; sha-checked."""
    root, ff = TREES[tree]; dst = WORK / 'trees' / tree
    files = tree_code_files(tree)
    for p, h in files.items():
        rel = os.path.relpath(p, root)
        if rel.startswith('..'): continue              # ../bin/*.dylib: loaded read-only from its absolute, sha-pinned path
        q = dst / rel; q.parent.mkdir(parents=True, exist_ok=True)
        if not q.exists(): shutil.copy2(p, q)
        if h is not None and sha256(q) != h: raise RegressError(f'copied tree file sha mismatch: {q}')
    return dst


def _original_args(r):
    d = Path(r['run'])
    for l in open(d / 'drive.jsonl'):
        x = json.loads(l)
        if x.get('stage') == 'start': return x['args']
    raise RegressError(f'no start record in {d}/drive.jsonl')


def regenerate(r, tag, perturb=None, threads=None):
    """re-run the window's own frozen pipeline from a byte copy of its tree; returns the new run dir and process record."""
    dst = _copy_tree(r['tree']); a = dict(_original_args(r))
    if perturb == 'zs_step': a['zs_step'] = a['zs_step'] * 2          # negative control NC-T1: a changed parameter must not reproduce
    name = f"{a['name']}__{tag}"
    sub = f"w{a['T0']:.2f}" if a['grid'] == 'v4' else f"w{a['T0']}"
    new = dst / 'runs' / sub / name
    if new.exists(): raise RegressError(f'{new} exists (never overwrite); use a new tag')
    cmd = [PY, '-u', '-B', 'atlas_v5.py', str(a['T0']), a['tlo'], a['thi'], '--name', name, '--grid', a['grid'], '--evaluator', a['evaluator'],
           '--pw', repr(a['pw']), '--wm', repr(a['wm']), '--zs-step', repr(a['zs_step']), '--zs-refine', repr(a['zs_refine']),
           '--gen-timeout', '3000']
    th = threads if threads is not None else RECORDED_THREADS.get(r['tree'], 2)
    extra = dict(ZFAST_THREADS=th)
    if r['id'] in RECORDED_CENTER: extra['ZFAST_CENTER'] = RECORDED_CENTER[r['id']]
    g = guarded(cmd, dst, WORK / 'logs' / f'tier1_{r["tree"]}_{name}.log', env=env_base(**extra), timeout=3500)
    g['zfast_env'] = extra
    return new, g, a


def compare_regenerated(r, new):
    """canonical identity of the regenerated window against the frozen one."""
    old = Path(r['run']); rep = {}
    def certset(d, sub):
        return {Path(f).name: json.load(open(f)) for f in sorted(glob.glob(str(d / sub / 'cert_*.json')))}
    for sub in ('certs', 'certs_np'):
        A, B = certset(old, sub), certset(new, sub)
        same = sorted(set(A) & set(B))
        ident = [k for k in same if canon(strip_keys(A[k], {'gen_seconds'})) == canon(strip_keys(B[k], {'gen_seconds'}))]
        byte_ident = [k for k in same if sha256(old / sub / k) == sha256(new / sub / k)]
        rep[sub] = dict(frozen=len(A), regenerated=len(B), same_names=len(same), canonical_identical=len(ident),
                        byte_identical=len(byte_ident), differing=[k for k in same if k not in ident][:10],
                        only_frozen=sorted(set(A) - set(B))[:10], only_new=sorted(set(B) - set(A))[:10])
    for f in ('pieces.json', 'zs.json', 'gen_measurements.json'):
        A = json.load(open(old / f)) if (old / f).exists() else None; B = json.load(open(new / f)) if (new / f).exists() else None
        rep[f] = dict(canonical_identical=(A is not None and B is not None and canon(A) == canon(B)),
                      byte_identical=(A is not None and B is not None and sha256(old / f) == sha256(new / f)))
    def rc(d):
        p = d / 'replay_check' / 'replay_check.json'
        if not p.exists(): return None
        x = json.load(open(p))
        return dict(passed=x.get('passed'), passed_B=x.get('passed_B'), certificates=x.get('certificates'), passed_both=x.get('passed_both'),
                    min_candidate_lower=x.get('min_candidate_lower'), seams=[(x.get('tiling') or {}).get(k) for k in ('seams_hull', 'seams_target')],
                    gaps_d0=len((x.get('tiling') or {}).get('gaps_d0') or []), uncovered=len((x.get('claim_B') or {}).get('uncovered') or []))
    def rj(d):
        p = d / 'replay_check' / 'replay.jsonl'
        if not p.exists(): return None
        return sorted(canon(strip_keys(dict(json.loads(l), cert=os.path.basename(json.loads(l)['cert'])), {'seconds'})) for l in open(p))
    rep['replay_check'] = dict(frozen=rc(old), regenerated=rc(new), identical=(rc(old) == rc(new) and rc(old) is not None))
    rep['replay_records_identical'] = (rj(old) is not None and rj(old) == rj(new))
    rep['identical'] = bool(all(rep[s]['canonical_identical'] == rep[s]['frozen'] == rep[s]['regenerated'] for s in ('certs', 'certs_np'))
                            and all(rep[f]['canonical_identical'] for f in ('pieces.json', 'zs.json', 'gen_measurements.json'))
                            and rep['replay_check']['identical'] and rep['replay_records_identical'])
    return rep
