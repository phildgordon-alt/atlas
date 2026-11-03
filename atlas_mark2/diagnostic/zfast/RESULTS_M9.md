# RESULTS_M9: a faster, leaner RH window pipeline (libzfast.v14 + atlas_v5z6/v5z7) before 10²⁵ → 10²⁸ (2026-11-01)

**Pre-registration.** `PREDICTIONS_M9.md`, sha c7ecc70e… (`PREDICTIONS_M9.sha256`), hashed 18:12 before every measurement below. The plan
is `OPTIMIZE_M9.md`. **No 10²⁵ computation was done and w_1e24 was not regenerated.**

**Machine.** M1, 4 P-cores + 4 E-cores, 8 GB. nice 19, one heavy job at a time, footprint watchdogs on. Two non-Atlas `colab drivemount`
processes (~100% of one core each) ran throughout and were left alone, so every timing here is a contended-machine timing.

## 0. Answer first

- **Profile.** At high T the session moment pass is the whole cost: about 4 of them per v5z5 window, against ~300 s of non-session
  work at 10²².
  - Inside a session the per-term kernel takes **96.7%** of the time (50 ns ≈ 160 cycles per term).
  - The rest is per-block Arb work (~3%), the head (0.1%) and point evaluation (ms per point).
  - The kernel streamed its 20 complex moment accumulators through memory on every term.
- **Built: zfast `src/v14` → `bin/libzfast.v14.dylib`** (sha 7abaaa8a…; same build script and flags as v13b).
  - A NEON-register kernel that performs the **same IEEE operations in the same order**: 2.49× on one thread.
  - A work queue on all 8 cores. It keeps v13b's exact decomposition D as a recorded parameter and merges per bucket in v13b's order;
    W, the worker count, is output-free.
  - Exact checkpoint/resume.
  - A parallel Z grid, identical to the serial one.
- **Built: atlas_v5z6, then atlas_v5z7.** Two sessions per window instead of four:
  - the generator's session also writes the Turing grid, and the unchanged `scan_turing5.py recount` counts from it;
  - there is one replay of record.

  v5z7 is v5z6 with two fail-safe resume defects of the driver fixed; both were found by the checkpoint gate (§3). **Use v5z7.**
- **Identity: all bit-identical.**
  - v14 matches the frozen v13b dylib and a build of the frozen v13b *source* on the full session state hash, the Z grid bytes, Z balls
    and rows: 10 cases, D 1/2/4, W 1/3/8, 10¹²–10²⁰.
  - It reproduces M8's 10²¹ 4-thread max_rad exactly.
  - Under v5z6 **and** under v5z7, wide_1e22 is regenerated identically: 100/100 certificates, 777/777 S-layer certificates, zs.json and
    gen_measurements.json byte-identical, replay records identical.
  - Checkpoint: a test-hook exit, a real SIGKILL and a pipeline killed inside its generator session all resume to identical output.
  - Tier 0 and tier 1 are green; the Turing gate is 43/43 and its controls are all detected.
- **Measured speedup (contended machine).**
  - Session at 10²¹: v13b at 4 threads took 197.6 s; v14 with 8 workers takes **64.5 s (3.06×)**. Against v13b on 1 thread it is 9.7×.
  - Full production window [10²², 10²² + 100]: **895 s, against 4,623 s for v5z5's four sessions (5.2×)**. It closes (A) and (B) and
    gives 777 = the Turing count. Peak footprint is 0.25 GB.
- **New projections at 4P+4E** (inference from the measured 3.06×). The v5z5 figures in brackets are for the same machine:

| height | session | window | v5z5 window |
|---|---|---|---|
| 10²⁵ | 1.8 h | **≈ 3.7 h** | 22.2 h |
| 10²⁶ | 5.7 h | **≈ 11.5 h** | ≈ 70 h |
| 10²⁸ (HIK height) | 2.4 days | **≈ 4.7 days** | ≈ 29 days; M8's v5z6 plan was 14.5 days |

- **Needs independent review before claims rest on it:**
  - the v14 kernel and scheduler, which are new trusted code (bit-identity is confirmed mechanically, not by proof review);
  - the checkpoint load path, a new way for numbers to enter a session, guarded by header equality and a SHA-256 per line;
  - nothing changed any error bound, so no precision-theory update was needed.

## 1. Profile (`runs/m9/profile/`)

- **v13b at 10²⁰, 1 thread** (H 61, Δ 0.012, K 18, J 12):
  - build 199.8 s; 3.99·10⁹ terms;
  - 249,847 blocks (mean B ≈ 16,000, bmax binds);
  - head 0.20 s; 2.4 ms per Z point.
