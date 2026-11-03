# THEORY_ZFAST: a rigorous, low-memory evaluator of Z(t) and the row values of ζ at large height (M1, 2026-10-19)

Scope: specification and complete error analysis of `src/zfast.c`.
- **Output:** for an exact height t = T0 + u (T0 an integer, u a binary64), zfast returns a ball [m − e, m + e] that provably
  contains Hardy's Z(t).
- **§10** extends the analysis to ζ(s) and ζ′(s) at s = σ + it, σ ∈ {1/2 + π/5.6, 1/2 + π/3.2}. Those are atlas_v5's row jets.

Labels:
- **[T]**: proved here.
- **[A]**: an Arb/FLINT 3.6.0 routine, trusted exactly as atlas_v5 already trusts Arb.
- **[L]**: literature, quoted with its source and how the quote was obtained.

## 0. What Atlas needs from Z

These requirements come from `atlas_v5/lib/verify_zs5.py`, `sech5.py` and `THEORY_V5.md`.

**(i) Signs of Z.** The verifier needs `Zg(T0, t)` only through its sign at the endpoints of the sign-change intervals:

```
(z1.lower() > 0 and z2.upper() < 0) or (z1.upper() < 0 and z2.lower() > 0)
```

So any ball whose radius is below |Z| at those points is sufficient. The generator (untrusted) uses Z values to search, and it
refines intervals to a width of 1e-4.
- Near a simple zero ρ, |Z(t)| ≈ |Z′(ρ)| |t − ρ|. At the 10¹⁶ record windows, the 20 endpoints have |Z| between about 1e-4 and 1
  (§11 checks this on the real data).
- A radius of 1e-9 or less is therefore ample.

**(ii) Rows.** Each sech row needs one enclosure of Re(−ζ′/ζ)(1/2 + b + ix), with b = π/(2a) and a ∈ {2.8, 1.6} (kernels found in
the 10¹⁵/10¹⁶ certificates). So σ = 1/2 + π/5.6 ≈ 1.0610 or σ = 1/2 + π/3.2 ≈ 1.4817.
- v5 computes this with an Arb length-2 jet at 128 bits.
- The rows enter the LP with margins of about 0.8, so an absolute radius of 1e-8 or less changes nothing material.
- Matching certificates (M4) requires only that the closure decisions agree, not that the radii agree.

## 1. Inputs and exact heights [T]

- t = T0 + u is formed exactly in Arb (`zf_height`: `arb_add` at `ARF_PREC_EXACT`; asserted exact). This is v5's `hx`.
- τ = t/(2π) is computed by Arb at working precision wp = 330 + bitlen(T0) + 4.
- The midpoint and radius of every Arb quantity below are rigorous, by Arb's ball semantics [A].

Requirements, all asserted in the code:
- t > 1000;
- N = ⌊√(t/2π)⌋ < 2⁵², so that every n ≤ N is an exact binary64 and every product below stays far from overflow and underflow;
- 2 ≤ J ≤ 32.

## 2. Arithmetic model and trust base

**IEEE binary64 [T, standard].** Round to nearest, unit roundoff u = 2⁻⁵³. Without underflow or overflow,
fl(a ∘ b) = (a ∘ b)(1 + δ) with |δ| ≤ u, for ∘ ∈ {+, −, ×, /}, for √, for fma(a, b, c) = ab + c (a single rounding), and for
int64 → double conversion.
- Arm64 (Apple M1) implements these. The source calls `fma()` explicitly.
- The file is compiled with `-ffp-contract=off -fno-fast-math`, so the compiler fuses nothing else.
- All magnitudes used are at least 2⁻¹⁰⁰⁰ or exactly zero (§6), so there is no underflow.

**TwoSum [T, Knuth].** In round to nearest without overflow, the sequence s = a + b, bb = s − a, e = (a − (s − bb)) + (b − bb)
gives s + e = a + b exactly.

**Integer arithmetic** in Z/2²⁵⁶ (four uint64 limbs with carries) is exact.

**Arb [A]** supplies the following, used in the same way atlas_v5 uses Arb:
- `acb_dirichlet_hardy_theta` (θ);
- `arb_log_ui`, `arb_cos_pi`, `arb_rsqrt` (the head terms and the phase nodes);
- `acb_dirichlet_zeta_rs_f_coeffs`, `acb_dirichlet_zeta_rs_d_coeffs` (the Riemann–Siegel correction terms);
- `acb_dirichlet_zeta_rs_bound` (the remainder, §3);
- mag_t arithmetic, which rounds upward and is used for every error bound accumulated in the C code.

