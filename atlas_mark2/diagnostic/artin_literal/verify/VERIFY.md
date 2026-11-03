# VERIFY: adversarial check of the artin_literal claim (2026-10-19)

Claim under test (`../RESULTS.md`, `../HYPOTHESES.md`): for the 15 S5 quintic fields of signature (1,2) with d = 8249, 17744.3, 19876, 25624, 27029, 27364,
27881, 29081, 30301, 32069, 33616, 34189, 37156, 38069, 38189, every hypothesis of Calegari, Math. Ann. 356 (2013), Thm 1.1 and Thm 1.2 holds.
So every irreducible representation of Gal(K~/Q) ≅ S5 is modular.

Rules followed: nothing was contacted or posted, and no existing file was modified. Every new file is in this directory. One process at a time
under nice 19. Peak footprint was 0.81 GB (one PARI lfun attempt that hit its stack cap); every other run used ≤ 0.74 GB.

## Verdict table

| # | check | verdict |
|---|---|---|
| 1a | Hypotheses of Thm 1.1 / 1.2 as printed (S5; c ∈ 2B; unramified at 5 with Frob_5 ∈ 2B; ζ_H ≠ 0 on (0,1)) | **CONFIRMED** for all 15 |
| 1b | "5 and 3 both split in E" (§3) as a hidden hypothesis | **CONFIRMED not needed** (see §1). The sentence is never used, and the cited input (Sasaki, Thm 1) has no condition at 3 |
| 1c | Other assumptions in the proofs (ramification at 2/3, real places, H, auxiliary primes, Lemma 4.x analytic steps) | **CONFIRMED**: no extra condition found. One expository gap in Lemma 4.10(4) is harmless (§1.4) |
| 2 | Permutation-character identity, the zeta identity, and the sign argument | **CONFIRMED** (own code, `v_group.py`) |
| 3 | Algebra: S5, signature, 5 unramified, Frob_5 ∈ 2B (f mod 5 and sextic mod 5), H, d_H | **CONFIRMED for 15/15** with own PARI code and own invariants (`v_pari.py`) |
| 4a | Re-run of verify_FE.py and calegari3 verify_k10.py | **CONFIRMED**: identical output, 15/15. These verifiers check JSON bookkeeping only (§4) |
| 4b | Independent PARI lfun values inside the certified enclosures | **CONFIRMED** where feasible: ζ_E for 15/15 at σ = 1/2, 3/4, 7/8 (45/45 inside); ζ_F for 17744.3 (3/3 inside). ζ_F for 8249 and 27881 **UNVERIFIABLE** under the 1 GB cap (PARI stack overflow) |
| 4c | Conductors and Γ-shifts used in all 60 certificates match independently computed |d_F|, D_E, |d_K10|, d_K and signatures | **CONFIRMED** 15/15 × 2 sets |
| 5 | Novelty (were any of the 15 already known?) | **UNVERIFIABLE**. Dwyer, BLMS 46 (2014) 51–58 gives "concrete examples", list not readable (Wiley 403). Overlap cannot be excluded |

No PROBLEM was found that breaks the claim. Two framing corrections follow (§6).

## 1. Calegari's paper read directly (`../src/x/S5ArtinWeb.tex`, `../src/S5.txt`)

### 1.1 Hypotheses as printed
* **Thm 1.1:**
  * Gal(K~/Q) = S5.
  * (1) c ∈ (12)(34).
  * (2) K~/Q unramified at 5, Frob_5 ∈ (12)(34).
* **Thm 1.2:** adds that ζ_H(s) ≠ 0 for real s ∈ (0,1), where E is the quadratic subfield, F is a degree-6 subfield and H = F·E.
  * The Math. Ann. print drops the clause defining H. The arXiv text and the proof both have H = F·E. Confirmed: `S5.txt` line ~70 vs the TeX.
* **Nothing else is assumed:**
  * no condition at 2 or 3;
  * no squarefree discriminant;
  * no tame ramification;
  * no auxiliary primes.

### 1.2 Where each hypothesis is used
* **c ∈ 2B:**
  * E is real (c ∈ A5);
  * ϱ over E is totally odd: ϱ(c)² = 1 and ϱ(c) is projectively non-trivial, so its eigenvalues are {1, −1}.
