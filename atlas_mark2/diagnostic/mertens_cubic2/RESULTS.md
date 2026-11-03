# mertens_cubic2: RESULTS (2026-10-21)

This closes the six cubic fields left open by ../mertens_cubic/RESULTS.md (MC) for the naive Mertens-type conjecture of
Hu–Kaneko–Martin–Schildkraut (HKMS, arXiv 2109.06665; Math. Proc. Camb. Phil. Soc. 177 (2024) 481–523): −1 ≤ M⁻_K ≤ M⁺_K ≤ 1, where
M^±_K = lim sup / lim inf of M_K(x)/√x.

* Pre-registration: PREDICTIONS.md, sha256 d93e99df0e9a03890444d05ecc40c2c2dffee8bff0e0214ef5a6fb9eb38987d8. It was written before any
  computation and re-checked against PREDICTIONS.sha256.
* Theory: THEORY.md (written before the first use of rmb), plus THEORY_ADDENDUM.md (corrections found in validation).
* Rules followed: nothing outside this directory was modified, apart from one row appended to ../new_territory/TARGETS_LEDGER.md. No file was deleted or overwritten. One heavy process ran at a time, at nice 19, under a footprint watchdog of 1 GB or less; the largest footprint was 446 MB. No one was contacted.

## 0. Summary

**Theorem (six fields).** For each cubic field K below, M⁺_K ≥ h*_{K,T}(y₊) > 1 and M⁻_K ≤ h*_{K,T}(y₋) < −1. So the naive
Mertens-type conjecture fails for K, in both directions.

| K | d_K | defining polynomial | T | y₊ | h*(y₊) (set A; set B) | y₋ | h*(y₋) (set A; set B) |
|---|---|---|---|---|---|---|---|
| K31 | −31 | x³ + x + 1 | 800 | 1042.536553 | 1.06030365165 ± 1.4e−12; same ± 1.4e−12 | 3837.934110 | −1.14484986103 ± 2.6e−12; same ± 2.7e−12 |
| K59 | −59 | x³ + 2x + 1 | 400 | −2235.048720 | 2.36240265548 ± 5.4e−12; same ± 5.6e−12 | −2351.273247 | −2.38859700285 ± 9.3e−12; same ± 9.5e−12 |
| R49 | 49 | x³ − x² − 2x + 1 | 600 | −1852.914676 | 4.911102936 ± 5.8e−10; 4.91110293634 ± 8.2e−12 | −1782.899388 | −4.788483451 ± 3.4e−10; −4.78848345109 ± 5.6e−12 |
| R81 | 81 | x³ − 3x + 1 | 400 | −2361.612858 | 2.132782176 ± 1.0e−10; 2.13278217596 ± 5.7e−12 | 2148.321085 | −2.151701459 ± 3.0e−10; −2.15170145922 ± 3.0e−12 |
| R148 | 148 | x³ − x² − 3x + 1 | 400 | −331.996595 | 1.73152861622 ± 4.9e−12; same ± 5.0e−12 | 1057.021104 | −1.72389656423 ± 6.3e−12; same ± 6.4e−12 |
| R229 | 229 | x³ − 4x + 1 | 400 | 2680.665733 | 1.4421738700 ± 1.9e−11; same ± 1.9e−11 | −1685.897243 | −1.5283516249 ± 2.9e−11; same ± 3.0e−11 |

Notes on the table:
* h*_{K,T}(y) = Σ_{0<γ<T} 2Re[f(γ/T)e^{iγy}/(ρζ_K′(ρ))], with f the Jurkat–Peyerimhoff kernel (HKMS (3.6)).
* Each value is an Arb ball computed at the exact decimal y shown (runs/hcert_all_v1.json, logs/hcert_all_v1.log).
* Fields are written K = complex, R = totally real, followed by |d_K|. The polynomials were checked with PARI nfdisc.

**Combined statement.** Put these six together with MC T1–T5 and HKMS Theorem 1.1. Then **the naive Mertens-type conjecture is false for every
cubic field** (and for every quadratic field: ../corollaries, VERIFY.md).
* Complex cubic fields:
  * |d| ≥ 5178: M*_K(1) > 0 (MC T1);
  * |d| ≤ 5196: certified M*(1) or G(n±) (MC T3/T4);
  * d = −23 (MC T5);
  * d = −31, −59 (here).
* Totally real cubic fields:
  * d ≥ 5230 (MC T2);
  * d ≤ 10⁴ (MC T3/T4);
  * d = 49, 81, 148, 229 (here).
