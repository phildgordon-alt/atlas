# audit2: independent audit of the general_eval L-function evaluator (2026-10-19)

**Scope.** `THEORY_GENERAL.md`, `geval.py`, and the code paths the S5 certificates use:
* `calegari3/{ev3,zk10,cert_k10}.py` with `calegari3/THEORY.md`;
* `artin_all/{zFE,cert_FE}.py` with `artin_all/THEORY.md` §5. These are byte-identical to the artin_literal copies (`diff`).

**Rules followed.**
* Nothing outside `audit2/` was written, and no file was edited.
* Mutations are applied in memory to a copy of the geval source (`alib.load_geval`). No mutated file exists.
* One process at a time, nice 19, watchdog at 1000 MB (`wd.sh`).
* Two PARI `lfun` attempts on F overshot the cap before the 1 s poll killed them: 1111 MB and 1480 MB, for a few seconds. Every evaluator run stayed ≤ 462 MB.

**Earlier audit.** The partial audit in `../audit/` was read, not modified. Its results are cited where used: G1/G2′ pointwise checks, term-by-term actual/bound ratios, half/zero mutations, and 5 calegari3 fields against PARI. Everything below was re-run or extended here.

## Verdict

**The calegari3 (ζ_K10, ζ_K), artin_literal and artin_all (ζ_F, ζ_E) real-segment certificates stand.**
* No critical finding.
* Every error bound was re-derived and matches the document and the code. No analyticity, constant or sign error was found.
* In 1,000+ stress comparisons, no enclosure missed the truth (§3). Adversarial parameters only widen the radii.
* The only rigour defects are 4 minor items (§2). None can affect any verdict, and each is closed by an explicit slack argument.

**Robustness.** The certificates do not depend on tight bounds.
* Production jet errors are ≈ 4–10·10⁻¹² (`trap_node` ≈ 10⁻¹⁷, Taylor ≈ 10⁻²³, tail_X ≈ 4·10⁻¹²).
* The smallest cover margin is 0.78 (13116.1 F, set A).
* A verdict could flip only if the error bounds were too small by a factor of about 10¹¹.
* The artin_all "near-misses" are not precision near-misses.
  * The true separation for 13116.1 F is |σ(1−σ)Λ_F(σ)| ≈ 245 near σ = 1/2 (Λ_F(1/2) = −979.14).
  * For 18485.1 F it is ≈ 124 (Λ_F(1/2) = −495.48).
  * The small cover margins come from interval over-estimation of q·I − R on cover pieces: two terms of size ≈ R ≈ 5·10⁴ cancel. They do not come from the error terms.
* So the real risk is a systematic error (wrong formula or wrong data), not a loose or tight constant. The independent PARI/Arb comparisons in §3 target exactly that.

## 1. Re-derivation, item by item (all agree with document and code)