`zf_rs_corr` is a line-by-line copy of the correction part of FLINT's `acb_dirichlet_zeta_rs_r` (LGPL, F. Johansson). It omits
only the main sum, which Arb would compute by `powsum_sieved`. Its output is validated against Arb's complete ζ in §11.

## 3. The Riemann–Siegel formula with explicit remainder [L/A]

**Notation** (Arias de Reyna 2011 [ADR-I], eq. (5), as restated in [ADR-II] §3):

> "a = √(t/2π), N = ⌊a⌋ and p = 1 − 2(a − N)"

> "R(s) = Σ_{n=1}^{N} 1/n^s + (−1)^{N−1} U a^{−σ} ( Σ_{k=0}^{K} C_k(p)/a^k + RS_K )"

with ζ(s) = R(s) + χ(s) · conj(R(1 − s̄)) and U = exp(−i((t/2) log(t/2π) − t/2 − π/8)). R(s) is Riemann's integral, analytic
in s. C_k(p) is the finite combination Σ_{j ≤ 3k/2} (π/(2i))^j d_j^{(k)}(σ) F^{(3k−2j)}(p)/π^{2k} of derivatives of
F(z) = (e^{iπ(z²/2 + 3/8)} − i√2 cos(πz/2))/(2 cos πz). This is exactly the loop in `zf_rs_corr`.

**Remainder: [ADR-I] Theorem 4.2.**
- [ADR-II] (arXiv:2201.00342, p. 11) quotes it as
  > "|Σ_{k=L}^{K} C_k(p)/a^k + RS_K| ≤ c Σ_{k=L}^{K} Γ(k/2)/(ba)^k + c₁ Γ((K+1)/2)/(b₁a)^{K+1}"

  > "where b, c, b1 and c1 are the coefficients appearing in Theorems 4.1 and 4.2 of [1]"

  and p. 12 gives
  > "c1/c = (2^{3σ/2}/7)/(9^σ/π√2) … for σ > 0"

  and states that Theorem 4.2 applies when K + σ ≥ 2.
- FLINT's `acb_dirichlet_zeta_rs_bound` (source comment: "Arias de Reyna, Theorem 4.2"; fetched 2026-10-19 from flintlib/flint)
  implements, for σ ≥ 0, t > 0 and K ≥ 1:

  |RS_K| ≤ max(1/2, 2^{(3⌈σ⌉+1)/2}/7) · ( (11/10) √(2π/t) )^{K+1} · ⌊K/2⌋!

  - This is c₁ = 2^{3σ/2}/7, rounded up through ⌈σ⌉ and floored at 1/2.
  - It uses b₁ = 10/11 and Γ((K+1)/2) ≤ ⌊K/2⌋!.
- Here the rule is: K ≥ 2 always, and σ ≥ 1/2 (rows: σ ≤ 1.49; mirrored side 1 − σ ≥ −0.49, with K + (1 − σ) ≥ 2 for K ≥ 3).
- **Caveat.** [ADR-I] itself was not obtained: AMS returned 403 (`ref/ArdR2011_I*.pdf` are the 403 HTML pages, not the paper). The
  constants come from two concordant secondary sources, the [ADR-II] text and the FLINT source, and they are the bound Arb and
  atlas_v5 already rely on.
  - For Z we use K with bound < 2⁻¹⁰⁰ (K = 4–6 at 10¹⁰–10¹⁶).
  - Even a factor of 10³⁰ in the constant would not matter.
  - As an independent sanity check on the critical line, Gabcke's thesis bound, quoted in Bober–Hiary 2018 §2, applies:
    > "if t ≥ 200, then |R1(t)| < .053t^{−5/4}, |R4(t)| < 0.017t^{−11/4}"

    §11 compares the K = 1 and K = 6 corrections against it.

**Z on the critical line [T].** At s = 1/2 + it we have χ(s) = e^{−2iθ(t)} and 1 − s̄ = s. So
Z(t) = e^{iθ}ζ(s) = e^{iθ}R(s) + conj(e^{iθ}R(s)) = 2 Re(e^{iθ}R(s)), and therefore

  **Z(t) = 2 Σ_{n≤N} n^{−1/2} cos(θ(t) − t log n) + 2 Re(e^{iθ(t)} · corr(s))**,

