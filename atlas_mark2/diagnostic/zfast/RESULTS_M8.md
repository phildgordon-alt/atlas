# RESULTS_M8: scan_turing5 and the required Turing gate, a code-independent Z check to 10²², thread scaling, and the 10²⁵ decision (2026-11-01)

**Pre-registration.** `PREDICTIONS_M8.md`, sha 5b117db0… (`PREDICTIONS_M8.sha256`), hashed 15:36 after the calibration. No 10²⁵
computation of any kind was done. There are no amendments.

**Machine.** M1, 4 P-cores and 4 E-cores, 8 GB. nice 19, one heavy job at a time. Two non-Atlas processes (`colab drivemount`, parent
the Codex app, started 11:03 and 11:19) each use about 100% of one core and 13 MB. They are not ours and were not touched. Nothing
else heavy ran (ps).

## 0. Answer first

- **scan_turing5 is exact and reproduces every earlier Turing count.**
  - 36/36 stored records (1e16–1e24, wide_1e22) are reproduced from the saved scans, with N and the 12-digit U/L strings identical.
  - The F-M7a record (wide_1e22, v = 100) now pins at Δ_T = 40: N = …886865, equal to M7-A1.
  - 13/13 Arb crosscheck counts (1e12–1e16, including the 1e15 + 286 pair) are reproduced by fresh scans.
  - The 1e17/1e18 windows get Turing counts for the first time in this project: 11 and 11, equal to the certified sign changes.
- **Turing count-equality is now a required gate** (`engine/regress_v1/turing_gate.py`, amendment A6, re-hashed).
  - All 43 closed zfast windows pass: 1e12–1e24 and wide_1e22.
  - The registered negative control fails the gate as required. It deletes one zero from all 5 covering certificates plus its
    S-layer certificate: 776 ≠ 777. Three further controls also fail the gate as required.
- **The 4e91 Arb ball is diagnosed.** It is not a precision problem; it is radius growth from sequential accumulation.
  - Stock `acb_dirichlet_powsum_smooth` adds about 0.27·N terms into one ball, and mag_t rounds up by about 2^-29 per add.
  - The radius therefore grows like e^{2.2·10⁻⁹·n}: about e^{230} at 1e24, whatever the precision.
- **A new reference that shares no code with zfast** (stock FLINT only, blocked accumulation, 4 threads) agrees with zfast at 1e12,
  1e16, 1e20 and **1e22**:
  - 8/8 points;
  - |diff| ≤ 9e-16, at the double-print limit;
  - every zfast ball contains the reference.

  At 1e22 the point was chosen near a zero (Z ≈ 4.19e-5); the reference radius there is 9.7e-29. That point took 3,588 s at
  4 threads. **1e24 is feasible in memory (< 10 MB) but costs about 12 h per point. It was not run (≤ 1 h budget).**
- **Thread scaling, measured.** 1 → 2 → 4 threads gives 1.00 → 1.98 → **3.16×**. Session cost is linear in Nw to within 2%.
- **The 1e25 window was NOT run: STOP S1.**
  - Projection at 4 threads: 4 sessions × 5.49 h + overhead ≈ **22.2 h**, above the 16 h limit.
  - Without the Turing scan it would still be 16.7 h.
  - Predictions X1–X13 stay registered for an approved run.
