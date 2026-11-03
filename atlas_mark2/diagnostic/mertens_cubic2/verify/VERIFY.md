# Adversarial verification: "the naive Mertens-type conjecture is false for every cubic field"

Date: 2026-10-21. This verifies the claim stated in ../RESULTS.md §0 (and ../../mertens_cubic/RESULTS.md, "MC", T1–T5): for every cubic
field K, it is not the case that −1 ≤ M⁻_K ≤ M⁺_K ≤ 1, where M_K(x) = Σ_{N𝔞≤x} μ_K(𝔞).

Ground rules:
* I wrote all the code in this directory. It imports no Atlas module.
* It reads Atlas outputs read-only, in two ways:
  * as the object under test: weight files, M\* balls, witness lists, field lists;
  * as location hints only: Atlas zero ordinates told my local rescans where to look; the zeros themselves are my own.
* My independent tools are PARI/GP 2.17.2 (cypari2, with nbthreads = 1) and Arb (python-flint 0.9).
* Everything ran at nice 19, one heavy process at a time, with an RSS watchdog. The largest RSS was 634 MB.
* Total CPU was about 25 minutes. Nobody was contacted and nothing was posted. Nothing outside verify/ was written.

## Verdict: **CONFIRMED**

I found no error that affects the claim. Every load-bearing number I recomputed agrees with Atlas.

The one material observation is that the "thin margin" at the totally real threshold comes from Atlas's loose residue bound, not from
the problem itself. My independent rigorous bound gives a relative margin of 40% at D = 5230 and a threshold of 4448.

| # | Check | Status |
|---|---|---|
| 1 | Explicit thresholds (complex \|d\| ≥ 5178, real d ≥ 5230): every inequality, the monotonicity in D, the real margin | **CONFIRMED** (rigorous, own Arb code). The real margin is 40%, not 4e−4, with a sharper bound. |
| 2 | Field lists complete; M\*_K(1) for all 1144 fields | **CONFIRMED** (PARI nflist; PARI Dedekind ζ, all 1144 fields, not only a sample) |
| 3 | Integer-point argument (HKMS Lemma 3.4 / Prop 3.3); G(n+) at the witnesses | **CONFIRMED** (logic re-derived; all 117 fields and 225 points recomputed) |
| 4 | Ingham route for the 7 fields K23, K31, K59, R49, R81, R148, R229 | **CONFIRMED** (own Arb h\* from the certified weights; independent float zeros, counts and weights; Γ_R² weight formula re-derived and checked) |
| 5 | Smoothed exact Mertens against h\* (R148, R229) | **CONFIRMED** (agreement ≤ 5e−11; controls break) |

### The most precise defensible statement

**Theorem.** For every cubic field K, M⁺_K > 1 or M⁻_K < −1 (in the extended reals), so the naive Mertens-type conjecture of HKMS is false
for every cubic field. Each part is covered as follows:
* complex, \|d_K\| ≥ 5178: M\*_K(1) > 0 (explicit HKMS Thm 1.2 via Lemma 3.4b);
* totally real, d_K ≥ 5230: M\*_K(1) > 0. My independent bound already proves this for d_K ≥ 4448;
* all 762 complex fields with \|d\| ≤ 5196 and all 382 totally real fields with d ≤ 10⁴: certified M\*_K(1). This gives 1020 fields with
  M\*_K(1) > 0;
* 117 of the 124 fields with M\*_K(1) < 0: a certified G(n+) beyond ±1 with n < 10⁶;
* the remaining 7 fields (K23, K31, K59, R49, R81, R148, R229): the Ingham/Jurkat–Peyerimhoff route, with both M⁺ > 1 and M⁻ < −1.

Inputs: HKMS Lemma 3.4 / Prop 3.3 (Jurkat 1973) and Theorem 2.10, Ingham 1942 Thm 1 with the JP kernel, and Landau's theorem, all as
published. Then Atlas's Arb certificates (M\* balls, zero isolation by the argument principle, weight balls).