where corr(s) is the ball returned by `zf_rs_corr` (correction plus the RS_K bound). With Θ = θ/2π and τ = t/2π,
cos(θ − t log n) = cos(2π(Θ − τ log n)), a 1-periodic function of Θ − τ log n.

## 4. θ(t) [A]

θ(t) = Im log Γ(1/4 + it/2) − (t/2) log π is computed by `acb_dirichlet_hardy_theta` at precision wp.
- Θ = θ/(2π) is formed in Arb.
- Only Θ mod 1 is used. Its radius (of order 2^{−wp + 60}) is carried into ε₀ (§5).
- e^{iθ} for the correction uses `arb_sin_cos` of the same ball.

## 5. The phase: exact fixed-point forward differences [T]

**Blocks.** The fast part is split into blocks n = n0 + k, 0 ≤ k < B, with J + 1 ≤ B. Let f(x) = τ log x.

**Lemma 1 (interpolation).** Let p be the polynomial of degree ≤ J with p(m) = f(n0 + m) for m = 0..J. Its Newton form is
p(k) = Σ_{i=0}^{J} C(k, i) Δ^i f(n0), with forward differences Δ^i f(n0) = Σ_m (−1)^{i−m} C(i, m) f(n0 + m). For an integer
0 ≤ k ≤ B − 1:

  |f(n0 + k) − p(k)| ≤ τ/((J+1) n0^{J+1}) · Π_{i=0}^{J} |k − i| ≤ τ (B−1)^{J+1}/((J+1) n0^{J+1}),

and the error is 0 for k ≤ J.

*Proof.* The interpolation remainder is f^{(J+1)}(ξ)/(J+1)! · Π(k − i) with ξ ∈ [n0, n0 + B − 1], and
|f^{(J+1)}(x)| = τ J!/x^{J+1} ≤ τ J!/n0^{J+1}. ∎

**Representation.** An element w of Z/2²⁵⁶ represents the residue w/2²⁵⁶ mod 1.
- `fx_from_arb(x)` returns w = round(mid(x)·2²⁵⁶) mod 2²⁵⁶.
- There is then an integer m with |w/2²⁵⁶ − (x* + m)| ≤ rad(x) + 2⁻²⁵⁷ =: ε for every x* in the ball x.

**Initial values.** Arb computes, at precision wp:
- the balls L_m ∋ f(n0 + m), m = 0..J;
- the forward differences D_i = Δ^i L (in place; ball subtraction is rigorous).

The C code sets:
- E_0 = fx(Θ − D_0), with error ε₀;
- E_i = fx(−D_i) for i ≥ 1, with errors ε_i;

all errors mod 1.

**Lemma 2 (exact iteration).** The code performs, for each k, E_i ← E_i + E_{i+1} for i = 0, …, J − 1, in increasing i, each
step using the not-yet-updated E_{i+1}. After k steps E_0^{(k)} = Σ_{i=0}^{J} C(k, i) E_i^{(0)} in Z/2²⁵⁶.

*Proof.* By induction, E_i^{(k)} = Σ_j C(k, j) E_{i+j}^{(0)}, using Pascal's rule. ∎

**Theorem 1 (phase).** Let v = ⌊E_0^{(k)}/2¹⁹²⌋ be the top limb and x = v/2⁶⁴. Then, for some integer m,

  |x − (Θ − τ log(n0 + k) + m)| ≤ E_ph := Σ_{i=0}^{J} C(B−1, i) ε_i + τ (B−1)^{J+1}/((J+1) n0^{J+1}) + 2⁻⁶⁴.

*Proof.* By Lemma 2, E_0^{(k)}/2²⁵⁶ ≡ Σ C(k, i)(e_i + m_i) + (Θ − Σ C(k, i) Δ^i f(n0)) with |e_i| ≤ ε_i and m_i integers.
- C(k, i) m_i is an integer.
- Σ C(k, i) Δ^i f(n0) = p(k), and Lemma 1 bounds f(n0 + k) − p(k).
- C(k, i) ≤ C(B − 1, i).
- Truncating to the top 64 bits loses less than 2⁻⁶⁴. ∎

