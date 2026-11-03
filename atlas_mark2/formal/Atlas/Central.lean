/-
Atlas — the central-mass reduction used for 389.a (new_territory/ec389a/THEORY_389A.md §3).

A proven central zero ρ0 = 1/2 of multiplicity ≥ m0 is removed from the zero configuration: Z′ has the
multiplicity at ρ0 lowered by m0. We prove
* `reduce`: Z′ is again a `ZeroData` (ρ0 is its own mirror);
* `reduce_sum`: every window sum drops by exactly m0 · g(ρ0) when the window contains ordinate 0, so the
  replay's shifted enclosures (hi − m0 U(0,0), lo − m0 U(0,0)) are (H_rows) for Z′, and N_win − m0 is
  (H_count) for Z′ (`reduce_rows`, `reduce_count`: "the count bound is reduced by m0");
* `reduce_onLine`: if no sign-change interval meets 0, Lemma 1's on-line counts are unchanged;
* `v4_closed_of_odd`: the existing certificate theorems (`v4_onLine` + `v4_simple`), restated with the
  parity of the certificate's own intervals as hypothesis (that is all they use);
* `central_reduction`: hence the certificate theorem's conclusion holds for every zero other than ρ0, and
  ρ0 has multiplicity ≤ m0 + 1 if 0 is in the region (THEORY_389A §3 "Conclusion");
* `x1_exact`: with evenness (ε = +1) and m0 even, multiplicity = m0 (cross-check X1);
* `central_reduction_of_file`: the same from a checked certificate FILE (central policy from the audit).
-/
import Atlas.Degree2

noncomputable section

open Finset Set
open scoped Classical

namespace Atlas

/-- the centre ρ0 = 1/2 (analytic normalization) -/
abbrev centre : ℂ := 1 / 2

@[simp] lemma centre_re : centre.re = 1 / 2 := by simp [centre]
@[simp] lemma centre_im : centre.im = 0 := by simp [centre]

lemma reflect_centre : reflect centre = centre := by
  apply Complex.ext <;> simp [centre]; norm_num

lemma disp_centre : disp centre = 0 := by simp [disp]

namespace ZeroData

variable (Zd : ZeroData)

/-- **The reduced configuration Z′**: the multiplicity at ρ0 = 1/2 lowered by m0 (removed if it reaches 0). -/
def reduce (m0 : ℕ) : ZeroData where
  carrier := {ρ | ρ ∈ Zd.carrier ∧ (ρ ≠ centre ∨ m0 < Zd.mult ρ)}
  mult := fun ρ => if ρ = centre then Zd.mult ρ - m0 else Zd.mult ρ
  one_le_mult := by
    rintro ρ ⟨hc, h⟩
    by_cases hρ : ρ = centre
    · rw [ite_eq_left hρ]
      rcases h with h | h
      · exact absurd hρ h
      · omega
    · rw [ite_eq_right hρ]; exact Zd.one_le_mult ρ hc
  strip := fun ρ h => Zd.strip ρ h.1
  reflect_mem := by
    rintro ρ ⟨hc, h⟩
    refine ⟨Zd.reflect_mem ρ hc, ?_⟩
    by_cases hρ : ρ = centre
    · subst hρ; rw [reflect_centre]; exact h
    · left; intro he; apply hρ; rw [← reflect_reflect ρ, he, reflect_centre]
  mult_reflect := by
    rintro ρ ⟨hc, -⟩
    by_cases hρ : ρ = centre
    · subst hρ; rw [reflect_centre]
    · have hr : reflect ρ ≠ centre := by
        intro he; apply hρ; rw [← reflect_reflect ρ, he, reflect_centre]
      simp only [ite_eq_right hρ, ite_eq_right hr]; exact Zd.mult_reflect ρ hc
  finite_window := fun a b => (Zd.finite_window a b).subset (fun ρ h => ⟨h.1.1, h.2⟩)

lemma reduce_mult (m0 : ℕ) (ρ : ℂ) :
    (Zd.reduce m0).mult ρ = if ρ = centre then Zd.mult ρ - m0 else Zd.mult ρ := rfl

lemma mem_reduce (m0 : ℕ) (ρ : ℂ) :
    ρ ∈ (Zd.reduce m0).carrier ↔ ρ ∈ Zd.carrier ∧ (ρ ≠ centre ∨ m0 < Zd.mult ρ) := Iff.rfl