* In every case, either M⁺_K > 1 or M⁻_K < −1 (in the extended reals). For the six fields closed here, both hold.

**Dependencies.** The combined statement relies on MC T1–T4, which no separate agent has re-verified yet (MC §6). This directory
re-verifies only MC's K23 result (T5): see §3, V1.

## 1. Logic (unchanged from MC §1 L2; VH = ../corollaries/verify_hkms/VERIFY.md check 1)

Suppose M⁺_K < ∞ or M⁻_K > −∞; otherwise the claim holds trivially. Then:
* Landau gives RH for ζ_K, with no zero in (½, 1).
* Ingham (1942, Thm 1) with the JP kernel gives M⁻_K ≤ h*_{K,T}(y) ≤ M⁺_K for every real y. This needs:
  * (i) the complete list of zeros of ζ_K with 0 < γ < T, all simple;
  * (ii) ζ and L(ρ_K) share no zero below T;
  * (iii) ζ_K(½) ≠ 0;
  * (iv) no zero at height T.

The totally real signature changes only G(s) = D^{s/2}Γ_R(s)² in L = Λ/G (THEORY §1). The Ingham/Landau argument does not depend on the
signature. Every one of (i)–(iv) is certified below, although (ii)–(iv) are WLOG (MC §1).

## 2. Inputs and their certificates, per field

Two independent evaluators were used:
* **rmb2** (rmb2.py with driver zw_v5.py / zw_v4.py): a new rotated Mellin–Barnes evaluator for both Γ_C and Γ_R², with error bounds in THEORY §2 plus addendum A1–A3.
* **Arb's acb_dirichlet_l** (zwd_v7.py): used for the cyclic fields, where L(ρ) = L(χ)L(χ̄).

The complex fields additionally have the **deg2_fast** route:
* Tollis contig intervals below 100.5 (frozen, replay-closed);
* zscan certified sign changes above;
* weights from hstar_ge5 (general_eval jets, γ < 40) and hstar_rot5 (lfun_rot, 40 ≤ γ < T). This is the K23 pipeline, with the
  .out-loader bug fixed in the new copy hstar_ge5.py.

The certified weights below use L-zero intervals of width 2δ, with δ = 2^{−52} up to a few 2^{−50}.

| K | L zeros 0<γ<T: certified sign changes = N(T) (argument principle) | ζ zeros (vz_q1_T990, Arb) | min ζ/L gap | L(σ) > 0 on [½, 5/2] (min Λ on [½, 9/8]) | max weight radius A / B | runs (A, B, cross) |
|---|---|---|---|---|---|---|
| K31 | 1417 = [1417 ± 2e−11] (A), [1417 ± 2e−12] (B) | 491 | 2.5e−4 (at 701.30) | yes (0.7255) | 5.6e−12 / 5.8e−12 | zw5_K31_T800_A/B; deg2: Lzeros_K31 + wrot5_K31_T800_A |
| K59 | 661 = [661 ± 9e−11] (A), [661 ± 9e−13] (B) | 202 | 9.5e−4 (at 301.65) | yes (1.4748) | 1.5e−12 / 1.6e−12 | zw5_K59_T400_A/B; deg2: Lzeros_K59 + wrot5_K59_T400_A |
| R49 | 1051 = [1051 ± 3e−16] (Arb A, B), [1051 ± 4e−11] (rmb) | 341 | 1.5e−3 (at 353.49) | yes (1.9869; Arb on [½, 0.99]) | 4.0e−11 / 7.4e−13 | zwd7_R49_T600_A/B; rmb: zw4_R49_T600_A |
| R81 | 681 = [681 ± 3e−16] (Arb A, B), [681 ± 3e−10] (rmb) | 202 | 1.8e−3 (at 295.57) | yes (3.1596) | 1.8e−11 / 3.2e−13 | zwd7_R81_T400_A/B; rmb: zw5_R81_T400_A |
| R148 | 719 = [719 ± 1e−9] (A), [719 ± 3e−12] (B) | 202 | 3.9e−3 (at 349.31) | yes (6.0758) | 3.7e−13 / 3.9e−13 | zw5_R148_T400_A/B |
| R229 | 747 = [747 ± 1e−9] (A), [747 ± 3e−12] (B) | 202 | **4.4e−5** (at 329.03) | yes (8.4486) | 3.0e−10 / 3.1e−10 | zw5_R229_T400_A/B |