- **`sample`** (22,500 samples): `mom_range` self 21,756 (96.7%); FLINT/GMP/MPFR per-block work ≈ 3%.
- **Disassembly** (`_mom_range`): the moment loop loads, adds and stores the (re, im) accumulator pair through the stack on every term.
  The fixed-point phase recurrence is a generic 12 × 4-word loop. cos/sin is already a 2-lane fma chain.
- **Timing ablations of the new kernel** (`src/v14_bench/ablate.c`): 17.7 ns per term in all.
  - Phase recurrence ≈ 8 ns. It is limited by add-with-carry throughput: a fused two-step sweep is exact but was **not** faster
    (7.9 vs 6.8 ns/step) and was dropped.
  - Moments ≈ 5 ns; cos/sin ≈ 2.3 ns.
- **Compiler flags.** -O3 gains about 3% (noise) and was not used: v14 is built with v13b's exact flags.
- **The decomposition constraint.** The output depends on the thread decomposition (M8: max_rad differs at 1/2/4 threads). Every
  scheduling change therefore keeps D, and only the executor changes.

## 2. What was built (new files only; nothing frozen modified, nothing deleted)

| item | files |
|---|---|
| zfast v14 | `src/v14/{zfast.c (= v13b), zfast_m3b.inc (kernel `block_kernel_mom_z20`, `zfm_build`), zfast_sched14.inc (work queue, per-bucket merge, checkpoint), zfast_hash14.inc (state SHA-256), zfast_api14.c (zfa14_new/info/hash/Zgrid), zfast.h}`; snapshot `bin/src_v14/`, `bin/SHA256.v14` |
| test reference | `src/v14_bench/ref13h.c` + `build_ref13h.sh` → `bin/libzfast.ref13h.dylib` (sha d0438135…): the frozen v13b source compiled unmodified, plus the hash only |
| bench | `src/v14_bench/{kbench.c, ablate.c, fxbench.c}` |
| atlas_v5z6 | `tools/make_v5z6.py`, `tools/v5z6_src/zfast_provider.py` → `atlas_v5z6/` (V5Z6_FREEZE.sha256, 34 entries; THEORY_V5Z6.md, run_wide6.sh) |
| atlas_v5z7 | `tools/make_v5z7.py` → `atlas_v5z7/` (V5Z7_FREEZE.sha256, 35 entries; THEORY_V5Z7.md, run_wide7.sh). Byte copies of v5z6 except `atlas_v5.py` |
| gates | `engine/regress_v1/v5z6_gate.py` (`--identity`, `--w1e22`, `--ckpt`, `--tree atlas_v5z6|atlas_v5z7`); `engine/regress_v1/tier_m9.py` (F-M9a) |
| tools | `tools/m9_probe.py` (one session per process: hash, grid, Z, rows), `tools/run_m9_calib.sh` |

- **Provider (v5z6 = v5z7).**
  - D = ZFAST_THREADS, recorded as `zfast_session.threads`. The replay now takes its D from pieces.json.
  - W = ZFAST_WORKERS. ZFAST_CKPT is accepted in strict mode only.
  - `turing_grid()` is scan_turing5's scan logic, verbatim, on the process's own session.
- **Driver.** `--turing-grid` checks that the grid lies inside the session before computing. `--resume` works only while the
  generator's session is being built; old logs and directories are renamed `*.attemptN`, never deleted. Generator and replay have
  separate checkpoints.

## 3. Findings

- **F-M9a (harness, pre-existing).** `python -m engine.regress_v1 --tier 0` has crashed since M7 wrote the Lean dataset
  `v5z5_wide_1e22` (12:36): `lean.v5_datasets` raises StopIteration on the unknown prefix 'v5z5_'. The last green tier 0 was at 11:14.
  - `tier_m9.py` runs the unchanged CLI with in-memory registration only.
  - Scope `golden` is the GOLDEN_v1 scope exactly: **PASS**.
  - Scope `wide` registers v5z5. wide_1e22 checks 1,754/1,754 and Lean passes, but golden lists the two new entries by construction.
  - Proposed permanent fix (not made; harness change = amendment): add ('v5z5_', 'atlas_v5z5') to `lean.TREE_OF_PREFIX` and register
    atlas_v5z5 in `zfast.TREES`, then re-baseline golden by amendment.
- **F-M9b (v5z6 driver, fail-safe).** `gen_workers` was written into pieces.json, so `--resume` with a different ZFAST_WORKERS was
  refused ("run dir has different pieces"). It is fixed in v5z7, which records W in drive.jsonl only.
