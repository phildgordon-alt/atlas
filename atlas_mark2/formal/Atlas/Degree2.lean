/-
Atlas — the degree-2 lemmas, with the analytic facts as hypotheses
(new_territory/ec37a/THEORY_37A.md §1 Lemma Z; ec389a/THEORY_389A.md §1 Lemma Z⁺, §2.2; deg2/THEORY_DEG2.md §1, §7).

* Lemma Z for ε = ±1: from the hypothesis-level functional equation Λ(2c − s) = ε Λ(s) and real coefficients
  Λ(s̄) = conj Λ(s): (a) reality on the line, (b) zeros of Z = zeros of Λ on the line (and the factorization
  transfer for multiplicities), (c) sign symmetry Z(−t) vs Z(t). The weight e^{πt/2} is an abstract positive E(t).
* Central order parity: from g(−z) = ε g(z), g(z) = Λ(c + z), every nonzero Taylor coefficient of g at 0 has
  (−1)^n = ε; hence the order is even for ε = +1 and odd for ε = −1 (and g(0) = 0 for ε = −1). "Taylor
  coefficients" enter through an abstract relation with the three standard properties (uniqueness, z ↦ −z,
  scalar multiples): hypotheses, since no complex analysis is in this project's Mathlib closure.
* Lemma 1 (parity form) for a degree-2 L-function, derived from Lemma Z's zero/multiplicity identification and
  the classical sign-change parity of a real function (hypothesis `SignParity`), and the degree-2 instance of
  Corollary 2 ("count = sign changes"), which is otherwise verbatim `localCount_closed`.
* The degree-2 model (one var box W × [0, 1/2], f = 2; THEORY_DEG2 §7) gives a `V4Cert` with the single bin W,
  so every v4 theorem applies to degree-2 certificates; with the file audit, `exists_v4Cert_deg2`.
-/
import Atlas.Audit
import Atlas.LocalCount
import Atlas.Counting

noncomputable section

open Finset Set Complex ComplexConjugate
open scoped Classical

namespace Atlas

namespace Degree2

/-! ## (a) Lemma Z for ε = ±1 -/

/-- Hypothesis-level functional equation with centre c and root number ε, and real coefficients. -/
structure FE (Λ : ℂ → ℂ) (c : ℝ) (ε : ℂ) : Prop where
  conj_sym : ∀ s, Λ (conj s) = conj (Λ s)
  fe : ∀ s, Λ (2 * c - s) = ε * Λ s

/-- Z for ε = +1: E(t) Re Λ(c + it) (E(t) = e^{πt/2} in the docs) -/
def ZPlus (Λ : ℂ → ℂ) (c : ℝ) (E : ℝ → ℝ) (t : ℝ) : ℝ := E t * (Λ (c + t * I)).re

/-- Z for ε = −1: E(t) Im Λ(c + it) -/
def ZMinus (Λ : ℂ → ℂ) (c : ℝ) (E : ℝ → ℝ) (t : ℝ) : ℝ := E t * (Λ (c + t * I)).im

variable {Λ : ℂ → ℂ} {c : ℝ} {ε : ℂ}

lemma conj_line (t : ℝ) : conj ((c : ℂ) + t * I) = 2 * c - (c + t * I) := by
  apply Complex.ext <;> simp; ring

/-- conj Λ(c + it) = ε Λ(c + it) -/
lemma conj_on_line (h : FE Λ c ε) (t : ℝ) : conj (Λ (c + t * I)) = ε * Λ (c + t * I) := by
  rw [← h.conj_sym, conj_line, h.fe]

/-- **Lemma Z⁺ (a)** (ε = +1): Λ(c + it) is real. -/
theorem lemmaZ_real_plus (h : FE Λ c 1) (t : ℝ) : (Λ (c + t * I)).im = 0 := by
  have := conj_on_line h t
  rw [one_mul] at this
  exact Complex.conj_eq_iff_im.1 this

/-- **Lemma Z (a)** (ε = −1): Λ(c + it) is purely imaginary. -/
theorem lemmaZ_imag_minus (h : FE Λ c (-1)) (t : ℝ) : (Λ (c + t * I)).re = 0 := by
  have := congrArg Complex.re (conj_on_line h t)
  simp only [Complex.conj_re, neg_mul, one_mul, Complex.neg_re] at this
  linarith

