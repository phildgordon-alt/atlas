# engine/regress_v1: pre-registration (2026-11-01)

The harness that every future engine change must pass. It reproduces the frozen certificates and fails loudly when it cannot.
It is the gate for atlas_v5z5 (wide windows) and engine/bounds_v1. Approved by Phil 2026-11-01; spec source ADDITIONS_SCOPE.md §3.

This file is hashed (`PREREG.sha256`) before any counted run. A changed criterion after hashing is an amendment: dated, appended
below, and disclosed in RESULTS.md.

**Disclosed before hashing.** While building the code I ran smoke tests on four runs: tier 0 on z_1e12, lehmer, h_1e23 and w_1e24, and
tier 1 on lehmer (tag `smoke0`). They checked code paths, not outcomes. Two things they showed shaped §2.1 (c) and (f) below:
- **The w_1e24 margin moves.** Stored-measurement re-verification of w_1e24 cert_p100_200 gives min_candidate_lower
  0.7609682508238599, against 0.7609682507656522 in the stored replay record. The replay re-measures its rows, and some of its row
  enclosures differ from the generator's in the last digits.
- **The failed v5z3 1e23 run disagrees with its stored replay.** The failed-closed v5z3 h_1e23 run does not reproduce its stored
  per-certificate outcome, because of the N_win ambient-precision bug that was fixed in v5z4.

Neither smoke test is counted.

## 1. What "identical" means

- **Canonical JSON:** `json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=True)`. Floats are Python repr, so
  binary64 is compared bit-exactly.
- **Two certificates are identical** when their canonical texts are equal after removing only the volatile keys listed for their
  family. Nothing numeric is ever volatile: no intervals, y, w, ids, regions, Nwin, min_candidate_lower, boxes, or enclosure
  strings.
  - zfast certificates: `gen_seconds`.
  - zfast replay records: `seconds` and absolute paths (the `cert` path reduced to its basename).
  - geval_c: the frozen compare_c1 DROP regex,
    `^(t_.*|t|time.*|maxrss.*|src|stream|gs_stats|xcap|old_json|sparse_file|rows_file|local_file|pari_json|wd.*)$`.
  - level1: `t_exact`, `t_total`, `maxrss_MB`, `t_*`.
  - flagship cells and intervals.json: `seconds`, `t_*`, `time*`.
- **Byte identity** (sha256) is required for:
  - every frozen file listed in FROZEN.json, which is written once by `--freeze` before the first counted run and never rewritten;
  - Lean exporter output against the stored export;
  - the Lean audit binary's stdout against the stored audit output.
- **Golden identity.** The first counted tier-0 run writes GOLDEN_v1.json: canonical sha of every tier-0 record set, which
  includes intervals, margins, sign-change counts, model-match flags and geometry. Every later run must reproduce GOLDEN_v1.json
  exactly. Any difference is a FAIL, with the differing ids listed.

## 2. Tier 0: re-verify from stored data (cheap; run on every change)

### 2.1 zfast windows, atlas_v5 format (51 runs; 106 main + S-layer certificates)

Covers atlas_v5 originals (10 runs), record_heights/v5run (3), and zfast atlas_v5z (8), v5z2 (14), v5z3 (9) and v5z4 (7).

Per run, each with its own frozen code tree:
- **(a) Integrity.** The sha256 of every file in certs/ and certs_np/ equals FROZEN.json, and so do pieces.json, zs.json,
  gen_measurements.json, summary.json, crosscheck.json, and replay_check{,_independent}/{replay_check.json,replay.jsonl,exact_heights.json}.
  Every file in the tree's own *_FREEZE.sha256 still matches it.
- **(b) Replay from stored data.** This uses the tree's own frozen `lib/replay5.replay` and the sha-pinned verify_zs5 (plain and
  hardened by 2 ulps), plus the in-memory no-parity verifier for the S-layer. Two substitutions are made:
  - rows (Elo, Ehi) come from the stored gen_measurements.json;
  - the Z sign-change check is skipped, because it needs a zfast session at height T0 (it is covered by tier 1 and tier 2).

  Model, N_win, the far bound F and the (R)/(C) Arb bisection are recomputed by the frozen code.
- **(c) Comparison with the stored replay records.** Pass/fail must agree for every certificate and mode. Identity of
  min_candidate_lower is reported, together with max |Δ|. It is not a pass criterion, because the stored replay re-measured its rows
  (see the disclosure above).