What I independently re-proved rigorously, and what I only independently re-computed:
* **Rigorous (Arb):** the threshold inequalities, and the h\* sums from the certified weight balls.
* **Floating-point (PARI, 38–60 digits) and code-independent:** the field lists, M\*(1), M_K(n), and the zero lists, zero counts and
  weights.
* Every one of these agrees with Atlas's certified values, inside their radii.

## Check 1. Explicit thresholds. **CONFIRMED**

Code: threshold_v1.py, output in runs_threshold_v1.json. One process, 0.3 s.

**Residue formulas, re-derived from scratch.**

From Λ_K(s) = D^{s/2}γ_K(s)ζ_K(s) = Λ_K(1−s), with Λ′/Λ(s) = Σ_ρ 1/(s−ρ) − 1/s − 1/(s−1) (symmetric summation):
* **complex:** ζ_K′/ζ_K(s) = 1/s + (c_C − S − ½log D) + O(s), with c_C = 1 + ½log π + log 2π + 3γ/2 = 4.2760655066863…. Since
  ζ_K(s) ~ −(hR/w)s, this gives T0 = (w/hR)(S + ½log D − c_C). This matches MC.
* **real:** ζ_K′/ζ_K(s) = 2/s + (c_R − S − ½log D) + s(1 − Q − π²/8) + O(s²), with c_R = 1 + (3/2)log π + 3γ/2. Then
  T0 = (e0² − e1)/(2a2) with a2 = −hR/w, which gives T0 = (w/(2hR))[(S + a)² + Q − 1 + π²/8]. This matches MC.
* **class number formula:** w/(2hR) = 4/(κ√D), with w = 2.
* **k = 1:** −Res_{−1} = 16π⁵/(D^{3/2}ζ_K(2)), from the residue of γ_K(s)/γ_K(1−s) at −1, which is 8π²·2π³. This matches MC.
* **Pole orders:** the code finds pole orders 1/2 (complex, odd/even k) and 3/0 (real, even/odd k), as the vanishing orders of ζ_K at
  negative integers require.
* **Reflection forms:** I used Γ_R(s)/Γ_R(1−s) = (2π)^{−s}π/(sin(πs/2)Γ(1−s)) and Γ_C(s)/Γ_C(1−s) = (2π)^{1−2s}π/(sin(πs)Γ(1−s)²).
  Both were checked against direct Γ to 1e−58.

**Inequalities.**
* **Q ≥ −2S** under RH, because Re(1/ρ²) + 2Re(1/ρ) = ½/(¼+γ²)² > 0.
* **The minimum over S ≥ 0** of (S+a)² − 2S is 2a − 1 for a ≤ 1 and a² for a ≥ 1.
* **The κ bound** uses Hadamard for the even, order-1 function Λ_L(½+z) = Λ_L(½)Π(1+z²/γ²) under RH, which gives
  Λ_L(1) ≤ Λ_L(2). With Γ_R(1) = 1, Γ_R(2) = 1/π and L(2) ≤ ζ(2)², this gives κ ≤ ζ(2)²√D/π². Atlas's 2ζ(2)³√D/π³ is weaker, hence
  also valid.
* **RH is WLOG**, by HKMS Thm 2.10: RH failing gives M⁺ = ∞ or M⁻ = −∞.
* **The field-uniform intervals** are L ∈ [ζ⁻¹, ζ²], L′/L ∈ [2z₁, −z₁] and (L′/L)′ ∈ [−z₂, 2z₂]. Traces of ρ(Frob^m) lie in
  [−1, 2], including at ramified primes and in the cyclic case, and the Euler factors satisfy (1+x+x²)⁻¹ ≥ 1−x.

**Independent bound.** My residue bound for k ≥ 1 is an exact Laurent product in Arb with these intervals. For k > 30 I use a Cauchy
bound on \|h\| = ½, with these constants (Arb arc covers):
* min\|Γ(1−h)\| ≥ 0.806;
* min\|sin(πh/2)\| ≥ 0.7066;
* min\|sin πh\| ≥ 0.99999.

