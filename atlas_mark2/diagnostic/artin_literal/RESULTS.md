# artin_literal: Calegari's Theorem 1.2, all hypotheses as published, for the 15 literal fields (2026-10-18/19)

Files:
* `HYPOTHESES.md`: verbatim statements and the verification plan.
* `PREDICTIONS.md`: written and hashed before any analytic code ran; `PREDICTIONS.sha256` still verifies.
* Code: `grouptheory.py`, `algebra_flint.py`, `algebra_pari.py`, `zFE.py`, `cert_FE.py`, `verify_FE.py`, `validate_coeffs.py`, `pari_V3.py`.
* Outputs: `runs/`. Logs: `logs/`.

Nothing was contacted or posted. No file outside this directory was modified, except one appended row in
`../new_territory/TARGETS_LEDGER.md`. New tools: `/Users/kiosk/atlas_mark2/tools/paripy` (venv with cypari2 2.2.4 = PARI 2.17.2, plus
pypdf; 37 MB).

## 0. Bottom line

For each of the 15 fields
**8249, 17744.3, 19876, 25624, 27029, 27364, 27881, 29081, 30301, 32069, 33616, 34189, 37156, 38069, 38189** (LMFDB 5.1.d.k; polynomials
in `runs/algebra_flint.json`), every hypothesis of Calegari's Thm 1.1 and Thm 1.2 (arXiv:1112.1152 = Math. Ann. 356 (2013) 191–207) holds
as stated:

* (H0) Gal(K^gal/Q) = S5;
* (H1) complex conjugation is in the class (12)(34);
* (H2) K^gal/Q is unramified at 5 and Frob_5 is in the class (12)(34);
* (A) **ζ_H(s) ≠ 0 for real s ∈ (0,1)**, where H = F·E is the degree-12 compositum. In fact ζ_H(σ) < 0 on (0,1).

H0–H2 are exact computations, each done two independent ways. A is an interval-arithmetic certificate, via an exact factorisation of ζ_H
into Dedekind zeta functions, each certified negative on (0,1). **Calegari's remark that L(ρ5) ≠ 0 suffices is not used.**

**The theorem obtained (modulo the caveats in §5):**

