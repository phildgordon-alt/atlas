"""M6: code-independent Arb reference points at 10^24 (review2's GZ: acb_dirichlet_powsum_smooth main sum + Gabcke C0, C1 with the
R1 bound; shares no code with zfast).
  select SCANDIR OUT_IN OUT_JSON : from the saved scan grid (libzfast.v13b session values), choose 3 grid points by a fixed rule:
     (1) the decided grid point with the smallest |mid|/rad (the hardest sign);  (2) the grid point with the largest |mid|;
     (3) the grid point nearest the midpoint of the scan's closest pair.  Writes 'GZ T0 u_hex 192 -1' lines (review2 format) and a
     JSON with the zfast balls [mid - rad, mid + rad] (rad includes the double rounding of the midpoint, zfa3_Zgrid).
  compare REF_JSONL OUT_JSON : containment of each reference midpoint in the zfast ball and overlap of the balls; prints a summary."""
import json, sys, os
import numpy as np
mode = sys.argv[1]
if mode == 'select':
    SCAN, OUT_IN, OUT_JSON = sys.argv[2:5]; assert not os.path.exists(OUT_IN) and not os.path.exists(OUT_JSON)
    st = json.load(open(SCAN + '/scan_turing.json')); T0 = int(st['T0'])
    g = np.load(SCAN + '/grid.npz'); u, m, r = g['u'], g['mid'], g['rad']
    dec = np.abs(m) > r
    ratio = np.where(dec, np.abs(m) / np.maximum(r, 1e-300), np.inf)
    k1 = int(np.argmin(ratio)); k2 = int(np.argmax(np.abs(m)))
    cp = st['closest_pair']; pm = (sum(cp['z1']) / 2 + sum(cp['z2']) / 2) / 2; k3 = int(np.argmin(np.abs(u - pm)))
    pts = [dict(role='smallest |mid|/rad (decided)', k=k1), dict(role='largest |mid|', k=k2), dict(role='nearest closest-pair midpoint', k=k3)]
    for p in pts:
        k = p['k']; p.update(u=float(u[k]), u_hex=float(u[k]).hex(), mid=float(m[k]), rad=float(r[k]), decided=bool(dec[k]))
    with open(OUT_IN, 'w') as f:
        for p in pts: f.write(f"GZ {T0} {p['u_hex']} 192 -1\n")
    json.dump(dict(T0=str(T0), scan=SCAN, lib=st.get('lib'), points=pts), open(OUT_JSON, 'w'), indent=1)
    print(json.dumps(pts))
elif mode == 'compare':
    from flint import arb, ctx; ctx.prec = 256
    REF, PJ = sys.argv[2:4]; P = json.load(open(PJ))
    refs = [json.loads(l) for l in open(REF) if l.strip().startswith('{')]
    out = []
    for p in P['points']:
        rr = [d for d in refs if float.fromhex(d['u']) == p['u'] and d['T0'] == P['T0']]
        if not rr: out.append(dict(u=p['u'], status='no reference yet')); continue
        d = rr[0]; zb = arb(d['Z']); zmid = float(zb.mid().str(30, radius=False)); zrad = float(zb.rad().str(10, radius=False))
        diff = abs(zmid - p['mid'])
        out.append(dict(u=p['u'], role=p['role'], zfast_mid=p['mid'], zfast_rad=p['rad'], ref_mid=zmid, ref_rad=zrad, ref_sec=d.get('sec'), ref_maxrss_mb=d.get('maxrss_mb'),
                        diff=diff, ref_mid_inside_zfast_ball=diff <= p['rad'], balls_overlap=diff <= p['rad'] + zrad, diff_over_rad=diff / p['rad']))
    print(json.dumps(out, indent=1))
    json.dump(out, open(PJ.replace('.json', '_compare.json'), 'w'), indent=1)
