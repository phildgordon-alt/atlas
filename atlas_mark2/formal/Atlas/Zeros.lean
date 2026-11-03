/-
Atlas — the zero layer and the bridge to atoms (THEORY_ZSIGN §0–§1, atlas_v4 §1).

The zeros are an abstract `ZeroData` (same design as `Zeta23.ZeroConfig` in anthropics/formal-math:
a set of distinct zeros + a multiplicity function, invariant under ρ ↦ 1 − ρ̄, locally finite in
the ordinate), here with the STRICT strip 0 < Re ρ < 1 used by atlas_v4 §1.
Hardy's Z enters only through Lemma 1's analytic premise, which is a hypothesis (`Lemma1Parity`,
or the weaker `Lemma1Weak`), never an axiom.
-/
import Atlas.Basic

noncomputable section

open Finset Set ComplexConjugate
open scoped Classical

namespace Atlas

/-- ρ ↦ 1 − ρ̄ -/
def reflect (ρ : ℂ) : ℂ := 1 - conj ρ

@[simp] lemma reflect_re (ρ : ℂ) : (reflect ρ).re = 1 - ρ.re := by simp [reflect]
@[simp] lemma reflect_im (ρ : ℂ) : (reflect ρ).im = ρ.im := by simp [reflect]
@[simp] lemma reflect_reflect (ρ : ℂ) : reflect (reflect ρ) = ρ := by
  apply Complex.ext <;> simp

/-- Abstract zero data: the nontrivial zeros of ξ with multiplicity (cf. `Zeta23.ZeroConfig`). -/
structure ZeroData where
  carrier : Set ℂ
  mult : ℂ → ℕ
  one_le_mult : ∀ ρ ∈ carrier, 1 ≤ mult ρ
  strip : ∀ ρ ∈ carrier, 0 < ρ.re ∧ ρ.re < 1
  reflect_mem : ∀ ρ ∈ carrier, reflect ρ ∈ carrier
  mult_reflect : ∀ ρ ∈ carrier, mult (reflect ρ) = mult ρ
  finite_window : ∀ a b : ℝ, (carrier ∩ {ρ | a ≤ ρ.im ∧ ρ.im ≤ b}).Finite

/-- displacement d = |Re ρ − 1/2| -/
def disp (ρ : ℂ) : ℝ := |ρ.re - 1 / 2|

@[simp] lemma disp_reflect (ρ : ℂ) : disp (reflect ρ) = disp ρ := by
  unfold disp; rw [reflect_re, abs_sub_comm]; congr 1; ring

namespace ZeroData

variable (Zd : ZeroData)

/-- the zeros with height in the closed window [a, b] -/
def win (a b : ℝ) : Finset ℂ := (Zd.finite_window a b).toFinset

lemma mem_win {a b : ℝ} {ρ : ℂ} : ρ ∈ Zd.win a b ↔ ρ ∈ Zd.carrier ∧ a ≤ ρ.im ∧ ρ.im ≤ b := by
  simp [win]

lemma reflect_mem_win {a b : ℝ} {ρ : ℂ} (h : ρ ∈ Zd.win a b) : reflect ρ ∈ Zd.win a b := by
  rw [mem_win] at *; exact ⟨Zd.reflect_mem _ h.1, by simpa using h.2⟩

lemma disp_lt_half {ρ : ℂ} (h : ρ ∈ Zd.carrier) : disp ρ < 1 / 2 := by
  have := Zd.strip ρ h; unfold disp; rw [abs_lt]; constructor <;> linarith

/-- total multiplicity of the on-line zeros with height in the OPEN interval (t1, t2) -/
def onLine (t1 t2 : ℝ) : ℕ :=
  ∑ ρ ∈ (Zd.win t1 t2).filter (fun ρ => ρ.re = 1 / 2 ∧ t1 < ρ.im ∧ ρ.im < t2), Zd.mult ρ

