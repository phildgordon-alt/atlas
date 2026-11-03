"""engine/regress_v1 integrity layer (PREREG 2.1a, 2.4): FROZEN.json snapshot + re-check of every historical sha manifest."""
import glob, json, os, re, time
from pathlib import Path
from .common import DIAG, ROOT, HERE, RegressError, sha256
from . import zfast

FROZEN = HERE / 'FROZEN.json'
FAMILY_GLOBS = {
    'flagship_K23': ['flagship_K23/runs/w_*/certs/*.json', 'flagship_K23/runs/w_*/*.json'],
    'flagship_K23_ext': ['flagship_K23_ext/runs/w_*/certs/*.json', 'flagship_K23_ext/runs/w_*/*.json'],
    'geval_c': ['geval_c/runs/cert/*.json', 'geval_c/runs/field/*.json', 'geval_c/runs/negctl/*.json', 'geval_c/runs/checks_ecnf_*.json'],
    'geval_stream': ['geval_stream/runs/cert/*.json', 'geval_stream/runs/negctl/*.json'],
    'artin_sweep': ['artin_sweep/runs/cert/*.json', 'artin_sweep/runs/field/*.json', 'artin_sweep/runs/alg/**/*.json',
                    'artin_sweep/runs/alg_v2/**/*.json', 'artin_sweep/runs/negctl/*.json'],
    'level1': ['level1/runs/*/*.json'],
    'races': ['races/data/*.json'],
    'races2': ['races2/runs/*.json'],
    'lean_audit': ['../formal/audit/**/*.txt', '../formal/audit/**/*.expected', 'zfast/atlas_v5z*/lean_audit/*.txt',
                   'record_heights/lean_audit/*.txt'],
}
MANIFEST_DIRS = ['zfast', 'zfast/atlas_v5z', 'zfast/atlas_v5z2', 'zfast/atlas_v5z3', 'zfast/atlas_v5z4', 'atlas_v5', 'record_heights',
                 'record_heights/v5run', 'flagship_K23', 'flagship_K23_ext', 'geval_c', 'geval_stream', 'artin_sweep', 'level1', 'races',
                 'races2', '../formal/audit', '../formal/audit/data_v5', 'artin_literal', 'artin_all', 'general_eval/calegari3',
                 'lmfdb_ecnf', 'mertens_cubic', 'mertens_cubic2', 'race_skewes', 'race_signs', 'new_territory/tollis',
                 'new_territory/ec37a', 'new_territory/ec389a', 'deg2_fast', 'atlas_v4']
MANIFEST_PAT = re.compile(r'^(MANIFEST_.*\.sha256|SHA256SUMS.*|.*FREEZE.*\.sha256|CODE_AT_.*\.sha256|CODE_SHA256.*\.txt|VERIFY_ZS5\.sha256)$')
LINE = re.compile(r'^([0-9a-f]{64})\s+\*?(\S.*?)\s*$')
HARD_EXT = {'.json', '.py', '.c', '.h', '.inc', '.dylib', '.lean', '.sh', '.expected', '.jsonl', '.npz', '.sha256'}


def family_files():
    out = {}
    for fam, pats in FAMILY_GLOBS.items():
        fs = set()
        for p in pats:
            fs |= set(glob.glob(str(DIAG / p), recursive=True))
        out[fam] = sorted(str(Path(f).resolve()) for f in fs if os.path.isfile(f))
    zs = set()
    for r in zfast.runs():
        zs |= set(zfast.frozen_files(r))
    out['zfast_windows'] = sorted(zs)
    return out


