"""High-height points (10^16 .. 10^19) and production zfast values (single point + M3 session, 1 thread).
10^17 / 10^18: the endpoints of the certified target sign-change intervals of the v5z windows (all 22 at 10^17; at 10^18 the 10
with smallest |Z|), plus random, N-jump, frac(a) = 1/2 and session-edge points.  -> data/points_high.json, data/zfast_high.jsonl"""
import sys, json, math, random, time
from flint import arb, ctx
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L

rng = random.Random(77)
pts = []
def addp(T0, u, cls): pts.append(dict(T0=int(T0), u=float(u), cls=cls))
D = L.Drv()
RUNS = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z/runs'
sel = {}
for e, f in [(17, 'w100000000000000000/z_1e17'), (18, 'w1000000000000000000/z_1e18')]:
    d = json.load(open(f'{RUNS}/{f}/intervals_summary.json'))
    T0 = d['T0']; assert T0 == 10 ** e
    ends = [x for iv in d['intervals'] for x in iv]
    if e == 18:
        sid = D.sess(T0, 0.0)
        mags = sorted((abs(float(L.ball(D.SZ(sid, x)['Z']).mid())), x) for x in ends)
        ends = [x for _, x in mags[:10]]
    for x in ends: addp(T0, x, 'cert_endpoint')
for e in [16, 17, 18, 19]:
    T0 = 10 ** e
    nr = 4 if e == 16 else 2
    for _ in range(nr): addp(T0, rng.uniform(-2.5, 4.5), 'rand')
    if e <= 18:
        addp(T0, 3.0, 'edge')
    ctx.prec = 400
    pi2 = 2 * arb.pi()
    M = int(math.isqrt(T0 * 1000000 // 6283185)) + 1
    tj = pi2 * M * M; T0j = int(tj.floor().unique_fmpz()) - 1
    addp(T0j, L.exact_u(T0j, tj), 'jump')
    if e <= 18:
        tf = pi2 * (arb(M) + arb('0.5')) ** 2; T0f = int(tf.floor().unique_fmpz()) - 1
        addp(T0f, L.exact_u(T0f, tf), 'pspec_0.5')
json.dump(pts, L.xopen(f'{L.R}/data/points_high.json'), indent=0)
out = L.xopen(f'{L.R}/data/zfast_high.jsonl')
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
print('done high', len(pts))
