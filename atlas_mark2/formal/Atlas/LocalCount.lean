/-
Atlas — the local-count closure of atlas_v4_2 (diagnostic/atlas_v4_2/THEORY_V4_2.md §1–§2,
diagnostic/local_count/LOCAL_COUNT.md Theorem 1 and Corollary 2).

* `theorem1_count`: the summation step of Theorem 1. The sech kernel, its positivity (Lemma 0) and the
  Arb enclosure (E) are NOT formalized. They enter as the hypothesis `hE` (the window sum of every row
  is ≤ Ehi_j, which is (E) together with "far zeros and mirror terms contribute ≥ 0") and the
  majorant condition `hM` (G ≥ 1 on J × [0, 1/2)).
* `localCount_closed`: Corollary 2. Theorem 1's bound enters as the hypothesis N(J) ≤ B, and the
  closure test as B < k + 2, which is equivalent to ⌊B⌋ ≤ k + 1 (stated this way so that no Mathlib
  floor files are needed; the local Mathlib cache holds only this project's import closure). The k intervals are pairwise disjoint, lie inside J, and carry
  certified opposite signs of Z. Lemma 1 is used in its PARITY form (`Lemma1Parity`). atlas_v3's
  Lemma 2 is not used.
-/
import Atlas.Zeros

noncomputable section

open Finset Set
open scoped Classical

namespace Atlas

namespace ZeroData

variable (Zd : ZeroData)

/-- N(J): the zeros with ordinate in the closed window [A, B], with multiplicity, wherever their real
part is -/
def count (A B : ℝ) : ℕ := ∑ ρ ∈ Zd.win A B, Zd.mult ρ

/-- on-line multiplicity in (a, b) as a sum over the window zeros, when (a, b) ⊂ [A, B] -/
lemma onLine_eq_win {A B a b : ℝ} (ha : A ≤ a) (hb : b ≤ B) :
    Zd.onLine a b = ∑ ρ ∈ Zd.win A B,
      if (ρ.re = 1 / 2 ∧ a < ρ.im ∧ ρ.im < b) then Zd.mult ρ else 0 := by
  rw [← Finset.sum_filter]
  unfold onLine
  apply Finset.sum_congr _ (fun _ _ => rfl)
  ext ρ
  simp only [Finset.mem_filter, mem_win]
  constructor
  · rintro ⟨⟨hc, -, -⟩, hr, h2, h3⟩
    exact ⟨⟨hc, by linarith, by linarith⟩, hr, h2, h3⟩
  · rintro ⟨⟨hc, -, -⟩, hr, h2, h3⟩
    exact ⟨⟨hc, h2.le, h3.le⟩, hr, h2, h3⟩

/-- **Theorem 1, summation step (LOCAL_COUNT.md §2).** Rows j with weights c_j ≥ 0 and kernels
U_j(x, d). If every row's window sum is ≤ Ehi_j (hypothesis `hE`: the enclosure (E) plus nonnegativity
of the dropped far-zero and mirror terms), and the majorant G = Σ c_j U_j is ≥ 1 on J × [0, 1/2)
(`hM`), then N(J) ≤ Σ c_j Ehi_j. -/
theorem theorem1_count {ι : Type*} [Fintype ι] (A B : ℝ) (c Ehi : ι → ℝ) (U : ι → ℝ → ℝ → ℝ)
    (hc : ∀ j, 0 ≤ c j)
    (hE : ∀ j, ∑ ρ ∈ Zd.win A B, (Zd.mult ρ : ℝ) * U j ρ.im (disp ρ) ≤ Ehi j)
    (hM : ∀ x d, A ≤ x → x ≤ B → 0 ≤ d → d < 1 / 2 → 1 ≤ ∑ j, c j * U j x d) :
    (Zd.count A B : ℝ) ≤ ∑ j, c j * Ehi j := by
  have h1 : (Zd.count A B : ℝ) = ∑ ρ ∈ Zd.win A B, (Zd.mult ρ : ℝ) := by
    unfold count; push_cast; rfl
  have h2 : ∑ ρ ∈ Zd.win A B, (Zd.mult ρ : ℝ) ≤
      ∑ ρ ∈ Zd.win A B, (Zd.mult ρ : ℝ) * ∑ j, c j * U j ρ.im (disp ρ) := by
    apply Finset.sum_le_sum
    intro ρ hρ
    obtain ⟨hc', ha, hb⟩ := (Zd.mem_win).1 hρ
    have hG := hM ρ.im (disp ρ) ha hb (by unfold disp; exact abs_nonneg _) (Zd.disp_lt_half hc')
    exact le_mul_of_one_le_right (Nat.cast_nonneg _) hG
  have h3 : ∑ ρ ∈ Zd.win A B, (Zd.mult ρ : ℝ) * ∑ j, c j * U j ρ.im (disp ρ) =
      ∑ j, c j * ∑ ρ ∈ Zd.win A B, (Zd.mult ρ : ℝ) * U j ρ.im (disp ρ) := by
    simp_rw [Finset.mul_sum]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl; intro j _
    apply Finset.sum_congr rfl; intro ρ _
    ring
  have h4 : ∑ j, c j * ∑ ρ ∈ Zd.win A B, (Zd.mult ρ : ℝ) * U j ρ.im (disp ρ) ≤ ∑ j, c j * Ehi j :=
    Finset.sum_le_sum fun j _ => mul_le_mul_of_nonneg_left (hE j) (hc j)
  linarith

/-- **Corollary 2 (local-count closure; THEORY_V4_2 §2).** Let N(J) ≤ B (Theorem 1's bound, a
hypothesis) and B < k + 2 (⇔ ⌊B⌋ ≤ k + 1). Let (p_i, q_i), i < k, be pairwise disjoint open intervals inside
J = [A, B] with Z(p_i) Z(q_i) < 0. With Lemma 1 in its parity form (each interval carries on-line zeros
of ODD total multiplicity), every zero with ordinate in J is on the critical line and simple. -/
theorem localCount_closed {A B Bub : ℝ} (k : ℕ)
    (hB : (Zd.count A B : ℝ) ≤ Bub) (hk : Bub < (k : ℝ) + 2)
    {Z : ℝ → ℝ} (hL : Zd.Lemma1Parity Z)
    (p q : Fin k → ℝ) (hpq : ∀ i, p i < q i) (hp : ∀ i, A ≤ p i) (hq : ∀ i, q i ≤ B)
    (hdisj : ∀ i j, i ≠ j → Disjoint (Ioo (p i) (q i)) (Ioo (p j) (q j)))
    (hZ : ∀ i, Z (p i) * Z (q i) < 0) : Zd.Closed A B := by
  -- the integer count is at most k + 1
  have hN : Zd.count A B ≤ k + 1 := by
    have h1 : (Zd.count A B : ℝ) < (k : ℝ) + 2 := lt_of_le_of_lt hB hk
    have h2 : Zd.count A B < k + 2 := by exact_mod_cast h1
    omega
  set s := Zd.win A B with hs
  let P : Fin k → ℂ → Prop := fun i ρ => ρ.re = 1 / 2 ∧ p i < ρ.im ∧ ρ.im < q i
  let on : Fin k → ℕ := fun i => Zd.onLine (p i) (q i)
  have hon : ∀ i, on i = ∑ ρ ∈ s, if P i ρ then Zd.mult ρ else 0 := fun i =>
    Zd.onLine_eq_win (hp i) (hq i)
  have hodd : ∀ i, Odd (on i) := fun i => hL _ _ (hpq i) (hZ i)
  have hon1 : ∀ i, 1 ≤ on i := fun i => (hodd i).pos
  -- at most one interval contains a given ordinate
  have huniq : ∀ ρ, ∀ i j, P i ρ → P j ρ → i = j := by
    intro ρ i j hi hj
    by_contra hne
    exact Set.disjoint_left.1 (hdisj i j hne) ⟨hi.2.1, hi.2.2⟩ ⟨hj.2.1, hj.2.2⟩
  let f : ℂ → ℕ := fun ρ => ∑ i, if P i ρ then Zd.mult ρ else 0
  have hf_in : ∀ ρ i, P i ρ → f ρ = Zd.mult ρ := by
    intro ρ i hi
    simp only [f]
    rw [Finset.sum_eq_single i (fun j _ hj => by
      rw [ite_eq_right_iff]; intro h; exact absurd (huniq ρ j i h hi) hj)
      (fun h => absurd (Finset.mem_univ i) h)]
    rw [ite_eq_left hi]
  have hf_out : ∀ ρ, (∀ i, ¬ P i ρ) → f ρ = 0 := by
    intro ρ h
    simp only [f]
    apply Finset.sum_eq_zero
    intro i _
    rw [ite_eq_right (h i)]
  have hf_le : ∀ ρ, f ρ ≤ Zd.mult ρ := by
    intro ρ
    by_cases hex : ∃ i, P i ρ
    · obtain ⟨i, hi⟩ := hex
      rw [hf_in ρ i hi]
    · rw [hf_out ρ (fun i hi => hex ⟨i, hi⟩)]
      exact Nat.zero_le _
  have hsum_on : ∑ i, on i = ∑ ρ ∈ s, f ρ := by
    simp only [hon, f]
    exact Finset.sum_comm
  have hcount : Zd.count A B = ∑ ρ ∈ s, f ρ + ∑ ρ ∈ s, (Zd.mult ρ - f ρ) := by
    unfold count
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro ρ _
    have := hf_le ρ
    omega
  have hk_le : k ≤ ∑ i, on i := by
    calc k = ∑ _i : Fin k, 1 := by simp
      _ ≤ ∑ i, on i := Finset.sum_le_sum fun i _ => hon1 i
  intro ρ hc h0 h1
  have hρ : ρ ∈ s := (Zd.mem_win).2 ⟨hc, h0, h1⟩
  have hm := Zd.one_le_mult ρ hc
  by_contra hbad
  -- any off-line or multiple zero forces N(J) ≥ k + 2
  have hbig : k + 2 ≤ Zd.count A B := by
    by_cases hre : ρ.re = 1 / 2
    · have hm2 : 2 ≤ Zd.mult ρ := by
        by_contra h
        exact hbad ⟨hre, by omega⟩
      by_cases hex : ∃ i, P i ρ
      · -- a multiple on-line zero inside an interval: that interval's odd count is ≥ 3
        obtain ⟨i, hi⟩ := hex
        have hmle : Zd.mult ρ ≤ on i := by
          rw [hon i]
          have := Finset.single_le_sum (f := fun σ => if P i σ then Zd.mult σ else 0)
            (fun _ _ => Nat.zero_le _) hρ
          simpa [ite_eq_left hi] using this
        have h3 : 3 ≤ on i := by
          obtain ⟨r, hr⟩ := hodd i
          omega
        have hsplit : ∑ j, on j = ∑ j : Fin k, 1 + ∑ j, (on j - 1) := by
          rw [← Finset.sum_add_distrib]
          apply Finset.sum_congr rfl
          intro j _
          have := hon1 j
          omega
        have hsingle : on i - 1 ≤ ∑ j, (on j - 1) :=
          Finset.single_le_sum (f := fun j => on j - 1) (fun _ _ => Nat.zero_le _)
            (Finset.mem_univ i)
        have hk1 : ∑ _j : Fin k, (1 : ℕ) = k := by simp
        omega
      · -- a multiple on-line zero in no interval
        have hf0 := hf_out ρ (fun i hi => hex ⟨i, hi⟩)
        have hsingle : Zd.mult ρ - f ρ ≤ ∑ σ ∈ s, (Zd.mult σ - f σ) :=
          Finset.single_le_sum (f := fun σ => Zd.mult σ - f σ) (fun _ _ => Nat.zero_le _) hρ
        omega
    · -- an off-line zero and its mirror: two distinct zeros, in no interval's on-line count
      have hne : reflect ρ ≠ ρ := by
        intro h; apply hre; have := congrArg Complex.re h; simp at this; linarith
      have hρ' : reflect ρ ∈ s := Zd.reflect_mem_win hρ
      have hre' : (reflect ρ).re ≠ 1 / 2 := by
        rw [reflect_re]; intro h; apply hre; linarith
      have hf1 : f ρ = 0 := hf_out ρ (fun i hi => hre hi.1)
      have hf2 : f (reflect ρ) = 0 := hf_out (reflect ρ) (fun i hi => hre' hi.1)
      have hsub : ({ρ, reflect ρ} : Finset ℂ) ⊆ s := by
        intro x hx; simp at hx; rcases hx with rfl | rfl <;> assumption
      have h2 := Finset.sum_le_sum_of_subset (f := fun σ => Zd.mult σ - f σ) hsub
      rw [Finset.sum_pair hne.symm] at h2
      have hmr := Zd.mult_reflect ρ hc
      rw [hf1, hf2, hmr] at h2
      omega
  omega

end ZeroData

end Atlas
