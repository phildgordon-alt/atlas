# artin_sweep: final results — Artin's conjecture for LMFDB S5 quintic fields, d > 2·10⁴ (2026-10-21/27)

Pre-registration: `PREDICTIONS.md` (sha256 9ada0348…, `PREDICTIONS.sha256`) then `PREDICTIONS_ADDENDUM_1.md`
(`PREDICTIONS_ADDENDUM_1.sha256`). Earlier stages: `RESULTS.md` (stage 0, stopped at the disk floor before the queue started) and
`INTEGRATED.md` (switch from the frozen streamed engine, queue_v1/cert_field_v1, to the reviewed geval_c engine, queue_v2 →
queue_v3/cert_field_v3 + the v2 algebra gate). This file reports the **final** state: the queue ran out its wall budget twice
(first stop ≈ 2026-10-25 11:54 at d = 119 297, resumed; final stop 2026-10-27 00:01:52) and is now idle.

## 0. Bottom line

* **2 259 fields** with d > 2·10⁴ are now certified **ζ_H(σ) < 0 on (0,1), in both parameter sets A and B**, via
  ζ_H ζ ζ_K = ζ_F ζ_E ζ_K10 with all four factors on the right certified negative (A/B overlap) — hence Artin's conjecture (every
  irreducible complex representation of Gal(K̃/Q) ≅ S5 is automorphic) for each. Combined with the pre-existing coverage
  (174 fields d ≤ 2·10⁴ from `artin_all`, 12 literal fields in (2·10⁴, 4·10⁴] from `artin_literal`), Atlas now holds this result for
  **2 445 distinct LMFDB S5 quintic fields of signature (1,2)**, contiguous in d from the smallest field up to **d_max = 132 536**,
  with the two gaps below.