/-- **Lemma Z⁺ (b), zero set** (ε = +1): Z(t) = 0 ⇔ Λ(c + it) = 0. -/
theorem lemmaZ_zero_plus (h : FE Λ c 1) {E : ℝ → ℝ} (hE : ∀ t, 0 < E t) (t : ℝ) :
    ZPlus Λ c E t = 0 ↔ Λ (c + t * I) = 0 := by
  have him := lemmaZ_real_plus h t
  unfold ZPlus
  constructor
  · intro hz
    have hre : (Λ (c + t * I)).re = 0 := by
      rcases mul_eq_zero.1 hz with h1 | h1
      · exact absurd h1 (hE t).ne'
      · exact h1
    exact Complex.ext (by simpa using hre) (by simpa using him)
  · intro hz; rw [hz]; simp

/-- **Lemma Z (b), zero set** (ε = −1): Z(t) = 0 ⇔ Λ(c + it) = 0. -/
theorem lemmaZ_zero_minus (h : FE Λ c (-1)) {E : ℝ → ℝ} (hE : ∀ t, 0 < E t) (t : ℝ) :
    ZMinus Λ c E t = 0 ↔ Λ (c + t * I) = 0 := by
  have hre := lemmaZ_imag_minus h t
  unfold ZMinus
  constructor
  · intro hz
    have him : (Λ (c + t * I)).im = 0 := by
      rcases mul_eq_zero.1 hz with h1 | h1
      · exact absurd h1 (hE t).ne'
      · exact h1
    exact Complex.ext (by simpa using hre) (by simpa using him)
  · intro hz; rw [hz]; simp

