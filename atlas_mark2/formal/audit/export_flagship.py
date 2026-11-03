#!/usr/bin/env python3
"""Driver for the Lean audit of the flagship K23 run (diagnostic/flagship_K23, 2026-10-10): exact export of
  * the 980 flagship windows runs/w_<a> (a = 200, 210, ..., 9990; 20 cells each, 19,600 certificates), and
  * the 20 existing Tollis K23 contig chunks new_territory/tollis/runs/contig/K23/c_<a>_<a+10> ([0, 200], 400 certificates),
into audit/data_flagship/flagship_K23.txt, plus a negative-control dataset audit/data_flagship/flagship_K23_nc.txt.

The exporter formal/export/export_certs.py is loaded UNCHANGED as a module (importlib; its main() is not run, nothing in its
source is replaced); only its module global OUT (the output directory read by W.write) is set. This driver calls its own
W, W.cert, W.target and deg2_run.  The flagship certificate format is the deg2-family format that deg2_run reads
(certs/cell_*.json with window, cell, d_range, intervals, negative_control, no central; replay.json with cells[].plain/hardened
and summary.target), so NO format adaptation is needed.  The only difference from the exporter's deg2_dataset() is:
  * group names are paths relative to diagnostic/ (deg2_run(w, DIAG, d)), because the two sources live in different trees;
  * three union targets are written with explicit names (deg2_dataset would only name them after a parent directory):
      union_0_10000   = [0, 10^4]   over all 1,000 groups (20 tollis chunks + 980 flagship windows)
      union_0_200     = [0, 200]    over the 20 tollis K23 chunks
      union_200_10000 = [200, 10^4] over the 980 flagship windows
  * per-run targets are taken from replay.json summary.target exactly as deg2_dataset does; the driver additionally asserts that
    they are [a, a+10].
Negative controls (flagship_K23_nc, every certificate marked negative_control = 1): deliberately broken copies of real flagship
certificates (structural faults the Lean checks must report) and coverage targets that must fail; see NC below.  Expected
violations are printed and written to audit/data_flagship/flagship_K23_nc.expected.
usage (from formal/): python3 audit/export_flagship.py [OUTDIR]"""
import sys, os, json, copy, importlib.util
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(os.path.dirname(HERE), 'export', 'export_certs.py')
spec = importlib.util.spec_from_file_location('export_certs_lib', EXP)
E = importlib.util.module_from_spec(spec)
_argv = sys.argv; sys.argv = [EXP]          # the exporter's module-level OUT reads sys.argv; give it none
spec.loader.exec_module(E)
sys.argv = _argv
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'data_flagship')
E.OUT = OUT

DIAG = E.DIAG
TOL = os.path.join(E.NT, 'tollis', 'runs', 'contig', 'K23')
FL = os.path.join(DIAG, 'flagship_K23', 'runs')
tdirs = E.chunks(TOL, 0, 200)
fdirs = [os.path.join(FL, 'w_%d' % a) for a in range(200, 10000, 10)]
assert len(tdirs) == 20 and len(fdirs) == 980
for d in tdirs + fdirs:
    assert os.path.exists(os.path.join(d, 'replay.json')), d

# ---------------- real dataset ----------------
w = E.W('flagship_K23', 0)
groups = {}
for d in tdirs + fdirs:
    n0 = w.ncert
    g, t = E.deg2_run(w, DIAG, d)
    a = int(os.path.basename(d).split('_')[-2] if 'c_' in os.path.basename(d) else os.path.basename(d).split('_')[1])
    assert t is not None and list(map(float, t)) == [a, a + 10], (d, t)
    assert w.ncert - n0 == 20, (d, w.ncert - n0)
    w.target(g, t[0], t[1], [g])
    groups[d] = g
w.target('union_0_10000', 0, 10000, [groups[d] for d in tdirs + fdirs])
w.target('union_0_200', 0, 200, [groups[d] for d in tdirs])
w.target('union_200_10000', 200, 10000, [groups[d] for d in fdirs])
w.write()
assert w.ncert == 20000

# ---------------- negative controls ----------------
# Each NC certificate is a real flagship certificate (read-only) with ONE structural fault, written with nc = 1 under its own
# group nc/<tag>.  passed is set to 1 (the Arb verdict of the original), so that coverage targets can use them.
nc = E.W('flagship_K23_nc', 0)
expected = []                               # (what, expected to be reported)


def load(a, i):
    d = os.path.join(FL, 'w_%d' % a)
    fn = sorted(os.listdir(os.path.join(d, 'certs')))[i]
    return fn, json.load(open(os.path.join(d, 'certs', fn)))


def put(tag, fn, c, central=None):
    reg = [c['cell'][0], c['cell'][1], c['d_range'][0], c['d_range'][1]]
    nc.cert('nc/' + tag, fn, 'main', True, True, c['window'], [reg], c['intervals'], central)


