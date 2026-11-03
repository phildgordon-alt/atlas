"""Sign replay (THEORY_ZFAST 11.5): every certified sign-change interval [t1, t2] of the record windows must have zfast balls at
t1 and t2 that both exclude 0 and have opposite signs.  Also reports min |Z|/rad (decisiveness margin)."""
import json, sys
from flint import arb
Z = {(d['T0'], float(d['u'])): d for d in map(json.loads, open(sys.argv[2]))}
ivs = json.load(open(sys.argv[1])); out = {}
for name, w in ivs.items():
    T0 = str(w['T0']); n = ok = 0; worst = None; minabs = None
    for t1, t2 in w['intervals']:
        a, b = Z[(T0, t1)], Z[(T0, t2)]
        za, zb = float(a['Z_mid']), float(b['Z_mid']); ra, rb = a['Z_rad'], b['Z_rad']
        dec = abs(za) > ra and abs(zb) > rb; opp = (za > 0) != (zb > 0)
        n += 1; ok += dec and opp
        m = min(abs(za) / ra, abs(zb) / rb)
        if worst is None or m < worst: worst = m
        mz = min(abs(za), abs(zb)); minabs = mz if minabs is None else min(minabs, mz)
    out[name] = dict(intervals=n, decided_and_opposite=ok, min_absZ=minabs, min_absZ_over_rad=worst)
print(json.dumps(out, indent=1))
