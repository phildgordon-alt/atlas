# Review of the v2 algebra gate (investigate_24064/algebra_pari_gate_v2.py), 2026-10-21

The reviewer did not write the gate. The reviewer's code is `independent_table_v1.py`, and the output is in `runs/independent_table_v1.json`. It
imports nothing from artin_all, artin_literal or investigate_24064. `crosscompare_v1.py` compares the reviewer's data with the author's, and its
output is in `runs/crosscompare_v1.log`.

**Verdict: PASS.** Both filters are correct necessary conditions, and they are applied to the right objects. With both filters applied, the
F/H patterns are determined at every p. Neither filter is enough by itself. The code implements the mathematics as stated. Two
strengthenings are adopted in production (see §4), but neither is needed for correctness.

## 1. Filter (a): inertia admissibility

Let p be a prime and 𝔓 a prime of the Galois closure K̃ above p. Write D = D(𝔓/p) ⊂ Gal(K̃/Q) = S5 and I = I(𝔓/p) = G_0 ⊂ D. Then:

* **The wild inertia is normal.** G_1 is normal in G_0.
* **The tame quotient is cyclic.** G_0/G_1 embeds into the multiplicative group of the residue field (Serre, *Local Fields*, IV §2,
  Prop. 7 and Cor. 1), so it is cyclic of order prime to p.
* **G_1 is a p-group** (Cor. 3). Because [G_0 : G_1] is prime to p, G_1 is the unique Sylow-p subgroup of I.

So I has a normal Sylow-p subgroup P (P = 1 when p ∤ |I|), and I/P is cyclic. These are properties of the abstract group I, and they are
preserved under conjugation. It is therefore correct to test them on the representative of each S5-conjugacy class of pairs (D, I). D and I
are taken in Gal(K̃/Q), as subgroups of S5 through the action on the roots of f. They are not the decomposition and inertia data of K or of
any subfield. This is the level at which `local_pairs()` and `ef_of()` work.

* **The condition is necessary, not sufficient.** For example, the tame relation (Frobenius acts on G_0/G_1 by the p-th power) is not
  imposed. A necessary condition can only remove pairs that cannot occur. The true pair always survives, so the v2 candidate set is a
  subset of v1's that still contains the truth.
* **The code tests the condition correctly.** `admissible()` asks whether the elements of p-power order form a set of size q = |Syl_p|.
  That is equivalent to the Sylow-p subgroup being unique, hence normal: every Sylow subgroup lies in that set, and conversely that set
  contains every Sylow subgroup. The code then asks whether ⟨x⟩P = I for some x, which says I/P is cyclic. The reviewer's version counts
  the Sylow subgroups directly and computes element orders in I/P. Both versions give the same verdict on all 38 classes at p = 2, 3, 5, 7.
* **p ≥ 7 is covered by p = 7.** For p ≥ 7, p ∤ 120, so P = 1 and the condition reads "I cyclic". The reviewer checked p = 7, 11 and 13
  and got identical results (`p_ge_7_is_I_cyclic: true`). Using p = 7 as the representative of all p ≥ 7 is therefore valid.

## 2. Filter (b): the auxiliary field KE = K(√D_E)

* **KE is the fixed field of A4.** K = K̃^{S4} with S4 = Stab(point), and E = K̃^{A5}. The compositum KE is the fixed field of
  S4 ∩ A5 = A4, which has index 10. K ∩ E = Q, since the degrees 5 and 2 are coprime, so [KE : Q] = 10.
* **The code builds that field.** `polcompositum(f, x² − D_E')[1]` is a degree-10 polynomial. The record requires KE_degree = 10, KE
  irreducible, and K ⊂ KE and E ⊂ KE (nfisincl). A degree-10 field containing both K and E equals KE.
* **The local data at p are correct.** KE is ramified only at primes dividing d, which are all in listP = primes(disc f) ∪ {5}.
  nfinit([pKE, listP]) is maximal at listP, so idealprimedec gives the true (e, f) at those primes.
* **The (e, f) pattern of KE is determined by the class of (D, I).** The primes of K̃^U above p correspond to D\G/U, with e = |I g U|/|U|
  and e·f = |D g U|/|U|. This is the same rule `ef_of` uses for K, K10, E, F and H, and it depends only on (D, I) up to conjugacy.
  `ef_on(ACT_KE, ·)` computes it with the orbit method, and the reviewer recomputed it with the double-coset formula. The two agree on all
  38 classes.
* **Matching KE is a valid extra constraint.** The true (D, I) must reproduce PARI's KE pattern. KE is built from f and D_E only, so the
  constraint does not use F or H and is not circular with the F/H check it supports.

## 3. Independent table (reviewer's code)

