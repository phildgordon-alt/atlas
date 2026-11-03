"""M3 validation driver (PREDICTIONS_M3 R1-R5).  Runs sequentially (one process at a time), threads <= 2."""
import json, random, subprocess, sys, os
from flint import arb, ctx
ctx.prec = 200
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
V = sys.argv[1]            # session build version, e.g. v10a
OUT = B + 'runs/m3/'
TH = '2'
def run(cmd, inp):
    r = subprocess.run(['nice', '-n', '19'] + cmd, input=inp, capture_output=True, text=True, check=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
def ball(d, f='Z'):
    m = arb(d[f + '_mid']); r = arb(d[f + '_rad']) * (1 + arb('1e-5')) + abs(m) * arb('1e-24')
    return m, r
def overlap(a, b):
    (m1, r1), (m2, r2) = a, b
    return bool(abs(m1 - m2).upper() <= (r1 + r2).upper()), float(abs(m1 - m2).mid())
res = {}
random.seed(20261020)
# R1 + R5: sessions vs single point
for T0 in [10**10, 10**13, 10**16]:
    us = [-2.0, 4.0, 1.0] + [random.uniform(-2, 4) for _ in range(97)]
    S = run([B + 'bin/zfm_cli.' + V, str(T0), '1.0', '3', 'z', '0', '0.2', '16', TH, '12'], '\n'.join(map(repr, us)) + '\n')
    P = run([B + 'bin/zfast_cli2.v9', '--threads', TH], ''.join(f'{T0} {u!r}\n' for u in us))
    json.dump(dict(session=S, single=P), open(OUT + f'R1_{T0}.json', 'w'))
    ok = 0; md = 0; rr = []
    for s, p in zip(S[1:], P):
        o, d = overlap(ball(s), ball(p)); ok += o; md = max(md, d); rr.append(s['Z_rad'] / p['Z_rad'])
    res[f'R1_{T0}'] = dict(n=len(us), overlap=ok, max_diff=md, max_rad_ratio=max(rr), session_build=S[0]['sec_build'],
                           med_point_sec=sorted(x['sec_total'] for x in S[1:])[len(us) // 2], single_med_sec=sorted(x['sec_total'] for x in P)[len(us) // 2])
    print(res[f'R1_{T0}'], flush=True)
# R2: against stored Arb balls (points with -2 <= u <= 4)
refs = {}
for f in ['runs/m2/val_arb_le15.jsonl', 'runs/m2/val_arbsmooth_1e16.jsonl']:
    for d in map(json.loads, open(B + f)): refs.setdefault(d['T0'], []).append(d)
tot = 0; cont = 0
for T0, L in sorted(refs.items(), key=lambda q: int(q[0])):
    L = [d for d in L if -2 <= float(d['u']) <= 4]
    if not L: continue
    S = run([B + 'bin/zfm_cli.' + V, T0, '1.0', '3', 'z', '0', '0.2', '16', TH, '12'], ''.join(d['u'] + '\n' for d in L))
    for s, d in zip(S[1:], L):
        rb = arb(d['Z']); m, r = ball(s)
        tot += 1; cont += bool(rb.mid() - rb.rad() >= (m - r).mid() and rb.mid() + rb.rad() <= (m + r).mid())
res['R2'] = dict(points=tot, contained=cont); print(res['R2'], flush=True)
# R3: N-jump windows
for T in [10**12, 10**14]:
    import math
    M = math.isqrt(int(T / (2 * math.pi))) + 5
    tM = 2 * arb.pi() * arb(M) ** 2
    T0 = int(tM.floor().unique_fmpz()); u0 = float((tM - T0).mid())
    us = [u0 + d for d in [-2.9, -1.0, -1e-3, -1e-7, 1e-7, 1e-3, 1.0, 2.9]] + [u0 + random.uniform(-3, 3) for _ in range(12)]
    S = run([B + 'bin/zfm_cli.' + V, str(T0), repr(u0), '3', 'z', '0', '0.2', '16', TH, '12'], '\n'.join(map(repr, us)) + '\n')
    P = run([B + 'bin/zfast_cli2.v9', '--threads', TH], ''.join(f'{T0} {u!r}\n' for u in us))
    ok = sum(overlap(ball(s), ball(p))[0] for s, p in zip(S[1:], P)); Ns = sorted(set(s['N'] for s in S[1:]))
    res[f'R3_{T}'] = dict(n=len(us), overlap=ok, N_values=Ns, Nw=S[0]['Nw']); print(res[f'R3_{T}'], flush=True)
json.dump(res, open(OUT + f'validate_Z_{V}.json', 'w'), indent=1)