> By Calegari, Math. Ann. 356 (2013), Thm 1.1 and Thm 1.2, for each of the 15 quintic fields K above, every irreducible complex
> representation ρ of Gal(K^gal/Q) ≅ S5 is modular: there is an automorphic π on GL(dim ρ)/Q, cuspidal if ρ ≠ 1, with L(π,s) = L(ρ,s).
> * dims 4, 6 are Thm 1.1;
> * dim 5 (ρ5 and ρ5⊗η) is Thm 1.2;
> * dims 1 are trivial and the quadratic character of E.
>
> In particular **the Artin conjecture holds for every representation of Gal(K^gal/Q)**: L(ρ,s) is entire for every non-trivial
> irreducible ρ. Consequently, for every subfield M ⊆ K^gal, ζ_M(s)/ζ(s) is entire (Dedekind's conjecture for these M, e.g. K10).

This is Calegari's Thm 5.1 wording ("any complex representation of Gal(K^gal/Q) is automorphic"), now for 15 more fields.

## 1. Algebraic hypotheses (exact; `runs/algebra_flint.json`, `runs/algebra_pari.json`, `runs/grouptheory.json`)

**All 15 fields pass every item below.**

**Route 1** (python-flint, own code; no PARI):
* f irreducible; a transposition Frobenius exists (first such p: 79, 71, 67, 103, 251, 79, 269, 17, 97, 59, 149, 31, 101, 167, 113 in
  list order), so Gal = S5.
* Exact Sturm count gives 1 real root of f, so signature (1,2) and c ∈ 2B.
* 5 ∤ d_K, 5 ∤ disc f. f mod 5 has pattern (2,2,1), so Frob_5 ∈ 2B.
* Frob_5 ∈ 2B again from mod-5 patterns of defining polynomials of **F, H and K10** with discriminant prime to 5 (orbit sums over F20, D5,
  S2×S3; each class pattern is unique). (D_E/5) = +1.
* The sextic resolvent g and h(x) = g(x²) are built from certified Arb root enclosures with exact integer rounding. Both are irreducible.
  Signatures (2,2) and (4,4) by Sturm.
* Frobenius consistency f/g/h/K10 (and the parity against (D_E/p)) at all good p < 3000 (421–427 primes per field): 0 failures.

**Route 2** (PARI 2.17.2):
* `polgalois(f)` = S5; `polgalois(g)` = PGL(2,5) = S5(6); `polsturm(f)` = 1; `nfdisc(f)` = d.
* idealprimedec(K,5): unramified, residue degrees (1,2,2). e = 1 above 5 in K, K10, F, E and H.
* nfisincl: F ⊂ H and E ⊂ H; K ⊄ H.

**H (degree 12) data:**
* |d_H| = D_E·|d_F|·|d_K10|/d_K holds exactly in all 15 fields (= d⁶ for the 10 squarefree d). |d_H| ranges from 4.8·10²⁰ (17744.3) to
  3.1·10²⁷ (38189).
* Local Artin identity Z_H·Z_Q·Z_K = Z_F·Z_E·Z_K10 at every p | 5·disc f.
* Dirichlet-series identity ζ_H·ζ·ζ_K = ζ_F·ζ_E·ζ_K10 coefficientwise for n ≤ 2·10⁴ (PARI dirzetak of all six fields).
* dirzetak(H) = the local-factor rule (Frobenius class → cycle type on S5/D5) for n ≤ 2·10⁴. Same for F.

**Group-theoretic derivation (independent of PARI's F and H).** At every ramified prime of every field, all (D, I) inertia/decomposition
pairs compatible with PARI's K, K10, E data give a single (e,f)-pattern on S5/F20 and on S5/D5. It equals PARI's F and H data.

**Published-text defect (HYPOTHESES §1):**
* The Math. Ann. statement of Thm 1.2 lacks the clause defining H ("…and let H be the compositum of F and E. Suppose that"). The arXiv
  version has it, and the proof uses it. We use the arXiv definition.
* F is unique up to conjugacy: all 6 subgroups of order 20 in S5 are conjugate to F20. So ζ_H is well defined.

## 2. Analytic hypothesis A: ζ_H(σ) ≠ 0 on (0,1)

**Direct (degree 12, N = |d_H|): infeasible (P4 met).**
* The planner needs X2 = 2.3·10¹² (17744.3) up to 1.3·10¹⁶ (38189) coefficients.
* The smallest case is roughly 2 CPU-years and ~6 TB of stored coefficients on this machine. Not attempted for any field.

**Factorisation route (rigorous).**
* Artin formalism plus the character relation Ind_{D5}1 + 1 + Ind_{S4}1 = Ind_{F20}1 + Ind_{A5}1 + Ind_{S2×S3}1 (grouptheory.py) give
  the identity of meromorphic functions ζ_H ζ ζ_K = ζ_F ζ_E ζ_K10. It was also checked numerically as Dirichlet series (§1).
* For σ ∈ (0,1): ζ(σ) < 0 (classical); ζ_K(σ) < 0 and ζ_K10(σ) < 0 (calegari3); ζ_F(σ) < 0 and ζ_E(σ) < 0 (here).
* So ζ_H(σ) = ζ_F ζ_E ζ_K10/(ζ ζ_K) < 0.
* Only Dedekind zeta functions and Hecke's theorem are involved. No holomorphy of a non-monomial Artin L-function is assumed.

**Certificates here** (`cert_FE.py`; calegari3's method and parameter sets A/B imported unchanged; Λ_M(σ) < 0 on [1/2,1) via
σ(1−σ)I_1(σ) < R, then the FE):
* **30/30 runs CERTIFIED** for ζ_F (degree 6, Γ_R⁴Γ_R(s+1)², N = |d_F|) and **30/30** for ζ_E (degree 2, N = D_E).
* `verify_FE.py` re-reads every JSON (ours and calegari3's K10/K JSONs, whose sha256 match calegari3/SHA256SUMS) and checks: exact
  contiguous rational cover of [1/2,1], every piece with positive margin, R > 0, all residue checks overlapping.
* Result: **15/15 fields have all four objects (F, E, K10, K) certified in both sets ⇒ ζ_H(σ) < 0 on (0,1).**

Selected numbers (set A; full data in `runs/cert/FE_*.json`):

| field | \|d_F\| | X2 (A) | ζ_F(1/2) | ζ_E(1/2) | min margin F (A/B) | time A/B (s) |
|---|---|---|---|---|---|---|
| 17744.3 | 2.18e10 | 3.8e6 | −10.8675 | −1.3463 | 15341 / 15383 | 11 / 13 |
| 33616 | 1.48e11 | 1.0e7 | −8.7817 | −3.2573 | 19793 / 19931 | 20 / 26 |
| 27881 | 4.42e11 | 1.9e7 | −4.1863 | −3.8319 | 12190 / 12358 | 32 / 49 |
| 8249 | 5.61e11 | 2.1e7 | −14.2641 | −3.4968 | 44847 / 45169 | 60 / 66 |
| 19876 | 1.96e12 | 4.1e7 | −16.7868 | −9.1748 | 71311 / 72170 | 113 / 163 |
| 27364 | 5.12e12 | 7.1e7 | −26.9796 | −12.3152 | 145648 / 147445 | 251 / 408 |
| 37156 | 1.28e13 | 1.1e8 | −12.9026 | −12.3400 | 83746 / 86436 | 715 / 964 |
| 25624 | 1.68e13 | 1.3e8 | −3.8472 | −8.9794 | 25716 / 27046 | 755 / 1238 |
| 27029 | 1.97e13 | 1.4e8 | −2.5230 | −2.4686 | 17048 / 18196 | 856 / 1440 |
| 29081 | 2.46e13 | 1.6e8 | −2.7216 | −5.0301 | 18343 / 20149 | 1228 / 1717 |
| 30301 | 2.78e13 | 1.8e8 | −42.9765 | −1.6751 | 350625 / 356578 | 1510 / 2152 |
| 32069 | 3.30e13 | 1.9e8 | −51.2520 | −1.6689 | 435688 / 443352 | 1674 / 2464 |
| 34189 | 4.00e13 | 2.1e8 | −0.90916 | −6.2607 | 4111 / 6056 | 2009 / 3281 |
| 38069 | 5.52e13 | 2.4e8 | −19.5088 | −1.0412 | 176873 / 185257 | 2699 / 4607 |
| 38189 | 5.57e13 | 2.4e8 | −52.7672 | −1.5078 | 506889 / 517794 | 2743 / 5053 |

ζ_E min margins: 14.4 (17744.3) to 224 (37156). ζ_K10(1/2) from calegari3 is in [−2.25, −0.175] for these fields.

## 3. Cross-checks and prediction outcomes (PREDICTIONS.md)

| # | outcome |
|---|---|
| V1 coefficients = PARI dirzetak, n ≤ 10⁵ | **Met for F (15/15), two sieve block sizes.** For E the first comparison **failed**: my zFE.py used 1 − χ(p)X, which is the L(χ) factor, instead of ζ_E's (1−X)(1−χ(p)X). Fixed **before any certificate ran**. Then 15/15 match (`runs/valid/coeff_hash_*.json`). The certificates all use the fixed code. |
| V2 residue checks pass, R rel. radius ≤ 1e−9 | **Met**: all 60 objects × 3 checks overlap. R_F rel. radius ≤ ~1e−13; R_E ≤ 2e−9. |
| V3 R vs PARI bnfinit (non-rigorous) | **Met**: R_F = 16 h Reg/w to rel. ≤ 4.3e−14 (all 15, beyond prediction); R_E = 2 h Reg to ≤ 1.2e−8 (the R_E ball radius limits it; "≥ 10 digits" missed for 17744.3 at 7.9 digits). PARI `lfun(ζ_F, 1/2)` for 17744.3 = −10.867529217519743592, inside our ball [−10.867529 ± 2.2e−7]. For 33616, PARI overflowed its 500 MB stack (not retried). |
| V4 A/B overlap at 5 points | **Met**, 15/15. |
| NC1–NC5 (d = 8249, both sets) | See §3.1. |
| P1 all certified | **Met** (60/60 objects). |
| P2 argmin on the σ = 1/2 piece, margin > 1 | Margin > 1: **met** (min 4111, 34189 F A; E min 14.4). Argmin on the first piece: **met for set A (15/15) and for ζ_E, missed for set B ζ_F in 11/15** (argmin on the second piece [41/80, 21/40], or [21/40, 43/80] for 34189), presumably because the jet-error term varies across the cover. Margin values are positive regardless. |
| P3 cost | X2(F) ≤ 0.85·X2(K10): **met** (max 0.79). Time ≤ 0.8× calegari3: **missed** (max ratio 1.01). Footprint ≤ 1.2 GB: **missed** in 12/30 runs (max 2696 MB, 38189 B, i.e. 90% of the 3 GB watchdog; no kill). Total 10.7 h wall, one process at a time, nice 19. |
| P4 direct ζ_H infeasible | **Met** (§2). |
| P5 disk < 50 MB | **Met** (~2 MB; venv 37 MB separate). |

### 3.1 Negative controls (8249; `runs/negctl/`, `logs/run_negctl.out`)

**22/22 variants rejected** (residue checks fail; both sets). The unmodified data pass the same checks in the production runs.
* ζ_F: R·(1±1e−8) (NC1); N → 2N, N → N/d (NC2); Γ_R⁶ and Γ_R²Γ_R(s+1)⁴ (NC3); a_97 + 1, and the ramified Euler factor at 73 replaced by
  (1−X)⁶ (NC4). 8 variants × 2 sets.
* ζ_E: D_E → 4D_E (NC5), R·(1+1e−8), Γ_R⁶. 3 × 2.
* As predicted for every item.

## 4. Calegari's hypotheses: status per field

Every row below is identical for the 15 fields (per-field data: `runs/algebra_*.json`, `runs/verify_FE.json`).

| hypothesis | verification | status |
|---|---|---|
| Gal(K^gal/Q) = S5 | flint (irreducible + transposition) & PARI polgalois | ✔ 15/15 |
| c ∈ (12)(34) | exact Sturm & PARI polsturm: 1 real root | ✔ 15/15 |
| K^gal unramified at 5 | 5 ∤ d_K (flint, PARI nfdisc) | ✔ 15/15 |
| Frob_5 ∈ (12)(34) | f, F, H, K10 patterns mod 5 (flint); PARI idealprimedec | ✔ 15/15 |
| E, F, H (degree 12) | fixed fields A5, F20, D5; certified-root polynomials; PARI inclusions; discriminant identity | ✔ 15/15 |
| ζ_H(σ) ≠ 0, σ ∈ (0,1) | ζ_H = ζ_F ζ_E ζ_K10/(ζ ζ_K), all certified < 0, two parameter sets | ✔ 15/15 (ζ_H(σ) < 0) |

## 5. Caveats (please read before any claim)

1. **Expert confirmation still recommended.** We verified the hypotheses. That Thm 1.2's proof is correct and complete is Calegari's
   (refereed, Math. Ann.). Specific points to put to an expert (ideally Calegari):
   * (a) **"3 split in E".** The proof text (§3) says "By assumption, E is real, and 5 and 3 both split in E". Nothing in the stated
     hypotheses implies 3 splits. It does split for only 7 of the 15 fields: 19876, 25624, 27364, 30301, 33616, 34189, 37156. It is inert
     in E for 8249, 17744.3, 27029, 27881, 29081, 32069, 38069, 38189. The sentence is not used visibly later (Lemma 3.2 cites only the
     Frob_5 condition for Sasaki's Theorem 1, a 2011 preprint we did not read). If Sasaki's theorem needed 3 split, the 7 fields would
     still be covered. **The most conservative statement is: all hypotheses as stated hold for all 15; the unexplained "3 split" remark
     holds for 7 of them.**
   * (b) The Math. Ann. text omits the definition of H in the statement of Thm 1.2. We use the arXiv/proof definition.
2. **Cited, not re-proved:** Hecke (continuation, FE, poles), Artin formalism (including ramified factors), ζ(σ) < 0, the calegari3
   evaluator lemmas (THEORY_GENERAL; code not formally verified), and Arb.
3. **Field data from PARI:** maximal orders at p | 5·disc f, |d_M|, ramified (e,f). These are cross-checked by the discriminant identity,
   the local Artin identity, the group-theoretic derivation, coefficient identities and the residue checks. bnfinit values (V3) are
   non-rigorous and used only as cross-checks.
4. The certificates for ζ_K10 and ζ_K are calegari3's (2026-10-13…17), re-verified here from their JSON (sha256 match). They were not
   re-run.
5. No novelty check was done here. Calegari 2013 has d = 1609 only; Dwyer (BLMS 2014, not readable) treated "several" fields with an
   unknown list, which may overlap these 15. Phrase any claim as "to our knowledge".

## 6. Reproduce

* `python grouptheory.py`; `python algebra_flint.py`; `paripy/bin/python algebra_pari.py`; `validate_coeffs.py ours|pari`
* `./run_all.sh` (production); `./run_negctl.sh` (negative controls); `python verify_FE.py`; `paripy/bin/python pari_V3.py <labels>`

The main venv is `/Users/kiosk/projects/atlas-rerun/.venv`. PARI scripts run with `/Users/kiosk/atlas_mark2/tools/paripy/bin/python`.
Checksums: `SHA256SUMS`.
