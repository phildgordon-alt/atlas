# Atlas certificate logic in Lean 4 + Mathlib

This project formalizes the **logic** of Atlas's certificates: the THEORY_ZSIGN Theorem, atlas_v3 Lemma 2,
the atlas_v4 all-open model, assembly and S-layer, the atlas_v4_1 counting closure, the atlas_v4_2 local-count closure, and (2026-10-08)
the degree-2 lemmas (Lemma Z for ε = ±1, central order parity, the 389.a central-mass reduction, Corollary 2 for degree 2) plus a
**Lean-checked audit of the certificate files** (`lake exe atlas_audit`; results in `audit/RESULTS.md`). The numerical side
(Arb enclosures, the LP, the argument-principle counter) is not formalized. Its outputs, and the classical
analytic facts the docs inherit, appear as **explicit hypotheses in theorem statements**. The project
declares no `axiom`, uses no `sorry`, and every theorem depends only on `propext`, `Classical.choice` and
`Quot.sound` (output below).

Sources (2026-10-08 additions): `diagnostic/new_territory/{deg2/THEORY_DEG2.md, ec37a/THEORY_37A.md, ec389a/THEORY_389A.md}` and the
RESULTS/README of each pipeline (certificate formats, targets). Sources: `diagnostic/zsign/THEORY_ZSIGN.md`, `diagnostic/atlas_v3/README.md` (Lemma 2),
`diagnostic/atlas_v4/THEORY_V4.md` (§1, §5, §6, §10), `diagnostic/atlas_v4_1/THEORY_V4_1.md` (§2, §6),
`diagnostic/atlas_v4_2/THEORY_V4_2.md` (§1, §2; = `diagnostic/local_count/LOCAL_COUNT.md` Theorem 1, Corollary 2).
Nothing under `diagnostic/` was modified.

Conventions follow `anthropics/formal-math/zeta23` (read only, nothing vendored). The zeros are an abstract,
ζ-free structure: a set of distinct zeros plus a multiplicity function, closed under ρ ↦ 1 − ρ̄ with equal
multiplicity, and locally finite in the ordinate. This is `Zeta23.ZeroConfig` with the **strict** strip
0 < Re ρ < 1, which atlas_v4 §1 uses. Sylvester/Weil-form infrastructure is not needed: the Atlas logic is
linear and combinatorial.

## Files

| file | content |
|---|---|
| `Atlas/Basic.lean` | atoms (x, d, f), var boxes, (H_model), certificate data `Cert` (rows, intervals, duals), Φ, χ_i, Φ_w, K, Σw, (H_rows), (H_count), (R), the verifier's closed-interval (R), steps (i)–(v) of the Theorem as lemmas |
| `Atlas/Certificate.lean` | L1, L2, L3, L4 at the atom level |
| `Atlas/Zeros.lean` | `ZeroData`, Lemma 1's premise (parity and weak forms), canonical window atoms, the all-open model, and the transfer zero sums ↔ atom sums |
| `Atlas/Window.lean` | `V4Cert`, `NPCert`, and L2, L3, L4 stated about the zeros |
| `Atlas/Counting.lean` | L5: Lemma A and Lemma B |
| `Atlas/Assembly.lean` | L6: claims (A) and (B) for a hull |
| `Atlas/LocalCount.lean` | L7: Theorem 1's summation step and Corollary 2 (local-count closure, atlas_v4_2) |
| `AtlasAudit/Check.lean` | L8: the executable file checks (core Lean only, no Mathlib, so the executable links without compiling Mathlib) |
| `AtlasAudit/Main.lean` | `lake exe atlas_audit FILE…`: parser + report (trusted, not proved) |
| `Atlas/Audit.lean` | L8: correctness of every check (check = true ⇒ statement over ℝ), file → `V4Cert` / `NPCert`, coverage ⇒ window claim, claim (B) coverage |
| `Atlas/Degree2.lean` | L9: Lemma Z (ε = ±1), central order parity, Lemma 1 from Lemma Z, Corollary 2 / Lemma B for degree 2, degree-2 model ⇒ `V4Cert` |
| `Atlas/Central.lean` | L10: the central-mass reduction (389.a) and its connection to the certificate theorems |
| `export/export_certs.py` | exact exporter (binary64 → exact rational, no rounding) of every certificate file to `audit/data/*.txt` |
| `audit/` | `RESULTS.md` (audit summary and findings), `audit_output.txt`, `export_output.txt`, `mutation_test.py` + `mutation_output.txt`, `SHA256SUMS` |
| `scripts/PrintAxioms.lean`, `scripts/PrintAxioms.out` | `#print axioms` audit |

