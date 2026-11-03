"""bat2_run.py DRIVER TAG [v10b] [light]: run the review2 battery with a driver binary (production rd3.v12a / rd3.v10b or a mutant)
and judge containment against the stock-Arb references (data/bat2_ref.jsonl).  Output data/bat2_<TAG>.json (never overwritten).
light: skip T0 >= 1e14 in the session/single families (mutant runs)."""
import json, subprocess, sys, time
from flint import arb, ctx
R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review2'
drv, tag = sys.argv[1], sys.argv[2]
v10b = 'v10b' in sys.argv[3:]; light = 'light' in sys.argv[3:]
ctx.prec = 300
pts = json.load(open(f'{R}/data/bat2_points.json'))
pts.update(json.load(open(f'{R}/data/bat2_points_extra.json')))
ZR, PR = {}, {}
for l in list(open(f'{R}/data/bat2_ref.jsonl')) + list(open(f'{R}/data/bat2_ref_extra.jsonl')):
    d = json.loads(l)
    if d['cmd'] == 'AZ': ZR[(int(d['T0']), float.fromhex(d['u']))] = d['Z']
    else: PR[(int(d['T0']), float.fromhex(d['u']), d['a'])] = d

def run(lines):
    r = subprocess.run(['nice', '-n', '19', drv], input='\n'.join(lines) + '\n', capture_output=True, text=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()], r.returncode, r.stderr[-300:]

def judge(zs, rs, what):
    z, r = arb(zs), arb(rs)
    if not z.is_finite() or not (float(z.rad()) < 1e300):
        return dict(ok=True, excluded='undecided', ratio=0.0, what=what, z=zs, ref=rs)
    ok = z.contains(arb(r.mid())) and z.overlaps(r)
    rad = float(z.rad()); dif = abs(float((z.mid() - r.mid())))
    return dict(ok=bool(ok), ratio=dif / rad if rad > 0 else float('inf'), what=what, z=zs, ref=rs)

fams = {}
def add(f, rec): fams.setdefault(f, []).append(rec)
t0 = time.time()
# K
o, rc, er = run(['KER 300000 7']); add('K', dict(ok=bool(o and o[0]['ok']), ratio=(o[0]['max_cos'] / o[0]['ZF_EC']) if o else 9, what=str(o)[:200]))
# PH
PH = ['PH 10000000000 0.5 50000 300 6', 'PH 1000000000000 1.5 400000 2000 8', 'PH 10000000000000000 0.25 30000000 1564 12',
      'PH 10000000000000000 0.25 30000000 9000 24', 'PH 100000000000000000000 0.7 3000000000 16384 12',
      'PH 10000000000000000000000 0.3 30000000000 16384 12']
o, rc, er = run(PH)
for d in o: add('PH', dict(ok=bool(d['ok']), ratio=d['ratio'], what=f"J{d['J']} B{d['B']} T0 {d['T0']}"))
if len(o) < len(PH): add('PH', dict(ok=False, ratio=9, what='crash ' + er))
# WP
WP = []
for T0, n0, B in ((10 ** 16, 30000000, 1564), (10 ** 12, 200000, 700), (10 ** 20, 3000000000, 16384), (10 ** 10, 5000, 64), (10 ** 10, 1200, 200)):
    for kind in range(4):
        for a in ((2.8, 1.6) if kind < 2 else (1.6,)): WP.append(f'WP {T0} {n0} {B} {kind} {a} 3000')
