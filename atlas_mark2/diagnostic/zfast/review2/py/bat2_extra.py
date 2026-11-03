"""bat2_extra.py: extra Taylor-stressed points (sessions with small K / large Delta at 1e6..1e12, Z and rows) + stock-Arb refs."""
import json, random, subprocess, os
R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review2'
WD = '/Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh'
rng = random.Random(77)
X = dict(SZx=[], ROWx=[])
for T0 in (10 ** 6, 10 ** 8, 10 ** 10, 10 ** 12):
    for K, D in ((3, 0.6), (5, 0.5)):
        X['SZx'].append(dict(T0=T0, u0=1.0, H=4.0, Delta=D, K=K, us=[rng.uniform(-3, 5) for _ in range(4)]))
    for K, D in ((3, 0.6), (6, 0.4)):
        X['ROWx'].append(dict(T0=T0, u0=1.0, H=4.0, Delta=D, K=K, us=[rng.uniform(-3, 5) for _ in range(3)]))
json.dump(X, open(f'{R}/data/bat2_points_extra.json', 'x'), indent=0)
inp = f'{R}/data/bat2_ref_extra.in'
with open(inp, 'x') as f:
    for s in X['SZx']:
        for u in s['us']: f.write(f"AZ {s['T0']} {u.hex()} 160\n")
    for s in X['ROWx']:
        for u in s['us']:
            for a in (2.8, 1.6): f.write(f"AR {s['T0']} {u.hex()} {a} 160\n")
env = dict(os.environ, FP_MB='800', RSS_KB='800000', TL='7200')
r = subprocess.run([WD, f'{R}/bin/ref', inp, f'{R}/data/bat2_ref_extra.jsonl'], env=env, capture_output=True, text=True)
print(r.stdout)