The tail ratio is less than 0.008/D.

I tested this bound against the **actual** residues of all 1144 fields, computed by PARI for k ≤ 6. There were **no violations**. The
largest ratio of actual to bound for the dominant real k = 2 term was 0.34 (R9409); for the complex k = 2 term it was 0.55. So my bound is
valid and not artificially tight.

| | lower term | rest (Atlas) | rest (mine) | relative margin (mine) |
|---|---|---|---|---|
| complex D = 5178 | T1 ≥ 2.95244e−3 | 3.377e−4 | 2.8288e−4 | 0.904 |
| real D = 5230, Atlas κ | T0 ≥ 1.67839e−3 (same value as Atlas) | 1.67770e−3 | 1.00584e−3 | **0.401** |
| real D = 5230, my κ | T0 ≥ 1.75761e−3 | — | 1.00584e−3 | 0.428 |

My k = 2 real bound is 1.006e−3, against Atlas's 1.678e−3. The difference comes from Atlas expanding Λ_L first and then using
per-coefficient absolute values (mstar2.residue_coeffs). Both bounds are rigorous; mine is smaller. Since mine is a valid upper bound and
Atlas's is larger, Atlas's positivity claim at 5230 is implied.

With my bound, the method's real threshold is **4448** with Atlas's κ, and 4390 with mine. The complex threshold is limited by T0 ≥ 0
alone: e^{2c_C} = 5177.78, so D ≥ 5178.

**One check covers all larger D.**
* **Complex:** D^{3/2}·(the bound) = const − Σ_k D^{1−k}Σ_{i≤1}c_{k,i}(log D)^i − tail. Each term is decreasing once log D ≥ 1, and
  T0 ≥ 0 for D ≥ 5178.
* **Real:** D·(the bound) = (4π²/ζ(2)²)·core(a(D)) − Σ_k D^{½−k}Σ_{i≤2}c_{k,i}(log D)^i − tail. Here core is increasing and the sum
  is decreasing for log D ≥ 4/3.
* **The tail:** it is D^{α−k} with k ≥ 31, so it is decreasing.
* **Numerical confirmation:** margin·D^{3/2} rises from 995 (D = 5178) to 1100 (D = 10¹²). Margin·D (real, Atlas κ) rises from 3.5
  (D = 5230) to 1462.

**Lemma 3.4(b):** if M\*(1) > 0, then M⁺ ≥ G(1+) = μ_K(O_K) + M\*(1) > 1. This is unconditional, as in the HKMS proof.

## Check 2. Field lists and M\*_K(1). **CONFIRMED**

Code: fields_mstar_v2.py, compare_mstar_v3.py. Outputs: runs_fields_mstar_v2.json, runs_compare_mstar_v3.json. About 8 min.

