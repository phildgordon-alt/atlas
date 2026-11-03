/-
Atlas — correctness of the certificate-FILE audit (`AtlasAudit/Check.lean`, run by `lake exe atlas_audit`).

For each Boolean check of `AtlasAudit.Check` we prove: check = true ⇒ the set-theoretic statement over ℝ
(the exported numbers are exact rationals, cast into ℝ). Then we connect the checked statements to the
hypotheses of the existing certificate theorems:
* `exists_v4Cert`: a checked v4 certificate file supplies EVERY combinatorial field of `V4Cert`
  (region ⊂ window, intervals ⊂ window, t1 < t2, bins cover the window, and (R) on the file's model
  implies (R) on `allOpen bins`); only the Arb facts (dual ≥ 0, (R), (C)) remain as hypotheses.
* `targetOk_spec` / `closed_of_targetOk`: the exact tiling check implies the pointwise 2-D cover of
  target × [0, 1/2] (including the d = 0 line), and hence the window claim from per-region claims.
* `claimBOk_spec`: the S-layer coverage hypothesis of `V4ValidB` / `claimB`.
* `centralOk_spec`: the central-reduction policy (used by `Atlas/Central.lean`).
TRUSTED (outside this file): the exporter and the parser (text → `CertD`), and every Arb verdict.
-/
import Atlas.Window
import Atlas.Assembly
import AtlasAudit.Check
import Mathlib.Data.Rat.Cast.Order

noncomputable section

open Set Atlas

namespace AtlasAudit

/-! ### Bool → Prop plumbing -/

lemma dle {a b : Rat} (h : decide (a ≤ b) = true) : (a : ℝ) ≤ b := by
  exact_mod_cast of_decide_eq_true h

lemma dlt {a b : Rat} (h : decide (a < b) = true) : (a : ℝ) < b := by
  exact_mod_cast of_decide_eq_true h

/-! ### 1. region and interval checks -/

theorem regionOk_spec {np : Bool} {wlo whi : Rat} {r : Reg} (h : regionOk np wlo whi r = true) :
    (wlo : ℝ) ≤ r.x0 ∧ (r.x0 : ℝ) < r.x1 ∧ (r.x1 : ℝ) ≤ whi ∧ (r.d0 : ℝ) = 0 ∧
      (if np then (r.d1 : ℝ) = 0 else (r.d1 : ℝ) = 1 / 2) := by
  unfold regionOk at h
  simp only [Bool.and_eq_true] at h
  obtain ⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩ := h
  refine ⟨dle h1, dlt h2, dle h3, ?_, ?_⟩
  · have := of_decide_eq_true h4; rw [this]; simp
  · cases np
    · have : r.d1 = 1 / 2 := of_decide_eq_true (by simpa using h5)
      simp only [Bool.false_eq_true, ite_false]; rw [this]; push_cast; ring
    · have : r.d1 = 0 := of_decide_eq_true (by simpa using h5)
      simp only [ite_true]; rw [this]; simp

theorem ivOk_spec {wlo whi : Rat} {i : Iv} (h : ivOk wlo whi i = true) :
    (wlo : ℝ) ≤ i.t1 ∧ (i.t1 : ℝ) < i.t2 ∧ (i.t2 : ℝ) ≤ whi := by
  unfold ivOk at h
  simp only [Bool.and_eq_true] at h
  exact ⟨dle h.1.1, dlt h.1.2, dle h.2⟩

/-- sorted + t1 < t2 ⇒ pairwise strictly separated (so sorted and pairwise disjoint as closed sets). -/
theorem sortedDisjoint_spec : ∀ (l : List Iv), sortedDisjoint l = true →
    (∀ i ∈ l, (i.t1 : ℝ) < i.t2) → l.Pairwise (fun a b => (a.t2 : ℝ) < b.t1)
  | [], _, _ => List.Pairwise.nil
  | [_], _, _ => List.pairwise_singleton _ _
  | a :: b :: l, h, hlt => by
    unfold sortedDisjoint at h
    simp only [Bool.and_eq_true] at h
    have hab : (a.t2 : ℝ) < b.t1 := dlt h.1
    have ih := sortedDisjoint_spec (b :: l) h.2 (fun i hi => hlt i (List.mem_cons_of_mem _ hi))
    refine List.Pairwise.cons ?_ ih
    intro c hc
    rcases List.mem_cons.1 hc with rfl | hc
    · exact hab
    · have hb := hlt b (by simp)
      have hbc := List.rel_of_pairwise_cons ih hc
      linarith

