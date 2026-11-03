"""atlas_v5 replay = atlas_v4 lib/replay4.py at exact heights (THEORY_V5.md sections 1-4): every certificate is in offsets from its integer
T0; the model is rebuilt on the certificate's grid (heights.Grid, offsets), rows are re-measured at the exact heights T0 + u with the
certificate's evaluator (model5.measure), F by model5.far_bound5, and the sha-pinned verify_zs5.check is called with T0.
CLI (in a directory holding verify_zs5.py, model5.py, heights.py, sech5.py):  VERIFY_ZS5_SHA=... replay5.py OUT.jsonl cert.json [...]
atlas_v4 docstring follows (verify_zs -> verify_zs5, model4 -> model5).
atlas_v4 replay (independent of the generator; THEORY_V4.md section 5).  Uses NO number produced by the generator except the dual
certificate itself (row ids, y, w, sign-change intervals, regions).
CLI (in a directory holding verify_zs.py, model4.py):  VERIFY_ZS_SHA=... replay4.py OUT.jsonl cert.json [cert.json ...]
For every certificate, in both modes (plain, harden):
  * the model is REBUILT from its definition (model4.model: all-open, bins e(k) = T0 + k*0.01, k in [k0, k1)) and must equal the
    certificate's vars / window / Nwin exactly; the bins are taken from the run record (pieces.json), passed in the cert as T0/bins and
    re-checked by replay_target4.py against pieces.json;
  * every row is REBUILT: sech 'a|t' (0 < a < pi) -> fresh E_comp(t) (certify_sech_interferometer, unchanged) + im.far_bound;
    any other row id (e.g. Lorentzian 'L...') is REJECTED (THEORY_V4 section 2);
  * 'harden': Elo/Ehi/Fa moved 2 ulps outward;
  * the sha-pinned, unchanged verify_zs.check does the rigorous work: Z sign change at every interval (independent gamma-form
    Z, 160 bits), (R) on every var box, (C) on the first region; every further region is checked by a further call with vars=[]
    (only (C); (R) does not depend on the region) and check_z=False (same intervals, already checked in the first call).
Certificates with mode 'noparity' (S-layer, THEORY_V4 section 10) are checked by the no-parity verifier instead: the same pinned source
with exactly one line changed (candidate charged f * SUM w of the intervals its d = 0 box meets), built in memory below.
Writes one JSON record per (certificate, plain/hardened) to OUT.jsonl."""
import sys, json, hashlib, os, time, math
import numpy as np
VSHA = hashlib.sha256(open('verify_zs5.py', 'rb').read()).hexdigest(); PIN = os.environ.get('VERIFY_ZS5_SHA')
assert PIN and VSHA == PIN, 'verify_zs5.py sha mismatch or VERIFY_ZS5_SHA not set'
sys.path.insert(0, os.getcwd())
import verify_zs5 as verify_zs, types
import model5 as M
from heights import Grid
MEAS = {}
_NP_OLD = "                v=v-K-2*arb(yc)+W\n"; _NP_NEW = "                v=v-K-2*arb(yc)+W-arb(f)*zsub(b0,b1,e0)\n"


def noparity_check():
    """the no-parity verifier (THEORY_V4 section 10): the pinned verify_zs.py source with exactly one line changed, built in memory."""
    src = open('verify_zs5.py').read(); assert hashlib.sha256(src.encode()).hexdigest() == PIN and src.count(_NP_OLD) == 1
    mod = types.ModuleType('verify_zs_noparity'); exec(src.replace(_NP_OLD, _NP_NEW), mod.__dict__); return mod.check


NPCHECK = noparity_check()


