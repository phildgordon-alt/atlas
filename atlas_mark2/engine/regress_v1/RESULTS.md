# engine/regress_v1: results (2026-11-01)

**Pre-registration.**
- `PREREG.md`: sha256 80774906…ecabd, hashed 09:27 before any counted run. PREREG §2.2 says 31 v5 datasets; the actual count is 33 (miscount in the pre-registration).
- `PREREG_AMENDMENTS.md`: A1–A4, each made after a finding and disclosed below. Its sha256 is in `PREREG_AMENDMENTS.sha256`.

**Snapshot.** `FROZEN.json` holds 68,153 files (sha256 498228e3…, `FROZEN.sha256`), written once at 09:28.

**Command.** `python -m engine.regress_v1 --tier 0|1`, `--controls`, `--list-tier2`, run on the Atlas venv (python-flint 0.9.0 /
FLINT 3.6.0).

**Constraints held.** nice 19, ≤ 2 threads, 3 GB footprint watchdog, one job at a time. Nothing was written outside
`engine/`: a `find -newer PREREG.md` over diagnostic/ and formal/ is empty apart from the unrelated nn_float_verify job.

## 1. Bottom line

| check | result |
|---|---|
| Tier 0, final run `reports/tier0_20261101_095813` (107 s wall) | **6 of 7 sections PASS; artin_sweep FAILS on a count** (§3) |
| zfast windows, tier 0 | **51/51 runs pass**: 106 main + 571 S-layer certificates, 1,354 plain/hardened records. Pass/fail and min_candidate_lower are **bit-identical to the stored independent-replay records in 1,354/1,354** |
| Lean audit, tier 0 | **PASS**. 33/33 v5 re-exports are byte-identical: zfast 27, record_heights 4, data_v5 2. The audit binary reproduces all 30
per-dataset stored outputs plus the combined data_v5 output byte-identically, with 0 violations. One dataset, v5_check_1e14, has
no stored output. Base export: 11/11 byte-identical, audit output identical. Flagship export: 3/3 identical, audit output identical |
| Integrity | 68,153/68,153 frozen files unchanged. 59 historical manifests (14,092 entries): 0 hard mismatches, 12 superseded entries, 6 INFO (append-only logs and md) |
| Tier 1, final run `reports/tier1_20261101_094820` (551 s) | **PASS, 30/30**. Z1: 25/25 windows regenerated canonically identical (252 certificate files, plus pieces, zs, gen_measurements and replay results). Z-X (v5z4 code on v5z3 x_1e16): identical, with pieces.json differing only in `z_provider`. G1 geval_c 4/4, L1 level1 1/1, K1 flagship w_2640 20/20 cells plus intervals/rows/summary |
| Negative controls `reports/controls_20261101_095741` | **10 of 11 detected.** NC3 (perturbed measurement) was NOT detected by the replay layer, as pre-registered (§4) |
| Golden | GOLDEN_v1.json was written by run 2. Run 3 compared against it: 0 differing |

## 2. Findings, as found (frozen code not touched)

- **F-A1. Precision side effect (amendment A1).** In run 1, one S-layer certificate (`certs_np/cert_z0008.json`) in each of
  v5z2 h_1e22 and v5z3 x_1e22 had an N_win model mismatch.
  - That tree's model5 gives N_win = 49.70631629661506 at ambient 128 bits and …505 at 256 bits. The stored value and v5z4's
    fixed-precision value are …505.
  - This is the pre-v5z4 ambient-precision dependence. Y2 (RESULTS_M5d) checked only the 92 main certificates, so it extends to
    at least this S-layer certificate at 1e22.
  - It is not a soundness problem: the real replay runs at 256 bits after the sech engine starts, and it passed. Under v5z4 the
    value is deterministic.
  - Emulating that side effect in the stored-data worker (A1) made every one of the 1,354 records match the stored replay
    exactly. This also covers the failed-closed v5z3 h/hp_1e23 runs.
  - It also refutes my pre-registration guess that the w_1e24 margin difference came from replay re-measurement: precision
    state was the cause.
