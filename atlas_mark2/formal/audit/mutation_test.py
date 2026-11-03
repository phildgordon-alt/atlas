"""Non-vacuity test of the Lean audit: write 12 single-fault mutations of the exported data into a temporary directory and run
lake exe atlas_audit on each; every mutation must be reported.  usage: python3 audit/mutation_test.py  (from formal/)"""
import sys, os, subprocess, tempfile
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data') + '/'
S = tempfile.mkdtemp(prefix='atlas_audit_mut_')
def load(n): return open(D+n+'.txt').read().split('\n')
def save(name, L): open(S+'/'+name+'.txt','w').write('\n'.join(L))
def certs(L):
    out=[]; i=0
    while i < len(L):
        if L[i].startswith('CERT '):
            j=i
            while L[j] != 'END': j+=1
            out.append((i,j)); i=j+1
        else: i+=1
    return out
L=load('deg2'); C=certs(L)
# M1: drop one certificate of contig c_100_110
i,j=[c for c in C if ' runs/contig/c_100_110 ' in L[c[0]]][3]; save('M1_drop_cert', L[:i]+L[j+1:])
# M2: flip 'passed' of one certificate
i,j=C[5]; t=L[i].split(' '); t[4]='0'; L2=list(L); L2[i]=' '.join(t); save('M2_not_passed', L2)
# M3: interval outside window (t2 := whi + 1)
i,j=C[7]; t=L[i].split(' '); whi=t[7]; L2=list(L)
k=[x for x in range(i,j) if L[x].startswith('IV ')][-1]; a=L[k].split(' '); # make it a valid rational: whi as p/q -> replace with large integer
L2[k]='IV %s 100000'%a[1]; save('M3_iv_outside', L2)
# M4: swap two intervals (unsorted)
i,j=C[9]; L2=list(L); ks=[x for x in range(i,j) if L[x].startswith('IV ')]; L2[ks[0]],L2[ks[1]]=L[ks[1]],L[ks[0]]; save('M4_unsorted', L2)
# M5: region d1 = 49/100
i,j=C[11]; L2=list(L); k=[x for x in range(i,j) if L[x].startswith('REG ')][0]; a=L[k].split(' '); a[4]='49/100'; L2[k]=' '.join(a); save('M5_d1', L2)
# M6: region outside window (x1 := whi + 1)
i,j=C[13]; L2=list(L); k=[x for x in range(i,j) if L[x].startswith('REG ')][0]; a=L[k].split(' '); a[2]='100000'; L2[k]=' '.join(a); save('M6_region_outside', L2)
# M7: overlapping intervals (t1 of 2nd := t2 of 1st)
i,j=C[15]; L2=list(L); ks=[x for x in range(i,j) if L[x].startswith('IV ')]; a=L[ks[0]].split(' '); b=L[ks[1]].split(' '); b[1]=a[2]; L2[ks[1]]=' '.join(b); save('M7_touching', L2)
# 389a: M8 drop CENTRAL of a certificate whose window contains 0; M9 m0 = 3; M10 interval meeting 0 in a central cert
L=load('ec389a'); C=certs(L)
cc=[c for c in C if any(L[x].startswith('CENTRAL') for x in range(*c))]
i,j=cc[0]; L2=[l for x,l in enumerate(L) if not (i<=x<j and l.startswith('CENTRAL'))]; save('M8_central_dropped', L2)
L2=list(L); k=[x for x in range(i,j) if L[x].startswith('CENTRAL')][0]; L2[k]='CENTRAL 3'; save('M9_m0_3', L2)
L2=list(L); k=[x for x in range(i,j) if L[x].startswith('IV ')][0]; L2[k]='IV -1/1000 1/1000'; 
# keep sorted: put it as first interval only if previous are all < -1/1000; just replace an interval near 0
ks=[x for x in range(i,j) if L[x].startswith('IV ')]
import fractions
vals=[(fractions.Fraction(L[x].split(' ')[1]),fractions.Fraction(L[x].split(' ')[2]),x) for x in ks]
neg=[v for v in vals if v[1]<0]; pos=[v for v in vals if v[0]>0]
L2=list(L); L2.insert(pos[0][2], 'IV -1/1000000 1/1000000'); save('M10_iv_meets0', L2)
# v4: M11 drop one np certificate; M12 drop one VAR pair in the middle of a model
L=load('v4_acceptance'); C=certs(L)
npc=[c for c in C if ' np ' in L[c[0]]]; i,j=npc[0]; save('M11_np_dropped', L[:i]+L[j+1:])
i,j=C[0]; vs=[x for x in range(i,j) if L[x].startswith('VAR ')]; m=vs[len(vs)//2]; m=m - ((m-vs[0])%2)
save('M12_bin_dropped', L[:m]+L[m+2:])

EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.lake', 'build', 'bin', 'atlas_audit')
ok = 0; names = sorted(f for f in os.listdir(S) if f.endswith('.txt'))
for f in names:
    out = subprocess.run([EXE, os.path.join(S, f)], capture_output=True, text=True).stdout
    hits = [l.strip() for l in out.splitlines() if l.startswith('  CERT ') or l.startswith('  TARGET ') or l.startswith('  CLAIM')]
    caught = 'TOTAL VIOLATIONS (non-control datasets): 0' not in out
    ok += caught
    print('%-24s %s  %s' % (f[:-4], 'CAUGHT' if caught else 'MISSED', hits[0] if hits else ''))
print('mutations caught: %d/%d' % (ok, len(names)))
import shutil; shutil.rmtree(S, ignore_errors=True)
sys.exit(0 if ok == len(names) else 1)
