#!/usr/bin/env python
"""atlas_v5/replay_target5.py = atlas_v4 replay_target4.py with exact heights (THEORY_V5.md): every height is an offset from the run's
integer T0; hull/target/regions/intervals are compared and tiled in offsets (an exact translation of the absolute heights, THEORY_V5
section 1); certificates are replayed by lib/replay5.py with the sha-pinned lib/verify_zs5.py.  Also writes replay_check/exact_heights.json
(hull, target, every passed region as exact rationals T0 + u).  atlas_v4 docstring follows.
atlas_v4/replay_target4.py -- independent re-check of a finished atlas_v4 target WITHOUT any generator code.
CLI: replay_target4.py runs/w{T0}/{NAME} [OUTDIR_NAME=replay_check]
Uses only: pieces.json (T0, target, hull bins, WM), the certificate files certs/*.json (their dual data), and fresh copies of
lib/{verify_zs.py (sha-pinned), model4.py, replay4.py} placed in replay_check/.  Steps:
  1 hull: recomputed from (T0, tlo, thi) and compared with pieces.json;
  2 every certificate: T0 must be the run's T0; region(s) must lie in [hull] x [0, 1/2] with exact bin-edge floats e(k);
    window bins = piece bins +- WM bins (as pieces.json says); replay4.py plain + hardened (fresh process, 2.5 GB watchdog):
    model + rows rebuilt, sha-pinned verify_zs.check;
  3 exact tiling (exact_tiling_check.check, unchanged, sha 0868990e...) of hull x [0, 1/2] and target x [0, 1/2] by the regions of the
    certificates that passed BOTH modes, plus a 1-D exact sweep that the d = 0 line of the hull is covered by passed regions with d_lo = 0;
  4 claim (B) (THEORY_V4 section 10): the S-layer certificates certs_np/ replayed by the no-parity verifier (plain + hardened) must cover,
    exactly, every sign-change interval of every passed main certificate inside its region.  Exit code reflects claim (A) only.
Writes replay_check/replay_check.json; exit 0 iff everything passes."""
import json, sys, os, shutil, hashlib, importlib.util, glob, time
from fractions import Fraction as Fr
from pathlib import Path
V4 = Path(__file__).resolve().parent; sys.path.insert(0, str(V4))
import atlas_v5 as D
from heights import Grid
TILING = '/Users/kiosk/atlas/workbench/math_ablation_20260928/audit_20261004/exact_tiling_check.py'; TILING_SHA = '0868990ee2027ba493593d514607acc0aad729ed94c7cf61b1cf3d1f22a08b45'


def sweep(a, b, ivs):
    """exact 1-D cover of [a, b] by closed intervals ivs (Fractions); returns list of gaps."""
    gaps = []; cur = a
    for x0, x1 in sorted(ivs):
        if x1 < cur: continue
        if x0 > cur: gaps.append([float(cur), float(x0)]);
        cur = max(cur, x1)
        if cur >= b: break
    if cur < b: gaps.append([float(cur), float(b)])
    return gaps