About 2,750 lines of Lean (1,326 new on 2026-10-08).

## What is a hypothesis, what is proved

**Hypotheses (never axioms).** Each appears as an argument of the theorems that use it.

* **Zero model `ZeroData`.** These are classical facts about the nontrivial zeros of ξ:
  * multiplicity ≥ 1;
  * 0 < Re ρ < 1;
  * closure under ρ ↦ 1 − ρ̄ with equal multiplicity;
  * finitely many zeros per closed height window.
* **Lemma 1's analytic premise.**
  * `Lemma1Parity Z`: t1 < t2 and Z(t1)·Z(t2) < 0 ⇒ the on-line zeros with height in (t1, t2) have **odd** total multiplicity.
  * `Lemma1Weak Z`: the same premise gives total multiplicity ≥ 1. It is proved from the parity form (`Lemma1Weak.of_parity`).
* **Arb facts.** `Z (t1 i) * Z (t2 i) < 0` for each interval of each certificate.
* **Inherited analytic inputs.**
  * (H_rows) as `ZRows C wlo whi`: Σ_ρ m_ρ U_j(Im ρ, |Re ρ − 1/2|) is ≤ Ehi_j + [L]Fa_j and ≥ Elo_j − Fa_j. The sum runs over the zeros with height in the window.
  * (H_count) as `ZCount`: Σ_ρ m_ρ ≤ Nwin.
* **Local-count bound (v4_2).** N(J) ≤ B (Theorem 1's output; `theorem1_count` derives it from row sums ≤ Ehi_j
  and the majorant condition G ≥ 1 on J × [0, 1/2)), and the closure test B < k + 2 (⇔ ⌊B⌋ ≤ k + 1).
