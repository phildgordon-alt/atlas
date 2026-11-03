# MARGIN_ANATOMY: what the "min margin" of the zfast RH windows is made of, 1e16 → 1e24 (2026-11-01)

Diagnostic study. Nothing frozen was modified; no certificate is changed, re-issued or re-claimed. Light compute only
(about 10 s of Arb plus a few seconds of floats, one thread, nice 19).

- Tools (new, not in any trust path): `tools/margin_decomp_v1.py`, `tools/tight_margin_v1.py`, `tools/margin_anatomy_v1.py`.
- Outputs: `runs/roadmap_margin/decomp_v1.jsonl` (76 main certificates, 1e12–1e24), `tight_v1.jsonl` (76),
  `anatomy_v1.jsonl` (31 distinct main certificates, 1e16–1e24, with scan-based far-zero split and combination swap test).
- Inputs read: every `atlas_v5z{2,3,4}/runs/w*/*/certs/cert_p*.json`, its run's `gen_measurements.json`, and the non-rigorous
  scan zero lists `runs/m5/scan2_1e{16,20,21,22,23}/zeros_intervals.json`, `runs/m6/scan3_1e24/zeros_intervals.json`
  (used only to explain terms, never as a certificate input).

## 0. Answer first

1. **The reported number is mostly not margin.** `min_candidate_lower` (verify_zs5.check, `atlas_v5z4/lib/verify_zs5.py` lines 66–81)
   is the minimum lower bound over the *first* bisection leaves whose Arb lower bound became positive. The verifier stops
   splitting a candidate box as soon as it passes. So the number is "true worst-case slack minus an interval-arithmetic
   overestimate at the stopping box size". A branch-and-bound to 1e-3 with the same Arb box formula gives the true value.
   - True certified slack at 1e24: **≥ 1.0888** (all four 1e24 main certificates; reported 0.6145–0.761).
   - True at 1e20: ≥ 1.1449 (reported 0.7726). At 1e23: ≥ 1.0876 (reported 0.6132).
   - The gap (true − reported) is a constant of the dual combination, not of height: **0.366–0.373** for combination A
     (y_up ≈ [0.985, 0.012, 0.003]) and **0.475** for combination B (y_up ≈ [0.479, 0.263, 0.258]); 76/76 certificates,
     tight ≥ reported in every case.
2. **The 1e24 "drop" (0.729 → 0.616) is a combination switch, not height and not the close pair.**
   Δreported = −0.113 = **−0.102 from the verifier artifact** (A's 0.373 → B's 0.475) **+ −0.012 real** (1.102 → 1.090).
   The LP picks B on pieces whose window edges are crowded from outside (zeros within 0.014–0.046 of *both* edges, 17–18
   zeros in the two 1-unit outer strips). The same switch already happened at 1e23: `wr_1e23` piece p-200_-100 reports
   **0.613** at 1e23. The close-pair piece at 1e24 (wp_1e24 p-200_-100, contains the δ ≈ 0.12 pair) is an A piece with true
   slack 1.123, better than average. So zero spacing *inside* the window is irrelevant; spacing *just outside the edges*
   decides A vs B and costs ~0.01–0.03 of real slack.
3. **The real decline is the far-zero term, linear in L = log(T/2π).** True slack = Pc − far − resid with Pc fixed by the
   kernel (1.490 for A, 1.300 for B), resid ≈ 0.005, and far ≈ 0.0068·L. Fit over 37 combination-A certificates
   (1e12–1e24): **true slack ≈ 1.481 − 0.0070·L** (σ = 0.021). That is about −0.016 per decade, with no acceleration.
4. **Projection (current engine, unchanged parameters).** True worst-piece slack ≈ 1.07 (1e25), 1.05 (1e26), **1.00–1.04 (1e28)**;
   the frozen verifier would *report* about 0.55–0.67 at 1e28. The true slack reaches 0 near L ≈ 212, T ≈ 10^92.
   **Margin is not a limit for HIK's 1e28 window.** The binding limit there is cost (√T per zfast session).
