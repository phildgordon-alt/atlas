# Lean-checked audit of the certificate files: results (2026-10-08, re-run after all 25 Tollis fields)

**Outcome: 0 violations in every real dataset.** 8,091 distinct real certificate files (plus 108 negative-control files) were checked:
every exact/combinatorial condition held, and every target × [0, 1/2] was exactly covered. This includes all 6,400 Tollis
certificates (all 25 complex cubic fields of Tollis's Table 6.2) and the exact union [0, 110] × [0, 1/2] of every field. The checks are Lean functions,
and Lean proves that each one implies its statement over ℝ (`Atlas/Audit.lean`). The numerical inequalities stay trusted
(Arb; see "Trust").

## What was run

```
cd formal
nice -n 19 python3 export/export_certs.py          # exact export  -> audit/data/*.txt   (output: audit/export_output.txt)
nice -n 19 python3 ../release/bundle/tools/export_tollis_unions.py audit/data /Users/kiosk/atlas_mark2/diagnostic
                                                    # -> audit/data/tollis_ext_unions.txt (see below)
nice -n 19 ~/.elan/bin/lake build atlas_audit
nice -n 19 ~/.elan/bin/lake exe atlas_audit audit/data/{deg2,ec37a,ec389a,tollis,tollis_extra,tollis_ext_unions,v4_acceptance,v4_other}.txt \
     audit/data/{deg2,ec37a,ec389a,tollis}_nc.txt   # output: audit/audit_output.txt, exit code 0
nice -n 19 python3 audit/mutation_test.py           # non-vacuity: 12/12 single-fault mutations caught (audit/mutation_output.txt)
```

* Cost: the audit binary takes 2.7 s wall and 72 MB peak RSS (`audit/audit_time.txt`; via `lake exe` 7.3 s); the export takes 3.5 s.
* **Re-run 2026-10-08 (evening), after ADDENDUM 2 of tollis/RESULTS.md (the 15 fields −116 … −239).** `export_certs.py` is
  unchanged (same sha as before). Its `tollis_extra` dataset now holds every core and contig run of the 19 fields outside the six
  pre-registered ones (4 × 244 + 15 × 244 = 4,636 certificates, one target per run). Because the unchanged exporter writes no union
  target for those fields, the bundle-only driver `release/bundle/tools/export_tollis_unions.py` (sha256 cbc75f0d…bcbc) loads the
  exporter's source unchanged (only the DIAG literal is set), calls its own `deg2_dataset`, and writes `tollis_ext_unions`: the same
  4,636 certificate records (checked equal as a multiset to those of `tollis_extra`) plus one union target [0, 110] per field.
  `v4_other` now also contains `lehmer_full_pair` (1 main + 2 S-layer), produced after the first audit. The other data files are
  byte-identical to the first export. `audit/mutation_test.py` was re-run: 12/12 caught, output identical.
* Hashes of the data files, the exporter and the Lean sources are in `audit/SHA256SUMS`.
* Nothing under `diagnostic/` was written.

## Results per dataset

| dataset | certificate files | replay-passed | intervals | per-certificate checks | targets exactly covered | claim (B) | violations |
|---|---|---|---|---|---|---|---|
| deg2 (11.a [100,110], [200,210]; 23.1.b.a [93.5,104]; val 11.a [0,20], 23 [0,18]; contig 11.a, 30 chunks) | 737 | 737 | 20,088 | 737/737 | 36/36 (5 runs, 30 chunks, union [0,300]) | — | **0** |
| ec37a (val [0,10] + 19 chunks) | 400 | 400 | 11,920 | 400/400 | 21/21 (20 runs, union [0,200]) | — | **0** |
| ec389a (val [0,10] + 20 chunks; central reduction) | 420 | 420 | 15,560 | 420/420, of which 40 use the reduction | 22/22 (21 runs, union [0,200]) | — | **0** |
| tollis, the six pre-registered fields (6 core, 6 val, 75 contig chunks) | 1,764 | 1,764 | 47,544 | 1,764/1,764 | 94/94 (87 runs, unions [0,110] ×6, K23 [0,200]) | — | **0** |
| tollis_extra: the 19 further fields −87 … −239 (19 core windows + 209 contig chunks) | 4,636 | 4,636 | 146,928 | 4,636/4,636 | 228/228 (one per run) | — | **0** |
| tollis_ext_unions: the same 4,636 records + the union [0,110] of each of the 19 fields | (4,636, same files) | 4,636 | 146,928 | 4,636/4,636 | 247/247 (228 runs + 19 unions [0,110]) | — | **0** |
| v4 acceptance (V1 [9000,9010], Lehmer, c7002, Rosser, 663318) | 32 (15 main + 17 S-layer) | 32 | 185 (+27,918 model boxes) | 32/32 | 10/10 (target and hull of each run) | 5/5 | **0** |
| v4, the other 15 runs (dev, val, T4-like 1e4–1e7, pathtest, lehmer_full_pair) | 102 (43 + 59) | 102 | 633 (+89,434 boxes) | 102/102 | 30/30 | 15/15 | **0** |
| negative controls deg2 / ec37a / ec389a / tollis | 1 / 28 / 59 / 20 | — | 15 / 236 / 1,023 / 200 | 1/1, 28/28, **20/59**, 20/20 | — | — | ec389a_nc: **39**, as expected |

* The 39 ec389a control violations are exactly the deliberate central-policy breaks: 19 in `nc/m0_0` (window ∋ 0 with no
  reduction) and 20 in `nc/m0_1` (m0 = 1 ≠ the proved order 2). This matches `ec389a/logs/lean_gap_check.json` (39).
* The other controls (forged fake intervals, wrong ε in the generator) are structurally well-formed. They are caught only by
  Arb (NO_SIGN_CHANGE / series mismatch), which is the expected split.
* The interval counts agree with each pipeline's Python `lean_gap_check` once the controls are added back:
  - deg2: 20,088 + 15 = 20,103;
  - ec37a: 11,920 + 236 = 12,156;
  - ec389a: 15,560 + 1,023 = 16,583;
  - tollis (six fields, first audit): 47,544 + 200 = 47,744;
  - tollis, all 25 fields: 47,544 + 146,928 + 200 = 194,672, equal to `tollis/logs/lean_gap_check_addendum2.json`
    (6,420 files, 6,400 real; 1,764 + 4,636 = 6,400).

## What is checked, and the theorem that makes each check mean something

All numbers are exact rationals: the exporter converts each stored binary64 with `Fraction(float)`, which is exact and does
not round. The checks run in Lean on `Rat`.

| condition | Lean check (`AtlasAudit/Check.lean`) | proved meaning (`Atlas/Audit.lean`) |
|---|---|---|
| candidate region ⊂ window, x0 < x1; d-range exactly [0, 1/2] (so the candidate box contains d = 0), or {0} for an S-layer certificate | `regionOk` | `regionOk_spec` |
| every sign-change interval ⊂ window, t1 < t2 | `ivOk` | `ivOk_spec` |
| intervals sorted and pairwise disjoint (t2_k < t1_{k+1}) | `sortedDisjoint` | `sortedDisjoint_spec` (pairwise strict separation), `ivs_disjoint` (the `Disjoint (Ioo …)` form used by Lemma B / Corollary 2) |
| central reduction (389.a): recorded ⇔ used ⇔ window ∋ 0; m0 = 2 (the proved order); no interval meets 0. For every other dataset: no reduction | `centralOk` (expect = 2 / 0) | `centralOk_spec` |
| v4 all-open model: the boxes come in on/off pairs per bin, and the bins cover the window | `binsOf`, `modelOk` | `binsOf_spec`, `allOpen_sub`, `condR_allOpen`, `modelOk_spec` |
| per target: target × [0, 1/2] covered by regions of replay-passed certificates (full d-height); this includes the d = 0 line | `targetOk` (sort, then exact sweep) | `coversB_spec` (any order is sound), `targetOk_spec` (pointwise 2-D cover), `targetOk_line`, `closed_of_targetOk` |
| v4 claim (B): every interval of every passed main certificate, intersected with its region, is covered by passed S-layer regions | `claimBOk` | `claimBOk_spec` (exactly the `hcov` hypothesis of `claimB` / `V4ValidB`) |

**Closing the file-to-theorem gap.**
* `exists_v4Cert` (and `exists_npCert`) turns a v4 certificate that passed the check into a `V4Cert` (an `NPCert`). The
  remaining inputs are the Arb facts (dual ≥ 0, (R) on the file's model boxes, (C)) and the matching of the interval data.
* `Degree2.exists_v4Cert_deg2` does the same for the degree-2 files, via the single-box model.
* `central_reduction_of_file` does it for the 389.a central cells.
* The coverage checks feed `closed_of_targetOk` (the window claim, from per-region claims) and `claimB`.

## Trust (unchanged by this audit, now stated precisely)

**Trusted (not proved in Lean):**
* Every numerical inequality: Arb enclosures of the rows, (R), (C), the consistency check, the sign of Z at the endpoints,
  far allowances and N_win.
* The replay verdicts `passed`, read from `replay.json` (deg2 family) or `replay_check/replay.jsonl` (v4). These require
  plain AND hardened to pass.
* The exporter (about 180 lines of Python) and the text parser in `AtlasAudit/Main.lean`.
* The Lean compiler, which runs the checks natively; the proofs are about the same definitions.
* For the degree-2 family, (R) is checked on boxes that `replay_verify.py` generates from the window: [wlo, whi] split into 8
  pieces × [0, 1/2]. That is code, not file data, so it is not in the audit.

**Proved:** each check ⇒ its statement over ℝ, and the connection to `V4Cert` / `NPCert` / `claimB` / the window assembly.
**Non-vacuity:** `audit/mutation_test.py` injects 12 single faults and all are caught:
* a dropped certificate;
* a certificate marked not passed;
* an interval outside the window;
* two swapped intervals;
* two touching intervals;
* d1 = 0.49;
* a region outside the window;
* the central entry dropped;
* m0 = 3;
* an interval straddling 0 in a central cell;
* a dropped S-layer certificate;
* a dropped model bin.

## Findings (no violation; precision and record-keeping)

1. **Decimal endpoints are covered only up to the binary64 value.**
   * Every target is exactly covered with the endpoints *as stored*, which are binary64.
   * When the claimed decimal endpoint is not a dyadic rational, the audit also checks the exact decimal. In 26 such checks it
     is not covered, by a sub-ulp sliver at one end (26 checks in the first audit; 43 distinct ones in the re-run, the 17 new
     ones being the 15 new Tollis core windows and the target/hull of lehmer_full_pair [7005, 7005.2]; the duplicates in
     `tollis_ext_unions` are not counted). The sliver widths (diagnostic, Python) are:
     - tollis core windows, e.g. K23 [91.81, 103.81]: 2.3e−15 at the low end;
     - Lehmer [7005.06, 7005.10]: 4.0e−13, low end;
     - c7002: 2.2e−13, high end;
     - Rosser [6820050.98, 6820052.15]: 4.5e−10, low end;
     - 663318 [663318.4, 663318.6]: 2.3e−11 at both ends;
     - the tollis extras and the v4 dev/pathtest runs: similar slivers.
   * So these claims hold for [fl(lo), fl(hi)], not literally for the decimal interval.
   * No headline claim is affected:
     - every contiguous claim has integer endpoints, which are exact: deg2 [0, 300], ec37a/ec389a [0, 200], tollis [0, 110]
       and K23 [0, 200], V1 [9000, 9010];
     - each tollis core window lies inside its field's contiguous [0, 110].
   * For the v4 point targets, the fix is wording ("[fl(lo), fl(hi)]") or padding the target by one ulp.
2. **The Lehmer target holds only one zero of Lehmer's pair** (observation from the data, outside the audit's scope).
   * The certified region is [7005.06, 7005.10].
   * The pair's second zero lies in the interval (7005.1005469, 7005.1006250), 5.5e−4 *above* the target. It is credited as a
     sign change but not certified by that run.
   * The pre-registered target is stated correctly as [7005.06, 7005.10]. Do not describe it as "Lehmer's pair".
3. **(Superseded: the extras are now reported in tollis/RESULTS.md ADDENDUM and ADDENDUM 2, and all 19 are complete and audited
   with their unions.)** Original finding: **Tollis extras exist that RESULTS.md says were not run.** At export time, core runs for −87, −104, −107 and −108 (and K87
   contig chunks) were present with replay records; generation was still in progress during this audit.
   * They are audited separately (`tollis_extra`, 0 violations).
   * The pre-registered `tollis` dataset is fixed to the six fields.
   * `tollis/RESULTS.md` ("not run") is out of date or awaiting an update.
4. **Slack in the central policy.** The Lean reduction (`central_reduction`) needs only wlo ≤ 0 ≤ whi, and only that no
   *open* interval contains 0. The files satisfy the stricter wlo < 0 < whi and t2 < 0 ∨ t1 > 0.
5. **Claim (B) in the replay uses `regions[0]` only** (`replay_target4.py`). Every v4 main certificate has exactly one region,
   so this is harmless; the Lean check covers all regions.

## Flagship K23 to height 10⁴: Lean audit (2026-10-10)

**Outcome: 0 violations.** The 20,000 certificates of L(s, ρ) for K = Q(x³ − x − 1), d_K = −23, were checked:
* 980 flagship windows `diagnostic/flagship_K23/runs/w_<a>`, a = 200 … 9990, with 20 cells each (19,600 certificates);
* the 20 existing Tollis K23 contig chunks `new_territory/tollis/runs/contig/K23/c_<a>_<a+10>` on [0, 200] (400 certificates).

Every per-certificate condition held, and all 1,003 targets × [0, 1/2] are exactly covered. That includes the union
**[0, 10⁴] × [0, 1/2]** over all 1,000 runs. This is the Lean counterpart of P4 in `flagship_K23/RESULTS.md`, which used the
Python `lean_gap_check.py`.

```
cd formal
nice -n 19 python3 audit/export_flagship.py          # -> audit/data_flagship/flagship_K23{,_nc}.txt, flagship_K23_nc.expected (8.9 s, 0.30 GB)
nice -n 19 ~/.elan/bin/lake build atlas_audit         # cached; binary sha256 b77863fc…033db unchanged
nice -n 19 ~/.elan/bin/lake exe atlas_audit audit/data_flagship/flagship_K23.txt audit/data_flagship/flagship_K23_nc.txt
                                                     # output: audit/audit_output_flagship.txt, exit code 0
nice -n 19 python3 audit/mutation_test_flagship.py   # 16/16 single-fault mutations caught (audit/mutation_output_flagship.txt)
```

**Driver.** `audit/export_flagship.py` is new. It imports `export/export_certs.py` unchanged as a module (sha 5ceaaeb1…, as in
SHA256SUMS): no source text is replaced and `main()` is not run. Only the module global `OUT` is set. The driver then calls the
exporter's own `W`, `W.cert`, `W.target`, `deg2_run` and `chunks`.

**No format adaptation was needed.** Flagship certificates have the deg2-family format that `deg2_run` reads:
* `certs/cell_*.json` with `window`, `cell`, `d_range`, `intervals`, an empty `negative_control` and no `central`;
* `replay.json`, where passed means plain AND hardened = CERTIFIED, and the target comes from `summary.target`.

The only departures from `deg2_dataset()` are bookkeeping:
* Group names are paths relative to `diagnostic/`, because the two sources sit in different trees.
* Three union targets are written with explicit names: `union_0_10000` (1,000 groups), `union_0_200` (20 Tollis chunks) and
  `union_200_10000` (980 flagship windows).
* The driver asserts 20 certificates per run, and that each `summary.target` is [a, a + 10].

Cross-check: the 400 Tollis K23 chunk records equal the corresponding records of `audit/data/tollis.txt` as a multiset (group
prefix normalised). The interval count, 1,111,420, equals `flagship_K23/logs/post.json` lean_gap `intervals_checked`. The export
is deterministic: a re-export gave byte-identical files.

| dataset | certificate files | replay-passed | intervals | per-certificate checks | targets exactly covered | violations |
|---|---|---|---|---|---|---|
| flagship_K23 (980 windows + 20 Tollis chunks) | 20,000 | 20,000 | 1,111,420 | 20,000/20,000 | 1,003/1,003 (1,000 runs + unions [0, 10⁴], [0, 200], [200, 10⁴]) | **0** |
| flagship_K23_nc (negative controls) | 49 | 49 | 2,825 | 39/49 | 1/5 | **14, all expected** |

* All target endpoints are integers, so there are no decimal-endpoint slivers (decimal versions: 0/0). No central reductions.
* **Negative controls** (`flagship_K23_nc.txt`, every record marked nc = 1). The 14 expected violations are listed in
  `flagship_K23_nc.expected`, and exactly those 14 were reported.
  * 10 real flagship certificates, each with one structural fault:
    - d-range [0, 0.49];
    - d-range [0.01, 0.5];
    - a cell beyond the window;
    - a reversed cell;
    - an interval leaving the window;
    - two swapped intervals;
    - touching intervals;
    - a reversed interval;
    - a CENTRAL m0 = 2 entry where expect_m0 = 0;
    - a duplicated interval.

    All 10 were caught by the per-certificate checks.
  * Coverage controls built from the real certificates of w_5000 and w_5010, the latter with cell [5010.5, 5011] dropped:
    - [5000, 5010] over w_5000 must be covered, and it is: no false alarm.
    - Four targets must fail, and all four were reported: [5010, 5020] with the missing cell; the union [5000, 5020];
      [5000, 5010 + 2⁻⁴⁰] (sub-ulp overreach); and [5000, 5010] credited to the wrong run.
* **Mutation test** (`audit/mutation_test_flagship.py`, new). The unmutated file is run first and must be clean. Then 16 single
  faults are injected into `flagship_K23.txt`, and all 16 are caught:
  - a dropped flagship certificate;
  - a dropped Tollis certificate;
  - a certificate marked not passed;
  - an interval outside the window;
  - two swapped intervals;
  - touching intervals;
  - d1 = 49/100;
  - d0 = 1/100;
  - a region outside the window;
  - an inserted CENTRAL;
  - a 2⁻⁶⁰ gap between two cells;
  - a degenerate interval with t1 = t2;
  - a certificate moved to another run's group;
  - the union target extended by 2⁻⁴⁰;
  - a certificate marked nc in the real dataset;
  - a duplicated interval.

  A dropped certificate, or a region with the wrong d-range, breaks three targets at once: its window, [0, 10⁴], and [0, 200]
  or [200, 10⁴].
* **Cost.** The binary takes 6.4 s wall and 388 MB peak RSS on both files (`audit/audit_time_flagship.txt`); via `lake exe` it
  takes 7.9 s. The mutation test takes 118 s. The data file is 72 MB, because exact rationals of binary64 values near 10⁴ are long.
* **Trust is unchanged** (see "Trust" above).
  * Every numerical inequality stays trusted Arb: rows, (R) on the 8 × [0, 1/2] boxes generated by `replay_verify.py`, (C),
    the sign of Z at the endpoints (Z1/Z2/Z3), far allowances and N_win.
  * So do the `passed` verdicts in `replay.json`, the exporter and the driver (Python), and the parser.
  * What is Lean-checked: each combinatorial condition, and the exact tiling of [0, 10⁴] × [0, 1/2] by regions of passed
    certificates. Lean proves that these checks imply their statements over ℝ (`Atlas/Audit.lean`).
  * Above t = 700 the Arb sign checks share code with the generator (flagship RESULTS §4). The audit does not change this.
* Nothing under `diagnostic/` was written, except the one appended line in `flagship_K23/RESULTS.md` that points here.
  `audit/data/`, the exporter and the Lean sources are unchanged: their hashes match SHA256SUMS.