How each column is certified:
* **Completeness, simplicity, all on the line (i):** N(T) is computed on the right half contour ½ → 5/2 → 5/2+iT → ½+iT (THEORY §3.3).
  It must contain exactly one integer, and that integer must equal the number of disjoint intervals with strict opposite signs of Z.
  This holds in every run. For K31/K59 the deg2_fast intervals (Tollis below 100.5 plus zscan above) match the rmb intervals one-to-one,
  with the same count (merge_zeros_v1, logs/deg2_K*.log). That is two code-independent zero isolations, with completeness from N(T).
* **ζ/L disjointness (ii):** all enclosures are sorted and asserted strictly separated. The minimum gap is in the table. R229 has a ζ zero
  and an L zero 4.4e−5 apart; K59 has near-collisions at 141.12 (1.3e−3) and 419.86 (8e−5, above T = 400).
* **ζ_K(½) ≠ 0 (iii):** ζ(½) < 0, and Λ(½, ρ) > 0 from the real-segment certificate (and ../corollaries/runs/central_*_A.jsonl).
* **No zero at T (iv):** the top-edge pieces exclude 0 at σ = ½. No L interval or ζ ball meets T (asserted).
* **No real zero in (½, 1):** ζ(σ) < 0 there, and Λ(σ, ρ) > 0 (real-segment column).
* **Coefficients:**
  * a_n come from ../corollaries/cubic_central.cubic_L (Delone–Faddeev types plus an exact sieve; MC §6: checked against PARI lfunan).
  * Cyclic fields: equal to the Dirichlet coefficients of L(χ)L(χ̄) for n ≤ 5000 (zwd_v7 check_coeffs).
  * K31/K59: equal to the Tollis/deg2_fast a_p tables implicitly, through the one-to-one zero match and the 1.4e−7 weight agreement below.
* **h\*:** ../mertens_cubic/hstar_cert_v1.py (read-only), an Arb sum at exact rational y. It asserts that no zero enclosure meets T.

## 3. Validation of the new evaluator (THEORY §5)

* **V1, complex structure, against existing certificates (K23, T = 600, zw4_K23_T600_A):**
  * N(600) = 979, equal to the sign changes, and all 979 intervals match ../flagship_K23/explicit/zeros_K23_H1e4.json one-to-one.
  * All 1320 weights overlap MC's certified wrot3_K23_T600_A and _B. The maximum |Δw| is 6.9e−8, at most 0.061 of the summed radii.
  * MC's two certificates are reproduced: h*(−4713.6018) = 1.23828206244 ± 6e−12 and h*(−2100.5118) = −1.18855485477 ± 6e−12. MC had radius 1.5e−5.
  * This is an independent re-computation of MC T5 by a different evaluator.
* **V2, real structure, against an independent evaluator:**
  * R49: rmb (zw4) against Arb Dirichlet (zwd7). Equal N(600) = 1051. All 1392 weights agree to 3.3e−16, at most 1.2e−4 of the radii.
  * R81: zw5 against zwd7. All 883 agree to 1.1e−16.
  * Arb sets A against B: 2e−19.
* **V2′, complex fields:**
  * rmb weights against deg2_fast weights: K31, all 1908 overlap (max |Δw| 5.3e−8, 0.041 of the radii); K59, all 863 overlap (5.1e−8, 0.070).
  * h* from the deg2_fast weights: K31 1.06030 ± 9.2e−6 and −1.14485 ± 7.6e−6; K59 2.3624 ± 1.5e−5 and −2.3886 ± 1.6e−5.
  * These are also certified beyond ±1. They are wider only because of the lfun_rot Lemma-E derivative bound.
* **V3, negative controls (negctl_v1.py, runs/negctl_R49.json, runs/negctl_R148.json):**
  * The test: Λ from two rotations must agree, and for R49 it must also agree with Arb. The score is the discrepancy divided by the error bound.
  * Correct data scores 2e−17. Wrong data must score above 1.
  * Wrong gamma factor: 279–11471. Detected.
  * a₂ + 1: 605–25079. Detected.
  * Conductor N + 1: 3.7–506. Detected.
* **V4, A/B consistency:**
  * For rmb, sets A and B differ in c, φ0, a, bits, precision, K and ρ. The weight midpoints agree to binary64 (Δ = 0 for every field).
  * Every certified h* in the table agrees between A and B, and with the cross-route files.

## 4. Smoothed-Mertens sanity check (smooth_check_v3.py; logs/smooth3_*.log; runs/smooth3_*.json; N = 5·10⁶)

