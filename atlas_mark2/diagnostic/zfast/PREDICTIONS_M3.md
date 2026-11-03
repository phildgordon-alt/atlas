# zfast M3 predictions (2026-10-19, written after THEORY_M3.md and before any M3 code or measurement; sha in PREDICTIONS_M3.sha256)

Defaults: H = 3, Δ = 0.2, K = 16, J = 12, 1–2 threads.

| # | prediction | criterion |
|---|---|---|
| R1 | Session Z against single-point zfast (v9), ≥ 100 points per height at 10¹⁰, 10¹³, 10¹⁶ spread over [t0 − 3, t0 + 3]: 100 % overlap; actual \|diff\| ≤ 1e-12 | any non-overlap = FAIL |
| R2 | Session Z against Arb (≥ 30 points, 10¹⁰–10¹⁶): 100 % containment of Arb's ball | any miss = FAIL |
| R3 | N-jump windows (10¹², 10¹⁴): 100 % overlap with single-point zfast on both sides of the jump | FAIL otherwise |
| R4 | Session rows (a = 2.8, 1.6) against Arb jets (10¹⁰–10¹⁴) and single-point zf_row (10¹⁶): 100 % overlap | FAIL otherwise |
| R5 | Session radius ≤ 3 × the single-point radius at the same height | point prediction |
| R6 | Z session build ≈ 3–5 single-point Z (10¹⁶: 1.5–3 s on one thread); per-point Z evaluation ≤ 10 ms; row session ≈ 6–10 Z; per-point row ≤ 30 ms | point predictions |
| R7 | Projected per-window zfast cost for a v5 window (one Z session, two row sessions, about 1300 point evaluations): 10¹⁶ ≤ 1 min, 10¹⁸ ≤ 5 min, 10²⁰ ≤ 40 min, 10²² ≤ 6 h (one core), dominated by the moment passes above 10¹⁸ | checked at 10¹⁸ by one actual session |
