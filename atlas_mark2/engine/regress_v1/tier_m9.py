"""engine/regress_v1 tiers with in-memory registration (new file, RESULTS_M9 finding F-M9a).  cli.py, zfast.py and lean.py are unchanged.
Why: since M7 wrote the Lean dataset atlas_v5z5/lean_audit/v5z5_wide_1e22.txt (2026-11-01 12:36), `--tier 0` stops in lean.v5_datasets
(StopIteration: no tree for the prefix 'v5z5_').  Two scopes (env M9_SCOPE):
  golden (default) : the GOLDEN_v1 scope exactly -- v5z5_* Lean datasets are skipped and atlas_v5z5 is not registered, so every section
                     and the golden identity test compare like with like (nothing frozen may differ);
  wide             : atlas_v5z5 registered (tree + Lean prefix), as v5z5_gate.py / turing_gate.py do; golden then lists the new entries
                     (wide_1e22, lean) as differing by construction (they are not in GOLDEN_v1).
  python -m engine.regress_v1.tier_m9 --tier 0 | --tier 1   (same options as engine.regress_v1)"""
import os
from . import zfast, lean, cli
SCOPE = os.environ.get('M9_SCOPE', 'golden')
if SCOPE == 'wide':
    zfast.TREES.setdefault('atlas_v5z5', (zfast.ZF / 'atlas_v5z5', 'V5Z5_FREEZE.sha256'))
    if not any(p == 'v5z5_' for p, _ in lean.TREE_OF_PREFIX): lean.TREE_OF_PREFIX.insert(0, ('v5z5_', 'atlas_v5z5'))
elif SCOPE == 'golden':
    _orig = lean.v5_datasets
    if not any(p == 'v5z5_' for p, _ in lean.TREE_OF_PREFIX): lean.TREE_OF_PREFIX.insert(0, ('v5z5_', '__skip__'))
    _trees = zfast.TREES
    def _filtered():
        zfast.TREES = dict(_trees, __skip__=(zfast.ZF / 'atlas_v5z5', 'V5Z5_FREEZE.sha256'))
        try: return [d for d in _orig() if not d['name'].startswith('v5z5_')]
        finally: zfast.TREES = _trees
    lean.v5_datasets = _filtered
else:
    raise SystemExit(f'M9_SCOPE must be golden or wide, not {SCOPE!r}')
if __name__ == '__main__':
    cli.main()
