/-
Atlas certificate logic — L1 (sign-change credit), L2 (the certificate Theorem),
L3 (atlas_v3 Lemma 2, parity ⇒ simplicity), L4 (atlas_v4 §10 parity-free S-layer (i), (ii)).
All at the level of atoms (THEORY_ZSIGN §0–§3).
-/
import Atlas.Basic

noncomputable section

open Finset Set

namespace Atlas

namespace Cert

variable {J ι : Type*} [Fintype J] [Fintype ι] (C : Cert J ι)

/-! ## L1. Sign-change credit (SUM rule) -/

/-- **L1 (THEORY_ZSIGN §2 step (iii), §3 "Overlapping / duplicate intervals").**
For any family of intervals (overlapping or duplicated), if each n_i ≥ 1 and w ≥ 0, then
Σ_a f_a Σ_i w_i χ_i(a) = Σ_i w_i n_i ≥ Σ_i w_i. -/
theorem signChange_credit (hw : ∀ i, 0 ≤ C.w i) (A : Multiset Atom)
    (hn : ∀ i, 1 ≤ C.n i A) :
    C.W ≤ (A.map fun a => (a.f : ℝ) * C.wsum a.x a.d).sum := by
  rw [C.sum_fwsum]
  unfold W
  refine Finset.sum_le_sum fun i _ => ?_
  have := mul_le_mul_of_nonneg_left (hn i) (hw i)
  linarith

/-- L1, the form used in the proofs: Σ_i w_i ≤ Σ_i w_i n_i. -/
theorem W_le_sum_wn (hw : ∀ i, 0 ≤ C.w i) (A : Multiset Atom) (hn : ∀ i, 1 ≤ C.n i A) :
    C.W ≤ ∑ i, C.w i * C.n i A := by
  have := C.signChange_credit hw A hn; rwa [C.sum_fwsum] at this

/-- L1 with parity (atlas_v3 Lemma 2): if every n_i is odd, and n_i ≥ 2 whenever
x⋆ ∈ I_i, then Σ_i w_i n_i ≥ Σ_i w_i + 2 Σ_{i ∋ x⋆} w_i. -/
theorem W_le_sum_wn_parity (hw : ∀ i, 0 ≤ C.w i) (A : Multiset Atom) (xs : ℝ)
    (hodd : ∀ i, Odd (C.nNat i A))
    (htwo : ∀ i, xs ∈ Ioo (C.t1 i) (C.t2 i) → 2 ≤ C.nNat i A) :
    C.W + 2 * C.wsum xs 0 ≤ ∑ i, C.w i * C.n i A := by
  unfold W wsum
  rw [Finset.mul_sum, ← Finset.sum_add_distrib]
  refine Finset.sum_le_sum fun i _ => ?_
  rw [C.n_eq_nNat]
  unfold chi
  by_cases hx : xs ∈ Ioo (C.t1 i) (C.t2 i)
  · have h3 : 3 ≤ C.nNat i A := by
      obtain ⟨k, hk⟩ := hodd i; have := htwo i hx; omega
    have h3' : (3 : ℝ) ≤ C.nNat i A := by exact_mod_cast h3
    simp only [hx, and_self, ite_true]
    nlinarith [hw i]
  · have h1 : 1 ≤ C.nNat i A := by obtain ⟨k, hk⟩ := hodd i; omega
    have h1' : (1 : ℝ) ≤ C.nNat i A := by exact_mod_cast h1
    simp only [hx, and_false, ite_false]
    nlinarith [hw i]

/-! ## L2. The certificate Theorem (THEORY_ZSIGN §2) -/