- **Plan.** A version v5z6 with 2 sessions per window (the generator's session also writes the Turing grid; no inline replay):
  - 1e25 in about 11 h;
  - 1e26 in about 35 h;
  - 1e28 at HIK's height in about 14.5 days on 4 threads.

## 1. scan_turing5 (`tools/scan_turing5.py`, sha 898bf5c5…)

- **Fix.** v, Δ_T and every endpoint are exact Fractions. The integral runs over exactly [T0 + v, T0 + v ± Δ_T], the divisor is
  exactly Δ_T, and intervals are selected by exact comparison.
- **Δ_T rule.** D = min(40, ⌊v − ulo⌋, ⌊uhi − v⌋), never a clipped float.
- **Formulas.** The Arb θ integrals, the Bober–Hiary bound and the integer extraction are otherwise those of scan_turing2/3/4.
- **Modes.** `scan` makes one zfast session; `recount` works from a saved scan with no zfast call.
- **Code hygiene.** Explicit raises replace asserts; it refuses -O.
- **Validation** (`tools/validate_turing5.py` → `runs/m8/turing5_validation.json`, ok = true):

| part | records | result |
|---|---|---|
| saved scans: scan_1e16 (v1, float N), scan2_1e16/20/21/22/23, turing_extra_1e23 (Δ_T 36/38/40), scan3_1e24, scan4_1e22, turing2_1e22_D39 | 36 records at integer Δ_T + 1 F-M7a record | 36/36 identical (N_lower, N_upper, U, L strings); the v1 floats are equal as floats. F-M7a: scan4 v = 100 was unpinned (U − L 1.35e7); now pinned (U − L 0.469), N = 76106294246675308886865 = the M7-A1 value |
| window counts in those scans | 19 | 19/19 count = sign changes, 0 straddling |
| fresh scans (`runs/m8/fresh/`, 37–79 s each, 2 threads) vs every crosscheck.json Arb count | 13 windows (z/y/x, 1e12–1e16, the pair) | 13/13 identical N at both ends |
| fresh 1e17, 1e18 | — | N(1e17) = 577829042746896155, N(1e17 + 2) = …166; N(1e18) = 6144758226908675409, N(1e18 + 2) = …420; 11 and 11 = the certified sign changes (no earlier Turing record for these windows) |

## 2. The required Turing gate (`engine/regress_v1/turing_gate.py`, sha 25e7972f…; amendment A6)

**Checks.**
- G-T1: the record is from scan_turing5 and its T0 is the run's T0.
- G-T2: both target ends are exact Turing points and both are pinned.
- G-T3: replay and independent replay give passed and passed_B.
- G-T4: the certified intervals are disjoint.
- G-T5: no interval straddles an end.
- G-T6: the Turing count equals the certified sign changes.

**Status.** A6 makes it REQUIRED for v5z5 windows. PREREG_AMENDMENTS.md has the new sha b86ce3b9…; the A5 value is kept in
`PREREG_AMENDMENTS_upto_A5.sha256`. zfast.py and cli.py are unchanged.

- **`all`** (`reports/turing_all_20261101_140532.json`): **43/43** closed zfast windows pass. The 2 failed-closed v5z3 h/hp_1e23 runs
  are skipped, since they carry no claim. The 7 atlas_v5 originals below 1e7 have no Turing record and are out of scope.
- **Controls** (copies under `engine/regress_v1/work/turing_nc_*`): the baseline copy PASSES. Every control FAILS the gate, on
  wide_1e22 (`_140557`) and on w_1e24 (`_140600`):

| control | wide_1e22 outcome |
|---|---|
| NC-T1: the median zero deleted from all main certificates listing it (5: p4700…p5100) and its S-layer certificate (z0388) | FAIL, G-T6: 777 ≠ 776 (replay records would still pass; M7 NC-W4b) |
| NC-T2: N(hi) + 1 | FAIL, G-T6 |
| NC-T3: lower end unpinned | FAIL, G-T2 |
| NC-T4: record from a pre-fix tool | FAIL, G-T1 |

## 3. Code-independent Z (`zcheck_m8/`)

**3a. Diagnosis of the 4.27e91 ball** (M6: `review2/bin/ref` GZ at 1e24, prec 192, 33.8 h).

- **Not the parts.**
  - Theta has radius 3.1e-20 and the Gabcke term 5.3e-32 (GC command).
  - A single stock powsum term at k = 4e11 has radius 4.9e-39 at prec 192 and 7.4e-44 at 208 (`bin/probe_term`).
  - The full stock powsum at 1e24 for N ≤ 1e7 has radius ≤ 3e-29 (`bin/probe_rad`).
- **Mechanism.** In acb_dirichlet_powsum_smooth, every n coprime to 30 adds into the same ball sums[0], about 1.06·10¹¹ adds at 1e24.
  Once the term radii are below one mag ulp of the running radius, each add rounds the radius up.
  - `bin/probe_mag3` (2·10⁸ adds, inexact midpoints) measures a radius growth of exactly e^{c·n} with c = 2.18·10⁻⁹ per add, ≈ 2^-28.8.
  - At 1e24 that is e^{~230}, which gives ~1e70–1e100 from a 1e-30 base. The observed 4.27e91 is in that band.
  - The model also predicts e^{7} at 1e21 and e^{23} at 1e22, which is consistent with the stored 1e20/1e21 agreement.
- **Consequences.**
  - The ball is valid but useless.
  - The precision difference, 192 vs the default 208, is irrelevant.
  - Stock powsum_smooth is unusable from about 1e23.
- **Caveat.** This is not a FLINT correctness bug. It is an accumulation-order effect.

**3b. zref_m8** (`src/zref_m8.c`, sha b413d26d…; binary f1988f5c…).

- **What it is.** Stock FLINT 3.6.0 only, with no zfast code. It runs FLINT's powsum_smooth algorithm, re-implemented with blocked
  accumulation: no ball receives more than about 7·10⁴ sequential adds, so radius growth is below 2e-4.
- **Other parts.** pthreads over chunks of n, several points per pass, and rv_ref's independent Gabcke correction copied verbatim.
- **Comparison.** `compare_m8.py` → `compare_m8.json`, ok = true. The zfast balls come from the saved scan grids at exactly the same u.

| height | points | zref radius | max \|diff\| vs zfast mid | zfast radius | contains / sign | wall |
|---|---|---|---|---|---|---|
| 1e12 | 3 | 5.3e-17 (Gabcke R1) | 2.2e-16 | 7e-12 – 1.5e-11 | yes / agree | < 1 s |
| 1e16 | 3 | 5.3e-22 | 8.9e-16 | 8e-11 – 1.5e-10 | yes / agree | 8 s (4 thr) |
| 1e20 | 2 (one near-zero, Z = −1.73e-4) | 5.3e-27 | 2.8e-16 | 9e-10 | yes / agree | 609 s (4 thr, 2 points) |
| **1e22** | 1 near-zero inside wide_1e22 (u = 65.292, Z = 4.1896e-5) | 9.7e-29 | 3.9e-16 | 3.85e-9 | yes / agree | **3,588 s** (4 thr) |

- **Stock acb_dirichlet_hardy_z** at 1e12/1e16 agrees with zref to ≤ 1.3e-16, inside zref's ball (`runs/stock_az_low.jsonl`).
- **Criterion** (CORE_ROADMAP 3a: radius ≤ 1e-10, |diff| ≤ 1e-13, contained) is **met at 1e22**. |diff| is limited by the 17-digit
  print of the zfast midpoint.
- **1e24.** Memory is not the limit: maxrss is 5.7 MB at 1e22, and N = 4e11 needs the same. The cost is: 0.34 µs CPU per n per point
  → 1.36·10⁵ CPU-s ≈ **12 h per point at 4 threads**.
  - Extra points in the same pass save little, because log n is the shared part and sin/cos dominates.
  - **Not run** (≤ 1 h budget). Max height verified this session: **1e22**.

## 4. Thread scaling (`runs/m8/calib/calib.jsonl`, 1e21, wide session parameters)

| threads | build (s) | speedup |
|---|---|---|
| 1 | 624.4 | 1.00 |
| 2 | 315.0 | 1.98 |
| 4 | 197.6 | 3.16 (CPU 768 s vs 630 s: about 79% efficiency with the 2 spinners present) |

**Linear in Nw.**
- Predicted 996 s vs measured 992 s (1e22, 2 threads).
- Predicted 19,745 s vs measured 20,098 s (1e24, 1 thread).

## 5. The 10²⁵ window: not run (S1)

At 4 threads one 1e25 session is 19,763 s (5.49 h). The v5z5 window with the required gate needs 4 sessions (generator, inline replay,
independent replay, Turing scan), so the projection is ≈ 80,000 s ≈ **22.2 h > 16 h**. Even 3 sessions without the Turing scan (16.7 h)
exceed the limit. The prepared script `tools/run_m8.sh` was **not started**. It checks the hash, then runs the frozen v5z5 driver,
the independent replay, scan_turing5, crosscheck, turing_gate, Lean and tight margins.

## 6. Predictions

| # | outcome | verdict |
|---|---|---|
| X1–X11, X13, NC-X1, NC-X2 | not run (S1 at hashing) | **NOT RUN** (stay registered) |
| X12 (wall) | projection 22.2 h; the window was not run | **NOT RUN**. The projection itself triggered S1 |
| S1 (registered decision) | 22.2 h > 16 h | **APPLIED** |

The §0 disclosures (scan_turing5, the gate, the Z check, the calibration) were facts recorded before hashing, not predictions.
There are therefore no MET/MISS items for them. Against the task's own targets:
- scan_turing5 reproduction: **done**;
- gate + control: **done**;
- Z check at ≥ 1e22: **done at 1e22, 1 point; 1e24 not done (cost)**;
- calibration: **done**;
- 1e25: **not run**.

**MISSes against the task** (stated plainly):
- the 1e25 window, through the cost STOP;
- a code-independent point at 1e24;
- only 1 point at 1e22 rather than "a handful", to stay within the 1 h budget.

## 7. Concrete plan for 10²⁶ and 10²⁸ (inference from the calibration)

1. **v5z6: 2 sessions per window** (new tree from v5z5, gated). This halves every cost below.
   - **Driver change 1.** The generator's wide session uses H = 91, which costs the same, and writes the scan_turing5 grid
     (u ∈ [−40, W + 40], step 0.004), so the Turing count reuses the generator's session.
   - **Driver change 2.** `--no-inline-replay`, so the fresh-process independent replay is the replay of record.
   - **Gate.**
     - v5z5_gate G2/G3 in legacy mode (identical certificates);
     - a wide_1e22 rerun identical in certificates;
     - the Turing count from the shared grid equal to scan4/scan_turing5 (777);
     - turing_gate controls.
   - **Effort:** 1–2 days.
2. **1e25 on v5z6:** 2 × 5.5 h ≈ **11.2 h**. Re-register X1–X13 by amendment (code version).
3. **1e26:** 2 × 17.4 h ≈ **35 h**. Predicted: 924 zeros per 100 units; tight min ≈ 1.00; STOP if tight < 0.45.
4. **1e28 at HIK's y = 10²⁸ + 501675.8:** one session ≈ 7.2 days at 4 threads.
   - v5z6 total ≈ **14.5 days**; v5z5 as-is ≈ 29 days.
   - Expected: about 997 zeros per 100 units; Nw = 3.99e13 < 2^52.
   - A checkpoint/resume facility for the moment pass is advisable for a 7-day process.
   - That build is new (zfast session state saved per block range), but it touches the evaluator and needs review2-style review.
5. **Code-independent Z at ≥ 1e24:** run zref_m8 on 1–3 points of w_1e24 after the next window (≈ 12 h per point, < 10 MB).
   - At 1e28 the O(N) reference costs ≈ 50 days per point. A sub-√T or multi-evaluation reference is needed there (ledger row 336).
   - Cheaper options: exact integer phase reduction, or lower-precision blocks with proven bounds. Both are inference.

## 8. Files

- **New code:**
  - `tools/scan_turing5.py`, `tools/validate_turing5.py`, `tools/calib_threads_m8.py`, `tools/wd_fp_m8.sh`, `tools/run_m8.sh`
    (not run);
  - `engine/regress_v1/turing_gate.py`;
  - `zcheck_m8/src/{zref_m8.c, probe_rad.c, probe_term.c, probe_mag.c, probe_mag3.c}`, `zcheck_m8/compare_m8.py`.
- **Data:** `runs/m8/` (turing5_recount, fresh, calib, turing5_validation.json); `zcheck_m8/runs/`, `zcheck_m8/compare_m8.json`;
  `engine/regress_v1/reports/turing_*.json`.
- **Docs:** `PREDICTIONS_M8.md`/`.sha256`, this file, `MANIFEST_M8.sha256`; amendment A6.
- **Untouched:** nothing frozen was modified, and nothing was deleted. The only exception is two scratch outputs of my own first
  smoke test, rewritten under new names before validation.

Wording: the certification method is Atlas's own and new. Only zfast's evaluation core has prior art (FLINT dfloat). The 1e22
agreement is a code-independent check of zfast values, not a new zero height.