So **the phase reduction modulo 1 is exact integer arithmetic**. No floating-point log, multiplication or range reduction touches
the phase. At any height, the only height dependence is through τ in the interpolation term, which the block length is chosen
to keep at or below 2⁻⁷² per term. For the same reason, no triple-double arithmetic is ever needed: the 256-bit fraction covers
any t for which N < 2⁵².

The code evaluates E_ph for each block in mag_t (upward) arithmetic:
- binomials: `mag_bin_uiui`;
- the interpolation term: n0^{J+1}(J + 1) as a lower bound.

The block length B is chosen heuristically (`choose_B`). The bound actually used is the one computed for the actual B.

## 6. The cos kernel [T]

**Input:** v ∈ [0, 2⁶⁴), with x = v/2⁶⁴.

**Steps:**
1. q = ((v + 2⁶¹) mod 2⁶⁴) >> 62 and r = (int64)(v − q·2⁶²) ∈ [−2⁶¹, 2⁶¹), so x ≡ q/4 + r/2⁶⁴ exactly.
2. y = fl(fl((double) r) · K) with K = fl(2π/2⁶⁴), and z = fl(y·y).
3. cos y ≈ fma(Q(z), z, 1), where Q is the 8-step fma-Horner of the binary64 roundings of (−1)^j/(2j)!, j = 1..8.
4. sin y ≈ fma(fl(y·z), Q_s(z), y), where Q_s uses (−1)^j/(2j+1)!.
5. cos 2πx = (cos y, −sin y, −cos y, sin y) for q = 0, 1, 2, 3. These are exact sign and selection operations.

**Lemma 3.** For every v, |computed cos 2πx − cos 2πx| ≤ E_c = 4.88·10⁻¹⁶ (≈ 4.39u). The same bound holds for sin.

*Proof:* `tools/sincos_bound.py`, in Arb ball arithmetic. It sums four terms:
- (a) the argument error |y − y*| ≤ ((1+u)³ − 1)·π/4;
- (b) the Taylor remainder Y^{18}/18! (Y^{19}/19! for sin), plus the coefficient roundings;
- (c) the change of the exact polynomial between z and y², bounded as max|C′| · u Y²;
- (d) the fma-Horner rounding, by running error bounds with magnitude bounds at each step.

Output: E_cos = 4.8731e-16, E_sin = 3.9094e-16. The coefficients printed by the script are the hex literals in `zfast.c`.
(c) assumes the code uses exactly those literals (checked in §11 by the kernel test). ∎

The kernel is tested empirically against Arb in §11; the observed error must be ≤ E_c.

## 7. One term and one block [T]

**Weight.** ŵ = fl(1/fl(√n)), with n exact. |ŵ/w* − 1| ≤ (1 + u)/(1 − u) − 1 ≤ 2.01u, where w* = n^{−1/2}.

**Term.** t̂ = fl(ŵ ĉ). Let c* = cos 2π(Θ − τ log n). By Lemma 3, Theorem 1 and |d cos(2πx)/dx| ≤ 2π,
|ĉ − c*| ≤ E_c + 2π E_ph. Then

  |t̂ − w* c*| ≤ u|ŵĉ| + |ŵ − w*||ĉ| + w*|ĉ − c*| ≤ w* (3.03u + E_c + 2π E_ph),

using |ĉ| ≤ 1 + E_c. The code uses 7 > 2π.

**Summation within a block.** Terms are added sequentially in groups of at most 16 into g, starting from 0.0. Each group sum is
added into (hi, lo) by TwoSum (hi + e = hi + g exactly), followed by lo ← fl(lo + e).
- The error of one group is at most γ₁₅ Σ_group |t̂| (Higham Thm 4.4, recursive summation, with γ_m = mu/(1 − mu)).
- The errors of the lo additions are at most n_g² u² Σ|t̂|, where n_g = ⌈B/16⌉ is the number of groups: |e| ≤ u|hi| and there are
  at most n_g additions of size at most n_g u Σ|t̂|. The code uses the factor 2 n_g² u² Σ|t̂|.
- Σ|t̂| ≤ (1 + E_c)(1 + 3.1u) Σ w* ≤ (1 + E_c)(1 + 3.1u) B/√n0.

**Block bound** (computed in mag_t):

  e_block = (B/√n0) · [3.03u + E_c + 7 E_ph + γ₁₅ (1 + E_c)(1 + 3.1u) + 2 n_g² u²].