- **(d) Geometry.** Recomputed from the certificates that pass tier 0 in both modes, using the pinned exact_tiling_check.py (sha 0868990e…):
  - hull and target × [0,½] tiled with 0 seams;
  - the d = 0 sweep has no gaps;
  - claim (B): every sign-change interval of a main certificate is covered by S-layer regions.
- **(e) Sign-change counts.** The number of sign-change intervals inside the target equals the stored crosscheck.json's
  `atlas_sign_changes_in_target` and its Arb Turing `arb_count`, where crosscheck.json exists.
- **(f) Pass rules.**
  - For runs recorded `all_closed: true`: every record passes, with no model mismatch, no missing measurement, (c) pass-flags
    equal, (d) closed with claim (B), and (e) agreeing.
  - For the 2 runs recorded NOT closed (v5z3 h_1e23, hp_1e23; failed closed, not claim-bearing): tier 0 must also find NOT
    closed.

### 2.2 Lean audit inputs and outputs (formal/, binary built 2026-10-08)

- **(a) v5 exports.** There are 31 stored datasets:
  - zfast lean_audit/*: 8 + 6 + 7 + 6;
  - record_heights/lean_audit: 4;
  - formal/audit/data_v5: 2.

  For each, re-export into engine/ scratch with `python3 export/export_certs.py --v5 DATASET OUTDIR RUN_DIR...`, giving the run
  dirs in the order of the stored file. The export must be byte-identical to the stored export.
  Then run `.lake/build/bin/atlas_audit` on the STORED export. Its output must be byte-identical to the stored audit output where
  one exists, and must report `TOTAL VIOLATIONS (non-control datasets): 0`.
- **(b) Base audit.** Run `export_certs.py OUTDIR` into scratch. Every file except tollis_ext_unions.txt (made by another tool) must
  be byte-identical to formal/audit/data/*. Then run atlas_audit on the stored base list
  (`{deg2,ec37a,ec389a,tollis,tollis_extra,tollis_ext_unions,v4_acceptance,v4_other}.txt` + `{deg2,ec37a,ec389a,tollis}_nc.txt`).
  Its output must equal audit/audit_output.txt.
- **(c) Flagship.** Run `audit/export_flagship.py OUTDIR` into scratch; the result must be byte-identical to
  audit/data_flagship/*. Then run atlas_audit on the stored flagship files; its output must equal
  audit/audit_output_flagship.txt.

### 2.3 artin_sweep

Run the frozen `verify_sweep_v3.py` (reads JSON only) with its output files redirected into engine/ scratch. The tree is never
written. Expected, from RESULTS_FINAL.md §0:
- theorem_C holds for **2,259** fields with d > 2·10⁴;
- the only DONE-but-not-certified fields are 5.1.98385.1 and 5.1.105177.1.

Any other count is reported plainly as a non-reproduction.

### 2.4 Integrity of every other family

- FROZEN.json (sha256 snapshot at freeze time) covers the certificate files of:
  - flagship_K23 and _ext (cells, intervals, replay);
  - geval_c and geval_stream runs/cert;
  - artin_sweep runs/{cert,field,alg_v2};
  - level1 runs;
  - races data, races2 runs;
  - formal/audit;
  - plus the families of §2.1.
- **Historical manifests.** Every pre-existing SHA256SUMS / *_FREEZE / CODE_AT_* / CODE_SHA256* manifest in these families is
  re-checked.
  - A mismatch on a certificate, data or code file (`.json`, `.py`, `.c`, `.h`, `.dylib`, `.lean`, `.txt` under data/audit) is a
    FAIL.
  - A mismatch on a log or markdown file is reported as INFO, since append-only logs grow.

## 3. Tier 1: sampled regeneration (seconds to minutes; run before any engine change is used)

- **Z1. Every zfast window whose recorded wall time is ≤ 120 s: 25 runs.**
  - atlas_v5: t4v4, big_1e12, t2_663318, rosser, c7002, lehmer, lehmer_full_pair, v1_9000;
  - v5z: 1e12–1e18 + pair;
  - v5z2: 1e12–1e18 + pair;
  - v5z3: x_1e16.

  Each is re-run from a byte copy of its own frozen tree (sha-checked against the tree's FREEZE file) under
  engine/regress_v1/work/, with its recorded arguments. This includes the Z sign-change check, the row re-measurement and replay.
  Pass requires canonical identity of every certs/ and certs_np/ file and of pieces.json, zs.json and gen_measurements.json, plus
  identical replay_check.json results and identical replay records.
- **Z-X. Cross-version: current production code (v5z4) regenerates v5z3's x_1e16** (same libzfast v13b), compared with the frozen
  v5z3 files. Pass requires:
  - canonical identity of every certificate and of gen_measurements.json and zs.json;
  - pieces.json may differ ONLY in the `z_provider` string, and replay results must be identical.

  This is the template for the v5z5 gate.
- **G1. geval_c**, `review/rcert.py <scratch> 5.1.22352.1 --tag _V8`. All 8 files must be canonically identical (DROP rule) to
  runs/cert/{k10,FE}_5.1.22352.1_{A,B}.r2.json (the scored geval_c V8 files) and to the base files (artin_sweep originals).
- **L1. level1**, `run_weight.py 12 gen <scratch>`. Must be canonically identical to runs/A_gen/k0012.json.
- **K1. flagship_K23**, `gen_cert.py K23 2640 2650 <scratch> --intervals iv.json` (cwd flagship_K23). Must be canonically identical
  to runs/w_2640 (certs/cell_*.json, intervals.json).

## 4. Negative controls (each must FAIL; pre-registered)

All mutations are made in memory or on copies under engine/. Frozen files are never touched.

| id | control | expected detection |
|---|---|---|
| NC1 | tampered certificate: copy of z_1e12, with cert_p0_100.json's y[0] changed by 1 ulp | integrity FAIL (sha) and golden FAIL (the stored-data check may still certify; that is why integrity exists) |
| NC2 | tampered certificate: every credit weight w × 1.10 (worker `--tamper-cert`), on z_1e12 and w_1e24 | tier-0 replay FAIL |
| NC3 | perturbed measurement: every stored Ehi lowered by 1e-3 (`--perturb-meas`), on z_1e12 and w_1e24 | tier-0 replay FAIL |
| NC4 | wrong y vector: the upper duals permuted (`--wrong-y`), on z_1e12 and w_1e24 | tier-0 replay FAIL |
| NC5 | swapped zero interval: one sign-change interval replaced by the gap between it and the next (`--swap-interval`), on z_1e12 and w_1e24 | tier-0 FAIL (replay or geometry) |
| NC6 | regeneration with a changed parameter (zs_step × 2) on z_1e12 | tier-1 identity FAIL |
| NC7 | Lean: a stored export with one interval endpoint altered (copy) | audit output differs from stored and/or violations > 0 |

A control that does not fail is reported as a harness defect.

## 5. Tier 2: listed, not run now

- 26 zfast windows with recorded wall > 120 s:
  - atlas_v5 big_1e13/14;
  - record_heights 1e15/1e16/pair;
  - v5z2 1e20–1e22;
  - v5z3 1e20–1e23;
  - v5z4 1e22–1e24. The 1e24 runs take about 11.5 h each.
- Full flagship windows (about 60 s each, ×1,980).
- The artin_sweep queue rerun, geval_stream V-runs, and races/races2 regeneration (they write into their own trees, so they need a
  copy wrapper).

## 6. Future test for bounds_v1 (registered now, NOT implemented)

**B1.** engine/bounds_v1 will provide count_upper / far_bound with a selectable S(T) constant.
- **With Trudgian 2014 pinned**, tier 0 + Z1 + Z-X must be identical (golden).
- **With Platt–Trudgian 2015 selected**, every main certificate must stay CERTIFIED, with y and min_candidate_lower unchanged,
  because y_c = 0 and y_low = 0 in every main certificate (ADDITIONS_SCOPE F1). Only N_win and F change, by about −0.56 at 1e24.

The harness will run this as `--module bounds_v1 --st-constant platt_trudgian_2015`. The constants must be read from the PDFs
before use.

## 7. Operating rules

- Use the Atlas venv (python-flint 0.9.0 / FLINT 3.6.0).
- The harness refuses to start if `sys.flags.optimize != 0` or PYTHONOPTIMIZE is set, or if free disk is below 2 GB.
- One heavy process at a time, nice 19, ≤ 2 threads (ZFAST_THREADS=2, BLAS 1), footprint watchdog 3 GB, and any single job over
  1 h is killed.
- The harness writes only under engine/.
