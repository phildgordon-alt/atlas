"""V1b-V1d: v12 rows-from-Z vs v9 single rows, stored Arb jets (M2), v10b row-session radii; Z vs v11 kind-2 Z values. 1 thread."""
import json, subprocess, random
from flint import arb, ctx
ctx.prec = 200
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'; TH = '1'
def run(cmd, inp):
    r = subprocess.run(['nice', '-n', '19'] + cmd, input=inp, capture_output=True, text=True, check=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
def ov(a, b):
    a, b = arb(a), arb(b); return bool(abs(a.mid() - b.mid()) <= a.rad() + b.rad())
def inside(r, z): r, z = arb(r), arb(z); return bool(r.mid() - r.rad() >= z.mid() - z.rad() and r.mid() + r.rad() <= z.mid() + z.rad())
random.seed(1515); out = {}
for T0 in [10**10, 10**13, 10**16]:
    ru = [(random.choice(['2.8', '1.6']), random.uniform(-3, 5)) for _ in range(20)]; zu = [random.uniform(-3, 5) for _ in range(20)]
    C = run([B + 'bin/zfm4_cli.v12a', str(T0), '1.0', '4', '0.15', '18', TH, '12'], ''.join(f'r {a} {u!r}\n' for a, u in ru) + ''.join(f'z {u!r}\n' for u in zu))
    sess = C[0]['session']; C = C[1:]
    R = run([B + 'bin/zfast_row_cli2.v9', '--threads', TH], ''.join(f'{T0} {u!r} {a}\n' for a, u in ru))
    K2 = run([B + 'bin/zfm2_cli.v11a', str(T0), '1.0', '4', '2.8', '1.6', '0.15', '16', TH, '12'], ''.join(f'z {u!r}\n' for u in zu))[1:]
    rs = run([B + 'bin/zfm_cli.v10b', str(T0), '1.0', '4', 'row', '2.8', '0.15', '16', TH, '12'], ''.join(f'{u!r}\n' for a, u in ru if a == '2.8'))[1:]
    rows_ok = sum(ov(c['res']['P'], r['P']) and c['res']['ok'] == 1 for c, r in zip(C[:20], R))
    zsame = sum(c['res']['Z_mid'] == k['res']['Z_mid'] for c, k in zip(C[20:], K2))
    rad12 = [c['res']['rad'] for (a, u), c in zip(ru, C[:20]) if a == '2.8']; rad10 = [r['P_rad'] for r in rs]
    out[str(T0)] = dict(rows_overlap_v9=rows_ok, n=20, z_identical_to_v11=zsame, zn=20, max_rad_ratio_vs_v10b=max(x / y for x, y in zip(rad12, rad10)),
                        build=sess['sec_build'], max_row_sec=max(c['res']['sec'] for c in C[:20]))
    print(T0, out[str(T0)], flush=True)
# stored Arb jets (M2): rows at <= 1e15 with u in [0, 2): sessions centred at 1
refs = {}
for f in ['runs/m2/row_arb_le14.jsonl', 'runs/m2/row_arb_15b.jsonl']:
    for d in map(json.loads, open(B + f)): refs.setdefault(d['T0'], []).append(d)
tot = cont = 0
for T0, L in sorted(refs.items(), key=lambda q: int(q[0])):
    C = run([B + 'bin/zfm4_cli.v12a', T0, '1.0', '4', '0.15', '18', TH, '12'], ''.join(f"r {d['a']} {d['u']}\n" for d in L))[1:]
    for c, d in zip(C, L):
        tot += 1; cont += all(inside(d[f], c['res'][f]) for f in ['zeta_re', 'zeta_im', 'dzeta_re', 'dzeta_im', 'P']) and c['res']['ok'] == 1
out['arb_jets'] = dict(points=tot, contained=cont); print(out['arb_jets'])
json.dump(out, open(B + 'runs/m5/V1b_v12.json', 'w'), indent=1)
