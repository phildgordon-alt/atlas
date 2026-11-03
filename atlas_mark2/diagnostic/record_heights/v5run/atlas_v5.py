#!/usr/bin/env python
"""atlas_v5 -- atlas_v4 with exact heights (THEORY_V5.md): every height is an integer T0 plus a binary64 offset.

  atlas_v5.py T0 tlo thi --name NAME [--grid v5|v4] [--evaluator dirichlet|zeta] [--pw 1.0] [--wm 2.0] [--zs-step 0.005]
              [--zs-refine 1e-4] [--gen-timeout 7200]
T0: decimal integer.  tlo, thi: ABSOLUTE target heights as decimal strings.  grid v5: target offsets = exact (tlo - T0), rounded
outward to binary64 if not exact (recorded).  grid v4 (compatibility with atlas_v4 runs): tlo, thi parsed as binary64 exactly as v4 did
(float(tlo)), offsets = float(tlo) - T0 exactly.  atlas_v4 docstring follows (atlas_v4 -> atlas_v5, replay_target4 -> replay_target5).

T0 only fixes the bin grid e(k) = T0 + k*0.01 (no band, no ledgers).  Stages:
  1 pieces       hull = smallest run of bins containing [tlo, thi]; pieces of at most PW; window = piece +- WM      (this process)
  2 generator    lib/gen_target.py in a fresh process (2.5 GB watchdog): sign changes once, then one all-open sech-row LP
                 certificate per piece, region piece x [0, 1/2]                                                       (NOT trusted)
  3 replay       replay_target4.py in a fresh process: rebuilds every model and row, sha-pinned verify_zs plain + hardened,
                 exact tiling of hull/target x [0, 1/2] and the d = 0 line                                         (no generator code)
Output runs/w{T0}/{NAME}/: pieces.json, zs.json, certs/, gen.jsonl, replay_check/, summary.json, drive.jsonl.  Exit 0 iff closed."""
import argparse, json, os, re, shutil, subprocess, sys, time, hashlib, math
from pathlib import Path

V4 = Path(__file__).resolve().parent
sys.path.insert(0, str(V4 / 'lib'))
from fractions import Fraction
from heights import Grid
PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
VERIFY_ZS5_SHA = open(V4 / 'VERIFY_ZS5.sha256').read().split()[0]
GEN_LIB = ('gen_target5.py', 'gen4.py', 'model5.py', 'sech5.py', 'heights.py', 'zs5.py', 'zfun5.py', 'verify.py', 'lp.py')
LIM_GB = float(os.environ.get('V4_LIM_GB', '2.5')); H = 0.01


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def footprint_gb(pid):
    try: o = subprocess.run(['footprint', '-p', str(pid)], capture_output=True, text=True, timeout=20).stdout
    except Exception: return 0.
    m = re.search(r'phys_footprint:\s*([\d.]+)\s*(KB|MB|GB)', o)
    return float(m.group(1)) * {'KB': 1e-6, 'MB': 1e-3, 'GB': 1}[m.group(2)] if m else 0.


def rss_gb(pid):
    try: return int(subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True).stdout.strip() or 0) / 1e6
    except Exception: return 0.


def guarded(cmd, cwd, log, env=None, timeout=None, lim=None):
    """fresh process (nice 19); killed if RSS or phys_footprint > lim GB or wall time > timeout."""
    lim = lim or LIM_GB; t0 = time.time(); peak = 0.; killed = None; n = 0
    with open(log, 'a') as f:
        p = subprocess.Popen(['nice', '-n', '19'] + cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT)
        while p.poll() is None:
            g = rss_gb(p.pid)
            if n % 4 == 0: g = max(g, footprint_gb(p.pid))
            peak = max(peak, g); n += 1
            if g > lim: p.kill(); killed = 'memory'; break
            if timeout and time.time() - t0 > timeout: p.kill(); killed = 'timeout'; break
            time.sleep(0.25)
        p.wait()
    return dict(rc=p.returncode, killed=killed, peak_gb=round(peak, 3), seconds=round(time.time() - t0, 2))


def hull_bins(G, ulo, uhi):
    """v4's hull_bins in offsets (exact translation of v4's comparisons)"""
    e = G.edge
    k_lo = math.floor(ulo / H + 1e-6); k_hi = math.ceil(uhi / H - 1e-6)
    while e(k_lo) > ulo: k_lo -= 1
    while e(k_hi) < uhi: k_hi += 1
    return k_lo, k_hi


