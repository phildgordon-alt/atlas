# mertens_cubic: RESULTS (2026-10-20)

Target: the naive Mertens-type conjecture of Hu–Kaneko–Martin–Schildkraut (HKMS; arXiv 2109.06665 v2; Math. Proc. Camb. Phil. Soc.
177 (2024) 481–523), i.e. −1 ≤ M⁻_K ≤ M⁺_K ≤ 1 with M^±_K = lim sup / lim inf M_K(x)/√x, for cubic fields K.
Pre-registration: PREDICTIONS.md, sha256 0c5ea9aa…b6e658 (re-checked 2026-10-20: matches PREDICTIONS.sha256).
Computation of 2026-10-19 (chains 1–2, K23 set-A weights) by the previous agent; this file, chain 3 (K23 set-B weights), the Arb
certification of h*, the smoothed-Mertens check and the summaries are 2026-10-20. Nothing outside this directory was modified.
No one was contacted; nothing was posted.

## 0. Summary

| # | Statement | Status |
|---|---|---|
| T1 | Every **complex** cubic field with \|d_K\| ≥ 5178 has M*_K(1) > 0, hence M⁺_K > 1 (explicit HKMS Thm 1.2: D_{1,2} ≤ 5177) | proved, unconditional (§2) |
| T2 | Every **totally real** cubic field with d_K ≥ 5230 has M*_K(1) > 0, hence M⁺_K > 1 (explicit D_{3,0} ≤ 5229) | proved, unconditional (RH used only WLOG, §2) |
| T3 | All 762 complex cubic fields with \|d\| ≤ 5196 and all 382 totally real cubic fields with d ≤ 10⁴: M*_K(1) certified (sets A, B agree) | 702 / 318 have M*_K(1) > 0; 60 / 64 have M*_K(1) ∈ (−0.62, 0); **none** < −1 |
| T4 | Of the 124 fields with M*_K(1) < 0, 117 are settled by a certified G(n±) = (M_K(n±) + M*_K(n))/√n beyond ±1 with n ≤ 10⁶ | proved (HKMS Prop 3.3 / Lemma 3.4 argument) |
| T5 | K = Q(x³ − x − 1), d = −23: h*_{K,600}(−4713.6018) ≥ 1.2382 and h*_{K,600}(−2100.5118) ≤ −1.1885, so **M⁺_K ≥ 1.238 and M⁻_K ≤ −1.188** | proved, Ingham route, sets A and B (§3) |
| **C** | The naive Mertens-type conjecture is **false for every complex cubic field except possibly d = −31 and d = −59**, and **false for every totally real cubic field except possibly d = 49, 81, 148, 229** | T1–T5 together. **6 fields remain open** (§4) |

So the complex family is *not* complete: "false for every complex cubic field" is two fields short (−31, −59). The totally real family is
four fields short (49, 81, 148, 229).

## 1. The logic (what each certificate needs)

Write G_K(x) = (M_K(x) + M*_K(x))/√x, with M*_K(x) = −Σ_{k≥0} Res_{s=−k} x^s/(sζ_K(s)) (HKMS (3.2)).

