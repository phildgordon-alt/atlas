"""atlas_v4 generator (NOT trusted): one sign-change LP certificate for a whole piece region [x0,x1] x [d0,d1] (THEORY_V4.md).
Derived from atlas_v3/lib/lslab_zs.py (same LP, same column generation, same cutting-plane exchange, same check()).
Changes (generator only; soundness rests on replay4.py + the sha-pinned verify_zs.check):
  * the region may be any width; Lorentzian rows are laid over [x0-HALF, x1+HALF] (not +-0.2 around a centre);
  * no column capping (one level: the model's caps are the state's caps);  d1 = 0 is allowed (pure simplicity certificate);
  * the sign-change intervals can be passed in (computed once per target, adaptively refined), restricted to the window;
  * sech rows can be dropped (NOSECH=1);  candidate samples on a coarse grid, refined by the exchange;
  * noparity=True (per-zero simplicity certificates without Lemma 2, THEORY_V4 section 10);
  * v4 production: EPS='' (no Lorentzian rows; replay4 rejects them, THEORY_V4 section 2); farL.py in the work dir is a stub.
Used as a module (certify) by run_pieces.py, or CLI:  gen4.py case.json 'x0,x1,d0,d1;x0,x1,d0,d1' out.json [zs.json]"""
import json, sys, os, time, collections, numpy as np
_E = os.environ
_HERE = os.path.dirname(os.path.abspath(__file__))
from farL import far_L
_argv = sys.argv; sys.argv = ['verify.py', '0.003']
exec(open(os.path.join(os.getcwd(), 'verify.py')).read().split("name=sys.argv[2]")[0]); sys.argv = _argv
TAU = float(_E.get('TAU', '1e-4')); TAU_CHECK = 1e-4
EPS = tuple(float(x) for x in _E.get('EPS', '').split(',') if x)
LSTEP = float(_E.get('LSTEP', '0.005')); HALF = float(_E.get('HALF', '0.2')); GUARD = float(_E.get('GUARD_FACTOR', '2'))
REM_STEP = float(_E.get('REM_STEP', '0.005')); RMAX = int(_E.get('RMAX', '6000')); MAX_LP_BYTES = float(_E.get('MAX_LP_BYTES', '2.0e8'))
CSTEP = float(_E.get('CSTEP', '0.002')); CND = int(_E.get('CND', '16'))
NOPARITY = False   # set by certify(noparity=True): (C) at d = 0 charged 2*SUM w of the intervals met (parity-free form, THEORY_V4 section 10)
BOXSTATS = collections.Counter()
PHI_CACHE = {}


def lor(e, t):
    k = (e, t)
    if k not in PHI_CACHE: PHI_CACHE[k] = Phi(e, t)
    return PHI_CACHE[k]


def zsub_box(ZIV, b0, b1, e0, w):
    if e0 > 0: return 0.
    return sum(wi for (t1, t2), wi in zip(ZIV, w) if b0 <= t2 and b1 >= t1)