(v1 deadlocked in PARI's multithreaded lfuninit and was killed; it produced no output.)

**Completeness.** I compared against PARI `nflist("S3",[1,5196],1)` (762 fields) and `nflist("S3",[1,10^4],0)` + `nflist("C3",[1,10^4])`
(382 fields), matching fields by polredabs. Each Atlas binary cubic form was converted to a monic polynomial (a²f(y/a)), and both its
polredabs and its nfdisc were checked.

Result:
* 762/762 complex and 382/382 real fields match, with no missing, extra or duplicate fields;
* no form/discriminant mismatch;
* this includes all 760 complex fields with \|d\| ≤ 5177 and all 178 real fields with d ≤ 5229.

**M\*_K(1), recomputed for all 1144 fields, not only a sample of 40.** I used PARI's own Dedekind ζ (lfuncreate(pol)), Laurent series at
s = −k, with k up to 30, 20 or 14, at 60 digits. The last term is ≤ 1.8e−46. The known zero orders were truncated, and PARI returned exact
zeros there.

Agreement:
* every value lies inside the Atlas ball of **both** set A and set B (±1e−13), so there are 0 sign disagreements;
* the max \|Δ\| is 2.6e−9, which is inside that field's radius;
* the counts are 702 complex / 318 real with M\*(1) > 0, and 60 / 64 with M\*(1) < 0;
* the minimum values are K87 −0.532204 and R169 −0.616389. None is below −1.
* The largest \|d\| with M\* < 0 is 516 (complex) and 2300 (real).

All of this exactly as stated in MC T3. Spot checks: K23 = −0.467207286138490, R49 = −0.460251846030945. The seeded random sample of 40
is listed in runs_compare_mstar_v3.json.

## Check 3. Integer points. **CONFIRMED**

Code: intpoint_v2.py. Outputs: runs_intpoint_v2_all117.json (all 117 fields) and runs_intpoint_v2.json (the first 21-field pass).

**Logic.** Suppose the conjecture held. Then M_K(x)/√x is bounded on both sides. By HKMS Thm 2.10 this gives RH, simple zeros and
ζ_K(½) ≠ 0. By Prop 2.8, 1/\|ρζ_K′(ρ)\| ≤ M⁺, so the weights are bounded, and the hypotheses of Prop 3.3 hold.

Prop 3.3 then says that (M_K(x) + M\*_K(x))/√x is a limit point of M_K(x)/√x for every x > 0. M\* is continuous, and the set of limit
points is closed. So the one-sided value G(n+) = (Σ_{m≤n} c(m) + M\*_K(n))/√n is also a limit point, and M⁻ ≤ G(n+) ≤ M⁺.

Hence G(n+) > 1 forces M⁺ > 1, and G(n+) < −1 forces M⁻ < −1. Either contradicts the assumption. (This is the HKMS Table 2 procedure.)

**Recomputation.**
* c(n) = μ_K Dirichlet coefficients from PARI `direuler` over Π_{𝔓\|p}(1 − X^{f(𝔓)}) (idealprimedec). These are exact integers, checked
  equal to dirdiv(1, lfunan) for n ≤ 3000 in all 117 fields.
* M\*_K(n) comes from PARI Laurent series, including the log n terms.

Result: all **117** fields and **225** witness points were recomputed. Every one agrees with Atlas's bound to ≤ 5.3e−13, and every one is
beyond ±1. The smallest margin is R1573 at n = 170075, with G = 1.0061333.

The fields include:
* K44 (n = 926174) and R2292 (n = 978687);
* the one-sided K44, K76 and K104;
* the small-margin fields K76 (−1.00744), R257 (−1.01406) and R788 (−1.02505).

The 7 unsettled fields are exactly K23, K31, K59, R49, R81, R148 and R229.

## Check 4. The Ingham route (7 fields). **CONFIRMED**

Code: ingham_pari_v5.py (outputs runs_ingham5_<K>_T<T>.json), hstar_v1.py (log_hstar_v1.log), ingham_extra_v1.py.

**Logic.** VH check 1 carries over unchanged. Only the facts used there matter: a finite-order meromorphic ζ_K with a simple pole at 1,
the Dirichlet series 1/ζ_K, and real coefficients. The signature enters only through the weights.

If the conjecture held, then:
* RH, simple zeros, ζ_K(½) ≠ 0 and no real zeros would all follow (two-sided boundedness makes the Mellin integral converge absolutely
  for Re s > ½);
* hence M⁻ ≤ h\*_{K,T}(y) ≤ M⁺ by Ingham.

So only two inputs are non-WLOG: the completeness of the zero list below T, and the accuracy of the weights.

**Real-signature weight formula, re-derived.**
* For totally real K the Galois closure is totally real, so ρ(c) = I and γ_L = Γ_R(s)², with conductor D.
* At an L-zero, L′(ρ) = Λ′(ρ)/G(ρ) with G(s) = D^{s/2}π^{−s}Γ(s/2)², because Λ(ρ) = 0.
* ζ_K′ = ζ·L′ there, and ζ′·L at ζ-zeros.

Checks:
* PARI's lfundiv(ζ_K, ζ) has Vga [0,0] and conductor D for R49, R81, R148 and R229, and [0,1] for K23, K31 and K59.
* Λ′/G divided by PARI's L′ equals 1 + O(1e−18) at R229 zeros.
* At the R229 near-collision pair (ζ zero 329.033071680, L zero 329.033115243, gap 4.36e−5, weights ≈ ±1.4667), I computed ζ_K′(ρ)
  **directly** from PARI's Dedekind ζ. This needs no splitting and no disjointness assumption, and it agrees with Atlas's weights to
  7e−15 relative.

**Zeros: independent float route.**
* ζ zeros: PARI lfunzeros.
* L zeros: my own sign scan of PARI lfunhardy, with step 0.02, refined by solve(), plus local rescans with step 1e−5.
* The coarse scan missed close pairs. The local rescans recovered all of them: 5 pairs in R49 (smallest gap 0.0012 at 168.38) and 2 pairs
  in R81 (smallest gap 0.0014 at 109.59). Those rescans were guided by Atlas's ordinates, but each zero is my own sign change.
* My float argument-principle count N_L(T) = (1/π)[θ(T) + arg L along 5/2 → 5/2+iT → ½+iT] decides completeness independently.

| K | T | ζ zeros (mine = Atlas) | L zeros: my sign changes = my N_L(T) = Atlas | max rel. Δw vs Atlas | min ζ/L gap | nearest zero to T | ζ_K(½) |
|---|---|---|---|---|---|---|---|
| K23 | 600 | 341 | 979 = 979.000 = 979 | 3.8e−7 (wrot3 midpoints; radii 1.3e−5) | 3.1e−4 | 0.250 | −0.2542 |
| K31 | 800 | 491 | 1417 = 1417.000 = 1417 | 2.2e−10 | 2.5e−4 (701.30) | 0.039 | −0.3180 |
| K59 | 400 | 202 | 661 = 661.000 = 661 | 2.5e−11 | 9.5e−4 (301.65) | **9.4e−4** | −0.5507 |
| R49 | 600 | 341 | 1051 = 1051.000 = 1051 | 3.1e−11 | 1.5e−3 (353.49) | 0.263 | −0.1481 |
| R81 | 400 | 202 | 681 = 681.000 = 681 | 3.1e−11 | 1.8e−3 (295.57) | 0.015 | −0.2078 |
| R148 | 400 | 202 | 719 = 719.000 = 719 | 6.7e−12 | 3.9e−3 (349.31) | 0.015 | −0.3440 |
| R229 | 400 | 202 | 747 = 747.000 = 747 | 9.3e−11 | **4.4e−5** (329.03) | 0.015 | −0.4291 |

Notes on the table:
* Every zero matches Atlas's list one-to-one, with the same source (ζ or L).
* L(σ) > 0 on a 201-point grid of [½, 1] for every field. The minimum is at σ = ½: 0.101 (R49) up to 0.377 (K59).
* K59 has an L zero 9.4e−4 from T = 400. Atlas's enclosures exclude T. In any case f(γ/T) = O((1−γ/T)³) ≈ 1e−17 there, so h\* does not
  depend on which side it lies.

**h\*.** These are my own Arb sums: JP kernel, exact rational y, the L-ordinate taken as the full certified interval, and an assertion
that no enclosure meets T. They use Atlas's set A **and** set B weight balls, at both extreme y values per field plus two sample y values.

The certified values reproduced:
* K31: [1.06030365165 ± 1.4e−12] and [−1.14484986103 ± 2.6e−12];
* K59: 2.36240265548 and −2.38859700285;
* R49: 4.91110293634 and −4.78848345109;
* R81: 2.13278217596 and −2.15170145922;
* R148: 1.73152861622 and −1.72389656423;
* R229: 1.4421738700 and −1.5283516249;
* K23 (MC T5): [1.2383 ± 2.8e−5] and [−1.1886 ± 5.6e−5], and also 1.2056 / −1.1134 at the second pair of y.

All 12 extreme values for the six fields, and the K23 values, agree with Atlas's table, with the same radii.

The float h\* from **my own PARI weights** agrees with all of these to ≤ 7e−12 (K23: ≤ 6e−8, at the level of the wrot3 midpoint error).
Every certified value is beyond ±1 by at least 0.06 (K31 max: 1.0603).

## Check 5. Smoothed exact Mertens. **CONFIRMED** (sanity check only, not a proof step)

Code: smooth_dump_v1.py, smooth_v1.py. Output: log_smooth_v1.log.

The method is my own derivation: K_T(u) = (T/2π)·2ĝ(Tu)², with ĝ(x) = 2π cos(x/2)/(π² − x²). Concretely:
* the step function M_K is integrated exactly against the cumulative kernel (8-point Gauss–Legendre cells of width 1e−4, plus sub-cell
  quadrature at each log n);
* the window is \|u\| ≤ 4, with neglected tail ≤ 1e−8 if \|F\| ≤ 5;
* N = 1.25·10⁶, T = 400, y = 6, 8, 9, 10;
* M\* is the real-signature M\* from PARI.

| K | max \|smoothed − h\*(Atlas A)\| | max \|smoothed − h\*(my PARI weights)\| | smallest control deviation (no L / conj / wrong M\*) |
|---|---|---|---|
| R148 | 4.3e−11 | 4.3e−11 | 5.0e−2 / 0.53 / 0.70 |
| R229 | 5.0e−11 | 4.9e−11 | 1.0e−4 / 0.20 / 0.52 |

These are the two S3 real fields that Atlas flagged as having no second evaluator (RESULTS §7 item 3). Their zeros, weights, real-signature
M\* and μ_K are mutually consistent to 5e−11.

## Remarks (none affects the verdict)

1. **Wording.** MC §2 says "T0 ≥ 1.67839e−3 > rest ≤ 1.67770e−3, a thin margin". The thinness belongs to Atlas's bound, not to the
   threshold. A sharper and equally rigorous bound gives a 40% margin and D_{3,0} ≤ 4447. Atlas may quote either.
2. **Atlas's inputs.** As stated in RESULTS §0, the certified status of T4/T5 and of the six fields rests on Atlas's Arb certificates. I
   reproduced every one of them by independent floating-point computation. The threshold step (T1/T2) I re-proved rigorously.
3. **PARI as a start list.** PARI lfunhardy with a coarse step misses close zero pairs, as Atlas also found in its own A4. Completeness
   must come from a count, as both Atlas and I did.
4. **External results used as published.** HKMS Prop 3.3 rests on Jurkat's APD theorem, and Lemma 3.4 on Prop 2.8 / Thm 2.10. Ingham
   1942 Thm 1 is used with the JP kernel. These were not re-proved here beyond VH check 1.
5. **Process.**
   * I edited two of my own scripts before their first run: threshold_v1.py (an arc-cover radius set too small) and intpoint_v1.py
     (removed dead code).
   * I renamed my own empty log file log_ingham_R81_T400.log to log_ingham_R81_T400_v2_killed.log.
   * Superseded runs, all killed, were the v1 PARI run (multithread deadlock), ingham v2 (lfuninit without derivative order, about 11
     CPU-min wasted), v3 (coarse scan only) and v4 (a solve() bracket bug).
   * Later fixes went into new versioned files. No Atlas file was touched.

## Files (verify/)

threshold_v1.py, fields_mstar_v{1,2}.py, compare_mstar_v{1,2,3}.py, intpoint_v{1,2}.py, ingham_pari_v{1..5}.py, ingham_extra_v1.py,
hstar_v1.py, smooth_dump_v1.py, smooth_v1.py, queue_ingham_v{1..4}.sh, watchdog_v{1,2,3}.sh; runs_\*.json, log_\*.log, sm_\*_c.bin,
sm_\*_mstar.json. Hashes: SHA256SUMS_verify.txt.