The exact M_K(x), plus M*_K with the field's own signature (mus [0, 0] for the real fields), is smoothed with K_T and compared with
h*_{K,T}(y) from the certified weights. The difference is shown below. The controls must be far from zero.

| K | y = −0.5 | 9 | 11 | 13 | 14.5 | smallest control deviation (noL / conj / wrong signature) |
|---|---|---|---|---|---|---|
| K31 | 1e−8 | 1.0e−5 | 2.6e−6 | −2.2e−6 | −9.7e−6 | 4.7e−2 / 1.5e−1 / 1.8e−1 |
| K59 | 3e−7 | −6.8e−6 | 3.8e−6 | 1e−7 | 3.0e−6 | 1.1e−1 / 8.6e−3 / 1.1e−1 |
| R49 | 3e−8 | −2.2e−5 | −2.0e−5 | 2.3e−5 | −1.0e−5 | 7.3e−2 / 9.8e−2 / 5.3e−2 |
| R81 | 2e−7 | −2.9e−6 | 3.4e−6 | 1.0e−6 | 5.7e−6 | 3.9e−3 / 2.5e−1 / 5.9e−3 |
| R148 | 3e−7 | −1.2e−5 | −6.9e−6 | 7.6e−6 | −5.2e−6 | 4.2e−2 / 7.7e−2 / 7.5e−2 |
| R229 | 4e−7 | −5.7e−6 | −1.7e−6 | −4.7e−6 | −6.2e−6 | 1.0e−1 / 1.6e−1 / 5.6e−2 |

Every |diff| is ≤ 2.3e−5. Every control is ≥ 3.9e−3 at its weakest y and up to O(1) elsewhere (logs). This checks the zeros, the weights,
the real-signature G(s), M* and the exact M_K against each other, for all six fields.

## 5. Prediction outcomes (PREDICTIONS.md)

| P | prediction (prior) | outcome |
|---|---|---|
| P1 | each field closes with T ≤ 1000 (70% each); all six (40%) | **hit**: all six, with T = 400 (4 fields), 600 (R49) and 800 (K31) |
| P2 | both signs at the same T (55%) | **hit** for all six |
| P3 | T ≥ 600 needed for ≥ 4 fields (60%) | **miss**: only K31 (800) and R49 (600, not tried lower). T = 400 suffices for K59, R81, R148, R229 |
| P4 | N(T) = sign changes, ζ/L disjoint, every field (97%) | **hit** (also K23) |
| P5 | rmb agrees with deg2_fast/K23 weights (90%) and with Arb for 49, 81 (90%) | **hit** (§3) |
| P6 | smoothed − h* ≤ 1e−4 on [9, 14.5] (85%) | **hit** (≤ 2.3e−5) |
| P7 | "false for every cubic field" this session (40%) | **hit** (subject to MC T1–T4, §0) |
| N1–N3 | controls break | **as required** (§3 V3, §4) |
| cost | < 6 CPU-h, < 1 GB | **miss on CPU**: about 7.5 CPU-h, of which about 2.2 h was waste: the v1 PARI run on R148 killed after 2.2 h, and the evaluator debugging. Memory **hit**: max footprint 446 MB |

## 6. Deviations, misses and caveats (stated plainly)

* **The pre-registered evaluator (rmb.py, zw_v1) had three defects.** They were found in validation on K23 before any certified output:
  * radius blow-up in the node recurrence;
  * a Taylor-remainder bound too loose above t ≈ 20;
  * binary64 underflow of error bounds above t ≈ 450.
  The last one is unsound, but it made the run abort; it did not produce a wrong certificate. All three are fixed in rmb2 / zw_v4–v5
  (THEORY_ADDENDUM A1–A3). The certified results use only rmb2 + zw_v4/v5, and zwd_v7.
* **PARI start lists were unreliable** (A4). They missed up to 9% of zeros, or contained spurious pairs. Completeness is decided only by
  N(T), and it caught this. **Floating-point scans built on the incomplete lists understated h\*.** For example, R49 scanned 1.15 at T = 600 from
  the PARI list, against the certified 4.91. All final y values come from scans of the certified weights.
* **The deg2_fast route for K31/K59 ran with set A only.** Set B parameters of lfun_rot were not run. The two-set requirement is met by rmb
  A/B; deg2_fast is the code-independent cross-check.