def check(ZIV, ids, Elo, Ehi, Fa, m, regions, y, w, maxdepth=int(_E.get('MAXDEPTH', '48')), budget=int(_E.get('BOX_BUDGET', '8000000'))):
    """as lslab_zs.check (generator-side, float-guided Arb bisection; returns violations as cuts)."""
    J = len(ids); A, T, isL = kern_np(ids); c = y[:J] - y[J:2 * J]; yc = y[2 * J]
    terms = [(arb(float(c[j])), A[j], T[j], bool(isL[j])) for j in range(J) if abs(c[j]) > 0]
    K = sum(arb(float(y[j])) * (arb(float(Ehi[j])) + (arb(float(Fa[j])) if isL[j] else 0)) - arb(float(y[J + j])) * (arb(float(Elo[j])) - arb(float(Fa[j]))) for j in range(J)) + arb(yc) * (arb(m['Nwin']) - 2)
    KZ = K - sum((arb(float(wi)) for wi in w), arb(0))
    viol = []; boxes = 0; minc = None; BOXSTATS.clear()
    roots = [('rem', lo, hi, 0., 0., 1.) if k == 'on' else ('rem', lo, hi, 0., cap, 2.) for k, lo, hi, _, cap in m['vars']] + [('cand', *rg, 2.) for rg in regions]
    for ri, (kind, x0, x1, d0, d1, f) in enumerate(roots):
        stack = [(x0, x1, d0, d1, 0)]; key = f'{kind}{ri}[{x0:.3f},{x1:.3f}]x[{d0:.4g},{d1:.4g}]'
        while stack:
            b0, b1, e0, e1, dep = stack.pop(); boxes += 1; BOXSTATS[key] += 1
            if boxes > budget: return dict(status='BUDGET', violations=viol, boxes=boxes, top=BOXSTATS.most_common(8))
            v = phi_box(terms, yc, b0, b1, e0, e1, f)
            if kind == 'cand': v = v - KZ - 2 * arb(yc) - (arb(f) * arb(zsub_box(ZIV, b0, b1, e0, w)) if NOPARITY else 0)
            else: v = v - arb(f) * arb(zsub_box(ZIV, b0, b1, e0, w))
            ok = v.lower() > 0 if kind == 'cand' else v.lower() >= 0
            if ok:
                if kind == 'cand': minc = v.lower() if minc is None else min(minc, v.lower())
                continue
            xm, dm = (b0 + b1) / 2, (e0 + e1) / 2
            pv = phi_box(terms, yc, xm, xm, dm, dm, f)
            if kind == 'cand': pv = pv - KZ - 2 * arb(yc) - (arb(f) * arb(zsub_box(ZIV, xm, xm, dm, w)) if NOPARITY else 0)
            else: pv = pv - arb(f) * arb(zsub_box(ZIV, xm, xm, dm, w))
            if (pv.upper() < 0) or (kind == 'cand' and pv.upper() <= 0): viol.append((kind, xm, dm, f)); continue
            if kind == 'rem' and dep >= 24 and pv.upper() < TAU_CHECK * f * 0.5: viol.append((kind, xm, dm, f)); continue
            if dep >= maxdepth: return dict(status='UNRESOLVED_DEPTH', violations=viol, boxes=boxes, box=[kind, b0, b1, e0, e1, v.str(5)])
            if (b1 - b0) >= 4 * (e1 - e0) or e0 == e1: mm = (b0 + b1) / 2; stack += [(b0, mm, e0, e1, dep + 1), (mm, b1, e0, e1, dep + 1)]
            else: mm = (e0 + e1) / 2; stack += [(b0, b1, e0, mm, dep + 1), (b0, b1, mm, e1, dep + 1)]
    return dict(status='CERTIFIED' if not viol else 'VIOLATIONS', violations=viol, boxes=boxes,
                min_candidate_lower=float(minc) if minc is not None else None, top=BOXSTATS.most_common(8))


class MemGuard(Exception): pass


def solve_cg(M, b, Aeq, n, J, nrem, mW):
    K0 = int(_E.get('CG_INIT', '120')); KADD = int(_E.get('CG_ADD', '80')); c = np.r_[np.zeros(n - 1), -1.]
    act = sorted(set(range(2 * J, n)) | set(np.argsort(M[:, :2 * J].min(axis=0))[:K0].tolist()))
    for it in range(200):
        A = M[:, act]
        res = linprog(c[act], A_ub=A, b_ub=b, A_eq=Aeq[:, act], b_eq=[1], bounds=[(None, None) if j == n - 1 else (0, None) for j in act], method='highs')
        if res.status != 0:
            if len(act) >= n: raise RuntimeError(f'LP status {res.status}')
            act = sorted(set(act) | set(range(min(n, len(act) * 2)))); continue
        lu = res.ineqlin.marginals; le = res.eqlin.marginals; red = c - (M.T @ lu) - (Aeq.T @ le)
        red[act] = 0; cand_ = np.where(red < -1e-9)[0]
        if not len(cand_): break
        act = sorted(set(act) | set(cand_[np.argsort(red[cand_])][:KADD].tolist()))
    x = np.zeros(n); x[act] = res.x; slack = (b - M @ x)[:nrem]
    return x[:2 * J + 1], x[2 * J + 1:2 * J + 1 + mW], -res.fun, slack, it + 1, len(act)


def solve(ZIV, ids, Elo, Ehi, Fa, m, rem, cand):
    A, T, isL = kern_np(ids); J = len(ids); mW = len(ZIV); n = 2 * J + 1 + mW + 1; R = len(rem) + len(cand)
    if R * n * 8 > MAX_LP_BYTES: raise MemGuard(f'LP {R}x{n} = {R * n * 8 / 1e9:.2f} GB > cap')
    M = np.zeros((R, n)); b = np.zeros(R); EhiF = np.where(isL, Ehi + Fa, Ehi); i = 0
    for x, d, f in rem:
        u = f * U_np(A, T, isL, x, d); M[i, :J] = -u; M[i, J:2 * J] = u; M[i, 2 * J] = -f; b[i] = -TAU * f
        if d == 0:
            for k, (t1, t2) in enumerate(ZIV):
                if t1 <= x <= t2: M[i, 2 * J + 1 + k] = f
        i += 1
    for x, d in cand:
        u = 2 * U_np(A, T, isL, x, d); M[i, :J] = -(u - EhiF); M[i, J:2 * J] = -(-u + (Elo - Fa)); M[i, 2 * J] = -(2 - (m['Nwin'] - 2) - 2)
        M[i, 2 * J + 1:2 * J + 1 + mW] = -1; M[i, -1] = 1
        if NOPARITY and d == 0:
            for k, (t1, t2) in enumerate(ZIV):
                if t1 <= x <= t2: M[i, 2 * J + 1 + k] += 2
        i += 1
    Aeq = np.zeros((1, n)); Aeq[0, :2 * J + 1] = 1
    return solve_cg(M, b, Aeq, n, J, len(rem), mW)


