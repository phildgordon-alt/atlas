# engine/regress_v1: amendments to PREREG.md (sha256 80774906…ecabd)

PREREG.md is unchanged. The amendments below were made after the first counted tier-0 run on 2026-11-01 at 09:30, report
`reports/tier0_20261101_093017.*`. That run's results are kept and reported in RESULTS.md.

## A1 (2026-11-01 09:4x): emulate the frozen replay's precision state in the zfast tier-0 worker

**Finding.** In run 1, v5z2 h_1e22 and v5z3 x_1e22 had one S-layer certificate each (`certs_np/cert_z0008.json`, plain and
hardened) with N_win model-mismatch.

- With that tree's model5, N_win is 49.70631629661506 at ambient 128 bits and 49.70631629661505 at 256 bits.
- The stored value, and v5z4's fixed-precision value, are …505.
- In a real replay, the first `model5.measure` initialises the sech engine, and its `_init` sets `ctx.prec = 256` for the rest of
  the process (certify_sech_interferometer.py line 163). The stored-data substitute skipped that side effect.

This is the documented pre-v5z4 ambient-precision dependence of N_win. Y2 (RESULTS_M5d) had checked only the 92 MAIN
certificates, so this S-layer instance was not covered by it.

**Change.** The stored-measurement function now sets `ctx.prec = 256` on every call, exactly as the frozen measure does.
`--no-a1` reproduces the as-registered procedure.

## A2: harness bug fixes in the historical-manifest check and the Lean comparison

- **Manifest paths.** Manifests resolve relative paths against different bases: their own dir, diagnostic/, atlas_mark2/ or
  formal/. The first existing candidate is now used. Run 1 had reported about 180 false "missing" entries.
- **Superseded entries.** A mismatch is "superseded" (INFO) when the file's current sha256 is recorded for that file by ANY
  manifest. Examples: a later freeze or addendum, such as lmfdb_ecnf CODE_AT_ADDENDUM's version history, or formal/audit
  SHA256SUMS.bak_prev5.
- **INFO, not FAIL.** Append-only `.jsonl` logs (other than `replay.jsonl`) and `atlas_v5z_runner.sha256` (a growing list of runner
  hashes) are INFO.
- **Lean.** For a v5 dataset with no stored audit output (`v5_check_1e14`), the audit-output identity is "not applicable" rather
  than "false". PREREG 2.2(a) already says "where one exists".

## A3: golden baseline

GOLDEN_v1.json is written by the first tier-0 run after A1–A2. The file written by run 1 is kept as `GOLDEN_v1_run1_preamend.json`.

## A4 (2026-11-01 09:48): regenerate with the environment the original run scripts exported

**Finding.** Tier-1 run 1 (`reports/tier1_20261101_093633.*`) found 5 of 8 cheap v5z2 windows not identical: y_1e12, y_1e15,
y_pair_1e15_286, y_1e16 and y_1e17.

- In every one of them, all certificate files, zs.json and the replay results were canonically identical.
- Only gen_measurements.json differed: a few row enclosures differ in the last ulp of one endpoint.
- Cause: atlas_v5z2/run_v2.sh exported `ZFAST_CENTER=1.0` (287.0 for the pair window) and `ZFAST_THREADS=1` through
  run_window.sh's 8th argument. The harness had exported neither.
- A rerun with threads = 1 alone (`reports/tier1_20261101_094542.*`) still differed. Adding the recorded centre made y_1e12
  identical (`reports/tier1_20261101_094803.*`).

**Change.** Regeneration now uses the recorded per-run env (zfast.py RECORDED_CENTER, RECORDED_THREADS), and an inherited
ZFAST_CENTER is removed from the environment.

**Lesson for v5z5.** zfast row enclosures depend on the session centre. The run record (drive.jsonl) must store ZFAST_CENTER and
ZFAST_THREADS, or regeneration identity cannot be checked without reading shell scripts.

## A5 (2026-11-01 ~11:1x): artin_sweep expected count 2,259 → 2,256 (Phil-approved correction)

**Finding.** F-ART (RESULTS.md §2): the stored field summaries and the frozen verifier both give 2,256 fields with d > 2·10⁴
certified in both sets (130 `calegari_published` + 2,126 `calegari_plus_PS`), not the 2,259 of RESULTS_FINAL.md §0. Tier-0 runs
`reports/tier0_20261101_093017`, `_095813` and `_103006` all failed the artin section on this count only.

**Correction source.** Phil approved the correction 2026-11-01. Correction blocks were appended (nothing above edited) to
`diagnostic/artin_sweep/RESULTS_FINAL.md` ("CORRECTION 2026-11-01") and `diagnostic/CORRECTIONS_2026-10-06.md`
("Correction 2026-11-01 (artin_sweep count)").

**Change.** `others.py`: the expected theorem_C count is the constant `EXPECTED_THEOREM_C = 2256` (was the literal 2259). The
expected gaps (5.1.98385.1, 5.1.105177.1) are unchanged. PREREG.md is unchanged; the as-registered value was 2,259. Earlier reports
are kept as written.

