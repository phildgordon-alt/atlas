"""Builds atlas_v5z3/ from atlas_v5z2/ (new files only): provider re-pinned to libzfast.v13b (review2 fixes m1-m4); the run
scripts point at atlas_v5z3; everything else is a byte copy."""
import os, hashlib, shutil
Z2 = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z2/'; Z3 = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z3/'
OLD = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v12a.dylib'; NEW = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v13b.dylib'
os.makedirs(Z3 + 'lib'); os.makedirs(Z3 + 'nzeros')
for f in ['crosscheck.py', 'replay_target5.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py'] + ['lib/' + x for x in os.listdir(Z2 + 'lib') if x.endswith('.py') and x != 'zfast_provider.py']:
    shutil.copyfile(Z2 + f, Z3 + f)
p = open(Z2 + 'lib/zfast_provider.py').read()
osha, nsha = hashlib.sha256(open(OLD, 'rb').read()).hexdigest(), hashlib.sha256(open(NEW, 'rb').read()).hexdigest()
assert p.count(OLD) == 2 and p.count(osha) == 1
p = p.replace(OLD, NEW).replace(osha, nsha).replace('atlas_v5z2 Z / row provider', 'atlas_v5z3 Z / row provider (= v5z2 provider re-pinned to libzfast.v13b)')
open(Z3 + 'lib/zfast_provider.py', 'w').write(p)
d = open(Z2 + 'atlas_v5.py').read()
a = "z_provider='zfast libzfast.v12a, provider v5z2 (THEORY_M5, THEORY_M5b)'"; assert d.count(a) == 1
open(Z3 + 'atlas_v5.py', 'w').write(d.replace(a, "z_provider='zfast libzfast.v13b, provider v5z3 (THEORY_M5, THEORY_M5b, review2 fixes)'"))
for f in ['run_window.sh', 'run_height.sh']:
    s = open(Z2 + f).read().replace('/zfast/atlas_v5z2', '/zfast/atlas_v5z3').replace('cd atlas_v5z2', 'cd atlas_v5z3').replace('atlas_v5z2/runs/v5z.log', 'atlas_v5z3/runs/v5z.log')
    open(Z3 + f, 'w').write(s); os.chmod(Z3 + f, 0o755)
open(Z3 + 'THEORY_V5Z3.md', 'w').write('''# atlas_v5z3 = atlas_v5z2 with libzfast.v13b (2026-10-19)

The provider is re-pinned from libzfast.v12a to libzfast.v13b, which is v12a plus the review2 fixes:
- **m1:** `ok = 0` rows are indeterminate;
- **m2:** the session guards;
- **m3:** the bucket-remainder abort is removed, because short remainders are finished in the head;
- **m4:** full printed balls.

Mathematics and code paths are otherwise identical (THEORY_V5Z2.md, THEORY_M5, THEORY_M5b). The run scripts point at this tree. Every
other file is a byte copy of atlas_v5z2.
''')
print('v13b sha', nsha)
