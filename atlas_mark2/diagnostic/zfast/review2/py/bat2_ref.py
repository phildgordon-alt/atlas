"""bat2_ref.py: stock-Arb references (bin/ref = copy of review/src/rv_ref.c, links only FLINT 3.6.0) for every battery point.
AZ for Z (acb_dirichlet_hardy_z), AR for rows (acb_dirichlet_zeta_jet, P = Re(-zeta'/zeta)).  Watchdog 800 MB footprint."""
import json, subprocess, os
R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review2'
WD = '/Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh'
pts = json.load(open(f'{R}/data/bat2_points.json'))
zl, rl = set(), set()
for g in ('Zsess', 'Zstress_sess'):
    for s in pts[g]:
        for u in s['us']: zl.add((s['T0'], u))
for p in pts['Zsingle']: zl.add((p['T0'], p['u']))
for g in ('rows', 'rows_stress'):
    for s in pts[g]:
        for u in s['us']:
            for a in (2.8, 1.6): rl.add((s['T0'], u, a))
inp = f'{R}/data/bat2_ref.in'
with open(inp, 'x') as f:
    for T0, u in sorted(zl): f.write(f'AZ {T0} {u.hex()} 160\n')
    for T0, u, a in sorted(rl): f.write(f'AR {T0} {u.hex()} {a} 160\n')
env = dict(os.environ, FP_MB='800', RSS_KB='800000', TL='14400')
r = subprocess.run([WD, f'{R}/bin/ref', inp, f'{R}/data/bat2_ref.jsonl'], env=env, capture_output=True, text=True)
print(r.stdout, r.stderr[-500:])