o, rc, er = run(WP)
for d in o: add('WP', dict(ok=bool(d['ok']), ratio=d['ratio'], what=f"kind{d['kind']} a{d['a']} n0 {d['n0']} B {d['B']}"))
if len(o) < len(WP): add('WP', dict(ok=False, ratio=9, what='crash ' + er))
# single-point Z
CFG = dict(prod='12 16384 -72 0', J6='6 65536 -20 0', J24='24 65536 -72 0', J8b64='8 64 -72 0', kcorr2='12 16384 -72 2')
L = [p for p in pts['Zsingle'] if not (light and p['T0'] >= 10 ** 14)]
o, rc, er = run([f"Z {p['T0']} {p['u'].hex()} {CFG[p['cfg']]}" for p in L])
for p, d in zip(L, o): add('Z1_' + ('prod' if p['cfg'] == 'prod' else 'stress'), judge(d['Z'], ZR[(p['T0'], p['u'])], f"{p['cfg']} {p['T0']}"))
if len(o) < len(L): add('Z1_prod', dict(ok=False, ratio=9, what='crash ' + er))
# sessions
H, D, K = (3.0, 0.2, 16) if v10b else (4.0, 0.15, 18)
def sess_lines(group, stress):
    out = []
    for s in pts[group]:
        if light and s['T0'] >= 10 ** 14: continue
        h, dd, k = (s['H'], s['Delta'], s['K']) if stress else (H, D, K)
        us = [u for u in s['us'] if abs(u - s['u0']) <= h]
        out.append((s, us, f"SZ {s['T0']} {s['u0']!r} {h} {dd} {k} 12 {len(us)} " + ' '.join(u.hex() for u in us)))
    return out
for group, fam, stress in (('Zsess', 'SZ_prod', False), ('Zstress_sess', 'SZ_stress', True), ('SZx', 'SZ_stress2', True)):
    SL = sess_lines(group, stress)
    o, rc, er = run([x[2] for x in SL])
    for (s, us, _), d in zip(SL, o):
        for p in d['pts']:
            u = float.fromhex(p['u']); add(fam, judge(p['Z'], ZR[(s['T0'], u)], f"{s.get('cls', 'K%d' % s.get('K', 0))} {s['T0']} {u!r}"))
    if len(o) < len(SL): add(fam, dict(ok=False, ratio=9, what='crash ' + er))
# rows
for group, fam, stress in (('rows', 'ROW_prod', False), ('rows_stress', 'ROW_stress', True), ('ROWx', 'ROW_stress2', True)) + ((() if v10b else (('rows', 'ROW1_prod', False), ('ROWx', 'ROW1_stress2', True)))):
    lines = []; meta = []
    for s in pts[group]:
        h, dd, k = (s['H'], s['Delta'], s['K']) if stress else ((3.0, 0.2, 16) if fam.startswith('ROW1') else (H, D, K))
        us = [u for u in s['us'] if abs(u - s['u0']) <= h]
        for a in (2.8, 1.6):
            c = 'S1' if (v10b or fam.startswith('ROW1')) else 'S3'
            lines.append(f"{c} {s['T0']} {s['u0']!r} {h} {dd} {k} 12 {a} {len(us)} " + ' '.join(u.hex() for u in us)); meta.append((s, a))
    o, rc, er = run(lines)
    for (s, a), d in zip(meta, o):
        for p in d['pts']:
            u = float.fromhex(p['u']); ref = PR[(s['T0'], u, a)]
            for key, rk in (('P', 'P'), ('zr', 'zr'), ('zi', 'zi'), ('dzr', 'dzr'), ('dzi', 'dzi')):
                rec = judge(p[key], ref[rk], f"{key} a{a} {s['T0']} {u!r}")
                if not p['ok']: rec = dict(ok=True, excluded='refused', ratio=0.0, what=rec['what'] + ' ok=0', z=rec['z'], ref=rec['ref'])
                add(fam, rec)
    if len(o) < len(lines): add(fam, dict(ok=False, ratio=9, what='crash ' + er))
res = dict(driver=drv, tag=tag, v10b=v10b, light=light, sec=time.time() - t0, families=[])
for f, recs in fams.items():
    fails = [r for r in recs if not r['ok']]
    res['families'].append(dict(family=f, n=len(recs), excluded=sum(1 for r in recs if r.get('excluded')), fails=len(fails), max_ratio=max(r['ratio'] for r in recs), first_fail=fails[0] if fails else None))
res['detected'] = any(f['fails'] for f in res['families'])
json.dump(res, open(f'{R}/data/bat3_{tag}.json', 'x'), indent=1)
print(tag, 'detected' if res['detected'] else 'all-pass', [(f['family'], f['n'], f['excluded'], f['fails'], '%.3g' % f['max_ratio']) for f in res['families']], '%.0fs' % res['sec'])
