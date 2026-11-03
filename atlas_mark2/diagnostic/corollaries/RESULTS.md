# Free corollaries: RESULTS (2026-10-11)

Pre-registration: `PREDICTIONS.md`, sha256 `b9a6a176…d435` (`PREDICTIONS.sha256`), written before any computation here. Sources are in
`refs/` (arXiv PDFs and text extracted with pypdf). Raw outputs: `runs/`. Logs: `logs/`. The summary tables come from `python summarize.py`
(`logs/summary.txt`). File hashes: `SHA256SUMS`. Everything ran at `nice -n 19`, one process at a time (two light ones overlapped
briefly). Peak RSS was 140 MB or less. Total CPU time was about 1.5 h.

## 0. Headline

| item | statement | status |
|---|---|---|
| 1 | Super-positivity (Goldfeld–Huang Thm 1.2) for 11.a, 37.a1, 389.a1, all 270 complex cubic L(ρ_K) with \|d\| ≤ 2000 (this includes the 25 Tollis fields), and the 366 totally real S3 cubic L(ρ_K) with d ≤ 10⁴ | **proved** (corollary of existing certificates). Direct Taylor check: 0 negative coefficients in 655 × 2 parameter sets |
| 1′ | The 16 cyclic totally real cubics | GH Thm 1.2 **does not apply as stated** (ρ = χ ⊕ χ̄ is not cuspidal, and χ is not self-dual). Its proof gives the same conclusion for Λ(χ)Λ(χ̄) |
| 2 | ζ_K(1/2) ≠ 0 (in fact < 0) for all 652 cubic fields (270 complex, \|d\| ≤ 2000; 382 totally real, d ≤ 10⁴) | **proved**, by two routes for the complex fields |
| 2′ | Hayani's LI(L) central clause L(1/2, χ) ≠ 0 for every irreducible χ of Gal(L/Q), for the Galois closure L of each of the 652 fields | **proved**. But Hayani 2607.23150 names **no** explicit field, so nothing in that paper becomes unconditional |
| 3 | HKMS naive Mertens-type conjecture is **false** for Q(√5) and Q(√−3), with both M⁺_K > 1 and M⁻_K < −1 | **proved** (rigorous, no LLL needed). Together with HKMS Thm 1.1 this gives "false for every quadratic field" |
| 3′ | HKMS's own Q(i) number h*_{Q(i),600}(72.85) ≤ −1.008 is **not reproduced**: we get −0.9367231179 ± 3e−13. Their other value, ≥ 1.029 at y = −85.15, is reproduced (1.2002). We certify M⁻_{Q(i)} < −1 at y = 90.6694 instead | discrepancy in their paper; their theorem stands |
| 4 | Watkins Table 1, moduli −163, −17923, −115147: ξ₀ enclosed to about 19 digits; no real zero in (0, 1); the zeros with \|t\| ≤ T₀ are exactly the on-line pair ±ξ₀ | **proved** |

## 1. Item 1: super-positivity

### 1.1 Sources (quoted exactly; refs/1612.09359.txt, v3)
* GH Thm 1.2: *"Let π denote a self dual cuspidal automorphic representation of GL(n, A). For s ∈ C let Λ(s, π) be the completed
  L-function of π with functional equation Λ(s, π) = ±Λ(1 − s, π). Assume that Λ(s, π) ≠ 0 for s = σ + it where 1/2 < σ < 1,
  |t| ≤ σ − 1/2. Then π has the super-positivity property as in definition (1.1)."*
* GH Rem. 1.4: *"Theorem 1.2 provides a method to manually check if an individual L-function has the super-positivity property. It is
  enough to check, for example, that all the zeros of Λ(s, π) with imaginary part ≤ 1/2 are on the line Re(s) = 1/2. By examining the
  zeros of L-functions database [16] one sees that all the self dual L-functions in this database do indeed satisfy the super-positivity
  property."*
* Def. 1.1: (1) Λ^{(k)}(1/2, π) ≥ 0 for all k; (2) Λ^{(k)}(σ, π) > 0 for σ > 1/2 and all k; (3) Λ^{(k0)}(1/2) ≠ 0 ⇒ Λ^{(k0+2i)}(1/2) ≠ 0.
* Proof (§2). It uses only these facts: λ(s) = Λ(s + 1/2) satisfies λ(−s) = ±λ(s); λ is real and positive on the real axis to the right of
  the zeros; it is entire of order 1; and its Hadamard product groups the zeros into quadruples or on-line pairs.

