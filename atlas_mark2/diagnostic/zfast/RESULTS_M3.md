# zfast M3 results: window sessions by bucketed Taylor moments (2026-10-19)

- Theory: `THEORY_M3.md` (sha e58fe536…). Predictions: `PREDICTIONS_M3.md` (sha 70eccf25…), both written before the M3 code.
- Code: `src/v10/zfast_m3.inc`, built as **v10a** (`bin/zfm_cli.v10a`, sources in `bin/src_v10a/`). It is appended to v9
  unchanged.
- Data: `runs/m3/`.
- Defaults: H = 3 (a session covers t0 ± 3, which is v5's search span [−2, 4] around a target [T, T + 2] with t0 = T + 1),
  Δ = 0.2, K = 16, J = 12, 2 threads. The machine was shared with other agents' jobs.

Prior art (cited): the moment stage is that of Odlyzko–Schönhage / Platt 2017. FLINT's development branch computes the same bucket
moments in dfloat arithmetic (`_platt_smk`, 2026-10-02). zfast's version is an independent implementation on exact fixed-point
phases. Its points are evaluated directly from the moments, with no FFT grid and no band-limited interpolation, which is sufficient
for windows of about 6 units.

## Scoring

| # | result | verdict |
|---|---|---|
| R1 session Z against single-point zfast v9, 100 points per height at 10¹⁰, 10¹³, 10¹⁶ over [t0 − 3, t0 + 3] (window ends included) | 300/300 overlap; max \|diff\| 2.4e-15 | **MET** |
| R2 session Z against Arb (stored M2 references with u ∈ [−2, 4], 10¹⁰–10¹⁶) | 136/136: Arb's ball lies inside the session ball | **MET** |
| R3 N-jump windows (t0 = 2πM², 10¹² and 10¹⁴; points at ±1e-7, ±1e-3, ±1, ±2.9 from the jump and random) | 40/40 overlap; both N values occur in each window | **MET** |
| R4 row sessions (a = 2.8, 1.6) against Arb jets (38 points, 10¹⁰–10¹⁵) and against single-point zf_row (12 points, 10¹⁶) | 38/38 contained (ζ, ζ′, P); max \|ΔP\| 1.5e-17; 12/12 overlap | **MET** |
| R5 session radius ≤ 3 × single-point radius | max ratio 2.96 (10¹⁰), 2.57 (10¹³), 2.48 (10¹⁶) | **MET** (just) |
| R6 costs at 10¹⁶ (2 threads) | Z session build 1.27 s = 3.8 single Z (predicted 3–5); point 0.16 ms (≤ 10 ms); row session 1.44 s = 4.3 Z (predicted 6–10: cheaper than predicted); row point ≤ 4.6 ms (≤ 30 ms) | **MET** (rows beat the prediction) |
| R7 10¹⁸ actual | Z session 10.9 s; row session 11.4 s; Z point at 10¹⁸ + 0.40625 against Arb (`powsum_smooth`, M2): diff 4.7e-16, radius 3.8e-10 | **MET** |

## Per-window zfast cost (v5 claim)

One Z session, two row sessions (a = 2.8 and 1.6), and about 1300 point evaluations (Z points at about 0.2–2 ms, row points about
5 ms). Times are for 2 threads; on one core multiply the session part by about 1.6.

| height | sessions | points | zfast total per window | v5 as run with Arb |
|---|---|---|---|---|
| 10¹⁶ | 4.1 s | ≈ 3 s | **≈ 7 s** | 2.5 h pipeline (Z + jets ≈ 2.3 h of it) |
| 10¹⁸ | 33.7 s | ≈ 3 s | **≈ 40 s** | ≈ 37 h projected |
| 10²⁰ | ≈ 5.5 min (×10 per 2 decades) | ≈ 3 s | ≈ 6 min | ≈ 15 days |
| 10²² | ≈ 55 min | ≈ 3 s | ≈ 1 h | ≈ 150 days |

**Caveat.** These are the ζ-evaluation costs only. A v5 window also contains:
- the LP and cutting planes;
- the Arb prime-side sums S_M of the sech rows (10⁶ prime powers per row, in Arb);
- the far-bound counts;
- the exact tiling;
- the Lean audit.

At 10¹³ these were about 10 % of the pipeline. With ζ now nearly free, they become the dominant cost. M4 measures this.
