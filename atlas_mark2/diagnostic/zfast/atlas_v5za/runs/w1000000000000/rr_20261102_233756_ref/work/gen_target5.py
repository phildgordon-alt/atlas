"""atlas_v5 generator for a whole target (NOT trusted) = atlas_v4 lib/gen_target.py with exact heights (THEORY_V5.md section 6):
it works in WORK coordinates of the run grid (grid v4: absolute binary64 exactly as v4; grid v5: offsets from the integer T0), measures
rows / Z at the exact heights (model5, zfun5) with the run evaluator, and writes every certificate in OFFSETS (heights.Grid.to_off, exact).
atlas_v4 docstring follows.
atlas_v4 generator for a whole target (NOT trusted).  Run in the work dir:  gen_target.py RUN_DIR
Reads RUN_DIR/pieces.json; writes RUN_DIR/zs.json (sign changes), RUN_DIR/certs/cert_<piece>.json, appends RUN_DIR/gen.jsonl.
Per piece, escalation (THEORY_V4 section 6; none of it changes what is proved):
  tier 1  sech kernels 1.6, 2.8 at centres every 0.25 over [a - 0.1, b + 0.1]
  tier 2  + kernel 2.2, centres every 0.05
  tier 3  Z re-sampled in the piece's window with step ZS_STEP/5 (more sign changes = more credit), tier-2 rows
  tier 4  split the piece in two at a bin edge (each half from tier 1), down to width MINW
Then the S-layer (THEORY_V4 section 10): per sign-change interval met by a main region, a parity-free certificate on
[t1 - 0.001, t2 + 0.001] x {0} (tiers z1 measured rows within 0.3 -> z2 1.6, 2.8 every 0.05 -> z3 + 2.2 every 0.01 -> z4 finer Z), certs_np/.
TEST HOOKS (path coverage only; recorded in gen.jsonl): V4_TEST_SKIP_TIERS=t1,t2 skips those tiers; V4_TEST_SPLIT=1 makes every piece
wider than 2*MINW skip all tiers once (forces the split path)."""
import sys, os, json, time
sys.path.insert(0, os.getcwd())
os.environ.setdefault('EPS', '')
import model5 as M, zs5 as zs4, gen4
from heights import Grid, H

RUN = sys.argv[1]; P = json.load(open(os.path.join(RUN, 'pieces.json')))
T0 = P['T0']; WMB = P['wm_bins']; ZSTEP = P['zs_step']; MINW = int(os.environ.get('MINW_BINS', '5'))
assert isinstance(T0, int) and P['format'] == 'atlas_v5'
G = Grid(T0, P['grid']); BASE = G.base; EVAL = P['evaluator']; zs4.BASE[0] = BASE; zs4.REFINE = P['zs_refine']


def conv(c):
    """certificate fields from work coordinates to offsets (exact; identity on grid v5)"""
    o = G.to_off
    c = dict(c); c['window'] = [o(v) for v in c['window']]; c['vars'] = [[v[0], o(v[1]), o(v[2]), v[3], v[4]] for v in c['vars']]
    c['regions'] = [[o(r[0]), o(r[1]), r[2], r[3]] for r in c['regions']]; c['zs_intervals'] = [[o(a), o(b)] for a, b in c['zs_intervals']]
    c['ids'] = [f"{k.split('|')[0]}|{o(float(k.split('|')[1]))!r}" for k in c['ids']]
    if 'interval' in c: c['interval'] = [o(v) for v in c['interval']]
    return dict(c, format='atlas_v5', T0=T0, grid=P['grid'], evaluator=EVAL, coordinates='offsets from T0')

os.makedirs(os.path.join(RUN, 'certs'), exist_ok=True)
LOG = open(os.path.join(RUN, 'gen.jsonl'), 'a')


def log(**r):
    r['t'] = round(time.time() - T_START, 2); LOG.write(json.dumps(r) + '\n'); LOG.flush(); print(json.dumps(r)[:300], flush=True)


