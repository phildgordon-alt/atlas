# THEORY_M3: window multi-evaluation by bucketed Taylor moments (written before the M3 code, 2026-10-19)

**Purpose.** One √T pass per window, after which every Z value and every row value at any point of the window costs O(#buckets · K)
ball operations plus the Arb θ/correction. Notation follows THEORY_ZFAST.md (cited as Z§n).

**Prior art.**
- This is the moment stage of Odlyzko–Schönhage, in the form Platt uses: Platt, Math. Comp. 86 (2017); Arb's
  `acb_dirichlet_platt_multieval`.
- FLINT's development branch computes exactly these bucket moments, S[k][m] = Σ_j z_j b_j^k, in dfloat arithmetic with a priori
  bounds (`_platt_smk`, commit "dfloat", 2026-10-02; copy in `ref/flint_main_dfloat_powsum.c`).
- zfast's moments are an independent implementation. They use zfast's exact fixed-point phases (Z§5).
- Atlas windows are at most about 6 units long (v5 searches the span [−2, 4] around a 2-unit target) and need about 500 points.
  Each point is therefore evaluated directly from the moments by a Taylor sum. The FFT-to-grid and band-limited interpolation
  stages of O–S/Platt are not needed. Their purpose is to evaluate 10⁵–10⁹ grid points.

## 1. Setting

- **Session.** A centre t0 = T0 + u0 (exact) and a half-width H. Points are t = T0 + u with |h| ≤ H, where h = u − u0 is formed
  exactly in Arb.
- **N.** Let Nw = ⌊√((t0 + H)/2π)⌋. For each point, N(t) = ⌊√(t/2π)⌋ ≤ Nw.
- **Weights.** Real weights w_j(n), j = 1..J_w:
  - Z: w(n) = n^{−1/2};
  - rows at σ: A(n) = n^{−σ} and W(n) = n^{σ−1}.
- **Target.** F_j(t) = Σ_{n≤Nw} w_j(n) e^{−it log n}, and G_j(t) = Σ_{n≤Nw} w_j(n) log n · e^{−it log n}.
  - Point-wise sums up to N(t) are obtained by subtracting the at most few terms N(t) < n ≤ Nw in Arb.
  - Then:
    - Z(t) = 2 Re(e^{iθ(t)} F(t)) + 2 Re(e^{iθ} corr(t)) (Z§3);
    - S₁ = F_A, S₁′ = −G_A, S₂ = conj(F_W) and S₂′ = conj(G_W). These are the sums of Z§10, because the weights are real and t is
      real.

## 2. Buckets and moments [T]

- **Buckets.** The range 1..Nw is partitioned into consecutive buckets b = [n_b, n_{b+1}).
  - Each bucket has a centre L_b (a binary64).
  - X_b ≥ max_{n∈b} |log n − L_b| is computed as an Arb upper bound at the two ends; log is monotone.
  - Buckets have log-width at most Δ, so X_b ≲ Δ/2.
- **Moments.**

  M_{j,b,k} = Σ_{n∈b} w_j(n) e^{−i t0 log n} (log n − L_b)^k,  k = 0..K+1.

**Lemma M1 (Taylor).** For |h| ≤ H, with z = −ih(log n − L_b) and |z| ≤ |h|X_b,

  e^{−i(t0+h) log n} = e^{−ihL_b} e^{−it0 log n} Σ_{k=0}^{K} z^k/k! + ρ,  |ρ| ≤ (|h|X_b)^{K+1}/(K+1)! · e^{|h|X_b}

(Taylor remainder of exp: |Σ_{k>K} z^k/k!| ≤ |z|^{K+1}/(K+1)! · Σ_m |z|^m/m!). Hence

  F_j(t) = Σ_b e^{−ihL_b} Σ_{k=0}^{K} (−ih)^k/k! M_{j,b,k}  ±  Σ_b V_{j,b} (|h|X_b)^{K+1}/(K+1)! · e^{|h|X_b},

with V_{j,b} ≥ Σ_{n∈b} |w_j(n)|. Writing log n = L_b + (log n − L_b),

  G_j(t) = Σ_b e^{−ihL_b} Σ_{k=0}^{K} (−ih)^k/k! (L_b M_{j,b,k} + M_{j,b,k+1})  ±  Σ_b (|L_b| + X_b) V_{j,b} (|h|X_b)^{K+1}/(K+1)! · e^{|h|X_b}.

**Point evaluation** is done in Arb ball arithmetic from the moment balls; e^{−ihL_b} and (−ih)^k/k! are exact-input Arb
operations. The remainder is added as a radius.

## 3. Computing the moments [T]

**Head buckets** (n < n_head, Z§8): each term w_j(n) e^{−it0 log n} (log n − L_b)^k is a product of Arb balls, accumulated in Arb.

**Fast part.**
- Blocks (Z§5) never cross a bucket edge, because block lengths are capped at the bucket end.
- Per block:
  - the phase table for t0 with Θ = 0, so that (c, s) = (cos, sin)(2πx) with x ≈ −τ0 log n, and c + is ≈ e^{−it0 log n} with the
    error of Z§5–6;
  - the weights:
    - Z: ŵ = fl(1/fl(√n)), with relative error ≤ 2.01u;
    - rows: the Z§10 Taylor polynomials, with errors e_w and magnitude bounds m_w;
  - x̂ = Horner value of a polynomial for log(c_B + k′) − L_b, where c_B is the block centre. It is the Z§10 log polynomial with the
    constant coefficient log c_B − L_b formed in Arb before rounding. Its error e_x comes from the same three-part bound (Cauchy
    remainder, coefficient rounding, Horner rounding). It is about u·X_b, not u·log n.
- Per term and weight: p₀ = (fl(ŵĉ), fl(ŵŝ)), then p_k = fl(p_{k−1} · x̂) componentwise. p_k is added to accumulator k, using the
  Z§7 groups of 16 plus TwoSum.

**Lemma M2 (per-term error).** Let X = X_b + e_x, which bounds |x*| = |log n − L_b| and |x̂|, let m_w ≥ |ŵ|, |w*|, and let
τ_tr = E_c + 2π E_ph. Then each component of p_k differs from the true w* · (cos, −sin) · x*^k by at most

  m_w [ τ_tr X^k + k X^{k−1} e_x + ((1+u)^{k+1} − 1)(1 + E_c) X^k ] + e_w X^k.

*Proof.*
- |ŵĉx̂^k − w*c*x*^k| ≤ |ŵ||ĉ − c*||x̂|^k + |ŵ||c*||x̂^k − x*^k| + |c*| |x*|^k |ŵ − w*|, with |x̂^k − x*^k| ≤ k X^{k−1} e_x.
- The k + 1 roundings in the computed products contribute at most ((1+u)^{k+1} − 1)|ŵ||ĉ||x̂|^k.
- For Z, e_w = 2.01u m_w. ∎

**Summation.** As in Z§7, with Σ|p_k| ≤ B m_w (1 + E_c) X^k (1 + u)^{k+2} per block. The block bound is accumulated in mag_t
upward arithmetic, for each (j, k), and added to both the real and imaginary parts of the moment ball.

**V_{j,b}** = Σ over the head terms, in Arb, plus Σ over blocks of B · m_w.

## 4. Result [T]

Every Z or row value computed from a session is a ball containing the true value. The ingredients are:
- Lemma M1 for the h-expansion;
- Lemma M2 and the summation bound for the moments;
- Z§3–4 (Arb) for θ and the RS correction at the actual t, with N(t);
- the point-wise subtraction of n ∈ (N(t), Nw], in Arb;
- for rows, Z§10 for H, H′ and χ at the actual s.

**Parameters.** H (session half-width), Δ (bucket log-width) and K (Taylor order).
- With H = 3, Δ = 0.2 and K = 16: (|h|X_b)^{K+1}/(K+1)! ≤ 0.3¹⁷/17! ≈ 3.5·10⁻²⁴. The remainder is negligible.
- Cost per term is about K + 2 complex multiply-adds per weight, so a Z session costs about 3–5 single-point Z passes, and a row
  session (two weights) about 6–10.

## 5. Validation (M3 predictions in PREDICTIONS_M3.md)

1. Session values against single-point zfast (M2-validated), at at least 100 points spread over the window, at 10¹⁰–10¹⁶. The
   balls must overlap, and the actual difference must be ≤ 1e-12.
2. Session values against Arb at a subset (stock Arb ≤ 10¹⁵ under the watchdog; `arbref_smooth` at 10¹⁶).
3. A window with an N jump inside it (constructed at 10¹² and 10¹⁴).
4. Rows from sessions against Arb jets (≤ 10¹⁴) and against single-point zf_row (10¹⁶).
5. Cost: session build time and per-point time at 10¹³–10¹⁶. Projection of the per-window cost to 10¹⁸–10²².