### 1.2 Applicability, family by family
The triangle T = {1/2 < σ < 1, |t| ≤ σ − 1/2} lies in |t| < 1/2. Each existing certificate covers |t| ≤ 1 or more, including t = 0 (the
real segment).

| family | automorphic object | GH hypotheses | zero-free T from |
|---|---|---|---|
| 11.a, 37.a1, 389.a1 | weight-2 newforms (modularity), trivial central character ⇒ self-dual cuspidal GL(2) | yes | `../new_territory/CONTIG_RESULTS.md` (11.a, \|t\| ≤ 300), `ec37a`, `ec389a` (\|t\| ≤ 200; central orders 1 and 2 exactly; all other zeros on the line) |
| 270 complex cubic K, \|d\| ≤ 2000 | ρ_K: odd 2-dim. irreducible representation of S3, induced from a ring-class character of Q(√d) ⇒ weight-1 dihedral newform of level \|d\|; ρ orthogonal ⇒ self-dual | yes | `../new_territory/cubic_sweep/RESULTS_STAGE1.md`: every zero of L(ρ_K) with \|Im s\| ≤ 1 is on the line and simple |
| 25 Tollis fields (−23 … −239) | subset of the 270 | yes | same |
| 366 totally real S3 cubic K, d ≤ 10⁴ | ρ_K even dihedral ⇒ Maass cusp form (λ = 1/4), self-dual | yes | `../general_eval/RESULTS.md` P-A/E1: argument-principle count on [−1/16, 17/16] × [−1, 1], 0 zeros (344 fields) or exactly one on-line simple pair (38 fields) |
| 16 C3 (cyclic) totally real cubics (d = 49, 81, 169, 361, 961, 1369, 1849, 3721, 3969 ×2, 4489, 5329, 6241, 8281 ×2, 9409) | ρ = χ ⊕ χ̄ with χ cubic Dirichlet: **not cuspidal, χ not self-dual** | **no** | same certificate. GH's §2 argument applies verbatim to Λ(s, χ)Λ(s, χ̄), which is real, even about 1/2 and entire of order 1 |

**Theorem 1.** Let L be one of: L(s, 11.a), L(s, 37.a1), L(s, 389.a1); L(s, ρ_K) for each complex cubic field K with |d_K| ≤ 2000 (270 fields);
or L(s, ρ_K) for each non-Galois totally real cubic field with d_K ≤ 10⁴ (366 fields). Then the completed Λ(s) has the super-positivity
property of GH Def. 1.1: Λ^{(k)}(1/2) ≥ 0 for all k, and Λ^{(k)}(σ) > 0 for all σ > 1/2 and all k. For the 16 cyclic cubics the same holds
for Λ(s, χ)Λ(s, χ̄) = Λ(s, ρ_K), by GH's proof (not by GH Thm 1.2 as stated).

**Direct check (P1, two parameter sets; `cubic_central.py`, `gecert.py`).** We computed certified enclosures of c_k = Λ^{(k)}(centre)/k!
for k ≤ 40 (set A) and k ≤ 48 (set B). These are general_eval node values plus trapezoid and node error per coefficient, plus a
Cauchy bound for the n > X tail (gecert docstring). There is also an A-split data check per L-function.

| family | n | certified negative c_k | other parity encloses 0 | A-split pass | min j0 (A / B) |
|---|---|---|---|---|---|
| curves | 3 | 0 | 3 | 3 | 14 / 18 |
| complex cubic | 270 | 0 | 270 | 270 | 14 / 18 |
| totally real cubic | 382 | 0 | 382 | 382 | 16 / 18 |

Here j0 is the largest index up to which every coefficient of the non-vanishing parity is certified > 0. P1 predicted ≥ 10: **held**.
Independent cross-check for the curves, in this Λ normalisation (= 2× the ec37a/ec389a normalisation): 37.a1 c_1 = 0.592477817399601,
which is 2 × Λ′(1) = 2 × 0.2962389087; 389.a1 c_2 = 4.76702868626781, which is 2 × Λ″(1)/2. Both match the earlier certified values.

## 2. Item 2: ζ_K(1/2) ≠ 0 and the LI(L) central clause