**Assembly.** hi and lo are added to an Arb accumulator, and Arb's ball additions are rigorous [A]. e_block is accumulated over
all blocks in mag_t and added to the radius.

**Magnitudes.**
- w* ≥ 2⁻²⁶.
- |ĉ| is either 0 or at least about 2⁻⁶⁶, since x is a multiple of 2⁻⁶⁴ and cos has simple zeros.
- Products are therefore at least 2⁻⁹² or exactly 0, so there is no underflow.

## 8. Head terms [A]

For n < n_head, the terms n^{−1/2} cos(π · 2(Θ − τ log n)) are evaluated directly in Arb (`arb_log_ui`, `arb_cos_pi`,
`arb_rsqrt`) and summed in Arb. Here n_head is the first n at which `choose_B` returns a block of at least max(2(J+1), 32).

## 9. Result [T]

  **Z(t) ∈ 2 (H + F ± Σ e_block) + 2 Re(e^{iθ} corr)**,

where:
- H is the head ball;
- F is the exact Arb sum of the block hi and lo values;
- corr carries the Thm 4.2 remainder.

Every inequality used is proved in §§3–8 or is a stated Arb [A] or IEEE property.

**Expected radius.** It is dominated by the a-priori summation and kernel terms: about 2 · 2√N · (3u + E_c + γ₁₅) ≈ 2√N · 4.4·10⁻¹⁵.
That is 10⁻¹² at 10¹⁰ and about 10⁻¹⁰ at 10¹⁶. The actual error is expected to be about 10³ times smaller: the errors are random
and the bounds are worst case.

## 10. Rows: ζ(s) and ζ′(s) at σ ≠ 1/2, sharing the main-sum pass [T, plan to implement in M2b]

Let s = σ + it, with t = T0 + u exact and N = ⌊√(t/2π)⌋.

**Analytic split.** Fix N. On a disc around s on which ⌊√(Im z/2π)⌋ = N:
- H(z) := R(z) − Σ_{n≤N} n^{−z} is analytic, because R is Riemann's integral, analytic in z.
- H̃(z) := conj(H(1 − z̄)) is analytic.
- R̃(z) := conj(R(1 − z̄)) = Σ_{n≤N} n^{z−1} + H̃(z).

Hence:
- ζ(s) = S₁ + H + χ(S₂ + H̃);
- ζ′(s) = S₁′ + H′ + χ′(S₂ + H̃) + χ(S₂′ + H̃′),

with:
- S₁ = Σ n^{−s} and S₁′ = −Σ log n · n^{−s};
- S₂ = Σ n^{s−1} and S₂′ = Σ log n · n^{s−1};
- χ and χ′ from Arb (log χ = (s − 1/2) log π + log Γ((1−s)/2) − log Γ(s/2), so χ′/χ = log π − ψ((1−s)/2)/2 − ψ(s/2)/2) [A].

**Main sums.** S₁, S₁′, S₂ and S₂′ share one pass. The phase t log n is exactly §5 (with Θ = 0), and cos and sin come from Lemma 3.
- The weights n^{−σ}, n^{σ−1} and log n are per-block polynomials in k. Their binary64 coefficients come from Arb Taylor
  expansions at the block centre. Their error bounds are the Taylor remainder (from Cauchy bounds on the disc |z − n_c| < n_c/2),
  the coefficient rounding and the Horner rounding (§6 method).
- The per-term and summation bounds are §7 with the weight error added. |S₂| can be as large as N^σ/σ, but it is multiplied by
  |χ| ≍ a^{1−2σ}, and the ball arithmetic of the assembly takes care of this.

**H and H′.** H(z) costs O(K²) Arb operations with no main sum: it is `zf_rs_corr` at z, plus Σ_{N<n≤N(z)} n^{−z} if
N(z) ≠ N. Its derivative is obtained by a central difference with an analytic remainder. Let M ≥ |H| on the disc |z − s| ≤ ρ
(bounded by evaluating `zf_rs_corr` on the ball s + ρ·D, which is valid by ball semantics as long as N is constant there; otherwise
ρ is halved). Then for h < ρ, with H(s ± ih):

  |H′(s) − (H(s + ih) − H(s − ih))/(2ih)| ≤ Σ_{k ≥ 3 odd} M h^{k−1}/ρ^k ≤ (M/ρ)(h/ρ)²/(1 − (h/ρ)²),

