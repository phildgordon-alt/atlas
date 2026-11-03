/-
Atlas — L5: the counting closure of atlas_v4_1 §2 (Lemma A: N ≤ 1; Lemma B: count = sign changes).

The argument-principle counter is NOT formalized: its output enters as the hypothesis
`boxCount … = N` ("N is the number of zeros in the closed box, with multiplicity").
-/
import Atlas.Zeros

noncomputable section

open Finset Set
open scoped Classical

namespace Atlas

namespace ZeroData

variable (Zd : ZeroData)

/-- the zeros in the closed box B = [σ0, σ1] × [t0, t1] -/
def boxZeros (σ0 σ1 t0 t1 : ℝ) : Finset ℂ :=
  (Zd.win t0 t1).filter fun ρ => σ0 ≤ ρ.re ∧ ρ.re ≤ σ1

/-- number of zeros in B, with multiplicity -/
def boxCount (σ0 σ1 t0 t1 : ℝ) : ℕ := ∑ ρ ∈ Zd.boxZeros σ0 σ1 t0 t1, Zd.mult ρ

lemma mem_boxZeros {σ0 σ1 t0 t1 : ℝ} {ρ : ℂ} :
    ρ ∈ Zd.boxZeros σ0 σ1 t0 t1 ↔
      ρ ∈ Zd.carrier ∧ t0 ≤ ρ.im ∧ ρ.im ≤ t1 ∧ σ0 ≤ ρ.re ∧ ρ.re ≤ σ1 := by
  simp [boxZeros, mem_win, and_assoc]

/-- **L5, Lemma A (atlas_v4_1 §2).** In a box symmetric about Re s = 1/2 (σ0 + σ1 = 1, F3), with
the mirror-symmetric zero set (F2, a field of `ZeroData`), if the count is N ≤ 1 then every zero in
the box is on the line and simple. -/
theorem lemmaA {σ0 σ1 t0 t1 : ℝ} (hsym : σ0 + σ1 = 1) (hN : Zd.boxCount σ0 σ1 t0 t1 ≤ 1)
    (ρ : ℂ) (hρ : ρ ∈ Zd.boxZeros σ0 σ1 t0 t1) : ρ.re = 1 / 2 ∧ Zd.mult ρ = 1 := by
  obtain ⟨hc, h0, h1, hs0, hs1⟩ := (Zd.mem_boxZeros).1 hρ
  have hm := Zd.one_le_mult ρ hc
  have hle : Zd.mult ρ ≤ Zd.boxCount σ0 σ1 t0 t1 :=
    Finset.single_le_sum (f := Zd.mult) (fun _ _ => Nat.zero_le _) hρ
  by_cases hre : ρ.re = 1 / 2
  · exact ⟨hre, by omega⟩
  · exfalso
    have hne : reflect ρ ≠ ρ := by
      intro h; apply hre; have := congrArg Complex.re h; simp at this; linarith
    have hρ' : reflect ρ ∈ Zd.boxZeros σ0 σ1 t0 t1 :=
      (Zd.mem_boxZeros).2 ⟨Zd.reflect_mem ρ hc, by simpa using h0, by simpa using h1,
        by simp; linarith, by simp; linarith⟩
    have hsub : ({ρ, reflect ρ} : Finset ℂ) ⊆ Zd.boxZeros σ0 σ1 t0 t1 := by
      intro x hx; simp at hx; rcases hx with rfl | rfl <;> assumption
    have h2 := Finset.sum_le_sum_of_subset (f := Zd.mult) hsub
    rw [Finset.sum_pair hne.symm, Zd.mult_reflect ρ hc] at h2
    unfold boxCount at hN
    omega

/-- Lemma A, window form: if the box contains the critical strip (σ0 ≤ 0, so σ1 ≥ 1), N ≤ 1
gives the v4 claim on [t0, t1]: every zero with height in [t0, t1] is on the line and simple. -/
theorem lemmaA_closed {σ0 σ1 t0 t1 : ℝ} (hsym : σ0 + σ1 = 1) (hσ : σ0 ≤ 0)
    (hN : Zd.boxCount σ0 σ1 t0 t1 ≤ 1) : Zd.Closed t0 t1 := by
  intro ρ hc h0 h1
  have hs := Zd.strip ρ hc
  exact Zd.lemmaA hsym hN ρ ((Zd.mem_boxZeros).2 ⟨hc, h0, h1, by linarith, by linarith⟩)

