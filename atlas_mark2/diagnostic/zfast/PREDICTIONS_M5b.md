# M5 addendum (2026-10-19, after V1 and before any v12 measurement; sha in PREDICTIONS_M5b.sha256)

**V1 outcome (v11).**
- Overlap: 240/240 MET.
- Combined-session cost: 2.4–3.6 × a Z-only session against a predicted ≤ 1.6 ×. **MISSED.** The cause is four Horner weight
  evaluations per term.

**New design, v12 (THEORY_M5b.md).** Rows are evaluated from the *Z moments* (weight n^{-1/2}) at the complex shift
h′ = h ∓ i(σ − 1/2). Lemma M1 holds for complex z with |z| ≤ |h′|X_b. A row costs a point evaluation; no extra moment weights.

| # | prediction | criterion |
|---|---|---|
| V1b | v12 rows-from-Z (kind-0 session, H = 4, Δ = 0.15, K = 18) against v9 single-point rows and v10b row sessions, 20 rows per height at 10¹⁰, 10¹³, 10¹⁶, and against the stored Arb jets (≤ 10¹⁵, M2 data): 100 % overlap; P radius ≤ 10 × the v10b row-session radius | any non-overlap = FAIL |
| V1c | v12 Z values identical to v10b/v11 kind-0 values (same code path) | FAIL otherwise |
| V1d | v12 session cost = Z-only session cost (± 10 %); row point ≤ 20 ms | point predictions |
