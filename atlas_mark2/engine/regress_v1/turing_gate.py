"""engine/regress_v1 Turing count-equality gate (new file, amendment A6; PREDICTIONS_M8).  REQUIRED for every atlas_v5z5 window from M8 on.

Why (RESULTS_M7 NC-W4 / NC-W4b): a v5z5 window's pieces overlap (window = piece +- 2), so each zero is listed and credited by ~5 main
certificates.  Deleting a zero from one certificate, or from all of them, leaves every replay record passing (less credit is still a
valid certificate) - the replay cannot see a missing zero.  The claim "these are all the zeros in the target" then rests on the count.
This gate makes the separate-method Turing count (tools/scan_turing5.py, exact Delta_T) a required check:

  G-T1  the Turing record is from scan_turing5 (tool string; its tool_sha256 is reported), same T0 as pieces.json
  G-T2  both target ends u_lo, u_hi are Turing points (exact rational equality) and both are pinned (N_lower == N_upper, sign decided)
  G-T3  the run's replay passed (claim A) and passed_B (claim B), in replay_check/ and, if present, replay_check_independent/
  G-T4  the certified sign-change intervals of the main certificates lying inside the target are pairwise disjoint
  G-T5  no certified interval straddles a target end
  G-T6  N(T0 + u_hi) - N(T0 + u_lo) == number of those intervals

  python -m engine.regress_v1.turing_gate check RUN TURING_JSON [TURING_JSON ...]   gate one run (first record holding both ends)
  python -m engine.regress_v1.turing_gate all                                        every closed zfast window with a scan_turing5 record
  python -m engine.regress_v1.turing_gate controls RUN TURING_JSON                   NC-T1..NC-T4 on COPIES under work/ (must all FAIL)
Writes engine/regress_v1/reports/turing_<kind>_<stamp>.json.  Read-only on every run directory."""
import argparse, glob, json, shutil, sys, time
from fractions import Fraction as F
from pathlib import Path
from .common import HERE, WORK, RegressError, guard
from . import zfast

ZF = zfast.ZF
zfast.TREES.setdefault('atlas_v5z5', (ZF / 'atlas_v5z5', 'V5Z5_FREEZE.sha256'))     # in memory only
REPORTS = HERE / 'reports'
M8 = ZF / 'runs' / 'm8'


def _turing_point(T, u):
    for k, rec in T['turing'].items():
        if F(rec.get('v_exact', k)) == F(u):
            return rec
    return None


def gate(run, tjsons):
    run = Path(run); P = json.load(open(run / 'pieces.json')); T0 = int(P['T0']); ulo, uhi = (F(x) for x in P['target'])
    fails = []; used = None; rlo = rhi = None
    for tj in tjsons:
        T = json.load(open(tj))
        if not str(T.get('tool', '')).startswith('scan_turing5') or int(T['T0']) != T0: continue
        a, b = _turing_point(T, ulo), _turing_point(T, uhi)
        if a is not None and b is not None: used, rlo, rhi = (str(tj), T.get('tool_sha256')), a, b; break
    if used is None: fails.append('G-T1/G-T2: no scan_turing5 record with T0 and both target ends')
    else:
        if not (rlo['pinned'] and rhi['pinned'] and rlo['N'] is not None and rhi['N'] is not None): fails.append('G-T2: a target end is not pinned')
    for sub in ('replay_check', 'replay_check_independent'):
        f = run / sub / 'replay_check.json'
        if sub == 'replay_check' and not f.exists(): fails.append('G-T3: no replay_check.json'); continue
        if f.exists():
            rc = json.load(open(f))
            if not (rc.get('passed') is True and rc.get('passed_B') is True): fails.append(f'G-T3: {sub} passed={rc.get("passed")} passed_B={rc.get("passed_B")}')
    iv = set()
    for f in sorted(glob.glob(str(run / 'certs' / 'cert_*.json'))):
        for a, b in json.load(open(f))['zs_intervals']: iv.add((a, b))
    inside = sorted(x for x in iv if ulo <= F(x[0]) and F(x[1]) <= uhi)
    straddle = sorted(x for x in iv if (F(x[0]) < ulo < F(x[1])) or (F(x[0]) < uhi < F(x[1])))
    if any(not F(inside[i][1]) <= F(inside[i + 1][0]) for i in range(len(inside) - 1)): fails.append('G-T4: certified intervals not disjoint')
    if straddle: fails.append(f'G-T5: {len(straddle)} interval(s) straddle a target end')
    count = (rhi['N'] - rlo['N']) if used and rlo['N'] is not None and rhi['N'] is not None else None
    if count is not None and count != len(inside): fails.append(f'G-T6: Turing count {count} != certified sign changes {len(inside)}')
    return dict(run=str(run), T0=str(T0), target=[str(ulo), str(uhi)], turing_record=used,
                N_lo=rlo and rlo['N'], N_hi=rhi and rhi['N'], U_minus_L=[rlo and rlo['U_minus_L'], rhi and rhi['U_minus_L']],
                turing_count=count, certified_sign_changes=len(inside), straddling=straddle, fails=fails, ok=not fails)


def _all_records():
    return sorted(glob.glob(str(M8 / 'turing5_recount' / '*.json')) + glob.glob(str(M8 / 'fresh' / '*' / 'scan_turing.json'))
                  + glob.glob(str(M8 / '*' / 'scan_turing.json')) + glob.glob(str(M8 / '*' / 'turing5_*.json')))


