"""X1-X4 (PREDICTIONS_M5c): review2 fixes in v13b.  (v2 of m5c_validate.py: parses nan/inf.)"""
import json, subprocess, math
from flint import arb, ctx
ctx.prec = 300
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'; TH = '2'
def run(cmd, inp, check=True):
    r = subprocess.run(['nice', '-n', '19'] + cmd, input=inp, capture_output=True, text=True)
    if check and r.returncode != 0: raise RuntimeError(r.stderr[-300:])
    return r
import re
def jl(r): return [json.loads(re.sub(r':\s*(-?)(nan|inf)\b', lambda m: ': ' + ('-' if m.group(1) else '') + ('NaN' if m.group(2) == 'nan' else 'Infinity'), l)) for l in r.stdout.splitlines() if l.strip()]   # v2: NaN/inf from indeterminate balls
res = {}
# X1: m1 trigger
T0 = 999998594275; M = math.isqrt(int(T0 / (2 * math.pi))) + 1
cand = [m for m in range(M - 3, M + 4)]
tm = min((2 * arb.pi() * arb(m) ** 2 for m in cand), key=lambda x: abs(float((x - T0).mid())))
uj = float((tm - T0).mid())
pts = [uj - 1e-9, uj + 1e-9, uj + 0.5]
r = jl(run([B + 'bin/zfm4_cli.v13b', str(T0), repr(round(uj)), '4', '0.15', '18', TH, '12'], ''.join(f'r 2.8 {u!r}\n' for u in pts)))
res['X1'] = [dict(u=d['u'], ok=d['res']['ok'], P=d['res']['P']) for d in r[1:]]
print('X1', res['X1'])
# X2: guards
g1 = run([B + 'bin/zfm4_cli.v13b', '10000000000', '1.0', '4', '0.15', '18', '1', '40'], 'z 1.0\n', check=False)
g2 = run([B + 'bin/zfm4_cli.v13b', '500', '1.0', '4', '0.15', '18', '1', '12'], 'z 1.0\n', check=False)
g3 = run([B + 'bin/zfm4_cli.v13b', '10000000000', '1.0', '4', '0.15', '18', '1', '12'], 'z 1.0\n', check=False)
res['X2'] = dict(J40_aborts=g1.returncode != 0, J40_msg=g1.stderr.strip()[-60:], small_t_aborts=g2.returncode != 0, small_msg=g2.stderr.strip()[-60:], production_ok=g3.returncode == 0)
print('X2', res['X2'])
# X3: containment vs stored Arb references
refs = {}
for f in ['runs/m2/val_arb_le15.jsonl', 'runs/m2/val_arbsmooth_1e16.jsonl', 'runs/m2/high_arbsmooth_1e18b.jsonl', 'runs/m2/high_arbsmooth_1e20.jsonl', 'runs/m5/arbsmooth_1e21.jsonl']:
    for d in map(json.loads, open(B + f)):
        if -3 <= float(d['u']) <= 5: refs.setdefault(d['T0'], []).append(d)
tot = cont = 0; x4 = []
for T, L in sorted(refs.items(), key=lambda q: int(q[0])):
    inp = ''.join(f"z {d['u']}\n" for d in L)
    a = jl(run([B + 'bin/zfm4_cli.v13b', T, '1.0', '4', '0.15', '18', TH, '12'], inp))[1:]
    b = jl(run([B + 'bin/zfm4_cli.v12a', T, '1.0', '4', '0.15', '18', TH, '12'], inp))[1:]
    for d, x, y in zip(L, a, b):
        rb = arb(d['Z']); zb = arb(x['res']['Z'])
        tot += 1; cont += bool(rb.mid() - rb.rad() >= zb.mid() - zb.rad() and rb.mid() + rb.rad() <= zb.mid() + zb.rad())
        x4.append(dict(T0=T, same_mid=x['res']['Z_mid'] == y['res']['Z_mid'], printed_rad_v13=float(zb.rad()), printed_rad_v12=float(arb(y['res']['Z']).rad())))
rows = {}
for f in ['runs/m2/row_arb_le14.jsonl', 'runs/m2/row_arb_15b.jsonl']:
    for d in map(json.loads, open(B + f)): rows.setdefault(d['T0'], []).append(d)
rt = rc = 0
for T, L in sorted(rows.items(), key=lambda q: int(q[0])):
    a = jl(run([B + 'bin/zfm4_cli.v13b', T, '1.0', '4', '0.15', '18', TH, '12'], ''.join(f"r {d['a']} {d['u']}\n" for d in L)))[1:]
    for d, x in zip(L, a):
        rt += 1
        rc += all(bool(arb(d[f]).mid() - arb(d[f]).rad() >= arb(x['res'][f]).mid() - arb(x['res'][f]).rad() and arb(d[f]).mid() + arb(d[f]).rad() <= arb(x['res'][f]).mid() + arb(x['res'][f]).rad()) for f in ['zeta_re', 'zeta_im', 'dzeta_re', 'dzeta_im', 'P']) and x['res']['ok'] == 1
res['X3'] = dict(z_points=tot, z_contained=cont, heights=sorted(refs, key=int), row_points=rt, row_contained=rc)
res['X4'] = dict(points=len(x4), same_mid=sum(x['same_mid'] for x in x4), median_printed_rad_ratio=sorted(x['printed_rad_v13'] / x['printed_rad_v12'] for x in x4)[len(x4) // 2])
print('X3', res['X3']); print('X4', res['X4'])
json.dump(res, open(B + 'runs/m5c/X1_X4.json', 'w'), indent=1)