def main():
    t0 = time.time(); RUN = Path(sys.argv[1]).resolve(); R = RUN / (sys.argv[2] if len(sys.argv) > 2 else 'replay_check'); shutil.rmtree(R, ignore_errors=True); R.mkdir()
    for f in ('verify_zs5.py', 'model5.py', 'replay5.py', 'heights.py', 'sech5.py'): shutil.copy(V4 / 'lib' / f, R / f)
    assert D.sha(R / 'verify_zs5.py') == D.VERIFY_ZS5_SHA
    P = json.load(open(RUN / 'pieces.json')); T0 = P['T0']; assert isinstance(T0, int) and P['format'] == 'atlas_v5'
    G = Grid(T0, P['grid']); e = G.edge
    tlo, thi, tnote = D.target_offsets(T0, P['target_input'][0], P['target_input'][1], P['grid']); assert [tlo, thi] == P['target']
    kl, kh = D.hull_bins(G, tlo, thi); hull_ok = [kl, kh] == P['hull_bins'] and P['hull'] == [e(kl), e(kh)]
    certs = sorted(glob.glob(str(RUN / 'certs' / 'cert_*.json'))); struct = {}
    for f in certs:
        c = json.load(open(f)); ka, kb = c['piece_bins']; k0, k1 = c['bins']
        ok = (c['T0'] == T0 and c['grid'] == P['grid'] and c['evaluator'] == P['evaluator'] and c['format'] == 'atlas_v5' and c.get('mode', 'main') == 'main' and kl <= ka < kb <= kh and [k0, k1] == [ka - P['wm_bins'], kb + P['wm_bins']]
              and c['regions'] == [[e(ka), e(kb), 0.0, 0.5]])
        struct[f] = ok
    npc = sorted(glob.glob(str(RUN / 'certs_np' / 'cert_*.json')))
    for f in npc:
        c = json.load(open(f)); struct[f] = c['T0'] == T0 and c['grid'] == P['grid'] and c['evaluator'] == P['evaluator'] and c['format'] == 'atlas_v5' and c.get('mode') == 'noparity' and len(c['regions']) == 1 and c['regions'][0][2:] == [0.0, 0.0]
    g = D.guarded([D.PY, '-u', '-B', 'replay5.py', 'replay.jsonl'] + certs + npc, R, R / 'replay5.log',
                  env=dict(os.environ, VERIFY_ZS5_SHA=D.VERIFY_ZS5_SHA, PYTHONDONTWRITEBYTECODE='1')) if certs else dict(rc=None, peak_gb=0, seconds=0, killed=None)
    recs = [json.loads(l) for l in open(R / 'replay.jsonl')] if (R / 'replay.jsonl').exists() else []
    by = {}
    for r in recs: by.setdefault(r['cert'], {})['harden' if r['hardened'] else 'plain'] = r
    passed = [f for f in certs if struct[f] and by.get(f, {}).get('plain', {}).get('passed') and by.get(f, {}).get('harden', {}).get('passed')]
    # tiling
    sp = importlib.util.spec_from_file_location('tl', TILING); TL = importlib.util.module_from_spec(sp); sp.loader.exec_module(TL)
    RD = R / 'tiling_rects'; RD.mkdir(); rects = []; d0 = []
    for f in passed:
        for i, rg in enumerate(json.load(open(f))['regions']):
            q = RD / f'{Path(f).stem}_{i}.json'; json.dump(dict(region=rg, source=f), open(q, 'w')); rects.append(q)
            if rg[2] == 0.0: d0.append((Fr(rg[0]), Fr(rg[1])))
    _, s_h = TL.check('hull', [(Fr(e(kl)), Fr(e(kh)), Fr(0), Fr(0.5))], rects)
    _, s_t = TL.check('target', [(Fr(tlo), Fr(thi), Fr(0), Fr(0.5))], rects)
    g0 = sweep(Fr(e(kl)), Fr(e(kh)), d0)
    til = dict(coordinates='offsets from T0 (exact translation)', T0=T0, tiling_script=TILING, tiling_sha256=D.sha(TILING), tiling_sha_ok=D.sha(TILING) == TILING_SHA, hull=[e(kl), e(kh)], target=[tlo, thi],
               regions=len(rects), seams_hull=len(s_h), seams_target=len(s_t), gaps_d0=g0, seams=(s_h + s_t)[:20])
    mins = [by[f][m]['min_candidate_lower'] for f in passed for m in ('plain', 'harden')]
    # claim (B), THEORY_V4 section 10: every interval of every passed main certificate (within its region) inside passed no-parity regions
    npp = [f for f in npc if struct[f] and by.get(f, {}).get('plain', {}).get('passed') and by.get(f, {}).get('harden', {}).get('passed')]
    segs = [(Fr(rg[0]), Fr(rg[1])) for f in npp for rg in json.load(open(f))['regions']]; uncovered = []; nseg = 0
    for f in passed:
        c = json.load(open(f)); x0, x1 = c['regions'][0][:2]
        for t1, t2 in c['zs_intervals']:
            if t1 <= x1 and t2 >= x0:
                nseg += 1; gp = sweep(Fr(max(t1, x0)), Fr(min(t2, x1)), segs)
                if gp: uncovered.append(dict(cert=Path(f).name, interval=[t1, t2], gaps=gp))
    npmins = [by[f][m]['min_candidate_lower'] for f in npp for m in ('plain', 'harden')]
    claimB = dict(np_certificates=len(npc), np_passed_both=len(npp), intervals_to_cover=nseg, uncovered=uncovered,
                  np_min_candidate_lower=min(npmins, default=None), verifier='pinned verify_zs5.py with one line changed (replay5.noparity_check)')
    res = dict(run=str(RUN), hull_ok=hull_ok, certificates=len(certs), structure_ok=sum(struct.values()), passed_both=len(passed),
               failed=[dict(cert=f, structure=struct[f], plain=by.get(f, {}).get('plain', {}).get('passed'), harden=by.get(f, {}).get('harden', {}).get('passed'))
                       for f in certs if f not in passed],
               min_candidate_lower=min(mins, default=None), replay_process=g, tiling=til,
               passed=bool(hull_ok and certs and len(passed) == len(certs) and not s_h and not s_t and not g0 and til['tiling_sha_ok']),
               claim_B=claimB,
               seconds=round(time.time() - t0, 2))
    res['passed_B'] = bool(res['passed'] and not uncovered and len(npp) == len(npc))
    json.dump(res, open(R / 'replay_check.json', 'w'), indent=1)
    X = lambda u: str(Fr(T0) + Fr(u))
    json.dump(dict(T0=T0, grid=P['grid'], hull=[X(e(kl)), X(e(kh))], target=[X(tlo), X(thi)], target_note=tnote,
                   passed_regions=[[X(rg[0]), X(rg[1]), str(Fr(rg[2])), str(Fr(rg[3]))] for f in passed for rg in json.load(open(f))['regions']]),
              open(R / 'exact_heights.json', 'w'), indent=1)
    print(json.dumps(dict(passed=res['passed'], passed_B_simple_without_lemma2=res['passed_B'], np=f"{len(npp)}/{len(npc)}", certs=f"{len(passed)}/{len(certs)}", seams=[len(s_h), len(s_t), len(g0)], min_candidate_lower=res['min_candidate_lower'],
                          seconds=res['seconds'], replay_peak_gb=g.get('peak_gb'))), flush=True)
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main()