/-- on-line multiplicity in (a, b) as a sum over the box zeros, when (a, b) ⊂ [t0, t1] and the box
contains Re s = 1/2 -/
lemma onLine_eq_box {σ0 σ1 t0 t1 a b : ℝ} (h0 : σ0 ≤ 1 / 2) (h1 : 1 / 2 ≤ σ1) (ha : t0 ≤ a)
    (hb : b ≤ t1) :
    Zd.onLine a b = ∑ ρ ∈ Zd.boxZeros σ0 σ1 t0 t1,
      if (ρ.re = 1 / 2 ∧ a < ρ.im ∧ ρ.im < b) then Zd.mult ρ else 0 := by
  rw [← Finset.sum_filter]
  unfold onLine
  apply Finset.sum_congr _ (fun _ _ => rfl)
  ext ρ
  simp only [Finset.mem_filter, mem_win, mem_boxZeros]
  constructor
  · rintro ⟨⟨hc, -, -⟩, hr, h2, h3⟩
    exact ⟨⟨hc, by linarith, by linarith, by linarith, by linarith⟩, hr, h2, h3⟩
  · rintro ⟨⟨hc, -, -, -, -⟩, hr, h2, h3⟩
    exact ⟨⟨hc, h2.le, h3.le⟩, hr, h2, h3⟩