### 2.1 Sources (exact)
* Kandhil, arXiv:2212.00324v2, §1: *"Armitage [1] gave examples of number fields K for which ζK(1/2) = 0. On the other hand, it is believed
  that ζK(1/2) ≠ 0 when K is an Sn-number field, that is, a number field of degree n whose normal closure has Galois group Sn over Q."*
* Hayani, arXiv:2607.23150v1, §1.3: *"LI(L): We assume LI−(L). Moreover, we assume that L(1/2, L/Q, χ) ≠ 0 if χ is an orthogonal or
  unitary irreducible character of G+."*

**Theorem 2.** For each of the 270 complex cubic fields with |d_K| ≤ 2000 and the 382 totally real cubic fields with d_K ≤ 10⁴,
L(1/2, ρ_K) > 0, hence ζ_K(1/2) = ζ(1/2) L(1/2, ρ_K) < 0. This covers all 636 S3 cubic fields in these ranges (Kandhil's "S_n-number
field", n = 3) and the 16 C3 fields.
* Smallest values: L(1/2, ρ) = 0.174036326987934 ± 2.5e−16 (complex, d = −23); 0.0713869670929816 ± 5e−17 (real, d = 9409, a C3 field).
  Set A and set B overlap for all 652 fields.
* Second, independent route for the complex fields: the sweep certificate (simplicity for |γ| ≤ 1) plus the even central order already
  imply L(1/2, ρ_K) ≠ 0 (THEORY_SWEEP §0.2). For the totally real fields the general_eval box count (0 zeros, or one pair at t ≠ 0)
  includes s = 1/2.

**Theorem 2′ (LI(L) central clause).** For the Galois closure L of each S3 field above, the irreducible characters of S3 are 1, sgn and ρ,
all orthogonal. We have ζ(1/2) ≠ 0, L(1/2, ρ_K) > 0, and L(1/2, χ_D) > 0 for the quadratic resolvent (D = the fundamental discriminant
of Q(√d_K)). That is 588 distinct D, certified in two sets; the smallest is L(1/2, χ_9413) = 0.0674933265 ± 5e−11. For the C3 fields,
L(1/2, χ)L(1/2, χ̄) = L(1/2, ρ_K) ≠ 0. So Hayani's non-vanishing clause holds for all 652 Galois closures.

**Hayani's paper names no fields.** We read §1.1–1.3 and searched the full text for explicit polynomials, LMFDB labels and "example".
Its constructions (Thm 1.5) have Gal(L/Q) ≅ S_{q⁴} with q ≡ 1 (mod 2p(p−1)), e.g. S_{13⁴} for p = 3. These are existence results,
far beyond any computation. So the ask "for whatever fields it names" is **empty**, as P2c predicted. The S3 statement above is the
generic instance only. The clause is one of three hypotheses (GRH, LI⁻, central clause), and the other two remain.

## 3. Item 3: HKMS naive Mertens-type conjecture for Q(√5) and Q(√−3)

### 3.1 Source (exact; refs/2109.06665.txt, v2, remark after Thm 1.1)
*"While the basic statement |MK(x)| ≤ x^{1/2} for all x ≥ 1 is false for K = Q(√−3) and K = Q(√5) (an easy computation demonstrates that
MQ(√−3)(7) = −3 and MQ(√5)(11) = −4), the methods of this paper are not immediately capable of demonstrating that the naïve
Mertens-type conjecture fails for these fields (as this requires knowledge of limiting behavior), unlike the other cases of the previous
theorem. It is, however, likely that computations analogous to those used in [OtR85] to falsify the original Mertens conjecture would
suffice for both of these quadratic fields as well."*
The conjecture: *"(The naïve Mertens-type conjecture over K). −1 ≤ M⁻_K ≤ M⁺_K ≤ 1."* For Q(i) they wrote: *"A computation demonstrates
that h∗_{Q(i),600}(72.85) ≤ −1.008 and h∗_{Q(i),600}(−85.15) ≥ 1.029."*

### 3.2 What must be computed (from HKMS §3.1–3.2)
* Lemma 3.4 / Thm 2.10: if RH fails for ζ_K, or ζ_K has a multiple zero (including at 1/2), then M⁺_K = ∞ or M⁻_K = −∞, and the
  conjecture is false.