/-- **Window sums of Z′.** If ρ0 is a zero of multiplicity ≥ m0 and the window contains ordinate 0, every
multiplicity-weighted window sum drops by exactly m0 · g(ρ0). -/
theorem reduce_sum {m0 : ℕ} (h0 : centre ∈ Zd.carrier) (hm : m0 ≤ Zd.mult centre) {a b : ℝ}
    (ha : a ≤ 0) (hb : 0 ≤ b) (g : ℂ → ℝ) :
    ∑ ρ ∈ (Zd.reduce m0).win a b, ((Zd.reduce m0).mult ρ : ℝ) * g ρ =
      ∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ) * g ρ - m0 * g centre := by
  have hsub : (Zd.reduce m0).win a b ⊆ Zd.win a b := by
    intro ρ hρ
    rw [mem_win] at hρ ⊢
    exact ⟨hρ.1.1, hρ.2⟩
  rw [Finset.sum_subset hsub (fun ρ hρ hn => ?_)]
  · have hc : centre ∈ Zd.win a b := (Zd.mem_win).2 ⟨h0, by simp [ha], by simp [hb]⟩
    rw [← Finset.add_sum_erase _ _ hc, ← Finset.add_sum_erase _ _ hc, reduce_mult, ite_eq_left rfl]
    have hrest : ∑ ρ ∈ (Zd.win a b).erase centre, ((Zd.reduce m0).mult ρ : ℝ) * g ρ =
        ∑ ρ ∈ (Zd.win a b).erase centre, (Zd.mult ρ : ℝ) * g ρ := by
      apply Finset.sum_congr rfl
      intro ρ hρ
      rw [reduce_mult, ite_eq_right (Finset.ne_of_mem_erase hρ)]
    rw [hrest, Nat.cast_sub hm]; ring
  · -- ρ in the old window but not in the new one: ρ = ρ0 with multiplicity exactly m0
    have h1 := (Zd.mem_win).1 hρ
    have h2 : ρ ∉ (Zd.reduce m0).carrier := fun hh => hn ((Zd.reduce m0).mem_win.2 ⟨hh, h1.2⟩)
    rw [mem_reduce] at h2
    push Not at h2
    obtain ⟨hρc, hle⟩ := h2 h1.1
    rw [reduce_mult, ite_eq_left hρc]
    have : Zd.mult ρ - m0 = 0 := by omega
    rw [this]; simp

/-- (H_rows′): the enclosures shifted by m0 U_j(0,0) are (H_rows) for Z′. -/
theorem reduce_rows {J ι : Type*} [Fintype J] [Fintype ι] {m0 : ℕ} (h0 : centre ∈ Zd.carrier)
    (hm : m0 ≤ Zd.mult centre) (C : Cert J ι) {a b : ℝ} (ha : a ≤ 0) (hb : 0 ≤ b)
    (hRows : ∀ j, (∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ) * C.U j ρ.im (disp ρ)) ≤
        C.Ehi j + m0 * C.U j 0 0 + C.lorF j ∧
      C.Elo j + m0 * C.U j 0 0 - C.Fa j ≤ ∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ) * C.U j ρ.im (disp ρ)) :
    (Zd.reduce m0).ZRows C a b := by
  intro j
  have e := Zd.reduce_sum h0 hm ha hb (fun ρ => C.U j ρ.im (disp ρ))
  simp only [centre_im, disp_centre] at e
  rw [e]
  obtain ⟨h1, h2⟩ := hRows j
  constructor <;> linarith

/-- (H_count′): **the count bound is reduced by m0**: N(Z′, W) ≤ N_win − m0 when N(Z, W) ≤ N_win. -/
theorem reduce_count {J ι : Type*} [Fintype J] [Fintype ι] {m0 : ℕ} (h0 : centre ∈ Zd.carrier)
    (hm : m0 ≤ Zd.mult centre) (C : Cert J ι) {a b : ℝ} (ha : a ≤ 0) (hb : 0 ≤ b)
    (hCount : (∑ ρ ∈ Zd.win a b, (Zd.mult ρ : ℝ)) ≤ C.Nwin + m0) :
    (Zd.reduce m0).ZCount C a b := by
  have e := Zd.reduce_sum h0 hm ha hb (fun _ => 1)
  simp only [mul_one] at e
  unfold ZCount
  rw [e]; linarith

