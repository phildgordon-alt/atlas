"""Follow-up to check_dylib.py: is the computed (unprinted) rv_drv.prod th=2 ball inside the dylib's printed ball?  Uses the
driver's exact-ish radius (6 significant digits, inflated by 1e-5 relative) instead of its 3-digit printed radius."""
import sys, json
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L
from flint import arb, ctx
D = [json.loads(l) for l in open(f'{L.R}/data/dylib_low.jsonl')]
drv = L.Drv(); S = {}; bad = 0; n = 0
for d in D:
    c = L.centre(d['u']); k = (d['T0'], c)
    if k not in S: S[k] = drv.sess(d['T0'], c, th=2)
    r = drv.SZ(S[k], d['u'])
    ctx.prec = 600
    z = arb(d['dylib']); m = arb(r['Z']).mid(); rad = arb(r['rad']) * (1 + arb('1e-5'))
    inside = bool(abs(m - z.mid()) + rad <= z.rad())
    n += 1; bad += not inside
print('driver computed ball inside dylib printed ball:', n - bad, '/', n)
drv.close()
