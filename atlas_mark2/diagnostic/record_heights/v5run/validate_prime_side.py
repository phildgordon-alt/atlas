#!/usr/bin/env python
"""THEORY_V5 section 9 step 2: the 'dirichlet' evaluator (lib/sech5.py) against v4's 'zeta' evaluator (certify_sech_interferometer.E_comp)
at exact heights T0 + u.  For each (T0, u, a): both Arb enclosures of E_a(T0 + u), their radii, overlap (required), times; also the
prime parts separately.  CLI: validate_prime_side.py OUT.json T0 [T0 ...]  (offsets u = 0.005, 0.505, 1.005, 1.505, 1.995)"""
import sys, json, time, math
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/atlas_v5/lib')
import model5 as M                                     # noqa: E402  (imports integer_mechanism; ctx.prec 128)
import sech5                                           # noqa: E402
import certify_sech_interferometer as eng              # noqa: E402
from heights import hx                                 # noqa: E402
from flint import arb, ctx                             # noqa: E402

out = []; U = (0.005, 0.505, 1.005, 1.505, 1.995)
for T0 in map(int, sys.argv[2:]):
    for a in (1.6, 2.2, 2.8):
        M.measure(f'{a}|0.5', 0, 'zeta')                # configure + _init the engine for kernel a (as model5.measure does)
        sech5.setup(a)
        for u in U:
            old = ctx.prec; ctx.prec = 256
            try:
                x = hx(T0, u)
                t = time.time(); Ez = eng.E_comp(x); tz = time.time() - t
                t = time.time(); Ed = sech5.E5(a, x, T0); td = time.time() - t
                pz = eng.prime_series(x); pd = sech5.prime_dirichlet(a, x, T0)
            finally: ctx.prec = old
            ov = bool(Ez.overlaps(Ed)); povl = bool(pz.overlaps(pd))
            r = dict(T0=T0, u=u, a=a, E_zeta=Ez.str(15), E_dirichlet=Ed.str(15), rad_zeta=float(Ez.rad()), rad_dirichlet=float(Ed.rad()),
                     overlap=ov, prime_overlap=povl, mid_diff=float(abs(Ez.mid() - Ed.mid())), sec_zeta=round(tz, 3), sec_dirichlet=round(td, 3),
                     K_zeta=eng._W['K'])
            out.append(r); print(json.dumps(r), flush=True)
            json.dump(dict(results=out, all_overlap=all(q['overlap'] for q in out)), open(sys.argv[1], 'w'), indent=1)
print(json.dumps(dict(n=len(out), all_overlap=all(q['overlap'] for q in out), max_rad_dirichlet=max(q['rad_dirichlet'] for q in out),
                      max_rad_zeta=max(q['rad_zeta'] for q in out))))
