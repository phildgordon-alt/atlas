"""M4 acceptance comparison (THEORY_V5Z section 3): original v5 window vs v5z window.
compare_windows.py ORIG_RUN NEW_RUN -> JSON: closure (A)/(B), counts, one-to-one interval match (exact rationals), min_candidate_lower."""
import json, sys
from fractions import Fraction as F
o, n = sys.argv[1], sys.argv[2]
def load(r):
    c = json.load(open(r + '/crosscheck.json')); rc = json.load(open(r + '/replay_check/replay_check.json'))
    ri = json.load(open(r + '/replay_check_independent/replay_check.json'))
    iv = [(F(a), F(b)) for a, b in c['intervals_inside']]
    return dict(c=c, rc=rc, ri=ri, iv=iv)
A, B = load(o), load(n)
def meets(x, y): return x[0] <= y[1] and y[0] <= x[1]
m1 = [sum(meets(x, y) for y in B['iv']) for x in A['iv']]; m2 = [sum(meets(y, x) for x in A['iv']) for y in B['iv']]
res = dict(orig=o, new=n,
           closed=[A['c']['closed'], B['c']['closed']], claimB=[A['c']['claimB'], B['c']['claimB']],
           independent_replay=[A['ri']['passed'], B['ri']['passed']], independent_B=[A['ri']['passed_B'], B['ri']['passed_B']],
           counts=[A['c']['atlas_sign_changes_in_target'], B['c']['atlas_sign_changes_in_target']], arb_count=A['c']['arb_count'],
           new_matches_arb=B['c']['match'],
           one_to_one=all(k == 1 for k in m1) and all(k == 1 for k in m2) and len(m1) == len(m2),
           identical_intervals=A['iv'] == B['iv'],
           min_candidate_lower=[A['rc'].get('min_candidate_lower'), B['rc'].get('min_candidate_lower')],
           seams=[A['ri']['tiling'].get('seams_hull'), B['ri']['tiling'].get('seams_hull')] if 'tiling' in A['ri'] else None)
res['mcl_diff'] = abs(res['min_candidate_lower'][0] - res['min_candidate_lower'][1])
res['ACCEPT'] = (res['closed'] == [True, True] and res['claimB'] == [True, True] and res['independent_replay'] == [True, True]
                 and res['counts'][0] == res['counts'][1] == res['arb_count'] and res['one_to_one'])
print(json.dumps(res, indent=1))
