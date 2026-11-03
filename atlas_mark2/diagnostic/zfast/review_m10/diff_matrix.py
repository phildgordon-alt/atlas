#!/usr/bin/env python3
"""review_m10: v13b (frozen dylib) / ref13h (frozen v13b source + hash) / v14 differential matrix.  Each run is a fresh process, nice 19."""
import json, subprocess, sys, random
import os
H = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'run_one.py')
def run(*a):
    p = subprocess.run(['nice', '-n', '19', 'python3', H, *map(str, a)], capture_output=True, text=True)
    if p.returncode: return dict(err=p.returncode, stderr=p.stderr[-400:])
    return json.loads(p.stdout)
cases = json.loads(sys.argv[1])          # list of [T0, u0, H, Delta, D, [W...], npts, gridn]
rng = random.Random(20261102); bad = 0
for T0, u0, Hh, Dl, D, Ws, npts, gridn in cases:
    seed = rng.randrange(10**9)
    ref = run('ref13h', T0, u0, Hh, Dl, D, D, '', npts, seed, 0)
    v13 = run('v13b', T0, u0, Hh, Dl, D, D, '', npts, seed, gridn)
    line = f'T0={T0} H={Hh} Delta={Dl} D={D}: '
    for W in Ws:
        v = run('v14', T0, u0, Hh, Dl, D, W, '', npts, seed, gridn)
        okh = v.get('hash') is not None and v.get('hash') == ref.get('hash'); okz = v.get('Z') is not None and v.get('Z') == v13.get('Z') == ref.get('Z'); okg = (v.get('grid') is not None and v.get('grid') == v13.get('grid')) if gridn else True
        bad += not (okh and okz and okg)
        line += f"W={W}[hash {'=' if okh else 'DIFF'} Z {'=' if okz else 'DIFF'} grid {'=' if okg else 'DIFF'} items {v.get('info', {}).get('items')} fast {v.get('info', {}).get('sec_fast')}] "
    print(line, 'ref_hash', (ref.get('hash') or str(ref))[:16], flush=True)
print('MISMATCHES', bad)
