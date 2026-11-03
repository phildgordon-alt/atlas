# atlas_v5z4 = atlas_v5z3 with a deterministic N_win (2026-10-20)

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
