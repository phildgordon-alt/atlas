"""review_v14c differential: v14 (reference, zfa14_new, W1) vs v14c no-ckpt (zfa14_new) vs v14c fresh ckpt vs v14c full resume
(complete ckpt, other W, verify ALL) vs v14c partial resume (ckpt truncated mid-line at ~45 %, other W, verify ALL).
Compares state SHA-256, Z-grid sha, rows sha, Z strings.  usage: diff_rv.py OUTDIR"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import *

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700, exist_ok=True)
cases = [('100000000000000', '50.0', '61.0', '0.012', (1, 2, 3, 5, 7), (1, 3, 8)),
         ('1000000000000000000', '7.25', '40.0', '0.02', (1, 2, 3, 5, 7), (1, 3)),
         ('1000000000000000000', '7.25', '40.0', '0.02', (2, 5), (8,)),
         ('100000000000000000000', '-3.5', '20.0', '0.03', (3, 7), (2,))]
refs = {}; res = []; bad = 0
for ci, (T0, U0, H, DL, Ds, Ws) in enumerate(cases):
    for D in Ds:
        if (T0, D) not in refs:
            t = time.time(); refs[(T0, D)] = probe(L14, 'v14', T0, U0, H, DL, D, 1); print('ref', T0, D, round(time.time() - t, 1), flush=True)
        ref = refs[(T0, D)]
        for W in Ws:
            tag = f'{ci}_{D}_{W}'
            a = probe(L14C, 'v14', T0, U0, H, DL, D, W)
            ckp = os.path.join(OUT, f'ck_{tag}.txt'); kf = os.path.join(KD, f'{tag}.key')
            b = probe(L14C, 'v14c', T0, U0, H, DL, D, W, ckp, key=kf)
            W2 = 2 if W != 2 else 1
            c = probe(L14C, 'v14c', T0, U0, H, DL, D, W2, ckp, key=kf, vn=1000000)
            data = open(ckp, 'rb').read(); cut = int(len(data) * 0.45)
            ckp2 = os.path.join(OUT, f'ckp_{tag}.txt'); open(ckp2, 'wb').write(data[:cut]); kf2 = os.path.join(KD, f'p{tag}.key'); copykey(kf, kf2)
            d = probe(L14C, 'v14c', T0, U0, H, DL, D, W2, ckp2, key=kf2, vn=1000000)
            e2 = probe(L14C, 'v14c', T0, U0, H, DL, D, W, ckp2, key=kf2, vn=1000000)     # resume of a resume (complete now)
            allr = (ref, a, b, c, d, e2)
            same = len({kk(x) for x in allr}) == 1 and all(x['rc'] == 0 for x in allr)
            bad += not same
            row = dict(T0=T0, D=D, W=W, same=same, items=a['info']['items'], c_loaded=c['info'].get('items_loaded'), c_verified=c['info'].get('verified'),
                       d_loaded=d['info'].get('items_loaded'), d_rejected=d['info'].get('lines_rejected'), d_verified=d['info'].get('verified'),
                       e_loaded=e2['info'].get('items_loaded'), e_rejected=e2['info'].get('lines_rejected'),
                       sec_fast=[x['info']['sec_fast'] for x in allr], max_unsynced=b['info'].get('max_unsynced_s'), syncs=b['info'].get('ckpt_syncs'),
                       hashes=[(x.get('state_sha256') or '')[:12] for x in allr], rcs=[x['rc'] for x in allr])
            res.append(row); print(json.dumps(row), flush=True)
json.dump(res, open(os.path.join(OUT, 'diff_results.json'), 'w'), indent=1)
print(json.dumps(dict(cases=len(res), mismatches=bad)))