def freeze():
    """write FROZEN.json once (never rewritten)."""
    if FROZEN.exists(): raise RegressError('FROZEN.json exists; it is written once and never rewritten')
    t0 = time.time(); fams = family_files(); files = {}
    for fam, fs in fams.items():
        for f in fs: files[f] = dict(sha256=sha256(f), family=fam)
    json.dump(dict(created=time.strftime('%Y-%m-%d %H:%M:%S %Z'), files=files,
                   counts={k: len(v) for k, v in fams.items()}), open(FROZEN, 'w'), indent=0, sort_keys=True)
    return dict(files=len(files), counts={k: len(v) for k, v in fams.items()}, seconds=round(time.time() - t0, 1))


def check_frozen(only=None):
    if not FROZEN.exists(): raise RegressError('FROZEN.json missing: run --freeze first')
    F = json.load(open(FROZEN))['files']; bad = []; n = 0
    for f, rec in F.items():
        if only and not only(f, rec): continue
        n += 1
        if not os.path.exists(f): bad.append(dict(file=f, family=rec['family'], problem='missing'))
        elif sha256(f) != rec['sha256']: bad.append(dict(file=f, family=rec['family'], problem='sha256 changed'))
    by = {}
    for f, rec in F.items():
        if only and not only(f, rec): continue
        by.setdefault(rec['family'], [0, 0]); by[rec['family']][0] += 1
    for b in bad: by[b['family']][1] += 1
    return dict(checked=n, mismatches=bad[:50], n_mismatch=len(bad), by_family={k: dict(files=v[0], bad=v[1]) for k, v in by.items()})


def manifests():
    out = []
    for d in MANIFEST_DIRS:
        p = (DIAG / d).resolve()
        if not p.is_dir(): continue
        for f in sorted(os.listdir(p)):
            if MANIFEST_PAT.match(f) and (p / f).is_file(): out.append(p / f)
    return out


def _resolve(m, rel):
    # A2: manifests use different bases (their own dir, diagnostic/, atlas_mark2/, formal/): first existing candidate wins
    cands = [m.parent / rel, DIAG / rel, ROOT / rel, ROOT / 'formal' / rel] + [p / rel for p in m.parent.parents if str(p).startswith(str(ROOT))]
    return next((c.resolve() for c in cands if c.exists()), (m.parent / rel).resolve())


def check_manifests():
    """every entry of every historical manifest.  A mismatch whose current sha256 is recorded for the same file by ANY manifest
    (a later freeze / addendum supersedes an earlier one) is 'superseded' (INFO); a log/markdown/runner-list mismatch is INFO;
    any other mismatch on certificate, data or code is a hard FAIL (A2)."""
    ms = manifests(); entries = []
    for m in ms:
        for line in open(m, errors='replace'):
            x = LINE.match(line.strip())
            if x: entries.append((m, x.group(1), _resolve(m, x.group(2))))
    known = {}
    for m, h, f in entries: known.setdefault(str(f), set()).add(h)
    cache = {}
    def cur(f):
        if f not in cache: cache[f] = sha256(f) if os.path.isfile(f) else None
        return cache[f]
    rep = {}; hard = info = sup = 0
    for m, h, f in entries:
        r = rep.setdefault(str(m), dict(manifest=str(m), entries=0, fail=[], info=[], superseded=[])); r['entries'] += 1
        c = cur(str(f))
        if f.exists() and f.is_dir(): continue
        if c == h: continue
        if c is not None and c in known[str(f)]:
            r['superseded'].append(str(f)); sup += 1; continue
        ext = f.suffix.lower()
        rec = dict(file=str(f), problem='missing' if c is None else 'sha256 differs from every manifest entry')
        hard_kind = ((ext in HARD_EXT and not (ext == '.jsonl' and f.name != 'replay.jsonl') and not f.name.endswith('_runner.sha256'))
                     or (ext == '.txt' and any(k in str(f) for k in ('/data', '/audit', '/runs/'))))
        if hard_kind: r['fail'].append(rec); hard += 1
        else: r['info'].append(rec); info += 1
    rep = list(rep.values())
    return dict(manifests=len(ms), entries=len(entries), hard_mismatches=hard, info_mismatches=info, superseded=sup, detail=rep)