S5 has 156 subgroups in 19 conjugacy classes. There are **38** classes of pairs (D, I) with I ⊴ D, D/I cyclic and I ≠ 1. The multiset of
per-pair data (orders, the patterns of K, K10, E, F, H and KE, and admissibility at 2, 3, 5, 7) is **identical** to the author's
(`crosscompare_v1.log`).

The table counts, for each prime and each choice of filters, how many (K, K10, E[, KE]) patterns still allow more than one F/H pattern:

| p | admissible pairs | no filter (v1) | (a) only | (b) only | (a)+(b) | number of patterns with (a)+(b) |
|---|---|---|---|---|---|---|
| 2 | 26 | 2 | 1 | 1 | **0** | 25 |
| 3 | 22 | 2 | 1 | 1 | **0** | 21 |
| 5 | 21 | 2 | 1 | 1 | **0** | 18 |
| ≥7 | 18 | 2 | 1 | 1 | **0** | 17 |

The author's `table_check()` gives the same numbers: 26/25, 22/21, 21/18 and 18/17, with no ambiguity. **The F/H patterns are unique for
every class at p = 2, 3, 5 and ≥ 7 after both filters.** Each filter removes a different ambiguity, so both are needed:

* **Filter (b) settles the 2-group pattern.** That pattern is K (1,1)(4,1), K10 (2,1)(4,1)(4,1), E (2,1). At p = 2 all three of its
  pairs (C4,C4), (D8,D8) and (D8,C4) are admissible, but their KE patterns differ:

  | pair | KE pattern |
  |---|---|
  | (C4, C4) | (2,1)(4,1)(4,1) |
  | (D8, D8) | (2,1)(8,1) |
  | (D8, C4) | (2,1)(4,2) |

* **Filter (a) settles the (5,1)/(10,1)/(2,1) pattern.** Its two pairs are (F20, F20), with F pattern (1,1)(5,1), and (S5, S5), with
  F pattern (6,1). KE is (10,1) for both, so filter (b) cannot separate them. Filter (a) can: I = S5 is never admissible, because its
  Sylow-p subgroup is never normal, and I = F20 is admissible only at p = 5.

**The two observed cases.** PARI's data, run through the reviewer's own table:

* **5.1.24064.1 at p = 2.** PARI's KE pattern is (2,1)(8,1). Exactly one pair survives, (D8, D8). Its F pattern (2,1)(4,1) and H pattern
  (4,1)³ equal PARI's.
* **5.1.17145.1 at p = 3.** (D8, D8) is not admissible, because D8 is not 3-admissible. PARI's KE pattern is (2,1)(4,2), which leaves
  (D8, C4). Its F and H patterns, (1,2)(4,1) and (2,2)(4,1)(4,1), equal PARI's.

## 4. Code review of algebra_pari_gate_v2.py (and what production adds)

**The gate's code is correct.**

* **v1 is reused unchanged.** The v1 computation is `SV1.one`, imported read-only. That module's import creates directories with
  `exist_ok` only, and nothing else in it writes.
* **The v2 `all_ok` is strictly stronger than v1's.** It is the v1 formula with `gt_derivation_all` replaced by `gt_derivation_all_v2`,
  plus table_unambiguous, KE degree 10, KE irreducible, K ⊂ KE, E ⊂ KE, and the calegari2 local data unchanged. Only the derivation
  term is replaced, never weakened. At unramified primes in listP, KE must be unramified.

**The 24064 failure was only the derivation term.** INTEGRATED.md lists `incl_K_in_H` and `local/5 ramified` as failures. That is a
misreading: the required values of those keys are False, and they are False. The reviewer checked the v1 record of 5.1.24064.1 directly. The
only failed term is `gt_derivation_all`, at p = 2, where 3 pairs match. That agrees with the main session's REPORT.

**Two strengthenings are adopted in production** (`../algebra_pari_sweep_v2.py`). Neither changes the mathematics.

1. `calegari2_local_identical` must be True. The gate accepts None, meaning the file is absent.
2. Every v1 key of the recomputed record must equal the stored `runs/alg/pari/<label>.json`, apart from the timing keys `t` and `t_coeff`.
   The result is recorded as `v1_record_identical`. This keeps the v2 record consistent with the v1 record and the shadow local data the
   certificate run uses.

The production script imports the reviewed gate module read-only, calls its `one()` unchanged, and writes `runs/alg_v2/pari/<label>.json`
under artin_sweep, as new files only. Both modules are hashed in `../../geval_c/CODE_AT_VALIDATION_v5.sha256`.

## 5. Scope

* **Fields certified under v1 are not reopened.** Their F/H Euler factors came from PARI. They were cross-checked against PARI's dirzetak
  through the hashes, and they passed the v1 derivation uniquely. The author's validation (72 sweep fields identical) and the scan of 276
  records stand.
* **The review covers the mathematics and the gate code**, not the analytic engine. The engine is unchanged (geval_c v4, review
  ../../geval_c/review/REVIEW.md).
