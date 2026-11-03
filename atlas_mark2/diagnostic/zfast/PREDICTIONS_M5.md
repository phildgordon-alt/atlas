# M5 predictions (2026-10-19; written after THEORY_M5.md and the v11 dev smoke test at 10¹⁰, before every M5 measurement; sha in PREDICTIONS_M5.sha256)

All results are contingent on the independent review (zfast/review/). Runs: ≤ 2 threads in total, a 1 GB footprint cap, and no
deletions or in-place edits.

| # | prediction | criterion |
|---|---|---|
| V1 | v11 combined session against v10b sessions and single-point v9 at 10¹⁰, 10¹³, 10¹⁶ (Z: 60 points per height; rows: 20 per height): 100 % overlap; combined build ≤ 1.6 × a Z-only session | any non-overlap = FAIL |
| V2 | v5z2 (provider: one combined session per process) re-certifies the six originals (10¹², 10¹³, 10¹⁴, 10¹⁵, 10¹⁵ + 286, 10¹⁶) with **identical** intervals, and reproduces v5z's 10¹⁷/10¹⁸ results (identical intervals) | any mismatch = FAIL, stop |
| V3 | Turing count (Lemma T) at 10¹⁶: pins N(10¹⁶) and N(10¹⁶ + 2) to Arb's values (54118226280292478, …488) | mismatch = FAIL |
| V4 | Arb `powsum_smooth` at 10²¹ (1 point): contained in the zfast single-point and session balls; \|diff\| ≤ 1e-14 | FAIL otherwise |
| W20–W23 | [10^E, +2] closes (A)+(B) with v5z2: E = 20 (85 %), 21 (80 %), 22 (75 %), 23 (65 %); margins ≈ 0.78 / 0.75 / 0.72 / 0.70; 11–13 sign changes | reported |
| C | Turing counts pin N at both ends of every new window (80 % each) and, where pinned, equal v5z2's count (100 %) | mismatch = stop and investigate |
| P | scan min δ over [T − 20, T + 22] ∈ [0.07, 0.25] at each height; pair window closes (75 %) | reported |
| T | cost per window (pipeline + independent replay, 2 threads): 10²⁰ ≈ 8 min, 10²¹ ≈ 25 min, 10²² ≈ 75 min, 10²³ ≈ 4 h; wide scan session ≈ 1–1.5 × a window session plus ≤ 3 min for the grid | point predictions |
| M | peak footprint ≤ 0.3 GB for zfast/v5z2 processes; Arb reference runs ≤ 950 MB (watchdog) | > 1 GB = breach |
