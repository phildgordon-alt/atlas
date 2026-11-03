# PREDICTIONS_M6: RH windows at 10²⁴ and two more close pairs near 10²³ (written 2026-10-23 before any 10²⁴ measurement; sha in PREDICTIONS_M6.sha256)

Pipeline: the reviewed atlas_v5z4 tree (V5Z4_FREEZE.sha256) with libzfast.v13b, unchanged. New files only: `tools/scan_turing3.py`
(scan_turing2.py pinned to v13b), `tools/turing_extra.py`, `tools/gz_points_m6.py`, `tools/endpoint_margin_m6.py`,
`tools/provenance_m6.py`, `tools/budget_m6.py`, `atlas_v5z4/run_window_m6.sh`, `run_m6_stage1.sh`, `run_m6_stage2.sh`, `run_m6_gz.sh`.
Constraints: nice 19, ZFAST_THREADS=1, footprint ≤ 500 MB (driver kill limit V4_LIM_GB=0.5; scan under a 500 MB watchdog), disk
floor 2 GB (runs are ~1 MB each), nothing deleted or edited in place.

## 0. Error budget at 10²⁴ (re-checked explicitly; `tools/budget_m6.py`)

Facts (THEORY_ZFAST §§5–7, THEORY_M3 §3, review2 §2; the v13b code evaluates these bounds per block in mag_t):
- **Term count.** N = ⌊√((10²⁴ + 65)/2π)⌋ = 398 942 280 401 ≈ 4.0·10¹¹ (not 1.3·10¹²: that figure is 10²⁵'s). N < 2⁵² ≈ 4.5·10¹⁵
  (the m2 guard) and every n is an exact binary64. bitlen(T0) = 80, Arb working precision wp = 414 bits.
- **Phases are exact integers**, so there is no "double-double validity" question for t·log n at any height below the N < 2⁵² limit
  (≈ 10³²). The per-block phase bound is E_ph ≈ 2⁻⁶⁴ + interpolation (≤ 2⁻⁷²) + propagation (≤ 2⁻⁸⁰); the measured per-block maximum at
  10²³ was 5.8·10⁻¹⁹, entering the term bound as 7·E_ph ≈ 4·10⁻¹⁸ ≪ 3.03u.
- **RS remainder** (FLINT zeta_rs_bound, σ = 1/2): ≤ 1.2·10⁻³⁵ at K = 2 and 1.8·10⁻⁵⁸ at K = 4. Negligible.
- **Per-term rounding accumulation** (the only height-dependent floating-point cost). Each moment accumulator is a
  (hi, lo) double-double fed by groups of ≤ 16 double terms. The bound per term for the k = 0 moment is
  m_w·[E_c + 7E_ph + 1.0001u(1+E_c) + 2.01u + γ₁₅(1+E_c)(1+3u) + 2n_g²u²] = 2.49·10⁻¹⁵·n^{−1/2}; the double-double lo-accumulation
  part 2n_g²u² = 2.6·10⁻²⁶ is the only part that a triple-double accumulator would shrink, and it is 10¹¹ times below the rest.
  Summed over n ≤ N (Σ n^{−1/2} ≈ 2√N = 1.26·10⁶) and over the K = 18 Taylor moments at |h|X_b ≤ 0.37, the a-priori Z radius is
  ≈ 8.6·10⁻⁹ (H = 4 production session) to 9·10⁻⁹ (scan session, worst h). Calibration: the same model gives 8.6·10⁻¹⁰ at 10²⁰
  (review2 observed 1.1–1.3·10⁻⁹) and 5·10⁻⁹ at 10²³ (scan grid radii observed 3.9–9.9·10⁻⁹, median 7.1·10⁻⁹); the radii scale as
  √N ∝ T^{1/4}.
- **Need.** Signs at sign-change endpoints: the linearized endpoint |Z|/radius at 10²³ is ≥ 3.3·10³ (`endpoint_margin_m6`,
  min over both windows); dividing by 3.16 for 10²⁴ leaves ≥ 10³. Rows enter with margins ≈ 0.7 against radii ≈ 10⁻⁸.
- **N_win** (model5.count_upper5, v5z4): fixed precision 256 + 80 = 336 bits, θ(10²⁴) ≈ 2⁸⁴, enclosure error ≈ 2⁻²⁵². Deterministic.

**Conclusion.** The double-double accumulation bound is met at 10²⁴ with about three orders of magnitude to spare; the radius is
rigorous at any height and only its size matters for closure. **Triple-double accumulation is not needed and would not help**: the
dominant terms are per-term double roundings (kernel, products, group sums), not the accumulator. No new source is built.
Trigger for revisiting: any endpoint sign undecided (generator fails to close with "undecided" intervals) or a scan grid point with
|mid| ≤ rad; then the fix would be double-double products/kernel, not a triple-double accumulator.

## 1. Predictions

| # | prediction | criterion |
|---|---|---|
| B1 | 10²⁴ scan (H = 61, Δ = 0.012, K = 18, v13b): grid radii in [1.0·10⁻⁸, 4.0·10⁻⁸], max ≤ 4·10⁻⁸ (√10 × the 10²³ values); 0 undecided grid points; session `Nw` = 398942280401, `max_phase_err` ≤ 10⁻¹⁷ | outside the range = the budget model is miscalibrated (report; not a soundness issue) |
| B2 | Linearized endpoint margin (`endpoint_margin_m6`) for both 10²⁴ windows: min ratio ≥ 300 | < 300 = MISS (report; the certificates stand regardless, every sign being rigorously decided) |
| C1 | Turing cross-count at 10²⁴: all window ends pinned (U − L ∈ [0.45, 0.62]); N(10²⁴) and N(10²⁴ + 2) within 3 of 8343565023546958629481544.16 and …561.17 (θ/π + 1) | a non-pinned end = report; a count differing from the certified sign-change count = STOP |
| W24 | [10²⁴, 10²⁴ + 2] closes (A) + (B): 16–19 sign changes (mean 17.0), count = Turing count, both main certificates pass plain + hardened + independent replay, 0 seams, min margin ∈ [0.67, 0.75] (trend 0.729 − 0.02) | any replay failure = STOP and diagnose before anything else |
| P24 | The 10²⁴ scan's closest pair in [T − 20, T + 22] has δ ≤ 0.20 (previous heights 0.042–0.161); its window closes with the same checks; the pair is certified (both zeros on the line, simple) | δ > 0.25 = MISS (report) |
| Q23 | Two more 10²³ windows from scan2_1e23: wq_1e23 = [10²³ − 24, 10²³ − 22] (pair at −23.29, δ ≈ 0.098, tied with the certified pair) and wr_1e23 = [10²³ − 2, 10²³] (pair at −0.95, δ ≈ 0.163; makes [10²³ − 2, 10²³ + 4] a contiguous certified interval): both close (A) + (B); 17 and 17 sign changes (the scan's interval counts); Turing counts (`turing_extra` on the saved scan, Δ = 36 at −24) equal 17 and 17 with all ends pinned; min margins ∈ [0.70, 0.75] | count ≠ 17 = STOP |
| G | GZ (stock FLINT powsum_smooth + Gabcke; review2's `ref`) at 3 grid points of the 10²⁴ scan chosen by the fixed rule of `gz_points_m6.py`: every reference midpoint inside the zfast ball; \|diff\| ≤ 10⁻¹³ (10²⁰: 1.5·10⁻¹⁵) | a reference outside a zfast ball = STOP (soundness) |
| L | Lean audit (formal/export_certs.py --v5 + atlas_audit) for all four windows: 0 violations; 18–21 certificates each (2 main + the S-layer ones) | any violation = STOP |
| T | Costs on ONE thread (10²³ session = 3025 s on 2 threads; ×1.9 for one thread, ×3.16 for N): scan 10²⁴ ≈ 18 500 s (range 12 000–30 000); each 10²⁴ window pipeline ≈ 36 000 s + independent replay ≈ 18 000 s (range ×0.6–×1.6); each 10²³ window ≈ 11 500 + 5 800 s; total zfast ≈ 45 h. GZ ≈ 1.6–2.0·10⁵ s per point (0.4–0.5 µs/term; 10²¹: 0.36), ≤ 10 MB | > 2× over = MISS (report) |
| M | Peak footprint per process ≤ 0.3 GB (10²³: 0.19 GB); no watchdog kill | a kill = report and re-plan |

Order: stage 1 (scan) → inspect → stage 2 (w_1e24, wp_1e24, wq_1e23, wr_1e23 with Lean audits) and, in parallel, the single GZ
process (3 lines, sequential). Hand-back after stage 2; GZ points still running are reported as pending.
