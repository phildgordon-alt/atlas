#!/usr/bin/env python
"""Diagnostic cross-check of a finished atlas_v5 target against Arb's rigorous Turing count (NOT part of the trust base).
CLI: crosscheck.py RUN_DIR N_lo N_hi  (Arb N(T0 + u_lo), N(T0 + u_hi) from nzeros/nzeros_big.jsonl or arb_nzeros.py)
Counts the certified sign-change intervals (as used by the replay-passed main certificates, i.e. verified by verify_zs5) lying inside the
target, flags intervals straddling a target edge, and collects margins.  Writes RUN_DIR/crosscheck.json."""
import sys, json, glob, math
from fractions import Fraction as F
from pathlib import Path
run = Path(sys.argv[1]); Nlo, Nhi = int(sys.argv[2]), int(sys.argv[3])
P = json.load(open(run / 'pieces.json')); T0 = P['T0']; ulo, uhi = P['target']
rc = json.load(open(run / 'replay_check' / 'replay_check.json'))
recs = [json.loads(l) for l in open(run / 'replay_check' / 'replay.jsonl')]
ivs = set(); inside = set(); straddle = set()
for f in sorted(glob.glob(str(run / 'certs' / 'cert_*.json'))):
    for a, b in json.load(open(f))['zs_intervals']: ivs.add((a, b))
for a, b in sorted(ivs):
    if ulo <= a and b <= uhi: inside.add((a, b))
    elif a < uhi and b > ulo: straddle.add((a, b))
# disjointness of the counted intervals (each holds >= 1 zero, odd multiplicity; disjoint => distinct zeros)
s = sorted(inside); disjoint = all(s[i][1] <= s[i + 1][0] for i in range(len(s) - 1))
gl = [json.loads(l) for l in open(run / 'gen.jsonl')]
att = [x for x in gl if x['stage'] == 'attempt']
mains = [r for r in recs if r['mode'] == 'main']; nps = [r for r in recs if r['mode'] == 'noparity']
res = dict(run=str(run), T0=T0, target_exact=[str(F(T0) + F(ulo)), str(F(T0) + F(uhi))], arb_N=[Nlo, Nhi], arb_count=Nhi - Nlo,
           atlas_sign_changes_in_target=len(inside), straddling=sorted(straddle), disjoint=disjoint, match=(len(inside) == Nhi - Nlo and not straddle),
           intervals_inside=[[str(F(T0) + F(a)), str(F(T0) + F(b))] for a, b in s],
           intervals_inside_decimal=['%.6f' % float(F(a) + F(b)) for a, b in []],
           widths=[b - a for a, b in s],
           main_min_candidate_lower=[dict(cert=Path(r['cert']).name, hardened=r['hardened'], mcl=r['min_candidate_lower'], rows=r['rows'], intervals=r['intervals']) for r in mains],
           np_min_candidate_lower=min((r['min_candidate_lower'] for r in nps if r['min_candidate_lower'] is not None), default=None),
           attempts=[(x['piece'], x['tier'], x['status'], x.get('min_candidate_lower'), x['rows_used'], x['intervals']) for x in att],
           closed=rc['passed'], claimB=rc['passed_B'], log10T=math.log10(T0) if T0 else None)
json.dump(res, open(run / 'crosscheck.json', 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('arb_count', 'atlas_sign_changes_in_target', 'straddling', 'disjoint', 'match', 'closed', 'claimB')}),
      json.dumps(res['attempts']))