* **Frob_5 ∈ 2B, unramified:** only in Lemma 3.2 ("given the assumed conditions on ϱ(Frob_5)") to invoke Sasaki's Theorem 1.
* **ζ_H ≠ 0:** only in the last paragraph of §4.
  * If Ω (density-zero set of 4A primes) is infinite, μ_Ω has a real pole in (0,1).
  * Hence L(ρ5) has a zero there, since L(ϖ) is entire.
  * Hence ζ_H = ζ_F·L(η)·L(ρ5) vanishes there, since ζ_F and L(η) are holomorphic on (0,1).
  * I checked that the ρ5 in ζ_H (Ind_{D5}1 = Ind_{F20}1 + η + ρ5, trace +1 on 2A) is the same ρ5 that the Ω-argument compares with ϖ: L_p(ρ5) at 4A is (1+X²)(1−X)(1+X)², consistent with that table.

### 1.3 "5 and 3 both split in E": not a genuine hypothesis
* The sentence appears once (§3, first paragraph) and is never used again. 3 occurs nowhere else in the proof, the tables or the lemmas.
* Lemma 3.2 cites "Theorem 1 of [Sas11b]" (preprint). I fetched the published version: Sasaki, *On Artin representations and nearly ordinary
  Hecke algebras over totally real fields*, Doc. Math. 18 (2013) 997–1038, open access, saved as `Sasaki_DocMath18_2013.pdf`.
* **Its Theorem 1 verbatim:** "Let F be a totally real field. Suppose that 5 splits completely in F. Suppose that ρ … is a totally odd, irreducible,
  continuous representation satisfying: the image of proj ρ is A5; the projective image of the decomposition group at every place of F above
  5 has order 2. Then ρ arises from a holomorphic cuspidal Hilbert modular eigenform of weight 1 and L(ρ,s) is entire."
* **No condition at 3.** Sasaki's proof of mod-5 modularity (Lemma 6, Thm 7) only needs 5 unramified in F. It handles 3 by passing to a solvable
  extension F_Σ, choosing an elliptic curve that is ordinary at 3, and applying Kisin's theorem. His introduction says this removes the
  "3-distinguishedness condition" of Taylor. The likeliest explanation is that Calegari's sentence is a vestige of an earlier dependence on a
  condition at 3.
* **The 15 fields satisfy Sasaki's Thm 1:**
  * E is real.
  * 5 splits in E, since Frob_5 is even ((D_E/5) = +1, re-checked).
  * Each v | 5 has residue degree 1, so the decomposition group in Gal(K~/E) = A5 is ⟨Frob_5⟩, of order 2.
  * The projective image is A5, and ϱ is totally odd.
* **Independent confirmation** (`KhareLaRosaWiese_2206.08116.pdf`, Expo. Math. 2023, Thm 4.4): Pilloni–Stroh, Astérisque 382 (2016), Thm 0.3 proves
  every totally odd irreducible 2-dimensional ϱ over a totally real field is modular. That makes Lemma 3.2 unconditional. Khare–La Rosa–Wiese
  note that Calegari's Frob_5 condition is then superfluous, and that Dwyer [Dwy14] had already remarked this.
* **(D_E/3) re-computed:** +1 for 19876, 25624, 27364, 30301, 33616, 34189, 37156; −1 for the other 8, matching RESULTS.md. This is irrelevant
  by the above.

