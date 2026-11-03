"""V1: v11 combined session vs v10b sessions (Z, rows) and single-point v9.  1 thread (an Arb reference job runs in parallel)."""
import json, subprocess, random, sys
from flint import arb, ctx
ctx.prec = 200
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'; TH = '1'
def run(cmd, inp):
    r = subprocess.run(['nice', '-n', '19'] + cmd, input=inp, capture_output=True, text=True, check=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
def ov(a, b):
    a, b = arb(a), arb(b); return bool(abs(a.mid() - b.mid()) <= a.rad() + b.rad()), float(abs(a.mid() - b.mid()))
random.seed(515)
out = {}
for T0 in [10**10, 10**13, 10**16]:
    zu = [random.uniform(-3, 5) for _ in range(60)]; ru = [(random.choice([0, 1]), random.uniform(-3, 5)) for _ in range(20)]
    cmds = ''.join(f'z {u!r}\n' for u in zu) + ''.join(f'r {w} {u!r}\n' for w, u in ru)
    C = run([B + 'bin/zfm2_cli.v11a', str(T0), '1.0', '4', '2.8', '1.6', '0.15', '16', TH, '12'], cmds)
    sess = C[0]['session']; C = C[1:]
    S = run([B + 'bin/zfast_cli2.v9', '--threads', TH], ''.join(f'{T0} {u!r}\n' for u in zu))
    R = run([B + 'bin/zfast_row_cli2.v9', '--threads', TH], ''.join(f'{T0} {u!r} {[2.8, 1.6][w]}\n' for w, u in ru))
    zo = [ov(c['res']['Z'], s['Z']) for c, s in zip(C[:60], S)]
    ro = [ov(c['res']['P'], r['P']) for c, r in zip(C[60:], R)]
    zsess = run([B + 'bin/zfm_cli.v10b', str(T0), '1.0', '4', 'z', '0', '0.15', '16', TH, '12'], '0.5\n')[0]
    out[str(T0)] = dict(z_overlap=sum(o for o, _ in zo), z_n=len(zo), z_maxdiff=max(d for _, d in zo), row_overlap=sum(o for o, _ in ro), row_n=len(ro),
                        row_maxdiff=max(d for _, d in ro), combined_build=sess['sec_build'], z_only_build=zsess['sec_build'], ratio=sess['sec_build'] / zsess['sec_build'])
    print(T0, out[str(T0)], flush=True)
json.dump(out, open(B + 'runs/m5/V1_v11.json', 'w'), indent=1)
