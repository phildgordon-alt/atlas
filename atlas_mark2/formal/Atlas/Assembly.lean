/-
Atlas — L6: assembly of the window claim (atlas_v4 §6, §10 (iii); atlas_v4_1 §6).
-/
import Atlas.Window
import Atlas.Counting

noncomputable section

open Finset Set
open scoped Classical

namespace Atlas

namespace ZeroData

variable (Zd : ZeroData)

/-- [x0, x1] is the region of a v4 certificate that passed the verifier, with its Arb sign facts
and its inherited (H_rows), (H_count). -/
def V4Valid (Z : ℝ → ℝ) (x0 x1 : ℝ) : Prop :=
  ∃ (J ι : Type) (_ : Fintype J) (_ : Fintype ι) (K : V4Cert J ι),
    K.x0 = x0 ∧ K.x1 = x1 ∧ (∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0) ∧
    Zd.ZRows K.C K.wlo K.whi ∧ Zd.ZCount K.C K.wlo K.whi

/-- [x0, x1] is a v4 region whose simplicity is closed by the S-layer (claim (B), §10 (iii)). -/
def V4ValidB (Z : ℝ → ℝ) (x0 x1 : ℝ) : Prop :=
  ∃ (J ι : Type) (_ : Fintype J) (_ : Fintype ι) (K : V4Cert J ι),
    K.x0 = x0 ∧ K.x1 = x1 ∧ (∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0) ∧
    Zd.ZRows K.C K.wlo K.whi ∧ Zd.ZCount K.C K.wlo K.whi ∧
    (∀ i x, x ∈ Icc (K.C.t1 i) (K.C.t2 i) → K.x0 ≤ x → x ≤ K.x1 →
      ∃ s0 s1, s0 ≤ x ∧ x ≤ s1 ∧ Zd.NPValid Z s0 s1)

/-- [t0, t1] is a counted leaf (atlas_v4_1): rule `count` (Lemma A) or rule `signchanges`
(Lemma B), in a box [σ0, σ1] × [t0, t1] symmetric about 1/2 and containing the strip. -/
def CountedLeaf (Z : ℝ → ℝ) (t0 t1 : ℝ) : Prop :=
  (∃ σ0 σ1, σ0 + σ1 = 1 ∧ σ0 ≤ 0 ∧ Zd.boxCount σ0 σ1 t0 t1 ≤ 1) ∨
  (∃ σ0 σ1 N, ∃ a b : Fin N → ℝ, σ0 ≤ 0 ∧ 1 ≤ σ1 ∧ Zd.boxCount σ0 σ1 t0 t1 = N ∧
    (∀ k, a k < b k) ∧ (∀ k, t0 ≤ a k) ∧ (∀ k, b k ≤ t1) ∧
    (∀ k l, k ≠ l → Disjoint (Ioo (a k) (b k)) (Ioo (a l) (b l))) ∧
    (∀ k, Z (a k) * Z (b k) < 0))

lemma CountedLeaf.closed {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z) {t0 t1 : ℝ}
    (h : Zd.CountedLeaf Z t0 t1) : Zd.Closed t0 t1 := by
  rcases h with ⟨σ0, σ1, hs, hσ, hN⟩ | ⟨σ0, σ1, N, a, b, hσ0, hσ1, hN, hab, ha, hb, hd, hZ⟩
  · exact Zd.lemmaA_closed hs hσ hN
  · exact Zd.lemmaB_closed hσ0 hσ1 N hN hL a b hab ha hb hd hZ

/-- Closed regions glue: if the x-projections of the closed regions cover the hull, the hull is
closed. -/
theorem closed_of_cover {h0 h1 : ℝ} (R : Set (ℝ × ℝ)) (hR : ∀ r ∈ R, Zd.Closed r.1 r.2)
    (hcov : ∀ x, h0 ≤ x → x ≤ h1 → ∃ r ∈ R, r.1 ≤ x ∧ x ≤ r.2) : Zd.Closed h0 h1 := by
  intro ρ hc ha hb
  obtain ⟨r, hr, h1', h2'⟩ := hcov ρ.im ha hb
  exact hR r hr ρ hc h1' h2'

/-- **L6, claim (A) (atlas_v4 §6 + atlas_v4_1 §6).** If the hull [h0, h1] is covered by regions
each of which is a passed v4 certificate region or a counted leaf, then every zero with height in
the hull is on the critical line and simple. Hypotheses: Lemma 1 (parity form), and per region the
Arb/inherited facts packaged in `V4Valid` / `CountedLeaf`. -/
theorem window_claim_A {Z : ℝ → ℝ} (hL : Zd.Lemma1Parity Z) {h0 h1 : ℝ} (R : Set (ℝ × ℝ))
    (hR : ∀ r ∈ R, Zd.V4Valid Z r.1 r.2 ∨ Zd.CountedLeaf Z r.1 r.2)
    (hcov : ∀ x, h0 ≤ x → x ≤ h1 → ∃ r ∈ R, r.1 ≤ x ∧ x ≤ r.2) : Zd.Closed h0 h1 := by
  refine Zd.closed_of_cover R (fun r hr => ?_) hcov
  rcases hR r hr with ⟨J, ι, _, _, K, h0', h1', hZ, hRows, hCount⟩ | hC
  · rw [← h0', ← h1']; exact Zd.v4_closed K hL hZ hRows hCount
  · exact CountedLeaf.closed Zd (Lemma1Weak.of_parity Zd hL) hC

/-- **L6, claim (B) (atlas_v4 §10 (iii)).** The same conclusion from the WEAK Lemma 1 only
(no parity, no atlas_v3 Lemma 2), when every v4 region also has its intervals covered by
no-parity per-zero certificates. -/
theorem window_claim_B {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z) {h0 h1 : ℝ} (R : Set (ℝ × ℝ))
    (hR : ∀ r ∈ R, Zd.V4ValidB Z r.1 r.2 ∨ Zd.CountedLeaf Z r.1 r.2)
    (hcov : ∀ x, h0 ≤ x → x ≤ h1 → ∃ r ∈ R, r.1 ≤ x ∧ x ≤ r.2) : Zd.Closed h0 h1 := by
  refine Zd.closed_of_cover R (fun r hr => ?_) hcov
  rcases hR r hr with ⟨J, ι, _, _, K, h0', h1', hZ, hRows, hCount, hnp⟩ | hC
  · rw [← h0', ← h1']; exact Zd.claimB K hL hZ hRows hCount hnp
  · exact CountedLeaf.closed Zd hL hC

/-- The 2-D tiling form used by the replay (hull × [0, 1/2] covered by regions [x0,x1] × [0,1/2])
implies the 1-D cover used above (take d = 0). -/
lemma cover_of_cover2D {h0 h1 : ℝ} (R : Set (ℝ × ℝ))
    (h2 : ∀ x d, h0 ≤ x → x ≤ h1 → 0 ≤ d → d ≤ 1 / 2 →
      ∃ r ∈ R, r.1 ≤ x ∧ x ≤ r.2 ∧ (0 : ℝ) ≤ d ∧ d ≤ 1 / 2) :
    ∀ x, h0 ≤ x → x ≤ h1 → ∃ r ∈ R, r.1 ≤ x ∧ x ≤ r.2 := by
  intro x ha hb
  obtain ⟨r, hr, h1', h2', -⟩ := h2 x 0 ha hb le_rfl (by norm_num)
  exact ⟨r, hr, h1', h2'⟩

end ZeroData

end Atlas
