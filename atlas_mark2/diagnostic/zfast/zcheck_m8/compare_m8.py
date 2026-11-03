"""M8 step 2: compare zref_m8 balls (stock FLINT only, no zfast code) with the zfast balls stored in saved scan grids at the same u.
Criterion (CORE_ROADMAP 3a): zref radius <= 1e-10, |mid diff| <= 1e-13, the two balls intersect, and the zfast ball contains the
zref midpoint.  Also stock Arb hardy_z (review2/bin/ref AZ) at 1e12/1e16.  Writes zcheck_m8/compare_m8.json."""
import json, os, sys
import numpy as np
from flint import arb
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'): raise SystemExit('refusing -O')
D = '/Users/kiosk/atlas_mark2/diagnostic/zfast'
GRIDS = {10**12: 'runs/m8/fresh/s5_1e12', 10**16: 'runs/m8/fresh/s5_10000000000000000_c1', 10**20: 'runs/m5/scan2_1e20',
         10**22: 'runs/m7/scan4_1e22', 10**24: 'runs/m6/scan3_1e24'}
out = []
for f in ('zref_low.jsonl', 'zref_1e20.jsonl', 'zref_1e22.jsonl', 'zref_1e24.jsonl'):
    p = f'{D}/zcheck_m8/runs/{f}'
    if not os.path.exists(p): continue
    for line in open(p):
        r = json.loads(line); T0 = int(r['T0']); u = float.fromhex(r['u'])
        g = np.load(f'{D}/{GRIDS[T0]}/grid.npz'); k = np.nonzero(g['u'] == u)[0]
        if len(k) != 1: raise SystemExit(f'u {u} not a grid point of {GRIDS[T0]}')
        k = int(k[0]); zm, zr = float(g['mid'][k]), float(g['rad'][k])
        Z = arb(r['Z']); zf = arb(zm) + arb(0, zr)
        diff = abs(float(arb(r['Z_mid'])) - zm)
        rec = dict(T0=str(T0), u=u, zfast_grid=GRIDS[T0], zfast_mid=zm, zfast_rad=zr, zref=r['Z'], zref_rad=r['Z_rad'], abs_diff=diff,
                   overlap=bool(Z.overlaps(zf)), zfast_contains_zref_mid=bool(zf.contains(arb(r['Z_mid']))),
                   sign_agree=(zm > 0) == (float(arb(r['Z_mid'])) > 0), main_sec=r['main_sec'], threads=r['threads'], N=r['N'])
        rec['ok'] = rec['overlap'] and rec['zfast_contains_zref_mid'] and r['Z_rad'] <= 1e-10 and diff <= 1e-13
        out.append(rec)
json.dump(dict(points=out, ok=all(x['ok'] for x in out)), open(f'{D}/zcheck_m8/compare_m8.json', 'w'), indent=1)
for x in out: print(x['T0'], x['u'], 'diff %.2e zref_rad %.2e zfast_rad %.2e' % (x['abs_diff'], x['zref_rad'], x['zfast_rad']), x['ok'])
