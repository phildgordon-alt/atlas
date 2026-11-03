"""Containment test battery used for production zfast AND every mutant (mutation testing).
  battery.py prep          -> data/bat_points.json, data/bat_ref_AZ.jsonl, data/bat_ref_AR.jsonl  (stock Arb, watchdog 800 MB)
  battery.py run BUILD     -> data/bat_BUILD.json  (BUILD = prod or a mutant name; bin/rv_drv.BUILD)
Families (each reports pass/fail; a mutant is 'detected' if any family fails):
  K   kernel: cos/sin of 2 pi v/2^64 vs Arb for ~60k adversarial+random v; fail if max error > the build's ZF_EC
  P   phase:  zf_phase_test at stress and production (J, B); fail if observed > bound
  Zp  single-point Z, production params, 36 points 1e10..1e15 (rand/jump/pspec/zero) vs stock Arb hardy_z
  Zs  single-point Z, stress params: small t with kcorr = 2 (Arb uses Euler-Maclaurin there: independent of RS), J = 6 with
      log2_interp = -20 and bmax 2^16 (interpolation-dominated radius), J = 24 / bmax 2^16 (256-bit rounding-propagation dominated)
  Sp  M3 session Z, production params (H 3, Delta 0.2, K 16), same points as Zp
  Ss  M3 session Z, stress params: K = 3 and K = 5 with Delta = 0.6 (Taylor-remainder dominated)
  Rp  rows: session and single-point P = Re(-zeta'/zeta), a = 2.8 and 1.6, at 1e10..1e12 vs stock Arb jets"""
import sys, json, os, random, subprocess, math, re
from flint import arb, ctx
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L

R = L.R


def prep():
    low = [json.loads(l) for l in open(f'{R}/data/zfast_low.jsonl')]
    rng = random.Random(5)
    zp = []
    for e in range(10, 16):
        cand = [p for p in low if len(str(p['T0'])) == e + 1 or (p['cls'] in ('jump',) and abs(math.log10(p['T0']) - e) < 0.5)]
        for cls in ['rand', 'jump', 'pspec_0.5', 'zero', 'zero_mid', 'edge']:
            c = [p for p in cand if p['cls'] == cls]
            if c: zp.append(dict(T0=c[0]['T0'], u=c[0]['u'], cls=cls))
    small = []
    for T0 in [1001, 1500, 3000, 10000, 100000, 1000000]:
        for k in range(3): small.append(dict(T0=T0, u=rng.uniform(0, 1), cls='small'))
    rows = []
    for e in [10, 11, 12]:
        for k in range(3): rows.append(dict(T0=10 ** e, u=rng.uniform(-2.5, 3.5), cls='row'))
    pts = dict(zp=zp, small=small, rows=rows)
    json.dump(pts, L.xopen(f'{R}/data/bat_points.json'), indent=0)
    # references
    inp = f'{R}/data/bat_ref_AZ.in'
    with L.xopen(inp) as f:
        for p in small: f.write(f"AZ {p['T0']} {p['u'].hex()} {128 + p['T0'].bit_length()}\n")
    env = dict(os.environ, FP_MB='800', RSS_KB='800000', TL='3600')
    print(subprocess.run([L.WD, L.REF, inp, f'{R}/data/bat_ref_AZ.jsonl'], env=env, capture_output=True, text=True).stdout)
    inp = f'{R}/data/bat_ref_AR.in'
    with L.xopen(inp) as f:
        for p in rows:
            for a in [2.8, 1.6]: f.write(f"AR {p['T0']} {p['u'].hex()} {a} 128\n")
    print(subprocess.run([L.WD, L.REF, inp, f'{R}/data/bat_ref_AR.jsonl'], env=env, capture_output=True, text=True).stdout)


def load_refs():
    refs = {}
    for f in [f'{R}/data/ref_low_AZ.jsonl', f'{R}/data/bat_ref_AZ.jsonl']:
        for l in open(f):
            d = json.loads(l); refs[(int(d['T0']), float.fromhex(d['u']))] = d['Z']
    rrefs = {}
    for l in open(f'{R}/data/bat_ref_AR.jsonl'):
        d = json.loads(l); rrefs[(int(d['T0']), float.fromhex(d['u']), d['a'])] = d['P']
    return refs, rrefs


def ec_of(build):
    src = f'{R}/mut/{build}/zfast.c' if build != 'prod' else '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/src_v10b/zfast.c'
    return float(re.search(r'#define ZF_EC ([0-9.e+-]+)', open(src).read()).group(1))


def fam(name, res, key='ok'):
    fails = [r for r in res if not r[key]]
    return dict(family=name, n=len(res), fails=len(fails), pass_=len(fails) == 0,
                max_ratio=max([r.get('ratio', 0) for r in res] + [0]), first_fail=fails[0] if fails else None)