- **F-A4. Recorded environment matters (amendment A4).** In tier-1 run 1, 5/8 cheap v5z2 windows differed, in gen_measurements.json
  only (last-ulp row enclosures). Certificates, zs and replay results were identical.
  - Cause: run_v2.sh exported `ZFAST_CENTER=1.0` (287.0 for the pair) and `ZFAST_THREADS=1`. drive.jsonl does not record either.
  - Using the recorded env made 25/25 identical.
  - **Requirement for v5z5:** store ZFAST_CENTER and ZFAST_THREADS in drive.jsonl/pieces.json.
- **F-ART. artin_sweep headline count NOT reproduced.** RESULTS_FINAL.md §0 says **2,259** fields with d > 2·10⁴ are certified in
  both sets. The frozen verifier (verify_sweep_v3, output redirected) and a direct count of the stored field summaries both give
  **2,256**: 130 `calegari_published` + 2,126 `calegari_plus_PS`.
  - The two gaps are confirmed as stated (5.1.98385.1, 5.1.105177.1).
  - Two further DONE/all-certified summaries have d ≤ 2·10⁴. That makes 2,128 PS records "in this directory", which matches the
    route table of §1, but they are outside the d > 2·10⁴ claim.
  - The stored data therefore support 2,256 (d > 2·10⁴), or 2,258 field records in total. 2,259 looks like a count error in
    RESULTS_FINAL.md. **I have not edited RESULTS_FINAL.md**; this needs an erratum, at Phil's call.
  - The verifier's d_max_contiguous is 98,369, which stops at the first gap. That is consistent with "contiguous with 2 gaps".
  - The artin section will keep failing until the expected count in the harness, or the claim, is corrected.
- **Historical manifests.**
  - 12 entries are superseded: a file's current sha is recorded by a later manifest (e.g. lmfdb_ecnf CODE_AT_ADDENDUM version
    history, formal/audit SHA256SUMS.bak_prev5 → exporter changed for `--v5`, tollis diag_tollis.py).
  - The 6 INFO entries are logs that grew (m6.log, compare_v1.jsonl, queue_v1.jsonl, enum13_ng12.log, tollis RESULTS.md and
    SUMMARY.log).
  - No certificate, data or code file has drifted from every manifest.

## 3. Per family

| family | tier 0 (stored data) | tier 1 (regeneration) | tier 2 (listed, not run) |
|---|---|---|---|
| zfast atlas_v5 originals (10 runs) | 10/10 | 8/8 (incl. big_1e12, 123 s) | big_1e13, big_1e14 |
| record_heights v5run (3) | 3/3 | — | big_1e15, pair, big_1e16 (≈ 1–2.5 h each) |
| atlas_v5z (8) | 8/8 | 8/8 (1e12–1e18 + pair) | — |
| atlas_v5z2 (14) | 14/14 | 8/8 (after A4) | h/hp 1e20–1e22 |
| atlas_v5z3 (9, 2 failed-closed) | 9/9 (h/hp_1e23 reproduce NOT closed and every stored per-certificate outcome) | 1/1 | x/xp 1e20–1e22, h/hp 1e23 |
| atlas_v5z4 (7, incl. 1e24) | 7/7 | Z-X cross-version 1/1 | w_1e22 … wp_1e24 (11.5 h each at 1e24) |
| Lean audit (formal/) | PASS (all byte-identical) | — | — |
| flagship_K23 + ext | integrity 47,520 files; Lean flagship identical | K1 w_2640 identical | the other 1,979 windows (≈ 60 s each) |
| geval_c | integrity | G1 5.1.22352.1: 4/4 canonical-identical to the scored V8 .r2 files and to the artin_sweep base files | other V-runs |
| geval_stream | integrity | — (writes into its own tree; needs a copy wrapper) | V-runs |
| artin_sweep | **FAIL: 2,256 vs 2,259** (§2) | — (queue_v3 writes queue logs; needs a root wrapper) | queue rerun |
| level1 | integrity | L1 k = 12 identical | other weights |
| races, races2 | integrity | — (generators overwrite their own data/; need a copy) | regeneration |