* **R49 and R81: the primary route is Arb Dirichlet.** The real segment near σ = 1 comes from rmb (A5).
* **The scan queue was stopped early.** scan_float_v2 finished R229 only at T = 400. T = 400 was enough, so this is not a problem.
* **No novelty search beyond MC §7.** To our knowledge no cubic field was treated individually before MC (OpenAlex: one citer of HKMS).
  The six individual disproofs, and hence the complete cubic statement, appear new. The method is HKMS's own Ingham route.
* **Independence.** The six results here are certified by two independent evaluators each:
  * rmb2 + deg2_fast for K31/K59;
  * rmb2 + Arb Dirichlet for R49/R81;
  * rmb2 sets A/B for R148/R229. This is one code base; rmb2 itself is validated against Arb and deg2_fast (§3).
  * An adversarial re-verification by a separate agent, as VERIFY.md did for the quadratic case, is still recommended before external use. MC T1–T4 need it too.

## 7. For an independent verifier

Run from this directory, with PY = /Users/kiosk/projects/atlas-rerun/.venv/bin/python, one command at a time.

* **Re-certify h\*:** $PY ../mertens_cubic/hstar_cert_v1.py cert runs/<file>.json T y, using the files and y values in §0 and §2. Takes seconds.
* **Re-run a field end to end:**
  * $PY zw_v5.py R229 400 A runs/pari3_R229_T410.json takes about 6 min;
  * $PY zwd_v7.py R49 600 B none takes about 2 min;
  * the deg2 route: queue_deg2_v1.sh / queue_deg2_v2.sh (K31 lfun_rot about 1 h).
* **Comparisons:** compare_w_v1.py FILE1 FILE2.
* **Controls:** negctl_v1.py NAME.
* **Smoothed check:** smooth_check_v3.py NAME WFILE T 5e6 −0.5,9,11,13,14.5.
* **What to attack:**
  1. Lemmas R0–R6′, in particular |K₀(w)| ≤ K₀(Re w), the rotation of the theta split, and the strip and node bounds with the e^{±ωy} factors.
  2. The argument-principle count (right half contour, Re L > 0 on σ = 5/2 from ζ(5/2)² − 1 < 1).
  3. The coefficient identification for the S3 fields R148/R229, which have no second evaluator. Their checks are the A-split-type rotation
     consistency and the smoothed-Mertens agreement.
  4. MC T1–T4.

## 8. Costs

All CPU-time figures are approximate.

| step | CPU | peak footprint |
|---|---|---|
| PARI scouting: v1 K31/K59/R49/R81 (17 min); v1 R148 (2.2 h, killed: lfuninit re-initialisation); v2 K31/R148/R229 (18 min); v3 starts (2.5 min) | ≈ 2.8 h | 406 MB |
| float scans (v1 killed after 3 s, 1.55 GB; v2 about 75 min) | ≈ 1.3 h | 319 MB |
| validation: zw K23 T600, zw4 R49, zwd runs, negctl, debugging runs | ≈ 0.7 h | 52 MB |
| certified rmb2 runs (9 × zw5) | 1.5 h | 40 MB |
| deg2_fast route: zscan builds/scans, hstar_ge5, hstar_rot5 K59 (20 min), K31 (60 min) | ≈ 1.4 h | 128 MB |
| h* certification scan (hcert_all_v1), smoothed checks | ≈ 0.4 h | 446 MB |

## 9. Files

* **Code:**
  * rmb.py (pre-registered, superseded) and rmb2.py;
  * zw_v1…zw_v5.py (zw_v4 used for K23/R49 validation, zw_v5 for certified runs);
  * zwd_v1…zwd_v7.py (zwd_v7 used);
  * hstar_ge5.py, hstar_rot4.py and hstar_rot5.py (rot5 used);
  * merge_zeros_v1.py, compare_w_v1.py, negctl_v1.py, smooth_check_v3.py, hcert_all_v1.py;
  * explore_pari_v1–v3.py, scan_float_v1–v2.py;
  * run_v1.sh and the queue_*.sh scripts.
* **Certified outputs (runs/):**
  * zw5_<K>_T<T>_{A,B}.json, zwd7_<K>_T<T>_{A,B}.json, zw4_{K23,R49}_T600_A.json;
  * wge5_*/wrot5_*, Lzeros_{K31,K59}.json, zscan_*_iv.json, zmodels_*/;
  * hcert_all_v1.json, smooth3_*.json, negctl_*.json.
* **Superseded or diagnostic outputs (kept):** zw2_/zw3_ K23 T100 and pari*_ start lists.
* **Hashes:** SHA256SUMS covers every file in this directory except itself.