T_START = time.time(); MEAS = {}; TM = [0.0]


def meas(key):
    if key not in MEAS:
        ts = time.time(); MEAS[key] = M.measure(key, BASE, EVAL); TM[0] += time.time() - ts
    return MEAS[key]


def rows_for(ka, kb, kers, stride_bins):
    out = []
    for a in kers:
        for mm in range(ka - 10, kb + 10):
            if mm % stride_bins: continue
            key = f'{a}|{G.w_centre(mm)!r}'; lo, hi = meas(key); out.append((key, lo, hi))
    return out


# sign changes once for the whole span of all windows
lo_all = G.w_edge(P['hull_bins'][0] - WMB); hi_all = G.w_edge(P['hull_bins'][1] + WMB)
ts = time.time(); st = {}; ZS = zs4.find(lo_all, hi_all, ZSTEP, st)
json.dump(dict(span=[lo_all, hi_all], step=ZSTEP, stats=st, intervals=ZS, coordinates='work', base=BASE,
               intervals_offsets=[[G.to_off(a), G.to_off(b)] for a, b in ZS]), open(os.path.join(RUN, 'zs.json'), 'w'))
log(stage='zs', span=[lo_all, hi_all], seconds=round(time.time() - ts, 2), **st)
ZS_FINE = {}


def window_iv(k0, k1, fine=False):
    wlo, whi = G.w_edge(k0), G.w_edge(k1)
    src = ZS
    if fine:
        key = (k0, k1)
        if key not in ZS_FINE:
            ts = time.time(); s2 = {}; ZS_FINE[key] = zs4.find(wlo, whi, ZSTEP / 5, s2); log(stage='zs_fine', window=[wlo, whi], seconds=round(time.time() - ts, 2), **s2)
        src = ZS_FINE[key]
    return [(t1, t2) for t1, t2 in src if wlo <= t1 and t2 <= whi]


TIERS = [('t1', (1.6, 2.8), 25, False), ('t2', (1.6, 2.2, 2.8), 5, False), ('t3', (1.6, 2.2, 2.8), 5, True)]


SKIP = set(x for x in os.environ.get('V4_TEST_SKIP_TIERS', '').split(',') if x); SPLIT = os.environ.get('V4_TEST_SPLIT') == '1'


def do_piece(ka, kb, name, top=True):
    k0, k1 = ka - WMB, kb + WMB
    for tn, kers, sb, fine in TIERS:
        if tn in SKIP or (SPLIT and top and kb - ka >= 2 * MINW): log(stage='test_hook_skip', piece=name, tier=tn); continue
        ts = time.time(); tm0 = TM[0]
        rows = rows_for(ka, kb, kers, sb); m = M.model(G, BASE, k0, k1, rows); ZIV = window_iv(k0, k1, fine)
        region = [G.w_edge(ka), G.w_edge(kb), 0.0, M.CAP]
        r = gen4.certify(m, [region], ZIV, log=lambda s: None)
        log(stage='attempt', piece=name, bins=[ka, kb], tier=tn, status=r['status'], rows_offered=len(rows), rows_used=len(r.get('ids', [])),
            intervals=len(ZIV), min_candidate_lower=r.get('min_candidate_lower'), rounds=r.get('rounds'), gen_seconds=r.get('gen_seconds'),
            meas_seconds=round(TM[0] - tm0, 2), seconds=round(time.time() - ts, 2))
        if r['status'] == 'CERTIFIED':
            f = os.path.join(RUN, 'certs', f'cert_{name}.json')
            json.dump(conv(dict(r, bins=[k0, k1], piece_bins=[ka, kb], piece=name, tier=tn)), open(f, 'w'))
            return [f]
    if kb - ka >= 2 * MINW:
        km = (ka + kb) // 2
        return do_piece(ka, km, name + 'a', False) + do_piece(km, kb, name + 'b', False)
    log(stage='piece_failed', piece=name, bins=[ka, kb]); return []


