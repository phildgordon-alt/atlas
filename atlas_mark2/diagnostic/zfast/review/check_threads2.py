"""Production configuration of the provider (sessions with 2 threads, as ZFAST_THREADS default) on the low point set vs stock Arb."""
import sys, json
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L
pts = [json.loads(l) for l in open(f'{L.R}/data/zfast_low.jsonl')]
refs = {(int(d['T0']), float.fromhex(d['u'])): d['Z'] for d in map(json.loads, open(f'{L.R}/data/ref_low_AZ.jsonl'))}
D = L.Drv(); sess = {}; n = ok = 0; mr = 0.0
out = L.xopen(f'{L.R}/data/threads2_low.jsonl')
for p in pts:
    c = L.centre(p['u']); k = (p['T0'], c)
    if k not in sess: sess[k] = D.sess(p['T0'], c, th=2)
    r = D.SZ(sess[k], p['u']); cmp = L.compare(r['Z'], refs[(p['T0'], p['u'])])
    n += 1; ok += cmp['overlap'] and cmp['contained']; mr = max(mr, cmp['ratio'])
    out.write(json.dumps(dict(p, sess2=r['Z'], cmp=cmp)) + '\n')
D.close(); print('threads=2 sessions:', ok, '/', n, 'contained; max diff/rad', mr)
