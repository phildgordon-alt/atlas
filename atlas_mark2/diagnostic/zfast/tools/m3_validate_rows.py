"""M3 rows validation (R4): row sessions vs stored Arb jets (<= 1e15) and vs single-point zf_row (1e16)."""
import json, subprocess, sys, random
from flint import arb, ctx
ctx.prec = 200
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'; V = sys.argv[1]; TH = '2'
def run(cmd, inp):
    r = subprocess.run(['nice', '-n', '19'] + cmd, input=inp, capture_output=True, text=True, check=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
def inside(r, z): return bool(r.mid() - r.rad() >= z.mid() - z.rad() and r.mid() + r.rad() <= z.mid() + z.rad())
refs = {}
for f in ['runs/m2/row_arb_le14.jsonl', 'runs/m2/row_arb_15b.jsonl']:
    for d in map(json.loads, open(B + f)): refs.setdefault((d['T0'], d['a']), []).append(d)
res = dict(arb=[], single=[])
for (T0, a), L in sorted(refs.items(), key=lambda q: (int(q[0][0]), q[0][1])):
    S = run([B + 'bin/zfm_cli.' + V, T0, '1.0', '3', 'row', a, '0.2', '16', TH, '12'], ''.join(d['u'] + '\n' for d in L))
    for s, d in zip(S[1:], L):
        ok = all(inside(arb(d[f]), arb(s[f])) for f in ['zeta_re', 'zeta_im', 'dzeta_re', 'dzeta_im', 'P']) and s['ok'] == 1
        res['arb'].append(dict(T0=T0, a=a, u=d['u'], ok=ok, P_rad=s['P_rad'], P_diff=float(abs(arb(s['P_mid']) - arb(d['P']).mid())),
                               build=S[0]['sec_build'], point=s['sec_total']))
random.seed(5)
for a in ['2.8', '1.6']:
    us = [repr(random.uniform(-2, 4)) for _ in range(6)]
    T0 = str(10**16)
    S = run([B + 'bin/zfm_cli.' + V, T0, '1.0', '3', 'row', a, '0.2', '16', TH, '12'], ''.join(u + '\n' for u in us))
    P = run([B + 'bin/zfast_row_cli2.v9', '--threads', TH], ''.join(f'{T0} {u} {a}\n' for u in us))
    for s, p in zip(S[1:], P):
        Ps, Pp = arb(s['P']), arb(p['P'])
        ok = bool(abs(Ps.mid() - Pp.mid()) <= (Ps.rad() + Pp.rad())) and s['ok'] == 1
        res['single'].append(dict(T0=T0, a=a, u=s['u'], ok=ok, P_rad=s['P_rad'], P_rad_single=float(Pp.rad()),
                                  build=S[0]['sec_build'], point=s['sec_total'], single_sec=p['sec_total']))
summ = dict(arb_points=len(res['arb']), arb_ok=sum(x['ok'] for x in res['arb']), max_P_diff=max(x['P_diff'] for x in res['arb']),
            single_points=len(res['single']), single_ok=sum(x['ok'] for x in res['single']),
            builds={f"{x['T0']}|{x['a']}": x['build'] for x in res['arb'] + res['single']},
            max_point_sec=max(x['point'] for x in res['arb'] + res['single']))
json.dump(dict(summary=summ, detail=res), open(B + f'runs/m3/validate_rows_{V}.json', 'w'), indent=1)
print(json.dumps(summ, indent=1))
