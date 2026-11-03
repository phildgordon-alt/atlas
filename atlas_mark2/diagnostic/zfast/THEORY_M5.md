# THEORY_M5: the push to 10²⁰–10²³ (written before any M5 measurement, 2026-10-19)

All results stay **contingent on the independent review** running in `zfast/review/`.

The push has four parts:
- (1) combined sessions and provider v5z2, for cost;
- (2) a precision analysis for 10²¹–10²³ (no triple-double needed);
- (3) close-pair scans;
- (4) an independent rigorous zero count by Turing's method, which is a *separate method*.

## 1. Combined sessions (v11) and the provider v5z2

**v11 kind-2 session.** One moment pass (THEORY_M3 §3) carries five weights:
- w₀ = n^{−1/2} (Z);
- w₁ = n^{−σ₁} and w₂ = n^{σ₁−1} (rows at a₁ = 2.8);
- w₃ = n^{−σ₂} and w₄ = n^{σ₂−1} (rows at a₂ = 1.6).

The phases, the x̂ polynomial, the per-weight bounds (Lemma M2, with m_w and e_w per weight) and the summation bounds are exactly
THEORY_M3. Weights 1–4 use the Z§10 polynomials and w₀ uses IEEE 1/√n, as before. Point evaluation is M3 §2 with the weight
indices (0 for Z; (1, 2) or (3, 4) for rows).
- Code: `src/v11/zfast_m3b.inc`, generated from v10b's `zfast_m3.inc` by a scripted, listed set of replacements.
- Nothing changes mathematically: the lemmas are per weight.

**Provider v5z2** (`atlas_v5z2/lib/zfast_provider.py`, new and trusted):
- One combined session per (T0, centre).
- The centre is the env value `ZFAST_CENTER`, set by the run script to the target centre. A query with |u − centre| > H falls
  back to the rule c = 8·round(u/8).
- H = 4, Δ = 0.15 and K = 16, so |h|·X_b ≤ 0.3.
- Rows with a ∉ {2.8, 1.6} are rejected (v5 uses only these two).

**Why.** v5 queries Z on [−2, 4] and rows inside the window. One session covers [c − 4, c + 4] ⊇ [−3, 5]. Each process (generator,
replay, independent replay) therefore builds exactly one session instead of four.

**Soundness.** Every value is still a ball from a session whose validity range contains the point; this is asserted. Which session
answers is a matter of cost only.

## 2. Precision at 10²¹–10²³: why no triple-double is needed [T]

The 2026-10-18 cost note assumed floating phases t·log n, for which double-double's 106 bits run out near 10²¹ (t log n ≈ 2⁷⁷).
zfast never forms t·log n in floating point:
- **Phases.** The phase is a residue in Z/2²⁵⁶. It is advanced by exact integer additions from Arb nodes computed at
  wp = 330 + bitlen(T0) bits (THEORY_ZFAST §5, Theorem 1).
  - The phase error bound is E_ph = Σ C(B−1, i) ε_i + τ(B−1)^{J+1}/((J+1)n0^{J+1}) + 2⁻⁶⁴.
  - Height enters only through τ in the interpolation term, which `choose_B` keeps ≤ 2⁻⁷² by shortening blocks. At 10²³,
    B ≈ n0/2200 (1564 at 10¹⁶).
  - The ε_i are ≤ 2⁻²⁵⁷ + Arb radius ≈ 2^{−330+…}, independent of height.
- **Remaining height-dependent requirements:**
  - N < 2⁵² (N = 1.26·10¹¹ at 10²³: fine);
  - binary64 n exact (fine);
  - the radius grows like √N·u (≈ 2·10⁻⁸ for Z at 10²³; signs need |Z| > rad; the smallest certified |Z| so far is 4.6e-6);
  - the 2⁻⁶⁴ truncation term, which is height independent.
- The M2 phase test already covered 10²⁰ and 10²² blocks (19/19, all errors at the 2⁻⁶⁴ floor).

