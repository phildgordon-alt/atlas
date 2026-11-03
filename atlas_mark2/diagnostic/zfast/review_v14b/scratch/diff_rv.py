"""reviewer differential: v14 vs v14b (no ckpt, zfa14_new) vs v14b (zfa14b_new with fresh ckpt) vs v14b resumed (complete ckpt).
Compares state hash, Z grid sha, rows sha, Z strings.  usage: diff_rv.py OUTDIR"""
import json, os, subprocess, sys, itertools
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
PROBE = ZF + 'tools/m12_probe.py'
L14, L14B = ZF + 'bin/libzfast.v14.dylib', ZF + 'bin/libzfast.v14b.dylib'
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700, exist_ok=True)


def probe(lib, mode, T0, U0, H, DL, D, W, ck='-', role='gen', nonce='c' * 32, key='-', vn=8):
    e = {k: v for k, v in os.environ.items() if not k.startswith('ZFAST')}
    cmd = ['nice', '-n', '19', PY, '-B', PROBE, lib, mode, T0, U0, H, DL, '18', '12', str(D), str(W), ck, str(float(U0) - 3), '0.004', '200', role, nonce, key, str(vn)]
    p = subprocess.run(cmd, capture_output=True, text=True, env=e, timeout=1200)
    r = json.loads(p.stdout.strip().splitlines()[-1]); r['rc'] = p.returncode; r['stderr'] = p.stderr[-400:]
    return r


def k(r): return (r.get('state_sha256'), (r.get('grid') or {}).get('sha256'), r.get('rows_sha256'), tuple(r.get('Z') or ()))


cases = [('100000000000000', '50.0', '61.0', '0.012'), ('1000000000000000000', '7.25', '40.0', '0.02'), ('100000000000000000000', '-3.5', '20.0', '0.03')]
res = []; bad = 0
for ci, (T0, U0, H, DL) in enumerate(cases):
    for D in (1, 2, 3, 5):
        ref = probe(L14, 'v14', T0, U0, H, DL, D, 1)
        if ci == 2 and D not in (3, 5): continue
        for W in ((1, 4) if ci == 2 else (1, 2, 3, 4)):
            a = probe(L14B, 'v14', T0, U0, H, DL, D, W)
            ckp = os.path.join(OUT, f'ck_{ci}_{D}_{W}.txt'); kf = os.path.join(KD, f'{ci}_{D}_{W}.key')
            for f in (ckp, kf):
                if os.path.exists(f): os.remove(f)
            b = probe(L14B, 'v14b', T0, U0, H, DL, D, W, ckp, key=kf)
            c = probe(L14B, 'v14b', T0, U0, H, DL, D, 4 if W != 4 else 1, ckp, key=kf, vn=1000000)    # resume from complete ckpt, verify ALL items
            same = k(ref) == k(a) == k(b) == k(c) and all(x['rc'] == 0 for x in (ref, a, b, c))
            bad += not same
            row = dict(T0=T0, D=D, W=W, same=same, items=a['info']['items'], loaded=c['info'].get('items_loaded'), verified=c['info'].get('verified'),
                       sec_fast=a['info']['sec_fast'], hashes=[x.get('state_sha256', '')[:12] for x in (ref, a, b, c)])
            res.append(row); print(json.dumps(row), flush=True)
print(json.dumps(dict(cases=len(res), mismatches=bad)))
