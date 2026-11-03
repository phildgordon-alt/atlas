"""Rows at 10^17 / 10^18: production zfast (session + single point) vs stock Arb jets (acb_dirichlet_zeta_jet, which at these
heights and precisions uses Arb's own low-memory powsum_smooth main sums and Arb's own RS correction).  -> data/rows_high_*.jsonl"""
import sys, json, os, subprocess
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L
pts = [(10 ** 17, 0.5546875, 2.8), (10 ** 17, 1.3125, 1.6), (10 ** 18, 0.40625, 2.8)]
out = L.xopen(f'{L.R}/data/rows_high_zfast.jsonl')
D = L.Drv()
for T0, u, a in pts:
    sid = D.sess(T0, L.centre(u), kind=1, a=a)
    r1 = D.SR(sid, u); r2 = D.ROW(T0, u, a)
    out.write(json.dumps(dict(T0=T0, u=u, a=a, sess=r1, single=r2)) + '\n'); out.flush()
D.close(); out.close()
inp = f'{L.R}/data/rows_high_ref.in'
with L.xopen(inp) as f:
    for T0, u, a in pts: f.write(f'AR {T0} {u.hex()} {a} 192\n')
r = subprocess.run([L.WD, L.REF, inp, f'{L.R}/data/rows_high_ref.jsonl'], env=dict(os.environ, FP_MB='800', RSS_KB='800000', TL='7200'),
                   capture_output=True, text=True)
print(r.stdout, r.stderr[-300:])
