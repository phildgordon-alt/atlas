"""engine/regress_v1 tier-0 worker for atlas_v5-format zfast windows (one RUN directory per process).

Runs the FROZEN replay logic of the run's own code tree (TREE/lib/replay5.py: model rebuild, outward hardening, sha-pinned
verify_zs5.check, in-memory no-parity verifier) on every certificate of the run, with two substitutions only:
  * row measurements (Elo, Ehi) are read from the run's STORED gen_measurements.json instead of being re-measured
    (re-measurement = tier 1/2);
  * the Z sign-change check is skipped (check_z=False): it needs a zfast session at height T0 (tier 1/2).
Everything else (model, Nwin, far bound F, the (R)/(C) Arb bisection, hardening by 2 ulps) is recomputed by the frozen code.
Nothing is written inside the frozen tree: the worker only imports from it (cwd = TREE/lib, read-only, -B, no bytecode).

usage: python -B zfast_t0_worker.py TREE RUN_DIR OUT_JSON [--perturb-meas | --wrong-y | --swap-interval | --tamper-cert]
The four flags are the pre-registered negative controls (PREREG.md section 4); each one mutates IN MEMORY only."""
import sys, os, json, glob, time, copy, math

if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run with python -O / PYTHONOPTIMIZE (Atlas rule)')

TREE, RUN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ARGS = sys.argv[4:]
NO_A1 = '--no-a1' in ARGS                     # PREREG amendment A1 off: reproduce the as-registered procedure
CTL = next((x for x in ARGS if x != '--no-a1'), None)
LIB = os.path.join(TREE, 'lib')
VSHA = open(os.path.join(TREE, 'VERIFY_ZS5.sha256')).read().split()[0]
os.environ['VERIFY_ZS5_SHA'] = VSHA
os.chdir(LIB)                       # replay5 opens 'verify_zs5.py' relative to cwd (read-only)
sys.path.insert(0, LIB)
sys.dont_write_bytecode = True
import replay5 as R                 # noqa: E402  (asserts the verify_zs5 pin itself)
from heights import Grid            # noqa: E402

P = json.load(open(os.path.join(RUN, 'pieces.json')))
T0 = P['T0']; G = Grid(T0, P['grid'])
MEAS_W = json.load(open(os.path.join(RUN, 'gen_measurements.json')))
missing = []


from flint import ctx as _ctx      # noqa: E402


def stored_measure(key, base, evaluator):
    """stored generator measurement for row id `key` (offset coordinates) -> (Elo, Ehi); work-coordinate lookup.
    Amendment A1 (PREREG): the frozen model5.measure initialises the sech engine, whose _init sets flint ctx.prec = 256 for the rest
    of the process (certify_sech_interferometer._init, line 163).  The stored-data substitute reproduces that side effect, so the
    frozen replay logic runs in the same precision state as the real replay (relevant to the pre-v5z4 ambient-precision N_win)."""
    if not NO_A1:
        _ctx.prec = 256
    a, u = key.split('|')
    wkey = f'{a}|{G.from_off(float(u))!r}'
    if wkey not in MEAS_W:
        missing.append(key)
        raise KeyError(f'no stored measurement for {key}')
    lo, hi = MEAS_W[wkey]
    if CTL == '--perturb-meas':      # negative control: every stored Ehi lowered by 1e-3 (an untrue, too-small enclosure)
        hi = hi - 1e-3
    return float(lo), float(hi)


R.M.measure = stored_measure
R.MEAS.clear()


def no_z(checker):
    def f(*a, **k):
        k['check_z'] = False
        return checker(*a, **k)
    return f


def mutate(c):
    c = copy.deepcopy(c)
    if CTL == '--wrong-y':           # negative control: dual vector replaced by a permutation (wrong y)
        y = list(c['y']); J = len(c['ids']); up = y[:J]; c['y'] = up[::-1][1:] + up[::-1][:1] + y[J:] if J > 1 else [0.0] * len(y)
    elif CTL == '--swap-interval':   # negative control: one sign-change interval moved to an empty place (swap with neighbour gap)
        iv = c['zs_intervals']
        if len(iv) >= 2:
            k = len(iv) // 2; t1, t2 = iv[k]; n1, n2 = iv[k + 1]
            iv[k] = [t2, n1]         # the gap between two consecutive sign changes: no sign change credited there
        c['zs_intervals'] = iv
    elif CTL == '--tamper-cert':     # negative control: every credit weight w raised by 10 %
        c['w'] = [float(v) * 1.10 for v in c['w']]
    return c


t0 = time.time()
files = sorted(glob.glob(os.path.join(RUN, 'certs', 'cert_*.json'))) + sorted(glob.glob(os.path.join(RUN, 'certs_np', 'cert_*.json')))
out = []
for f in files:
    c = json.load(open(f))
    if CTL: c = mutate(c)
    mode = c.get('mode', 'main')
    base_checker = R.NPCHECK if mode == 'noparity' else R.verify_zs.check
    for h in (False, True):
        try:
            r = R.replay(f, h, c=c, checker=no_z(base_checker))
            out.append(dict(cert=os.path.relpath(f, RUN), mode=mode, hardened=h, passed=r['passed'], model_match=r['model_match'],
                            rejected_rows=r['rejected_rows'], rows=r['rows'], intervals=r['intervals'],
                            regions=[{k: q.get(k) for k in ('region', 'status', 'min_candidate_lower', 'boxes', 'sum_w')} for q in r['regions']],
                            min_candidate_lower=r['min_candidate_lower'], seconds=r['seconds']))
        except Exception as e:      # recorded, never swallowed silently
            out.append(dict(cert=os.path.relpath(f, RUN), mode=mode, hardened=h, passed=False, error=f'{type(e).__name__}: {e}'))
json.dump(dict(tree=TREE, run=RUN, control=CTL, verify_zs5_sha=VSHA, records=out, missing_measurements=sorted(set(missing)),
               seconds=round(time.time() - t0, 2)), open(OUT, 'w'), indent=1)
print(json.dumps(dict(run=RUN, control=CTL, n=len(out), passed=sum(r['passed'] for r in out), seconds=round(time.time() - t0, 2))))
