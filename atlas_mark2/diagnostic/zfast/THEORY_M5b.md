# THEORY_M5b: rows from the Z moments by a complex shift (written before the v12 code, 2026-10-19)

Let b = σ − 1/2 (b = π/5.6 or π/3.2). Then, for real t = t0 + h:
- n^{−σ} e^{−it log n} = n^{−1/2} e^{−i h′ log n} e^{−it0 log n}, with h′ = h − ib;
- n^{σ−1} e^{−it log n} = n^{−1/2} e^{−i h″ log n} e^{−it0 log n}, with h″ = h + ib.

**Lemma M1c.** Lemma M1 (THEORY_M3 §2) holds for complex h′. The Taylor bound |e^z − Σ_{k≤K} z^k/k!| ≤ |z|^{K+1}/(K+1)! · e^{|z|}
is valid for complex z with |z| ≤ |h′|X_b. Therefore, with M_{0,b,k} the Z moments (weight n^{−1/2}):

  F_σ(t) := Σ_{n≤N_w} n^{−σ} e^{−it log n} = Σ_b e^{−ih′L_b} Σ_{k≤K} (−ih′)^k/k! M_{0,b,k}  ±  Σ_b |e^{−ih′L_b}| V_{0,b} (|h′|X_b)^{K+1}/(K+1)! · e^{|h′|X_b}.

The same holds for G (log n weight: L_b M_k + M_{k+1}, remainder × (|L_b| + X_b)), and for the W weight with h″.
- |e^{−ih′L_b}| = e^{−bL_b} for h′ and e^{+bL_b} for h″. It is taken as an Arb upper bound of the computed exponential ball.
- The point-wise subtraction of n ∈ (N(t), N_w] uses the exact weights in Arb.

**Assembly.** S₁ = F_σ, S₁′ = −G_σ, S₂ = conj(F_W), S₂′ = conj(G_W), then H, H′ and χ exactly as THEORY_ZFAST §10 and zfm_row.

**Parameters.**
- H = 4, Δ = 0.15: |h′| ≤ √(16 + 0.96) < 4.12 and X_b ≤ 0.075 (plus ε), so |h′|X_b ≤ 0.31.
- K = 18: 0.31¹⁹/19! ≈ 4e-27.

**Conditioning.**
- The W sums grow like N^{σ}/σ.
- The moment errors (absolute, ∝ V_{0,b}) are multiplied by e^{bL_b} ≈ n^b and then by |χ| ≍ N^{1−2σ}.
- The net factor is N^{1−σ} ≤ 1 for σ > 1, the same as for the polynomial weights. The ball arithmetic carries it.
