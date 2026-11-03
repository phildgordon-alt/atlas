"""Generate adversarial + random test heights and evaluate production zfast (single point and M3 session) at each.
usage: run_points.py TAG EXP1,EXP2,...   ->  data/points_TAG.json, data/zfast_TAG.jsonl   (never overwrites)
Point classes per height T0 = 10^e:
  rand     6 random binary64 u in [-2.5, 4.5]
  edge     u = +3, -3 (|h| = H exactly in the provider's session c = 0)
  bigu     u = 1e6 + 0.123
  jump     t at the N jump 2 pi M^2 (nearest double, +-1e-9, +-2^-40)
  pspec    frac(a) = 1/4, 1/2, 3/4 (removable singularities of the RS correction F, ADR p = 1/2, 0, -1/2)
  zero     adjacent doubles straddling a zero of Z found by bisection on zfast itself (|Z| ~ 1e-15), and zero +- 1e-10"""
import sys, json, math, random, time
from flint import arb, ctx
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L

tag = sys.argv[1]; exps = [int(e) for e in sys.argv[2].split(',')]
rng = random.Random(1000 + sum(exps))
pts = []
D = L.Drv()


def addp(T0, u, cls):
    pts.append(dict(T0=int(T0), u=float(u), cls=cls))


def zsign(T0, u):
    z = L.ball(D.Z(T0, u)['Z'])
    return 1 if z > 0 else (-1 if z < 0 else 0)


for e in exps:
    T0 = 10 ** e
    for _ in range(6): addp(T0, rng.uniform(-2.5, 4.5), 'rand')
    addp(T0, 3.0, 'edge'); addp(T0, -3.0, 'edge'); addp(T0, 1e6 + 0.123, 'bigu')
    ctx.prec = 400
    pi2 = 2 * arb.pi()
    M = int(math.isqrt(T0 * 1000000 // 6283185)) + 1           # about sqrt(T0/2pi) + 1
    tj = pi2 * M * M
    T0j = int(tj.floor().unique_fmpz()) - 1
    uj = L.exact_u(T0j, tj)
    for d in [0.0, 1e-9, -1e-9, 2.0 ** -40, -(2.0 ** -40)]: addp(T0j, uj + d, 'jump')
    for f in ['0.25', '0.5', '0.75']:
        tf = pi2 * (arb(M) + arb(f)) ** 2
        T0f = int(tf.floor().unique_fmpz()) - 1
        addp(T0f, L.exact_u(T0f, tf), 'pspec_' + f)
    # zero: first sign change of Z on u in [0, 2], step 0.02, then bisection on binary64
    prev = zsign(T0, 0.0); ua = 0.0; found = None
    k = 1
    while k <= 100 and found is None:
        ub = 0.02 * k; s = zsign(T0, ub)
        if s != 0 and prev != 0 and s != prev: found = (ua, ub, prev)
        if s != 0: prev, ua = s, ub
        k += 1
    if found:
        a, b, sa = found
        for _ in range(80):
            m = (a + b) / 2
            if m == a or m == b: break
            s = zsign(T0, m)
            if s == 0: break               # undecided: zfast radius reached; stop (a, b) here
            if s == sa: a = m
            else: b = m
        addp(T0, a, 'zero'); addp(T0, b, 'zero'); addp(T0, a - 1e-10, 'zero'); addp(T0, b + 1e-10, 'zero')
        m = (a + b) / 2
        addp(T0, m, 'zero_mid')

json.dump(pts, L.xopen(f'{L.R}/data/points_{tag}.json'), indent=0)
out = L.xopen(f'{L.R}/data/zfast_{tag}.jsonl')
sess = {}
for p in pts:
    T0, u = p['T0'], p['u']
    t0 = time.time(); r1 = D.Z(T0, u); t1 = time.time()
    c = L.centre(u); key = (T0, c)
    if key not in sess: sess[key] = D.sess(T0, c)
    r2 = D.SZ(sess[key], u); t2 = time.time()
    out.write(json.dumps(dict(p, single=r1['Z'], single_rad=r1['rad'], N=r1['N'], sess=r2['Z'], sess_rad=r2['rad'], sess_c=c,
                              sec_single=t1 - t0, sec_sess=t2 - t1)) + '\n'); out.flush()
D.close()
print('done', tag, len(pts))