def run(build):
    exe = f'{R}/bin/rv_drv.{build}'
    D = L.Drv(exe)
    pts = json.load(open(f'{R}/data/bat_points.json'))
    refs, rrefs = load_refs()
    out = dict(build=build, families=[])
    # K
    ctx.prec = 128
    E = ec_of(build); rng = random.Random(9); res = []; mx = 0.0
    tp = 2 * arb.pi(); two64 = arb(2) ** 64
    vs = [(q * (1 << 62) + (1 << 61) - 1 - rng.randrange(1 << 40)) % (1 << 64) for q in range(4) for _ in range(5000)]
    vs += [rng.randrange(1 << 64) for _ in range(40000)]
    for v in vs:
        d = D.q(f'CS {v}'); x = tp * arb(v) / two64
        e = max(float(abs(arb(float.fromhex(d['c'])) - x.cos()).upper()), float(abs(arb(float.fromhex(d['s'])) - x.sin()).upper()))
        mx = max(mx, e)
    out['families'].append(dict(family='K', n=len(vs), max_err=mx, E_c=E, pass_=mx <= E, fails=int(mx > E), max_ratio=mx / E))
    # P
    res = []
    for (T0, u, n0, B, J) in [(10 ** 10, 0.3, 20000, 300, 6), (10 ** 10, 0.3, 5000, 200, 4), (10 ** 12, 1.7, 2000, 120, 2),
                              (10 ** 16, 0.5, 10 ** 7, 16384, 12), (10 ** 16, 0.5, 4 * 10 ** 7 - 70000, 65536, 24), (10 ** 18, 0.25, 4 * 10 ** 8 - 20000, 16384, 12),
                              (10 ** 14, 0.9, 300000, 4000, 8)]:
        d = D.PH(T0, u, n0, B, J)
        res.append(dict(case=[T0, u, n0, B, J], obs=d['maxerr'], bound=d['bound'], ok=d['maxerr'] <= d['bound'], ratio=d['maxerr'] / d['bound']))
    out['families'].append(fam('P', res))
    # Zp, Sp
    resZ, resS = [], []; sess = {}
    for p in pts['zp']:
        ref = refs[(p['T0'], p['u'])]
        a = L.compare(D.Z(p['T0'], p['u'])['Z'], ref); resZ.append(dict(p, ok=a['overlap'], ratio=a['ratio']))
        c = L.centre(p['u']); k = (p['T0'], c)
        if k not in sess: sess[k] = D.sess(p['T0'], c)
        b = L.compare(D.SZ(sess[k], p['u'])['Z'], ref); resS.append(dict(p, ok=b['overlap'], ratio=b['ratio']))
    out['families'].append(fam('Zp', resZ)); out['families'].append(fam('Sp', resS))
    # Zs
    res = []
    for p in pts['small']:
        a = L.compare(D.Z(p['T0'], p['u'], kcorr=2)['Z'], refs[(p['T0'], p['u'])]); res.append(dict(p, var='kcorr2', ok=a['overlap'], ratio=a['ratio']))
    for p in pts['zp'][:12]:
        ref = refs[(p['T0'], p['u'])]
        for (J, bm, l2) in [(6, 65536, -20.0), (24, 65536, -72.0), (4, 4096, -10.0)]:
            a = L.compare(D.Z(p['T0'], p['u'], J=J, bmax=bm, l2=l2)['Z'], ref); res.append(dict(p, var=[J, bm, l2], ok=a['overlap'], ratio=a['ratio']))
    out['families'].append(fam('Zs', res))
    # Ss
    res = []
    for p in pts['zp'][:12]:
        ref = refs[(p['T0'], p['u'])]; c = L.centre(p['u'])
        for (K, Dl) in [(3, 0.6), (5, 0.6), (2, 0.2)]:
            sid = D.sess(p['T0'], c, K=K, Delta=Dl)
            a = L.compare(D.SZ(sid, p['u'])['Z'], ref); res.append(dict(p, var=[K, Dl], ok=a['overlap'], ratio=a['ratio']))
    out['families'].append(fam('Ss', res))
    # Rp
    res = []
    for p in pts['rows']:
        for a_ in [2.8, 1.6]:
            ref = rrefs[(p['T0'], p['u'], a_)]
            sid = D.sess(p['T0'], L.centre(p['u']), kind=1, a=a_)
            r1 = D.SR(sid, p['u']); r2 = D.ROW(p['T0'], p['u'], a_)
            x = L.compare(r1['P'], ref); y = L.compare(r2['P'], ref)
            res.append(dict(p, a=a_, kind='sess', ok=x['overlap'] and r1['ok'] == 1, ratio=x['ratio']))
            res.append(dict(p, a=a_, kind='single', ok=y['overlap'] and r2['ok'] == 1, ratio=y['ratio']))
    out['families'].append(fam('Rp', res))
    D.close()
    out['detected'] = any(not f['pass_'] for f in out['families'])
    json.dump(out, L.xopen(f'{R}/data/bat_{build}.json'), indent=0)
    print(build, 'DETECTED' if out['detected'] else 'not detected', [(f['family'], f['fails'], f'{f["max_ratio"]:.3g}') for f in out['families']], flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'prep': prep()
    else:
        for b in sys.argv[2:]: run(b)
