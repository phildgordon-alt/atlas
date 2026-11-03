"""bat2_prep.py: build the fixed adversarial point list for the review2 battery (data/bat2_points.json, never overwritten).
Point search uses the production driver bin/rd3.v12a (only to LOCATE adversarial points: N jumps, p = +-1/2, near-zeros);
correctness is judged later against stock Arb (bin/ref)."""
import json, math, random, subprocess, sys, os
from fractions import Fraction
from flint import arb, ctx
R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review2'
DRV = f'{R}/bin/rd3.v12a'
ctx.prec = 300
rng = random.Random(20261019)

def run(lines):
    r = subprocess.run(['nice', '-n', '19', DRV], input='\n'.join(lines) + '\n', capture_output=True, text=True, check=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]

def sess_Z(T0, us, u0=1.0):
    d = run([f"SZ {T0} {u0!r} 4 0.15 18 12 {len(us)} " + ' '.join(u.hex() for u in us)])[0]
    return [(float.fromhex(p['u']), arb(p['Z'])) for p in d['pts']]

def T0_for(E, frac):
    """T0 integer with a = sqrt(t/2pi) = M + frac at t = T0 + u*, u* in [1, 2): returns (T0, u*)"""
    M = math.isqrt(int(10 ** E / (2 * math.pi)))
    t = 2 * arb.pi() * (arb(M) + frac) ** 2
    T0 = int(t.floor().mid()) - 1
    us = t - T0
    return T0, float(us.mid())

def zeros(T0, lo=-3.0, hi=5.0, n=161, want=2):
    us = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    v = sess_Z(T0, us)
    out = []
    for (a, za), (b, zb) in zip(v, v[1:]):
        if (za > 0 and zb < 0) or (za < 0 and zb > 0):
            sa = 1 if za > 0 else -1
            for it in range(10):                      # 64-point sub-grids: ~2^-60 relative resolution
                g = [a + (b - a) * i / 64 for i in range(1, 64)]
                w = sess_Z(T0, g)
                na, nb = a, b
                for (x, z) in w:
                    if not (z > 0 or z < 0): na = nb = x; break   # undecided (|Z| below radius): take it
                    if (1 if z > 0 else -1) == sa: na = x
                    else: nb = x; break
                a, b = na, nb
                if a == b or b - a <= abs(a) * 2e-16: break
            out.append(a)
            if len(out) >= want: break
    return out

pts = dict(Zsess=[], Zsingle=[], Zstress_sess=[], rows=[], rows_stress=[])
for E in range(10, 16):
    T0 = 10 ** E
    us = [rng.uniform(-3, 5) for _ in range(6)] + [-3.0, 5.0, 1.0]
    zs = zeros(T0)
    us += zs + [z + 1e-12 for z in zs]
    pts['Zsess'].append(dict(T0=T0, u0=1.0, cls='plain', us=us))
    Tj, uj = T0_for(E, 0)                       # N jump at u = uj
    pts['Zsess'].append(dict(T0=Tj, u0=1.0, cls='Njump', ujump=uj,
                             us=[uj + d for d in (-1e-6, -1e-9, -1e-12, 0.0, 1e-12, 1e-9, 1e-6)] + [-3.0, rng.uniform(-3, uj), rng.uniform(uj, 5)]))
    for fr, nm in ((Fraction(1, 4), 'p=+1/2'), (Fraction(3, 4), 'p=-1/2')):
        Tp, up = T0_for(E, arb(fr.numerator) / fr.denominator)
        pts['Zsess'].append(dict(T0=Tp, u0=1.0, cls=nm, us=[up + d for d in (-1e-9, 0.0, 1e-9)] + [rng.uniform(-3, 5)]))
    pts['Zsingle'].append(dict(T0=T0, u=rng.uniform(0, 2), cfg='prod'))
for T0 in (10 ** 10, 10 ** 12):
    for cfg in ('J6', 'J24', 'J8b64'):
        pts['Zsingle'].append(dict(T0=T0, u=rng.uniform(0, 2), cfg=cfg))
for T0 in (1500, 3000, 20000, 100000):
    pts['Zsingle'].append(dict(T0=T0, u=rng.uniform(0, 2), cfg='kcorr2'))
    for K, D in ((2, 0.6), (3, 0.6), (5, 0.4)):
        pts['Zstress_sess'].append(dict(T0=T0, u0=1.0, H=4.0, Delta=D, K=K, us=[rng.uniform(-3, 5) for _ in range(4)] + [-3.0, 5.0]))
for E in (10, 11, 12, 13):
    pts['rows'].append(dict(T0=10 ** E, u0=1.0, us=[rng.uniform(-3, 5) for _ in range(3)] + [5.0]))
Tj, uj = T0_for(12, 0)
pts['rows'].append(dict(T0=Tj, u0=1.0, cls='Njump', us=[uj - 1e-9, uj + 1e-9, uj - 0.02, uj + 0.02]))
for T0 in (2000, 30000):
    for K, D in ((3, 0.6), (6, 0.4)):
        pts['rows_stress'].append(dict(T0=T0, u0=1.0, H=4.0, Delta=D, K=K, us=[rng.uniform(-3, 5) for _ in range(3)]))
json.dump(pts, open(f'{R}/data/bat2_points.json', 'x'), indent=0)
print({k: sum(len(x.get('us', [1])) for x in v) for k, v in pts.items()})