/-- the separated intervals, indexed: i < j ⇒ t2_i < t1_j; and pairwise disjoint open intervals
(the form of the hypotheses of `lemmaB` and `localCount_closed`). -/
theorem ivs_disjoint {l : List Iv} (h : l.Pairwise (fun a b => (a.t2 : ℝ) < b.t1)) (i j : Fin l.length) (hij : i ≠ j) :
    Disjoint (Ioo ((l.get i).t1 : ℝ) (l.get i).t2) (Ioo ((l.get j).t1 : ℝ) (l.get j).t2) := by
  rw [List.pairwise_iff_getElem] at h
  rw [Set.disjoint_left]
  intro x hx hx'
  rcases lt_or_gt_of_ne (Fin.val_ne_of_ne hij) with hl | hl
  · have := h i j i.2 j.2 hl
    simp only [List.get_eq_getElem] at hx hx'
    linarith [hx.2, hx'.1]
  · have := h j i j.2 i.2 hl
    simp only [List.get_eq_getElem] at hx hx'
    linarith [hx.1, hx'.2]

/-! ### 2. the exact 1-D cover (sweep) -/

/-- invariant of the sweep: `some c` ⇒ [lo, c] ⊂ ⋃ of the intervals seen so far (all in S). -/
def SweepInv (lo : Rat) (S : Rat × Rat → Prop) : Option Rat → Prop
  | none => True
  | some c => ∀ x : ℝ, (lo : ℝ) ≤ x → x ≤ c → ∃ p, S p ∧ (p.1 : ℝ) ≤ x ∧ x ≤ p.2

lemma sweepStep_inv {lo : Rat} {S : Rat × Rat → Prop} {st : Option Rat} {p : Rat × Rat}
    (hst : SweepInv lo S st) (hp : S p) : SweepInv lo S (sweepStep lo st p) := by
  cases st with
  | none =>
    simp only [sweepStep]
    split_ifs with h
    · intro x hx1 hx2
      exact ⟨p, hp, le_trans (by exact_mod_cast h.1) hx1, hx2⟩
    · trivial
  | some c =>
    simp only [sweepStep]
    split_ifs with h1 h2
    · intro x hx1 hx2
      by_cases hxc : x ≤ c
      · exact hst x hx1 hxc
      · exact ⟨p, hp, le_trans (by exact_mod_cast h1) (le_of_lt (not_le.1 hxc)), hx2⟩
    · exact hst
    · exact hst

lemma foldl_inv {lo : Rat} {S : Rat × Rat → Prop} :
    ∀ (l : List (Rat × Rat)) (st : Option Rat), SweepInv lo S st → (∀ p ∈ l, S p) →
      SweepInv lo S (l.foldl (sweepStep lo) st)
  | [], _, h, _ => h
  | p :: l, st, h, hl => by
    simp only [List.foldl_cons]
    exact foldl_inv l _ (sweepStep_inv h (hl p (by simp))) (fun q hq => hl q (by simp [hq]))

/-- **Covering lemma.** `coversB lo hi L = true` ⇒ every real x ∈ [lo, hi] lies in some [a, b] ∈ L. -/
theorem coversB_spec {lo hi : Rat} {L : List (Rat × Rat)} (h : coversB lo hi L = true) :
    ∀ x : ℝ, (lo : ℝ) ≤ x → x ≤ hi → ∃ p ∈ L, (p.1 : ℝ) ≤ x ∧ x ≤ p.2 := by
  unfold coversB at h
  have hinv := foldl_inv (lo := lo) (S := fun p => p ∈ L)
    (L.mergeSort (fun p q => decide (p.1 ≤ q.1))) none trivial
    (fun p hp => List.mem_mergeSort.1 hp)
  unfold sweep at h
  split at h
  · rename_i c hc
    rw [hc] at hinv
    intro x hx1 hx2
    obtain ⟨p, hp, h1, h2⟩ := hinv x hx1 (le_trans hx2 (dle h))
    exact ⟨p, hp, h1, h2⟩
  · exact absurd h (by simp)

/-! ### 3. the central policy -/

theorem centralOk_spec {expect : Nat} {c : CertD} (h : centralOk expect c = true) :
    (c.central.isSome = true ↔ c.m0 ≠ 0) ∧
    (c.m0 ≠ 0 ↔ (c.wlo : ℝ) < 0 ∧ (0 : ℝ) < c.whi ∧ expect ≠ 0) ∧
    (c.m0 ≠ 0 → c.m0 = expect ∧ ∀ i ∈ c.ivs, (i.t2 : ℝ) < 0 ∨ (0 : ℝ) < i.t1) := by
  unfold centralOk at h
  simp only [Bool.and_eq_true, beq_iff_eq, Bool.or_eq_true, Bool.not_eq_true'] at h
  obtain ⟨⟨h1, h2⟩, h3⟩ := h
  unfold CertD.used at h1 h2 h3
  unfold CertD.has0 at h2
  refine ⟨?_, ?_, ?_⟩
  · rw [h1]; simp
  · constructor
    · intro hm
      have : (decide (c.wlo < 0) && decide (0 < c.whi) && decide (expect ≠ 0)) = true := by
        rw [← h2]; simpa using hm
      simp only [Bool.and_eq_true, decide_eq_true_eq] at this
      exact ⟨by exact_mod_cast this.1.1, by exact_mod_cast this.1.2, this.2⟩
    · rintro ⟨ha, hb, he⟩
      have ha' : c.wlo < 0 := by exact_mod_cast ha
      have hb' : 0 < c.whi := by exact_mod_cast hb
      have : decide (c.m0 ≠ 0) = true := by rw [h2]; simp [ha', hb', he]
      simpa using this
  · intro hm
    have hu : decide (c.m0 ≠ 0) = true := by simpa using hm
    rcases h3 with h3 | h3
    · rw [hu] at h3; exact absurd h3 (by simp)
    · simp only [decide_eq_true_eq, List.all_eq_true] at h3
      refine ⟨h3.1, fun i hi => ?_⟩
      have := h3.2 i hi
      unfold meets0 at this
      simp only [Bool.not_eq_true', Bool.and_eq_false_iff, decide_eq_false_iff_not, not_le] at this
      rcases this with h | h
      · right; exact_mod_cast h
      · left; exact_mod_cast h

/-! ### 4. the v4 all-open model -/

/-- the var boxes of an exported model (`on` ↦ f = 1, `off` ↦ f = 2) -/
def varBoxes (vs : List Var) : Set VarBox :=
  {B | ∃ v ∈ vs, B = ⟨v.lo, v.hi, v.dlo, v.dhi, if v.on then 1 else 2⟩}

/-- the bins as a set of real pairs -/
def binSet (bs : List (Rat × Rat)) : Set (ℝ × ℝ) := {p | ∃ q ∈ bs, p = ((q.1 : ℝ), (q.2 : ℝ))}

theorem binsOf_spec : ∀ (vs : List Var) (bs : List (Rat × Rat)), binsOf vs = some bs →
    ∀ q ∈ bs, (∃ v ∈ vs, v.on = true ∧ v.lo = q.1 ∧ v.hi = q.2 ∧ v.dlo = 0 ∧ v.dhi = 0) ∧
      (∃ v ∈ vs, v.on = false ∧ v.lo = q.1 ∧ v.hi = q.2 ∧ v.dlo = 0 ∧ v.dhi = 1 / 2)
  | [], bs, h => by
    simp only [binsOf, Option.some.injEq] at h; subst h; simp
  | [_], _, h => by simp [binsOf] at h
  | a :: b :: l, bs, h => by
    unfold binsOf at h
    split_ifs at h with hc
    · simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_true_eq] at hc
      obtain ⟨⟨⟨⟨⟨⟨⟨ha, hb⟩, hlo⟩, hhi⟩, hd1⟩, hd2⟩, hd3⟩, hd4⟩ := hc
      cases hl : binsOf l with
      | none => rw [hl] at h; simp at h
      | some bs' =>
        rw [hl] at h
        simp only [Option.map_some, Option.some.injEq] at h
        subst h
        intro q hq
        rcases List.mem_cons.1 hq with rfl | hq
        · exact ⟨⟨a, by simp, ha, rfl, rfl, hd1, hd2⟩, ⟨b, by simp, hb, hlo.symm, hhi.symm, hd3, hd4⟩⟩
        · obtain ⟨⟨v, hv, h1⟩, ⟨w, hw, h2⟩⟩ := binsOf_spec l bs' hl q hq
          exact ⟨⟨v, by simp [hv], h1⟩, ⟨w, by simp [hw], h2⟩⟩

/-- the all-open model of the bins is contained in the file's model -/
theorem allOpen_sub {vs : List Var} {bs : List (Rat × Rat)} (h : binsOf vs = some bs) :
    ZeroData.allOpen (binSet bs) ⊆ varBoxes vs := by
  rintro B ⟨p, ⟨q, hq, rfl⟩, hB⟩
  obtain ⟨⟨v, hv, hon, hlo, hhi, hd1, hd2⟩, ⟨w, hw, hoff, hlo', hhi', hd3, hd4⟩⟩ :=
    binsOf_spec vs bs h q hq
  rcases hB with rfl | rfl
  · refine ⟨v, hv, ?_⟩
    simp [hon, hlo, hhi, hd1, hd2]
  · refine ⟨w, hw, ?_⟩
    simp [hoff, hlo', hhi', hd3, hd4]

/-- (R) on the file's model ⇒ (R) on the all-open model of its bins -/
theorem condR_allOpen {J ι : Type*} [Fintype J] [Fintype ι] (C : Cert J ι) {vs : List Var}
    {bs : List (Rat × Rat)} (h : binsOf vs = some bs) (hR : C.CondR (varBoxes vs)) :
    C.CondR (ZeroData.allOpen (binSet bs)) :=
  fun b hb => hR b (allOpen_sub h hb)

theorem modelOk_spec {c : CertD} (h : modelOk c = true) :
    ∃ bs, binsOf c.vars = some bs ∧
      ∀ x : ℝ, (c.wlo : ℝ) ≤ x → x ≤ c.whi → ∃ p ∈ binSet bs, p.1 ≤ x ∧ x ≤ p.2 := by
  unfold modelOk at h
  split at h
  · rename_i bs hbs
    refine ⟨bs, hbs, fun x h1 h2 => ?_⟩
    obtain ⟨q, hq, hq1, hq2⟩ := coversB_spec h x h1 h2
    exact ⟨_, ⟨q, hq, rfl⟩, hq1, hq2⟩
  · exact absurd h (by simp)

/-! ### 5. the per-certificate check -/

theorem certOk_spec {expect : Nat} {model : Bool} {c : CertD} (h : certOk expect model c = true) :
    c.regions ≠ [] ∧
    (∀ r ∈ c.regions, (c.wlo : ℝ) ≤ r.x0 ∧ (r.x0 : ℝ) < r.x1 ∧ (r.x1 : ℝ) ≤ c.whi ∧ (r.d0 : ℝ) = 0 ∧
      (if c.np then (r.d1 : ℝ) = 0 else (r.d1 : ℝ) = 1 / 2)) ∧
    (∀ i ∈ c.ivs, (c.wlo : ℝ) ≤ i.t1 ∧ (i.t1 : ℝ) < i.t2 ∧ (i.t2 : ℝ) ≤ c.whi) ∧
    c.ivs.Pairwise (fun a b => (a.t2 : ℝ) < b.t1) ∧
    centralOk expect c = true ∧
    (model = true → modelOk c = true) := by
  unfold certOk at h
  simp only [Bool.and_eq_true, Bool.not_eq_true', List.all_eq_true, Bool.or_eq_true,
    List.isEmpty_eq_false_iff] at h
  obtain ⟨⟨⟨⟨⟨h0, h1⟩, h2⟩, h3⟩, h4⟩, h5⟩ := h
  have hiv : ∀ i ∈ c.ivs, (c.wlo : ℝ) ≤ i.t1 ∧ (i.t1 : ℝ) < i.t2 ∧ (i.t2 : ℝ) ≤ c.whi :=
    fun i hi => ivOk_spec (h2 i hi)
  refine ⟨h0, fun r hr => regionOk_spec (h1 r hr), hiv,
    sortedDisjoint_spec _ h3 (fun i hi => (hiv i hi).2.1), h4, fun hm => ?_⟩
  rcases h5 with h5 | h5
  · rw [hm] at h5; exact absurd h5 (by simp)
  · exact h5

/-- **File → `V4Cert`.** A (main) certificate that passes `certOk _ true` supplies every combinatorial
field of `V4Cert` for each of its regions. What remains are the Arb-verified facts: the dual is ≥ 0,
(R) holds on the file's model boxes, (C) holds on the region × [0, 1/2]; and the certificate data `C`
must carry the file's intervals (`ht1`, `ht2`). -/
theorem exists_v4Cert {J : Type} [Fintype J] {expect : Nat} {c : CertD}
    (h : certOk expect true c = true) {r : Reg} (hr : r ∈ c.regions)
    (C : Cert J (Fin c.ivs.length))
    (ht1 : ∀ i, C.t1 i = ((c.ivs.get i).t1 : ℝ)) (ht2 : ∀ i, C.t2 i = ((c.ivs.get i).t2 : ℝ))
    (dual : C.DualNonneg) (condR : C.CondR (varBoxes c.vars))
    (condC : ∀ x d, (r.x0 : ℝ) ≤ x → x ≤ r.x1 → 0 ≤ d → d ≤ 1 / 2 →
      0 < C.Phi x d 2 - C.K - 2 * C.yc + C.W) :
    ∃ K : V4Cert J (Fin c.ivs.length), K.C = C ∧ K.wlo = c.wlo ∧ K.whi = c.whi ∧
      K.x0 = r.x0 ∧ K.x1 = r.x1 := by
  obtain ⟨-, hreg, hiv, -, -, hmod⟩ := certOk_spec h
  obtain ⟨bs, hbs, hcov⟩ := modelOk_spec (hmod rfl)
  obtain ⟨hx0, -, hx1, -, -⟩ := hreg r hr
  have hivi : ∀ i : Fin c.ivs.length, (c.wlo : ℝ) ≤ (c.ivs.get i).t1 ∧
      ((c.ivs.get i).t1 : ℝ) < (c.ivs.get i).t2 ∧ ((c.ivs.get i).t2 : ℝ) ≤ c.whi :=
    fun i => hiv _ (List.get_mem _ _)
  let K : V4Cert J (Fin c.ivs.length) :=
    { C := C, wlo := c.wlo, whi := c.whi, x0 := r.x0, x1 := r.x1, bins := binSet bs,
      dual := dual, bins_cover := hcov, condR := condR_allOpen C hbs condR, condC := condC,
      x0_ge := hx0, x1_le := hx1,
      iv_lo := fun i => by rw [ht1]; exact (hivi i).1,
      iv_hi := fun i => by rw [ht2]; exact (hivi i).2.2,
      iv_lt := fun i => by rw [ht1, ht2]; exact (hivi i).2.1 }
  exact ⟨K, rfl, rfl, rfl, rfl, rfl⟩

/-- The same for a no-parity (S-layer) certificate: every combinatorial field of `NPCert`. -/
theorem exists_npCert {J : Type} [Fintype J] {expect : Nat} {c : CertD}
    (h : certOk expect true c = true) {r : Reg} (hr : r ∈ c.regions)
    (C : Cert J (Fin c.ivs.length))
    (ht1 : ∀ i, C.t1 i = ((c.ivs.get i).t1 : ℝ)) (ht2 : ∀ i, C.t2 i = ((c.ivs.get i).t2 : ℝ))
    (dual : C.DualNonneg) (condR : C.CondR (varBoxes c.vars))
    (condCnp : ∀ x, (r.x0 : ℝ) ≤ x → x ≤ r.x1 →
      0 < C.Phi x 0 2 - C.K - 2 * C.yc + C.W - 2 * C.wsumCl x) :
    ∃ P : NPCert J (Fin c.ivs.length), P.C = C ∧ P.s0 = r.x0 ∧ P.s1 = r.x1 := by
  obtain ⟨-, hreg, hiv, -, -, hmod⟩ := certOk_spec h
  obtain ⟨bs, hbs, hcov⟩ := modelOk_spec (hmod rfl)
  obtain ⟨hx0, -, hx1, -, -⟩ := hreg r hr
  have hivi : ∀ i : Fin c.ivs.length, (c.wlo : ℝ) ≤ (c.ivs.get i).t1 ∧
      ((c.ivs.get i).t1 : ℝ) < (c.ivs.get i).t2 ∧ ((c.ivs.get i).t2 : ℝ) ≤ c.whi :=
    fun i => hiv _ (List.get_mem _ _)
  let P : NPCert J (Fin c.ivs.length) :=
    { C := C, wlo := c.wlo, whi := c.whi, s0 := r.x0, s1 := r.x1, bins := binSet bs,
      dual := dual, bins_cover := hcov, condR := condR_allOpen C hbs condR, condCnp := condCnp,
      s0_ge := hx0, s1_le := hx1,
      iv_lo := fun i => by rw [ht1]; exact (hivi i).1,
      iv_hi := fun i => by rw [ht2]; exact (hivi i).2.2,
      iv_lt := fun i => by rw [ht1, ht2]; exact (hivi i).2.1 }
  exact ⟨P, rfl, rfl, rfl⟩

/-! ### 6. targets: exact tiling ⇒ pointwise 2-D cover, including the d = 0 line -/

theorem targetOk_spec {tlo thi : Rat} {gs : List String} {cs : List CertD}
    (h : targetOk tlo thi gs cs = true) :
    ∀ x d : ℝ, (tlo : ℝ) ≤ x → x ≤ thi → 0 ≤ d → d ≤ 1 / 2 →
      ∃ c ∈ cs, c.passed = true ∧ c.np = false ∧ c.group ∈ gs ∧
        ∃ r ∈ c.regions, (r.x0 : ℝ) ≤ x ∧ x ≤ r.x1 ∧ (r.d0 : ℝ) ≤ d ∧ d ≤ r.d1 := by
  intro x d h1 h2 hd0 hd1
  obtain ⟨p, hp, hp1, hp2⟩ := coversB_spec h x h1 h2
  unfold certRegions at hp
  simp only [List.mem_flatMap, List.mem_filter, List.mem_map, Bool.and_eq_true,
    Bool.not_eq_true', decide_eq_true_eq, List.contains_iff_mem] at hp
  obtain ⟨c, ⟨hc, ⟨hpass, hnp⟩, hg⟩, r, ⟨hr, hrd0, hrd1⟩, rfl⟩ := hp
  refine ⟨c, hc, hpass, hnp, hg, r, hr, hp1, hp2, ?_, ?_⟩
  · have : (r.d0 : ℝ) ≤ 0 := by exact_mod_cast hrd0
    linarith
  · have : ((1 / 2 : Rat) : ℝ) ≤ r.d1 := by exact_mod_cast hrd1
    have e : ((1 / 2 : Rat) : ℝ) = 1 / 2 := by push_cast; ring
    linarith

/-- the d = 0 slice (the 1-D cover used by `window_claim_A` / `closed_of_cover`) -/
theorem targetOk_line {tlo thi : Rat} {gs : List String} {cs : List CertD}
    (h : targetOk tlo thi gs cs = true) :
    ∀ x : ℝ, (tlo : ℝ) ≤ x → x ≤ thi →
      ∃ c ∈ cs, c.passed = true ∧ c.np = false ∧ c.group ∈ gs ∧
        ∃ r ∈ c.regions, (r.x0 : ℝ) ≤ x ∧ x ≤ r.x1 := by
  intro x h1 h2
  obtain ⟨c, hc, hp, hn, hg, r, hr, hx1, hx2, -⟩ := targetOk_spec h x 0 h1 h2 le_rfl (by norm_num)
  exact ⟨c, hc, hp, hn, hg, r, hr, hx1, hx2⟩

/-- **Assembly from the files.** If the target check passes and every region of every passed main
certificate of the groups is closed (each by `v4_closed` / `claimB`, from `exists_v4Cert` plus the
Arb and analytic hypotheses), then every zero with height in the target is on the line and simple. -/
theorem closed_of_targetOk (Zd : ZeroData) {tlo thi : Rat} {gs : List String} {cs : List CertD}
    (h : targetOk tlo thi gs cs = true)
    (hreg : ∀ c ∈ cs, c.passed = true → c.np = false → c.group ∈ gs →
      ∀ r ∈ c.regions, Zd.Closed r.x0 r.x1) :
    Zd.Closed tlo thi := by
  intro ρ hc h0 h1
  obtain ⟨c, hcs, hp, hn, hg, r, hr, hx1, hx2⟩ := targetOk_line h ρ.im h0 h1
  exact hreg c hcs hp hn hg r hr ρ hc hx1 hx2

/-! ### 7. claim (B): S-layer coverage -/

lemma rmax_le {a b : Rat} {x : ℝ} (h : ((rmax a b : Rat) : ℝ) ≤ x) : (a : ℝ) ≤ x ∧ (b : ℝ) ≤ x := by
  unfold rmax at h
  split_ifs at h with hab
  · have : (a : ℝ) ≤ b := by exact_mod_cast hab
    exact ⟨by linarith, h⟩
  · have : (b : ℝ) < a := by exact_mod_cast (not_le.1 hab)
    exact ⟨h, by linarith⟩

lemma le_rmin {a b : Rat} {x : ℝ} (ha : x ≤ (a : ℝ)) (hb : x ≤ (b : ℝ)) : x ≤ ((rmin a b : Rat) : ℝ) := by
  unfold rmin; split_ifs <;> assumption

lemma le_rmax {a b : Rat} {x : ℝ} (ha : (a : ℝ) ≤ x) (hb : (b : ℝ) ≤ x) : ((rmax a b : Rat) : ℝ) ≤ x := by
  unfold rmax; split_ifs <;> assumption

/-- **Claim (B) coverage from the files** (the hypothesis `hcov` of `claimB` / `V4ValidB`, with the
covering regions those of passed no-parity certificates of the same run). -/
theorem claimBOk_spec {g : String} {cs : List CertD} (h : claimBOk g cs = true) :
    ∀ c ∈ cs, c.passed = true → c.np = false → c.group = g → ∀ r ∈ c.regions, ∀ i ∈ c.ivs,
      ∀ x : ℝ, (i.t1 : ℝ) ≤ x → x ≤ i.t2 → (r.x0 : ℝ) ≤ x → x ≤ r.x1 →
        ∃ c' ∈ cs, c'.passed = true ∧ c'.np = true ∧ c'.group = g ∧
          ∃ r' ∈ c'.regions, (r'.x0 : ℝ) ≤ x ∧ x ≤ r'.x1 := by
  intro c hc hp hn hg r hr i hi x h1 h2 h3 h4
  unfold claimBOk at h
  simp only [List.all_eq_true, List.mem_filter, Bool.and_eq_true, Bool.not_eq_true',
    beq_iff_eq] at h
  have hci := h c ⟨hc, ⟨hp, hn⟩, hg⟩ r hr i hi
  have hA : i.t1 ≤ r.x1 := by exact_mod_cast (le_trans h1 h4)
  have hB : r.x0 ≤ i.t2 := by exact_mod_cast (le_trans h3 h2)
  rw [ite_eq_left_of_eq_true _ _ (eq_true (by simp only [decide_eq_true_eq]; exact ⟨hA, hB⟩))] at hci
  obtain ⟨p, hp', hp1, hp2⟩ := coversB_spec hci x (le_rmax h1 h3) (le_rmin h2 h4)
  unfold npSegs at hp'
  simp only [List.mem_flatMap, List.mem_filter, List.mem_map, Bool.and_eq_true,
    beq_iff_eq] at hp'
  obtain ⟨c', ⟨hc', ⟨hp'', hn'⟩, hg'⟩, r', hr', rfl⟩ := hp'
  exact ⟨c', hc', hp'', hn', hg', r', hr', hp1, hp2⟩

end AtlasAudit
