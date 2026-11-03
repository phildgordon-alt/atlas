/-
Atlas certificate logic — basic objects (THEORY_ZSIGN.md §0, §2).

Everything here is ζ-free: the zeros enter only through a finite multiset of *atoms*
a = (x, d, f) (height, displacement |Re ρ − 1/2|, weight f ∈ {1, 2}).
-/
import Mathlib.Basic.Complex.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Multiset
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Data.Set.Finite.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

noncomputable section

open Finset Set

namespace Atlas

/-- An atom a = (x, d, f) of THEORY_ZSIGN §0: x = height, d = |Re ρ − 1/2|, f = weight
(f = 1 for an on-line zero, f = 2 for an off-line pair, or for two units of a multiple on-line zero). -/
structure Atom where
  x : ℝ
  d : ℝ
  f : ℕ

/-- A var box of the case model: [lo, hi] × [dlo, dhi] with weight f (THEORY_ZSIGN §0, (H_model)). -/
structure VarBox where
  lo : ℝ
  hi : ℝ
  dlo : ℝ
  dhi : ℝ
  f : ℕ

/-- An atom lies in a var box (and carries that box's weight). -/
def VarBox.Contains (b : VarBox) (a : Atom) : Prop :=
  a.f = b.f ∧ b.lo ≤ a.x ∧ a.x ≤ b.hi ∧ b.dlo ≤ a.d ∧ a.d ≤ b.dhi

/-- (H_model) for a multiset of atoms and a set of var boxes. -/
def HModel (boxes : Set VarBox) (A : Multiset Atom) : Prop :=
  ∀ a ∈ A, ∃ b ∈ boxes, b.Contains a

/-- The data of one certificate (THEORY_ZSIGN §2): rows `J`, sign-change intervals `ι`,
row kernels `U`, row enclosures `Ehi, Elo`, far allowances `Fa`, Lorentzian flags `lor`,
the count bound `Nwin`, and the dual certificate `yup, ylow, yc, w`. -/
structure Cert (J ι : Type*) [Fintype J] [Fintype ι] where
  U : J → ℝ → ℝ → ℝ
  Ehi : J → ℝ
  Elo : J → ℝ
  Fa : J → ℝ
  lor : J → Bool
  Nwin : ℝ
  yup : J → ℝ
  ylow : J → ℝ
  yc : ℝ
  t1 : ι → ℝ
  t2 : ι → ℝ
  w : ι → ℝ

/-- N = Σ_a f_a (total count with multiplicity) -/
def Ncnt (A : Multiset Atom) : ℝ := (A.map fun a => (a.f : ℝ)).sum

namespace Cert

variable {J ι : Type*} [Fintype J] [Fintype ι] (C : Cert J ι)

/-- the Lorentzian far term `[j Lorentzian] Fa_j` -/
def lorF (j : J) : ℝ := if C.lor j then C.Fa j else 0

/-- c_j = yup_j − ylow_j -/
def c (j : J) : ℝ := C.yup j - C.ylow j

/-- Φ(x,d,f) = f (yc + Σ_j c_j U_j(x,d)) -/
def Phi (x d : ℝ) (f : ℕ) : ℝ := (f : ℝ) * (C.yc + ∑ j, C.c j * C.U j x d)

/-- χ_i(x,d) = 1 if d = 0 and x ∈ I_i = (t1_i, t2_i) (open), else 0 -/
def chi (i : ι) (x d : ℝ) : ℝ := if d = 0 ∧ x ∈ Ioo (C.t1 i) (C.t2 i) then 1 else 0

/-- Σ_i w_i χ_i(x,d) -/
def wsum (x d : ℝ) : ℝ := ∑ i, C.w i * C.chi i x d

/-- Φ_w(x,d,f) = Φ(x,d,f) − f Σ_i w_i χ_i(x,d) -/
def PhiW (x d : ℝ) (f : ℕ) : ℝ := C.Phi x d f - (f : ℝ) * C.wsum x d

/-- K = Σ_j [yup_j (Ehi_j + [L]Fa_j) − ylow_j (Elo_j − Fa_j)] + yc (Nwin − 2) -/
def K : ℝ := (∑ j, (C.yup j * (C.Ehi j + C.lorF j) - C.ylow j * (C.Elo j - C.Fa j)))
  + C.yc * (C.Nwin - 2)

/-- Σ_i w_i -/
def W : ℝ := ∑ i, C.w i

/-- the dual certificate is sign-admissible: yup, ylow, yc, w ≥ 0 -/
def DualNonneg : Prop :=
  (∀ j, 0 ≤ C.yup j) ∧ (∀ j, 0 ≤ C.ylow j) ∧ 0 ≤ C.yc ∧ (∀ i, 0 ≤ C.w i)

/-! ### Window sums over a multiset of atoms -/

/-- S_j = Σ_a f_a U_j(x_a, d_a) -/
def S (j : J) (A : Multiset Atom) : ℝ := (A.map fun a => (a.f : ℝ) * C.U j a.x a.d).sum

/-- n_i = Σ over atoms with d = 0 and x ∈ I_i of f_a (real-valued) -/
def n (i : ι) (A : Multiset Atom) : ℝ := (A.map fun a => (a.f : ℝ) * C.chi i a.x a.d).sum

/-- n_i as a natural number (for parity) -/
def nNat (i : ι) (A : Multiset Atom) : ℕ :=
  (A.map fun a => if a.d = 0 ∧ a.x ∈ Ioo (C.t1 i) (C.t2 i) then a.f else 0).sum

/-- (H_rows): S_j ≤ Ehi_j + [L]Fa_j and S_j ≥ Elo_j − Fa_j for every row. -/
def HRows (A : Multiset Atom) : Prop :=
  ∀ j, C.S j A ≤ C.Ehi j + C.lorF j ∧ C.Elo j - C.Fa j ≤ C.S j A

/-- (H_count): N ≤ Nwin. -/
def HCount (A : Multiset Atom) : Prop := Ncnt A ≤ C.Nwin

/-- (R): Φ_w ≥ 0 at every point of every var box (with that box's f). -/
def CondR (boxes : Set VarBox) : Prop :=
  ∀ b ∈ boxes, ∀ x d, b.lo ≤ x → x ≤ b.hi → b.dlo ≤ d → d ≤ b.dhi → 0 ≤ C.PhiW x d b.f

/-- The verifier's form of (R) (THEORY_ZSIGN §3 "Endpoints", §4.2): the subtraction uses the
CLOSED intervals [t1_i, t2_i] and boxes reaching d = 0. -/
def chiCl (i : ι) (x d : ℝ) : ℝ := if d = 0 ∧ x ∈ Icc (C.t1 i) (C.t2 i) then 1 else 0

def CondRClosed (boxes : Set VarBox) : Prop :=
  ∀ b ∈ boxes, ∀ x d, b.lo ≤ x → x ≤ b.hi → b.dlo ≤ d → d ≤ b.dhi →
    0 ≤ C.Phi x d b.f - (b.f : ℝ) * ∑ i, C.w i * C.chiCl i x d

/-! ### Algebraic lemmas -/

lemma chi_le_chiCl (i : ι) (x d : ℝ) : C.chi i x d ≤ C.chiCl i x d := by
  unfold chi chiCl
  by_cases h : d = 0 ∧ x ∈ Ioo (C.t1 i) (C.t2 i)
  · have h' : d = 0 ∧ x ∈ Icc (C.t1 i) (C.t2 i) := ⟨h.1, Ioo_subset_Icc_self h.2⟩
    simp [h, h']
  · simp only [h, ite_false]; split_ifs <;> norm_num

/-- The verifier's closed-interval (R) implies the mathematical (R) (conservative, w ≥ 0). -/
theorem condR_of_closed (hw : ∀ i, 0 ≤ C.w i) {boxes : Set VarBox}
    (h : C.CondRClosed boxes) : C.CondR boxes := by
  intro b hb x d h1 h2 h3 h4
  have := h b hb x d h1 h2 h3 h4
  unfold PhiW wsum
  have hs : ∑ i, C.w i * C.chi i x d ≤ ∑ i, C.w i * C.chiCl i x d :=
    Finset.sum_le_sum fun i _ => mul_le_mul_of_nonneg_left (C.chi_le_chiCl i x d) (hw i)
  have hf : (0 : ℝ) ≤ b.f := Nat.cast_nonneg _
  nlinarith

/-- Exchange of a multiset sum with a finite sum. -/
lemma msum_fsum {κ : Type*} [Fintype κ] (A : Multiset Atom) (F : Atom → κ → ℝ) :
    (A.map fun a => ∑ k, F a k).sum = ∑ k, (A.map fun a => F a k).sum := by
  induction A using Multiset.induction_on with
  | empty => simp
  | cons a A ih => simp [ih, Finset.sum_add_distrib]

lemma msum_add (A : Multiset Atom) (F G : Atom → ℝ) :
    (A.map fun a => F a + G a).sum = (A.map F).sum + (A.map G).sum := by
  induction A using Multiset.induction_on with
  | empty => simp
  | cons a A ih => simp [ih]; ring

lemma msum_sub (A : Multiset Atom) (F G : Atom → ℝ) :
    (A.map fun a => F a - G a).sum = (A.map F).sum - (A.map G).sum := by
  induction A using Multiset.induction_on with
  | empty => simp
  | cons a A ih => simp [ih]; ring

lemma msum_mul_left (A : Multiset Atom) (r : ℝ) (F : Atom → ℝ) :
    (A.map fun a => r * F a).sum = r * (A.map F).sum := by
  induction A using Multiset.induction_on with
  | empty => simp
  | cons a A ih => simp [ih]; ring

lemma msum_nonneg (A : Multiset Atom) (F : Atom → ℝ) (h : ∀ a ∈ A, 0 ≤ F a) :
    0 ≤ (A.map F).sum := by
  induction A using Multiset.induction_on with
  | empty => simp
  | cons a A ih =>
    simp only [Multiset.map_cons, Multiset.sum_cons]
    have h1 := h a (Multiset.mem_cons_self a A)
    have h2 := ih fun b hb => h b (Multiset.mem_cons_of_mem hb)
    linarith

lemma msum_le (A : Multiset Atom) (F G : Atom → ℝ) (h : ∀ a ∈ A, F a ≤ G a) :
    (A.map F).sum ≤ (A.map G).sum := by
  have := msum_nonneg A (fun a => G a - F a) (fun a ha => sub_nonneg.2 (h a ha))
  rw [msum_sub] at this; linarith

/-- n_i (real) is the cast of n_i (natural). -/
lemma n_eq_nNat (i : ι) (A : Multiset Atom) : C.n i A = (C.nNat i A : ℝ) := by
  unfold n nNat
  induction A using Multiset.induction_on with
  | empty => simp
  | cons a A ih =>
    simp only [Multiset.map_cons, Multiset.sum_cons, Nat.cast_add, ih]
    unfold chi
    split_ifs <;> simp

/-- Σ_a Φ(a) = yc N + Σ_j c_j S_j. -/
lemma sum_Phi (A : Multiset Atom) :
    (A.map fun a => C.Phi a.x a.d a.f).sum = C.yc * Ncnt A + ∑ j, C.c j * C.S j A := by
  have h1 : (fun a : Atom => C.Phi a.x a.d a.f) =
      fun a => C.yc * (a.f : ℝ) + ∑ j, C.c j * ((a.f : ℝ) * C.U j a.x a.d) := by
    funext a; unfold Phi; rw [mul_add, Finset.mul_sum]; congr 1; ring
    exact Finset.sum_congr rfl fun j _ => by ring
  rw [h1, msum_add, msum_mul_left, msum_fsum]
  unfold Ncnt S
  congr 1
  exact Finset.sum_congr rfl fun j _ => msum_mul_left _ _ _

/-- Steps (i)–(ii) of the Theorem: Σ_{a∈A} Φ(a) ≤ K + 2 yc, from (H_rows), (H_count), y ≥ 0. -/
theorem sum_Phi_le (hy : C.DualNonneg) (A : Multiset Atom) (hR : C.HRows A) (hN : C.HCount A) :
    (A.map fun a => C.Phi a.x a.d a.f).sum ≤ C.K + 2 * C.yc := by
  obtain ⟨hyu, hyl, hyc, -⟩ := hy
  rw [C.sum_Phi A]
  have hrow : ∑ j, C.c j * C.S j A ≤
      ∑ j, (C.yup j * (C.Ehi j + C.lorF j) - C.ylow j * (C.Elo j - C.Fa j)) := by
    refine Finset.sum_le_sum fun j _ => ?_
    obtain ⟨hu, hl⟩ := hR j
    unfold c
    have := mul_le_mul_of_nonneg_left hu (hyu j)
    have := mul_le_mul_of_nonneg_left hl (hyl j)
    nlinarith
  have hcnt : C.yc * Ncnt A ≤ C.yc * C.Nwin := mul_le_mul_of_nonneg_left hN hyc
  unfold K
  linarith

/-- Σ_a f_a Σ_i w_i χ_i(a) = Σ_i w_i n_i (exchange of finite sums). -/
lemma sum_fwsum (A : Multiset Atom) :
    (A.map fun a => (a.f : ℝ) * C.wsum a.x a.d).sum = ∑ i, C.w i * C.n i A := by
  unfold wsum n
  have : (fun a : Atom => (a.f : ℝ) * ∑ i, C.w i * C.chi i a.x a.d) =
      fun a => ∑ i, C.w i * ((a.f : ℝ) * C.chi i a.x a.d) := by
    funext a; rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun i _ => by ring
  rw [this, msum_fsum]
  exact Finset.sum_congr rfl fun i _ => msum_mul_left _ _ _

/-- Σ_a Φ_w(a) = Σ_a Φ(a) − Σ_i w_i n_i. -/
lemma sum_PhiW (A : Multiset Atom) :
    (A.map fun a => C.PhiW a.x a.d a.f).sum =
      (A.map fun a => C.Phi a.x a.d a.f).sum - ∑ i, C.w i * C.n i A := by
  unfold PhiW
  rw [msum_sub, sum_fwsum]

/-- **Core inequality** (steps (iv)–(v) of the Theorem, factored out): if the distinguished
atom a⋆ is removed from A = a⋆ ::ₘ A', every remaining atom has Φ_w ≥ 0, and
Σ_A Φ ≤ K + 2yc, then Φ_w(a⋆) ≤ K + 2yc − Σ_i w_i n_i(A). -/
theorem core (astar : Atom) (A' : Multiset Atom)
    (hsum : ((astar ::ₘ A').map fun a => C.Phi a.x a.d a.f).sum ≤ C.K + 2 * C.yc)
    (hrest : ∀ a ∈ A', 0 ≤ C.PhiW a.x a.d a.f) :
    C.PhiW astar.x astar.d astar.f ≤ C.K + 2 * C.yc - ∑ i, C.w i * C.n i (astar ::ₘ A') := by
  have h := C.sum_PhiW (astar ::ₘ A')
  rw [Multiset.map_cons, Multiset.sum_cons] at h
  have h0 := msum_nonneg A' (fun a => C.PhiW a.x a.d a.f) hrest
  linarith

/-- (R) + (H_model) ⇒ Φ_w ≥ 0 at every modelled atom. -/
theorem PhiW_nonneg_of_model {boxes : Set VarBox} (hR : C.CondR boxes) {A : Multiset Atom}
    (hM : HModel boxes A) : ∀ a ∈ A, 0 ≤ C.PhiW a.x a.d a.f := by
  intro a ha
  obtain ⟨b, hb, hf, h1, h2, h3, h4⟩ := hM a ha
  rw [hf]
  exact hR b hb a.x a.d h1 h2 h3 h4

lemma chi_of_d_ne {i : ι} {x d : ℝ} (hd : d ≠ 0) : C.chi i x d = 0 := by
  unfold chi; simp [hd]

lemma wsum_of_d_ne {x d : ℝ} (hd : d ≠ 0) : C.wsum x d = 0 := by
  unfold wsum; simp [C.chi_of_d_ne hd]

end Cert

end Atlas