| item | check | status |
|---|---|---|
| Lemma A′, (MB) | ∫₁^∞ t^{s−z−1}dt = 1/(z−s) needs Re z > Re s. Fubini holds. Dual family at K_w − s. dz = i dy gives 1/2π. Code: `jet` kernels u1 = 1/(z−s0), u2 = 1/(z−(K_w−s0)), factor (−1)^k on the dual, conjugate nodes for y < 0 (V(z̄) = conj V(z) for real a_n). | ✓ |
| (J), jets | Expansions converge for \|h\| < c − Re s0 and \|h\| < c − Re(K_w − s0). Code asserts d − ρ > 0. | ✓ |
| Lemma G1 | DLMF 5.8.3 product; keep k < K_Γ. B_j = 2(α_j + K_Γ − 1) ≤ B. ∫(1+y²/B²)^{−p} = B√π Γ(p−½)/Γ(p) for p > ½ (code: p ≥ 3/2). Pointwise ratio ≤ 1 (`../audit/runs/lemmas.json`). The integral is only 30–54 % of the bound (`runs/slack.json`). | ✓ |
| Lemma G2/G2′ | Stirling with K = 1: \|R\| ≤ sec²(½ph)/(12\|w\|) ≤ 1/(6\|w\|). τ·ph w ≥ πτ/2 − α (arctan x ≤ x). \|w_j\| ∈ [\|y\|/2, \|y\|/2 + α_j]. The constant C_Γ is identical in doc and code (`stirling_C`). Pointwise ratio ≤ 0.95. | ✓ |
| Lemma Tr | Trefethen–Weideman 2014 Thm 5.1, stated correctly. The strip shift y → y + ib moves Re z to c − b. The integrand is analytic iff c − a > max(Re s0, Re(K_w − s0), −min μ). Code asserts `lo > max(re_d1, re_d2, 0)`; a = frac·a_max with frac ≤ 15/16, floored to 1/1024, so strictly inside. γ·Q is log-convex (Γ log-convex; Q a positive sum of exponentials), so the max is at the strip edges. Bint increases in σ′. \|z − s0\| ≥ Re z − Re s0. The A-split factor sup is taken over the strip. | ✓ |
| Lemma Nt | Omitted nodes satisfy \|y\| ≥ Y + h. The code uses Y′ = Y − h, which is conservative by 2h. g is decreasing iff λ > P_e/(y + b); asserted (`slope.lower() > 0`). ∫_{Y′}^∞ g ≤ g(Y′)/slope. Factor 2 for both signs. | ✓ |
| Lemma TJ | \|c_k\| ≤ (1/2π) Q(c)γ(c)Bint(c)(d1^{−k−1} + d2^{−k−1}). Geometric tail (ρ/d)^{K+1}/(d − ρ). | ✓ |
| Lemma D | Binomial series valid for \|u\| < 1 (δ_C ≤ δ < 1, from m(1−δ) ≤ lo and hi ≤ m(1+δ), exact rationals). \|binom(−z,j)\| ≤ (\|z\|)_j/j!. t_{j+1}/t_j = δ(\|z\|+j)/(j+1) ≤ q for j ≥ J+1 **when \|z\| ≥ 1** (see m4). zmax = \|c + iY\| ≥ \|z_m\|, and t is monotone in \|z\|. \|x_m^{−z}\| = x_m^{−c}. Moments are exact Python integers, converted to Arb balls. The remainder is added as a box acb(r, r) ⊇ disc of radius r. | ✓ |
| Q(σ) | Singletons exact. Cells use the lower end lo, valid for σ ≥ 0 (asserted). | ✓ |
| Lemma X | φ > 0 and φ(x) ≤ x^{−c′}γ(c′)Bint(c′)/2π. G(σ,x) ≤ …/(c′−σ). \|G(s,x)\| ≤ G(Re s, x), increasing in σ. Rankin requires β − c′ + w/2 < 0 (asserted). ζ(β)^r with \|a_n\| ≤ d_r(n). A-factors: first family A^{σ−c′}, dual A^{c′+σ−K_w}, both maximised at σ_hi when A ≥ 1. Code formulas match exactly. | ✓ |
| Middle-range cells | The bound uses x_n ≥ lo_x with the decreasing majorant x^{−c′}. It does not need monotonicity of G itself; the doc's "G(σ,·) decreasing" is true for σ ≥ 0 but not needed. c′ comes from a float grid, then `limit_denominator(8)`; the rounding is ≤ 1/16 < the 1/8 offset, so c′ > need always (see m2). | ✓ |
| (H2) | Dedekind ζ_M has 0 ≤ a_n ≤ d_{[M:Q]}(n), and r = L.r = degree in Rankin (K10: 10, F: 6, K: 5, E: 2). | ✓ |
| Γ shifts | Γ_C(s) = Γ_R(s)Γ_R(s+1) exactly (Legendre). K10 (2,4): Γ_R⁶Γ_R(s+1)⁴. K (1,2): Γ_R³Γ_R(s+1)². F (2,2): Γ_R⁴Γ_R(s+1)². E real quadratic: Γ_R². Code `MU_*` match. Signatures are checked independently by PARI (`nf.sign`) in `p_ref.py`/`p_R.py`. | ✓ |
| Polar terms, Lemmas P/S | Contour move picks up R t^{−1} at 1 and −R at 0. Re-derived ∫_{1/A}^∞(u^{−s} − u^{−s−1}) = A^{s−1}/(s−1) − A^s/s = p_A. value_A kernels A^{s−z}, A^{z−(K_w−s)} match. | ✓ |
| Residue solve | R = (I_A − I_1)/(p_1 − p_A) at s1 = 3/2, A = 5/4. The denominator ≈ 0.029, so the R radius is ≈ 35× the I radii; this is handled by balls. `Rc.real + imag radius` is conservative. Checks at 3 other (s, A) are data validation only. | ✓ |
| Real-segment inequality | On (0,1), p_1(σ) = −1/(σ(1−σ)), so Λ < 0 ⟺ σ(1−σ)I_1(σ) < R. The cover covers [1/2,1] exactly: set A one jet, ρ = 17/64 ≥ 1/4 + 1/64; set B jets 5/8 and 7/8 with ρ = 9/64 > 1/8 on [1/2,3/4] ∪ [3/4,1]. Piece balls are built with arb(mid, rad), checked to be outward. At σ = 1, q = 0 and the condition is R > 0. Λ(σ) = Λ(1−σ) gives (0, 1/2]. | ✓ |
| Float → ball | ar(Fraction) = arb(num)/den (rounded, with radius). arb(float) is exact. arb(mid, rad) adds the radius outward (verified). x.upper() is exact. Floats are used only for parameter choice, except **geval.up()** in `strip_M` (m1). | see m1 |