- **F-M9c (v5z6 driver, fail-safe).** After a generator death the driver still ran the replay, which wrote passed = false, and `--resume`
  reused that replay, so the window ended "not closed".
  - v5z7 runs no replay unless `gen_done` is logged, and reuses a replay only if it passed.
  - Neither defect could produce a false PASS.
  - Recorded failing report: `reports/v5z6_ckpt_20261101_185956.json`. C1–C3 passed there; C4's certs, zs and grid were identical, but
    the replay was stale.
- **F-M9d.** The production parameters (H 91, Δ 0.008) still give 98/100 main certificates, 777/777 S-layer certificates and zs.json
  identical to wide_1e22's (H 61, Δ 0.012). Session radii hardly move the generator's rational choices.

## 4. Predictions: MET / MISS

| # | outcome | verdict |
|---|---|---|
| I1 | `v5z6_identity_20261101_182730`: 9 cases × W ∈ {1,3,8} (10¹² D 1/2/4, 10¹⁶ D 1/2/4, 10¹⁶ legacy H 4 Δ 0.15, 10²⁰ D 2; 10²⁰ D 4 at W 8): state hash, grid, rows, Z all equal to ref13h | **MET** |
| I2 | frozen v13b dylib = ref13h (grid bytes, rows, Z) at 10¹², 10¹⁶ (both parameter sets), 10²⁰ | **MET** |
| I3 | v14 generic kernel (scheduler only, W 4) = ref13h | **MET** |
| NC-I1 | D 1 vs D 2 hashes differ | **MET** (detected) |
| I4 | 10²¹ D 4: max_rad 2.8794749640237427e-09 at W 8, 4 and 1 = M8's 4-thread value; state hash equal across W | **MET** (exact) |
| G1 | `v5z6_w1e22_20261101_184310` (v5z6) and `v5z6_w1e22_20261101_190737` (v5z7): certs 100/100, certs_np 777/777 canonical; replay result + records identical; pieces diff ⊆ {z_provider, zfast_session}, its v5z5 keys equal | **MET** (both trees) |
| G1b | zs.json, gen_measurements.json byte-identical | **MET** (both) |
| C1–C4 | v5z6 (`_185956`): C1–C3 MET, **C4 MISS** (F-M9c; the first attempt `_185654` stopped on F-M9b). v5z7 (`v5z6_ckpt_20261101_190427`): C1 rc 77 → resume, 120/1,459 items loaded, identical; C2 SIGKILL at 310 lines → resume with W 3, 309 items loaded, identical; C3 refused; C4 generator killed (test hook, 200 items) → `--resume` with W 4 → 8 → window identical (certs, certs_np, zs, measurements, replay records, grid bytes) | **MISS on v5z6, MET on v5z7** |
| T0 | `tier0_20261101_181531` (golden scope): 7/7 PASS. Context: plain CLI crashes (F-M9a); wide scope `_181200` PASSes every section except golden (new entries) | **MET** (via wrapper; disclosed) |
| T1 | `tier1_20261101_181728`: PASS (Z1, Z-X, G1, L1, K1) | **MET** |
| TG | `turing_all_20261101_193643`: 43/43 pass. Controls on wide7_1e22 (`turing_controls_20261101_193644`): baseline PASS; NC-T1..T4 all FAIL | **MET** |
| W1 | wide7_1e22 (v5z7): (A) 100/100, (B) 777/777, replay of record passed and passed_B, uncovered [] | **MET** |
| W2 | 777 certified sign changes, 0 straddling | **MET** |
| W3 | recount from the generator's own grid: N(T0) = …886088, N(T0 + 100) = …886865, pinned (U − L 0.474 / 0.469); 777; `turing_check_20261101_193614` PASS | **MET** |
| W4 | 45,001 points, 0 undecided, 1,399 zeros, 0 dips (= scan4_1e22); grid 42 s at W 8 (scan4: 174 s serial) | **MET** |
| W5 | peak 0.248 GB (generator), replay 0.035 | **MET** |
| W6 | recorded: 98/100 + 777/777 identical to wide_1e22 (F-M9d) | (recorded) |
| S1 | 10²¹ W 1: 250.5 s vs 624.4 → **2.49×** (≥ 2.2) | **MET** |
| S2 | 10²¹ W 8: 64.5 s vs 197.6 → **3.06×** (≥ 2.4; predicted 3.0) | **MET** |
| S3 | W 4 84.3 s vs W 8 64.5 s → 1.31× (≥ 1.1) | **MET** |
| S4 | production window 895 s (pipeline 894: generator 584 incl. grid 42; replay 310; recount < 1 s; gate) ≤ 1,500 (predicted 950) | **MET** |
| S5 | 4,623 / 895 = **5.2×** (≥ 3.0; predicted 4.9) | **MET** |
| S6 | 2 sessions per window | **MET** |