def target_offsets(T0, tlo, thi, grid):
    """(ulo, uhi, note): offsets of the claimed target; v4 grid: binary64 absolute values as v4; v5 grid: exact decimals, outward if needed"""
    if grid == 'v4':
        from heights import as_float_exact
        return as_float_exact(Fraction(float(tlo)) - T0), as_float_exact(Fraction(float(thi)) - T0), 'binary64 absolute target (atlas_v4 convention)'
    lo, hi = Fraction(tlo) - T0, Fraction(thi) - T0
    ulo, uhi = float(lo), float(hi)
    if Fraction(ulo) > lo: ulo = math.nextafter(ulo, -math.inf)
    if Fraction(uhi) < hi: uhi = math.nextafter(uhi, math.inf)
    return ulo, uhi, ('exact' if (Fraction(ulo), Fraction(uhi)) == (lo, hi) else 'rounded outward to binary64 offsets')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('T0', type=int); ap.add_argument('tlo'); ap.add_argument('thi')
    ap.add_argument('--grid', choices=('v5', 'v4'), default='v5'); ap.add_argument('--evaluator', choices=('dirichlet', 'zeta'), default='dirichlet')
    ap.add_argument('--zs-refine', type=float, default=1e-4)
    ap.add_argument('--name', required=True); ap.add_argument('--pw', type=float, default=1.0); ap.add_argument('--wm', type=float, default=2.0)
    ap.add_argument('--zs-step', type=float, default=0.005); ap.add_argument('--gen-timeout', type=float, default=7200)
    a = ap.parse_args(); t_start = time.time()
    RUN = V4 / 'runs' / (f'w{a.T0:.2f}' if a.grid == 'v4' else f'w{a.T0}') / a.name; RUN.mkdir(parents=True, exist_ok=True); W = RUN / 'work'; W.mkdir(exist_ok=True)
    DJ = open(RUN / 'drive.jsonl', 'a')
    def log(**r):
        r['t'] = round(time.time() - t_start, 2); DJ.write(json.dumps(r) + '\n'); DJ.flush(); print(json.dumps(r)[:300], flush=True)
    log(stage='start', args=vars(a), lim_gb=LIM_GB, lib_sha={f: sha(V4 / 'lib' / f) for f in GEN_LIB + ('verify_zs5.py', 'replay5.py')},
        driver_sha=sha(__file__), replay_target_sha=sha(V4 / 'replay_target5.py'))
    assert sha(V4 / 'lib' / 'verify_zs5.py') == VERIFY_ZS5_SHA
    # 1 pieces
    G = Grid(a.T0, a.grid); ulo, uhi, tnote = target_offsets(a.T0, a.tlo, a.thi, a.grid)
    k_lo, k_hi = hull_bins(G, ulo, uhi); e = G.edge
    pwb = max(1, round(a.pw / H)); n = -(-(k_hi - k_lo) // pwb); cuts = [k_lo + round((k_hi - k_lo) * j / n) for j in range(n + 1)]
    pieces = [dict(piece=f'p{p0}_{p1}', bins=[p0, p1], col=[e(p0), e(p1)]) for p0, p1 in zip(cuts, cuts[1:])]
    PJ = dict(format='atlas_v5', T0=a.T0, grid=a.grid, evaluator=a.evaluator, coordinates='offsets from T0', target_input=[a.tlo, a.thi],
              target=[ulo, uhi], target_note=tnote, hull=[e(k_lo), e(k_hi)], hull_bins=[k_lo, k_hi], pw=a.pw, wm=a.wm, wm_bins=round(a.wm / H),
              zs_step=a.zs_step, zs_refine=a.zs_refine, pieces=pieces)
    if not (RUN / 'pieces.json').exists(): json.dump(PJ, open(RUN / 'pieces.json', 'w'), indent=1)
    else: assert json.load(open(RUN / 'pieces.json')) == json.loads(json.dumps(PJ)), 'run dir has different pieces'
    log(stage='pieces', hull=PJ['hull'], n=len(pieces))
    # 2 generator
    for f in GEN_LIB: shutil.copy(V4 / 'lib' / f, W / f)
    (W / 'farL.py').write_text('def far_L(*a, **k):\n    raise RuntimeError("Lorentzian rows are disabled in atlas_v4/v5 (THEORY_V4 section 2)")\n')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', EPS='', CSTEP=os.environ.get('CSTEP', '0.005'), CND=os.environ.get('CND', '10'))
    done = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))
    if not done:
        shutil.rmtree(RUN / 'certs', ignore_errors=True)
        for f in ('gen.jsonl', 'gen.log', 'zs.json'): (RUN / f).unlink(missing_ok=True)
        g = guarded([PY, '-u', '-B', 'gen_target5.py', str(RUN)], W, RUN / 'gen.log', env=env, timeout=a.gen_timeout)
    else: g = dict(resumed=True)
    log(stage='generator', **g)
    # 3 replay (independent; no generator code)
    r = guarded([PY, '-u', '-B', str(V4 / 'replay_target5.py'), str(RUN)], V4, RUN / 'replay_target.log', env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    log(stage='replay_target', **r)
    rc = json.load(open(RUN / 'replay_check' / 'replay_check.json')) if (RUN / 'replay_check' / 'replay_check.json').exists() else {}
    gl = [json.loads(l) for l in open(RUN / 'gen.jsonl')] if (RUN / 'gen.jsonl').exists() else []
    gd = next((x for x in gl if x['stage'] == 'gen_done'), {}); zs = next((x for x in gl if x['stage'] == 'zs'), {}); md = next((x for x in gl if x['stage'] == 'main_done'), {})
    att = [x for x in gl if x['stage'] == 'attempt']
    summ = dict(T0=a.T0, grid=a.grid, evaluator=a.evaluator, target_input=[a.tlo, a.thi], target=PJ['target'], target_note=tnote, name=a.name, hull=PJ['hull'],
                hull_exact=[str(Fraction(a.T0) + Fraction(PJ['hull'][0])), str(Fraction(a.T0) + Fraction(PJ['hull'][1]))], pieces=len(pieces),
                test_hooks={k: os.environ[k] for k in ('V4_TEST_SKIP_TIERS', 'V4_TEST_SPLIT') if os.environ.get(k)},
                certificates=rc.get('certificates'), replay_passed_plain_and_hardened=rc.get('passed_both'),
                tiling=rc.get('tiling'), all_closed=bool(rc.get('passed')),
                simple_without_lemma2=bool(rc.get('passed_B')), claim_B=rc.get('claim_B'),
                generator=dict(seconds=g.get('seconds'), peak_gb=g.get('peak_gb'), killed=g.get('killed'), zs_seconds=zs.get('seconds'),
                               zs_intervals=zs.get('intervals'), zs_evals=zs.get('evals'), measurements=gd.get('measurements'),
                               meas_seconds=gd.get('meas_seconds'), attempts=len(att), tiers=[(x['piece'], x['tier'], x['status']) for x in att],
                               main_done_at=md.get('t'), np_certificates=gd.get('np_certificates'), np_intervals=gd.get('np_intervals'),
                               np_tiers=[(x['zero'], x['tier'], x['status']) for x in gl if x['stage'] == 'attempt_np']),
                replay=dict(seconds=r['seconds'], peak_gb=r['peak_gb'], min_candidate_lower=rc.get('min_candidate_lower')),
                wall_seconds=round(time.time() - t_start, 2), peak_gb=max(g.get('peak_gb') or 0, r['peak_gb'], (rc.get('replay_process') or {}).get('peak_gb') or 0),
                claim=('PASSED (A): every zero of zeta with height in the hull lies on the critical line and is simple (trust base: README.md; '
                       'simplicity via Lemma 2)') if rc.get('passed') else 'NOT CLOSED: see replay_check/replay_check.json',
                claim_simple_without_lemma2=('PASSED (B): simplicity also holds without Lemma 2 (S-layer, THEORY_V4 section 10)' if rc.get('passed_B')
                                             else 'claim (B) not established'))
    json.dump(summ, open(RUN / 'summary.json', 'w'), indent=1)
    log(stage='done', all_closed=summ['all_closed'], wall_seconds=summ['wall_seconds'], peak_gb=summ['peak_gb'])
    sys.exit(0 if summ['all_closed'] else 1)


if __name__ == '__main__':
    main()