## 2. Findings

**Critical:** none.

**Minor (rigour hygiene; none affects any result).**

* **m1 — float under-rounding in the trapezoid bound.**
  * `Evaluator.strip_M` sets `G = max(up(γQ at c−a), up(γQ at c+a))`, and in the A-split also `f1`, `f2`.
  * `up(x) = float(x.upper())` rounds to nearest. It fell below the exact upper bound in 1280/3000 test cases (`runs/slack.json`), by relative ≤ 2^{−53}.
  * The resulting M_k can therefore be 1 ulp too small.
  * This is absorbed. The G1 integral bound alone over-estimates ∫|γ| by a factor ≥ 1.8: the ratio is 0.30–0.54 for the K10, K, F, E Γ-factors at σ′ ∈ [1/2, 4] (`t_slack.py`). Q and the kernel bound add further slack.
  * Fix: use `x.upper()` (an exact arb) instead of `float`.
* **m2 — no assert in the middle-range tail.** `tail_X`'s middle range lacks the assert `c′ > max(e1, e2)` that the Rankin range has. It is guaranteed by construction: grid offset ≥ 1/8, rounding ≤ 1/16. A future change of grid could silently produce a negative term.
* **m3 — a_n ≥ 0 only asserted up to X.** `Ev3` uses the cell sums Σ a_n as Σ|a_n| on (X, X2], but asserts a_n ≥ 0 only for n ≤ X. This is valid because every local factor is Π(1 − X^f)^{-1}, which has nonnegative coefficients. That relies on the data being of that form, which is not asserted.
* **m4 — implicit |z| ≥ 1 in Lemma D.** The ratio bound q in Lemma D requires |z| ≥ 1. This is unstated in the THEORY and not asserted. It holds since |z| ≥ c ≥ 2 (c = 5/2 or 3).

**Untestable by 10× mutation (correctness rests on the re-derivation in §1, which holds).**
* **Trapezoid bound** (and its A-split factor): with a 10× shrink, the closest approach was 0.4–0.5 of the radius, even at h × 96. The bound is ≥ 20× above the actual error everywhere.
* **Lemma D remainder:** ≥ 3× slack after a 10× shrink, even at J = 2–4 and δ = 1/3.
* **Rankin range:** ≥ 50× slack after a 10× shrink. The ζ(β)^r X^{β−1} loss is the reason the two-range form exists.
* **Field-level PARI comparisons:** less sensitive than the exact references, because the R-solve radius dominates. On 1609 K10, the 10× mutations tailmid / taylor / jettotal / trap reached at most 0.69 and were not caught there.

**Cosmetic.**
* THEORY_GENERAL Lemma X: the remark "since G(σ,·) is decreasing" is unnecessary (see §1).
* artin_all RESULTS §2 calls 13116/18485 "near-misses" by cover margin. The margin measures cover over-estimation, not closeness to a zero or precision (see Verdict).
* `tail_X` computes an unused `lAf`.

## 3. Empirical stress (truth always enclosed unless marked)

Ratio = |mid − truth| / (rad + rad_ref); ≤ 1 means the truth is enclosed. Each run checks ~70 quantities:
* point values of I_1 and I_A against exact I_A = Λ − R_exact p_A;
* jets with K ∈ {3, 4, 6, 8, 12, 40, 48}, at the disc boundary and complex points;
* R;
* the full pipeline Λ = I_1 + R_solved p_1.