def first_two_ivs(c):
    assert len(c['intervals']) >= 2
    return c['intervals']


cases = []
fn, c = load(1000, 0); c['d_range'] = [0.0, 0.49]; put('d1_049', fn, c); cases.append(('d1_049', 'region d-range [0, 0.49]'))
fn, c = load(2000, 1); c['d_range'] = [0.01, 0.5]; put('d0_001', fn, c); cases.append(('d0_001', 'region d-range [0.01, 0.5] (d = 0 line missing)'))
fn, c = load(3000, 2); c['cell'] = [c['cell'][0], c['window'][1] + 1.0]; put('cell_outside', fn, c); cases.append(('cell_outside', 'cell beyond window'))
fn, c = load(3010, 3); c['cell'] = [c['cell'][1], c['cell'][0]]; put('cell_reversed', fn, c); cases.append(('cell_reversed', 'cell x0 > x1'))
fn, c = load(4000, 4); c['intervals'][-1] = [c['intervals'][-1][0], c['window'][1] + 0.5]; put('iv_outside', fn, c); cases.append(('iv_outside', 'interval leaves window'))
fn, c = load(5000, 5); iv = first_two_ivs(c); iv[0], iv[1] = iv[1], iv[0]; put('iv_swapped', fn, c); cases.append(('iv_swapped', 'two intervals swapped'))
fn, c = load(6000, 6); iv = first_two_ivs(c); iv[1] = [iv[0][1], iv[1][1]]; put('iv_touching', fn, c); cases.append(('iv_touching', 'touching intervals t2_k = t1_{k+1}'))
fn, c = load(7000, 7); iv = first_two_ivs(c); iv[0] = [iv[0][1], iv[0][0]]; put('iv_reversed', fn, c); cases.append(('iv_reversed', 'interval t1 > t2'))
fn, c = load(8000, 8); put('central_recorded', fn, c, central={'m0': 2}); cases.append(('central_recorded', 'central reduction recorded although expect_m0 = 0 and window not containing 0'))
fn, c = load(9000, 9); c['intervals'] = c['intervals'] + [list(c['intervals'][-1])]; put('iv_duplicate', fn, c); cases.append(('iv_duplicate', 'duplicated interval'))
for tag, what in cases:
    expected.append(('CERT nc/%s' % tag, what))

# coverage controls: the 20 certificates of window w_5000 (unmodified, nc = 1, passed as recorded) and w_5010 without its
# cell [5010.5, 5011]; one target that must PASS (no false alarm) and four that must FAIL.
for a, drop in ((5000, None), (5010, 1)):
    d = os.path.join(FL, 'w_%d' % a)
    passed = {cc['file'] for cc in json.load(open(os.path.join(d, 'replay.json')))['cells']
              if cc.get('plain') == 'CERTIFIED' and cc.get('hardened') == 'CERTIFIED'}
    for k, fnm in enumerate(sorted(os.listdir(os.path.join(d, 'certs')))):
        if k == drop:
            continue
        cc = json.load(open(os.path.join(d, 'certs', fnm)))
        nc.cert('cov/w_%d' % a, fnm, 'main', fnm in passed, True, cc['window'],
                [[cc['cell'][0], cc['cell'][1], cc['d_range'][0], cc['d_range'][1]]], cc['intervals'], cc.get('central'))
nc.target('ok_w5000', 5000, 5010, ['cov/w_5000'])                                  # must be covered
nc.target('gap_w5010_missing_cell', 5010, 5020, ['cov/w_5010'])                     # cell [5010.5, 5011] missing
nc.target('gap_union_5000_5020', 5000, 5020, ['cov/w_5000', 'cov/w_5010'])          # same gap inside a union
ov = Fraction(5010) + Fraction(1, 2 ** 40)                                         # sub-ulp overreach (W.target takes floats only)
nc.lines.append('TARGET overreach_1ulp 5000 %d/%d cov/w_5000' % (ov.numerator, ov.denominator))
nc.target('wrong_groups', 5000, 5010, ['cov/w_5010'])                               # coverage from the wrong run
expected += [('TARGET gap_w5010_missing_cell', 'missing cell'), ('TARGET gap_union_5000_5020', 'missing cell in union'),
             ('TARGET overreach_1ulp', 'target 2^-40 beyond coverage'), ('TARGET wrong_groups', 'wrong groups')]
nc.write()
with open(os.path.join(OUT, 'flagship_K23_nc.expected'), 'w') as f:
    for k, v in expected:
        f.write('%s\t%s\n' % (k, v))
print('negative controls: %d broken certificates + 40 coverage certificates (1 dropped), %d expected violations, 1 target expected covered'
      % (len(cases), len(expected)))
