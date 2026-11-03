"""Exact exporter for the Lean audit (formal/AtlasAudit, `lake exe atlas_audit`).

Reads the certificate JSON files of the Atlas pipelines READ-ONLY and writes, per dataset, a line-oriented text file
formal/audit/data/<dataset>.txt in which every number is the EXACT rational value of the binary64 float stored in the JSON
(Python's json module parses a decimal literal to the nearest double, exactly as the pipelines' own verifiers do; that double
is then converted with Fraction(float), which is exact). No rounding, no float arithmetic on exported values.

Format (one record per line, tokens separated by single spaces; a rational is "p/q" with q > 0, or "p"):
  DATASET <name> <expect_m0> <model 0|1>   (model = 1: every certificate carries an all-open v4 model, VAR lines)
  CERT <group> <file> <kind main|np> <passed 0|1> <negative_control 0|1> <wlo> <whi>
  REG <x0> <x1> <d0> <d1>            candidate region(s)
  IV <t1> <t2>                        sign-change intervals, in file order
  CENTRAL <m0>                        only if the certificate has a non-null 'central' entry
  VAR <on|off> <lo> <hi> <dlo> <dhi>  v4 all-open model boxes, in file order
  END
  TARGET <name> <lo> <hi> <group>[,<group>...]   exact tiling target: target x [0, 1/2] by passed regions of these groups
  CLAIMB <group>                       v4 claim (B): S-layer coverage inside this group
'passed' is the TRUSTED Arb replay verdict (plain AND hardened CERTIFIED / passed), read from the run's replay record.
The exporter interprets nothing else: every combinatorial condition is checked in Lean.
usage: python3 export_certs.py [OUTDIR]

v5 path (added 2026-10-08, atlas_v5 exact heights; the default path above is unchanged):
  python3 export_certs.py --v5 DATASET OUTDIR RUN_DIR [RUN_DIR ...]   -> OUTDIR/DATASET.txt
atlas_v5 certificates store every height as a binary64 OFFSET u from an integer T0 (JSON int, in the certificate and pieces.json);
the height is T0 + u exactly.  The v5 path writes every height as the exact rational Fraction(T0) + Fraction(u) (no rounding) and
displacements d exactly as the v4 path does.  Same record format, so the Lean audit (AtlasAudit) is unchanged."""
import sys, os, json, glob, math
from fractions import Fraction

DIAG = '/Users/kiosk/atlas_mark2/diagnostic'
NT = DIAG + '/new_territory'
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '--v5' else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audit', 'data')


def q(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError('not a number: %r' % (x,))
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError('non-finite: %r' % (x,))
    f = Fraction(x)                       # exact value of the double (or int)
    assert isinstance(x, int) or float(f) == x and Fraction(float(f)) == f
    return str(f.numerator) if f.denominator == 1 else '%d/%d' % (f.numerator, f.denominator)


class W:
    def __init__(self, name, expect_m0, model=0):
        self.name = name; self.lines = ['DATASET %s %d %d' % (name, expect_m0, model)]; self.ncert = 0

    def cert(self, group, fname, kind, passed, nc, window, regions, intervals, central, vars_=()):
        L = self.lines; self.ncert += 1
        L.append('CERT %s %s %s %d %d %s %s' % (group, fname, kind, int(bool(passed)), int(bool(nc)), q(window[0]), q(window[1])))
        assert len(window) == 2
        for r in regions:
            assert len(r) == 4; L.append('REG ' + ' '.join(q(v) for v in r))
        for iv in intervals:
            assert len(iv) == 2; L.append('IV %s %s' % (q(iv[0]), q(iv[1])))
        if central is not None:
            m0 = central.get('m0', 0)
            if not (isinstance(m0, int) and not isinstance(m0, bool)):
                raise ValueError('central m0 not an int in %s/%s' % (group, fname))
            L.append('CENTRAL %d' % m0)
        for v in vars_:
            assert len(v) == 5 and v[0] in ('on', 'off'); L.append('VAR %s ' % v[0] + ' '.join(q(x) for x in v[1:]))
        L.append('END')

    def target(self, name, lo, hi, groups):
        self.lines.append('TARGET %s %s %s %s' % (name, q(lo), q(hi), ','.join(groups)))
        # the CLAIMED target is a decimal (e.g. 91.06): also check the exact decimal rational of the shortest repr
        dl, dh = Fraction(repr(float(lo))), Fraction(repr(float(hi)))
        if (dl, dh) != (Fraction(lo), Fraction(hi)):
            fmt = lambda f: str(f.numerator) if f.denominator == 1 else '%d/%d' % (f.numerator, f.denominator)
            self.lines.append('TARGET %s:decimal %s %s %s' % (name, fmt(dl), fmt(dh), ','.join(groups)))

    def claimb(self, group):
        self.lines.append('CLAIMB %s' % group)

    def write(self):
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, self.name + '.txt')
        open(p, 'w').write('\n'.join(self.lines) + '\n')
        print('%-16s %5d certificates -> %s' % (self.name, self.ncert, p))