**Exact Arb references** (`s_exact.py`, `s_exact_extra.py`): ζ, χ₋₄, χ₅, Q(√5), Q(√−23), Q(√5,√−23) (degree 4), and Q(√5,√−3,i) (degree 8, N = 1.3·10⁷). There are 28 regimes:
* prod;
* X/8, X/32, X = 8, X = 20 with and without X2;
* h × 4 … × 96;
* Y/2, Y/4, Y = 3;
* J = 2…16 with δ up to 1/3;
* c = 2, 3;
* prec 53;
* all-bad.

Unmutated: **0 failures**, max ratio 0.476 (`runs/E_*.json`, `extra/runs/E_*.json`). Regimes violating Lemma D's q < 1 correctly assert.

**Fields vs PARI / Arb** (`s_fields.py`). Production builders, set-A parameters, 8 regimes each. Max ratio, unmutated:

| field | object | reference | max ratio | residue checks |
|---|---|---|---|---|
| 1609, 1649, 1777, 2297, 2617 | K10 | PARI lfunlambda, 38/30 digits, 18–25 points incl. near the real segment | ≤ 0.118 | all overlap |
| 1609, 1649, 1777, 2297, 2617 | K | PARI | ≤ 0.076 | all overlap |
| 10229.1, **13116.1, 18485.1** | E | PARI + rigorous Arb ζ·L(χ_D) | ≤ 0.073 | all overlap |
| 10229.1, **13116.1, 18485.1** | F | PARI bnfinit residue R = 2^{r1+r2}h·Reg/w only (lfun > 1 GB) | ≤ 0.074 | all overlap |

* The F residue agrees with the class-number formula to ≈ 13 significant digits:
  * 46900.60709869…, h = 8 (13116);
  * 50632.88849710…, h = 4 (18485);
  * 317480.9605904…, h = 4 (10229).
* This independently confirms N = |d_F|, the Γ-shifts and the coefficients for those fields.
* Point values of Λ_F are checked only through the A-split / residue consistency and set A/B agreement.
* Under adversarial regimes the cover sometimes fails (h × 8, J = 16 with δ = 1/4, X/16 for E). It always fails by widening the radii, never by excluding the truth. The production cover margins are reproduced exactly: 0.7805 (13116 F), 2.0988 (18485 F), 92.64 (1609 K10).

## 4. Mutation testing (each error term ÷ 10, one at a time; `alib.MUT10`)

| mutation | caught? | where (ratio > 1) |
|---|---|---|
| Taylor remainder (TJ) | **yes** | tq, bq: prod, J6, h × 4, … (max 3.1) |
| tail, middle range | **yes** | tq, bq: prod, X/8, X = 20, c = 2/3 (max 4.8) |
| Q(σ) | **yes** | tq, bq, ζ (max 3.1) |
| Bint (G1) | **yes** | tq, bq (max 4.8) |
| Stirling C_Γ (G2′) | **yes** | ζ at Y = 3 (1.59) |
| node truncation (Nt) | **yes** | ζ at Y = 3 (1.59) |
| total jet error | **yes** | tq, bq, ζ (max 4.8) |
| trapezoid (Tr) | no | closest 0.72 (bq, h × 32): untestable at 10× |
| A-split strip factor | no | closest 0.68: untestable at 10× |
| Lemma D remainder | no | closest 0.31 (tq, J = 4): untestable at 10× |
| tail, Rankin range | no | closest 0.31 (unchanged): untestable at 10× |

The earlier audit's gross mutations (zero / 10⁻⁶, wrong dual sign, wrong A exponent) were all caught (`../audit/logs/mut_*`).

## Files
* Code: `alib.py`, `s_exact.py`, `s_exact_extra.py`, `s_fields.py`, `p_ref.py`, `p_R.py`, `t_slack.py`.
* Drivers: `wd.sh`, `run_exact.sh`, `run_extra.sh`, `run_fields.sh`.
* Results: `runs/E_*.json` (exact + mutations), `extra/runs/E_*.json`, `runs/F_*.json` (fields; `_R` = with PARI residue), `runs/pari_*.json`, `runs/pariR_*.json`, `runs/slack.json`, `logs/`.