5. **Which engine change recovers the most margin:** widening the LP window (WM 2 → 3) recovers about **+0.27–0.30** of real
   slack (upper bound from the scan zeros); a tight candidate bound in the verifier report recovers 0.37–0.48 of *reported*
   number (no real change). A cited-bounds library recovers **0**: Nwin and the Trudgian far allowance F carry zero
   multipliers in every main and S-layer certificate 1e12–1e24 (y_c = 0, y_low = 0, checked). More rows: unmeasured, at most
   modest (Pc/K is already set by the 1.6-kernel).

## 1. Definitions (THEORY_ZSIGN §2, all main certificates have y_low = 0, y_c = 0)

margin(C) = min over region [x0,x1] × [0,½] of Φ(x,d,2) − K + Σw, with Φ(x,d,f) = f·Σ_j y_j Re sech(a_j(x − t_j − i d)),
K = Σ_j y_j Ehi_j (normalisation Σ y_j = 1 in the generator LP, `lib/gen4.py` solve_cg).

Write γ_i for the credited zeros (one per sign-change interval) and split K = Σ_i Φ(γ_i) + far. Then exactly

  margin = **Pc** − **far** − **resid**,  Pc = min_region Φ(·,·,2),  resid = Σ_i (Φ(γ_i,0) − w_i) ≥ 0.

- far = (zeros outside the LP window, weighted by Φ) + (mirror terms, negligible) + (Ehi − E, ball overhead).
  Check: far from K and far summed from the scan zeros agree to ≤ 1e-3 in all 25 certificates with a scan (table §2).
- Ball radius: Ehi − Elo ≤ 1.0e-6 per row, so the ball overhead is ≤ 5e-7. Negligible.
- Nwin (43 at 1e16 → 62 at 1e24) does not enter: y_c = 0.

## 2. Term table (distinct main certificates, 1e16–1e24; floats except "tight"; A/B = dual combination)

