"""Y2 (PREDICTIONS_M5d): recompute N_win with the v5z4 model5 (fixed precision) for every existing atlas_v5-format main certificate
(v5 originals, record_heights, v5z, v5z2, v5z3), in a fresh process with the sech engine NOT initialised (ctx.prec 128), and compare
with the stored value.  Also recompute with the engine's 256-bit side effect active, to show the result no longer depends on it."""
import sys, glob, json
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z4/lib')
import model5 as M
from heights import Grid
from flint import ctx
D = '/Users/kiosk/atlas_mark2/diagnostic/'
files = sorted(set(glob.glob(D + 'atlas_v5/runs/*/*/certs/cert_*.json') + glob.glob(D + 'record_heights/v5run/runs/*/*/certs/cert_*.json') +
                   glob.glob(D + 'zfast/atlas_v5z*/runs/*/*/certs/cert_*.json')))
rows = []
for f in files:
    c = json.load(open(f))
    if c.get('format') != 'atlas_v5' or c.get('mode', 'main') != 'main': continue
    G = Grid(c['T0'], c['grid'])
    out = []
    for prec in (128, 256):
        ctx.prec = prec; M._CU.clear()
        out.append(float(M.model(G, c['T0'], c['bins'][0], c['bins'][1], work=False)['Nwin']))
    ctx.prec = 128
    rows.append(dict(cert=f.replace(D, ''), T0=c['T0'], stored=c['Nwin'], v5z4_amb128=out[0], v5z4_amb256=out[1],
                     equal=(out[0] == float(c['Nwin'])), ambient_independent=(out[0] == out[1])))
bad = [r for r in rows if not r['equal']]
res = dict(certificates=len(rows), equal=sum(r['equal'] for r in rows), ambient_independent=sum(r['ambient_independent'] for r in rows),
           mismatches=bad, heights=sorted(set(r['T0'] for r in rows)))
json.dump(dict(summary=res, rows=rows), open('/Users/kiosk/atlas_mark2/diagnostic/zfast/runs/m5/Y2_nwin_all.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