* Otherwise, by the display after their Table 2, for every fixed T: M⁻_K ≤ liminf h*_{K,T} ≤ h*_{K,T}(y) ≤ limsup h*_{K,T} ≤ M⁺_K, with
  h*_{K,T}(y) = Σ_{|γ|<T} f(|γ|/T) e^{iγy}/(ρ ζ_K′(ρ)) and f(u) = (1−u)cos πu + sin(πu)/π (eq. 3.6). The middle inequality uses almost
  periodicity of the finite sum.
* So it suffices to have: (a) a **certified complete** list of the zeros of ζ_K = ζ · L(χ_D) with 0 < γ < T, all on the line and
  simple, with no ζ zero equal to an L zero; (b) certified 1/(ρ ζ_K′(ρ)); (c) one y with |h*| > 1. An Odlyzko–te Riele LLL search is
  **not** needed, because a direct scan finds y.

### 3.3 Method (`lzeros.py`, `run_zeros.py`, `hstar.py`, `hkms_certify.py`)
* **Zeros.** Arb Hardy Z for ζ, χ_5, χ_−3 (and χ_−4 as a control). Every sign change is bisected at exact dyadic points to width 2^−90
  (set A) or 2^−100 (set B).
* **Completeness.** At checkpoints every 100 (A) or 125 (B), up to about 1000, we use an argument-principle count
  N(T) = (1/π)[θ(T) + arg_c L(1/2 + iT)] (+1 for ζ) on [−1, 2] × [0, T], using Λ(1 − s̄) = conj Λ(s):
  * arg L on Re s = 2 is principal, since |L − 1| ≤ ζ(2) − 1 < 1;
  * on the top edge, Arb ball evaluations exclude 0 piece by piece;
  * the bottom edge needs Λ(σ) > 0 on [1/2, 2]. That comes from a general_eval jet on [1/2, 1] and the Euler product beyond 1; for ζ
    it is classical.
  The count equals the number of sign changes at every checkpoint, for every L and both sets (0 rescans).
* **Agreement checks.** The ζ list agrees with Arb's own rigorous `zeta_zeros` (an independent algorithm). The A and B lists agree to
  float precision: 649 / 904 / 823 / 868 zeros below about 1000 for q = 1 / 5 / 3 / 4.
* **Weights.** ζ_K′(ρ) = ζ′(ρ)L(ρ) or ζ(ρ)L′(ρ), via Arb series evaluated on the ordinate ball. The zero intervals of ζ and L(χ_D)
  are disjoint, which is asserted.
* **h\*.** A float scan proposes y, which is untrusted. The certificate is Arb evaluation of the whole sum at an exact rational y.
* **Diagnostic** (`diag_mertens_check.py`, `logs/diag_mertens_check.log`; not part of the proof). We smoothed the actual Mertens
  function M_K(x) (computed exactly to 3·10⁶ from μ * μχ) with the JP kernel and compared it with h* from our zeros:
  * Q(i) and Q(√−3): agreement to ~1e−4 at y = 8…14.
  * Q(√5): the difference is e^{−y/2}(4.156y − 7.55) to 3 digits. That is exactly the omitted M*_K term, since the double pole at s = 0
    gives slope −1/ζ_K′(0) = 2/log((1+√5)/2) = 4.156.
  This validates the weights, the signs and the y convention.

### 3.4 Results (all certified; `runs/hkms_cert_{A,B}.json`)

| K | set, T | y | h*_{K,T}(y) |
|---|---|---|---|
| Q(√5) | A, 600 (341 + 493 zeros) | 720.3427 | **1.05738521285 ± 4.4e−12** |
| Q(√5) | A, 600 | 722.7391 | **−1.06722864784 ± 3.8e−12** |
| Q(√5) | B, 990 (640 + 893 zeros) | 17736.1391 | **1.16984379838 ± 4.0e−12** |
| Q(√5) | B, 990 | 12927.3821 | **−1.14508971708 ± 2.4e−12** |
| Q(√−3) | A, 600 (341 + 445) | 84.5099 | **1.46764443125 ± 2.9e−12** |
| Q(√−3) | A, 600 | 800.8885 | **−1.59399508786 ± 2.0e−12** |
| Q(√−3) | B, 990 (640 + 813) | 9955.0694 | **1.77149932910 ± 3.4e−13** |
| Q(√−3) | B, 990 | 800.8888 | **−1.76750184246 ± 3.2e−12** |
| Q(i) (control) | A, 600 | −85.1474 / 90.6694 | 1.22097248997 / −1.19330058033 |
| Q(i) (control) | B, 990 | −85.1492 / 90.6693 | 1.28925963780 / −1.29503349656 |
| Q(i), HKMS's point | A, 600 | 72.85 | −0.936723117924 ± 3e−13 (HKMS: ≤ −1.008) |

