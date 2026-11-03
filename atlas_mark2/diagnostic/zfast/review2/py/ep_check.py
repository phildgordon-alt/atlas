"""ep_check.py ZS_JSON SESSION_JSONL : every certified interval (zs.json) must have opposite decided signs at its endpoints"""
import sys, json
from flint import arb, ctx
ctx.prec = 256
zs = json.load(open(sys.argv[1]))
vals = {}
for l in open(sys.argv[2]):
    d = json.loads(l)
    if d.get('kind') == 'Z': vals[float.fromhex(d['u'])] = arb(d['Z'])
ok = 0; worst = 1e300; res = []
for a, b in zs['intervals']:
    za, zb = vals[a], vals[b]
    good = (za > 0 and zb < 0) or (za < 0 and zb > 0)
    ok += good
    for z in (za, zb):
        r = abs(float(z.mid())) / float(z.rad()); worst = min(worst, r)
print(json.dumps(dict(intervals=len(zs['intervals']), opposite_decided=ok, min_absZ_over_rad=worst)))