**The one MISS is C4 on atlas_v5z6**, the resume path, and it is why v5z7 exists. It is stated plainly: v5z6 must not be used for
resumable runs.

## 5. Cost model and projections (inference)

- **Measured at 10²².**
  - Session ≈ 205 s at W 8. zs takes 281–310 s including the session and 25,655 points.
  - Non-session work ≈ 475 s per window: points, rows (71 s), LP and S-layer (≈ 120 s), grid (42 s), and ≈ 100 s of replay
    verification.
  - It grows only like log T.
- **Scaling.** Sessions scale ∝ √T (M5–M8; linear in Nw to within 2%). The 10²⁵ base is M8's 19,763 s (v13b at 4 threads) ÷ 3.06 =
  6,459 s.

| height | session | window (2 sessions + ≈ 550–700 s) | v5z5 window | per-session checkpoint items (D 2) |
|---|---|---|---|---|
| 10²⁵ | 1.79 h | **≈ 3.7 h** | 22.2 h | ~5k |
| 10²⁶ | 5.7 h | **≈ 11.5 h** | ≈ 70 h | ~5k |
| 10²⁸ | 56.7 h | **≈ 4.7 days** | ≈ 29 days | ~5k (largest item ≈ 2·10¹¹ terms ≈ 1–3 h on one core) |

- **Caveats.**
  - These are contended numbers; without the two spinners, expect roughly 10–25% less (not measured).
  - At 10²⁸ use D = 8–16 so that each item is smaller (finer checkpoints, better tail balance). D is recorded, and the replay inherits it.
  - Disk: about 1 KB per checkpoint line, so negligible.

## 6. Ranked next steps (code-level)

1. **10²⁵ on atlas_v5z7** (`run_wide7.sh`, H 91, Δ 0.008, D 4–8, W 8), after Phil's go.
   - Re-register M8's X1–X13 by amendment: code version v5z7, wall band ≈ 3–6 h.
   - Run the Lean audit afterwards.
2. **Independent review** (review2-style):
   - `bin/src_v14/zfast_m3b.inc` (`block_kernel_mom_z20`, `zfm_build`);
   - `zfast_sched14.inc` (the merge order argument and the checkpoint parser).
3. **F-M9a harness amendment** (lean prefix + tree registration + golden re-baseline), so that the plain `--tier 0` is green again.
4. **Lever c″** (not built): narrow-width phase recurrence.
   - E[i] for i ≥ 4 fits in 192/128/64 signed bits at n ≳ 10⁹, behind a per-block rigorous no-overflow check with a fallback to the
     256-bit path. It is exact integer arithmetic, so the output stays bit-identical.
   - Estimate +10–15%. It needs a written overflow lemma and review.
   - Optional shadow check: recompute 1 block in 1,000 with the generic kernel and abort on mismatch (~0.25% cost); worth adding to v15
     regardless.
5. **Out of scope here.** Hiary's T^{1/3} main sum is the only exponent change. FMA, a larger bmax or fewer Taylor terms would change
   the rounding and need a new written bound.

## 7. Files

- **Docs:** `OPTIMIZE_M9.md`, `PREDICTIONS_M9.md`/`.sha256`, this file, `MANIFEST_M9.sha256`.
- **Data:**
  - `runs/m9/` (profile, calib, identity/w1e22/ckpt logs, tier outputs);
  - `engine/regress_v1/reports/{v5z6_*, tier0_20261101_181200/181531, tier1_20261101_181728, turing_*_193614/193643/193644}.json`;
  - `atlas_v5z6/runs/w1000000000000/smoke_1e12`;
  - `atlas_v5z7/runs/w10000000000000000000000/wide7_1e22`.
- **Regenerations and checkpoint runs:** `engine/regress_v1/work/trees/atlas_v5z{6,7}/runs/`.
- **Untouched:** every frozen tree (v5z5 verified against its freeze by make_v5z6), frozen libzfast.v13b, regress cli/zfast/lean,
  scan_turing5.

Wording: the certification method (zero-list-free, Turing-free explicit-formula certificates) is Atlas's own and new. Only zfast's
evaluation core has prior art (FLINT dfloat); v14 makes that core faster without changing a single output bit. wide7_1e22 is a gate run
at an already-certified height, not a new zero height.