/-- **Lemma 1's analytic premise, parity form** (THEORY_ZSIGN §1, atlas_v3 Lemma 2):
if Z(t1), Z(t2) have strictly opposite signs, the on-line zeros in (t1, t2) have ODD total
multiplicity. (Classical fact about Hardy's Z; a hypothesis here.) -/
def Lemma1Parity (Z : ℝ → ℝ) : Prop :=
  ∀ t1 t2, t1 < t2 → Z t1 * Z t2 < 0 → Odd (Zd.onLine t1 t2)

/-- Lemma 1, the weak form n_I ≥ 1 (all that the Theorem and the S-layer use). -/
def Lemma1Weak (Z : ℝ → ℝ) : Prop :=
  ∀ t1 t2, t1 < t2 → Z t1 * Z t2 < 0 → 1 ≤ Zd.onLine t1 t2

lemma Lemma1Weak.of_parity {Z : ℝ → ℝ} (h : Zd.Lemma1Parity Z) : Zd.Lemma1Weak Z := by
  intro t1 t2 h12 hz; obtain ⟨k, hk⟩ := h t1 t2 h12 hz; omega

/-- "every zero with height in [x0, x1] is on the critical line and simple" -/
def Closed (x0 x1 : ℝ) : Prop :=
  ∀ ρ ∈ Zd.carrier, x0 ≤ ρ.im → ρ.im ≤ x1 → ρ.re = 1 / 2 ∧ Zd.mult ρ = 1

/-- "every zero with height in [x0, x1] is on the critical line" -/
def OnLine (x0 x1 : ℝ) : Prop :=
  ∀ ρ ∈ Zd.carrier, x0 ≤ ρ.im → ρ.im ≤ x1 → ρ.re = 1 / 2

/-! ### The canonical atoms of a window (atlas_v4 §1) -/

/-- an on-line zero of multiplicity k is k atoms (x, 0, 1); an off-line zero with Re ρ > 1/2 of
multiplicity m together with its mirror is m atoms (x, d, 2); zeros with Re ρ < 1/2 are carried by
their mirror. -/
def atomsOf (ρ : ℂ) : Multiset Atom :=
  if ρ.re = 1 / 2 then Multiset.replicate (Zd.mult ρ) ⟨ρ.im, 0, 1⟩
  else if 1 / 2 < ρ.re then Multiset.replicate (Zd.mult ρ) ⟨ρ.im, ρ.re - 1 / 2, 2⟩ else 0

/-- all atoms of the window [a, b] -/
def atoms (a b : ℝ) : Multiset Atom := ∑ ρ ∈ Zd.win a b, Zd.atomsOf ρ

lemma msum_finset_sum (s : Finset ℂ) (F : ℂ → Multiset Atom) (h : Atom → ℝ) :
    ((∑ ρ ∈ s, F ρ).map h).sum = ∑ ρ ∈ s, ((F ρ).map h).sum := by
  induction s using Finset.induction_on with
  | empty => simp
  | insert ρ s hρ ih => rw [Finset.sum_insert hρ, Finset.sum_insert hρ, Multiset.map_add,
      Multiset.sum_add, ih]

/-- **Transfer lemma**: the atom sum Σ_a f_a g(x_a, d_a) equals the zero sum
Σ_ρ m_ρ g(Im ρ, |Re ρ − 1/2|) (mirror zeros included). -/
theorem atoms_sum (a b : ℝ) (g : ℝ → ℝ → ℝ) :
    ((Zd.atoms a b).map fun t => (t.f : ℝ) * g t.x t.d).sum =
      ∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ) * g ρ.im (disp ρ) := by
  set s := Zd.win a b
  let on : ℂ → ℝ := fun ρ => if ρ.re = 1 / 2 then (Zd.mult ρ : ℝ) * g ρ.im (disp ρ) else 0
  let rt : ℂ → ℝ := fun ρ => if 1 / 2 < ρ.re then (Zd.mult ρ : ℝ) * g ρ.im (disp ρ) else 0
  let lf : ℂ → ℝ := fun ρ => if ρ.re < 1 / 2 then (Zd.mult ρ : ℝ) * g ρ.im (disp ρ) else 0
  have hL : ∀ ρ, ((Zd.atomsOf ρ).map fun t => (t.f : ℝ) * g t.x t.d).sum = on ρ + 2 * rt ρ := by
    intro ρ
    simp only [atomsOf, on, rt]
    by_cases h1 : ρ.re = 1 / 2
    · have h2 : ¬ (1 / 2 < ρ.re) := by rw [h1]; exact lt_irrefl _
      have h0 : disp ρ = 0 := by unfold disp; rw [h1, sub_self, abs_zero]
      rw [ite_eq_left h1, ite_eq_left h1, ite_eq_right h2, Multiset.map_replicate, Multiset.sum_replicate,
        nsmul_eq_mul, h0]
      push_cast; ring
    · by_cases h2 : 1 / 2 < ρ.re
      · have hd : disp ρ = ρ.re - 1 / 2 := by unfold disp; rw [abs_of_pos (by linarith)]
        rw [ite_eq_right h1, ite_eq_right h1, ite_eq_left h2, ite_eq_left h2, Multiset.map_replicate,
          Multiset.sum_replicate, nsmul_eq_mul, hd]
        push_cast; ring
      · rw [ite_eq_right h1, ite_eq_right h1, ite_eq_right h2, ite_eq_right h2]; simp
  have hR : ∀ ρ, (Zd.mult ρ : ℝ) * g ρ.im (disp ρ) = on ρ + rt ρ + lf ρ := by
    intro ρ; simp only [on, rt, lf]
    rcases lt_trichotomy ρ.re (1 / 2) with h | h | h
    · rw [ite_eq_right h.ne, ite_eq_right (not_lt.2 h.le), ite_eq_left h]; ring
    · rw [ite_eq_left h, ite_eq_right (by rw [h]; exact lt_irrefl _), ite_eq_right (by rw [h]; exact lt_irrefl _)]
      ring
    · rw [ite_eq_right h.ne', ite_eq_left h, ite_eq_right (not_lt.2 h.le)]; ring
  have hsym : ∑ ρ ∈ s, lf ρ = ∑ ρ ∈ s, rt ρ := by
    refine Finset.sum_nbij' reflect reflect (fun ρ h => Zd.reflect_mem_win h)
      (fun ρ h => Zd.reflect_mem_win h) (fun ρ _ => reflect_reflect ρ)
      (fun ρ _ => reflect_reflect ρ) ?_
    intro ρ hρ
    have hc := ((Zd.mem_win).1 hρ).1
    simp only [lf, rt, reflect_re, reflect_im, disp_reflect, Zd.mult_reflect ρ hc]
    have : (ρ.re < 1 / 2) ↔ (1 / 2 < 1 - ρ.re) := by constructor <;> intro <;> linarith
    simp only [this]
  rw [atoms, msum_finset_sum, Finset.sum_congr rfl fun ρ _ => hL ρ,
    Finset.sum_congr rfl fun ρ _ => hR ρ]
  simp only [Finset.sum_add_distrib, ← Finset.mul_sum]
  rw [hsym]; ring

/-! ### The all-open model (atlas_v4 §1) -/

/-- For bins [lo, hi] ∈ `bins`: one `on` box [lo,hi] × {0} (f = 1) and one `off` box
[lo,hi] × [0, 1/2] (f = 2). -/
def allOpen (bins : Set (ℝ × ℝ)) : Set VarBox :=
  {B | ∃ p ∈ bins, B = ⟨p.1, p.2, 0, 0, 1⟩ ∨ B = ⟨p.1, p.2, 0, 1 / 2, 2⟩}

lemma mem_atoms {a b : ℝ} {t : Atom} (ht : t ∈ Zd.atoms a b) :
    ∃ ρ ∈ Zd.win a b, t ∈ Zd.atomsOf ρ := by
  unfold atoms at ht
  exact Multiset.mem_sum.1 ht

/-- **(H_model) for the all-open model (atlas_v4 §1)**: if the bins cover the window, every
canonical atom lies in a var box. Uses only 0 < Re ρ < 1. -/
theorem hmodel_atoms {a b : ℝ} {bins : Set (ℝ × ℝ)}
    (hcov : ∀ x, a ≤ x → x ≤ b → ∃ p ∈ bins, p.1 ≤ x ∧ x ≤ p.2) :
    HModel (allOpen bins) (Zd.atoms a b) := by
  intro t ht
  obtain ⟨ρ, hρ, ht⟩ := Zd.mem_atoms ht
  obtain ⟨hc, ha, hb⟩ := (Zd.mem_win).1 hρ
  obtain ⟨p, hp, hp1, hp2⟩ := hcov ρ.im ha hb
  have hs := Zd.strip ρ hc
  unfold atomsOf at ht
  split_ifs at ht with h1 h2
  · rw [Multiset.eq_of_mem_replicate ht]
    exact ⟨_, ⟨p, hp, Or.inl rfl⟩, rfl, hp1, hp2, le_rfl, le_rfl⟩
  · rw [Multiset.eq_of_mem_replicate ht]
    refine ⟨_, ⟨p, hp, Or.inr rfl⟩, rfl, hp1, hp2, ?_, ?_⟩ <;> simp only <;> linarith
  · simp at ht

/-! ### Rows and count at the zero level -/

variable {J ι : Type*} [Fintype J] [Fintype ι]

/-- (H_rows) as a statement about the zeros of the window [a, b]
(S_j = Σ_ρ m_ρ U_j(Im ρ, |Re ρ − 1/2|)). Inherited analytic input: a hypothesis. -/
def ZRows (C : Cert J ι) (a b : ℝ) : Prop :=
  ∀ j, (∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ) * C.U j ρ.im (disp ρ)) ≤ C.Ehi j + C.lorF j ∧
    C.Elo j - C.Fa j ≤ ∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ) * C.U j ρ.im (disp ρ)

