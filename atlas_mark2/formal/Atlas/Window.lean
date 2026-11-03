/-
Atlas — one v4 certificate, stated about the zeros (atlas_v4 §1, §3, §5, §6, §10).

Hypotheses are split into
* verifier-checked facts about the certificate (fields of `V4Cert` / `NPCert`): y, w ≥ 0, (R) on the
  all-open model, (C) on the region, region and intervals inside the window, t1 < t2, bins cover the
  window;
* Arb-checked facts about Z: `Z t1 * Z t2 < 0` for each interval (a hypothesis `hZ`);
* inherited analytic inputs: (H_rows) `ZRows`, (H_count) `ZCount`, and Lemma 1's premise
  (`Lemma1Parity` or `Lemma1Weak`) — hypotheses.
-/
import Atlas.Certificate
import Atlas.Zeros

noncomputable section

open Finset Set
open scoped Classical

namespace Atlas

/-- A main v4 certificate whose region is [x0, x1] × [0, 1/2], with all verifier-checked facts. -/
structure V4Cert (J ι : Type) [Fintype J] [Fintype ι] where
  C : Cert J ι
  wlo : ℝ
  whi : ℝ
  x0 : ℝ
  x1 : ℝ
  bins : Set (ℝ × ℝ)
  dual : C.DualNonneg
  bins_cover : ∀ x, wlo ≤ x → x ≤ whi → ∃ p ∈ bins, p.1 ≤ x ∧ x ≤ p.2
  condR : C.CondR (ZeroData.allOpen bins)
  condC : ∀ x d, x0 ≤ x → x ≤ x1 → 0 ≤ d → d ≤ 1 / 2 → 0 < C.Phi x d 2 - C.K - 2 * C.yc + C.W
  x0_ge : wlo ≤ x0
  x1_le : x1 ≤ whi
  iv_lo : ∀ i, wlo ≤ C.t1 i
  iv_hi : ∀ i, C.t2 i ≤ whi
  iv_lt : ∀ i, C.t1 i < C.t2 i

/-- A per-zero certificate checked by the NO-PARITY verifier (atlas_v4 §10 (ii)); region
[s0, s1] × {0}. -/
structure NPCert (J ι : Type) [Fintype J] [Fintype ι] where
  C : Cert J ι
  wlo : ℝ
  whi : ℝ
  s0 : ℝ
  s1 : ℝ
  bins : Set (ℝ × ℝ)
  dual : C.DualNonneg
  bins_cover : ∀ x, wlo ≤ x → x ≤ whi → ∃ p ∈ bins, p.1 ≤ x ∧ x ≤ p.2
  condR : C.CondR (ZeroData.allOpen bins)
  condCnp : ∀ x, s0 ≤ x → x ≤ s1 → 0 < C.Phi x 0 2 - C.K - 2 * C.yc + C.W - 2 * C.wsumCl x
  s0_ge : wlo ≤ s0
  s1_le : s1 ≤ whi
  iv_lo : ∀ i, wlo ≤ C.t1 i
  iv_hi : ∀ i, C.t2 i ≤ whi
  iv_lt : ∀ i, C.t1 i < C.t2 i

namespace ZeroData

variable (Zd : ZeroData) {J ι : Type} [Fintype J] [Fintype ι]

lemma mem_win_of {a b x0 x1 : ℝ} {ρ : ℂ} (hc : ρ ∈ Zd.carrier) (h0 : x0 ≤ ρ.im) (h1 : ρ.im ≤ x1)
    (ha : a ≤ x0) (hb : x1 ≤ b) : ρ ∈ Zd.win a b :=
  (Zd.mem_win).2 ⟨hc, by linarith, by linarith⟩

