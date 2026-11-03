"""Cost probe: time one rigorous Z(T0+u) (the pinned verify_zs5.Zg, exact height, prec 160+bitlen(T0)) and one
length-2 zeta jet at 1/2+b+i(T0+u), b=pi/(2*2.8) (the v5 row's single Arb call, prec 128+bitlen).  usage: cost_probe.py EXP [jet]"""
import sys, time, json, resource
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/record_heights/v5run/lib')
import flint
from flint import arb, acb, acb_series, ctx
from verify_zs5 import Zg
from heights import hx
E = int(sys.argv[1]); T0 = 10**E; u = 0.505
t = time.time(); z = Zg(T0, u); tz = time.time() - t
out = dict(exp=E, flint=flint.__version__, Z=str(z.mid())[:25], Z_rad=float(z.rad()), Z_seconds=round(tz, 2))
if len(sys.argv) > 2:
    ctx.prec = 128 + T0.bit_length(); x = hx(T0, u); s = acb(arb(1)/2 + arb.pi()/(2*arb(2.8)), x)
    t = time.time(); c = acb_series([s, 1], 2).zeta().coeffs(); r = -c[1]/c[0]; out['jet_seconds'] = round(time.time() - t, 2); out['jet_rad'] = float(r.real.rad())
out['maxrss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 1)
print(json.dumps(out), flush=True)