/-- (H_count) at the zero level: N(window) ≤ Nwin. Inherited analytic input: a hypothesis. -/
def ZCount (C : Cert J ι) (a b : ℝ) : Prop := (∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ)) ≤ C.Nwin

theorem hrows_atoms (C : Cert J ι) {a b : ℝ} (h : Zd.ZRows C a b) : C.HRows (Zd.atoms a b) := by
  intro j; unfold Cert.S; rw [Zd.atoms_sum a b (C.U j)]; exact h j

theorem hcount_atoms (C : Cert J ι) {a b : ℝ} (h : Zd.ZCount C a b) :
    C.HCount (Zd.atoms a b) := by
  unfold Cert.HCount Ncnt
  have := Zd.atoms_sum a b (fun _ _ => 1)
  simp only [mul_one] at this
  rw [this]; exact h

/-- n_i of the canonical atoms = on-line multiplicity in I_i, PROVIDED I_i ⊂ window
(THEORY_ZSIGN §1: "I_i ⊂ W (needed)"). -/
theorem n_atoms (C : Cert J ι) {a b : ℝ} (i : ι) (ha : a ≤ C.t1 i) (hb : C.t2 i ≤ b) :
    C.n i (Zd.atoms a b) = (Zd.onLine (C.t1 i) (C.t2 i) : ℝ) := by
  unfold Cert.n
  rw [Zd.atoms_sum a b (C.chi i)]
  unfold onLine
  push_cast
  rw [Finset.sum_filter]
  have hfin : ∀ ρ, (Zd.mult ρ : ℝ) * C.chi i ρ.im (disp ρ) =
      if (ρ.re = 1 / 2 ∧ C.t1 i < ρ.im ∧ ρ.im < C.t2 i) then (Zd.mult ρ : ℝ) else 0 := by
    intro ρ
    have : (disp ρ = 0 ∧ ρ.im ∈ Ioo (C.t1 i) (C.t2 i)) ↔
        (ρ.re = 1 / 2 ∧ C.t1 i < ρ.im ∧ ρ.im < C.t2 i) := by
      unfold disp; rw [abs_eq_zero, sub_eq_zero, mem_Ioo]
    unfold Cert.chi
    by_cases hP : ρ.re = 1 / 2 ∧ C.t1 i < ρ.im ∧ ρ.im < C.t2 i
    · rw [ite_eq_left (this.mpr hP), ite_eq_left hP, mul_one]
    · rw [ite_eq_right (fun h => hP (this.mp h)), ite_eq_right hP, mul_zero]
  simp only [hfin]
  rw [← Finset.sum_filter, ← Finset.sum_filter]
  apply Finset.sum_congr _ (fun _ _ => rfl)
  ext ρ
  simp only [Finset.mem_filter, mem_win]
  constructor
  · rintro ⟨⟨hc, -, -⟩, h1, h2, h3⟩; exact ⟨⟨hc, h2.le, h3.le⟩, h1, h2, h3⟩
  · rintro ⟨⟨hc, -, -⟩, h1, h2, h3⟩
    exact ⟨⟨hc, by linarith, by linarith⟩, h1, h2, h3⟩