/-- **L2 (THEORY_ZSIGN §2, Theorem).** Let A = a⋆ ::ₘ A' be all atoms of the window, with
a⋆ = (x⋆, d⋆, 2) an off-line pair, d⋆ > 0, (x⋆, d⋆) in the candidate region
R = [x0,x1] × [d0,d1]. Assume (H_model) for every other atom, (H_rows), (H_count) for A,
n_i ≥ 1 for every interval (Lemma 1), y, w ≥ 0, (R) on every var box and (C) on R ∩ {d > 0}.
Then False: no off-line pair of zeros has (height, displacement) in R. -/
theorem certificate (hy : C.DualNonneg) (boxes : Set VarBox)
    (x0 x1 d0 d1 : ℝ)
    (hR : C.CondR boxes)
    (hC : ∀ x d, x0 ≤ x → x ≤ x1 → d0 ≤ d → d ≤ d1 → 0 < d →
      0 < C.Phi x d 2 - C.K - 2 * C.yc + C.W)
    (astar : Atom) (A' : Multiset Atom)
    (hf : astar.f = 2) (hd : 0 < astar.d)
    (hx0 : x0 ≤ astar.x) (hx1 : astar.x ≤ x1) (hd0 : d0 ≤ astar.d) (hd1 : astar.d ≤ d1)
    (hM : HModel boxes A')
    (hRows : C.HRows (astar ::ₘ A')) (hCount : C.HCount (astar ::ₘ A'))
    (hn : ∀ i, 1 ≤ C.n i (astar ::ₘ A')) : False := by
  have hsum := C.sum_Phi_le hy _ hRows hCount
  have hcore := C.core astar A' hsum (C.PhiW_nonneg_of_model hR hM)
  have hW := C.W_le_sum_wn hy.2.2.2 _ hn
  have hPW : C.PhiW astar.x astar.d astar.f = C.Phi astar.x astar.d astar.f := by
    unfold PhiW; rw [C.wsum_of_d_ne hd.ne']; ring
  have hc := hC astar.x astar.d hx0 hx1 hd0 hd1 hd
  rw [hPW, hf] at hcore
  linarith

/-- Reduction (THEORY_ZSIGN §3 "Reduction"): with no intervals the conditions are the old ones. -/
example (C : Cert J Empty) : C.W = 0 := by simp [Cert.W]

/-! ## L3. atlas_v3 Lemma 2: parity ⇒ simplicity at d = 0 -/

/-- **L3 (atlas_v3 README, Lemma 2).** A multiple on-line zero at height x⋆ ∈ [x0, x1] is
written as one f = 2 atom a⋆ = (x⋆, 0, 2) plus further atoms A' (the other k − 2 units, each an
f = 1 atom in an `on` box, plus all other window atoms). If (R) holds, (H_model) holds for A',
(H_rows), (H_count) hold for a⋆ ::ₘ A', every n_i is ODD (Lemma 1 with parity), and the
unchanged candidate condition (C) holds at the d = 0 point (x⋆, 0), then False. -/
theorem lemma2_parity (hy : C.DualNonneg) (boxes : Set VarBox)
    (hR : C.CondR boxes)
    (xs : ℝ) (hC0 : 0 < C.Phi xs 0 2 - C.K - 2 * C.yc + C.W)
    (A' : Multiset Atom) (hM : HModel boxes A')
    (hRows : C.HRows (⟨xs, 0, 2⟩ ::ₘ A')) (hCount : C.HCount (⟨xs, 0, 2⟩ ::ₘ A'))
    (hodd : ∀ i, Odd (C.nNat i (⟨xs, 0, 2⟩ ::ₘ A'))) : False := by
  set astar : Atom := ⟨xs, 0, 2⟩
  have hsum := C.sum_Phi_le hy _ hRows hCount
  have hcore := C.core astar A' hsum (C.PhiW_nonneg_of_model hR hM)
  -- if x⋆ ∈ I_i then a⋆ contributes f = 2 to n_i
  have htwo : ∀ i, xs ∈ Ioo (C.t1 i) (C.t2 i) → 2 ≤ C.nNat i (astar ::ₘ A') := by
    intro i hi
    unfold nNat
    simp only [Multiset.map_cons, Multiset.sum_cons, astar, hi, and_self, ite_true]
    omega
  have hpar := C.W_le_sum_wn_parity hy.2.2.2 _ xs hodd htwo
  have hPW : C.PhiW astar.x astar.d astar.f = C.Phi xs 0 2 - 2 * C.wsum xs 0 := by
    simp [PhiW, astar]
  rw [hPW] at hcore
  linarith

/-! ## L4. atlas_v4 §10: simplicity without parity (S-layer) -/

/-- **L4 (i) (atlas_v4 §10 (i)).** Main certificates are parity-free away from their
intervals: a multiple on-line zero at x⋆ lying in NO interval I_i (open intervals suffice; the
doc says "no closed interval", which is stronger) is excluded using only n_i ≥ 1. -/
theorem slayer_away (hy : C.DualNonneg) (boxes : Set VarBox)
    (hR : C.CondR boxes)
    (xs : ℝ) (hC0 : 0 < C.Phi xs 0 2 - C.K - 2 * C.yc + C.W)
    (hout : ∀ i, xs ∉ Ioo (C.t1 i) (C.t2 i))
    (A' : Multiset Atom) (hM : HModel boxes A')
    (hRows : C.HRows (⟨xs, 0, 2⟩ ::ₘ A')) (hCount : C.HCount (⟨xs, 0, 2⟩ ::ₘ A'))
    (hn : ∀ i, 1 ≤ C.n i (⟨xs, 0, 2⟩ ::ₘ A')) : False := by
  set astar : Atom := ⟨xs, 0, 2⟩
  have hsum := C.sum_Phi_le hy _ hRows hCount
  have hcore := C.core astar A' hsum (C.PhiW_nonneg_of_model hR hM)
  have hW := C.W_le_sum_wn hy.2.2.2 _ hn
  have hws : C.wsum xs 0 = 0 := by
    unfold wsum chi; simp [hout]
  have hPW : C.PhiW astar.x astar.d astar.f = C.Phi xs 0 2 := by
    simp [PhiW, astar, hws]
  rw [hPW] at hcore
  linarith

/-- Σ over the intervals whose CLOSURE contains x. -/
def wsumCl (x : ℝ) : ℝ := ∑ i, C.w i * (if x ∈ Icc (C.t1 i) (C.t2 i) then 1 else 0)

lemma wsum_le_wsumCl (hw : ∀ i, 0 ≤ C.w i) (x : ℝ) : C.wsum x 0 ≤ C.wsumCl x := by
  unfold wsum wsumCl chi
  refine Finset.sum_le_sum fun i _ => ?_
  by_cases h : x ∈ Ioo (C.t1 i) (C.t2 i)
  · simp [h, Ioo_subset_Icc_self h]
  · simp only [h, and_false, ite_false, mul_zero]
    split_ifs <;> linarith [hw i]

/-- **L4 (ii) (atlas_v4 §10 (ii)).** The no-parity candidate condition
Φ(x,0,2) − K − 2yc + Σw − 2 Σ_{i : x ∈ cl I_i} w_i > 0 (pointwise form of the one-line change of
the verifier) at the height x⋆ of a multiple on-line zero gives a contradiction using only
n_i ≥ 1 (no parity). -/
theorem slayer_perzero (hy : C.DualNonneg) (boxes : Set VarBox)
    (hR : C.CondR boxes)
    (xs : ℝ) (hCnp : 0 < C.Phi xs 0 2 - C.K - 2 * C.yc + C.W - 2 * C.wsumCl xs)
    (A' : Multiset Atom) (hM : HModel boxes A')
    (hRows : C.HRows (⟨xs, 0, 2⟩ ::ₘ A')) (hCount : C.HCount (⟨xs, 0, 2⟩ ::ₘ A'))
    (hn : ∀ i, 1 ≤ C.n i (⟨xs, 0, 2⟩ ::ₘ A')) : False := by
  set astar : Atom := ⟨xs, 0, 2⟩
  have hsum := C.sum_Phi_le hy _ hRows hCount
  have hcore := C.core astar A' hsum (C.PhiW_nonneg_of_model hR hM)
  have hW := C.W_le_sum_wn hy.2.2.2 _ hn
  have hPW : C.PhiW astar.x astar.d astar.f = C.Phi xs 0 2 - 2 * C.wsum xs 0 := by
    simp [PhiW, astar]
  have hcl := C.wsum_le_wsumCl hy.2.2.2 xs
  rw [hPW] at hcore
  linarith

/-- atlas_v4 §10 remark: a no-parity certificate cannot cover two true (simple, on-line)
zeros at once. If the no-parity condition holds at the heights of two distinct on-line atoms
a, b (f = 1, d = 0) and all other atoms are modelled, (H_rows), (H_count), n_i ≥ 1 give False. -/
theorem slayer_atMostOne (hy : C.DualNonneg) (boxes : Set VarBox) (hR : C.CondR boxes)
    (xa xb : ℝ)
    (hCa : 0 < C.Phi xa 0 2 - C.K - 2 * C.yc + C.W - 2 * C.wsumCl xa)
    (hCb : 0 < C.Phi xb 0 2 - C.K - 2 * C.yc + C.W - 2 * C.wsumCl xb)
    (A' : Multiset Atom) (hM : HModel boxes A')
    (hRows : C.HRows (⟨xa, 0, 1⟩ ::ₘ ⟨xb, 0, 1⟩ ::ₘ A'))
    (hCount : C.HCount (⟨xa, 0, 1⟩ ::ₘ ⟨xb, 0, 1⟩ ::ₘ A'))
    (hn : ∀ i, 1 ≤ C.n i (⟨xa, 0, 1⟩ ::ₘ ⟨xb, 0, 1⟩ ::ₘ A')) : False := by
  have hsum := C.sum_Phi_le hy _ hRows hCount
  have hW := C.W_le_sum_wn hy.2.2.2 _ hn
  have h := C.sum_PhiW (⟨xa, 0, 1⟩ ::ₘ ⟨xb, 0, 1⟩ ::ₘ A')
  simp only [Multiset.map_cons, Multiset.sum_cons] at h hsum
  have h0 := msum_nonneg A' (fun a => C.PhiW a.x a.d a.f) (C.PhiW_nonneg_of_model hR hM)
  have ha := C.wsum_le_wsumCl hy.2.2.2 xa
  have hb := C.wsum_le_wsumCl hy.2.2.2 xb
  have e2 : ∀ x, C.Phi x 0 2 = 2 * C.Phi x 0 1 := fun x => by unfold Phi; push_cast; ring
  have ea : C.PhiW xa 0 1 = C.Phi xa 0 1 - C.wsum xa 0 := by simp [PhiW]
  have eb : C.PhiW xb 0 1 = C.Phi xb 0 1 - C.wsum xb 0 := by simp [PhiW]
  rw [e2] at hCa hCb
  linarith

end Cert

end Atlas
