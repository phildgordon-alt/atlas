# margin_anatomy_v1.py (2026-11-01, for MARGIN_ANATOMY.md / CORE_ROADMAP.md). DIAGNOSTIC ONLY: not in any trust path,
# reads frozen run directories read-only, writes only to runs/roadmap_margin/. Float arithmetic (except where noted);
# zero locations come from the NON-rigorous scan files runs/m5/scan2_1e*/ and runs/m6/scan3_1e24/ (midpoints).
# Identity used (all main certs have y_low = 0, y_c = 0):  margin = Pc - K + Sum w = Pc - far - resid,
#   Pc = min_region Phi(x,d,2), far = K - Sum_{credited zeros} Phi(gamma), resid = Sum_i (Phi(gamma_i) - w_i).
import json, glob, os, math, cmath, sys
Z = '/Users/kiosk/atlas_mark2/diagnostic/zfast'
SCAN = {16: 'runs/m5/scan2_1e16', 20: 'runs/m5/scan2_1e20', 21: 'runs/m5/scan2_1e21', 22: 'runs/m5/scan2_1e22',
        23: 'runs/m5/scan2_1e23', 24: 'runs/m6/scan3_1e24'}
COMBO_A = {'1.6': 0.98520, '2.8a': 0.01190, '2.8b': 0.00300}
def U(a, r, d): return (1 / cmath.cosh(a * complex(r, -d))).real
zcache = {}
def zeros(e):
    if e not in SCAN: return None
    if e not in zcache:
        iv = json.load(open(os.path.join(Z, SCAN[e], 'zeros_intervals.json')))['intervals']
        zcache[e] = [(a + b) / 2 for a, b in iv]
    return zcache[e]
tight = {}
tp = os.path.join(Z, 'runs/roadmap_margin/tight_v1.jsonl')
if os.path.exists(tp):
    for l in open(tp):
        o = json.loads(l); tight[o['cert']] = o['tight_lower']
seen = set(); out = []
for cp in sorted(glob.glob(Z + '/atlas_v5z*/runs/w*/*/certs/cert_p*.json')):
    rd = os.path.dirname(os.path.dirname(cp)); c = json.load(open(cp)); T0 = c['T0']; e = len(str(T0)) - 1
    if e < 16: continue
    key = (T0, c['piece'], tuple(c['y']), c['window'][0])
    if key in seen: continue
    seen.add(key)
    meas = json.load(open(rd + '/gen_measurements.json'))
    ids = c['ids']; J = len(ids); y = c['y']; yup = y[:J]
    assert not any(y[J:2 * J]) and y[2 * J] == 0
    rows = [(float(i.split('|')[0]), float(i.split('|')[1])) for i in ids]
    Ehi = [meas[i][1] for i in ids]; Elo = [meas[i][0] for i in ids]
    def phi(x, d, yy=yup, f=1): return f * sum(yy[j] * U(rows[j][0], x - rows[j][1], d) for j in range(J))
    K = sum(yup[j] * Ehi[j] for j in range(J))
    x0, x1, d0, d1 = c['regions'][0]
    Pc = min(phi(x0 + (x1 - x0) * i / 200, d1 * k / 50, f=2) for i in range(201) for k in range(51))
    ivs = c['zs_intervals']; w = c['w']; gam = [(a + b) / 2 for a, b in ivs]
    sphi = sum(phi(g, 0) for g in gam); resid = sum(phi(g, 0) - wi for g, wi in zip(gam, w)); far = K - sphi
    L = math.log(T0 / (2 * math.pi)); wlo, whi = c['window']
    rec = dict(cert=os.path.relpath(cp, Z), e=e, piece=c['piece'], L=round(L, 3), ids=ids, yup=[round(v, 4) for v in yup],
               combo=('A' if abs(yup[0] - 0.9852) < 1e-3 else 'B' if (J == 3 and abs(yup[0] - 0.4791) < 1e-3) else 'other'),
               Nwin=round(c['Nwin'], 2), ballrad_max=max(Ehi[j] - Elo[j] for j in range(J)), K=K, sum_w=sum(w), Pc=Pc,
               far=far, resid=resid, sampled=c['sampled_margin'], reported=c['min_candidate_lower'],
               tight=tight.get(cp.split('runs/')[1]), window=[wlo, whi], n_credit=len(ivs))
    zs = zeros(e)
    if zs is not None and abs(c['T0'] - 10 ** e) == 0 and min(zs) < wlo - 15 and max(zs) > whi + 15:
        out_z = [g for g in zs if g < wlo or g > whi]
        far_scan = sum(phi(g, 0) for g in out_z)
        def strip(lo, hi): return sum(phi(g, 0) for g in out_z if lo <= min(abs(g - wlo) if g < wlo else 99, abs(g - whi) if g > whi else 99) < hi)
        rec.update(far_scan=far_scan, far_0_05=strip(0, 0.5), far_05_1=strip(0.5, 1), far_1_2=strip(1, 2), far_2plus=strip(2, 99),
                   widen1_gain_upper=strip(0, 1), widen2_gain_upper=strip(0, 2),
                   nearest_out_left=min((wlo - g for g in out_z if g < wlo), default=None),
                   nearest_out_right=min((g - whi for g in out_z if g > whi), default=None),
                   n_out_within1=sum(1 for g in out_z if (wlo - 1 <= g < wlo) or (whi < g <= whi + 1)),
                   n_in_window=sum(1 for g in zs if wlo <= g <= whi))
    # combo swap test: evaluate the other fixed combination on this piece (same row ids), w_i := Phi at interval midpoint minus resid share
    if J == 3:
        for nm, yy in (('A', [0.98520, 0.01190, 0.00300]), ('B', [0.47909, 0.26312, 0.25779])):
            KK = sum(yy[j] * Ehi[j] for j in range(J))
            PP = min(phi(x0 + (x1 - x0) * i / 200, d1 * k / 50, yy, 2) for i in range(201) for k in range(51))
            WW = sum(min(phi(a, 0, yy), phi(b, 0, yy)) for a, b in ivs)
            rec['swap_' + nm] = PP - KK + WW
    out.append(rec)
os.makedirs(Z + '/runs/roadmap_margin', exist_ok=True)
with open(Z + '/runs/roadmap_margin/anatomy_v1.jsonl', 'w') as f:
    for r in out: f.write(json.dumps(r) + '\n')
print(len(out), 'records')
