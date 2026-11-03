# M5 final: RH windows at 10²⁰, 10²¹ and 10²² with close pairs, re-certified with the review2-fixed zfast v13b (2026-10-19)

This supersedes nothing that is unedited. It summarizes RESULTS_M5_1e20.md and RESULTS_M5_1e21.md and adds 10²² and the review2
follow-up.

## 0. The claimed certificates and the exact code (for review)

**The claim** is the **atlas_v5z3** runs (`zfast/atlas_v5z3/runs/…/x_*`, `xp_*`):
- frozen tree `atlas_v5z3/` (V5Z3_FREEZE.sha256, 30 files);
- provider `lib/zfast_provider.py`, pinned to **`bin/libzfast.v13b.dylib`** (sha 82489d1a…; sources `bin/src_v13b/`).
- v13b = v12a (reviewed by review2: no critical findings) plus the review2 fixes m1–m4. Generated from `src/v12` by scripted
  replacements, then `src/v13` → `src/v13b`, with the corrected m3 clause.
- Every run dir has `provenance.json`.

The v12a runs of the same windows (`atlas_v5z2/runs/…/h_*`, `hp_*`) were made before review2's message. They are **superseded**;
their intervals and margins are identical (X6).

**Validation of v13b (PREDICTIONS_M5c, sha aa6dc3b7…)**

| # | result | verdict |
|---|---|---|
| X1 | review2's m1 trigger (T0 = 999998594275, ±1e-9 from the N jump): rows ok = 0, P = NaN (indeterminate); 0.5 away: ok = 1, a finite ball | **MET** |
| X2 | J = 40 aborts ("J out of range"); t0 − H ≤ 1000 aborts; production parameters run | **MET** |
| X3 | session Z inside the stored Arb balls: 139/139 (10¹⁰–10¹⁶, 10¹⁸, 10²⁰, 10²¹); rows inside the Arb jets: 38/38 | **MET** |
| X4 | midpoints identical to v12a at 139/139; printed radii median 0.52 × v12a's (m4) | **MET** |
| X5 | v5z3 reproduces [10¹⁶, +2] and both 10²⁰ windows with identical intervals and identical min_candidate_lower | **MET** |
| X6 | v5z3 re-certifies the four 10²¹/10²² windows: closed (A)+(B), identical intervals and margins to the v12a runs | **MET** |

## 1. Certified windows (atlas_v5z3, zfast v13b; all closed (A) and (B), with independent replay, 0 tiling seams and 0 Lean violations)

| window | zeros (sign changes) | Turing count (separate method; v12a scans) | min margin | closest pair in the window, δ | pipeline + independent replay (2 threads) | Lean certificates |
|---|---|---|---|---|---|---|
| [10²⁰, 10²⁰ + 2] | 13 | 13 (N(10²⁰) = 687769382578810314775) | 0.794 | [0.1034, 0.1045] | 200 s + 98 s | 15 |
| **[10²⁰ + 4, 10²⁰ + 6]** | 14 | 14 | 0.773 | **[0.0418, 0.0429]** | 200 s + 99 s | 16 |
| [10²¹, 10²¹ + 2] | 15 | 15 (N(10²¹) = 7244161625227817018173) | 0.769 | [0.563, 0.565] | 615 s + 306 s | 17 |
| [10²¹ − 6, 10²¹ − 4] | 15 | 15 | 0.794 | **[0.1602, 0.1614]** | 614 s + about 306 s | 17 |
| **[10²², 10²² + 2]** | 16 | 16 (N(10²²) = 76106294246675308886088, N(10²² + 2) = …104) | 0.748 | [0.3715, 0.3727] | 1925 s + 960 s | 18 |
| **[10²² + 17, 10²² + 19]** | 16 | 16 (N(10²² + 17) = …220, N(10²² + 19) = …236) | 0.769 | **[0.1196, 0.1208]** | 1927 s + 960 s | 18 |

**Closest pairs certified** (each zero on the critical line and simple):
- **10²⁰:** γ ∈ 10²⁰ + [4.719375, 4.719453] and 10²⁰ + [4.725391, 4.725469]. Gap ∈ [0.005937, 0.006094], **δ ≈ 0.042**: about 1/24
  of the mean spacing.