def rows(m, regions):
    """sech rows of the model (unless NOSECH) + Lorentzian rows L{e}|t over [x0-HALF, x1+HALF]; pole guards as lslab_zs.rows."""
    x0 = min(r[0] for r in regions); x1 = max(r[1] for r in regions)
    if _E.get('NOSECH') == '1': ids, Elo, Ehi, Fa = [], [], [], []
    else: ids = list(m['ids']); Elo = list(m['Elo']); Ehi = list(m['Ehi']); Fa = list(m['F'])
    offs = [(lo, hi, cap) for k, lo, hi, _, cap in m['vars'] if k == 'off' and cap > 0]
    wlo, whi = m['window']
    n0 = int(np.floor((x0 - HALF) / LSTEP)); n1 = int(np.ceil((x1 + HALF) / LSTEP))
    for e in EPS:
        for k in range(n0, n1 + 1):
            t = float(k * LSTEP)                                    # grid on multiples of LSTEP: shared between pieces (cache)
            if not (wlo < t < whi): continue
            if any(lo - 0.003 <= t <= hi + 0.003 and cap >= e / 2 for lo, hi, cap in offs): continue
            if any(r[3] > 0 and r[0] - 0.003 <= t <= r[1] + 0.003 and r[3] * GUARD >= e for r in regions): continue   # pole guard: candidate regions
            lo_, hi_ = lor(e, t); ids.append(f'L{e}|{t!r}'); Elo.append(lo_); Ehi.append(hi_); Fa.append(far_L(e, t, wlo, whi, m['Nwin']))
    return ids, np.array(Elo), np.array(Ehi), np.array(Fa)