done = []
for p in P['pieces']:
    done += do_piece(p['bins'][0], p['bins'][1], p['piece'])
log(stage='main_done', certificates=len(done), measurements=len(MEAS), meas_seconds=round(TM[0], 2))

# S-layer (THEORY_V4 section 10): one parity-free certificate per sign-change interval met by a main region
os.makedirs(os.path.join(RUN, 'certs_np'), exist_ok=True); DEL = 1e-3; ivs = set()
for f in done:
    c = json.load(open(f)); x0, x1 = [G.from_off(v) for v in c['regions'][0][:2]]
    c['zs_intervals'] = [[G.from_off(a), G.from_off(b)] for a, b in c['zs_intervals']]
    ivs |= {(t1, t2) for t1, t2 in c['zs_intervals'] if t1 <= x1 and t2 >= x0}


def near_rows(kz, span):
    return [(k, *v) for k, v in sorted(MEAS.items()) if abs(float(k.split('|')[1]) - G.w_edge(kz)) <= span]


ZT = [('z1', None, 0, False), ('z2', (1.6, 2.8), 5, False), ('z3', (1.6, 2.2, 2.8), 1, False), ('z4', (1.6, 2.2, 2.8), 1, True)]
nnp = 0
for idx, (t1, t2) in enumerate(sorted(ivs)):
    kz = int((t1 - (T0 - BASE)) // H); k0, k1 = kz - WMB, kz + 1 + WMB; region = [t1 - DEL, t2 + DEL, 0.0, 0.0]; ok = False
    for tn, kers, sb, fine in ZT:
        if tn in SKIP: log(stage='test_hook_skip', zero=idx, tier=tn); continue
        ts = time.time(); tm0 = TM[0]
        if kers: rows_for(kz - 5, kz + 6, kers, sb)                         # measure (cached) centres within ~0.15 of the zero
        rows = near_rows(kz, 0.3 if tn == 'z1' else 0.16)
        if not rows: continue
        m = M.model(G, BASE, k0, k1, rows); ZIV = window_iv(k0, k1, fine)
        r = gen4.certify(m, [region], ZIV, log=lambda s: None, noparity=True)
        log(stage='attempt_np', zero=idx, interval=[t1, t2], tier=tn, status=r['status'], rows_offered=len(rows), rows_used=len(r.get('ids', [])),
            min_candidate_lower=r.get('min_candidate_lower'), meas_seconds=round(TM[0] - tm0, 2), seconds=round(time.time() - ts, 2))
        if r['status'] == 'CERTIFIED':
            json.dump(conv(dict(r, bins=[k0, k1], mode='noparity', interval=[t1, t2], tier=tn)), open(os.path.join(RUN, 'certs_np', f'cert_z{idx:04d}.json'), 'w'))
            ok = True; nnp += 1; break
    if not ok: log(stage='np_failed', zero=idx, interval=[t1, t2])
json.dump(MEAS, open(os.path.join(RUN, 'gen_measurements.json'), 'w'))
log(stage='gen_done', certificates=len(done), np_certificates=nnp, np_intervals=len(ivs), measurements=len(MEAS), meas_seconds=round(TM[0], 2))
# atlas_v5z6 (THEORY_V5Z6.md): the Turing grid from THIS process's single zfast session (diagnostic; counted by scan_turing5.py recount)
if os.environ.get('ZFAST_TURING_GRID'):
    import zfast_provider as ZP
    TGS = json.loads(os.environ['ZFAST_TURING_GRID']); ts = time.time()
    tg = ZP.turing_grid(T0, TGS['outdir'], TGS['u0'], TGS['step'], TGS['n'])
    log(stage='turing_grid', spec=TGS, wall=round(time.time() - ts, 2), **tg)
print('DONE', flush=True)
