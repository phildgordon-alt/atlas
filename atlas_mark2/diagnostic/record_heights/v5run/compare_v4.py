#!/usr/bin/env python
"""THEORY_V5 section 9 step 1: compare an atlas_v5 compatibility run (grid v4, evaluator zeta) with the frozen atlas_v4 run of the same target.
CLI: compare_v4.py V4_RUN_DIR V5_RUN_DIR  -> V5_RUN_DIR/compare_v4.json; exit 0 iff the certificates are mathematically identical.
Every height is compared as an EXACT rational: v4 stores absolute binary64 x (value Fraction(x)); v5 stores offsets u from the integer T0
(value T0 + Fraction(u)).  Compared per certificate file (same names): bins, piece bins, window, regions, sign-change intervals, model vars,
row ids (kernel a and centre as real numbers), Nwin, y, w (binary64 equality), mode, tier; per run: pieces, hull, target, zs.json intervals.
Replay: both runs' replay verdicts (plain + hardened) and min_candidate_lower (relative difference reported)."""
import sys, json, glob, os
from fractions import Fraction as F
from pathlib import Path

v4, v5 = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
P4, P5 = json.load(open(v4 / 'pieces.json')), json.load(open(v5 / 'pieces.json'))
T0 = P5['T0']; assert isinstance(T0, int) and P5['grid'] == 'v4' and F(P4['T0']) == T0
X4 = lambda x: F(x)
X5 = lambda u: F(T0) + F(u)
diffs = []


def eq(tag, a, b):
    if a != b: diffs.append(dict(field=tag, v4=str(a)[:200], v5=str(b)[:200]))


eq('hull', [X4(v) for v in P4['hull']], [X5(v) for v in P5['hull']]); eq('target', [X4(v) for v in P4['target']], [X5(v) for v in P5['target']])
eq('hull_bins', P4['hull_bins'], P5['hull_bins']); eq('pieces', [p['bins'] for p in P4['pieces']], [p['bins'] for p in P5['pieces']])
eq('pieces_col', [[X4(v) for v in p['col']] for p in P4['pieces']], [[X5(v) for v in p['col']] for p in P5['pieces']])
z4, z5 = json.load(open(v4 / 'zs.json')), json.load(open(v5 / 'zs.json'))
eq('zs_intervals', [[X4(a), X4(b)] for a, b in z4['intervals']], [[X5(a), X5(b)] for a, b in z5['intervals_offsets']])


def rowkey4(k): a, t = k.split('|'); return (F(a), X4(float(t)))
def rowkey5(k): a, t = k.split('|'); return (F(a), X5(float(t)))


files = {}
for sub in ('certs', 'certs_np'):
    n4 = sorted(os.path.basename(f) for f in glob.glob(str(v4 / sub / 'cert_*.json'))); n5 = sorted(os.path.basename(f) for f in glob.glob(str(v5 / sub / 'cert_*.json')))
    eq(sub + ':files', n4, n5)
    for n in set(n4) & set(n5):
        c4, c5 = json.load(open(v4 / sub / n)), json.load(open(v5 / sub / n)); tag = f'{sub}/{n}'
        eq(tag + ':bins', c4['bins'], c5['bins']); eq(tag + ':piece_bins', c4.get('piece_bins'), c5.get('piece_bins'))
        eq(tag + ':mode', c4.get('mode', 'main'), c5.get('mode', 'main')); eq(tag + ':tier', c4.get('tier'), c5.get('tier'))
        eq(tag + ':window', [X4(v) for v in c4['window']], [X5(v) for v in c5['window']])
        eq(tag + ':regions', [[X4(r[0]), X4(r[1]), F(r[2]), F(r[3])] for r in c4['regions']], [[X5(r[0]), X5(r[1]), F(r[2]), F(r[3])] for r in c5['regions']])
        eq(tag + ':zs_intervals', [[X4(a), X4(b)] for a, b in c4['zs_intervals']], [[X5(a), X5(b)] for a, b in c5['zs_intervals']])
        eq(tag + ':vars', [[v[0], X4(v[1]), X4(v[2]), F(v[3]), F(v[4])] for v in c4['vars']], [[v[0], X5(v[1]), X5(v[2]), F(v[3]), F(v[4])] for v in c5['vars']])
        eq(tag + ':ids', [rowkey4(k) for k in c4['ids']], [rowkey5(k) for k in c5['ids']])
        eq(tag + ':Nwin', c4['Nwin'], c5['Nwin']); eq(tag + ':y', c4['y'], c5['y']); eq(tag + ':w', c4['w'], c5['w'])
        if 'interval' in c4: eq(tag + ':interval', [X4(v) for v in c4['interval']], [X5(v) for v in c5['interval']])
        files[tag] = dict(rows=len(c5['ids']), intervals=len(c5['zs_intervals']), sampled_margin_v4=c4.get('sampled_margin'), sampled_margin_v5=c5.get('sampled_margin'))


def rep(run, sub):
    out = {}
    for l in open(run / sub / 'replay.jsonl'):
        r = json.loads(l); k = '/'.join(r['cert'].split('/')[-2:]); out.setdefault(k, {})['h' if r['hardened'] else 'p'] = r
    return out


r4, r5 = rep(v4, 'replay_check'), rep(v5, 'replay_check'); mc = []
for k in sorted(set(r4) | set(r5)):
    for m in ('p', 'h'):
        a, b = r4.get(k, {}).get(m, {}), r5.get(k, {}).get(m, {})
        eq(f'replay:{k}:{m}:passed', a.get('passed'), b.get('passed'))
        if a.get('min_candidate_lower') is not None and b.get('min_candidate_lower') is not None:
            x, y = a['min_candidate_lower'], b['min_candidate_lower']; mc.append(dict(cert=k, mode=m, v4=x, v5=y, rel=abs(x - y) / max(abs(x), 1e-300)))
maxrel = max((q['rel'] for q in mc), default=0.0)
s4, s5 = json.load(open(v4 / 'summary.json')), json.load(open(v5 / 'summary.json'))
res = dict(v4=str(v4), v5=str(v5), T0=T0, identical=not diffs, differences=diffs, certificates_compared=len(files), files=files,
           min_candidate_lower=mc, max_relative_margin_difference=maxrel, margins_equal_up_to_1e9=maxrel <= 1e-9,
           closed_v4=s4['all_closed'], closed_v5=s5['all_closed'], claimB_v4=s4['simple_without_lemma2'], claimB_v5=s5['simple_without_lemma2'],
           wall_v4=s4['wall_seconds'], wall_v5=s5['wall_seconds'], peak_gb_v5=s5['peak_gb'])
json.dump(res, open(v5 / 'compare_v4.json', 'w'), indent=1)
print(json.dumps(dict(run=v5.name, identical=res['identical'], n_diff=len(diffs), certs=len(files), max_rel_margin=maxrel, closed=[res['closed_v4'], res['closed_v5']],
                      claimB=[res['claimB_v4'], res['claimB_v5']], wall=[res['wall_v4'], res['wall_v5']], first_diffs=diffs[:3])))
sys.exit(0 if (not diffs and res['margins_equal_up_to_1e9'] and res['closed_v5'] and res['claimB_v5']) else 1)
