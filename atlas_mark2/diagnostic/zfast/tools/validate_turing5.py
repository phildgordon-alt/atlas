"""M8 step 1 validation of scan_turing5.py recount: every earlier stored Turing count (scan_turing v1-v4, turing_extra, turing_extra2) is
recomputed from the SAVED scans (no zfast call) and compared.  Pass rule: for every earlier record with an integer (exact) Delta_T,
N_lower and N_upper identical (and the U, L 12-digit strings identical); for the one record with the non-exact clipped Delta_T
(scan4_1e22 v = 100, Delta 39.999999999, unpinned) the new value at the exact Delta_T must be pinned and equal the M7-A1 value.
v1 (scan_1e16) stored N as a float and saved no grid: recounted on scan2_1e16 and compared as float(N_new) == N_old.  Writes runs/m8/turing5_validation.json."""
import json, os, subprocess, sys
from fractions import Fraction as F
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'): raise SystemExit('refusing -O')
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast'; PY = sys.executable; O = ZF + '/runs/m8/turing5_recount'
os.makedirs(O, exist_ok=True)
# (saved scan, earlier record file, its key, DT for the recount, windows)
JOBS = [('runs/m5/scan2_1e16', 'runs/m5/scan_1e16/scan_turing.json', 40, [(0, 2), (18, 20)]),
        ('runs/m5/scan2_1e16', 'runs/m5/scan2_1e16/scan_turing.json', 40, [(0, 2), (18, 20)]),
        ('runs/m5/scan2_1e20', 'runs/m5/scan2_1e20/scan_turing.json', 40, [(0, 2), (4, 6)]),
        ('runs/m5/scan2_1e21', 'runs/m5/scan2_1e21/scan_turing.json', 40, [(-6, -4), (0, 2)]),
        ('runs/m5/scan2_1e22', 'runs/m5/scan2_1e22/scan_turing.json', 40, [(0, 2), (17, 19)]),
        ('runs/m5/scan2_1e23', 'runs/m5/scan2_1e23/scan_turing.json', 40, [(0, 2), (2, 4)]),
        ('runs/m5/scan2_1e23', 'runs/m6/turing_extra_1e23.json', 40, [(-24, -22), (-2, 0), (0, 2)]),
        ('runs/m6/scan3_1e24', 'runs/m6/scan3_1e24/scan_turing.json', 40, [(-3, -1), (0, 2)]),
        ('runs/m7/scan4_1e22', 'runs/m7/scan4_1e22/scan_turing.json', 40, [(0, 100)]),
        ('runs/m7/scan4_1e22', 'runs/m7/turing2_1e22_D39.json', 39, [(0, 100)])]
out = []; allok = True
for scan, rec, DT, wins in JOBS:
    old = json.load(open(f'{ZF}/{rec}'))['turing']
    pts = sorted({F(k) for k in old} | {F(x) for w in wins for x in w})
    tag = os.path.basename(os.path.dirname(rec)) + '_' + os.path.basename(rec).replace('.json', '') + '__' + os.path.basename(scan) + f'_DT{DT}'
    dst = f'{O}/{tag}.json'
    cmd = [PY, '-B', f'{ZF}/tools/scan_turing5.py', 'recount', f'{ZF}/{scan}', dst, '--points', ','.join(str(p) for p in pts), '--DT', str(DT)]
    for a, b in wins: cmd += ['--win', f'{a},{b}']
    if not os.path.exists(dst): subprocess.run(cmd, check=True, capture_output=True)
    new = json.load(open(dst))
    for k, o in old.items():
        n = new['turing'][str(F(k))]
        exact_D = float(o['Delta']).is_integer()
        if 'N_lower' in o:
            same = (n['N_lower'] == o['N_lower'] and n['N_upper'] == o['N_upper'])
            same_str = (n['U'] == o['U'] and n['L'] == o['L'])
        else:   # v1: float N
            same = (o['N'] is not None and float(n['N']) == o['N']); same_str = True   # v1 saved no grid: recounted on scan2_1e16 (same session params); strings not compared
        if exact_D:
            ok = same and same_str and n['pinned'] == o['pinned'] and F(n['Delta_exact']) == F(o['Delta'])
            kind = 'reproduce'
        else:
            ok = n['pinned'] and not o['pinned']; kind = 'F-M7a fixed (old Delta not exact)'
        allok &= ok
        out.append(dict(record=rec, v=k, kind=kind, old=dict(N=o.get('N'), lo=o.get('N_lower'), hi=o.get('N_upper'), D=o['Delta'], pinned=o['pinned'], UmL=o['U_minus_L']),
                        new=dict(N=n['N'], lo=n['N_lower'], hi=n['N_upper'], D=n['Delta_exact'], pinned=n['pinned'], UmL=n['U_minus_L']),
                        U_L_strings_identical=same_str, ok=ok))
    for w, r in new['windows'].items():
        out.append(dict(record=rec, window=w, count=r['count'], sign_changes=r['sign_changes_in_window'], straddling=r['straddling'],
                        ok=(r['count'] == r['sign_changes_in_window'] and not r['straddling'])))
        allok &= out[-1]['ok']