/-- n_i ≥ 1 for the canonical atoms, from Lemma 1 (weak) and the Arb sign facts. -/
lemma n_ge_one (C : Cert J ι) {a b : ℝ} {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (hZ : ∀ i, Z (C.t1 i) * Z (C.t2 i) < 0) (hlt : ∀ i, C.t1 i < C.t2 i)
    (hlo : ∀ i, a ≤ C.t1 i) (hhi : ∀ i, C.t2 i ≤ b) (i : ι) : 1 ≤ C.n i (Zd.atoms a b) := by
  rw [Zd.n_atoms C i (hlo i) (hhi i)]
  exact_mod_cast hL _ _ (hlt i) (hZ i)

/-- **L2 at the zero level (THEORY_ZSIGN Theorem for a v4 certificate).** No zero with height in
[x0, x1] is off the line. Uses only the WEAK Lemma 1 (n_i ≥ 1). -/
theorem v4_onLine (K : V4Cert J ι) {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (hZ : ∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0)
    (hRows : Zd.ZRows K.C K.wlo K.whi) (hCount : Zd.ZCount K.C K.wlo K.whi) :
    Zd.OnLine K.x0 K.x1 := by
  intro ρ hc h0 h1
  by_contra hre
  have hw := Zd.mem_win_of hc h0 h1 K.x0_ge K.x1_le
  obtain ⟨A', hA, hsub⟩ := Zd.atoms_split_offline hw hre
  have hM : HModel (allOpen K.bins) A' := fun t ht =>
    Zd.hmodel_atoms K.bins_cover t (hsub t ht)
  have hdpos : 0 < disp ρ := by
    unfold disp; exact abs_pos.2 (sub_ne_zero.2 hre)
  have hR := Zd.hrows_atoms K.C hRows
  have hN := Zd.hcount_atoms K.C hCount
  have hn := Zd.n_ge_one K.C hL hZ K.iv_lt K.iv_lo K.iv_hi
  rw [hA] at hR hN hn
  exact K.C.certificate K.dual _ K.x0 K.x1 0 (1 / 2) K.condR
    (fun x d hx0 hx1 hd0 hd1 _ => K.condC x d hx0 hx1 hd0 hd1)
    ⟨ρ.im, disp ρ, 2⟩ A' rfl hdpos h0 h1 hdpos.le (Zd.disp_lt_half hc).le hM hR hN hn

/-- The merged representation: a multiple on-line zero at x gives atoms (x,0,2) ::ₘ A' with all the
hypotheses of the atom-level lemmas transferred from the canonical atoms. -/
lemma merged_facts (C : Cert J ι) {a b : ℝ} {ρ : ℂ} (hw : ρ ∈ Zd.win a b) (hre : ρ.re = 1 / 2)
    (hm : 2 ≤ Zd.mult ρ) (bins : Set (ℝ × ℝ))
    (hcov : ∀ x, a ≤ x → x ≤ b → ∃ p ∈ bins, p.1 ≤ x ∧ x ≤ p.2)
    (hRows : Zd.ZRows C a b) (hCount : Zd.ZCount C a b) :
    ∃ A', HModel (allOpen bins) A' ∧ C.HRows (⟨ρ.im, 0, 2⟩ ::ₘ A') ∧
      C.HCount (⟨ρ.im, 0, 2⟩ ::ₘ A') ∧
      (∀ i, C.n i (⟨ρ.im, 0, 2⟩ ::ₘ A') = C.n i (Zd.atoms a b)) := by
  obtain ⟨A', hA, hsub⟩ := Zd.atoms_split_multiple hw hre hm
  refine ⟨A', fun t ht => Zd.hmodel_atoms hcov t (hsub t ht), ?_, ?_, ?_⟩
  · intro j
    have h := Zd.hrows_atoms C hRows j
    unfold Cert.S at h ⊢
    rw [merge_sum, ← hA]; exact h
  · have h := Zd.hcount_atoms C hCount
    unfold Cert.HCount Ncnt at h ⊢
    have e := merge_sum ρ.im A' (fun _ _ => 1)
    simp only [mul_one] at e
    rw [e, ← hA]; exact h
  · intro i; unfold Cert.n; rw [merge_sum, ← hA]

/-- **L3 at the zero level (atlas_v3 Lemma 2 for a v4 certificate).** No on-line zero with height
in [x0, x1] is multiple. Uses the PARITY form of Lemma 1. -/
theorem v4_simple (K : V4Cert J ι) {Z : ℝ → ℝ} (hL : Zd.Lemma1Parity Z)
    (hZ : ∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0)
    (hRows : Zd.ZRows K.C K.wlo K.whi) (hCount : Zd.ZCount K.C K.wlo K.whi)
    (ρ : ℂ) (hc : ρ ∈ Zd.carrier) (h0 : K.x0 ≤ ρ.im) (h1 : ρ.im ≤ K.x1) (hre : ρ.re = 1 / 2) :
    Zd.mult ρ = 1 := by
  have hm1 := Zd.one_le_mult ρ hc
  by_contra hne
  have hm : 2 ≤ Zd.mult ρ := by omega
  have hw := Zd.mem_win_of hc h0 h1 K.x0_ge K.x1_le
  obtain ⟨A', hM, hR, hN, hnEq⟩ := Zd.merged_facts K.C hw hre hm K.bins K.bins_cover hRows hCount
  have hodd : ∀ i, Odd (K.C.nNat i (⟨ρ.im, 0, 2⟩ ::ₘ A')) := by
    intro i
    have e1 := hnEq i
    rw [Cert.n_eq_nNat, Zd.n_atoms K.C i (K.iv_lo i) (K.iv_hi i)] at e1
    have e2 : K.C.nNat i (⟨ρ.im, 0, 2⟩ ::ₘ A') = Zd.onLine (K.C.t1 i) (K.C.t2 i) := by
      exact_mod_cast e1
    rw [e2]; exact hL _ _ (K.iv_lt i) (hZ i)
  exact K.C.lemma2_parity K.dual _ K.condR ρ.im
    (K.condC ρ.im 0 h0 h1 le_rfl (by norm_num)) A' hM hR hN hodd

/-- **Claim (A) of one v4 certificate (atlas_v4 §6):** every zero with height in [x0, x1] is on
the line and simple. -/
theorem v4_closed (K : V4Cert J ι) {Z : ℝ → ℝ} (hL : Zd.Lemma1Parity Z)
    (hZ : ∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0)
    (hRows : Zd.ZRows K.C K.wlo K.whi) (hCount : Zd.ZCount K.C K.wlo K.whi) :
    Zd.Closed K.x0 K.x1 := by
  intro ρ hc h0 h1
  have hon := Zd.v4_onLine K (Lemma1Weak.of_parity Zd hL) hZ hRows hCount ρ hc h0 h1
  exact ⟨hon, Zd.v4_simple K hL hZ hRows hCount ρ hc h0 h1 hon⟩

/-! ### L4 at the zero level: the S-layer (atlas_v4 §10) -/

/-- §10 (i): a main certificate is parity-free away from its intervals. -/
theorem v4_simple_away (K : V4Cert J ι) {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (hZ : ∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0)
    (hRows : Zd.ZRows K.C K.wlo K.whi) (hCount : Zd.ZCount K.C K.wlo K.whi)
    (ρ : ℂ) (hc : ρ ∈ Zd.carrier) (h0 : K.x0 ≤ ρ.im) (h1 : ρ.im ≤ K.x1) (hre : ρ.re = 1 / 2)
    (hout : ∀ i, ρ.im ∉ Ioo (K.C.t1 i) (K.C.t2 i)) : Zd.mult ρ = 1 := by
  have hm1 := Zd.one_le_mult ρ hc
  by_contra hne
  have hm : 2 ≤ Zd.mult ρ := by omega
  have hw := Zd.mem_win_of hc h0 h1 K.x0_ge K.x1_le
  obtain ⟨A', hM, hR, hN, hnEq⟩ := Zd.merged_facts K.C hw hre hm K.bins K.bins_cover hRows hCount
  have hn : ∀ i, 1 ≤ K.C.n i (⟨ρ.im, 0, 2⟩ ::ₘ A') := fun i => by
    rw [hnEq i]; exact Zd.n_ge_one K.C hL hZ K.iv_lt K.iv_lo K.iv_hi i
  exact K.C.slayer_away K.dual _ K.condR ρ.im (K.condC ρ.im 0 h0 h1 le_rfl (by norm_num))
    hout A' hM hR hN hn

/-- §10 (ii): a per-zero certificate passed by the no-parity verifier excludes a multiple on-line
zero in [s0, s1]. Weak Lemma 1 only. -/
theorem np_simple (P : NPCert J ι) {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (hZ : ∀ i, Z (P.C.t1 i) * Z (P.C.t2 i) < 0)
    (hRows : Zd.ZRows P.C P.wlo P.whi) (hCount : Zd.ZCount P.C P.wlo P.whi)
    (ρ : ℂ) (hc : ρ ∈ Zd.carrier) (h0 : P.s0 ≤ ρ.im) (h1 : ρ.im ≤ P.s1) (hre : ρ.re = 1 / 2) :
    Zd.mult ρ = 1 := by
  have hm1 := Zd.one_le_mult ρ hc
  by_contra hne
  have hm : 2 ≤ Zd.mult ρ := by omega
  have hw := Zd.mem_win_of hc h0 h1 P.s0_ge P.s1_le
  obtain ⟨A', hM, hR, hN, hnEq⟩ := Zd.merged_facts P.C hw hre hm P.bins P.bins_cover hRows hCount
  have hn : ∀ i, 1 ≤ P.C.n i (⟨ρ.im, 0, 2⟩ ::ₘ A') := fun i => by
    rw [hnEq i]; exact Zd.n_ge_one P.C hL hZ P.iv_lt P.iv_lo P.iv_hi i
  exact P.C.slayer_perzero P.dual _ P.condR ρ.im (P.condCnp ρ.im h0 h1) A' hM hR hN hn

/-- A per-zero certificate together with its Arb and inherited analytic hypotheses. -/
def NPValid (Z : ℝ → ℝ) (s0 s1 : ℝ) : Prop :=
  ∃ (J' ι' : Type) (_ : Fintype J') (_ : Fintype ι') (P : NPCert J' ι'),
    P.s0 = s0 ∧ P.s1 = s1 ∧ (∀ i, Z (P.C.t1 i) * Z (P.C.t2 i) < 0) ∧
    Zd.ZRows P.C P.wlo P.whi ∧ Zd.ZCount P.C P.wlo P.whi

/-- **§10 (iii), claim (B) for one main certificate.** If, for every interval I of the main
certificate, cl(I) ∩ [x0, x1] is covered by regions of per-zero no-parity certificates, then every
zero with height in [x0, x1] is on the line and simple — using only the WEAK Lemma 1 (no parity). -/
theorem claimB (K : V4Cert J ι) {Z : ℝ → ℝ} (hL : Zd.Lemma1Weak Z)
    (hZ : ∀ i, Z (K.C.t1 i) * Z (K.C.t2 i) < 0)
    (hRows : Zd.ZRows K.C K.wlo K.whi) (hCount : Zd.ZCount K.C K.wlo K.whi)
    (hcov : ∀ i x, x ∈ Icc (K.C.t1 i) (K.C.t2 i) → K.x0 ≤ x → x ≤ K.x1 →
      ∃ s0 s1, s0 ≤ x ∧ x ≤ s1 ∧ Zd.NPValid Z s0 s1) :
    Zd.Closed K.x0 K.x1 := by
  intro ρ hc h0 h1
  have hon := Zd.v4_onLine K hL hZ hRows hCount ρ hc h0 h1
  refine ⟨hon, ?_⟩
  by_cases hin : ∃ i, ρ.im ∈ Ioo (K.C.t1 i) (K.C.t2 i)
  · obtain ⟨i, hi⟩ := hin
    obtain ⟨s0, s1, hs0, hs1, J', ι', _, _, P, rfl, rfl, hZP, hRP, hCP⟩ :=
      hcov i ρ.im (Ioo_subset_Icc_self hi) h0 h1
    exact Zd.np_simple P hL hZP hRP hCP ρ hc hs0 hs1 hon
  · push Not at hin
    exact Zd.v4_simple_away K hL hZ hRows hCount ρ hc h0 h1 hon hin

end ZeroData

end Atlas