def gate_all():
    recs = _all_records(); out = []
    for r in zfast.runs():
        if not r['recorded_closed']: out.append(dict(run=r['id'], skipped='not closed (failed-closed run; no claim)')); continue
        g = gate(r['run'], recs); g['id'] = r['id']; out.append(g)
    gated = [x for x in out if 'ok' in x]
    covered = [x for x in gated if x['turing_record'] is not None]
    return dict(check='Turing count-equality over every closed zfast window', windows=len(out), gated=len(gated),
                with_turing_record=len(covered), passed=sum(x['ok'] for x in covered),
                no_record=[x['id'] for x in gated if x['turing_record'] is None], results=out,
                ok=all(x['ok'] for x in covered) and len(covered) > 0)


def controls(run, tj, stamp):
    run = Path(run).resolve(); S = WORK / f'turing_nc_{stamp}'; S.mkdir(parents=True)
    def copy_run(name):
        d = S / name; d.mkdir(); shutil.copy2(run / 'pieces.json', d / 'pieces.json')
        shutil.copytree(run / 'certs', d / 'certs'); shutil.copytree(run / 'certs_np', d / 'certs_np')
        for sub in ('replay_check', 'replay_check_independent'):
            if (run / sub / 'replay_check.json').exists(): (d / sub).mkdir(); shutil.copy2(run / sub / 'replay_check.json', d / sub / 'replay_check.json')
        return d
    res = {}
    d0 = copy_run('baseline'); res['baseline (copy, unmodified)'] = gate(d0, [tj])
    # NC-T1: delete one zero (the median interval inside the target) from ALL main certificates that list it, and its S-layer certificate
    d1 = copy_run('nct1'); P = json.load(open(run / 'pieces.json')); ulo, uhi = (F(x) for x in P['target'])
    iv = sorted({tuple(x) for f in (d1 / 'certs').glob('cert_*.json') for x in json.load(open(f))['zs_intervals']
                 if ulo <= F(x[0]) and F(x[1]) <= uhi})
    z = list(iv[len(iv) // 2]); hit = []
    for f in sorted((d1 / 'certs').glob('cert_*.json')):
        c = json.load(open(f))
        if z in c['zs_intervals']:
            k = c['zs_intervals'].index(z); del c['zs_intervals'][k]; del c['w'][k]; json.dump(c, open(f, 'w')); hit.append(f.name)
    np_hit = []
    for f in sorted((d1 / 'certs_np').glob('*.json')):
        if json.load(open(f)).get('interval') == z: f.unlink(); np_hit.append(f.name)     # copy under work/ only
    res['NC-T1 one zero deleted from all covering certificates'] = dict(gate(d1, [tj]), deleted=z, main_certs_hit=hit, np_certs_removed=np_hit)
    # NC-T2: Turing record with N(T0 + u_hi) + 1
    T = json.load(open(tj)); T2 = json.loads(json.dumps(T)); r = _turing_point(T2, uhi); r['N'] += 1; r['N_lower'] += 1; r['N_upper'] += 1
    p2 = S / 'nct2_turing.json'; json.dump(T2, open(p2, 'w')); res['NC-T2 Turing N(hi) + 1'] = gate(d0, [p2])
    # NC-T3: one end unpinned
    T3 = json.loads(json.dumps(T)); r = _turing_point(T3, ulo); r['N_upper'] = r['N_lower'] + 1; r['pinned'] = False; r['N'] = None
    p3 = S / 'nct3_turing.json'; json.dump(T3, open(p3, 'w')); res['NC-T3 lower end unpinned'] = gate(d0, [p3])
    # NC-T4: a record not produced by scan_turing5 (the pre-fix tools)
    T4 = json.loads(json.dumps(T)); T4['tool'] = 'scan_turing4.py'
    p4 = S / 'nct4_turing.json'; json.dump(T4, open(p4, 'w')); res['NC-T4 record from a pre-fix tool'] = gate(d0, [p4])
    det = {k: (not v['ok']) for k, v in res.items() if k.startswith('NC')}
    return dict(check=f'Turing gate negative controls on {run}', turing_json=str(tj), results=res, detected=det,
                baseline_ok=res['baseline (copy, unmodified)']['ok'], ok=res['baseline (copy, unmodified)']['ok'] and all(det.values()))


def main():
    guard()
    ap = argparse.ArgumentParser(prog='python -m engine.regress_v1.turing_gate')
    ap.add_argument('mode', choices=('check', 'all', 'controls')); ap.add_argument('args', nargs='*')
    a = ap.parse_args(); stamp = time.strftime('%Y%m%d_%H%M%S'); REPORTS.mkdir(exist_ok=True)
    if a.mode == 'check':
        if len(a.args) < 2: ap.error('check RUN TURING_JSON ...')
        rep = dict(check='Turing count-equality gate', **gate(a.args[0], a.args[1:]))
    elif a.mode == 'all': rep = gate_all()
    else:
        if len(a.args) != 2: ap.error('controls RUN TURING_JSON')
        rep = controls(a.args[0], a.args[1], stamp)
    rep.update(stamp=stamp, amendment='PREREG_AMENDMENTS.md A6')
    p = REPORTS / f'turing_{a.mode}_{stamp}.json'; json.dump(rep, open(p, 'w'), indent=1, default=str)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('results',)}, default=str, indent=1)[:4000])
    if 'detected' in rep: print(json.dumps(rep['detected'], indent=1))
    print(f'REPORT {p}: {"PASS" if rep["ok"] else "FAIL"}', flush=True)
    sys.exit(0 if rep['ok'] else 1)


if __name__ == '__main__':
    main()