**Theorem 3.** M⁺_K > 1 and M⁻_K < −1 for K = Q(√5) and K = Q(√−3). In fact M⁺ ≥ 1.1698 and M⁻ ≤ −1.1450 for Q(√5), and
M⁺ ≥ 1.7714 and M⁻ ≤ −1.7675 for Q(√−3), whenever M^± is finite. The naive Mertens-type conjecture is therefore false for both fields.
With HKMS Thm 1.1 it is false for **every** quadratic field. This is unconditional: either RH/simplicity fails and HKMS Lemma 3.4
applies, or our certified lists are exactly the zeros in the sum. P3a and P3b held, and both signs were found for both fields (P3b's
50% case).

**Q(i) discrepancy.** Our h*_{Q(i),600}(72.85) = −0.9367231179 is validated three ways: the actual-Mertens diagnostic, two parameter
sets, and the minimum near 72.85 (−0.9447 at 72.8483). It does not satisfy HKMS's "≤ −1.008". The value approaches −1 only as T grows
(−0.989 at T = 800). Their M⁺ bound (≥ 1.029 at −85.15) is consistent with ours. Their Thm 1.1(a) for Q(i) is still true: we certify
h* = −1.1933 at y = 90.6694 (T = 600). This is worth a polite note to the authors. (Not sent; per instructions, no contact.)

**Caveats.**
* We rely on HKMS's stated relation M⁻ ≤ h*_{K,T} ≤ M⁺ (Ingham's method with a non-negative kernel). We checked its numerical content
  (the diagnostic) but did not re-derive their Prop. 2.12 / Thm 2.10.
* The argument-principle count uses Arb's `dirichlet_l` / `zeta` / `hardy_z` / `lgamma` as trusted primitives.

## 4. Item 4: Watkins Table 1 moduli

Source: HOLES_TO_CLOSE §1.7 quoting Watkins §3: *"choose a modulus k for which we know a low-height zero 1/2 + iξ₀ of L(s, χ_k) which is
on the half-line"*, and *"It is in this step that we require the 13-digit precision on the location of the zeros."* Watkins's paper itself
was **not** retrieved (the AMS PDF is paywalled), so we compare only with the 4-digit values in our notes.

**Theorem 4** (`watkins.py`, sets A and B agree). For χ = (−q/·), q ∈ {163, 17923, 115147}:
* (a) L(1/2 + iξ₀, χ) = 0 with
  * ξ₀ ∈ 0.2029013374987986130 ± 5e−20 (q = 163)
  * ξ₀ ∈ 0.0309857994984843340 ± 7e−20 (q = 17923)
  * ξ₀ ∈ 0.0031576171546142824 ± 8e−20 (q = 115147)

  These come from a certified sign change of Hardy Z and match the quoted 0.2029, 0.03099, 0.003158.
* (b) L(σ, χ) > 0 for σ ∈ [1/2, 1], using a general_eval jet with adaptive subdivision. The minimum lower bound is 2.3e−6 for
  q = 115147, where Λ(1/2) = 0.00057743501620 ± 9e−15. With the Euler product and the FE, there is no real zero in (0, 1).
* (c) The argument-principle count in [−1/16, 17/16] × [−T₀, T₀], with T₀ = 1/2, 1/16, 1/128, is exactly 2.

So the zeros with |t| ≤ T₀ are exactly the conjugate on-line pair 1/2 ± iξ₀, simple, and not two real zeros. The cross-check of |L| at
1/2 + i/4 by two independent evaluators (Arb Hurwitz route vs general_eval Mellin–Barnes) overlaps in all 6 runs.

Run note: the first pass used a fixed 64-piece real-segment cover, which failed for q = 17923 and 115147 in set A because the pieces were
too coarse near the tiny Λ(1/2). That log is kept as `logs/watkins_v1_nonadaptive_realseg.log`. `gecert.real_segment` was then made
adaptive and all six runs were repeated (`logs/watkins.log`). The zero-list runs of item 3 used the earlier non-adaptive version, which
passed.

## 5. Pre-registered predictions vs outcome