/-- **Lemma 1 on Z′**: an interval not meeting ordinate 0 has the same on-line multiplicity for Z and Z′. -/
theorem reduce_onLine (m0 : ℕ) {t1 t2 : ℝ} (h : t2 ≤ 0 ∨ 0 ≤ t1) :
    (Zd.reduce m0).onLine t1 t2 = Zd.onLine t1 t2 := by
  have hne : ∀ ρ : ℂ, t1 < ρ.im → ρ.im < t2 → ρ ≠ centre := by
    intro ρ h1 h2 he
    rw [he, centre_im] at h1 h2
    rcases h with h | h <;> linarith
  unfold onLine
  have hset : (((Zd.reduce m0).win t1 t2).filter fun ρ => ρ.re = 1 / 2 ∧ t1 < ρ.im ∧ ρ.im < t2) =
      ((Zd.win t1 t2).filter fun ρ => ρ.re = 1 / 2 ∧ t1 < ρ.im ∧ ρ.im < t2) := by
    ext ρ
    simp only [Finset.mem_filter, mem_win, mem_reduce]
    constructor
    · rintro ⟨⟨⟨hc, -⟩, h1, h2⟩, hp⟩; exact ⟨⟨hc, h1, h2⟩, hp⟩
    · rintro ⟨⟨hc, h1, h2⟩, hp⟩; exact ⟨⟨⟨hc, Or.inl (hne ρ hp.2.1 hp.2.2)⟩, h1, h2⟩, hp⟩
  rw [hset]
  apply Finset.sum_congr rfl
  intro ρ hρ
  simp only [Finset.mem_filter] at hρ
  rw [reduce_mult, ite_eq_right (hne ρ hρ.2.2.1 hρ.2.2.2)]

