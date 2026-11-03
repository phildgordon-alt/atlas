"""empirical check of the production zf_cos2pi (v12a dylib) vs Arb at 128 bits: random v and boundary patterns"""
import sys, random, json, time
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review2')
import zfl
from flint import arb, ctx
ctx.prec = 128
L = zfl.prod(sys.argv[1]); n = int(sys.argv[2])
rng = random.Random(20261019)
vs = []
for q in range(4):
    for d in [0, 1, -1, 2, -2, 1 << 61, -(1 << 61), (1 << 61) - 1, -((1 << 61) - 1), (1 << 60), 12345, -(1 << 40)]:
        vs.append((q * (1 << 62) + d) % (1 << 64))
vs += [rng.getrandbits(64) for _ in range(n)]
# near quadrant edges, where |y| is maximal (pi/4)
vs += [((rng.randrange(4) << 62) + (1 << 61) + rng.randrange(-1 << 20, 1 << 20)) % (1 << 64) for _ in range(n // 4)]
t = time.time(); mc = ms = 0; vc = vsn = None
twopi = 2 * arb.pi()
for v in vs:
    c, s = L.cos2pi(v)
    x = arb(v) / arb(2) ** 63          # 2 pi v / 2^64 = pi * v/2^63
    cr, sr = x.cos_pi(), x.sin_pi()
    ec = float(abs(cr - c).upper()); es = float(abs(sr - s).upper())
    if ec > mc: mc, vc = ec, v
    if es > ms: ms, vsn = es, v
r = dict(lib=sys.argv[1], n=len(vs), max_cos_err=mc, v_cos=str(vc), max_sin_err=ms, v_sin=str(vsn), E_c=4.88e-16, ok=max(mc, ms) <= 4.88e-16, sec=time.time() - t)
print(json.dumps(r))
