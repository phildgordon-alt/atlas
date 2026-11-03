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
Output runs/w{T0}/{NAME}/: pieces.json, zs.json, certs/, gen.jsonl, replay_check/, summary.json, drive.jsonl.  Exit 0 iff closed.

atlas_v5z5 (THEORY_V5Z5.md): the zfast session is configured explicitly and recorded.  pieces.json gets `zfast_session` (mode, centre,
H, Delta, K, J, strict, generator threads); drive.jsonl's start record gets `env` (every variable that can change an output).
  legacy (default): v5z4 behaviour exactly (H 4, Delta 0.15, K 18, J 12; centre from env ZFAST_CENTER as before; ZFAST_H/DELTA/K/J/STRICT
                    are removed from the child env);
  --wide          : one strict session for the whole run: centre = midpoint of the Z span (or --zfast-center), --zfast-h/--zfast-delta
                    explicit; the span (+0.02) must lie inside [centre - H, centre + H] before anything is computed.

atlas_v5z6 (THEORY_V5Z6.md, RESULTS_M9): libzfast.v14 (sessions bit-identical to v13b at equal decomposition D = zfast_session.threads),
  ZFAST_WORKERS OS threads (output-free; recorded), per-role checkpoints in wide mode (RUN/zfast_ckpt_gen.txt, RUN/zfast_ckpt_replay.txt;
  the replay never reads the generator's), the replay's D from pieces.json;
  --turing-grid : the generator's session also covers [lo - 40, hi + 40] and saves the scan_turing5 grid in RUN/turing_grid (diagnostic);
  --resume      : continue a run whose generator (or replay) died while its session was being built: only while zs.json does not exist
                  and certs/ is empty (resp. replay_check/replay_check.json does not exist); earlier logs/dirs are RENAMED *.attemptN
                  (never deleted); the session resumes from its checkpoint, bit-identically.
  The replay of record is the driver's stage 3 (a fresh process, replay_target5.py byte copy); v5z6 runs no second replay.
atlas_v5z7 (RESULTS_M9 F-M9b, F-M9c): W not in pieces.json; no replay unless the generator finished; --resume reuses only a passed replay."""
import argparse, json, os, re, shutil, subprocess, sys, time, hashlib, math, platform
from pathlib import Path
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('atlas_v5z7: refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule)')

V4 = Path(__file__).resolve().parent
sys.path.insert(0, str(V4 / 'lib'))
from fractions import Fraction
from heights import Grid
PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
VERIFY_ZS5_SHA = open(V4 / 'VERIFY_ZS5.sha256').read().split()[0]
GEN_LIB = ('gen_target5.py', 'gen4.py', 'model5.py', 'sech5.py', 'heights.py', 'zs5.py', 'zfun5.py', 'verify.py', 'lp.py', 'zfast_provider.py')
LIM_GB = float(os.environ.get('V4_LIM_GB', '2.5')); H = 0.01
Z_PROVIDER = 'zfast libzfast.v14 (= v13b bit-identically at equal D), provider v5z6 (THEORY_V5Z6); model5 fixed-precision N_win (v5z4)'
ENV_KEYS = ('ZFAST_CENTER', 'ZFAST_THREADS', 'ZFAST_H', 'ZFAST_DELTA', 'ZFAST_K', 'ZFAST_J', 'ZFAST_STRICT', 'CSTEP', 'CND', 'MINW_BINS',
            'ZS_REFINE', 'ZS_DIP', 'EPS', 'V4_LIM_GB', 'V4_TEST_SKIP_TIERS', 'V4_TEST_SPLIT', 'SECH_TABLE', 'OMP_NUM_THREADS',
            'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'PYTHONHASHSEED', 'ZFAST_WORKERS', 'ZFAST_CKPT', 'ZFAST_TURING_GRID',
            'ZFAST14_GENERIC_KERNEL', 'ZFAST14_TEST_EXIT_AFTER')
SESSION_KEYS = ('ZFAST_CENTER', 'ZFAST_H', 'ZFAST_DELTA', 'ZFAST_K', 'ZFAST_J', 'ZFAST_STRICT')
LEGACY = dict(H=4.0, Delta=0.15, K=18, J=12)


def env_record(env):
    import flint
    return dict({k: env.get(k) for k in ENV_KEYS}, python=sys.version.split()[0], flint=getattr(flint, '__version__', None),
                platform=platform.platform(), executable=sys.executable)


def session_env(zs):
    """child-process env entries for a zfast_session record (pieces.json)."""
    e = {'ZFAST_H': repr(zs['H']), 'ZFAST_DELTA': repr(zs['Delta']), 'ZFAST_K': str(zs['K']), 'ZFAST_J': str(zs['J']),
         'ZFAST_STRICT': '1' if zs['strict'] else '0', 'ZFAST_THREADS': str(zs['threads'])}      # v5z6: D from the record
    if zs['center'] is not None: e['ZFAST_CENTER'] = zs['center']
    return e


def child_env(base, zs, **extra):
    e = dict(base)
    for k in SESSION_KEYS: e.pop(k, None)
    e.update(session_env(zs)); e.update(extra)
    return e


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
    ap.add_argument('--wide', action='store_true'); ap.add_argument('--zfast-center', type=float); ap.add_argument('--zfast-h', type=float)
    ap.add_argument('--zfast-delta', type=float); ap.add_argument('--zfast-k', type=int, default=18); ap.add_argument('--zfast-j', type=int, default=12)
    ap.add_argument('--turing-grid', action='store_true'); ap.add_argument('--resume', action='store_true')
    a = ap.parse_args(); t_start = time.time()
    for k in ('ZFAST_CKPT', 'ZFAST_TURING_GRID'): os.environ.pop(k, None)      # v5z6: role-specific, set below per child only
    if a.turing_grid and not a.wide: raise SystemExit('--turing-grid needs --wide')
    if not a.wide and any(v is not None for v in (a.zfast_center, a.zfast_h, a.zfast_delta)):
        raise SystemExit('--zfast-center/--zfast-h/--zfast-delta need --wide (legacy mode is v5z4 exactly)')
    if a.wide and (a.zfast_h is None or a.zfast_delta is None): raise SystemExit('--wide needs explicit --zfast-h and --zfast-delta')
    RUN = V4 / 'runs' / (f'w{a.T0:.2f}' if a.grid == 'v4' else f'w{a.T0}') / a.name; RUN.mkdir(parents=True, exist_ok=True); W = RUN / 'work'; W.mkdir(exist_ok=True)
    DJ = open(RUN / 'drive.jsonl', 'a')
    def log(**r):
        r['t'] = round(time.time() - t_start, 2); DJ.write(json.dumps(r) + '\n'); DJ.flush(); print(json.dumps(r)[:300], flush=True)
    # 1 pieces (computed before the start record so that the session record can be logged and checked first)
    G = Grid(a.T0, a.grid); ulo, uhi, tnote = target_offsets(a.T0, a.tlo, a.thi, a.grid)
    k_lo, k_hi = hull_bins(G, ulo, uhi); e = G.edge
    wmb = round(a.wm / H); span = [e(k_lo - wmb), e(k_hi + wmb)]
    gen_threads = int(os.environ.get('ZFAST_THREADS', '2'))
    if a.wide:
        c = a.zfast_center if a.zfast_center is not None else (span[0] + span[1]) / 2
        if not (c - a.zfast_h <= span[0] - 0.02 and span[1] + 0.02 <= c + a.zfast_h):
            raise SystemExit(f'--wide: Z span {span} (+0.02) is not inside the session [{c} - {a.zfast_h}, {c} + {a.zfast_h}]')
        ZSESS = dict(mode='wide', center=repr(float(c)), H=float(a.zfast_h), Delta=float(a.zfast_delta), K=a.zfast_k, J=a.zfast_j, strict=True,
                     threads=gen_threads, z_span=span)
        ZSESS.update(lib='v14')        # v5z7 (F-M9b): W is output-free and recorded only in drive.jsonl (env ZFAST_WORKERS)
        if a.turing_grid:
            TG = dict(u0=float(ulo) - 40.0, step=0.004, n=int(round((float(uhi) - float(ulo) + 80.0) / 0.004)) + 1)
            gend = TG['u0'] + (TG['n'] - 1) * TG['step']
            if not (c - a.zfast_h <= TG['u0'] and gend <= c + a.zfast_h):
                raise SystemExit(f'--turing-grid: grid [{TG["u0"]}, {gend}] is not inside the session [{c} - {a.zfast_h}, {c} + {a.zfast_h}]')
            ZSESS['turing_grid'] = TG
    else:
        ZSESS = dict(mode='legacy', center=os.environ.get('ZFAST_CENTER'), strict=False, threads=gen_threads, z_span=span, **LEGACY)
    log(stage='start', args=vars(a), lim_gb=LIM_GB, lib_sha={f: sha(V4 / 'lib' / f) for f in GEN_LIB + ('verify_zs5.py', 'replay5.py')},
        driver_sha=sha(__file__), replay_target_sha=sha(V4 / 'replay_target5.py'), env=env_record(os.environ), zfast_session=ZSESS)
    if sha(V4 / 'lib' / 'verify_zs5.py') != VERIFY_ZS5_SHA: raise RuntimeError('verify_zs5.py sha mismatch')
    pwb = max(1, round(a.pw / H)); n = -(-(k_hi - k_lo) // pwb); cuts = [k_lo + round((k_hi - k_lo) * j / n) for j in range(n + 1)]
    pieces = [dict(piece=f'p{p0}_{p1}', bins=[p0, p1], col=[e(p0), e(p1)]) for p0, p1 in zip(cuts, cuts[1:])]
    PJ = dict(format='atlas_v5', T0=a.T0, grid=a.grid, evaluator=a.evaluator, coordinates='offsets from T0', target_input=[a.tlo, a.thi],
              target=[ulo, uhi], target_note=tnote, hull=[e(k_lo), e(k_hi)], hull_bins=[k_lo, k_hi], pw=a.pw, wm=a.wm, wm_bins=round(a.wm / H),
              zs_step=a.zs_step, zs_refine=a.zs_refine, pieces=pieces, z_provider=Z_PROVIDER, zfast_session=ZSESS)
    if not (RUN / 'pieces.json').exists(): json.dump(PJ, open(RUN / 'pieces.json', 'w'), indent=1)
    elif json.load(open(RUN / 'pieces.json')) != json.loads(json.dumps(PJ)): raise RuntimeError('run dir has different pieces')
    log(stage='pieces', hull=PJ['hull'], n=len(pieces))
    # 2 generator
    for f in GEN_LIB:
        if not (W / f).exists(): shutil.copy(V4 / 'lib' / f, W / f)
        elif sha(W / f) != sha(V4 / 'lib' / f): raise RuntimeError(f'work copy {f} differs from lib')
    if not (W / 'farL.py').exists(): (W / 'farL.py').write_text('def far_L(*a, **k):\n    raise RuntimeError("Lorentzian rows are disabled in atlas_v4/v5 (THEORY_V4 section 2)")\n')
    v6 = {}
    if a.wide:
        v6['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_gen.txt')
        if ZSESS.get('turing_grid'): v6['ZFAST_TURING_GRID'] = json.dumps(dict(ZSESS['turing_grid'], outdir=str(RUN / 'turing_grid')))
    env = child_env(os.environ, ZSESS, PYTHONDONTWRITEBYTECODE='1', EPS='', CSTEP=os.environ.get('CSTEP', '0.005'), CND=os.environ.get('CND', '10'), **v6)
    done = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))
    if not done:
        if any((RUN / f).exists() for f in ('certs', 'gen.jsonl', 'gen.log', 'zs.json')):
            if not (a.resume and a.wide and not (RUN / 'zs.json').exists() and not (RUN / 'turing_grid').exists()
                    and not any((RUN / 'certs').glob('*')) and not (RUN / 'certs_np').exists()):
                raise RuntimeError('v5z never deletes: use a fresh --name (--resume only while the generator session is being built)')
            k = 1
            while any((RUN / f'{f}.attempt{k}').exists() for f in ('gen.log', 'gen.jsonl')): k += 1
            for f in ('gen.log', 'gen.jsonl'):
                if (RUN / f).exists(): (RUN / f).rename(RUN / f'{f}.attempt{k}')
            log(stage='resume_generator', attempt=k, ckpt=v6.get('ZFAST_CKPT'))
        g = guarded([PY, '-u', '-B', 'gen_target5.py', str(RUN)], W, RUN / 'gen.log', env=env, timeout=a.gen_timeout)
    else: g = dict(resumed=True)
    log(stage='generator', **g)
    # 3 replay (independent; no generator code)
    renv = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if a.wide: renv['ZFAST_CKPT'] = str(RUN / 'zfast_ckpt_replay.txt')         # the replay's own checkpoint, never the generator's
    gen_ok = (RUN / 'gen.jsonl').exists() and any(json.loads(l).get('stage') == 'gen_done' for l in open(RUN / 'gen.jsonl'))
    rprev = json.load(open(RUN / 'replay_check' / 'replay_check.json')) if (RUN / 'replay_check' / 'replay_check.json').exists() else None
    if not gen_ok: r = dict(skipped='generator did not finish (v5z7, F-M9c): no replay', seconds=None, peak_gb=0)
    elif a.resume and rprev is not None and rprev.get('passed') is True: r = dict(resumed=True, seconds=None, peak_gb=0)
    else:
        if (RUN / 'replay_check').exists():
            if not a.resume: raise RuntimeError('replay_check exists: use --resume (v5z never deletes)')
            k = 1
            while (RUN / f'replay_check.attempt{k}').exists(): k += 1
            (RUN / 'replay_check').rename(RUN / f'replay_check.attempt{k}')
            if (RUN / 'replay_target.log').exists(): (RUN / 'replay_target.log').rename(RUN / f'replay_target.log.attempt{k}')
            log(stage='resume_replay', attempt=k, ckpt=renv.get('ZFAST_CKPT'))
        r = guarded([PY, '-u', '-B', str(V4 / 'replay_target5.py'), str(RUN)], V4, RUN / 'replay_target.log', env=renv)
    log(stage='replay_target', **r)
    rc = json.load(open(RUN / 'replay_check' / 'replay_check.json')) if (RUN / 'replay_check' / 'replay_check.json').exists() else {}
    gl = [json.loads(l) for l in open(RUN / 'gen.jsonl')] if (RUN / 'gen.jsonl').exists() else []
    gd = next((x for x in gl if x['stage'] == 'gen_done'), {}); zs = next((x for x in gl if x['stage'] == 'zs'), {}); md = next((x for x in gl if x['stage'] == 'main_done'), {})
    att = [x for x in gl if x['stage'] == 'attempt']
    summ = dict(T0=a.T0, grid=a.grid, evaluator=a.evaluator, target_input=[a.tlo, a.thi], target=PJ['target'], target_note=tnote, name=a.name, hull=PJ['hull'],
                hull_exact=[str(Fraction(a.T0) + Fraction(PJ['hull'][0])), str(Fraction(a.T0) + Fraction(PJ['hull'][1]))], pieces=len(pieces),
                test_hooks={k: os.environ[k] for k in ('V4_TEST_SKIP_TIERS', 'V4_TEST_SPLIT') if os.environ.get(k)}, zfast_session=ZSESS,
                certificates=rc.get('certificates'), replay_passed_plain_and_hardened=rc.get('passed_both'),
                tiling=rc.get('tiling'), all_closed=bool(rc.get('passed')),
                simple_without_lemma2=bool(rc.get('passed_B')), claim_B=rc.get('claim_B'),
                generator=dict(seconds=g.get('seconds'), peak_gb=g.get('peak_gb'), killed=g.get('killed'), zs_seconds=zs.get('seconds'),
                               zs_intervals=zs.get('intervals'), zs_evals=zs.get('evals'), measurements=gd.get('measurements'),
                               meas_seconds=gd.get('meas_seconds'), attempts=len(att), tiers=[(x['piece'], x['tier'], x['status']) for x in att],
                               main_done_at=md.get('t'), np_certificates=gd.get('np_certificates'), np_intervals=gd.get('np_intervals'),
                               np_tiers=[(x['zero'], x['tier'], x['status']) for x in gl if x['stage'] == 'attempt_np']),
                replay=dict(seconds=r['seconds'], peak_gb=r['peak_gb'], min_candidate_lower=rc.get('min_candidate_lower')),
                sessions_per_window=2 if a.wide else None, turing_grid=next((x for x in gl if x['stage'] == 'turing_grid'), None),
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