### 1.4 Other proof steps checked
* Lemma 3.1 (lift to GL2(F5)·Δ via Tate's H² = 0) has no hypotheses.
* §3 relies on Asai/Ramakrishnan, Kim and Asgari. These are cited theorems with no field-specific condition.
* Lemma 4.10(4), "standard argument", has an expository gap that is harmless:
  * If the abscissa σ_c of μ_Ω were 1, μ would have a singularity at 1. But L(ρ5,1) is finite and non-zero, as is L(ϖ,1), so that cannot happen.
  * If σ_c ≤ 0, each factor ((1+p^{−s})/(1−p^{−s}))² blows up at s → 0⁺. Then μ_Ω grows faster than any power of 1/s, which contradicts
    meromorphy.
  * So σ_c ∈ (0,1), and Landau gives a real pole there.
* No condition on ramification at 2, 3 or 5 (beyond 5 unramified) appears anywhere.

## 2. Group theory and the zeta identity (`v_group.py`, `v_group.json`; own code, no reuse)

* **Permutation characters** on the classes (1, 2A, 2B, 3A, 4A, 5A, 6A), with subgroups built from explicit generators:
  * S5: 1,1,1,1,1,1,1
  * A5: 2,0,2,2,0,2,0
  * S4: 5,3,1,2,1,0,0
  * F20: 6,0,2,0,2,1,0
  * D5 = F20 ∩ A5: 12,0,4,0,0,2,0
  * S2×S3: 10,4,2,1,0,0,1
* **Identity:** Ind_{D5} + 1 + Ind_{S4} = Ind_{F20} + Ind_{A5} + Ind_{S2×S3} = (18,4,6,3,2,3,1). **Exact.**
* **Also checked:**
  * Ind_{D5} = Ind_{F20} + η + ρ5;
  * Ind_{S2×S3} = 1 + ρ4 + ρ5 (Calegari's table);
  * S5 has exactly 6 subgroups of order 20, all conjugate to F20, so "a degree-6 subfield" is unique up to conjugacy.
* **Artin formalism:** equal characters give isomorphic representations. Artin L-functions are additive, and induction-invariant with
  L(Ind_U^G 1, s) = ζ_{K~^U}(s), *including* ramified Euler factors (defined on inertia invariants) and Γ-factors. Hence
  ζ_H·ζ·ζ_K = ζ_F·ζ_E·ζ_K10 exactly as meromorphic functions.
* **Sign argument:**
  * On (0,1) all six Dedekind zetas are holomorphic (Hecke: pole only at s = 1).
  * ζ < 0 there; certificates give ζ_K, ζ_F, ζ_E, ζ_K10 < 0.
  * So ζ_H = ζ_Fζ_Eζ_K10/(ζζ_K) < 0 on (0,1).
  * No Artin holomorphy is assumed; only Hecke and Artin formalism are used. **CONFIRMED.**

## 3. Algebra, independently (`v_pari.py`, `v_pari.json`, PARI 2.17.2)

* **Method:**
  * Only f and d are read from the original JSON.
  * I used *different* invariants from the original code:
    * F20: Σ_i x_i²(x_{i+1}x_{i+4} + x_{i+2}x_{i+3});
    * D5: Σ_i (x_i² x_{i+1} + x_i x_{i+1}²);
    * S2×S3: x0 + x1.
  * Each stabiliser was asserted to have order 20 / 10 / 12.
  * Resolvents come from PARI polroots with rounding (max rounding error 1.8e−8, root separation ≥ 0.02).
  * The result is cross-validated by irreducibility, polgalois and nfisincl, so this route is not rigorous on its own. The original Arb route is.
* **All 15 fields pass every item:**
  * polgalois(f) = S5;
  * polsturm(f) = 1, so signature (1,2) and c ∈ 2B;
  * nfdisc(f) = d;
  * f mod 5 squarefree with degrees (2,2,1), and idealprimedec(K,5) has e = 1, f = (1,2,2);
  * sextic resolvent (own invariant): polgalois = PGL(2,5) = S5(6), signature (2,2). Mod 5 it gives the 2B pattern (2,2,1,1), either by
    factorisation (10 fields) or by idealprimedec when 5 | disc g (17744.3, 30301, 34189, 37156, 38069): e = 1, f = (2,2,1,1);
  * own degree-12 h: irreducible, signature (4,4), with F ⊂ H, Q(√D_E) ⊂ H and K ⊄ H, so H = F·E. Frob_5 pattern (2,2,2,2,1,1,1,1) = 2B;
  * |d_H|·d_K = D_E·|d_F|·|d_K10| exactly (all 15); |d_H| = d⁶ for 9 fields (the 8 with squarefree d, plus 25624);
  * (D_E/5) = +1.
* **LMFDB:** labels match the polynomials for 8249, 17744.3, 33616 and 38189 (API, galois_label 5T5, r2 = 2). The remaining API calls were
  rate-limited. Labels are only names; the polynomials themselves were verified.

## 4. Certificates

* **4a.** `verify_FE_rerun.py` is a copy with the output path redirected. Its output is identical to `../runs/verify_FE.json`: 15/15 fields have
  F, E, K10, K OK in sets A and B, calegari3 sha256 match, and A/B overlap.
  * `verify_k10_rerun.py` (redirected copy) reproduces the calegari3 summary: all literal fields CERTIFIED in A and B, min K margin 0.95 > 0.
  * **Caveat:** these verifiers re-read JSON flags and margins (cover contiguity, margin > 0, residue overlaps). They do not recompute the analytic
    bounds, so their soundness still rests on the calegari3 evaluator lemmas and code (not re-audited here).
* **4b.** PARI lfun, non-rigorous:
  * ζ_E: 45/45 values (15 fields × σ = 1/2, 3/4, 7/8) lie inside the certified enclosures.
  * ζ_F (17744.3): −10.8675292175197, −16.3236979007053, −28.6636361178368 at 1/2, 3/4, 7/8. All are inside the certified balls (|diff| ≤ 4.7e−12
    vs radii ≥ 3.5e−12).
  * ζ_K(1/2) < 0 for all 15.
  * ζ_F for 27881 and 8249 overflowed a 600–700 MB PARI stack (logs kept) and was not pursued under the 1 GB cap.
* **4c.** In all 60 certificate JSONs (4 objects × 15 fields, sets A and B), N equals my independently computed |d_F|, D_E, |d_K10|, d_K. The
  Γ-shifts equal the signatures: F (2,2) → 0⁴1²; E → 0²; K10 (2,4) → 0⁶1⁴; K (1,2) → 0³1².

## 5. Novelty

* **Dwyer**, "Real zeros of Artin L-functions corresponding to five-dimensional S5-representations", BLMS 46(1) (2014) 51–58,
  doi:10.1112/blms/bdt075. The abstract (OpenAlex, Bristol Pure) says "giving concrete examples of five-dimensional representations that satisfy
  the additional conditions necessary to prove their modularity", via the explicit formula.
  * The full text was not obtainable: Wiley 403, ResearchGate 403, no arXiv version found, and the Bristol record has no PDF.
  * The examples are therefore unknown. Small discriminants such as 8249 or 17744 are natural candidates, so **overlap cannot be excluded**.
* **Calegari 2013** treats only d = 1609. Booker 2006 is a method paper.
* Citing works found (OpenAlex): Pierce–Turnage-Butterbaugh–Wood (Invent. 2020) and Khare–La Rosa–Wiese (2023). Neither lists fields.
* Calegari's blog post "The Artin conjecture is rubbish" (2014): the domain is hijacked and archive.org is blocked.
* **Conclusion:** novelty is UNVERIFIABLE. Say "to our knowledge", and if possible get Dwyer's list (library access or an author's copy) before
  any claim.

## 6. Most precise defensible statement

> For each of the 15 quintic fields K (LMFDB 5.1.8249.1, 5.1.17744.3, 5.1.19876.1, 5.1.25624.1, 5.1.27029.1, 5.1.27364.1, 5.1.27881.1,
> 5.1.29081.1, 5.1.30301.1, 5.1.32069.1, 5.1.33616.1, 5.1.34189.1, 5.1.37156.1, 5.1.38069.1, 5.1.38189.1), the following hold:
> * Gal(K~/Q) ≅ S5, K has signature (1,2), and 5 is unramified in K~ with Frob_5 ∈ (12)(34). These are exact and were verified twice independently.
> * ζ_H(σ) < 0 for all σ ∈ (0,1), where H is the degree-12 fixed field of D5. This follows from an exact Artin-formalism identity and
>   interval-arithmetic certificates for four Dedekind zeta functions; the certificate code has not been independently audited.
>
> Hence every hypothesis of Calegari's Theorems 1.1–1.2 (Math. Ann. 356 (2013)) holds. With Sasaki's Theorem 1 (Doc. Math. 18 (2013)) as the
> two-dimensional input, which needs no condition at 3, every irreducible complex representation of Gal(K~/Q) is automorphic. In particular,
> Artin's conjecture holds for these 15 Galois groups.
> **Novelty is "to our knowledge"**: Dwyer (BLMS 2014) gave unspecified examples that may overlap.

**Framing corrections relative to RESULTS.md:**
* **(i)** Drop the "3 split for only 7 of the 15" hedge. The published Sasaki Theorem 1 has no condition at 3, and Pilloni–Stroh make Lemma 3.2
  unconditional. All 15 stand equally.
* **(ii)** The algebraic hypothesis Frob_5 ∈ 2B is known to be superfluous (Dwyer 2014; Khare–La Rosa–Wiese 2023, via Pilloni–Stroh). So the
  "literal hypotheses" selection is not a substantive restriction. The real content is the certified non-vanishing of ζ_H on (0,1).
  * Fields of signature (1,2) with Frob_5 ∉ 2B are equally accessible to the same method.
  * Others (Dwyer) may have treated such fields.

## Files (all new)
* Code: `v_group.py`, `v_pari.py`, `v_lfun.py`, `v_lfun2.py`, `v_lfun3.py`, `v_lfun4.py`, `verify_FE_rerun.py`, `verify_k10_rerun.py`.
* Outputs: `v_group.json`, `v_pari.json`, `v_lfun_E.json`, `v_lfun2_F.json`, `verify_FE_rerun.json`, `verify_k10_rerun.json`, `v_lmfdb.json`, `*.log`.
* Sources: `Sasaki_DocMath18_2013.pdf`, `KhareLaRosaWiese_2206.08116.pdf`.