# the M7-A1 value of N(T0 + 100) must equal the new exact-D40 value
a = json.load(open(f'{O}/scan4_1e22_scan_turing__scan4_1e22_DT40.json'))['turing']['100']['N']
b = json.load(open(f'{ZF}/runs/m7/turing2_1e22_D39.json'))['turing']['100.0']['N']
out.append(dict(check='scan4_1e22 v=100: exact D=40 value equals M7-A1 D=39 value', new=a, m7a1=b, ok=(a == b))); allok &= (a == b)
json.dump(dict(ok=allok, records=out), open(ZF + '/runs/m8/turing5_validation.json', 'w'), indent=1)
for x in out:
    if not x['ok']: print('FAIL', x)
print('records', sum(1 for x in out if 'v' in x), 'windows', sum(1 for x in out if 'window' in x), 'ALL OK' if allok else 'NOT OK')
# ---- part 2 (fresh scan_turing5 scans at 1e12-1e18, runs/m8/fresh): N at every window end vs the stored Arb Turing counts in every
# crosscheck.json (atlas_v5z / v5z2 / v5z3 windows, 1e12-1e16 incl. the 1e15+286 pair); 1e17/1e18 have no earlier Turing count (new).
import glob as _g
fresh = {}
for f in _g.glob(ZF + '/runs/m8/fresh/*/scan_turing.json'):
    d = json.load(open(f)); fresh.setdefault(int(d['T0']), []).append(d)
part2 = []
for cc in sorted(_g.glob(ZF + '/atlas_v5z*/runs/*/*/crosscheck.json')):
    c = json.load(open(cc)); T0 = int(c['T0']); P = json.load(open(os.path.dirname(cc) + '/pieces.json')); lo, hi = P['target']
    got = None
    for d in fresh.get(T0, []):
        a, b = d['turing'].get(str(F(lo))), d['turing'].get(str(F(hi)))
        if a and b: got = (a['N'], b['N'], a['pinned'] and b['pinned'])
    if got is None: continue
    ok = (got[0] == c['arb_N'][0] and got[1] == c['arb_N'][1] and got[2]); allok &= ok
    part2.append(dict(crosscheck=cc.replace(ZF + '/', ''), arb_N=c['arb_N'], scan_turing5_N=list(got[:2]), ok=ok))
d0 = json.load(open(ZF + '/runs/m8/turing5_validation.json')); d0['part2_fresh_vs_arb_crosscheck'] = part2; d0['ok'] = allok
json.dump(d0, open(ZF + '/runs/m8/turing5_validation.json', 'w'), indent=1)
print('part2', len(part2), 'crosscheck windows', sum(x['ok'] for x in part2), 'match', 'ALL OK' if allok else 'NOT OK')
