"""Compare zfast output with Arb reference output (THEORY_ZFAST 11.3).  Usage: compare.py zfast.jsonl ref1.jsonl [ref2.jsonl ...]
zfast ball: Z_mid (25 significant digits) +- Z_rad (%.6e).  Printing roundings are absorbed by widening the radius by a factor
(1 + 1e-5) plus 1e-24 |Z_mid|.  Reference: its printed Arb ball string 'Z' (Arb's printed balls are enclosures).
Checks per point: (a) the reference ball lies inside the zfast ball; (b) the balls intersect.  Prints per-height statistics and JSON."""
import sys, json, statistics
from flint import arb, ctx
ctx.prec = 200
def load(p): return {(d['T0'], d['u']): d for d in map(json.loads, open(p))}
Zf = load(sys.argv[1]); R = {}
for p in sys.argv[2:]: R.update(load(p))
rows = []; fails = []
for k, z in Zf.items():
    if k not in R: continue
    r = R[k]; zm = arb(z['Z_mid']); zr = arb(z['Z_rad']) * (1 + arb('1e-5')) + abs(zm) * arb('1e-24')
    zb = zm + arb(0, zr.upper()) if False else arb(zm.mid(), zr.upper())
    rb = arb(r['Z'])
    inside = bool((rb.mid() - rb.rad() >= zm.mid() - zr.upper()) and (rb.mid() + rb.rad() <= zm.mid() + zr.upper()))
    overlap = bool(abs(rb.mid() - zm.mid()) <= zr.upper() + rb.rad())
    diff = float(abs(rb.mid() - zm.mid()))
    rows.append(dict(T0=k[0], u=k[1], diff=diff, zrad=float(z['Z_rad']), inside=inside, overlap=overlap, Z=float(zm.mid()),
                     sec_zfast=z['sec_total'], sec_ref=r.get('sec'), rss_zfast=z['maxrss_mb'], rss_ref=r.get('maxrss_mb')))
    if not (inside and overlap): fails.append(rows[-1])
by = {}
for r in rows: by.setdefault(r['T0'], []).append(r)
summ = []
for T0 in sorted(by, key=int):
    L = by[T0]
    summ.append(dict(T0=T0, n=len(L), all_inside=all(x['inside'] for x in L), all_overlap=all(x['overlap'] for x in L),
                     max_diff=max(x['diff'] for x in L), max_rad=max(x['zrad'] for x in L),
                     median_rad_over_diff=statistics.median(x['zrad'] / max(x['diff'], 1e-40) for x in L),
                     min_rad_over_diff=min(x['zrad'] / max(x['diff'], 1e-40) for x in L),
                     med_sec_zfast=statistics.median(x['sec_zfast'] for x in L),
                     med_sec_ref=statistics.median(x['sec_ref'] for x in L if x['sec_ref'] is not None),
                     max_rss_zfast=max(x['rss_zfast'] for x in L), max_rss_ref=max(x['rss_ref'] or 0 for x in L)))
out = dict(points=len(rows), fails=fails, by_height=summ)
print(json.dumps(out, indent=1))
