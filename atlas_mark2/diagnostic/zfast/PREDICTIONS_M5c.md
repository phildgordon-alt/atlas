# M5c: review2 fixes (v13b) — predictions written before building or measuring v13b (2026-10-19; sha in PREDICTIONS_M5c.sha256)

v13b = v12a plus the review2 fixes:
- **m1:** `ok = 0` rows return indeterminate balls (zf_row, zfm_row2, zfm_row3);
- **m2:** the session guards 2 ≤ J ≤ 32, t0 − H > 1000, N_w < 2⁵², and the H/Δ range;
- **m3:** the head is extended so that no bucket remainder shorter than 2(J + 1) reaches a block;
- **m4:** the APIs print full balls (ARB_STR_MORE).

Provider v5z3 is the v5z2 provider re-pinned to libzfast.v13b. A new frozen tree is `atlas_v5z3/`.

**Note.** The 10²¹ and 10²² windows were certified with v12a *before* review2's message arrived. Review2 found nothing in v12a that
could make a certificate wrong:
- m1 rows are refused (rc −3 → RuntimeError);
- the m2 conditions hold at J = 12 and N ≤ 1.3·10¹¹;
- m3 is a crash only.

As instructed, they are re-certified with v13b. The v12a runs are reported as superseded, not as the claim.

| # | prediction | criterion |
|---|---|---|
| X1 | m1 trigger (T0 = 999998594275, u = u_jump ± 1e-9; review2's case): v13b rows are indeterminate (non-finite), and the provider raises | FAIL if finite |
| X2 | m2 guards: J = 40 aborts; T0 + u0 − H ≤ 1000 aborts; production parameters do not abort | FAIL otherwise |
| X3 | Containment against stored Arb references: Z sessions 136/136 (10¹⁰–10¹⁶) plus the 10¹⁸/10²⁰/10²¹ Arb points; rows 38/38 against the Arb jets | any miss = FAIL |
| X4 | v13b values equal to v12a values (midpoints) at every point where m3 does not trigger; radii of printed balls smaller (m4) | point prediction |
| X5 | atlas_v5z3 reproduces y_1e16 and h_1e20 (and hp_1e20) with **identical** intervals; margins differ ≤ 1e-9 (tighter printed balls) | interval mismatch = FAIL |
| X6 | Re-certification with v5z3 of [10²¹, +2], [10²¹ − 6, −4], [10²², +2], [10²² + 17, +19]: closed (A)+(B), the same counts as v12a and as the Turing counts; intervals identical to the v12a runs | mismatch = stop |