def deg2_run(w, root, rundir, nc=False):
    """one deg2-family run directory: certs/cell_*.json + replay.json (cells passed plain AND hardened)"""
    group = os.path.relpath(rundir, root)
    passed = set(); target = None
    rp = os.path.join(rundir, 'replay.json')
    if os.path.exists(rp) and not nc:
        r = json.load(open(rp)); target = r['summary'].get('target')
        for c in r['cells']:
            if c.get('plain') == 'CERTIFIED' and c.get('hardened') == 'CERTIFIED':
                passed.add(c['file'])
    for f in sorted(glob.glob(os.path.join(rundir, 'certs', 'cell_*.json'))):
        c = json.load(open(f)); fn = os.path.basename(f)
        reg = [c['cell'][0], c['cell'][1], c['d_range'][0], c['d_range'][1]]
        assert len(c['cell']) == 2 and len(c['d_range']) == 2
        w.cert(group, fn, 'main', fn in passed, bool(c.get('negative_control')) or nc, c['window'], [reg], c['intervals'], c.get('central'))
    return group, target


def deg2_dataset(name, root, rundirs, unions, expect_m0, ncdirs=()):
    w = W(name, expect_m0); ncw = W(name + '_nc', expect_m0)
    for d in rundirs:
        g, t = deg2_run(w, root, d)
        assert t is not None, d
        w.target(g, t[0], t[1], [g])
    for (lo, hi, dirs) in unions:
        w.target('union_%g_%g' % (lo, hi) if len(unions) == 1 else 'union_%s_%g_%g' % (os.path.basename(os.path.dirname(dirs[0])), lo, hi),
                 lo, hi, [os.path.relpath(d, root) for d in dirs])
    w.write()
    if ncdirs:
        for d in ncdirs: deg2_run(ncw, root, d, nc=True)
        ncw.write()


def chunks(base, lo, hi, step=10, prefix='c_'):
    return [os.path.join(base, '%s%d_%d' % (prefix, a, a + step)) for a in range(lo, hi, step)]


def main():
    # ---- deg2 (11.a, 23.1.b.a; contig 11.a [0, 300]) ----
    R = NT + '/deg2'
    runs = [R + '/runs/' + d for d in ('t_11a_100_110', 't_11a_200_210', 't_23_93.5_104', 'val_11a_0_20', 'val_23_0_18')]
    contig = chunks(R + '/runs/contig', 0, 300)
    deg2_dataset('deg2', R, runs + contig, [(0, 300, contig)], 0, [R + '/runs/nc/fake'])
    # ---- ec37a ----
    R = NT + '/ec37a'
    ch = chunks(R + '/runs/chunks', 10, 200)
    deg2_dataset('ec37a', R, [R + '/runs/val_0_10'] + ch, [(0, 200, [R + '/runs/val_0_10'] + ch)], 0,
                 [R + '/runs/nc/' + d for d in ('epsgen', 'forged')])
    # ---- ec389a (central reduction m0 = 2) ----
    R = NT + '/ec389a'
    ch = chunks(R + '/runs/chunks', 0, 200)
    deg2_dataset('ec389a', R, [R + '/runs/val_0_10'] + ch, [(0, 200, ch)], 2,
                 [R + '/runs/nc/' + d for d in ('forged', 'm0_0', 'm0_1')])
    # ---- tollis: the six pre-registered fields (core + val + contig), and the extras as a separate dataset ----
    R = NT + '/tollis'
    fields = ('K23', 'K31', 'K44', 'K59', 'K76', 'K83')
    def done(d): return os.path.isdir(d) and os.path.exists(os.path.join(d, 'replay.json'))
    core = [d for d in sorted(glob.glob(R + '/runs/core/K*_*')) if done(d) and os.path.basename(d).split('_')[0] in fields]
    val = [d for d in sorted(glob.glob(R + '/runs/val/K*_0_10')) if done(d) and os.path.basename(d).split('_')[0] in fields]
    cont = {k: chunks(R + '/runs/contig/' + k, 0, 200 if k == 'K23' else 110) for k in fields}
    unions = [(0, 110, cont[k][:11]) for k in fields] + [(0, 200, cont['K23'])]
    alld = core + val + [d for k in fields for d in cont[k]]
    deg2_dataset('tollis', R, alld, unions, 0, [R + '/runs/nc/forged'])
    # extras (K87, K104, K107, K108, ...: run after RESULTS.md was written, still in progress during this audit):
    # every core / contig run directory of a non-pre-registered field whose replay record exists at export time; no unions
    extra = [d for d in sorted(glob.glob(R + '/runs/core/K*_*') + glob.glob(R + '/runs/contig/K*/c_*'))
             if done(d) and os.path.basename(d.rstrip('/')).split('_')[0] not in fields
             and os.path.basename(os.path.dirname(d)) not in fields]
    if extra:
        deg2_dataset('tollis_extra', R, extra, [], 0)

    # ---- atlas_v4 acceptance runs (and the other v4 runs, as a separate dataset) ----
    V = DIAG + '/atlas_v4'
    acc = ['w9000.00/v1_9000', 'w7000.00/lehmer', 'w7000.00/c7002', 'w6820046.00/rosser', 'w663310.00/t2_663318']
    other = sorted(os.path.relpath(d, V + '/runs') for d in glob.glob(V + '/runs/w*/*') if os.path.isdir(d))
    other = [d for d in other if d not in acc]
    for name, lst in (('v4_acceptance', acc), ('v4_other', other)):
        w = W(name, 0, 1)
        for rd in lst:
            run = V + '/runs/' + rd; group = rd
            recs = [json.loads(l) for l in open(run + '/replay_check/replay.jsonl')]
            by = {}
            for r in recs:
                key = '/'.join(r['cert'].split('/')[-2:])
                by.setdefault(key, {})['h' if r['hardened'] else 'p'] = bool(r.get('passed'))
            for sub, kind in (('certs', 'main'), ('certs_np', 'np')):
                for f in sorted(glob.glob(run + '/' + sub + '/cert_*.json')):
                    c = json.load(open(f)); key = sub + '/' + os.path.basename(f)
                    ok = by.get(key, {}).get('p') is True and by.get(key, {}).get('h') is True
                    assert c.get('mode', 'main') == ('noparity' if kind == 'np' else 'main'), f
                    w.cert(group, key, kind, ok, False, c['window'], c['regions'], c['zs_intervals'], c.get('central'), c['vars'])
            P = json.load(open(run + '/pieces.json'))
            w.target(group + ':target', P['target'][0], P['target'][1], [group])
            w.target(group + ':hull', P['hull'][0], P['hull'][1], [group])
            w.claimb(group)
        w.write()


