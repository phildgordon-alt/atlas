"""high_cmp.py OUT REF.jsonl...: production v12a (rd3.v12a, H4 D0.15 K18) and v10b (rd3.v10b, H3 D0.2 K16) session values at every
reference point (GZ = Arb powsum_smooth + Gabcke C0,C1 with R1 bound; AZ = stock Arb; AR = stock Arb jet), contained or not."""
import json, subprocess, sys, time
from flint import arb, ctx
ctx.prec = 300
R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review2'
out = open(sys.argv[1], 'x')
Z, P = {}, {}
for f in sys.argv[2:]:
    for l in open(f):
        d = json.loads(l)
        k = (int(d['T0']), float.fromhex(d['u']))
        if d['cmd'] in ('GZ', 'AZ'): Z.setdefault(k, []).append(d)
        elif d['cmd'] == 'AR': P.setdefault(k + (d['a'],), []).append(d)

def drv(b, line):
    r = subprocess.run(['nice', '-n', '19', f'{R}/bin/rd3.{b}'], input=line + '\n', capture_output=True, text=True)
    return json.loads(r.stdout.splitlines()[0])

def centre(b, u):
    if b == 'v12a': return 1.0 if abs(u - 1.0) <= 4 else 8.0 * round(u / 8.0)
    return 6.0 * round(u / 6.0)

groups = {}
for (T0, u) in Z: groups.setdefault(('Z', T0), []).append(u)
for (T0, u, a) in P: groups.setdefault(('P', T0, a), []).append(u)
for key, us in sorted(groups.items(), key=lambda x: str(x[0])):
    for b in ('v12a', 'v10b'):
        bycent = {}
        for u in us: bycent.setdefault(centre(b, u), []).append(u)
        for c, uu in bycent.items():
            H, D, K = (4, 0.15, 18) if b == 'v12a' else (3, 0.2, 16)
            t = time.time()
            if key[0] == 'Z':
                d = drv(b, f"SZ {key[1]} {c!r} {H} {D} {K} 12 {len(uu)} " + ' '.join(x.hex() for x in uu))
            else:
                cmd = 'S3' if b == 'v12a' else 'S1'
                d = drv(b, f"{cmd} {key[1]} {c!r} {H} {D} {K} 12 {key[2]} {len(uu)} " + ' '.join(x.hex() for x in uu))
            for p in d['pts']:
                u = float.fromhex(p['u'])
                refs = Z[(key[1], u)] if key[0] == 'Z' else P[(key[1], u, key[2])]
                for ref in refs:
                    zs = p['Z'] if key[0] == 'Z' else p['P']; rs = ref['Z'] if key[0] == 'Z' else ref['P']
                    z, r = arb(zs), arb(rs)
                    rec = dict(lib=b, kind=key[0], T0=str(key[1]), u=u.hex(), a=key[2] if key[0] == 'P' else None, ref_cmd=ref['cmd'],
                               contained=bool(z.contains(arb(r.mid())) and z.overlaps(r)), ref_inside=bool(z.contains(r)),
                               diff=float(abs(z.mid() - r.mid())), rad=float(z.rad()), ref_rad=float(r.rad()), z=zs, ref=rs,
                               sess_sec=d['sec_build'])
                    out.write(json.dumps(rec) + '\n'); out.flush()
print('done')