| # | prediction | outcome |
|---|---|---|
| P1 | 0 negative coefficients; j0 ≥ 10; 37.a1 c_1 > 0, 389.a1 c_0 = c_1 = 0 (enclose 0), c_2 > 0 | **held** (min j0 14/18) |
| P2a | Λ(1/2, ρ_K) > 0 for all 652, both sets | **held** |
| P2b | L(1/2, χ_D) > 0 for the resolvents | **held** (588 D) |
| P2c | Hayani names no explicit field | **held** |
| P3a | sign changes = argument-principle counts, ζ and L zeros disjoint, to T2 | **held** (both sets, 0 rescans) |
| P3b | direct search finds \|h*\| > 1, at least one sign per field (70%), both signs (50%) | **held, both signs for both fields** |
| P4 | ξ₀ agrees with the quoted digits; no real zero; box count 2 | **held** (after the adaptive real-segment fix; first pass failed as reported) |

## 6. Novelty (brief check; no WebSearch)
Tools used: arXiv API (rate-limited), OpenAlex citation lists, and the full text of Martin et al., *An annotated bibliography for
comparative prime number theory* (arXiv 2309.08729, refs/).
* **HKMS:** OpenAlex lists 1 citer, the annotated bibliography. Its entry [356] still states the exceptions K ≠ Q(√−3), Q(√5). We found
  no resolution. **Moderate confidence this is new.** It is small: it completes "false for every quadratic field".
* **GH super-positivity:** the citers (Monotonicity properties of L-functions, 2018; level-aspect super-positivity, 2018; Eichler
  cohomology, 2017/2020) prove families or theory. GH Rem. 1.4 already says LMFDB lists "indeed satisfy" it, which is non-rigorous. Ours
  is the rigorous version for named L-functions. **Low novelty, bookkeeping.**
* **ζ_K(1/2) ≠ 0:** Kandhil's citers are theory papers (2405.02419; Gun–Sahu 2026, which is about parity of real zeros). Floating-point
  values of L(1/2, ρ) are in PARI and LMFDB. Tollis's rigorous counts for the 25 fields probably already exclude a central zero. **Low
  novelty**: a certified table for 652 fields.
* **Watkins:** the on-line status is in Platt's range. What is new is an interval-certified enclosure of ξ₀ and the explicit "pair, not
  two real zeros" certificate. It is a rigor footnote.

## 7. Files
* `PREDICTIONS.md`, `PREDICTIONS.sha256`
* `lzeros.py`, `run_zeros.py`, `run_zeros_all.sh` (zero lists)
* `hstar.py`, `hkms_certify.py` (h*)
* `gecert.py` (general_eval wrapper)
* `cubic_central.py`, `run_central_all.sh` (items 1–2)
* `watkins.py`, `run_watkins.sh`
* `summarize.py`, `diag_mertens_check.py`
* `refs/`, `runs/`, `logs/`

**Code-version notes.**
* `CODE_SHA256_zeros.txt` and `CODE_SHA256_central.txt` hold the hashes at first run.
* `cubic_central.py` changed once: the resolvent pass called isqrt on negative d. This affects only the resolvent family, which was
  then re-run in both sets.
* `gecert.py` changed once: the adaptive `real_segment`. `central_jet` did not change.
* `watkins.py` changed once: an Arb `acb` sign comparison. It crashed before producing any output.
* Final hashes are in `SHA256SUMS`.

**Addendum 2026-10-11 (independent verification, verify_hkms/VERIFY.md).** Item 3 CONFIRMED by independent code and zeros (all values to 12 digits). Wording: M⁻_K ≤ h*_{K,T}(y) ≤ M⁺_K follows from Ingham 1942 Thm 1 (Jurkat–Peyerimhoff kernel, as in Odlyzko–te Riele 1985) plus Landau, needing only simple zeros below T, ζ_K(1/2) ≠ 0 and no zero at height T — all certified; drop the 'did not re-derive' caveat and 'whenever M± is finite'. Q(i): HKMS's printed h*_{Q(i),600}(72.85) ≤ −1.008 is not reproduced under any of 9 conventions (we get −0.936723117924; ≤ −1.008 first holds near T ≈ 890); say 'consistent with (we get 1.2002)' for their other value; their Thm 1.1(a) for Q(i) still holds. Cite the published version: Math. Proc. Camb. Phil. Soc. 177 (2024) 481–523, which still excepts Q(√5) and Q(√−3).
