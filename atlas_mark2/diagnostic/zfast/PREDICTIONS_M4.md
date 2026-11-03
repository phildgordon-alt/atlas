# M4 predictions: atlas_v5z re-certification and new windows (2026-10-19, before any v5z run; sha in PREDICTIONS_M4.sha256)

atlas_v5z is frozen in `atlas_v5z/V5Z_FREEZE.sha256` (28 files, including libzfast.v10b and its sources). The protocol is
`atlas_v5z/THEORY_V5Z.md` §3. Runs are sequential, nice 19, with 2 zfast threads and v5's 2.5 GB watchdog. My own cap is a 1 GB
footprint, so any run that exceeds 1 GB is reported as a rule breach.

| # | prediction | criterion |
|---|---|---|
| S1 | Control [10¹², +2] and the five re-runs [10¹³, +2], [10¹⁴, +2], [10¹⁵, +2], [10¹⁵ + 286, +288], [10¹⁶, +2] all close (A) and (B), with the same sign-change counts as the originals (9, 9, 10, 10, 10; control 8) and a one-to-one interval match | any mismatch = FAIL (stop and report; no new heights) |
| S2 | Plain + hardened + independent replay pass; tiling 0 seams; Lean audit 0 violations, for all six | FAIL otherwise |
| S3 | min_candidate_lower equals the original to ≤ 1e-6 absolute (rows move by ≤ 1e-10) | point prediction |
| S4 | v5z pipeline wall per window: ≤ 4 min at 10¹³–10¹⁵, ≤ 6 min at 10¹⁶ (originals 344 s / 1078 s / 3143 s / 8874 s); independent replay ≤ 3 min | point predictions |
| S5 | Peak footprint per window ≤ 0.6 GB (dominated by the v5 Python/LP, not ζ) | > 1 GB = rule breach |
| S6 | [10¹⁷, +2] closes (A)+(B) (80 %); min margin ≈ 0.79; about 11–12 sign changes; wall ≤ 10 min | reported |
| S7 | [10¹⁸, +2] closes (A)+(B) (70 %); margin ≈ 0.75; about 12 sign changes; wall ≤ 20 min | reported |
| S8 | Arb's Turing count (acb_dirichlet_zeta_nzeros) under the 950 MB watchdog: available at 10¹⁷ (40 %) and at 10¹⁸ (20 %); if available, it equals the v5z count | a mismatch = stop and investigate |