**(L1) HKMS Lemma 3.4 and its proof (pp. 13–14).** Either M⁺_K = ∞ or M⁻_K = −∞ (when RH fails, or there is a multiple zero, by
HKMS Thm 2.10; a zero at ½ has even order by the sign of the functional equation, so it is covered by the multiple-zero case). Otherwise
RH holds, all zeros are simple and 1/|ρζ_K′(ρ)| is bounded, and HKMS Prop 3.3 (Jurkat's theorem) gives M⁻_K ≤ G_K(x) ≤ M⁺_K for every
x > 0. One-sided limits at integers n are allowed (limit points form a closed set; HKMS use n+ themselves in their Table 2). Hence:
* M*_K(1) > 0 ⇒ M⁺_K ≥ G(1+) = 1 + M*_K(1) > 1;
* G(n±) > 1 ⇒ M⁺_K > 1, and G(n±) < −1 ⇒ M⁻_K < −1.

**This route needs no zeros at all.** The only inputs are M*_K(x), from certified Taylor jets of Λ(s, ρ_K) at σ = 1 + k
(mstar.py / mstar2.py, general_eval evaluator, two parameter sets), and the exact integer M_K(n) (mertens_exact.py).

**(L2) Ingham route** (as re-derived in ../corollaries/verify_hkms/VERIFY.md, check 1). M⁻_K ≤ h*_{K,T}(y) ≤ M⁺_K for every real y,
where h*_{K,T}(y) = Σ_{0<γ<T} 2 Re[f(γ/T) e^{iγy}/(ρζ_K′(ρ))] and f is the Jurkat–Peyerimhoff kernel. If M⁺_K < ∞ and M⁻_K > −∞, then
Landau gives RH for ζ_K (including no real zeros in (½, 1)), and Ingham (1942, Thm 1) needs simple poles of 1/((s+½)ζ_K(s+½)) for
|t| ≤ T. To *compute* h* we need: (i) the complete list of zeros of ζ and of L(s, ρ_K) with 0 < γ < T; (ii) ζ and L(ρ_K) share none of
them (so ζ_K′(ρ) = ζ′(ρ)L(ρ) resp. ζ(ρ)L′(ρ) ≠ 0 and the zeros of ζ_K are simple); (iii) ζ_K(½) ≠ 0; (iv) no zero at height T.
Strictly, (ii)–(iv) and the absence of real zeros are also forced by boundedness (an extra pole would make M_K(x)/√x unbounded), so they
are WLOG; we certify them anyway (§3), as in the quadratic case.

## 2. Explicit HKMS Theorem 1.2 for cubic fields (bounds.py, bounds_search.py; runs/bounds.json, runs/bounds_search.json)

Notation: ζ_K = ζ·L, L = L(s, ρ_K) of degree 2, Λ_K(s) = D^{s/2} γ_K(s) ζ_K(s) = Λ_K(1−s), D = |d_K|; S = Σ_ρ Re(1/ρ),
Q = Σ_ρ Re(1/ρ²) (nontrivial zeros, symmetric summation).

**2.1 Leading terms** (closed forms checked numerically against the generic residue code in theory_check2.py / logs/theory_check2.log,
agreement to the last digit for K23, K31, K983, R49, R148):
* complex: T0 := −Res₀ 1/(sζ_K(s)) = (w/hR)(S + ½ log D − c_C), c_C = 1 + ½ log π + log 2π + 3γ/2 = 4.2760655… (the bounds.py docstring
  says 4.27623; the code computes the constant in Arb, and the docstring value is a typo). S ≥ 0 unconditionally (every zero has
  0 < β < 1, and Re(1/ρ) = β/|ρ|²). So T0 ≥ 0 as soon as ½ log D ≥ c_C, i.e. D ≥ 5177 (e^{2c_C} = 5176.6). T1 := −Res₋₁ = 16π⁵/(D^{3/2}ζ_K(2))
  ≥ 16π⁵/(D^{3/2}ζ(2)³) > 0.
* totally real: T0 = (w/(2hR))[(S + ½ log D − c_R)² + Q − 1 + π²/8], c_R = 1 + (3/2) log π + 3γ/2 = 3.5829183…. Under RH (WLOG
  by L1), Re(1/ρ²) + 2Re(1/ρ) = ½/(¼ + γ²)² > 0 for every zero ρ = ½ + iγ, so Q ≥ −2S. With a = ½ log D − c_R ≥ ½,
  min_{S≥0} [(S+a)² − 2S] = 2a − 1 (a ≤ 1) or a² (a ≥ 1).
  **2.3 (κ bound).** w/(2hR) = 4/(κ√D), κ = L(1, ρ_K). Under RH, Λ_L(s) = Λ_L(½)·Π_{γ>0}(1 + (s−½)²/γ²) (times (s−½)^{2m} if
  L(½) = 0) for real s; this is increasing in |s − ½|. Hence √D·L(1) = Λ_L(1) ≤ Λ_L(2) = D·L(2)/π² ≤ Dζ(2)²/π², i.e.
  κ ≤ ζ(2)²√D/π². bounds.py uses the weaker κ ≤ 2ζ(2)³√D/π³ (larger by 2ζ(2)/π = 1.047), so its bound is valid. (The docstring calls
  this bound "elementary"; the argument above uses RH, which is WLOG here. This is the derivation the code refers to.)
* k ≥ 2 (all k ≥ 1 for the real case): |Res₋ₖ| ≤ D^{−k−½} Σ_j |ct_{k,j}| (log D)^j/j!. The ct are computed by the same residue code from
  interval data valid for **every** cubic field: L(σ) ∈ [ζ(σ)⁻¹, ζ(σ)²], (L′/L)(σ) ∈ [2z₁, −z₁], (L′/L)′(σ) ∈ [−z₂, 2z₂], with z₁ = ζ′/ζ(σ)
  and z₂ = (ζ′/ζ)′(σ). These hold because every trace of ρ(Frob^m), including at ramified primes and for cyclic ρ = χ ⊕ χ̄, lies in [−1, 2].
  Only the first p coefficients of Λ_L enter the residue of order p ≤ 3, and three are supplied.
* Tail k > 12: mstar.tail_bound. This uses Cauchy on |s + k| = ½ and the functional equation, with |1/ζ_K(w)| ≤ ζ(Re w)³,
  |sin πs| ≥ 1 and |sin(πs/2)| ≥ 1/√2 on the circle (equality at the real points; float-checked), |Γ(1−s)| ≥ m₀ Π_{j≤k}(j − ½) and
  m₀ = min_{|u|=½}|Γ(1−u)| ≥ 0.8054 > 4/5. The m₀ value is an Arb ball cover, logs/check_m0_v1.log, run 2026-10-20. For k ≥ kmax + 400
  the successive ratio of the bounds is ≪ 1/2, which justifies the final 2b. The tail is below 1e−41 here.

**2.2 Monotonicity in D** (why one check at D₁ covers all D ≥ D₁).
* Complex: D^{3/2}T1 ≥ 16π⁵/ζ(2)³ is constant. D^{3/2}·(k-term) = D^{1−k}·poly(log D) with degree ≤ p − 1 ≤ 1 for k = 2, ≤ 2 in general.
  This decreases for log D > 2/(k−1), and the tail decreases in D. T0 ≥ 0 for D ≥ 5177.
* Real: D·T0 ≥ (const)·core(a), and core is increasing in a, hence in D. D·(k-term) = D^{½−k}·poly(log D) of degree ≤ 2. This decreases
  for log D > 2/(k − ½).
* So bounds_search's bisection is legitimate: ok(D) is monotone.

**Results.**
* complex_check(5178): T1 ≥ 2.9524e−3 > rest ≤ 3.377e−4 ⇒ M*_K(1) > 0 for every complex cubic field with D ≥ 5178.
  For D = 5177 the T0 ≥ 0 step fails (the assert), so 5178 is the threshold of this method.
* real_check(5230): T0 ≥ 1.67839e−3 > rest ≤ 1.67770e−3, a thin margin (4e−4 relative) but rigorous. real_check(5000) fails.

## 3. Computed results, both parameter sets

### 3.1 M*_K(1) for every field (runs/mstar_{complex,complex20k,real}_{A,B}.jsonl; runs/mstar_summary.json)

Field lists:
* complex, 2000 or less: 270 fields, cross-checked with PARI nflist field by field (../new_territory/cubic_sweep/RESULTS_STAGE1.md).
* complex, 2000 to 5196: 492 fields, indices 270–761 of fields_20000.json. That file is a Hunter enumeration of 3169 fields with
  \|d\| ≤ 2·10⁴. The count agrees with PARI `nflist("S3",[1,20000],1)`, and so do the cumulative counts 7, 25, 127, 270, 729, 1520, 3169
  (THEORY_SWEEP.md). It contains every field with \|d\| < 5178 (760 fields).
* totally real, d ≤ 10⁴: 382 fields (Hunter, general_eval/RESULTS.md).

Sets A and B (different evaluator plans, precision 256/320, jet radius, Gaussian/Lemma parameters): every ball overlaps across sets and has the same certified sign.
The maximum radius is 2.7e−9.

| family | n | M*(1) > 0 | M*(1) < 0 | min M*(1) | M*(1) < −1 | largest \|d\| with M* < 0 |
|---|---|---|---|---|---|---|
| complex \|d\| ≤ 2000 | 270 | 210 | 60 | −0.53220 (K87) | 0 | 516 |
| complex 2003–5196 | 492 | 492 | 0 | +0.04627 | 0 | — |
| totally real d ≤ 10⁴ | 382 | 318 | 64 | −0.61639 (R169) | 0 | 2300 |

Control (N2): the same residue code gives M*(1) = −0.575142 for Q(i) and −0.4851 for Q(√−3), equal to HKMS Table 1. It also gives
1.31791 for Q(√−43) (logs/quad_A_test1.log).

### 3.2 Fields with M*_K(1) < 0: certified G(n±) (runs/scan_{complex,real}_1e+06.jsonl; table: logs/summarize_scan_v1.log, runs/scan_summary_v1.json)

Exact M_K(n±) for n ≤ 10⁶; the candidate points are certified with Arb M*_K(n) in **both** sets at the same point. The full 124-row
table, with points and bounds, is in logs/summarize_scan_v1.log. Outcome:
* complex (60): 57 settled. 54 have both M⁺ > 1 and M⁻ < −1. K44 and K76 have only M⁻ < −1 (G(926174+) ≤ −1.1574, G(7958+) ≤ −1.0074).
  K104 has only M⁺ > 1 (G(14486+) ≥ 1.1725). **K23, K31 and K59 were not settled**: float max/min of G for n ≤ 10⁷ are
  K23 0.750/−0.565, K31 0.735/−0.646, K59 0.825/−0.900 (logs/scan_1e7.log).
* totally real (64): 60 settled, mostly in both directions. Examples: R1509, G(4+) ≤ −1.336; R1929, G(8+) ≤ −1.381;
  R1849, G ≥ 3.759 and ≤ −3.688. **R49, R81, R148 and R229 were not settled**: n ≤ 10⁷ float max/min 0.857/−0.817, 0.953/−0.951,
  0.925/−0.759, 0.891/−0.882.
* The smallest margins: R1573 (G ≥ 1.0061), K76 (≤ −1.0074), R788 (≤ −1.0250). Both sets give the same bound to four digits.

### 3.3 K23 by the Ingham route (T5)

Weights w(ρ) = 1/(ρζ_K′(ρ)) for all 1320 zeros of ζ_K with 0 < γ < 600 (341 of ζ, 979 of L(ρ)):
* γ < 40 from general_eval jets (hstar_ge4.py; runs/wge4_K23_T100_{A,B}.json);
* 40 ≤ γ < 600 from the rotated-contour evaluator with a Cauchy-formula derivative and a Lemma-E sup bound (hstar_rot3.py, hstar_cubic3.py;
  runs/wrot3_K23_T600_{A,B}.json);
* on [40, 100) both evaluators were run and compared: 98 zeros, maximum difference 1.7e−15, inside the radii.

| set | weights file | max weight radius | h*(−4713.6018) | h*(−2100.5118) |
|---|---|---|---|---|
| A | wrot3_K23_T600_A.json | 1.34e−5 | [1.23827, 1.23830] | [−1.18857, −1.18854] |
| B | wrot3_K23_T600_B.json | 1.41e−5 | [1.23827, 1.23830] | [−1.18857, −1.18854] |

The Arb sum is at exact rational y (hstar_cert_v1.py; logs/hcert_K23_T600_{A,B}.log). Set B (r = 1/12, R = 2/5, m = 28 nodes, φ = 40, 72 bits) differs from A only in parameters (same code); all 1320 A/B weights agree within their radii (max |Δ|/tol = 3.9e−9). It also gives h*(−3759.2377) ≥ 1.2056 and
h*(−3458.9293) ≤ −1.1134 (both sets).

Inputs and their certificates:
* (i) **Completeness, on the line, simplicity.**
  * ζ: ../corollaries/verify_hkms/vz_q1_T990.json, Arb acb_dirichlet_zeta_zero (Turing method), N(990) = 640, sha256 989931de….
  * L(ρ_K23): ../flagship_K23/explicit/zeros_K23_H1e4.json, 25,275 intervals to height 10⁴, certified complete, on the line, simple, and
    Lean-audited (../flagship_K23/RESULTS.md; ATLAS_STATUS row 1), sha256 f471daad….
* (ii) **ζ/L disjointness.** ../flagship_K23/disjoint/RESULTS.md: 0 overlaps for 0 < t ≤ 10⁴, minimum gap 3.69e−5. It is also
  re-asserted in hstar_rot3.py (consecutive enclosures strictly separated), which would have stopped the run otherwise.
* (iii) **ζ_K(½) ≠ 0.** ζ(½) < 0, and L(½, ρ_K23) = 0.174036326987934 ± 2e−16 > 0 (../corollaries/runs/central_complex_{A,B}.jsonl,
  Λ(½) = 0.5389976427263 > 0 in both sets).
* (iv) **No zero at height T = 600.** cert asserts that every enclosure lies strictly below or above T. The nearest zeros are
  599.7502 (L) and 600.1275 (L); the nearest ζ zeros are 599.5456 and 601.6021.
* **No real zeros.** ζ(σ) < 0 on [0, 1). Λ(σ, ρ_K23) > 0 for σ > ½ (super-positivity, ../corollaries/RESULTS.md Thm 1). The L-zero
  certificate covers [0, 10⁴] × [0, ½] (flagship Lean audit).

**Sanity check, P6** (smooth_check_v2.py, logs/smooth2_K23_T600_A.log, runs/smooth2_K23_T600_A_N5e+06.json). The actual exact M_K(x)
plus M*_K(x), smoothed with the JP kernel, equals h*_{K,600}(y) from the zeros:

| y | −0.05 | −0.5 | 9 | 11 | 13 | 14.5 |
|---|---|---|---|---|---|---|
| smoothed − h* | −7e−8 | 5e−8 | −7e−6 | −8e−6 | 5e−6 | 2e−6 |

Negative controls:
* N1a, L(ρ)-zero weights dropped: off by 2.5e−2 to 0.47.
* N1b, conjugated weights: off by 6.5e−3 to 0.88.
* N3, wrong signature (M* with mus = [0, 0]): off by 4e−2 to 3.6.

All three are far above the 1e−5 agreement. This also checks M_K, M* and the weights against each other.

## 4. What HKMS prove for degree ≥ 3, and what is left

* **HKMS prove** (Thm 1.2, §3.4): for each signature there is a D_{r1,2r2} such that the conjecture fails for every K of that signature
  with D_K > D. The constant is not explicit: Lemma 3.11 is a "≪" with an unspecified constant, Lemma 3.13 has a (1 + o(1)), and
  Louboutin's bound is used with "≪". They give no numerical value for any degree ≥ 3 signature and treat no cubic field
  individually. Their degree-≥3 content is otherwise Lemma 3.4 and Cor 2.11 (non-abelian Galois fields: false, because of
  multiple zeros; this does not apply to cubic fields themselves, whose ζ_K = ζ·L(ρ) has simple zeros in every computed case).
* **We add**:
  * explicit values D_{1,2} ≤ 5177 and D_{3,0} ≤ 5229 for the cubic signatures (T1, T2);
  * a complete computation below them (T3, T4, T5).
* **Largest complete statements**:
  * "false for every complex cubic field with \|d_K\| ≠ 31, 59". As a clean range: false for every complex cubic field with
    \|d_K\| > 59, and for d = −23 and every complex field with \|d\| ≤ 59 except −31 and −59. The complex fields with \|d\| ≤ 59 are
    −23, −31, −44, −59.
  * "false for every totally real cubic field with d_K > 229, and for every totally real cubic field except d = 49, 81, 148, 229".
* **Gap** (6 fields): K31 and K59 (complex); R49, R81, R148, R229 (totally real). For these, M*(1) ∈ (−0.53, −0.36) and G(n±) stays in
  (−1, 1) for n ≤ 10⁷. They need the Ingham route.
  * K31 and K59 (complex): L(ρ) zeros are certified only to about 110 (Tollis contig, 11 chunks). For K23, T ≤ 200 gives
    max \|h*\| ≈ 0.79 over \|y\| ≤ 10⁵, and T = 600 gives 1.24. So zeros to roughly 600 are needed: about 50 more contig chunks
    (≈ 45 s each) plus about 35 min of weights per field and set. Feasible, a few CPU-hours, but over this session's 1 CPU-h cap.
  * R49, R81, R148, R229 (totally real): need L(ρ) zeros (Γ_R(s)² gamma factor) to a few hundred, and a real-signature version of the
    weight code. hstar_cubic3/hstar_rot3 assume the complex Γ_C factor. R49 and R81 are cyclic (ρ = χ ⊕ χ̄; Dirichlet zeros suffice).
* Note on hstar_ge4.load_L_zeros (not used for K23): its glob `c_*` also matches `*.out` files in the contig directories and would
  crash. A future K31/K59 run must use a corrected copy (new file), not an edit.

## 5. Prediction outcomes

| P | Prediction (prior) | Outcome |
|---|---|---|
| P1a | K23 M*(1) < 0 (90%) | **hit**: −0.467207286138490 |
| P1b | K23 M*(1) < −1 (55%) | **miss**: no cubic field (of 1144) has M*(1) < −1 |
| P2a | K23 h* > 1 with T ≤ 200 (75%) | **miss**: at T = 200 the float max over \|y\| ≤ 5·10⁴ is 0.786 (at T = 100 over \|y\| ≤ 10⁵ it is 0.646) |
| P2b | K23 h* < −1 with T ≤ 200 (65%) | **miss** (−0.765) |
| P2c | T ≤ 1000 suffices for at least one sign (90%) | **hit**: T = 600, both signs |
| P3a | explicit D_{1,2} ≤ 2·10⁴ (70%) | **hit**: 5178 |
| P3b | whole complex chain closes this session (60%) | **miss**: K31, K59 open |
| P4 | #complex \|d\| ≤ 2000 with M*(1) ∈ [−1, 0] in [1, 100] (60%) | **hit**: 60 |
| P5a | explicit D_{3,0} ≤ 10⁶ (50%) | **hit**: 5230 |
| P5b | totally real NOT covered computationally this session (70%) | **miss**: covered except 4 fields |
| P6a | smoothed Mertens equals h* to ≤ 1e−3 at y ≈ 10–15 (85%) | **hit**: ≤ 8e−6 |
| P6b | h*(y) near y = 0⁻ approaches M*(1) as T grows (80%) | **partial**: only T = 600 tested. h*(−0.05) = −0.41908, equal to the smoothed e^{−y/2}M*(e^y) (7e−8), close to M*(1) = −0.4672 up to smoothing. No T-sequence was run. |
| N1, N2, N3 | controls must break / reproduce | **all as required** (§3.1, §3.3) |

## 6. Deviations

* No THEORY.md was written before the run. The derivations the code docstrings point to ("RESULTS.md §2, 2.2, 2.3") are supplied here,
  in §2. The κ bound needs RH (WLOG), which the docstring's "elementary" did not say.
* The bounds.py docstring constant c_C = 4.27623 is a typo for 4.2760655. The prediction "D > ~5172" should read 5177.
* The scan route (Prop 3.3 / G(n±), the method of HKMS Table 2) was not pre-registered. It settled 117 of the 124 negative-M* fields
  without any zeros, and it is the main workhorse.
* Sets A and B share the exact integer M_K(n). Its splitting types (cubic_types) are cross-checked with PARI idealprimedec for all
  3169 complex fields and p < 20,000, and the L coefficients with PARI lfunan. Witnesses with n > 20,000 rely on cubic_types beyond that
  range. The smoothed check (§3.3) independently validates M_K for K23 to 5·10⁶.
* K23 weights below γ = 40 come from a different evaluator (general_eval) than above 40 (lfun_rot). The overlap was compared, as above.
* Not independently re-verified by a separate agent yet (unlike the quadratic case, VERIFY.md). Recommended before any external use.

## 7. Novelty (provisional, 2026-10-20)

* OpenAlex lists one work citing HKMS (W4405592065): the annotated bibliography for comparative prime number theory (Expo. Math. 2025).
* An arXiv abstract search ("Mertens" ∧ "field") shows no follow-up on cubic or higher-degree fields.
* HKMS themselves give no explicit constant and treat no cubic field.
* So, to our knowledge:
  * the explicit thresholds 5178 / 5230 are new;
  * the 1144-field certified M*(1) table is new;
  * the individual disproofs of 1138 of the 1144 computed cubic fields are new (or of all cubic fields except six, counting the
    thresholds);
  * the first Ingham-route disproof for a degree-3 field, K23 (M⁺ ≥ 1.238, M⁻ ≤ −1.188), is new.
* The method is HKMS's own (Lemma 3.4, Prop 3.3, Table 2 style) plus Ingham/OtR. What is new is the explicit bounds, the certified data
  and the zeros.
* Semantic Scholar was rate-limited, so the citer list should be re-checked before any claim.

## 8. Files

* Code (2026-10-19):
  * mstar.py, mstar2.py, run_mstar.py: M*;
  * bounds.py, bounds_search.py;
  * mertens_exact.py;
  * scan_field.py;
  * hstar_cubic{,2,3}.py, hstar_ge{,2,3,4}.py, hstar_rot{,2,3}.py: weights;
  * smooth_check.py, theory_check{,2}.py;
  * summarize_mstar.py;
  * run_chain{1,2}.sh.
* New 2026-10-20 (no existing file modified):
  * run_chain3.sh (set-B weights);
  * hstar_cert_v1.py (float refine + Arb h*);
  * smooth_check_v2.py (reads wrot3 weights);
  * summarize_scan_v1.py;
  * runs/wge4_K23_T100_B.json, runs/wrot3_K23_T600_B.json, runs/scan_summary_v1.json, runs/smooth2_K23_T600_A_N5e+06.json;
  * logs/{wge4_K23_T100_B, wrot3_K23_T600_B, chain3, hcert_K23_T600_A, hcert_K23_T600_B, smooth2_K23_T600_A, check_m0_v1,
    summarize_scan_v1}.log.
* Hashes: SHA256SUMS (all files in this directory, excluding SHA256SUMS itself).