/-- **L5, Lemma B (atlas_v4_1 §2, "count = sign changes").** Let the box B = [σ0, σ1] × [t0, t1]
contain the line Re s = 1/2, let N = count(B), and let I_k = (a_k, b_k), k < N, be N pairwise
disjoint intervals inside [t0, t1] with Z(a_k) Z(b_k) < 0. With the weak Lemma 1 premise, every
zero in B is on the line and simple. (Mirror symmetry and parity are NOT used.) -/
theorem lemmaB {σ0 σ1 t0 t1 : ℝ} (hσ0 : σ0 ≤ 1 / 2) (hσ1 : 1 / 2 ≤ σ1) (N : ℕ)
    (hN : Zd.boxCount σ0 σ1 t0 t1 = N) {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (a b : Fin N → ℝ) (hab : ∀ k, a k < b k) (ha : ∀ k, t0 ≤ a k) (hb : ∀ k, b k ≤ t1)
    (hdisj : ∀ k l, k ≠ l → Disjoint (Ioo (a k) (b k)) (Ioo (a l) (b l)))
    (hZ : ∀ k, Z (a k) * Z (b k) < 0)
    (ρ : ℂ) (hρ : ρ ∈ Zd.boxZeros σ0 σ1 t0 t1) : ρ.re = 1 / 2 ∧ Zd.mult ρ = 1 := by
  set s := Zd.boxZeros σ0 σ1 t0 t1
  let P : Fin N → ℂ → Prop := fun k ρ => ρ.re = 1 / 2 ∧ a k < ρ.im ∧ ρ.im < b k
  let on : Fin N → ℕ := fun k => Zd.onLine (a k) (b k)
  have hon : ∀ k, on k = ∑ ρ ∈ s, if P k ρ then Zd.mult ρ else 0 := fun k =>
    Zd.onLine_eq_box hσ0 hσ1 (ha k) (hb k)
  have hon1 : ∀ k, 1 ≤ on k := fun k => hL _ _ (hab k) (hZ k)
  -- at most one interval contains a given height
  have huniq : ∀ ρ, ∀ k l, P k ρ → P l ρ → k = l := by
    intro ρ k l hk hl
    by_contra hne
    exact Set.disjoint_left.1 (hdisj k l hne) ⟨hk.2.1, hk.2.2⟩ ⟨hl.2.1, hl.2.2⟩
  let f : ℂ → ℕ := fun ρ => ∑ k, if P k ρ then Zd.mult ρ else 0
  have hf_le : ∀ ρ ∈ s, f ρ ≤ Zd.mult ρ := by
    intro ρ _
    by_cases hex : ∃ k, P k ρ
    · obtain ⟨k, hk⟩ := hex
      have : f ρ = Zd.mult ρ := by
        simp only [f]
        rw [Finset.sum_eq_single k (fun l _ hl => by
          rw [ite_eq_right (fun h => hl (huniq ρ l k h hk))]) (fun h => absurd (Finset.mem_univ k) h)]
        rw [ite_eq_left hk]
      omega
    · push Not at hex
      simp [f, hex]
  have hsum_on : ∑ k, on k = ∑ ρ ∈ s, f ρ := by
    simp only [hon, f]; exact Finset.sum_comm
  have hN1 : N ≤ ∑ k, on k := by
    calc N = ∑ _k : Fin N, 1 := by simp
      _ ≤ ∑ k, on k := Finset.sum_le_sum fun k _ => hon1 k
  have hfs : ∑ ρ ∈ s, f ρ ≤ ∑ ρ ∈ s, Zd.mult ρ := Finset.sum_le_sum hf_le
  have hcount : ∑ ρ ∈ s, Zd.mult ρ = N := hN
  -- equality everywhere
  have heq_f : ∑ ρ ∈ s, f ρ = ∑ ρ ∈ s, Zd.mult ρ := by omega
  have hpt := (Finset.sum_eq_sum_iff_of_le hf_le).1 heq_f ρ hρ
  have hc := ((Zd.mem_boxZeros).1 hρ).1
  have hm := Zd.one_le_mult ρ hc
  -- ρ lies in some interval
  obtain ⟨k, hk⟩ : ∃ k, P k ρ := by
    by_contra hex; push Not at hex
    have : f ρ = 0 := by simp [f, hex]
    omega
  refine ⟨hk.1, ?_⟩
  -- each interval carries exactly multiplicity 1
  have heq_on : ∑ k, on k = ∑ _k : Fin N, 1 := by simp; omega
  have hon_eq := (Finset.sum_eq_sum_iff_of_le (fun k _ => hon1 k)).1 heq_on.symm k
    (Finset.mem_univ k)
  have hmle : Zd.mult ρ ≤ on k := by
    rw [hon k]
    have := Finset.single_le_sum (f := fun σ => if P k σ then Zd.mult σ else 0)
      (fun _ _ => Nat.zero_le _) hρ
    simpa [ite_eq_left hk] using this
  omega

/-- Lemma B in the doc's form: points p_0 < p_1 < … < p_N in [t0, t1] with certified strictly
alternating signs of Z. -/
theorem lemmaB_alternating {σ0 σ1 t0 t1 : ℝ} (hσ0 : σ0 ≤ 1 / 2) (hσ1 : 1 / 2 ≤ σ1) (N : ℕ)
    (hN : Zd.boxCount σ0 σ1 t0 t1 = N) {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (p : Fin (N + 1) → ℝ) (hp : StrictMono p) (hp0 : t0 ≤ p 0) (hpN : p (Fin.last N) ≤ t1)
    (halt : ∀ k : Fin N, Z (p k.castSucc) * Z (p k.succ) < 0)
    (ρ : ℂ) (hρ : ρ ∈ Zd.boxZeros σ0 σ1 t0 t1) : ρ.re = 1 / 2 ∧ Zd.mult ρ = 1 := by
  refine Zd.lemmaB hσ0 hσ1 N hN hL (fun k => p k.castSucc) (fun k => p k.succ)
    (fun k => hp (Fin.castSucc_lt_succ)) (fun k => le_trans hp0 (hp.monotone (Fin.zero_le _)))
    (fun k => le_trans (hp.monotone (Fin.le_last _)) hpN) ?_ halt ρ hρ
  intro k l hkl
  rcases lt_or_gt_of_ne hkl with h | h
  · rw [Set.disjoint_left]
    rintro x ⟨-, hx2⟩ ⟨hx3, -⟩
    have : p k.succ ≤ p l.castSucc := hp.monotone (Fin.succ_le_castSucc_iff.2 h)
    linarith
  · rw [Set.disjoint_left]
    rintro x ⟨hx1, -⟩ ⟨-, hx4⟩
    have : p l.succ ≤ p k.castSucc := hp.monotone (Fin.succ_le_castSucc_iff.2 h)
    linarith

/-- Lemma B, window form (box containing the strip). -/
theorem lemmaB_closed {σ0 σ1 t0 t1 : ℝ} (hσ0 : σ0 ≤ 0) (hσ1 : 1 ≤ σ1) (N : ℕ)
    (hN : Zd.boxCount σ0 σ1 t0 t1 = N) {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (a b : Fin N → ℝ) (hab : ∀ k, a k < b k) (ha : ∀ k, t0 ≤ a k) (hb : ∀ k, b k ≤ t1)
    (hdisj : ∀ k l, k ≠ l → Disjoint (Ioo (a k) (b k)) (Ioo (a l) (b l)))
    (hZ : ∀ k, Z (a k) * Z (b k) < 0) : Zd.Closed t0 t1 := by
  intro ρ hc h0 h1
  have hs := Zd.strip ρ hc
  exact Zd.lemmaB (by linarith) (by linarith) N hN hL a b hab ha hb hdisj hZ ρ
    ((Zd.mem_boxZeros).2 ⟨hc, h0, h1, by linarith, by linarith⟩)

end ZeroData

end Atlas
