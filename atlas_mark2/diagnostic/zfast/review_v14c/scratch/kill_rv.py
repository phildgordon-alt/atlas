"""review_v14c: real SIGKILL at random times (fresh session, resumes, verify phase), then a final resume; compare with v14 (no ckpt).
Production libzfast.v14c, W <= 2.  usage: kill_rv.py OUTDIR"""
import json, os, random, signal, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import *

OUT = sys.argv[1]; os.makedirs(OUT); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700)
def cmd(T0, U0, H, DL, D, W, ck, kf, vn):
    return ['nice', '-n', '19', PY, '-B', PROBE, L14C, 'v14c', T0, U0, H, DL, '18', '12', str(D), str(W), ck, str(float(U0) - 3), '0.004', '200', 'gen', 'd' * 32, kf, str(vn)]
cases = [('1000000000000000000', '7.25', '40.0', '0.02', 2, 6, (1.0, 7.0)), ('100000000000000000000', '-3.5', '20.0', '0.03', 3, 3, (2.0, 40.0))]
res = []; bad = 0
for ci, (T0, U0, H, DL, D, ntr, (tmin, tmax)) in enumerate(cases):
    ref = probe(L14, 'v14', T0, U0, H, DL, D, 1)
    for tr in range(ntr):
        rng = random.Random(1000 * ci + tr); ck = os.path.join(OUT, f'k{ci}_{tr}.txt'); kf = os.path.join(KD, f'k{ci}_{tr}.key')
        kills = []
        for j in range(rng.choice((2, 3, 4))):
            e = {k: v for k, v in os.environ.items() if not k.startswith('ZFAST')}
            p = subprocess.Popen(cmd(T0, U0, H, DL, D, rng.choice((1, 2)), ck, kf, 64), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
            dt = rng.uniform(0.3, 2.5) if (j > 0 and rng.random() < 0.4) else rng.uniform(tmin, tmax)     # sometimes during load / verify
            time.sleep(dt); p.send_signal(signal.SIGKILL); out, err = p.communicate()
            nlines = sum(1 for _ in open(ck, 'rb')) if os.path.exists(ck) else 0
            kills.append(dict(at=round(dt, 2), rc=p.returncode, lines=nlines, err=err.decode()[-160:] if p.returncode not in (-9,) else ''))
        fin = probe(L14C, 'v14c', T0, U0, H, DL, D, rng.choice((1, 2)), ck, key=kf, nonce='d' * 32, vn=64)
        fin2 = probe(L14C, 'v14c', T0, U0, H, DL, D, 2, ck, key=kf, nonce='d' * 32, vn=1000000)       # complete, verify all
        same = fin['rc'] == 0 and fin2['rc'] == 0 and kk(fin) == kk(ref) == kk(fin2)
        bad += not same
        row = dict(T0=T0, D=D, trial=tr, same=same, kills=kills, loaded=(fin.get('info') or {}).get('items_loaded'), rejected=(fin.get('info') or {}).get('lines_rejected'),
                   verified=(fin.get('info') or {}).get('verified'), items=(fin.get('info') or {}).get('items'), fin2_loaded=(fin2.get('info') or {}).get('items_loaded'),
                   fin2_rejected=(fin2.get('info') or {}).get('lines_rejected'), reason=fin.get('reason') or fin2.get('reason'))
        res.append(row); print(json.dumps(row), flush=True)
json.dump(res, open(os.path.join(OUT, 'kill_results.json'), 'w'), indent=1)
print(json.dumps(dict(trials=len(res), mismatches=bad)))
