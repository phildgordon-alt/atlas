"""Rows (THEORY_ZFAST 10/11): Arb's balls (zeta, zeta', P = Re(-zeta'/zeta)) must lie inside zfast's.  zfast prints Arb-style ball
strings (arb_get_str: valid enclosures), so containment is checked ball-in-ball directly."""
import sys, json, statistics
from flint import arb
Z = {(d['T0'], d['u'], d['a']): d for d in map(json.loads, open(sys.argv[1]))}
R = {}
for p in sys.argv[2:]: R.update({(d['T0'], d['u'], d['a']): d for d in map(json.loads, open(p))})
def inside(r, z): return bool(r.mid() - r.rad() >= z.mid() - z.rad() and r.mid() + r.rad() <= z.mid() + z.rad())
rows = []
for k, z in Z.items():
    if k not in R: continue
    r = R[k]; ok = all(inside(arb(r[f]), arb(z[f])) for f in ['zeta_re', 'zeta_im', 'dzeta_re', 'dzeta_im', 'P'])
    P = arb(z['P']); Pr = arb(r['P'])
    rows.append(dict(T0=k[0], a=k[2], ok=ok and z['ok'] == 1, P_rad=float(P.rad()), P_diff=float(abs(P.mid() - Pr.mid())),
                     sec_z=z['sec_total'], sec_r=r['sec'], rss_z=z['maxrss_mb'], rss_r=r['maxrss_mb']))
by = {}
for x in rows: by.setdefault(x['T0'], []).append(x)
out = dict(points=len(rows), all_ok=all(x['ok'] for x in rows), fails=[x for x in rows if not x['ok']],
           by_height=[dict(T0=T, n=len(L), ok=all(x['ok'] for x in L), max_P_rad=max(x['P_rad'] for x in L), max_P_diff=max(x['P_diff'] for x in L),
                           med_sec_zfast=statistics.median(x['sec_z'] for x in L), med_sec_arb=statistics.median(x['sec_r'] for x in L),
                           max_rss_zfast=max(x['rss_z'] for x in L), max_rss_arb=max(x['rss_r'] for x in L)) for T, L in sorted(by.items(), key=lambda q: int(q[0]))])
print(json.dumps(out, indent=1))