* **2 gaps in the contiguous range (d > 2·10⁴): 5.1.98385.1 (d = 98 385) and 5.1.105177.1 (d = 105 177).** For both, ζ_F set A is
  **NOT CERTIFIED** (margin −163.3 and −48.5 respectively — the plan's X2 for set A undershot), while **set B, and all other six
  objects in both sets (K10, K, E in A and B; F in B), are CERTIFIED**. ζ_F(1/2) itself is negative in set B for both
  (−0.00991 ± 2e−14 and −0.01791 ± 4e−14), so these are very likely true positives — **not counterexamples** — but they do not meet
  the both-sets bar and are excluded from the 2 259 count. A set-A rerun with a wider X2 plan would very likely close them; this was
  not attempted (see §6).
* **2 operational timeouts, both resolved, not gaps:** 5.1.88925.1 and 5.1.95345.1 each hit the 1-hour per-field wall clock
  (`KILLED_TIME`, rc = 137, after 3 603 s) on 2026-10-23 and were logged `ALGEBRA_ERROR`. Both were retried on 2026-10-25 and
  completed quickly and cleanly (42 s and 298 s respectively), `status: DONE`, `all_certified: true`, route `calegari_plus_PS`. They
  are counted in the 2 259.
* **The sweep ended on its wall budget, not on a failure or a disk/memory limit.** Final queue event:
  `{"event": "stop", "reason": "wall budget", "next": "5.1.132569.1", "d": 132569}` at 2026-10-27 00:01:52. 5.1.132569.1 and
  everything above it (predicted ≈ 220 more fields to the fetched list's ceiling at d ≤ 1.5·10⁵) is simply not yet run.

## 1. Route split

| route | count (all field records, this directory) | count (final-queue, queue_v3.jsonl only) |
|---|---|---|
| `calegari_published` (literal: 5 ∤ d, Frob_5 ∈ 2B, Calegari Thm 1.1/1.2 as published) | 130 | 129 |
| `calegari_plus_PS` (Calegari + Lemma 3.2 via Pilloni–Stroh, as KLW state it) | 2 128 | 2 036 |
| none (did not reach a route: the 2 ζ_F-set-A gaps + 1 legacy record) | 3 | 4 |

Separately, **12 literal fields in (2·10⁴, 4·10⁴]** were certified earlier in `../artin_literal/` (part of the 15 reported there; the
other 3 have d ≤ 2·10⁴ and are already inside `artin_all`'s 174). Those 12 are excluded from this sweep's own totals (the queue was
built to skip them, per `PREDICTIONS.md` §1) but complete the "all fields with d ≤ D" statement together with the 2 445 above.

## 2. The two timeouts and the two gaps (detail)

* **Timeouts** (`logs/field/5.1.88925.1.log`, `5.1.95345.1.log`): the first attempt ran the algebra/structure checks fine (≈ 3 s) and
  then was killed by the watchdog at the 3 603 s field-level time limit during certification — not a correctness failure, just a slow
  first attempt (possibly an unlucky PARI stack/factorisation path). The retry two days later, same code, same parameters, finished
  in under 5 minutes each. No code or parameter was changed between the two attempts.
* **Gaps** (`runs/field/5.1.98385.1.json`, `5.1.105177.1.json`): `verdicts.F_A = "NOT CERTIFIED"` with `margins.F_A` negative
  (−163.3, −48.5) against `margins.F_B` positive and large (4.1, 9.4); every other verdict (`K10_A, K_A, E_A, K10_B, K_B, F_B, E_B`)
  is `"CERTIFIED"`, `AB_overlap` is true on the three objects where both sets closed, and `zeta_F_half` (set B) is strictly negative
  for both. `all_certified: false`, `zeta_H_negative: false`, `route: null` — the field is correctly excluded from the claim rather
  than silently passed.

## 3. Engines, gates and their review (what "evaluator audited / geval_c reviewed / gate v2 reviewed" means here)

* **geval_c** (`../geval_c/`), the certification engine for ζ_K10/ζ_K/ζ_F/ζ_E, was independently adversarially reviewed
  (`../geval_c/review/REVIEW.md`): verdict **no critical finding**; the core numerics (Lemma F, REDC bound, multi-limb width,
  Lemma P, C7 residues, thread determinism) reproduce independently to the character level. The review attached conditions before
  geval_c could carry claims: (1) fix the `PYTHONOPTIMIZE`/`-O` hole (m1: an unoptimized Python check stripped every C1–C7 check and
  the loaded-library assert); (2) claim runs launched only through the watchdog wrapper with hostile env vars unset and bound to a
  code-hash record (m2/m3); (3) C1–C7 remain mandatory; (4) no unreviewed code change (the 2³²−1 limit, degree-5-only path). All
  four are implemented (`gc_wrap_v4`, `wd_gc_v1.sh`, `verify_sweep_v2`/`v3`) and re-validated in `INTEGRATED.md` before the production
  queue ran: 12/12 re-run certificates canonical-identical to the originals, all 10 adversarial attacks (optimized Python, mutant
  library, `GEVALC_LIB`/`GEVALC_MUTATION_TEST` env vars, `DYLD_LIBRARY_PATH`, a shadow module, a missing hash record) **refused**,
  and negative controls on 5.1.20317.1 rejected (16/16 tampered F/E variants, both sets).
* **The v2 algebra gate** (`investigate_24064/algebra_pari_gate_v2.py`), introduced to resolve the one field (5.1.24064.1) where
  PARI's own Frobenius determination was inconclusive (`ALGEBRA_FAIL`), was independently reviewed in `review_gate_v2/REVIEW.md`:
  **verdict PASS**. Both of its necessary-condition filters (inertia admissibility at the abstract-group level; the degree-10
  auxiliary field K·E matching PARI's ramification pattern) were checked against an independently written reference implementation
  on all 38 S5-conjugacy classes of (D, I) pairs at p = 2, 3, 5, 7(, 11, 13), with identical verdicts, and against a cross-check of
  the gate's own output. Gate v2 plus the v4 engine were then re-validated on 3 already-certified fields (`reval_v3/`): canonical-
  identical certificates (0 differing leaves of 821/597/823 common leaves per object), 3/3 pass Theorem C, 0 rejections.
* **geval_stream** (the engine behind the stage-0 / queue_v1 fields, d ≤ 24 304) carries its own earlier review, referenced but not
  re-read for this report; it is superseded in production by geval_c for everything above d ≈ 24 337.

## 4. The exact theorem, by route, with caveats (unchanged from `RESULTS.md` §6, now covering 2 259 + 130 fields)

> **Literal fields** (5 ∤ d, Frob_5 ∈ 2B — 130 fields total, 12 of them via `artin_literal`): by Calegari (Math. Ann. 356 (2013),
> Thm 1.1/1.2) **as published**, every irreducible complex representation ρ of Gal(K̃/Q) ≅ S5 is automorphic, and Artin's conjecture
> holds for K̃.
>
> **All other certified fields** (2 128 + 2 gaps excluded, non-literal): Calegari's proof with Lemma 3.2 supplied by
> Pilloni–Stroh (Astérisque 382, 2016) Thm 0.3, **as Khare–La Rosa–Wiese (Expo. Math. 2023, Thm 1.2 and remark) state it**. The
> ζ_H route used throughout (ζ_H ζ ζ_K = ζ_F ζ_E ζ_K10, all four certified negative) is exactly Calegari's own remark that
> "the result actually only requires the non-vanishing of L(ρ5,s) for s ∈ (0,1)" combined with the factorisation
> ζ_H = ζ_F · L(η) · L(ρ5) — it needs **no holomorphy assumption on L(ρ5) or L(ρ4⊕ρ5)**. This matters because
> `../general_eval/calegari2/HOLOMORPHY_AUDIT.md` found that a *different* route used elsewhere in Atlas (asserting
> "Λ(ρ4⊕ρ5) entire by Aramata–Brauer") is a **false citation and circular** for non-Galois K10 — Dedekind's conjecture for K10 is not
> known and would itself be a consequence of the theorem being proved. That finding does **not** apply to this sweep's route, which
> only ever uses non-vanishing (an output of Hecke's holomorphy for ζ_H, not an extra input), per the audit's own §1 analysis of
> Calegari's Thm 1.2. No correction to this sweep's claim is needed from that audit.

**Caveats, unchanged:**
* **Pilloni–Stroh substitution needs expert confirmation** (Calegari). PS16 itself was not read by Atlas; the reading that the 5-
  and 6-dimensional cases and the ζ_H step survive the substitution is KLW's and Atlas's, not independently verified.
* **Dwyer (BLMS 46, 2014) overlap is unknown** (paywalled): Dwyer also remarks that the Frob_5 hypothesis is superfluous and gives
  unspecified examples; whether any of the 2 128 non-literal fields are already covered by Dwyer is not known.
* The evaluator (geval_c) is not formally verified, though audited and reviewed under the conditions in §3.
* Field data come from PARI, cross-checked by flint and by `dirzetak` hashes; the v2 gate adds a third, independently-reviewed check
  where PARI alone is inconclusive.
* The list relies on LMFDB completeness (checked for |D| < 1.2·10⁷ as of the 2026-10-21 completeness page).
* Novelty: "to our knowledge"; no exhaustive literature search.

## 5. Costs

| source | fields (field events) | productive cert time (CPU-equivalent wall, Σt) |
|---|---|---|
| queue_v1 (geval_stream, cert_field_v1) | 53 | 3.45 h |
| queue_v2 (switch validation, cert_field_v2/gc_wrap_v4) | 37 | 0.46 h |
| queue_v3 (production, cert_field_v3 + gate v2) | 2 169 field events (2 167 DONE + 2 timeouts) | 124.0 h, split **113.7 h** `calegari_plus_PS` / **10.1 h** `calegari_published` / 0.2 h other |
| **total Σt** | | **≈ 127.9 CPU-h** |

Plus ≈ 2.0 h of wall time lost to the two 3 603 s timeouts (not in Σt above, since those attempts produced no `t` field) and ≈ 45 min
for V1–V3 validation, 46 min for negative controls, and ≈ 2 h for the LMFDB fetch (one-off, light). Peak footprint stayed under the
1 500 MB cap throughout (typical 200–600 MB per field; largest observed 698 MB). No watchdog kill fired on disk or memory; the two
kills were both the field-level 1-hour time limit.

**Efficiency note.** The pre-registered cost model (`PREDICTIONS_ADDENDUM_1.md`) predicted D_reached ≈ 5.2·10⁴ (470–520 fields)
under the 96 h budget, calibrated on the old frozen streamed engine (geval_stream) at 36 min/field (d/87 529)^1.5. The switch to
geval_c (§3) made the engine roughly 5–10× faster per field at comparable d (e.g. 20–50 s vs 100–410 s at d ≈ 2.45·10⁴ per
`ATLAS_STATUS.md`, 2026-10-21), so the actual queue reached d = 132 536 (2 169 fields in queue_v3 alone) on a comparable total wall
budget — about 2.5× the field count and d-height the original model predicted.

## 6. What remains

* **5.1.132569.1 and above** (d ≤ 1.5·10⁵ per the fetched LMFDB list, ≈ 220 more fields by the list's own density) are not yet run;
  the queue is resumable (`queue_v3.py`, same fields file, same engine) whenever the wall budget is reopened.
* **The two gaps** (5.1.98385.1, 5.1.105177.1) need a set-A rerun with a wider X2 plan (the undershoot is in the planner, not the
  certificate; set B's wider plan already closes both). Not attempted here.
* **Pilloni–Stroh expert confirmation** and the **Dwyer overlap** (§4) remain open, paywalled/unverified items, as before.
* Fields with 1.5·10⁵ < d (beyond the fetched list) are outside the current LMFDB page range and were not fetched.
* No code, parameter or review condition changed during this report; nothing was contacted or posted; no file outside
  `artin_sweep/` (and the one `TARGETS_LEDGER.md` row noted in `RESULTS.md` §8) was written.

---
### CORRECTION 2026-11-01 (appended; nothing above edited)
The count in §0 is wrong. Recounting the stored per-field summaries (`runs/field/*.json`: status DONE, all_certified true, d > 2·10⁴)
gives **2 256** fields, not 2 259: **130** `calegari_published` + **2 126** `calegari_plus_PS` (not 2 128). Found by engine/regress_v1
tier 0 (frozen verifier) and independently recounted by hand the same day. The two gaps (5.1.98385.1, 5.1.105177.1) and the two resolved
timeouts are as stated. The combined total therefore reads **2 442** distinct fields (2 256 + 174 + 12), not 2 445. No certificate,
field verdict or d_max changes; only the headline tally. Logged in diagnostic/CORRECTIONS_2026-10-06.md.