using Cauchy |H^{(k)}(s)|/k! ≤ M/ρ^k. The same holds for H̃. Take h = 2⁻⁴⁰ and ρ = 1/32, and evaluate H(s ± ih) at precision
≥ 200 with K large enough that the Thm 4.2 radius divided by h is below 10⁻²⁰.

**Result.** Enclosures of ζ(s) and ζ′(s), and then Re(−ζ′/ζ)(s). |ζ(s)| ≥ ζ(2σ)/ζ(σ) > 0.05 for σ ≥ 1.06, so the quotient is
well conditioned.

## 11. Validation plan (M2; scored against PREDICTIONS_M2.md)

1. **Kernel test.** At least 10⁷ random v plus every boundary pattern (v = q·2⁶² + {0, ±1, ±2⁶¹, ±(2⁶¹ − 1)}, all four quadrants):
   max |cos_comp − cos 2πx| from an Arb reference, which must be ≤ E_c.
2. **Phase test.** For blocks at heights 10¹⁰, 10¹⁶, 10²⁰ and 10²², with block lengths up to bmax: the top limb vs Arb's
   (Θ − τ log n) mod 1 at every k; the error must be ≤ E_ph.
3. **Z against Arb.** At least 200 points with heights 10¹⁰–10¹⁶ (random u, and points near zeros). Arb's ball must intersect
   zfast's ball, and Arb's midpoint must lie in zfast's ball.
   - Reference up to 10¹⁵: atlas_v5's `Zg` formula (`tools/arb_ref.py`).
   - Reference at 10¹⁶: stock Arb needs 1.3 GB, above this task's 1 GB cap. The reference there is a C program using Arb's
     `acb_dirichlet_powsum_smooth` (Arb's low-memory main sum) plus `zf_rs_corr`. The correction itself is validated by step 3
     at ≤ 10¹⁵.
4. **Stress points.**
   - t near jumps of N (a = √(t/2π) within 10⁻⁹ of an integer, on both sides);
   - t at which Z is tiny (inside the certified sign-change intervals of the 10¹⁵/10¹⁶ windows);
   - very large u offsets;
   - J ∈ {6, 8, 16, 24} and bmax ∈ {64, 2¹⁴, 2¹⁶}, which must still give overlapping balls.
5. **Sign replay.** At every sign-change endpoint of the certified 10¹⁵, 10¹⁵ + 286 and 10¹⁶ windows (`zs.json` /
   certificates), zfast's sign must be decided and must equal the certified one.
6. **Speed and memory** against Arb at 10¹³–10¹⁶ (Arb at 10¹⁶ from COST.md), plus a projection to 10¹⁸–10²²
   (time ∝ N at fixed ns/term).

## References

- [ADR-I] J. Arias de Reyna, High precision computation of Riemann's zeta function by the Riemann–Siegel formula, I. Math. Comp.
  80 (2011) 995–1009. Not obtained (AMS 403). Constants via [ADR-II] and the FLINT source.
- [ADR-II] J. Arias de Reyna, …, II. arXiv:2201.00342 (2022). `ref/ArdR2022_II.pdf` and `.txt`.
- W. Gabcke, PhD thesis, Göttingen 1979, quoted via Bober–Hiary, Exp. Math. 27 (2018), arXiv:1607.00709 §2.
- FLINT 3.6.0 (Arb). Sources read: `acb_dirichlet/zeta_rs_r.c`, `zeta_rs_bound.c`, `zeta_rs.c`, `zeta_jet_rs.c` (flintlib/flint).
- **Prior art (important):** FLINT's development branch (commit "dfloat", 2026-10-02, F. Johansson) adds `dfloat`, a
  double/double-double/triple-double ball arithmetic, and `dfloat_powsum_sieved`. That is a rigorous low-precision sieved RS main
  sum, now the default inside `acb_dirichlet_zeta_rs_r`, together with a dfloat version of Platt's multi-evaluation sums. It is
  not in FLINT 3.6.0, which is installed here. zfast is an independent design:
  - exact integer fixed-point phases by forward differences;
  - no sieve, so O(1) memory;
  - its own error analysis.

  The comparison with FLINT main is recorded in STATUS.md. Copies: `ref/flint_main_dfloat.h` and
  `ref/flint_main_dfloat_powsum.c`.