def certify(m, regions, ZIV, log=print, noparity=False):
    """one dual (y, w) for all candidate regions (same remainder).  Returns dict(status, ...); on CERTIFIED the certificate fields.
    noparity=True: aim at the parity-free d = 0 condition (verified at replay by the no-parity verifier)."""
    global NOPARITY; NOPARITY = bool(noparity)
    t0 = time.time(); x0 = min(r[0] for r in regions); x1 = max(r[1] for r in regions)
    ids, Elo, Ehi, Fa = rows(m, regions); trows = time.time() - t0
    rem = []
    for k, lo, hi, _, cap in m['vars']:
        for x in np.arange(lo, hi, REM_STEP):
            if k == 'on': rem.append((x, 0., 1.))
            else: rem.extend((x, d, 2.) for d in [0.] + list(np.geomspace(1e-5, cap, 12)))
    cand = []
    for r0, r1, d0, d1 in regions:
        nx = max(3, int((r1 - r0) / CSTEP) + 1)
        dl = [0.] if d1 == 0 else ([0.] + list(np.geomspace(1e-6, d1, CND)) if d0 == 0 else list(np.geomspace(d0, d1, CND)))
        cand += [(x, d) for x in np.linspace(r0, r1, nx) for d in dl]
        if NOPARITY and d0 == 0: cand += [(float(x), 0.) for t1, t2 in ZIV if r0 <= t2 and t1 <= r1 for x in np.linspace(max(t1, r0), min(t2, r1), 3)]
    if len(rem) > RMAX // 4: rem = rem[::-(-len(rem) // (RMAX // 4))]
    NEAR = float(_E.get('NEAR', '0.15')); NST = float(_E.get('NEAR_STEP', '0.001')); NND = int(_E.get('NEAR_ND', '8')); NND_TALL = int(_E.get('NEAR_ND_TALL', '25'))
    rem += [(x, d, 2.) for k, lo, hi, _, cap in m['vars'] if k == 'off' and hi - lo <= 0.05 and lo < x1 + NEAR and hi > x0 - NEAR
            for x in np.arange(lo, hi, NST if cap > 0.01 else 2 * NST) for d in [0.] + list(np.geomspace(1e-5, cap, NND_TALL if cap > 0.01 else NND))]
    zrem = [(float(x), 0., 1.) for t1, t2 in ZIV for x in np.linspace(t1, t2, 5)]
    ncol = 2 * len(ids) + 2 + len(ZIV)
    RM = min(RMAX, int(MAX_LP_BYTES / 8 / ncol))
    if len(rem) + len(cand) + len(zrem) > RM: rem = rem[::-(-len(rem) // max(1, RM - len(cand) - len(zrem)))]
    log(f'ROWS ids {len(ids)} (L {sum(i.startswith("L") for i in ids)}) rowtime {trows:.1f}s LPCAP {RM} cols {ncol} start rows {len(rem) + len(cand) + len(zrem)} intervals {len(ZIV)}')
    slack = np.zeros(0); born = [-99] * len(rem); PROTECT = int(_E.get('PROTECT', '4')); tl = 0.; tc = 0.
    for rnd in range(int(_E.get('ROUNDS', '40'))):
        over = len(rem) + len(cand) + len(zrem) - RM
        if over > 0 and len(slack):
            elig = [i for i in range(len(slack)) if rnd - born[i] > PROTECT]; drop = set(sorted(elig, key=lambda i: -slack[i])[:over])
            keep = [i for i in range(len(rem)) if i not in drop]; rem = [rem[i] for i in keep]; born = [born[i] for i in keep]
        ts = time.time()
        try: y, w, mu, slack, its, nact = solve(ZIV, ids, Elo, Ehi, Fa, m, zrem + rem, cand)
        except MemGuard as e: return dict(status='MEMGUARD', detail=str(e), rounds=rnd)
        except RuntimeError as e: return dict(status='LP_FAIL', detail=str(e), rounds=rnd)
        tl += time.time() - ts
        slack = slack[len(zrem):]
        if mu <= 0: return dict(status='NONPOSITIVE_SAMPLED', sampled=mu, rounds=rnd)
        w = np.maximum(w, 0.); y = np.maximum(y, 0.)
        ts = time.time(); r = check(ZIV, ids, Elo, Ehi, Fa, m, regions, y, w); tc += time.time() - ts
        log(f"ROUND {rnd} rows {len(rem) + len(cand) + len(zrem)} cand {len(cand)} mu {mu:.3g} sum_w {w.sum():.3g} CG {its}/{nact} {r['status']} boxes {r.get('boxes')} viol {len(r['violations'])} "
            f"lp {tl:.1f}s check {tc:.1f}s top {(r.get('top') or [])[:2]}")
        if r['status'] == 'CERTIFIED':
            J = len(ids); act = [j for j in range(J) if y[j] > 0 or y[J + j] > 0]          # emit only rows with a nonzero multiplier
            yo = [float(y[j]) for j in act] + [float(y[J + j]) for j in act] + [float(y[2 * J])]
            return dict(status='CERTIFIED', rounds=rnd, min_candidate_lower=r['min_candidate_lower'], ids=[ids[j] for j in act], y=yo, w=list(map(float, w)),
                        zs_intervals=[list(iv) for iv in ZIV], vars=m['vars'], regions=[list(r) for r in regions], window=m['window'], Nwin=m['Nwin'], sampled_margin=float(mu),
                        gen_seconds=dict(rows=round(trows, 2), lp=round(tl, 2), check=round(tc, 2), total=round(time.time() - t0, 2)), boxes=r['boxes'])
        if not r['violations']: return dict(status=r['status'], box=r.get('box'), rounds=rnd)
        V = r['violations']; CUTS = int(_E.get('CUTS', '1000')); V = V[::-(-len(V) // CUTS)] if len(V) > CUTS else V
        for kind, x, d, f in V: (rem if kind == 'rem' else cand).append((x, d, f) if kind == 'rem' else (x, d))
        born += [rnd] * (len(rem) - len(born))
    return dict(status='EXCHANGE_LIMIT')


def window_intervals(zs, m):
    wlo, whi = m['window']; return [(t1, t2) for t1, t2 in zs if wlo <= t1 and t2 <= whi]


if __name__ == '__main__':
    case, regs, out = sys.argv[1], [[float(v) for v in r.split(',')] for r in sys.argv[2].split(';')], sys.argv[3]
    m = json.load(open(case))['case']['model']
    if len(sys.argv) > 4: zs = json.load(open(sys.argv[4]))['intervals']
    else:
        from zfun import find_sign_changes
        iv, _ = find_sign_changes(*m['window']); zs = [(a, b) for a, b, _, _ in iv]
    ZIV = window_intervals(zs, m)
    r = certify(m, regs, ZIV, log=lambda s: print(s, flush=True))
    print(json.dumps({k: v for k, v in r.items() if k not in ('ids', 'y', 'w', 'zs_intervals', 'vars')}), flush=True)
    if r['status'] == 'CERTIFIED': json.dump(dict(r, case=os.path.abspath(case)), open(out, 'w'))
