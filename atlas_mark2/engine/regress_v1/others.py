"""engine/regress_v1: artin_sweep stored verification (tier 0, PREREG 2.3) and tier-1 regenerations G1, L1, K1 (PREREG 3)."""
import glob, json, os, re
from pathlib import Path
from .common import DIAG, WORK, PY, HERE, RegressError, canon, strip_keys, guarded, env_base

ART = DIAG / 'artin_sweep'
DROP_C1 = re.compile(r'^(t_.*|t|time.*|maxrss.*|src|stream|gs_stats|xcap|old_json|sparse_file|rows_file|local_file|pari_json|wd.*)$')


# PREREG_AMENDMENTS A5 (2026-11-01): PREREG 2.3 registered 2,259 (RESULTS_FINAL.md section 0); Phil-approved correction to 2,256
# (CORRECTION block in diagnostic/artin_sweep/RESULTS_FINAL.md, diagnostic/CORRECTIONS_2026-10-06.md).  As registered: 2259.
EXPECTED_THEOREM_C = 2256

def drop_re(o, rx):
    if isinstance(o, dict): return {k: drop_re(v, rx) for k, v in o.items() if not rx.match(str(k))}
    if isinstance(o, list): return [drop_re(v, rx) for v in o]
    return o


ARTIN_WRAPPER = r'''
import sys, os, builtins
sys.dont_write_bytecode = True
if sys.flags.optimize: raise SystemExit("refusing -O")
OUTDIR = sys.argv[1]; HERE = "%s"
sys.path.insert(0, HERE); os.chdir(HERE)
import verify_sweep_v3 as V3
_open = builtins.open
def red(p, mode="r", *a, **k):
    if any(c in mode for c in "wax+"):
        p = os.path.join(OUTDIR, os.path.basename(p))      # every write goes to engine/ scratch
    return _open(p, mode, *a, **k)
V3.open = red
_exists = os.path.exists
sys.argv = ["verify_sweep_v3.py", "regress_v1"]
V3.main()
''' % str(ART)


def artin_tier0(scratch):
    S = Path(scratch); S.mkdir(parents=True, exist_ok=True); w = S / 'artin_wrapper.py'; w.write_text(ARTIN_WRAPPER)
    g = guarded([PY, '-B', str(w), str(S)], S, S / 'artin_verify.log', timeout=3000)
    fj = S / 'verify_regress_v1.json'
    if g['rc'] != 0 or not fj.exists(): return dict(ok=False, process=g, error='verify_sweep_v3 failed; see log')
    out = json.load(open(fj)); tot = out.pop('_totals')
    not_cert = sorted(k for k, v in out.items() if v.get('status') == 'DONE' and not v.get('theorem_C'))
    res = dict(process=g, totals=tot, theorem_C=tot.get('n_done') and sum(bool(v.get('theorem_C')) for v in out.values()),
               done_not_certified=not_cert, expected_theorem_C=EXPECTED_THEOREM_C, expected_gaps=['5.1.105177.1', '5.1.98385.1'])
    res['ok'] = bool(res['theorem_C'] == EXPECTED_THEOREM_C and not_cert == res['expected_gaps'])
    res['golden'] = {k: dict(status=v.get('status'), theorem_C=v.get('theorem_C'), margins=v.get('margins')) for k, v in out.items()}
    return res


def _cmp_files(new_files, ref_dir, rx, rename=lambda n: n):
    rep = {}
    for f in new_files:
        n = Path(f).name; ref = Path(ref_dir) / rename(n)
        if not ref.exists(): rep[n] = 'no reference'; continue
        a = canon(drop_re(json.load(open(f)), rx)); b = canon(drop_re(json.load(open(ref)), rx))
        rep[n] = (a == b)
    return rep


def g1(scratch):
    """geval_c field run 5.1.22352.1 via the review runner (output root redirected to scratch)."""
    S = Path(scratch); S.mkdir(parents=True, exist_ok=True); GC = DIAG / 'geval_c'
    g = guarded([PY, '-B', str(GC / 'review' / 'rcert.py'), str(S / 'out'), '5.1.22352.1', '--tag', '_V8'], GC, S / 'g1.log',
                env=env_base(OMP_NUM_THREADS='1'), timeout=1800)
    new = sorted(glob.glob(str(S / 'out' / 'runs' / 'cert' / '*.json')))
    base = lambda n: re.sub(r'(_V8)?(\.r\d+)?\.json$', '.json', n)
    r2 = lambda n: re.sub(r'(_V8)?(\.r\d+)?\.json$', '.r2.json', n)
    a = _cmp_files(new, GC / 'runs' / 'cert', DROP_C1, r2); b = _cmp_files(new, GC / 'runs' / 'cert', DROP_C1, base)
    ok = len(new) == 4 * 1 and all(v is True for v in a.values()) and all(v is True for v in b.values())
    # PREREG says "all 8 files": 8 = 4 certificates x {V8 scored .r2, base}; the runner writes 4 certificate files.
    return dict(id='G1 geval_c 5.1.22352.1', process=g, new_files=[Path(x).name for x in new], vs_scored_r2=a, vs_base=b, ok=bool(ok))


def l1(scratch):
    S = Path(scratch); S.mkdir(parents=True, exist_ok=True); L = DIAG / 'level1'
    g = guarded([PY, '-B', str(L / 'run_weight.py'), '12', 'gen', str(S / 'out')], L, S / 'l1.log', timeout=900)
    rx = re.compile(r'^(t_.*|t_exact|t_total|maxrss_MB|maxrss.*)$')
    new = sorted(glob.glob(str(S / 'out' / '*.json')))
    rep = _cmp_files(new, L / 'runs' / 'A_gen', rx)
    return dict(id='L1 level1 k=12 gen', process=g, compared=rep, ok=bool(new and all(v is True for v in rep.values())))


def k1(scratch):
    S = Path(scratch); S.mkdir(parents=True, exist_ok=True); K = DIAG / 'flagship_K23'
    out = S / 'w_2640'
    g = guarded([PY, '-u', '-B', str(K / 'gen_cert.py'), 'K23', '2640', '2650', str(out), '--intervals', 'iv.json'], K, S / 'k1.log', timeout=1200)
    rx = re.compile(r'^(seconds|t_.*|time.*|t)$')
    ref = K / 'runs' / 'w_2640'
    cells = _cmp_files(sorted(glob.glob(str(out / 'certs' / '*.json'))), ref / 'certs', rx)
    other = _cmp_files([str(out / f) for f in ('intervals.json', 'gen_summary.json', 'rows.json') if (out / f).exists()], ref, rx)
    n_ref = len(glob.glob(str(ref / 'certs' / '*.json')))
    ok = len(cells) == n_ref and all(v is True for v in cells.values()) and other.get('intervals.json') is True
    return dict(id='K1 flagship_K23 w_2640', process=g, cells=f"{sum(v is True for v in cells.values())}/{n_ref}",
                differing=[k for k, v in {**cells, **other}.items() if v is not True], other=other, ok=bool(ok))