- **10²¹:** γ ∈ 10²¹ − [5.137109, 5.137031] and 10²¹ − [5.115391, 5.115313]. Gap ∈ [0.02164, 0.02180], δ ≈ 0.161.
- **10²²:** γ ∈ 10²² + [18.458203, 18.458281] and 10²² + [18.473672, 18.473750]. Gap ∈ [0.01539, 0.01555], δ ≈ 0.120.

The scans covered 122 units around each height (860, 903 and 946 zeros located, 0 undecided points). Pairs were searched in
[T − 20, T + 22].

**Zeros of [10²², +2]** (midpoints, widths ≤ 7.8e-5): 0.06730, 0.25738, 0.35105, 0.45152, 0.53340, 0.67832, 0.82465, 0.87262,
0.98230, 1.10973, 1.34168, 1.38957, 1.55152, 1.63559, 1.80246, 1.95762.

**Margins.** The trend continues at about 0.025 per decade: 0.83 (10¹⁶) → 0.809 (10¹⁸) → 0.794 (10²⁰) → 0.769 (10²¹) → 0.748
(10²²).

**Turing cross-count (separate method).** For every window end, U − L = 0.41–0.49, so every N is pinned and every window count
equals Atlas's certified count. The method was validated at 10¹⁶ against Arb's N.
- The scans used libzfast.v12a (`tools/scan_turing2.py`). Review2 found no defect in v12a affecting Z values, and v13b's Z midpoints
  are identical (X4).

## 2. Scoring PREDICTIONS_M5 (f104fab0…)

- **V1:** overlap MET; cost MISSED → v12.
- **V1b–V1d:** MET.
- **V2:** MET. **V3:** MET.
- **V4:** MET at 10²¹ (Arb 4525 s).
- **W20–W22:** MET; margins 0.794 / 0.769 / 0.748 against predicted 0.78 / 0.75 / 0.72, so slightly better.
- **W23:** not attempted. Per the coordinator, the hand-back is at 10²².
- **C:** MET; all ends pinned and all counts equal.
- **P:** δ_min = 0.042 / 0.160 / 0.120; 10²⁰ is below the predicted range [0.07, 0.25]. All pair windows closed.
- **T** (per window, pipeline + replay):
  - 10²⁰: 9 + 4.4 min at 1 thread, or 3.3 + 1.6 min at 2 threads (prediction ≈ 8 min: MET);
  - 10²¹: 15.4 min (prediction 25: MET);
  - 10²²: 48 min (prediction 75: MET).
- **M:** MET; peak ≤ 0.1 GB per replay; Arb references ≤ 4.6 MB.

## 3. 10²³ (not done; ready)

- **Precision.** No triple-double is needed (THEORY_M5 §2: exact 256-bit phases; N = 1.26·10¹¹ < 2⁵²; V4 confirms at 10²¹).
- **Projected cost** (2 threads):
  - session about 3200 s;
  - window about 2.5 h (pipeline + replay);
  - scan about 1 h;
  - pair window about 2.5 h;
  - **total about 6 h**.
- An Arb `powsum_smooth` check at 10²³ would take about 11 h single-threaded (it can be run in parallel at the cost of 1 zfast thread).
- To do it: `cd atlas_v5z3; ZFAST_THREADS=2 ./run_height.sh 23`. Note that `run_height.sh` writes a new scan dir
  `runs/m5/scan2_1e23`.

## 4. Novelty (RESULTS_M5_1e20.md §3)

To our knowledge, these 10²⁰–10²² windows are the highest rigorous, unconditional RH windows in published or publicly documented
work. The certified close pair at 10²⁰ + 4.72 (δ ≈ 0.042) is the highest such certified Lehmer-type pair. All the standard caveats
apply:
- Arb/FLINT-dev Turing routines can do this given memory and time;
- non-rigorous computations go to 10³⁶;
- HIK's 10²⁸ window (now Math. Comp. 2026) is conditional;
- the method class is not new;
- zfast is in the trust base (review2: no critical findings for v12a; v13b adds only the fixes);
- the arXiv API was unavailable for the check.
