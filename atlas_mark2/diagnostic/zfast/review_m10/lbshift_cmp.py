import json, sys
from decimal import Decimal, getcontext
getcontext().prec = 60
def ball(s):
    m, r = s.strip('[]').split('+/-'); return Decimal(m.strip()), Decimal(r.strip())
h = json.load(open(sys.argv[1])); x = json.load(open(sys.argv[2]))
print('resumed items_loaded', x['info']['items_loaded'], '/', x['info']['items'])
dis = 0
for (u, a), (_, b) in zip(h['Z'], x['Z']):
    (ma, ra), (mb, rb) = ball(a), ball(b); gap = abs(ma - mb) - ra - rb
    dis += gap > 0
    print(f'u={u:9.4f} |mid diff|={float(abs(ma - mb)):.3e} rad_honest={float(ra):.2e} rad_resumed={float(rb):.2e} ', 'DISJOINT (unsound)' if gap > 0 else 'overlap')
print('disjoint', dis, 'of', len(h['Z']))