/-! ### Splitting off a distinguished atom -/

lemma atoms_eq_add (a b : ℝ) {ρ : ℂ} (hρ : ρ ∈ Zd.win a b) :
    Zd.atoms a b = Zd.atomsOf ρ + ∑ σ ∈ (Zd.win a b).erase ρ, Zd.atomsOf σ := by
  unfold atoms; rw [Finset.add_sum_erase _ _ hρ]

/-- an off-line zero gives a distinguished f = 2 atom (x, d, 2), d = disp ρ > 0 -/
theorem atoms_split_offline {a b : ℝ} {ρ : ℂ} (hρ : ρ ∈ Zd.win a b) (hre : ρ.re ≠ 1 / 2) :
    ∃ A', Zd.atoms a b = ⟨ρ.im, disp ρ, 2⟩ ::ₘ A' ∧ ∀ t ∈ A', t ∈ Zd.atoms a b := by
  -- choose the member of {ρ, reflect ρ} with Re > 1/2
  obtain ⟨σ, hσ, hσre, hσim, hσd⟩ : ∃ σ ∈ Zd.win a b, 1 / 2 < σ.re ∧ σ.im = ρ.im ∧
      disp σ = disp ρ := by
    rcases lt_or_gt_of_ne hre with h | h
    · exact ⟨reflect ρ, Zd.reflect_mem_win hρ, by simp; linarith, by simp, by simp⟩
    · exact ⟨ρ, hρ, h, rfl, rfl⟩
  have hc := ((Zd.mem_win).1 hσ).1
  have hm := Zd.one_le_mult σ hc
  have hd : disp σ = σ.re - 1 / 2 := by unfold disp; rw [abs_of_pos (by linarith)]
  have hof : Zd.atomsOf σ = ⟨ρ.im, disp ρ, 2⟩ ::ₘ Multiset.replicate (Zd.mult σ - 1)
      ⟨ρ.im, disp ρ, 2⟩ := by
    unfold atomsOf
    rw [ite_eq_right hσre.ne', ite_eq_left hσre, ← Multiset.replicate_succ, ← hσim, ← hσd, hd]
    congr 1; omega
  refine ⟨Multiset.replicate (Zd.mult σ - 1) ⟨ρ.im, disp ρ, 2⟩ +
    ∑ τ ∈ (Zd.win a b).erase σ, Zd.atomsOf τ, ?_, ?_⟩
  · rw [Zd.atoms_eq_add a b hσ, hof, Multiset.cons_add]
  · intro t ht
    rw [Zd.atoms_eq_add a b hσ, hof, Multiset.cons_add]
    exact Multiset.mem_cons_of_mem ht

/-- an on-line zero of multiplicity ≥ 2 gives two atoms (x, 0, 1) -/
theorem atoms_split_multiple {a b : ℝ} {ρ : ℂ} (hρ : ρ ∈ Zd.win a b) (hre : ρ.re = 1 / 2)
    (hm : 2 ≤ Zd.mult ρ) :
    ∃ A', Zd.atoms a b = ⟨ρ.im, 0, 1⟩ ::ₘ ⟨ρ.im, 0, 1⟩ ::ₘ A' ∧ ∀ t ∈ A', t ∈ Zd.atoms a b := by
  have hof : Zd.atomsOf ρ = ⟨ρ.im, 0, 1⟩ ::ₘ ⟨ρ.im, 0, 1⟩ ::ₘ
      Multiset.replicate (Zd.mult ρ - 2) ⟨ρ.im, 0, 1⟩ := by
    unfold atomsOf
    rw [ite_eq_left hre, ← Multiset.replicate_succ, ← Multiset.replicate_succ]
    congr 1; omega
  refine ⟨Multiset.replicate (Zd.mult ρ - 2) ⟨ρ.im, 0, 1⟩ +
    ∑ τ ∈ (Zd.win a b).erase ρ, Zd.atomsOf τ, ?_, ?_⟩
  · rw [Zd.atoms_eq_add a b hρ, hof, Multiset.cons_add, Multiset.cons_add]
  · intro t ht
    rw [Zd.atoms_eq_add a b hρ, hof, Multiset.cons_add, Multiset.cons_add]
    exact Multiset.mem_cons_of_mem (Multiset.mem_cons_of_mem ht)

/-- merging two (x,0,1) atoms into one (x,0,2) atom preserves every f-weighted sum -/
lemma merge_sum (x : ℝ) (A' : Multiset Atom) (g : ℝ → ℝ → ℝ) :
    ((⟨x, 0, 2⟩ ::ₘ A').map fun t : Atom => (t.f : ℝ) * g t.x t.d).sum =
      ((⟨x, 0, 1⟩ ::ₘ ⟨x, 0, 1⟩ ::ₘ A').map fun t : Atom => (t.f : ℝ) * g t.x t.d).sum := by
  simp; ring

end ZeroData

end Atlas