Columns: Pc, far (from K), far split by distance of the outside zero from the nearer window edge (0–0.5 / 0.5–1 / 1–2 / >2),
resid, sampled (generator's own float min), tight (Arb branch-and-bound lower bound), reported (`min_candidate_lower`),
swap = float margin of the *other* fixed combination on the same rows and intervals, nL/nR = distance of nearest outside zero.

| cert | piece | comb | Pc | far | 0–.5 | .5–1 | 1–2 | >2 | resid | tight | reported | swap A / B | nL / nR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| z_1e16 | p0_100 | A | 1.490 | 0.288 | 0.171 | 0.065 | 0.043 | 0.009 | 0.003 | 1.198 | 0.826 | 1.201 / 1.150 | .010 / .042 |
| z_1e16 | p100_200 | A | 1.490 | 0.281 | 0.174 | 0.056 | 0.040 | 0.010 | 0.003 | 1.205 | 0.833 | 1.208 / 1.154 | .042 / .058 |
| z_1e18 | p0_100 | A | 1.490 | 0.304 | – | – | – | – | 0.004 | 1.181 | 0.809 | 1.185 / 1.142 | – |
| h_1e20 | p0_100 | A | 1.490 | 0.319 | 0.184 | 0.075 | 0.048 | 0.012 | 0.004 | 1.166 | 0.794 | 1.170 / 1.135 | .114 / .198 |
| hp_1e20 | p500_600 | A | 1.490 | 0.340 | 0.200 | 0.078 | 0.049 | 0.013 | 0.004 | 1.145 | 0.773 | 1.149 / 1.123 | .006 / .106 |
| h_1e21 | p100_200 | A | 1.490 | 0.343 | 0.183 | 0.085 | 0.063 | 0.012 | 0.004 | 1.142 | 0.769 | 1.146 / 1.122 | .014 / .058 |
| h_1e22 | p100_200 | A | 1.490 | 0.365 | 0.220 | 0.085 | 0.046 | 0.014 | 0.004 | 1.120 | 0.748 | 1.125 / 1.111 | .050 / .022 |
| h_1e23 | p0_100 | A | 1.490 | 0.383 | 0.210 | 0.099 | 0.057 | 0.017 | 0.005 | 1.102 | 0.729 | 1.106 / 1.101 | .130 / .006 |
| hp_1e23 | p300_400 | A | 1.490 | 0.386 | 0.223 | 0.083 | 0.067 | 0.013 | 0.005 | 1.099 | 0.726 | 1.103 / 1.100 | .154 / .038 |
| wr_1e23 | p-200_-100 | **B** | 1.300 | 0.207 | 0.123 | 0.048 | 0.029 | 0.007 | 0.004 | 1.088 | **0.613** | 1.090 / 1.092 | .030 / .030 |
| w_1e24 | p0_100 | **B** | 1.300 | 0.205 | 0.119 | 0.050 | 0.029 | 0.007 | 0.005 | 1.090 | **0.616** | 1.094 / 1.095 | .030 / .046 |
| w_1e24 | p100_200 | A | 1.490 | 0.351 | 0.172 | 0.104 | 0.059 | 0.016 | 0.005 | 1.133 | 0.761 | 1.138 / 1.119 | .098 / .106 |
| wp_1e24 | p-200_-100 (close pair) | A | 1.490 | 0.362 | 0.193 | 0.090 | 0.063 | 0.016 | 0.005 | 1.123 | 0.750 | 1.128 / 1.113 | .138 / .058 |
| wp_1e24 | p-300_-200 | **B** | 1.300 | 0.206 | 0.110 | 0.060 | 0.028 | 0.008 | 0.005 | 1.089 | **0.614** | 1.092 / 1.094 | .014 / .038 |

Full rows (31 certificates, incl. 1e17, 1e18, 1e21 pairs, wq_1e23, Nwin, row ids, y, K, Σw, ball radii) are in
`runs/roadmap_margin/anatomy_v1.jsonl`.

**Reading.**
- **Pc is constant** (1.490 A, 1.493 for the 4-row variant, 1.300 B). It is a property of the kernel, not of height.
- **far is the only term that moves with height**, and ~60 % of it comes from zeros within 0.5 of the window edges, ~25 % from
  0.5–1. It grows like the zero density L/2π: far/L = 0.0059–0.0082 over all 37 A-certificates.
- **resid** (credited zeros not exactly at the minimum of Φ on their interval) is 0.003–0.005, growing ∝ L, negligible.
- **swap test.** On B pieces A would give 1.090–1.094 and B gives 1.092–1.095 (float): the LP is right to switch, and the
  real difference is ~0.002. On A pieces B would be 0.004–0.05 worse. B down-weights the 1.6 kernel, whose tails see the
  crowded outside zeros; it pays with a lower Pc (1.300). Its interval-arithmetic overestimate at the stopping box is larger
  (0.475 vs 0.373), which is what made the *reported* number fall.

## 3. Was the 1e24 drop zero spacing or height?

| test | result |
|---|---|
| Same height, other pieces | w_1e24 p100_200 reports 0.761 and wp_1e24 p-200_-100 reports 0.750: in the old 1e22–1e23 band. Only the two B pieces report 0.61. |
| Lower height, same combination | wr_1e23 p-200_-100 (B) reports **0.613 at 1e23**, i.e. the "1e24 level" one decade earlier. |
| Close pair | The 1e24 close pair (δ ≈ 0.12) sits in wp_1e24 p-200_-100, an A piece with true slack 1.123. Close pairs inside the window cost nothing (each gets its own credit). |
| True slack across the switch | 1e23 min 1.0876 (wr, B) → 1e24 min 1.0888 (wp, B): **no real drop**. A pieces: 1.099–1.145 (1e23) → 1.123–1.133 (1e24). |
| Configuration that triggers B | All three B pieces: outside zeros within 0.014–0.046 of *both* edges, 17–18 zeros in the 1-unit outer strips (A pieces: 13–17, usually one edge clear). |

**Verdict:** local zero configuration just outside the LP window (not inside it, not the close pair) selects combination B;
B's larger verifier overestimate produces the reported drop. Height contributes only the steady −0.016/decade. The
PREDICTIONS_M6 miss (W24 margin band [0.67, 0.75]) was a miss of a metric that mixes slack with a bisection artefact.

## 4. Projection (assumptions stated)

Assumptions: same engine (atlas_v5z4), same kernels {1.6, 2.8} and window ±2 (WM = 2), same piece size 1; the zero density
grows as L/2π and the local edge fluctuation stays as observed (σ ≈ 0.021 per piece, B pieces ≈ 0.02–0.04 below the A trend).
Fit: true slack(A) = 1.481 − 0.0070·L (37 certificates, L ∈ [25.8, 53.4]); this is an extrapolation in L by ≤ 9 units.

| height | L | true slack, trend (A) | worst piece (−2σ or B) | frozen verifier would report |
|---|---|---|---|---|
| 1e24 (observed) | 53.42 | 1.107 | 1.089 (observed) | 0.614 (observed) |
| 1e25 | 55.73 | 1.091 | ≈ 1.05–1.07 | ≈ 0.58–0.72 |
| 1e26 | 58.03 | 1.075 | ≈ 1.03–1.05 | ≈ 0.56–0.70 |
| 1e28 | 62.63 | 1.043 | ≈ 1.00–1.02 | ≈ 0.53–0.67 |
| zero crossing | ≈ 212 | 0 | — | T ≈ 10^92 (true); the reported value never decides closure |

The frozen verifier certifies whenever the true slack is positive (it bisects deeper; maxdepth 48 is far from binding at
these widths), so the reported value is not the closure criterion.

## 5. Which engine change buys the most margin

| change | effect on true slack | effect on reported number | evidence | cost / risk |
|---|---|---|---|---|
| **Wider LP window** (WM 2 → 3; window = piece ± 3) | **+0.27–0.30** (removes the 0–1 strips of far; upper bound, LP re-opt and new resid ~0.001/zero subtract a little) | same + | scan-zero split, §2 columns 0–.5 and .5–1 | ~+40 % var boxes and intervals per piece; Z already in session range [c−4, c+4] → set H = 5 or 6 in a new provider version |
| WM 2 → 4 | +0.33–0.36 | same + | §2, 1–2 column | session H ≥ 6 |
| **Tight candidate bound in the report** (branch-and-bound to 1e-3, report alongside the frozen value) | 0 | **+0.37–0.48** | tight_v1.jsonl, 76/76 | trivial; a new diagnostic or a new verifier version; frozen verifier untouched |
| More rows / kernels (e.g. 2.2, off-centre 1.6) | unmeasured; the LP already chooses among 3–4 rows | — | — | LP cap fine (pieces ~1e5 cells) |
| Cited-bounds library (better S(T) / N(T) constants) | **0** for these certificates (y_c = 0, y_low = 0 everywhere) | 0 | decomp_v1.jsonl, np certs checked | would matter only if signed rows (y_low > 0) are introduced; the Hasanalizade–Shen–Wong 2022 constants were not needed and not checked |
| Local-count closure (atlas_v4_2 Theorem 1 for Nwin) | 0 unless Nwin ≤ k_W + 1 (LOCAL_COUNT.md §4) | 0 | same | — |

**Recommendation.** Margin needs no rescue before 1e28. If it ever does (or to make B switches rarer), the lever is the window
width, not the bounds. Fix the *reporting* first so that predictions score the right quantity: PREDICTIONS_M7 should pre-register
the tight slack (expected ≈ 1.04 ± 0.05 at 1e28 for the current engine), not `min_candidate_lower`.

## 6. Checked vs inferred

- Checked: identity margin = Pc − far − resid reproduces `sampled_margin` to 1e-4 in all 76 certificates; tight ≥ reported in 76/76;
  far(K) = far(scan) to ≤ 1e-3 in 25/25; y_c = 0 and y_low = 0 in every main and S-layer certificate 1e12–1e24; the verifier's
  stopping rule (code read).
- Inferred: the trend extrapolation (§4); the WM gain is an upper bound from float sums over non-rigorous scan zeros, not a
  re-solved LP; the trigger for B is read from three pieces.
- K in the tight bound uses generator measurements, not replayed values (replay rebuilds them; they agree within balls).
