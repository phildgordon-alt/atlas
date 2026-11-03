"""Builds atlas_v5z4/ from atlas_v5z3/ (new files only).  One trusted change (THEORY_V5Z4.md): model5.count_upper5 evaluates at
the fixed precision 256 + bitlen(base) instead of the ambient ctx.prec, so N_win (and the far-bound shell counts) are deterministic
functions of (T0, x, y).  Cause: certify_sech_interferometer._init sets ctx.prec = 256 globally (never restored), so a model built
before the first row measurement used 128 bits and one built after used 256; at 1e23 the two give different binary64 upper bounds
(both valid) and the replay's exact model-equality check (correctly) rejected the first certificate."""
import os, shutil
Z3 = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z3/'; Z4 = '/Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z4/'
os.makedirs(Z4 + 'lib'); os.makedirs(Z4 + 'nzeros')
for f in ['crosscheck.py', 'replay_target5.py', 'VERIFY_ZS5.sha256', 'nzeros/arb_nzeros.py'] + ['lib/' + x for x in os.listdir(Z3 + 'lib') if x.endswith('.py') and x not in ('model5.py',)]:
    shutil.copyfile(Z3 + f, Z4 + f)
m = open(Z3 + 'lib/model5.py').read()
old = """def count_upper5(base, x, y):
    k = (base, x, y)
    if k not in _CU: _CU[k] = arb(((theta5(base, y) - theta5(base, x)) / arb.pi() + 2 * im.Smax(hx(base, y))).upper())
    return _CU[k]
"""
new = """NWIN_PREC = 256          # v5z4: count_upper5 runs at NWIN_PREC + bitlen(base) bits, independent of the ambient ctx.prec


def count_upper5(base, x, y):
    \"\"\"v5z4: same real expression as v5; evaluated at the fixed precision NWIN_PREC + bitlen(base), so the returned upper bound
    (an exact Arb number) is a deterministic function of (base, x, y).  (v5/v5z/v5z2/v5z3 used the ambient ctx.prec, which the
    sech engine raises from 128 to 256 on first use: harmless below 1e23, a replay mismatch at 1e23; THEORY_V5Z4.md.)\"\"\"
    k = (base, x, y)
    if k not in _CU:
        old = ctx.prec; ctx.prec = NWIN_PREC + int(base).bit_length()
        try: v = arb(((theta5(base, y) - theta5(base, x)) / arb.pi() + 2 * im.Smax(hx(base, y))).upper())
        finally: ctx.prec = old
        _CU[k] = v
    return _CU[k]
"""
assert m.count(old) == 1
open(Z4 + 'lib/model5.py', 'w').write(m.replace(old, new))
d = open(Z3 + 'atlas_v5.py').read()
a = "z_provider='zfast libzfast.v13b, provider v5z3 (THEORY_M5, THEORY_M5b, review2 fixes)'"; assert d.count(a) == 1
open(Z4 + 'atlas_v5.py', 'w').write(d.replace(a, "z_provider='zfast libzfast.v13b, provider v5z3; model5 fixed-precision N_win (v5z4)'"))
for f in ['run_window.sh', 'run_height.sh']:
    s = open(Z3 + f).read().replace('/zfast/atlas_v5z3', '/zfast/atlas_v5z4').replace('cd atlas_v5z3', 'cd atlas_v5z4').replace('atlas_v5z3/runs/v5z.log', 'atlas_v5z4/runs/v5z.log')
    open(Z4 + f, 'w').write(s); os.chmod(Z4 + f, 0o755)
open(Z4 + 'THEORY_V5Z4.md', 'w').write('''# atlas_v5z4 = atlas_v5z3 with a deterministic N_win (2026-10-20)

**Defect found at 10²³.** The replay requires the rebuilt model (vars, window, N_win) to equal the certificate's exactly. That is
correct and is kept. N_win = up(count_upper5(window).upper()), and count_upper5 encloses (θ(y) − θ(x))/π + 2S_max(y) in Arb **at the
ambient ctx.prec**.

The frozen sech engine (`certify_sech_interferometer._init`, called on the first row measurement of a process) sets ctx.prec = 256
and never restores it. So:
- a model built before the first row measurement used 128 bits (integer_mechanism's import-time setting);
- a model built after it used 256 bits.

At 10²³, θ ≈ 2.5·10²⁴ ≈ 2⁸¹, so the 128-bit enclosure is about 2·10⁻¹⁴ wider, and its binary64 upper bound is 59.77123605871552
instead of 59.7712360587155 (`runs/m5/nwin_prec_leak.json`). **Both are valid upper bounds; nothing unsound was certified or
accepted.**
- The generator measures rows first, so it used 256 bits.
- The replay built cert p0's model first (128 bits): mismatch, rejected.
- The replay then measured rows, so cert p100 was built at 256 bits: match.

At 10¹⁶, 10²⁰ and 10²² both precisions give the same double, so no earlier certificate was affected.

**Fix (the only trusted change).** count_upper5 now evaluates at the fixed precision 256 + bitlen(T0), restoring ctx.prec afterwards.
- It encloses the same real number as before, so it is valid for the same reason.
- N_win is now a deterministic function of (T0, window), independent of call order and of the engine's side effect.
- The enclosure error is ≈ 2^(bits(θ) − 256 − bitlen T0) ≤ 2⁻²⁵⁰ at any height.
- The far-bound shell counts use the same function and become deterministic too. The replay recomputes them, so they were never
  compared.

The frozen engine and v5's other files are unchanged; every other file is a byte copy of atlas_v5z3.
''')
print('ok')
