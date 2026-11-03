"""Sign-change intervals of a finished v5z window (crosscheck.py without Arb counts): intervals of the replay-passed main certificates
inside the target, straddlers, disjointness; writes RUN/intervals_summary.json and prints it; also writes the endpoints as 'T0 u' lines."""
import json, sys, glob
from fractions import Fraction as F
run = sys.argv[1]; P = json.load(open(run + '/pieces.json')); T0 = P['T0']; ulo, uhi = P['target']
rc = json.load(open(run + '/replay_check_independent/replay_check.json'))
ivs = set()
for f in sorted(glob.glob(run + '/certs/cert_*.json')):
    for a, b in json.load(open(f))['zs_intervals']: ivs.add((a, b))
inside = sorted((a, b) for a, b in ivs if ulo <= a and b <= uhi); straddle = sorted((a, b) for a, b in ivs if not (ulo <= a and b <= uhi) and a < uhi and b > ulo)
disjoint = all(inside[i][1] <= inside[i + 1][0] for i in range(len(inside) - 1))
gaps = [inside[i + 1][0] - inside[i][1] for i in range(len(inside) - 1)]
res = dict(run=run, T0=T0, closed=rc['passed'], claimB=rc['passed_B'], sign_changes_in_target=len(inside), straddling=straddle, disjoint=disjoint,
           intervals=[[a, b] for a, b in inside], min_gap_upper=min(b2 - a1 for (a1, b1), (a2, b2) in zip(inside, inside[1:])) if len(inside) > 1 else None,
           min_candidate_lower=rc['min_candidate_lower'])
json.dump(res, open(run + '/intervals_summary.json', 'w'), indent=1)
with open(run + '/endpoints.txt', 'w') as f:
    for a, b in sorted(ivs): f.write(f'{T0} {a!r}\n{T0} {b!r}\n')
print(json.dumps({k: v for k, v in res.items() if k != 'intervals'}))