/-- **Lemma Z (b), multiplicity — the algebraic step.** If Λ(s) = (s − s0)^m g(s) with s0 = c + i t0 on the
line, then along the line Λ(c + it) = (t − t0)^m · (i^m g(c + it)): the order in s at s0 becomes the order in t at
t0 (d/dt = i d/ds). That the cofactor i^m g(c + it0) is nonzero and that Z inherits it as a REAL cofactor is the
continuity step, not formalized (no analysis in this project's Mathlib closure); the docs' "with the same
multiplicity" enters the zero-level theorems below as the hypothesis `hord`. -/
theorem lemmaZ_factor {m : ℕ} {g : ℂ → ℂ} {t0 : ℝ}
    (hfac : ∀ s, Λ s = (s - (c + t0 * I)) ^ m * g s) (t : ℝ) :
    Λ (c + t * I) = ((t - t0 : ℝ) : ℂ) ^ m * (I ^ m * g (c + t * I)) := by
  rw [hfac]
  have : ((c : ℂ) + t * I) - (c + t0 * I) = ((t - t0 : ℝ) : ℂ) * I := by push_cast; ring
  rw [this, mul_pow]; ring

/-- the same, for Z with ε = +1: Z(t) = (t − t0)^m · E(t) Re(i^m g(c + it)). -/
theorem lemmaZ_factor_plus {E : ℝ → ℝ} {m : ℕ} {g : ℂ → ℂ} {t0 : ℝ}
    (hfac : ∀ s, Λ s = (s - (c + t0 * I)) ^ m * g s) (t : ℝ) :
    ZPlus Λ c E t = (t - t0) ^ m * (E t * (I ^ m * g (c + t * I)).re) := by
  unfold ZPlus
  rw [lemmaZ_factor hfac t]
  have : ((((t - t0 : ℝ) : ℂ) ^ m) * (I ^ m * g (c + t * I))).re =
      (t - t0) ^ m * (I ^ m * g (c + t * I)).re := by
    rw [← Complex.ofReal_pow, Complex.re_ofReal_mul]
  rw [this]; ring

/-- **Lemma Z⁺ (c)** (ε = +1): E(t) Z(−t) = E(−t) Z(t), so sign Z(−t) = sign Z(t). -/
theorem lemmaZ_sym_plus (h : FE Λ c 1) (E : ℝ → ℝ) (t : ℝ) :
    E t * ZPlus Λ c E (-t) = E (-t) * ZPlus Λ c E t := by
  unfold ZPlus
  have e : (c : ℂ) + ((-t : ℝ) : ℂ) * I = conj ((c : ℂ) + t * I) := by
    apply Complex.ext <;> simp
  rw [e, h.conj_sym, Complex.conj_re]; ring

/-- **Lemma Z (c)** (ε = −1): E(t) Z(−t) = −E(−t) Z(t), so sign Z(−t) = −sign Z(t). -/
theorem lemmaZ_sym_minus (h : FE Λ c (-1)) (E : ℝ → ℝ) (t : ℝ) :
    E t * ZMinus Λ c E (-t) = -(E (-t) * ZMinus Λ c E t) := by
  unfold ZMinus
  have e : (c : ℂ) + ((-t : ℝ) : ℂ) * I = conj ((c : ℂ) + t * I) := by
    apply Complex.ext <;> simp
  rw [e, h.conj_sym, Complex.conj_im]; ring

theorem lemmaZ_sign_plus (h : FE Λ c 1) {E : ℝ → ℝ} (hE : ∀ t, 0 < E t) (t : ℝ) :
    (0 < ZPlus Λ c E (-t) ↔ 0 < ZPlus Λ c E t) ∧ (ZPlus Λ c E (-t) < 0 ↔ ZPlus Λ c E t < 0) := by
  have e := lemmaZ_sym_plus h E t
  have h1 := hE t; have h2 := hE (-t)
  constructor <;> constructor <;> intro hz <;> nlinarith

theorem lemmaZ_sign_minus (h : FE Λ c (-1)) {E : ℝ → ℝ} (hE : ∀ t, 0 < E t) (t : ℝ) :
    (0 < ZMinus Λ c E (-t) ↔ ZMinus Λ c E t < 0) ∧ (ZMinus Λ c E (-t) < 0 ↔ 0 < ZMinus Λ c E t) := by
  have e := lemmaZ_sym_minus h E t
  have h1 := hE t; have h2 := hE (-t)
  constructor <;> constructor <;> intro hz <;> nlinarith

/-! ## (b) Central order parity -/

/-- An abstract "a is the Taylor coefficient sequence of f at 0" relation, with the three standard
properties that are used (hypotheses: uniqueness of power-series coefficients, and how z ↦ −z and scalar
multiplication act on them). -/
structure TaylorAt0 (Rep : (ℕ → ℂ) → (ℂ → ℂ) → Prop) : Prop where
  unique : ∀ a b f, Rep a f → Rep b f → a = b
  neg : ∀ a f, Rep a f → Rep (fun n => (-1) ^ n * a n) (fun z => f (-z))
  smul : ∀ a f (k : ℂ), Rep a f → Rep (fun n => k * a n) (fun z => k * f z)

/-- g(−z) = ε g(z) ⇒ (−1)^n a_n = ε a_n for every Taylor coefficient. -/
theorem coef_parity {Rep : (ℕ → ℂ) → (ℂ → ℂ) → Prop} (hT : TaylorAt0 Rep) {g : ℂ → ℂ} {a : ℕ → ℂ}
    (ha : Rep a g) (hfe : ∀ z, g (-z) = ε * g z) : ∀ n, (-1) ^ n * a n = ε * a n := by
  have h1 := hT.neg a g ha
  have h2 := hT.smul a g ε ha
  have e : (fun z => g (-z)) = fun z => ε * g z := funext hfe
  rw [e] at h1
  have := hT.unique _ _ _ h1 h2
  intro n; exact congrFun this n

/-- the FE in the variable z = s − c: g(z) := Λ(c + z) satisfies g(−z) = ε g(z). -/
lemma fe_shift (h : FE Λ c ε) (z : ℂ) : Λ (c + -z) = ε * Λ (c + z) := by
  rw [← h.fe]; congr 1; ring

lemma eq_zero_of_neg_eq {z : ℂ} (h : -z = z) : z = 0 := by
  have h2 : (2 : ℂ) * z = 0 := by
    have : z + z = 0 := by nth_rewrite 1 [← h]; exact neg_add_cancel z
    rw [two_mul]; exact this
  rcases mul_eq_zero.1 h2 with h3 | h3
  · norm_num at h3
  · exact h3

/-- **Central order parity.** If (−1)^n a_n = ε a_n for all n, every nonzero coefficient — in
particular the leading one, whose index is the order of the central zero — has even index for ε = +1 and
odd index for ε = −1. -/
theorem order_parity {a : ℕ → ℂ} (h : ∀ n, (-1) ^ n * a n = ε * a n) {m : ℕ} (hm : a m ≠ 0) :
    (ε = 1 → Even m) ∧ (ε = -1 → Odd m) := by
  constructor
  · rintro rfl
    rcases Nat.even_or_odd m with he | ho
    · exact he
    · have := h m
      rw [ho.neg_one_pow, one_mul, neg_one_mul] at this
      exact absurd (eq_zero_of_neg_eq this) hm
  · rintro rfl
    rcases Nat.even_or_odd m with he | ho
    · have := h m
      rw [he.neg_one_pow, one_mul, neg_one_mul] at this
      exact absurd (eq_zero_of_neg_eq this.symm) hm
    · exact ho

/-- ε = −1 ⇒ Λ(c) = 0 (Lemma Z (d)), directly from the FE. -/
theorem central_zero_minus (h : FE Λ c (-1)) : Λ c = 0 := by
  have := fe_shift h 0
  simp only [neg_zero, add_zero, neg_mul, one_mul] at this
  exact eq_zero_of_neg_eq this.symm

/-- **Central order parity for the zero data.** With the analytic identification of the central
multiplicity with the order of g = Λ(c + ·) at 0 (`hmult`: a_m ≠ 0 at m = mult ρ0), the multiplicity is even
for ε = +1 and odd for ε = −1. -/
theorem central_mult_parity {Rep : (ℕ → ℂ) → (ℂ → ℂ) → Prop} (hT : TaylorAt0 Rep) (h : FE Λ c ε)
    {a : ℕ → ℂ} (ha : Rep a (fun z => Λ (c + z))) (Zd : ZeroData) (ρ0 : ℂ)
    (hmult : a (Zd.mult ρ0) ≠ 0) :
    (ε = 1 → Even (Zd.mult ρ0)) ∧ (ε = -1 → Odd (Zd.mult ρ0)) :=
  order_parity (coef_parity hT ha (fun z => fe_shift h z)) hmult

/-- **Lemma C2 shape** (ε = +1): a_0 = 0 (Lemma M) and a_2 ≠ 0 (Arb) ⇒ the order is exactly 2
(a_1 = 0 by parity). -/
theorem order_two {a : ℕ → ℂ} (h : ∀ n, (-1) ^ n * a n = 1 * a n) (h0 : a 0 = 0) (h2 : a 2 ≠ 0) :
    (∀ n < 2, a n = 0) ∧ a 2 ≠ 0 := by
  refine ⟨fun n hn => ?_, h2⟩
  rcases (by omega : n = 0 ∨ n = 1) with rfl | rfl
  · exact h0
  · have := h 1; simp only [pow_one, neg_mul, one_mul] at this
    exact eq_zero_of_neg_eq this

/-! ## (d) Lemma 1 from Lemma Z, and Corollary 2 ("count = sign changes") for degree 2 -/

/-- the classical sign-change parity of a real function with finitely many zeros in (t1, t2), with
`ord t` its order of vanishing at t (real analysis; a hypothesis). -/
def SignParity (Z : ℝ → ℝ) (ord : ℝ → ℕ) : Prop :=
  ∀ t1 t2, t1 < t2 → Z t1 * Z t2 < 0 → ∀ S : Finset ℝ,
    (∀ t, t ∈ S ↔ (t1 < t ∧ t < t2 ∧ Z t = 0)) → Odd (∑ t ∈ S, ord t)

/-- the on-line point of ordinate t (analytic normalization, centre 1/2) -/
def onPt (t : ℝ) : ℂ := (1 / 2 : ℂ) + t * I

@[simp] lemma onPt_re (t : ℝ) : (onPt t).re = 1 / 2 := by simp [onPt]
@[simp] lemma onPt_im (t : ℝ) : (onPt t).im = t := by simp [onPt]

lemma eq_onPt {ρ : ℂ} (h : ρ.re = 1 / 2) : ρ = onPt ρ.im := by
  apply Complex.ext <;> simp [h]

/-- **Lemma 1 (parity form) for degree 2, from Lemma Z.** Hypotheses: Z vanishes exactly at the on-line
zeros (`hzero`, Lemma Z (b) zero set + "the carrier is the zero set of Λ_an"), with order = multiplicity
(`hord`, Lemma Z (b) multiplicity), and the sign-change parity of real functions (`hSP`). -/
theorem lemma1Parity_of_lemmaZ (Zd : ZeroData) {Z : ℝ → ℝ} {ord : ℝ → ℕ} (hSP : SignParity Z ord)
    (hzero : ∀ t, Z t = 0 ↔ onPt t ∈ Zd.carrier) (hord : ∀ t, Z t = 0 → ord t = Zd.mult (onPt t)) :
    Zd.Lemma1Parity Z := by
  intro t1 t2 h12 hz
  set F := (Zd.win t1 t2).filter (fun ρ => ρ.re = 1 / 2 ∧ t1 < ρ.im ∧ ρ.im < t2)
  have hS : ∀ t, t ∈ F.image Complex.im ↔ (t1 < t ∧ t < t2 ∧ Z t = 0) := by
    intro t
    simp only [Finset.mem_image, Finset.mem_filter, F, Zd.mem_win]
    constructor
    · rintro ⟨ρ, ⟨⟨hc, -, -⟩, hre, ha, hb⟩, rfl⟩
      refine ⟨ha, hb, (hzero _).2 ?_⟩
      rw [← eq_onPt hre]; exact hc
    · rintro ⟨ha, hb, hzt⟩
      refine ⟨onPt t, ⟨⟨(hzero t).1 hzt, ?_, ?_⟩, ?_, ?_, ?_⟩, ?_⟩ <;> simp <;> linarith
  have hsum := hSP t1 t2 h12 hz _ hS
  have hinj : Set.InjOn Complex.im (F : Set ℂ) := by
    intro ρ hρ σ hσ he
    simp only [Finset.coe_filter, Set.mem_ofPred_eq, F] at hρ hσ
    rw [eq_onPt hρ.2.1, eq_onPt hσ.2.1, he]
  rw [Finset.sum_image hinj] at hsum
  have e : ∑ ρ ∈ F, ord ρ.im = ∑ ρ ∈ F, Zd.mult ρ := by
    apply Finset.sum_congr rfl
    intro ρ hρ
    simp only [Finset.mem_filter, F, Zd.mem_win] at hρ
    have hz0 : Z ρ.im = 0 := (hzero _).2 (by rw [← eq_onPt hρ.2.1]; exact hρ.1.1)
    rw [hord _ hz0, ← eq_onPt hρ.2.1]
  unfold ZeroData.onLine
  rw [← e]; exact hsum

/-- The zero-set hypothesis `hzero` from Lemma Z⁺ (b) (ε = +1, analytic normalization c = 1/2), when the
carrier is the set of zeros of Λ_an in the open strip. -/
theorem hzero_of_lemmaZ_plus (Zd : ZeroData) (h : FE Λ (1 / 2) 1) {E : ℝ → ℝ} (hE : ∀ t, 0 < E t)
    (hcar : ∀ ρ, ρ ∈ Zd.carrier ↔ Λ ρ = 0 ∧ 0 < ρ.re ∧ ρ.re < 1) (t : ℝ) :
    ZPlus Λ (1 / 2) E t = 0 ↔ onPt t ∈ Zd.carrier := by
  rw [lemmaZ_zero_plus h hE, hcar]
  have e : ((1 / 2 : ℝ) : ℂ) + t * I = onPt t := by simp [onPt]
  rw [e]; simp only [onPt_re]; norm_num

theorem hzero_of_lemmaZ_minus (Zd : ZeroData) (h : FE Λ (1 / 2) (-1)) {E : ℝ → ℝ} (hE : ∀ t, 0 < E t)
    (hcar : ∀ ρ, ρ ∈ Zd.carrier ↔ Λ ρ = 0 ∧ 0 < ρ.re ∧ ρ.re < 1) (t : ℝ) :
    ZMinus Λ (1 / 2) E t = 0 ↔ onPt t ∈ Zd.carrier := by
  rw [lemmaZ_zero_minus h hE, hcar]
  have e : ((1 / 2 : ℝ) : ℂ) + t * I = onPt t := by simp [onPt]
  rw [e]; simp only [onPt_re]; norm_num

/-- **Corollary 2 for a degree-2 L-function** (an instance of `localCount_closed`): N(J) ≤ B < k + 2 and k
pairwise disjoint sign-change intervals of Z in J ⇒ every zero with ordinate in J is on the line and simple.
Lemma 1 comes from Lemma Z via `lemma1Parity_of_lemmaZ`. -/
theorem deg2_localCount_closed (Zd : ZeroData) {Z : ℝ → ℝ} {ord : ℝ → ℕ} (hSP : SignParity Z ord)
    (hzero : ∀ t, Z t = 0 ↔ onPt t ∈ Zd.carrier) (hord : ∀ t, Z t = 0 → ord t = Zd.mult (onPt t))
    {A B Bub : ℝ} (k : ℕ) (hB : (Zd.count A B : ℝ) ≤ Bub) (hk : Bub < (k : ℝ) + 2)
    (p q : Fin k → ℝ) (hpq : ∀ i, p i < q i) (hp : ∀ i, A ≤ p i) (hq : ∀ i, q i ≤ B)
    (hdisj : ∀ i j, i ≠ j → Disjoint (Ioo (p i) (q i)) (Ioo (p j) (q j)))
    (hZ : ∀ i, Z (p i) * Z (q i) < 0) : Zd.Closed A B :=
  Zd.localCount_closed k hB hk (lemma1Parity_of_lemmaZ Zd hSP hzero hord) p q hpq hp hq hdisj hZ

/-- Lemma B ("count = sign changes", v4_1) for degree 2: likewise an instance of `lemmaB_closed`. -/
theorem deg2_lemmaB_closed (Zd : ZeroData) {Z : ℝ → ℝ} {ord : ℝ → ℕ} (hSP : SignParity Z ord)
    (hzero : ∀ t, Z t = 0 ↔ onPt t ∈ Zd.carrier) (hord : ∀ t, Z t = 0 → ord t = Zd.mult (onPt t))
    {σ0 σ1 t0 t1 : ℝ} (hσ0 : σ0 ≤ 0) (hσ1 : 1 ≤ σ1) (N : ℕ) (hN : Zd.boxCount σ0 σ1 t0 t1 = N)
    (a b : Fin N → ℝ) (hab : ∀ k, a k < b k) (ha : ∀ k, t0 ≤ a k) (hb : ∀ k, b k ≤ t1)
    (hdisj : ∀ k l, k ≠ l → Disjoint (Ioo (a k) (b k)) (Ioo (a l) (b l)))
    (hZ : ∀ k, Z (a k) * Z (b k) < 0) : Zd.Closed t0 t1 :=
  Zd.lemmaB_closed hσ0 hσ1 N hN
    (ZeroData.Lemma1Weak.of_parity Zd (lemma1Parity_of_lemmaZ Zd hSP hzero hord)) a b hab ha hb hdisj hZ

/-! ## The degree-2 model: one var box W × [0, 1/2] with f = 2 (THEORY_DEG2 §7) -/

lemma PhiW_one {J ι : Type*} [Fintype J] [Fintype ι] (C : Cert J ι) (x d : ℝ) :
    C.PhiW x d 1 = C.PhiW x d 2 / 2 := by
  unfold Cert.PhiW Cert.Phi; push_cast; ring

/-- (R) on the single f = 2 box W × [0, 1/2] ⇒ (R) on the all-open model with the one bin W
("Φ scales with f, so f = 1 atoms are covered"). -/
theorem condR_deg2 {J ι : Type*} [Fintype J] [Fintype ι] (C : Cert J ι) {wlo whi : ℝ}
    (hR : C.CondR {⟨wlo, whi, 0, 1 / 2, 2⟩}) : C.CondR (ZeroData.allOpen {(wlo, whi)}) := by
  rintro B ⟨p, hp, hB⟩ x d h1 h2 h3 h4
  rw [Set.mem_singleton_iff] at hp
  subst hp
  rcases hB with rfl | rfl
  · simp only at h1 h2 h3 h4 ⊢
    have := hR _ rfl x d h1 h2 h3 (by linarith)
    rw [PhiW_one]; simp only at this; linarith
  · exact hR _ rfl x d h1 h2 h3 h4

/-- **A degree-2 certificate is a `V4Cert`** with the single bin W. -/
theorem exists_v4Cert_of_deg2 {J ι : Type} [Fintype J] [Fintype ι] (C : Cert J ι) {wlo whi x0 x1 : ℝ}
    (dual : C.DualNonneg) (hR : C.CondR {⟨wlo, whi, 0, 1 / 2, 2⟩})
    (condC : ∀ x d, x0 ≤ x → x ≤ x1 → 0 ≤ d → d ≤ 1 / 2 → 0 < C.Phi x d 2 - C.K - 2 * C.yc + C.W)
    (hx0 : wlo ≤ x0) (hx1 : x1 ≤ whi) (hlo : ∀ i, wlo ≤ C.t1 i) (hhi : ∀ i, C.t2 i ≤ whi)
    (hlt : ∀ i, C.t1 i < C.t2 i) :
    ∃ K : V4Cert J ι, K.C = C ∧ K.wlo = wlo ∧ K.whi = whi ∧ K.x0 = x0 ∧ K.x1 = x1 := by
  let K : V4Cert J ι :=
    { C := C, wlo := wlo, whi := whi, x0 := x0, x1 := x1, bins := {(wlo, whi)}, dual := dual,
      bins_cover := fun x h1 h2 => ⟨(wlo, whi), rfl, h1, h2⟩, condR := condR_deg2 C hR,
      condC := condC, x0_ge := hx0, x1_le := hx1, iv_lo := hlo, iv_hi := hhi, iv_lt := hlt }
  exact ⟨K, rfl, rfl, rfl, rfl, rfl⟩

/-- **File → `V4Cert` for a degree-2 certificate file** (deg2, ec37a, ec389a, tollis): the audit check
supplies region ⊂ window and the interval facts; Arb supplies dual ≥ 0, (R) on W × [0, 1/2] and (C). -/
theorem exists_v4Cert_deg2 {J : Type} [Fintype J] {expect : Nat} {model : Bool} {c : AtlasAudit.CertD}
    (h : AtlasAudit.certOk expect model c = true) {r : AtlasAudit.Reg} (hr : r ∈ c.regions)
    (C : Cert J (Fin c.ivs.length))
    (ht1 : ∀ i, C.t1 i = ((c.ivs.get i).t1 : ℝ)) (ht2 : ∀ i, C.t2 i = ((c.ivs.get i).t2 : ℝ))
    (dual : C.DualNonneg) (hR : C.CondR {⟨c.wlo, c.whi, 0, 1 / 2, 2⟩})
    (condC : ∀ x d, (r.x0 : ℝ) ≤ x → x ≤ r.x1 → 0 ≤ d → d ≤ 1 / 2 →
      0 < C.Phi x d 2 - C.K - 2 * C.yc + C.W) :
    ∃ K : V4Cert J (Fin c.ivs.length), K.C = C ∧ K.wlo = c.wlo ∧ K.whi = c.whi ∧
      K.x0 = r.x0 ∧ K.x1 = r.x1 := by
  obtain ⟨-, hreg, hiv, -, -, -⟩ := AtlasAudit.certOk_spec h
  obtain ⟨hx0, -, hx1, -, -⟩ := hreg r hr
  have hivi : ∀ i : Fin c.ivs.length, (c.wlo : ℝ) ≤ (c.ivs.get i).t1 ∧
      ((c.ivs.get i).t1 : ℝ) < (c.ivs.get i).t2 ∧ ((c.ivs.get i).t2 : ℝ) ≤ c.whi :=
    fun i => hiv _ (List.get_mem _ _)
  exact exists_v4Cert_of_deg2 C dual hR condC hx0 hx1
    (fun i => by rw [ht1]; exact (hivi i).1) (fun i => by rw [ht2]; exact (hivi i).2.2)
    (fun i => by rw [ht1, ht2]; exact (hivi i).2.1)

end Degree2

end Atlas