def replay(cert_f, harden, c=None, checker=None):
    """production: replay(path, harden).  c / checker are used ONLY by controls4.py (tampered certificate, no-parity verifier)."""
    t0 = time.time(); c = c if c is not None else json.load(open(cert_f))
    mode = c.get('mode', 'main'); assert mode in ('main', 'noparity')
    T0 = c['T0']; assert isinstance(T0, int) and not isinstance(T0, bool) and c['format'] == 'atlas_v5' and c['evaluator'] in ('zeta', 'dirichlet')
    G = Grid(T0, c['grid'])
    checker = checker or (NPCHECK if mode == 'noparity' else verify_zs.check)
    m = M.model(G, T0, c['bins'][0], c['bins'][1], work=False)
    rec = dict(cert=cert_f, hardened=harden, verify_zs5_sha=VSHA, mode=mode, T0=T0, grid=c['grid'], evaluator=c['evaluator'])
    same = dict(vars=[[v[0]] + list(map(float, v[1:])) for v in c['vars']] == [[v[0]] + list(map(float, v[1:])) for v in m['vars']],
                window=list(map(float, c['window'])) == list(map(float, m['window'])), Nwin=float(c['Nwin']) == float(m['Nwin']))
    wl, wh = m['window']
    same['regions_in_window'] = all(wl <= rg[0] < rg[1] <= wh and 0.0 <= rg[2] <= rg[3] <= M.CAP for rg in c['regions'])   # candidate must be a window atom
    rec['model_match'] = same
    ids = c['ids']; wlo, whi = m['window']; Nwin = m['Nwin']
    Elo, Ehi, Fa = [], [], []; bad = []
    for k in ids:
        try: a, t = float(k.split('|')[0]), float(k.split('|')[1]); ok = k == f'{a}|{t!r}' and 0 < a < math.pi
        except ValueError: ok = False
        if not ok: bad.append(k); continue
        mk = (T0, c['evaluator'], k)
        if mk not in MEAS: MEAS[mk] = M.measure(k, T0, c['evaluator'])
        Elo.append(MEAS[mk][0]); Ehi.append(MEAS[mk][1]); Fa.append(M.far_bound5(a, T0, t, wlo, whi))
    rec['rejected_rows'] = bad
    if harden:
        Elo = list(map(float, np.nextafter(np.nextafter(Elo, -np.inf), -np.inf))); Ehi = list(map(float, np.nextafter(np.nextafter(Ehi, np.inf), np.inf)))
        Fa = list(map(float, np.nextafter(np.nextafter(Fa, np.inf), np.inf)))
    rec['rows'] = len(ids)
    rec['finite'] = all(math.isfinite(v) for v in Elo + Ehi + Fa)
    res = []
    if all(same.values()) and rec['finite'] and not bad:
        for ri, rg in enumerate(c['regions']):
            r = checker(ids, Elo, Ehi, Fa, Nwin, m['vars'] if ri == 0 else [], m['window'], rg, c['y'], c['w'], c['zs_intervals'],
                                check_z=(ri == 0), T0=T0)
            res.append(dict(region=rg, **{k: r.get(k) for k in ('status', 'min_candidate_lower', 'boxes', 'sum_w', 'interval', 'box', 'kind', 'value')}))
            if r['status'] != 'CERTIFIED': break
    rec['regions'] = res
    rec['passed'] = bool(res) and len(res) == len(c['regions']) and all(q['status'] == 'CERTIFIED' for q in res)
    rec['min_candidate_lower'] = min([q['min_candidate_lower'] for q in res if q.get('min_candidate_lower') is not None], default=None)
    rec['intervals'] = len(c['zs_intervals']); rec['seconds'] = round(time.time() - t0, 2)
    return rec


if __name__ == '__main__':
    out = open(sys.argv[1], 'a')
    for f in sys.argv[2:]:
        for h in (False, True):
            r = replay(f, h); out.write(json.dumps(r) + '\n'); out.flush()
            print(json.dumps(dict(cert=f, hardened=h, passed=r['passed'], min_candidate_lower=r['min_candidate_lower'], model_match=r['model_match'],
                                  seconds=r['seconds'])), flush=True)