* **Counter output (v4_1).** `boxCount σ0 σ1 t0 t1 = N` (or ≤ 1) is the number of zeros in the closed box, with multiplicity.
* **Verifier-checked facts.** These are the fields of `V4Cert` / `NPCert`:
  * y, w ≥ 0;
  * (R) on the all-open model;
  * (C) on [x0, x1] × [0, 1/2], or the no-parity (C') on [s0, s1] × {0};
  * region ⊂ window, every interval ⊂ window, t1 < t2;
  * the bins cover the window.

* **(2026-10-08) Degree-2 analytic inputs** (`Atlas/Degree2.lean`, `Atlas/Central.lean`).
  * `Degree2.FE Λ c ε`: Λ(2c − s) = ε Λ(s) and Λ(s̄) = conj Λ(s) (modularity + real coefficients).
  * E(t) > 0, standing for e^{πt/2}.
  * `TaylorAt0 Rep`: uniqueness of Taylor coefficients at 0, and how z ↦ −z and scalar multiplication act on them.
  * The identification of the central multiplicity with the Taylor order: `a (mult ρ0) ≠ 0`.
  * `SignParity Z ord`: a real function changing sign on (t1, t2) has zeros of odd total order there.
  * `hzero` / `hord`: Z vanishes exactly at the on-line zeros, with order = multiplicity. `hzero` is DERIVED from Lemma Z (b)
    when the carrier is the zero set of Λ_an in the strip. `hord` is the continuity half of Lemma Z (b).
  * For 389.a: ρ0 = 1/2 is a zero with multiplicity ≥ m0 (Lemma M + evenness), and the TRUE zeros satisfy (H_rows) and
    (H_count) with the unreduced enclosures.
* **(2026-10-08) File audit.** The exporter, the parser and the replay verdicts (`passed`) are trusted. Each check is proved to
  imply its real-number statement.

**Proved.** Everything else: the algebra of the Theorem, the exchange of sums, the parity step, the all-open
(H_model), the transfer between atoms and zeros (including the mirror bijection and re-representing a multiple
zero as an f = 2 atom), the S-layer, Lemmas A and B, and the assembly.

## Map: Lean theorem ↔ doc statement

| # | doc statement | Lean | notes |
|---|---|---|---|
| L1 | THEORY_ZSIGN §2 (iii), §3 "overlapping / duplicate intervals": Σ_a f_a Σ_i w_i χ_i(a) = Σ_i w_i n_i ≥ Σ_i w_i | `Cert.signChange_credit`, `Cert.W_le_sum_wn`, `Cert.sum_fwsum` | any family of intervals, overlaps and duplicates allowed (SUM rule) |
| L1′ | Lemma 2's parity step: Σ w_i n_i ≥ Σw + 2 Σ_{i∋x⋆} w_i | `Cert.W_le_sum_wn_parity` | n_i odd, and n_i ≥ 2 when x⋆ ∈ I_i |
| — | §4.2 the verifier uses closed [t1, t2] ("conservative") | `Cert.condR_of_closed` | closed-interval (R) ⇒ (R) |
| — | Theorem steps (i)–(v) | `Cert.sum_Phi_le` (i)+(ii), `Cert.sum_PhiW` (iv), `Cert.core` (iv)+(v) | |
| L2 | THEORY_ZSIGN §2 Theorem (atom level) | `Cert.certificate` | (C) is assumed only for d > 0, exactly as stated |
| L2 | the Theorem for a v4 certificate, about zeros (v4 §1 + Theorem) | `ZeroData.v4_onLine` | uses **only** `Lemma1Weak` |
| L3 | atlas_v3 Lemma 2 (atom level) | `Cert.lemma2_parity` | needs (C) at the d = 0 point (x⋆, 0) |
| L3 | Lemma 2 for a v4 certificate, about zeros | `ZeroData.v4_simple`; with L2: `ZeroData.v4_closed` | uses `Lemma1Parity` |
| L4 | v4 §10 (i) | `Cert.slayer_away`, `ZeroData.v4_simple_away` | open intervals suffice (the doc says "no closed interval", which is stronger) |
| L4 | v4 §10 (ii) | `Cert.slayer_perzero`, `ZeroData.np_simple` | pointwise form of the one-line verifier change, with cl I_i |
| L4 | v4 §10 remark "cannot cover two true zeros" | `Cert.slayer_atMostOne` | |
| L4 | v4 §10 (iii), claim (B) for one main certificate | `ZeroData.claimB` | **weak Lemma 1 only** |
| L5 | v4_1 §2 Lemma A (N ≤ 1) | `ZeroData.lemmaA` (box symmetric, σ0 + σ1 = 1), `ZeroData.lemmaA_closed` (box ⊇ strip ⇒ v4 claim on [t0, t1]) | parity is not used |
| L5 | v4_1 §2 Lemma B ("count = sign changes") | `ZeroData.lemmaB` (N pairwise disjoint intervals), `ZeroData.lemmaB_alternating` (N+1 strictly alternating points, the doc's form), `ZeroData.lemmaB_closed` | weak Lemma 1 only; the mirror symmetry is not used either |
| L6 | v4 §6 claim, v4_1 §6 assembled claim (A) | `ZeroData.window_claim_A` | regions = passed v4 certificates or counted leaves; hull ⊂ union of x-projections |
| L6 | v4 §10 (iii) claim (B) over the hull | `ZeroData.window_claim_B` | weak Lemma 1 only |
| — | v4 §1 (H_model) for the all-open model | `ZeroData.hmodel_atoms` | uses 0 < Re ρ < 1 and that the bins cover W |
| — | rows and count of atoms = sums over zeros | `ZeroData.atoms_sum`, `hrows_atoms`, `hcount_atoms` | mirror bijection |
| — | n_i = on-line multiplicity in I_i, **if I_i ⊂ W** | `ZeroData.n_atoms` | |
| — | 2-D tiling ⇒ 1-D cover | `ZeroData.cover_of_cover2D` | |
| L7 | LOCAL_COUNT Theorem 1 (summation step: c ≥ 0, row sums ≤ Ehi, G ≥ 1 on J × [0, 1/2) ⇒ N(J) ≤ Σ c Ehi) | `ZeroData.theorem1_count` | kernel positivity (Lemma 0) and (E) enter as the hypothesis on window row sums |
| L7 | v4_2 Corollary 2 (N(J) ≤ B, ⌊B⌋ ≤ k + 1, k disjoint sign-change intervals in J ⇒ all zeros in J on the line and simple) | `ZeroData.localCount_closed` | **uses `Lemma1Parity`** (odd multiplicity per interval); not Lemma 2; uses mirror symmetry (off-line zeros come in pairs) |
| — | reduction m = 0 | `example` in Certificate.lean | |
| L8 | file audit: region ⊂ window, d-range [0, 1/2] (d = 0 included) | `AtlasAudit.regionOk_spec` | check `regionOk` |
| L8 | file audit: intervals ⊂ window, t1 < t2, sorted, pairwise disjoint | `ivOk_spec`, `sortedDisjoint_spec`, `ivs_disjoint` | checks `ivOk`, `sortedDisjoint` |
| L8 | file audit: THEORY_389A §6 (4), central policy | `centralOk_spec` | check `centralOk` |
| L8 | file audit: v4 all-open model = on/off pairs, bins cover W | `binsOf_spec`, `allOpen_sub`, `condR_allOpen`, `modelOk_spec` | check `modelOk` |
| L8 | file audit: per-certificate | `certOk_spec`; `exists_v4Cert`, `exists_npCert` (file ⇒ every combinatorial field of `V4Cert` / `NPCert`) | Arb facts remain hypotheses |
| L8 | exact tiling of target × [0, 1/2] (and the d = 0 line) | `coversB_spec` (sweep is sound for any order), `targetOk_spec`, `targetOk_line`, `closed_of_targetOk` | proves the pointwise cover, closing finding 7 below for the audited files |
| L8 | v4 §10 (iii) S-layer coverage | `claimBOk_spec` | = the `hcov` hypothesis of `claimB` |
| L9 | THEORY_37A Lemma Z (a), ε = −1; THEORY_389A Lemma Z⁺ (a), ε = +1 | `Degree2.lemmaZ_imag_minus`, `lemmaZ_real_plus` | from `Degree2.FE` (FE + real coefficients) |
| L9 | Lemma Z (b): zeros of Z = on-line zeros | `lemmaZ_zero_plus`, `lemmaZ_zero_minus`; multiplicity: `lemmaZ_factor`, `lemmaZ_factor_plus` (algebraic step) | the continuity step of "same multiplicity" is the hypothesis `hord` |
| L9 | Lemma Z (c): sign symmetry | `lemmaZ_sym_plus/minus`, `lemmaZ_sign_plus/minus` | weight E(t) = e^{πt/2} abstract, E > 0 |
| L9 | Lemma Z (d) / Z⁺ (d): central order parity | `coef_parity`, `order_parity`, `central_mult_parity`, `central_zero_minus`, `order_two` (Lemma C2 shape) | Taylor coefficients via the hypothesis structure `TaylorAt0` |
| L9 | Lemma 1 (parity form) for degree 2 | `lemma1Parity_of_lemmaZ`, `hzero_of_lemmaZ_plus/minus` | sign-change parity of real functions = hypothesis `SignParity` |
| L9 | Corollary 2 / Lemma B ("count = sign changes") for degree 2 | `deg2_localCount_closed`, `deg2_lemmaB_closed` | instances of `localCount_closed`, `lemmaB_closed` |
| L9 | THEORY_DEG2 §7 single box W × [0, 1/2], f = 2 | `condR_deg2`, `exists_v4Cert_of_deg2`, `exists_v4Cert_deg2` | "Φ scales with f"; a deg2 certificate is a `V4Cert` with one bin |
| L10 | THEORY_389A §3 reduced configuration Z′ | `ZeroData.reduce` | Z′ is a `ZeroData` (ρ0 = 1/2 is self-mirror) |
| L10 | (H_rows′), (H_count′): shifted enclosures, N_win − m0 | `reduce_sum`, `reduce_rows`, `reduce_count` | needs ρ0 ∈ zeros, m0 ≤ mult ρ0, wlo ≤ 0 ≤ whi |
| L10 | Lemma 1 on Z′ | `reduce_onLine` | needs only: no OPEN interval contains 0 |
| L10 | certificate theorem for Z′ ⇒ conclusion for Λ | `v4_closed_of_odd` (v4_closed with per-interval parity), `central_reduction` | all zeros ≠ ρ0 in the region on the line and simple; mult ρ0 ≤ m0 + 1 |
| L10 | X1 (multiplicity exactly m0) | `x1_exact` | with evenness (`central_mult_parity`) |
| L10 | the reduction from a checked 389.a file | `central_reduction_of_file` | policy facts from `centralOk_spec` |

The hypothesis signatures make the trust split exact.

* Only `v4_simple`, `v4_closed`, `window_claim_A` and `localCount_closed` take `Lemma1Parity`.
  `localCount_closed` needs it because the bound has slack 1: with only n_i ≥ 1, a double zero inside one
  interval would give N = k + 1 and pass the test ⌊B⌋ ≤ k + 1.
* Every other result, including the off-line exclusion, the S-layer, claim (B) and Lemmas A and B, takes at
  most `Lemma1Weak`.
* Claim (A) depends on parity, and therefore on atlas_v3 Lemma 2, only for simplicity.

## `#print axioms` (`scripts/PrintAxioms.out`)

Every theorem, old and new, depends only on `propext`, `Classical.choice`, `Quot.sound` (`x1_exact` uses only `propext`, `Quot.sound`).

```
'Atlas.Cert.condR_of_closed' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.sum_Phi_le' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.core' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.signChange_credit' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.W_le_sum_wn' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.W_le_sum_wn_parity' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.certificate' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.lemma2_parity' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.slayer_away' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.slayer_perzero' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Cert.slayer_atMostOne' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.atoms_sum' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.hmodel_atoms' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.n_atoms' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.atoms_split_offline' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.atoms_split_multiple' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.v4_onLine' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.v4_simple' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.v4_closed' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.v4_simple_away' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.np_simple' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.claimB' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.lemmaA' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.lemmaA_closed' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.lemmaB' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.lemmaB_alternating' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.lemmaB_closed' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.window_claim_A' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.window_claim_B' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.onLine_eq_win' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.theorem1_count' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.localCount_closed' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.regionOk_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.ivOk_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.sortedDisjoint_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.ivs_disjoint' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.coversB_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.centralOk_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.binsOf_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.allOpen_sub' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.condR_allOpen' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.modelOk_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.certOk_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.exists_v4Cert' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.exists_npCert' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.targetOk_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.targetOk_line' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.closed_of_targetOk' depends on axioms: [propext, Classical.choice, Quot.sound]
'AtlasAudit.claimBOk_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_real_plus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_imag_minus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_zero_plus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_zero_minus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_factor' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_factor_plus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_sym_plus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_sym_minus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_sign_plus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemmaZ_sign_minus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.coef_parity' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.order_parity' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.central_zero_minus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.central_mult_parity' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.order_two' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.lemma1Parity_of_lemmaZ' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.hzero_of_lemmaZ_plus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.hzero_of_lemmaZ_minus' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.deg2_localCount_closed' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.deg2_lemmaB_closed' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.condR_deg2' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.exists_v4Cert_of_deg2' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.Degree2.exists_v4Cert_deg2' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.reduce' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.reduce_sum' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.reduce_rows' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.reduce_count' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.reduce_onLine' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.v4_closed_of_odd' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.central_reduction' depends on axioms: [propext, Classical.choice, Quot.sound]
'Atlas.ZeroData.x1_exact' depends on axioms: [propext, Quot.sound]
'Atlas.central_reduction_of_file' depends on axioms: [propext, Classical.choice, Quot.sound]
```

`Atlas/LocalCount.lean` (2026-10-07) was built with the existing Mathlib cache (no new download): incremental build 4.5 s wall,
file check about 2 s. Floor is avoided (B < k + 2 instead of ⌊B⌋ ≤ k + 1) because `Mathlib.Algebra.Order.Floor` is not in the local
import closure.

## 2026-10-08 additions: file audit and degree-2 lemmas

**Part 1, file audit.**
* `export/export_certs.py` reads every certificate JSON read-only and writes exact rationals: `Fraction(float)` of each stored
  binary64, with no rounding.
* `lake exe atlas_audit` checks, for every certificate:
  * region ⊂ window with x0 < x1;
  * d-range exactly [0, 1/2], so the candidate box contains d = 0 (or {0} for S-layer certificates);
  * intervals ⊂ window, t1 < t2, sorted and pairwise disjoint;
  * the central policy: for 389.a, reduction used ⇔ window ∋ 0, m0 = 2, and no interval meets 0; no reduction elsewhere;
  * for v4, that the model is the all-open model and its bins cover the window.
* It also checks, for every target, the exact tiling of target × [0, 1/2] by replay-passed regions, and, for v4, the claim (B)
  S-layer coverage.
* `Atlas/Audit.lean` proves that each check implies its statement over ℝ. It also proves that a checked file supplies every
  combinatorial field of `V4Cert` / `NPCert`.
* Datasets:
  * deg2 (737 files), ec37a (400), ec389a (420), tollis (1,764 for the six pre-registered fields, plus 136 extras);
  * v4: 32 acceptance and 99 other files;
  * 108 negative-control files.
* Result: **0 violations** in every real dataset, and all 217 binary64 targets are exactly covered. The ec389a controls give
  39 violations (the intended m0 = 0 / 1 policy breaks). 12/12 injected faults were caught.
* The numerical inequalities (rows, (R), (C), signs of Z) stay **trusted** (Arb).
* Findings, all without violation:
  - claims with non-dyadic decimal endpoints (tollis core windows, Lehmer, c7002, Rosser, 663318) are exactly covered for the
    binary64 endpoints but miss sub-ulp slivers of the decimal interval;
  - the Lehmer target [7005.06, 7005.10] contains only the first zero of Lehmer's pair (the second is at 7005.1006);
  - tollis extras (−87, −104, −107, −108) were run after `tollis/RESULTS.md` said they were not.

  Details: `audit/RESULTS.md`.

**Part 2, degree-2 lemmas.** See rows L9 and L10 above.
* What the formalization shows:
  * Lemma Z (a) and (c), and the zero-set half of (b), follow by algebra from the FE hypothesis.
  * Central parity follows from FE + Taylor-coefficient uniqueness. Every nonzero coefficient has (−1)^n = ε, which is
    stronger than a statement about the leading one.
  * The central-mass reduction is now in Lean, so THEORY_389A §3's "only this reduction step … is outside the Lean files" is
    closed.
* One formal subtlety. The existing `v4_closed` takes Lemma 1 for *all* intervals. For Z′ that is not literally available:
  for an interval straddling 0, n′ = n − m0, which may be 0. The reduction therefore goes through `v4_closed_of_odd`, which
  takes parity only for the certificate's own intervals. Those are exactly the intervals the policy keeps away from 0.
* Not formalized:
  * the continuity step of Lemma Z (b)'s "same multiplicity" (hypothesis `hord`);
  * real-variable sign-change parity (`SignParity`);
  * Taylor uniqueness (`TaylorAt0`);
  * modularity, Lemma M, and Λ''(1) ≠ 0.
* The local Mathlib closure has no complex analysis, and no new Mathlib was downloaded.
* Build: `lake build` (all Atlas files, about 7 s incremental) and `lake build atlas_audit`. All runs used nice 19. No Mathlib
  download; the existing oleans suffice.

## Findings: gaps, ambiguities and slack in the informal proofs

No informal proof was found to be wrong. Formalizing made the following explicit.

1. **(C) at d = 0 (Lemma 2, §10 (i)).**
   * THEORY_ZSIGN states (C) only for d > 0, and its Theorem needs only that.
   * Lemma 2 ("the *unchanged* condition (C)") and §10 (i) need (C) at the point (x⋆, 0).
   * This holds because the verifier checks the closed box [x0, x1] × [d0, d1] with d0 = 0. It does not
     follow from the Theorem's (C) as written. In Lean, `lemma2_parity` and `slayer_away` take (C) at
     (x⋆, 0) as a separate hypothesis, and `V4Cert.condC` covers d ∈ [0, 1/2].
2. **Candidate region inside the window.**
   * THEORY_ZSIGN's Theorem does not state it.
   * atlas_v4 §5 added it as a replay check ("the Theorem needs the candidate to be a window atom").
   * The Lean proof uses it essentially (`V4Cert.x0_ge`, `x1_le`). Without it, (H_rows) and (H_count) say
     nothing about a⋆.
   * v3 certificates rely on the region being built inside the window. I did not check that.
3. **Intervals inside the window.** THEORY_ZSIGN states this, and it is load-bearing: `n_atoms` equates n_i
   with Lemma 1's on-line multiplicity only under t1 ≥ wlo and t2 ≤ whi.
4. **Box count, open vs closed (v4_1 Lemma A).**
   * The counter counts zeros in the open rectangle.
   * The proof needs the closed-box count, which is justified by the counter's certified nonvanishing on ∂B.
   * Lean takes the closed-box count as the hypothesis.
   * F1 (no trivial zeros and no pole in B) is what identifies ζ's count in B with the count of `ZeroData`.
     That is a hypothesis-level identification.
5. **Slack, not gaps.**
   * §10 (i) needs only that x⋆ is in no *open* interval.
   * Lemma B needs neither mirror symmetry nor parity.
   * Lemma A needs no parity.
   * In claim (A), parity (Lemma 2) is used only for simplicity on v4 regions. On-line-ness is parity-free.
6. **Re-representing a multiple zero (Lemma 2, §10).** The informal step "row sums and the count depend only on
   Σ f" is proved as `merge_sum`: merging two (x, 0, 1) atoms into one (x, 0, 2) atom preserves every
   f-weighted sum, including n_i and its parity.
7. **Tiling.**
   * The Lean assembly needs only a pointwise cover of the hull by x-projections.
   * For v4's full-height regions, the 2-D cover implies this (`cover_of_cover2D`, taking d = 0).
   * A cover of hull × [0, 1/2] by finitely many closed rectangles, up to measure zero (which is what the exact
     tiling checks), is automatically a pointwise cover, because a finite union of closed sets is closed.
     The d = 0 line therefore needs no separate check *logically*. The separate 1-D sweep in v4 guards
     against the v3 script bug (§9.1), not against a gap in the logic.
   * This measure-to-pointwise remark is not formalized. (2026-10-08: for the audited files it is not needed. `targetOk_spec`
     proves the pointwise closed cover, including d = 0, directly from the exact check.)

Outside the scope (hypotheses here, unverified by Lean):
* the sech-row (H_rows) argument, including "every zero's contribution depends only on (x, d)";
* Trudgian's Nwin;
* Lemma 1 itself (sign changes of Z and parity of multiplicities). For degree 2 it is now derived from Lemma Z (b) plus the
  real-variable `SignParity` (`lemma1Parity_of_lemmaZ`);
* Arb correctness;
* the argument-principle counter.

## Build

```
# toolchain (no shell-profile edits)
curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -o elan-init.sh
sh elan-init.sh -y --no-modify-path --default-toolchain none
cd /Users/kiosk/atlas_mark2/formal
~/.elan/bin/lake update                     # fetches mathlib v4.34.1 (toolchain leanprover/lean4:v4.34.1)
# DISK: fetch only the oleans this project imports (≈1.0k files) instead of all ~8.9k:
~/.elan/bin/lake exe cache get Mathlib.Data.Complex.Basic Mathlib.Algebra.Order.BigOperators.Group.Finset \
  Mathlib.Algebra.Order.BigOperators.Group.Multiset Mathlib.Data.Finsupp.Basic Mathlib.Tactic.Linarith \
  Mathlib.Tactic.Positivity Mathlib.Tactic.Ring Mathlib.Order.Interval.Set.Basic \
  Mathlib.Algebra.BigOperators.Ring.Finset Mathlib.Data.Set.Finite.Basic
nice -n 19 ~/.elan/bin/lake build
nice -n 19 ~/.elan/bin/lake env lean scripts/PrintAxioms.lean
# file audit (2026-10-08)
nice -n 19 python3 export/export_certs.py
nice -n 19 ~/.elan/bin/lake build atlas_audit
nice -n 19 .lake/build/bin/atlas_audit audit/data/*.txt      # exit 0 iff no violation outside the *_nc control datasets
nice -n 19 python3 audit/mutation_test.py
```

(`lake update` itself ran the full `cache get` once. See "Disk" below.)

## Disk and time

* **Disk.** About 14 GB was free at the start.
  * `lake update` ran the full Mathlib cache download automatically (8,908 files, about 7.6 GB in `.lake`).
    Together with the 2.7 GB toolchain, this briefly dropped free space to **4.4 GB**, below the 5 GB limit.
  * I immediately deleted the full Mathlib oleans and the download cache (`~/.cache/mathlib`). I then fetched
    only the import closure needed here (1,023 files).
  * Final footprint: `~/.elan` 2.7 GB plus `formal/.lake` 1.8 GB. About **10 GB is free** afterwards.
* **Time.**
  * Download: about 2 min.
  * Clean build of the 6 Atlas files: 17 s wall.
  * Peak RSS: 1.6 GB.
* **Builds.** Everything ran with `nice -n 19`. Only Atlas files were compiled. Mathlib was never compiled
  from source.