**Deviation from PREREG §3 G1.** PREREG says "all 8 files". The runner writes 4 certificate files. All 4 are identical against
both reference sets, which makes 8 comparisons.

The Z sign-change check is not repeated in tier 0. It needs a zfast session at height T0, so it is exercised only in tier 1
(Z1/Z-X, up to 1e18) and in tier 2.

## 4. Negative controls

| id | result |
|---|---|
| NC1: 1-ulp tamper of y on a copy | detected (sha changed, golden changed) |
| NC2: w × 1.10 | detected: 0/20 and 0/38 records pass |
| NC3: stored Ehi − 1e-3 | **NOT detected by the replay layer**: 20/20 and 38/38 still pass |
| NC4: wrong y | detected: 0/20 and 0/38 |
| NC5: swapped zero interval | detected: 0/20 and 4/38, not closed |
| NC6: zs_step × 2 regeneration | detected: not identical |
| NC7: altered Lean export endpoint | detected: audit rc 1, 1 violation |

**Why NC3 is not caught, and why that is not a soundness gap.** Lowering Ehi lowers K, so the certificate gets easier. The margin
rises by exactly 1e-3, because Σy = 1. Tier 0 trusts stored measurements by construction; the pre-registered prediction was wrong.

**Post-hoc check NC3b** (`reports/controls_posthoc_NC3b.json`): the golden comparison catches the same perturbation on both runs.
A perturbed gen_measurements.json on disk would also fail the sha check. Only tier 1/2 re-measurement validates a measurement
itself.

## 5. Costs

- **Tier 0:** about 107 s wall.
  - integrity 10 s, manifests 4 s;
  - zfast 33 s (51 runs, ≤ 0.04 GB each);
  - Lean 42 s (the flagship audit is 6 s at 0.38 GB);
  - artin 17 s.
- **Tier 1:** about 9 min.
- **Disk:** each tier-0 run leaves about 150 MB of scratch exports under `work/t0_*`. These are caches that can be cleaned; nothing
  was deleted.

## 6. Before atlas_v5z5 (and bounds_v1) can use the gate

1. **v5z5 must record its run environment.** Put ZFAST_CENTER and ZFAST_THREADS into drive.jsonl/pieces.json (F-A4). Then add its
   tree to `zfast.TREES` and its cheap windows to tier 1.
2. **Add a "v5z5 reproduces v5z4" item on the Z-X pattern.** v5z5 code on frozen windows at H = 4, WM = 2 must give identical
   certificates, and pieces.json may differ only in the provider string.
   - v5z4 has no cheap windows of its own. Its cheapest frozen window, w_1e22, takes about 32 min per regeneration (tier 2).
   - So the gate for v5z5 is: Z-X-style cross-version runs on cheap heights, plus one tier-2 regeneration of w_1e22, and of w_1e24
     if the generator path changes (11.5 h; Phil's call).
3. **Resolve F-ART.** Either correct RESULTS_FINAL.md's 2,259 or tell me it is right. Then set the expected count, so tier 0 can
   go fully green.
4. **bounds_v1.** Implement PREREG §6 (B1) as `--module bounds_v1`: identity with Trudgian pinned, unchanged y and margins with
   Platt–Trudgian. Read the PDFs first.
5. **Wrappers for the families that write into their own trees** (geval_stream, artin queue, races/races2), so they can join
   tier 1. Also a scratch-cleanup option.

## 7. What was checked and what is inference

- **Checked:** everything in the tables above, by running it. Reports are in `reports/`.
- **Inference:**
  - that the 2,259 is a counting error, rather than a missing field file;
  - that the last-ulp enclosure differences come from the zfast session centre and are rigorous either way. The y_1e12 rerun with
    the centre restored became identical, which supports this but does not prove the mechanism.