## A6 (2026-11-01 ~14:10, M8 step 1): Turing count-equality becomes a REQUIRED gate for atlas_v5z5 windows (new file turing_gate.py)

**Finding.** RESULTS_M7 NC-W4 / NC-W4b: v5z5 pieces overlap (window = piece ± 2), so each zero is credited by about 5 main
certificates. Deleting a zero from one, or from all of them, leaves every replay record passing, because less credit is still a valid
certificate. Only the separate-method Turing count catches it. F-M7a: the Turing tools scan_turing2/3/4 divided by arb(Δ_T) while
integrating over [v, fl(v + Δ_T)], which is wrong for a non-integer clipped Δ_T.

**Change.**
- New tool `diagnostic/zfast/tools/scan_turing5.py`, with exact rational Δ_T and v, the exact divisor, and exact interval selection.
  Validated in `diagnostic/zfast/runs/m8/turing5_validation.json`:
  - 36/36 stored Turing records (scan_turing v1–v4, turing_extra, turing_extra2; 1e16–1e24 and wide_1e22) reproduced from the
    saved scans, with N_lower, N_upper and the 12-digit U, L strings identical;
  - the one F-M7a record (scan4_1e22 v = 100) is now pinned at Δ_T = 40, equal to the M7-A1 value;
  - 13/13 Arb crosscheck counts (1e12–1e16) reproduced by fresh scans.
- New file `turing_gate.py` (zfast.py and cli.py unchanged) with checks G-T1..G-T6. It is REQUIRED for every atlas_v5z5 window from
  M8 on: a window whose gate fails is reported NOT CERTIFIED-COMPLETE, whatever its replay says.
- `turing_gate.py all` over every closed zfast window: 43/43 pass (reports/turing_all_20261101_140532.json). The 7 atlas_v5
  originals below 1e7 have no record and are out of scope.
- Controls NC-T1..NC-T4 (copies under work/) must all FAIL the gate, and they do on wide_1e22 and on w_1e24
  (reports/turing_controls_20261101_140557.json, _140600.json):
  - NC-T1: one zero deleted from all 5 covering main certificates and its S-layer certificate → 776 ≠ 777;
  - NC-T2: N(hi) + 1;
  - NC-T3: an end unpinned;
  - NC-T4: a record from a pre-fix tool.

PREREG.md is unchanged.

## A7 (2026-11-02 ~06:15, M10 step 1): plain `--tier 0` no longer crashes on Lean datasets of trees outside GOLDEN_v1 scope (F-M9a)

**Finding.** RESULTS_M9 F-M9a: since M7 wrote `diagnostic/zfast/atlas_v5z5/lean_audit/v5z5_wide_1e22.txt` (2026-11-01 12:36),
`python -m engine.regress_v1 --tier 0` stopped in `lean.v5_datasets` with a bare StopIteration: no entry of `TREE_OF_PREFIX`
matched the prefix 'v5z5_'. The last green plain tier 0 was 2026-11-01 11:14. M9 worked around it in memory (`tier_m9.py`).
Every later tree (v5z6, v5z7, including M10's 1e25 export) would hit the same crash.

**Change** (lean.py, cli.py; PREREG.md, zfast.py, FROZEN.json and GOLDEN_v1.json unchanged):
- `lean.TREE_OF_PREFIX` names the later trees: ('v5z7_', 'atlas_v5z7'), ('v5z6_', 'atlas_v5z6'), ('v5z5_', 'atlas_v5z5').
- `lean.v5_datasets` skips a dataset whose tree is not in `zfast.TREES` and lists it in `lean.SKIPPED_OUT_OF_SCOPE`. The tier-0 scope
  is therefore exactly the GOLDEN_v1 / FROZEN.json scope (atlas_v5 .. atlas_v5z4, record_heights), as registered. A dataset with no
  known prefix now raises RegressError instead of a bare StopIteration.
- `cli.tier0` reports the skipped datasets as top-level `lean_out_of_scope` (not a section, outside the golden hash).
- The out-of-scope trees keep their own required gates: v5z5_gate.py, v5z6_gate.py (identity, w1e22, ckpt), turing_gate.py (A6).

**Not done (disclosed).** Registering atlas_v5z5/6/7 inside tier 0 itself would need a FROZEN.json v2 and a GOLDEN_v2 re-baseline.
That is a larger amendment and was not made here.

**Hashes.** lean.py 2450a629… → 6813d0b6…; cli.py b359909c… → 5bf9c485…. The A6 hash of this file (b86ce3b9…) is kept in
`PREREG_AMENDMENTS_upto_A6.sha256`.

**Validation.** Plain `python -m engine.regress_v1 --tier 0` → `reports/tier0_20261102_061427.json`: PASS, 7/7 sections
(frozen_integrity, historical_manifests, zfast_tree_freeze, zfast_windows, lean_audit, artin_sweep, golden = GOLDEN_v1 identical),
106 s; lean_out_of_scope = [v5z5_wide_1e22]. Turing gate `all` → `reports/turing_all_20261102_061616.json`: 43/43 PASS.