**Validation (instead of a triple-double build).**
- One Arb `powsum_smooth` point at 10²¹ (about 1.1 h, 1 thread, watchdog), compared with zfast single-point and session values.
- At 10²² one more point if time allows (about 3.5 h).
- Arb is the reference here, so if they agree, Arb has independently confirmed the phase arithmetic at these heights.

## 3. Close-pair scan (non-rigorous search, rigorous certification)

**Wide session.** For each height T = 10^E: one kind-0 session centred at T + 1, with H = 61 and Δ = 0.012, so that
|h|X_b ≤ 61·0.006 = 0.37, and K = 18.

**Grid.** Z on u ∈ [−60, 62] at step 0.004, giving midpoints and radii (`zfa3_Zgrid`).
- A sign change between grid points with certified signs locates a zero to within the cell.
- Local minima of |Z| without a sign change ("dips") are refined on a 10× finer grid.

**Pair choice.** Among the zeros located in [T − 20, T + 22], take the smallest normalized gap δ = gap·log(T/2π)/2π.

**Certification.** The pair is certified by v5z2 in the target [T + k, T + k + 2], with k = ⌊midpoint⌋ − 1, chosen so that
the pair lies in [k + 0.5, k + 1.5]. This uses exactly the v5 claim (A)+(B).

The scan is a search heuristic. Only the v5z2 certificate is the claim.

## 4. Independent zero count by Turing's method (SEPARATE METHOD; diagnostic, not part of the v5 claim)

**Input [L].** Bober–Hiary 2018 §3 (quoted, read today):

> "|∫_t^{t+∆} S(y)dy| ≤ 0.128 log(t + ∆) + 2.30, provided that t > 168π and ∆ > 0"

Trudgian improved the constants; the weaker bound is used. Write B(x) = 0.128 log x + 2.30. N(y) = θ(y)/π + 1 + S(y) for y not
an ordinate (Riemann–von Mangoldt, exact).

**Lemma T (two-sided Turing bound) [T].** Let t0 − Δ > 168π, with Z(t0) ≠ 0.
- Let (a_j, b_j) be disjoint intervals in (t0, t0 + Δ] at whose ends Z has certified opposite signs.
- Let (a′_j, b′_j) be such intervals in [t0 − Δ, t0).

Then:
- N(t0) ≤ U := (1/Δ) [B(t0 + Δ) + Θ⁺ − Σ_j (t0 + Δ − b_j)];
- N(t0) ≥ L := (1/Δ) [Θ⁻ + Σ_j (a′_j − t0 + Δ) − B(t0)];

with Θ⁺ ≥ ∫_{t0}^{t0+Δ} (θ/π + 1) and Θ⁻ ≤ ∫_{t0−Δ}^{t0} (θ/π + 1).

*Proof.*
- **Upper bound.** For y ∈ (t0, t0 + Δ] not an ordinate, every (a_j, b_j) with b_j ≤ y contains a zero with ordinate in (t0, y], so
  N(y) ≥ N(t0) + #{j : b_j ≤ y}. Then S(y) ≥ N(t0) + #{b_j ≤ y} − θ(y)/π − 1. Integrate and use ∫_{t0}^{t0+Δ} S ≤ B(t0 + Δ).
- **Lower bound.** Symmetric: N(y) ≤ N(t0) − #{j : a′_j ≥ y} for y ∈ [t0 − Δ, t0), and ∫_{t0−Δ}^{t0} S ≥ −B(t0). ∎

If ⌈L⌉ = ⌊U⌋ =: m, then **N(t0) = m**. The window count is N(T + 2) − N(T).

**Inputs.**
- The signs come from zfast balls on the scan grid (certified where |mid| > rad).
- The θ integrals come from Arb: trapezoid on [a, b] minus (b−a)³/12 · [θ″ over the ball [a, b]] (Arb lgamma series), which gives
  rigorous Θ±.
- Δ = 40.

**What it does and does not show.** The count is a second, independent route: Turing + Bober–Hiary's constant + zfast signs. It is
compared with v5z's certified count, which uses no count. It is validated first at 10¹⁶, against Arb's N(10¹⁶) and N(10¹⁶ + 2).