# ---------------- v5 path (exact heights T0 + u) ----------------
def qf(f):
    f = Fraction(f); return str(f.numerator) if f.denominator == 1 else '%d/%d' % (f.numerator, f.denominator)


def qh(T0, u):
    """exact rational T0 + u of an atlas_v5 height (T0 int, u binary64 offset as parsed from the JSON)"""
    if not (isinstance(T0, int) and not isinstance(T0, bool)):
        raise ValueError('T0 not an int: %r' % (T0,))
    q(u)                                   # validates u (finite number, exact binary64)
    return qf(Fraction(T0) + Fraction(u))


def v5_dataset(name, outdir, runs):
    L = ['DATASET %s 0 1' % name]; n = 0
    for run in runs:
        run = os.path.abspath(run); P = json.load(open(run + '/pieces.json'))
        assert P.get('format') == 'atlas_v5', run
        T0 = P['T0']; group = os.path.relpath(run, os.path.dirname(os.path.dirname(run)))
        by = {}
        for l in open(run + '/replay_check/replay.jsonl'):
            r = json.loads(l); key = '/'.join(r['cert'].split('/')[-2:])
            by.setdefault(key, {})['h' if r['hardened'] else 'p'] = bool(r.get('passed'))
        for sub, kind in (('certs', 'main'), ('certs_np', 'np')):
            for f in sorted(glob.glob(run + '/' + sub + '/cert_*.json')):
                c = json.load(open(f)); key = sub + '/' + os.path.basename(f)
                assert c['format'] == 'atlas_v5' and c['T0'] == T0 and c.get('mode', 'main') == ('noparity' if kind == 'np' else 'main'), f
                ok = by.get(key, {}).get('p') is True and by.get(key, {}).get('h') is True
                L.append('CERT %s %s %s %d 0 %s %s' % (group, key, kind, int(ok), qh(T0, c['window'][0]), qh(T0, c['window'][1])))
                assert len(c['window']) == 2
                for r in c['regions']:
                    assert len(r) == 4; L.append('REG %s %s %s %s' % (qh(T0, r[0]), qh(T0, r[1]), q(r[2]), q(r[3])))
                for iv in c['zs_intervals']:
                    assert len(iv) == 2; L.append('IV %s %s' % (qh(T0, iv[0]), qh(T0, iv[1])))
                assert c.get('central') is None
                for v in c['vars']:
                    assert len(v) == 5 and v[0] in ('on', 'off'); L.append('VAR %s %s %s %s %s' % (v[0], qh(T0, v[1]), qh(T0, v[2]), q(v[3]), q(v[4])))
                L.append('END'); n += 1
        L.append('TARGET %s:target %s %s %s' % (group, qh(T0, P['target'][0]), qh(T0, P['target'][1]), group))
        dl, dh = Fraction(P['target_input'][0]), Fraction(P['target_input'][1])          # the claimed decimal target
        if (dl, dh) != (Fraction(T0) + Fraction(P['target'][0]), Fraction(T0) + Fraction(P['target'][1])):
            L.append('TARGET %s:target:decimal %s %s %s' % (group, qf(dl), qf(dh), group))
        L.append('TARGET %s:hull %s %s %s' % (group, qh(T0, P['hull'][0]), qh(T0, P['hull'][1]), group))
        L.append('CLAIMB %s' % group)
    os.makedirs(outdir, exist_ok=True); p = os.path.join(outdir, name + '.txt')
    open(p, 'w').write('\n'.join(L) + '\n'); print('%-16s %5d certificates -> %s' % (name, n, p))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--v5':
        v5_dataset(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        main()
