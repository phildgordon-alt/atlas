"""M6 diagnostic (NOT rigorous; no zfast call): estimate |Z| at the certified sign-change endpoints of a finished window and compare
with the session radius, using the saved scan grid of the same height (step 0.004): the zero inside each interval is located by
linear interpolation of the grid midpoints in the bracketing cell, |Z(endpoint)| ~ |slope| * |endpoint - zero|, and the radius is
the larger grid radius of that cell (the production H = 4 session has a radius of about the same size or smaller).
usage: endpoint_margin_m6.py RUN SCANDIR OUTJSON   (OUTJSON must not exist)"""
import json, sys, os
import numpy as np
RUN, SCAN, OUT = sys.argv[1:4]; assert not os.path.exists(OUT)
zs = json.load(open(RUN + '/zs.json')); iv = zs.get('intervals_offsets') or zs['intervals']
g = np.load(SCAN + '/grid.npz'); u, m, r = g['u'], g['mid'], g['rad']
rows = []
for a, b in iv:
    c = (a + b) / 2; j = int(np.searchsorted(u, c) - 1)
    if j < 0 or j + 1 >= len(u): continue
    s = (m[j + 1] - m[j]) / (u[j + 1] - u[j])
    if s == 0: continue
    z0 = u[j] - m[j] / s
    rad = max(float(r[j]), float(r[j + 1]))
    za, zb = abs(s) * abs(a - z0), abs(s) * abs(b - z0)
    rows.append(dict(interval=[a, b], zero_est=float(z0), slope=float(s), Z_a_est=float(za), Z_b_est=float(zb), rad=rad, ratio=float(min(za, zb) / rad)))
rows.sort(key=lambda d: d['ratio'])
res = dict(run=RUN, scan=SCAN, intervals=len(iv), analysed=len(rows), min_ratio=rows[0]['ratio'] if rows else None,
           median_ratio=float(np.median([d['ratio'] for d in rows])) if rows else None, smallest3=rows[:3], note='linearized estimate; diagnostic only')
json.dump(res, open(OUT, 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'smallest3'}))
