"""Non-vacuity test of the Lean audit on the flagship K23 export: write single-fault mutations of
audit/data_flagship/flagship_K23.txt into a temporary directory and run the atlas_audit binary on each; every mutation must
be reported (non-zero TOTAL VIOLATIONS).  The unmutated file is run first and must give 0.
usage (from formal/): python3 audit/mutation_test_flagship.py"""
import sys, os, subprocess, tempfile, shutil
from fractions import Fraction
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'data_flagship', 'flagship_K23.txt')
EXE = os.path.join(os.path.dirname(HERE), '.lake', 'build', 'bin', 'atlas_audit')
S = tempfile.mkdtemp(prefix='atlas_audit_mut_flagship_')
L = open(SRC).read().split('\n')


def certs(L):
    out = []; i = 0
    while i < len(L):
        if L[i].startswith('CERT '):
            j = i
            while L[j] != 'END': j += 1
            out.append((i, j)); i = j + 1
        else: i += 1
    return out


C = certs(L)
def grp(g): return [c for c in C if L[c[0]].split(' ')[1] == g]
def ivs(c): return [x for x in range(*c) if L[x].startswith('IV ')]
def reg(c): return [x for x in range(*c) if L[x].startswith('REG ')][0]
def fr(s): return Fraction(s)
def qs(f): return str(f.numerator) if f.denominator == 1 else '%d/%d' % (f.numerator, f.denominator)
muts = {}
def mut(name, L2): muts[name] = L2

W5 = grp('flagship_K23/runs/w_5000'); W99 = grp('flagship_K23/runs/w_9990'); T0 = grp('new_territory/tollis/runs/contig/K23/c_0_10')
W2 = grp('flagship_K23/runs/w_200'); W7 = grp('flagship_K23/runs/w_7770')
# M1 drop one flagship certificate (window target and both unions [0,1e4], [200,1e4] fail)
i, j = W5[7]; mut('M01_drop_flagship_cert', L[:i] + L[j + 1:])
# M2 drop one tollis certificate (unions [0,200] and [0,1e4] fail)
i, j = T0[3]; mut('M02_drop_tollis_cert', L[:i] + L[j + 1:])
# M3 one certificate marked not passed
i, j = W99[19]; t = L[i].split(' '); t[4] = '0'; L2 = list(L); L2[i] = ' '.join(t); mut('M03_not_passed', L2)
# M4 interval outside the window
c = W2[4]; k = ivs(c)[-1]; t = L[c[0]].split(' '); a = L[k].split(' '); L2 = list(L)
L2[k] = 'IV %s %s' % (a[1], qs(fr(t[7]) + 1)); mut('M04_iv_outside', L2)
# M5 two intervals swapped
c = W7[5]; ks = ivs(c); L2 = list(L); L2[ks[0]], L2[ks[1]] = L[ks[1]], L[ks[0]]; mut('M05_unsorted', L2)
# M6 touching intervals
c = W7[6]; ks = ivs(c); a = L[ks[0]].split(' '); b = L[ks[1]].split(' '); b[1] = a[2]; L2 = list(L); L2[ks[1]] = ' '.join(b); mut('M06_touching', L2)
# M7 region d1 = 49/100
c = W5[8]; k = reg(c); a = L[k].split(' '); a[4] = '49/100'; L2 = list(L); L2[k] = ' '.join(a); mut('M07_d1', L2)
# M8 region d0 = 1/100 (d = 0 line not covered)
c = W5[9]; k = reg(c); a = L[k].split(' '); a[3] = '1/100'; L2 = list(L); L2[k] = ' '.join(a); mut('M08_d0', L2)
# M9 region outside the window
c = W5[10]; k = reg(c); a = L[k].split(' '); a[2] = '100000'; L2 = list(L); L2[k] = ' '.join(a); mut('M09_region_outside', L2)
# M10 a CENTRAL entry where none is allowed (expect_m0 = 0)
c = W5[11]; L2 = list(L); L2.insert(c[1], 'CENTRAL 2'); mut('M10_central_inserted', L2)
# M11 sub-ulp gap: shift one cell's x0 up by 2^-60 (a gap of width 2^-60 between two cells)
c = W5[12]; k = reg(c); a = L[k].split(' '); a[1] = qs(fr(a[1]) + Fraction(1, 2 ** 60)); L2 = list(L); L2[k] = ' '.join(a); mut('M11_subulp_gap', L2)
# M12 interval with t1 = t2
c = W99[3]; k = ivs(c)[0]; a = L[k].split(' '); L2 = list(L); L2[k] = 'IV %s %s' % (a[1], a[1]); mut('M12_degenerate_iv', L2)
# M13 a certificate moved to another group (coverage of its own window breaks)
i, j = W5[13]; t = L[i].split(' '); t[1] = 'flagship_K23/runs/w_9990'; L2 = list(L); L2[i] = ' '.join(t); mut('M13_wrong_group', L2)
# M14 union target extended by 2^-40 beyond 10^4
k = [x for x, l in enumerate(L) if l.startswith('TARGET union_0_10000 ')][0]; a = L[k].split(' ')
a[3] = qs(Fraction(10000) + Fraction(1, 2 ** 40)); L2 = list(L); L2[k] = ' '.join(a); mut('M14_union_overreach', L2)
# M15 one certificate marked negative_control in the real dataset
i, j = W2[0]; t = L[i].split(' '); t[5] = '1'; L2 = list(L); L2[i] = ' '.join(t); mut('M15_marked_nc', L2)
# M16 duplicated interval
c = W2[1]; k = ivs(c)[0]; L2 = list(L); L2.insert(k + 1, L[k]); mut('M16_dup_iv', L2)


def run(path):
    return subprocess.run(['nice', '-n', '19', EXE, path], capture_output=True, text=True).stdout


p0 = os.path.join(S, 'M00_unmutated.txt'); open(p0, 'w').write('\n'.join(L))
o0 = run(p0); assert 'TOTAL VIOLATIONS (non-control datasets): 0' in o0, o0
print('%-26s %s' % ('M00_unmutated', 'clean (0 violations), as required'))
ok = 0
for name in sorted(muts):
    p = os.path.join(S, name + '.txt'); open(p, 'w').write('\n'.join(muts[name]))
    out = run(p)
    hits = [l.strip() for l in out.splitlines() if l.startswith('  CERT ') or l.startswith('  TARGET ') or l.startswith('  CLAIM')]
    nv = [l for l in out.splitlines() if l.startswith('TOTAL VIOLATIONS')]
    caught = 'TOTAL VIOLATIONS (non-control datasets): 0' not in out
    ok += caught
    print('%-26s %s  [%s] %s' % (name, 'CAUGHT' if caught else 'MISSED', nv[0].split(': ')[-1] if nv else 'parse error', hits[0][:150] if hits else ''))
    os.remove(p)
print('mutations caught: %d/%d' % (ok, len(muts)))
shutil.rmtree(S, ignore_errors=True)
sys.exit(0 if ok == len(muts) else 1)
