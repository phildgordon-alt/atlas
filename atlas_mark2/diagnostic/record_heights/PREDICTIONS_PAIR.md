# record_heights — pre-registration for the close-pair window (2026-10-18, written before the Atlas run)

Seen before writing (disclosure):
- the [10^15, +2] and [10^16, +2] windows closed (RESULTS.md);
- the closest pair certified in the 10^16 window has normalised gap δ = 0.20;
- an Arb scan (`cost/platt_scan_1e15.log`; `acb_dirichlet_platt_local_hardy_z_zeros`, Turing method, 1500 zeros from zero
  n = 5 045 354 828 589 586, 112 s, 0.40 GB) found the closest pair at 10^15 + 286.888503… and 10^15 + 286.907311…
  - gap 0.01881, **δ = 0.098**, the only δ < 0.1 among the 1499 gaps;
  - Arb's isolation is rigorous, but Atlas treats it as a scan, not as an input.

Target: [10^15 + 286, 10^15 + 288], exact integer endpoints, T0 = 10^15. Same frozen code (`v5run/`, V5_FREEZE 21/21 OK) and the
same parameters as the 10^15 window: grid v5, evaluator dirichlet, PW = 1, WM = 2, Z step 0.01, refinement 1e-4, timeout 21600 s,
2.5 GB watchdog. Claim definition identical (A, B).

| | prediction | bound |
|---|---|---|
| Q1 sign changes in target = Arb's isolated zeros in (286, 288] | 10 (from the Arb list: 286.0544, 286.1031, 286.5380, 286.6257, 286.8885, 286.9073, 287.0860, 287.5451, 287.7221, 287.7688) | equal |
| Q2 closes (A) and (B) | yes (75 %). Risk: the near-double zero lowers the LP margin; the pair is resolved by the 0.01 grid (gap 0.0188 > step) | reported as is |
| Q3 min_candidate_lower | ≈ 0.75 (lower than 0.86 because of the pair) | > 0 |
| Q4 wall (pipeline + independent replay) | ≈ 65 min | ≤ 2 h |
| Q5 peak | ≈ 0.7 GB | < 2.5 GB |
| Q6 the pair | two disjoint certified sign-change intervals with gap in [0.0186, 0.0190] | both in the target, disjoint |