/-- **The certificate theorems with per-interval parity** (`v4_onLine` + `v4_simple` = `v4_closed`, whose
proofs use Lemma 1 only on the certificate's own intervals). -/
theorem v4_closed_of_odd {J ι : Type} [Fintype J] [Fintype ι] (K : V4Cert J ι)
    (hodd : ∀ i, Odd (Zd.onLine (K.C.t1 i) (K.C.t2 i)))
    (hRows : Zd.ZRows K.C K.wlo K.whi) (hCount : Zd.ZCount K.C K.wlo K.whi) :
    Zd.Closed K.x0 K.x1 := by
  intro ρ hc h0 h1
  have hon : ρ.re = 1 / 2 := by
    by_contra hre
    have hn : ∀ i, 1 ≤ K.C.n i (Zd.atoms K.wlo K.whi) := fun i => by
      rw [Zd.n_atoms K.C i (K.iv_lo i) (K.iv_hi i)]; exact_mod_cast (hodd i).pos
    have hw := Zd.mem_win_of hc h0 h1 K.x0_ge K.x1_le
    obtain ⟨A', hA, hsub⟩ := Zd.atoms_split_offline hw hre
    have hM : HModel (allOpen K.bins) A' := fun t ht => Zd.hmodel_atoms K.bins_cover t (hsub t ht)
    have hdpos : 0 < disp ρ := by unfold disp; exact abs_pos.2 (sub_ne_zero.2 hre)
    have hR := Zd.hrows_atoms K.C hRows
    have hN := Zd.hcount_atoms K.C hCount
    rw [hA] at hR hN hn
    exact K.C.certificate K.dual _ K.x0 K.x1 0 (1 / 2) K.condR
      (fun x d hx0 hx1 hd0 hd1 _ => K.condC x d hx0 hx1 hd0 hd1)
      ⟨ρ.im, disp ρ, 2⟩ A' rfl hdpos h0 h1 hdpos.le (Zd.disp_lt_half hc).le hM hR hN hn
  refine ⟨hon, ?_⟩
  have hm1 := Zd.one_le_mult ρ hc
  by_contra hne
  have hm : 2 ≤ Zd.mult ρ := by omega
  have hw := Zd.mem_win_of hc h0 h1 K.x0_ge K.x1_le
  obtain ⟨A', hM, hR, hN, hnEq⟩ := Zd.merged_facts K.C hw hon hm K.bins K.bins_cover hRows hCount
  have hodd' : ∀ i, Odd (K.C.nNat i (⟨ρ.im, 0, 2⟩ ::ₘ A')) := by
    intro i
    have e1 := hnEq i
    rw [Cert.n_eq_nNat, Zd.n_atoms K.C i (K.iv_lo i) (K.iv_hi i)] at e1
    have e2 : K.C.nNat i (⟨ρ.im, 0, 2⟩ ::ₘ A') = Zd.onLine (K.C.t1 i) (K.C.t2 i) := by
      exact_mod_cast e1
    rw [e2]; exact hodd i
  exact K.C.lemma2_parity K.dual _ K.condR ρ.im
    (K.condC ρ.im 0 h0 h1 le_rfl (by norm_num)) A' hM hR hN hodd'

/-- **Central-mass reduction (THEORY_389A §3).** `K` is a certificate whose data are the replay's REDUCED
inputs (hi′ = hi − m0 U(0,0), lo′ = lo − m0 U(0,0), N_win′ = N_win − m0), so the true zeros satisfy (H_rows)
and (H_count) with the original enclosures written as `Ehi + m0 U(0,0)`, `Elo + m0 U(0,0)`, `Nwin + m0`.
If ρ0 = 1/2 is a zero of multiplicity ≥ m0, the window contains ordinate 0 and no sign-change interval meets
0, then every zero other than ρ0 with ordinate in the region is on the line and simple, and ρ0 has
multiplicity ≤ m0 + 1 if 0 is in the region. Lemma 1 (parity) is used for the TRUE zeros only. -/
theorem central_reduction {J ι : Type} [Fintype J] [Fintype ι] (K : V4Cert J ι) (m0 : ℕ)
    (h0 : centre ∈ Zd.carrier) (hm : m0 ≤ Zd.mult centre) (hwin : K.wlo ≤ 0 ∧ 0 ≤ K.whi)
    (hnot0 : ∀ i, K.C.t2 i < 0 ∨ 0 < K.C.t1 i)
    {Z : ℝ → ℝ} (hL : Zd.Lemma1Parity Z) (hZ : ∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0)
    (hRows : ∀ j, (∑ ρ ∈ Zd.win K.wlo K.whi, (Zd.mult ρ : ℝ) * K.C.U j ρ.im (disp ρ)) ≤
        K.C.Ehi j + m0 * K.C.U j 0 0 + K.C.lorF j ∧
      K.C.Elo j + m0 * K.C.U j 0 0 - K.C.Fa j ≤
        ∑ ρ ∈ Zd.win K.wlo K.whi, (Zd.mult ρ : ℝ) * K.C.U j ρ.im (disp ρ))
    (hCount : (∑ ρ ∈ Zd.win K.wlo K.whi, (Zd.mult ρ : ℝ)) ≤ K.C.Nwin + m0) :
    (∀ ρ ∈ Zd.carrier, K.x0 ≤ ρ.im → ρ.im ≤ K.x1 → ρ ≠ centre → ρ.re = 1 / 2 ∧ Zd.mult ρ = 1) ∧
    (K.x0 ≤ 0 → 0 ≤ K.x1 → Zd.mult centre ≤ m0 + 1) := by
  have hR' := Zd.reduce_rows h0 hm K.C hwin.1 hwin.2 hRows
  have hN' := Zd.reduce_count h0 hm K.C hwin.1 hwin.2 hCount
  have hodd : ∀ i, Odd ((Zd.reduce m0).onLine (K.C.t1 i) (K.C.t2 i)) := by
    intro i
    have h' : K.C.t2 i ≤ 0 ∨ 0 ≤ K.C.t1 i := by
      rcases hnot0 i with h | h
      · exact Or.inl h.le
      · exact Or.inr h.le
    rw [Zd.reduce_onLine m0 h']
    exact hL _ _ (K.iv_lt i) (hZ i)
  have hcl := (Zd.reduce m0).v4_closed_of_odd K hodd hR' hN'
  constructor
  · intro ρ hc hx0 hx1 hne
    have hc' : ρ ∈ (Zd.reduce m0).carrier := ⟨hc, Or.inl hne⟩
    have := hcl ρ hc' hx0 hx1
    rw [reduce_mult, ite_eq_right hne] at this
    exact this
  · intro hx0 hx1
    by_contra hgt
    push Not at hgt
    have hc' : centre ∈ (Zd.reduce m0).carrier := ⟨h0, Or.inr (by omega)⟩
    have := (hcl centre hc' (by simpa using hx0) (by simpa using hx1)).2
    rw [reduce_mult, ite_eq_left rfl] at this
    omega

/-- **Cross-check X1**: m0 ≤ mult ≤ m0 + 1, mult even (ε = +1, `Degree2.central_mult_parity`) and m0 even
⇒ mult = m0. -/
theorem x1_exact {m0 n : ℕ} (hm : m0 ≤ n) (hle : n ≤ m0 + 1) (hn : Even n) (h0 : Even m0) : n = m0 := by
  obtain ⟨a, rfl⟩ := hn; obtain ⟨b, rfl⟩ := h0; omega

end ZeroData

/-- **The central reduction from a checked certificate file.** If the audit's `certOk 2 _ c` holds and the
reduction is used (c.m0 ≠ 0), the policy gives m0 = 2, window ∋ 0 and no interval meeting 0; with the Arb
facts (dual, (R) on W × [0, 1/2], (C) on the region, signs of Z) and the analytic inputs for the TRUE zeros
(ρ0 = 1/2 a zero of multiplicity ≥ 2, Lemma 1, (H_rows), (H_count) with the unreduced enclosures), the
conclusion of `central_reduction` holds for the region with m0 = 2. -/
theorem central_reduction_of_file (Zd : ZeroData) {J : Type} [Fintype J] {model : Bool}
    {c : AtlasAudit.CertD} (h : AtlasAudit.certOk 2 model c = true) (hused : c.m0 ≠ 0)
    {r : AtlasAudit.Reg} (hr : r ∈ c.regions) (C : Cert J (Fin c.ivs.length))
    (ht1 : ∀ i, C.t1 i = ((c.ivs.get i).t1 : ℝ)) (ht2 : ∀ i, C.t2 i = ((c.ivs.get i).t2 : ℝ))
    (dual : C.DualNonneg) (hR : C.CondR {⟨c.wlo, c.whi, 0, 1 / 2, 2⟩})
    (condC : ∀ x d, (r.x0 : ℝ) ≤ x → x ≤ r.x1 → 0 ≤ d → d ≤ 1 / 2 →
      0 < C.Phi x d 2 - C.K - 2 * C.yc + C.W)
    (h0 : centre ∈ Zd.carrier) (hm : 2 ≤ Zd.mult centre)
    {Z : ℝ → ℝ} (hL : Zd.Lemma1Parity Z) (hZ : ∀ i, Z (C.t1 i) * Z (C.t2 i) < 0)
    (hRows : ∀ j, (∑ ρ ∈ Zd.win c.wlo c.whi, (Zd.mult ρ : ℝ) * C.U j ρ.im (disp ρ)) ≤
        C.Ehi j + 2 * C.U j 0 0 + C.lorF j ∧
      C.Elo j + 2 * C.U j 0 0 - C.Fa j ≤
        ∑ ρ ∈ Zd.win c.wlo c.whi, (Zd.mult ρ : ℝ) * C.U j ρ.im (disp ρ))
    (hCount : (∑ ρ ∈ Zd.win c.wlo c.whi, (Zd.mult ρ : ℝ)) ≤ C.Nwin + 2) :
    c.m0 = 2 ∧
    (∀ ρ ∈ Zd.carrier, (r.x0 : ℝ) ≤ ρ.im → ρ.im ≤ r.x1 → ρ ≠ centre → ρ.re = 1 / 2 ∧ Zd.mult ρ = 1) ∧
    ((r.x0 : ℝ) ≤ 0 → 0 ≤ (r.x1 : ℝ) → Zd.mult centre ≤ 3) := by
  obtain ⟨-, -, -, -, hcen, -⟩ := AtlasAudit.certOk_spec h
  obtain ⟨-, hwin, hpol⟩ := AtlasAudit.centralOk_spec hcen
  obtain ⟨hlo, hhi, -⟩ := hwin.1 hused
  obtain ⟨hm2, hivs⟩ := hpol hused
  obtain ⟨K, hKC, hKlo, hKhi, hKx0, hKx1⟩ := Degree2.exists_v4Cert_deg2 h hr C ht1 ht2 dual hR condC
  subst hKC
  have hnot0 : ∀ i, K.C.t2 i < 0 ∨ 0 < K.C.t1 i := by
    intro i; rw [ht1, ht2]; exact hivs _ (List.get_mem _ _)
  have hwin' : K.wlo ≤ 0 ∧ 0 ≤ K.whi := by rw [hKlo, hKhi]; exact ⟨hlo.le, hhi.le⟩
  rw [← hKlo, ← hKhi] at hRows hCount
  have := Zd.central_reduction K 2 h0 hm hwin' hnot0 hL hZ (by exact_mod_cast hRows)
    (by exact_mod_cast hCount)
  rw [hKx0, hKx1] at this
  exact ⟨hm2, this.1, this.2⟩

end Atlas
