"""Targeted stress for the M3 Taylor remainder (Lemma M1) and the per-moment bound (Lemma M2): tiny heights (few terms, so little
random cancellation), K = 2, wide buckets, points at |h| = H.  Runs prod and the given mutants; -> data/stress_m3_<builds>.json"""
import sys, json, os, subprocess
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L
builds = sys.argv[1:]
pts = []
for T0 in [2000, 5000, 20000, 100000]:
    for u in [-3.0, -2.9, -1.5, 1.5, 2.9, 3.0]: pts.append((T0, u))
inp = f'{L.R}/data/stress_m3_ref.in'; outp = f'{L.R}/data/stress_m3_ref.jsonl'
if not os.path.exists(outp):
    with L.xopen(inp) as f:
        for T0, u in pts: f.write(f'AZ {T0} {u.hex()} 160\n')
    subprocess.run([L.WD, L.REF, inp, outp], env=dict(os.environ, FP_MB='800', RSS_KB='800000', TL='600'), capture_output=True)
refs = {(int(d['T0']), float.fromhex(d['u'])): d['Z'] for d in map(json.loads, open(outp))}
res = {}
for b in builds:
    D = L.Drv(f'{L.R}/bin/rv_drv.{b}'); rows = []
    for (K, Dl) in [(2, 1.0), (2, 2.0), (3, 2.0), (2, 0.2)]:
        # (T0 = 1e5, Delta = 0.2) aborts in zfm_new with 'mom block too short' (finding: robustness, see REVIEW.md) -> skipped
        Ts = [T for T in [2000, 5000, 20000, 100000] if not (T == 100000 and Dl == 0.2)]
        sid = {T0: D.sess(T0, 0.0, K=K, Delta=Dl, H=3.0) for T0 in Ts}
        for T0, u in pts:
            if T0 not in sid: continue
            c = L.compare(D.SZ(sid[T0], u)['Z'], refs[(T0, u)])
            rows.append(dict(T0=T0, u=u, K=K, Delta=Dl, ok=c['overlap'], ratio=c['ratio'], diff=c['diff'], rad=c['rad_z']))
    D.close()
    res[b] = dict(fails=sum(not r['ok'] for r in rows), max_ratio=max(r['ratio'] for r in rows), worst=max(rows, key=lambda r: r['ratio']))
    print(b, res[b]['fails'], f"{res[b]['max_ratio']:.3g}", res[b]['worst'])
json.dump(res, L.xopen(f'{L.R}/data/stress_m3_{"_".join(builds)}.json'), indent=0)
