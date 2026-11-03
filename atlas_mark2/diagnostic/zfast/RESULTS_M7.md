# RESULTS_M7: atlas_v5z5 (wide-session windows), gate, and the window [10²², 10²² + 100] (2026-11-01)

Pre-registration: `PREDICTIONS_M7.md`, sha 34b28157… (`PREDICTIONS_M7.sha256`, hashed 10:27 before any v5z5 run). One amendment,
M7-A1, was appended after the Turing scan. The amended file's sha is b6e5d916… (`PREDICTIONS_M7_A1.sha256`). Machine: nice 19,
ZFAST_THREADS = 2 throughout, one Atlas job at a time. The side-project NN job (engine2_big) was using one core until about 12:30.

## 0. Answer first

- **The gate passed.**
  - Tier 0 and tier 1 are unchanged.
  - Under v5z5 code, v5z3 x_1e16 and v5z4 w_1e22 are regenerated canonically identical. pieces.json differs only in
    `z_provider` and the new `zfast_session` record.
  - Tier 0 is now fully green, after regress amendment A5 (artin count 2,256, Phil-approved correction).
- **One zfast session now certifies 100 units at 10²².**
  - [10²², 10²² + 100] closes on claim (A) and claim (B): 100/100 main and 777/777 S-layer certificates, replay plain and hardened.
  - The independent replay passes, and the Lean audit reports 0 violations over 877 certificates.
  - **777 zeros**, equal to the Turing count by a separate method: N(T0) = 76106294246675308886088, N(T0+100) = …886865.
- **Cost.** The pipeline took 2,373 s, against 1,927 s for the 2-unit run (1.23×); the independent replay took 1,083 s, against
  961 s. Zeros per wall-hour went from 19.9 to 809, a **40.6× gain**. Peak footprint was 0.22 GB.
- **Margins.** The reported min_candidate_lower is 0.5806 (piece p9600_9700). The **tight minimum is 1.065** and the median tight
  margin is 1.135; tight ≥ reported on 100/100 pieces.
- **Two MISSes, both in diagnostics, not in certificates:**
  - W5 as registered: the Turing tool's Δ_T arithmetic. It is fixed by amendment, and the amended W5 is MET.
  - NC-W4 as registered: the control was badly designed. The post-hoc NC-W4b detects the deletion.

## 1. What was built (new files only; nothing frozen modified)

- **`atlas_v5z5/`**, built by `tools/make_v5z5.py` from atlas_v5z4. It is frozen in `atlas_v5z5/V5Z5_FREEZE.sha256` (32 entries).
  Every lib, model, LP, verifier (verify_zs5 sha 79ca5b16…) and replay file is a byte copy of v5z4. Changed files:
  - `lib/zfast_provider.py` (source `tools/v5z5_src/zfast_provider.py`):
    - H, Δ, K, J and the centre come from env; the defaults are v5z4's.
    - Strict mode raises on a point outside the session, on a second session, or when no centre is given.
    - Explicit raises replace the asserts.
    - It refuses to load under -O or PYTHONOPTIMIZE. Every pipeline process imports it, so the frozen asserts in the copied libs
      always stay active.
  - `atlas_v5.py`:
    - `--wide --zfast-h --zfast-delta [--zfast-center]`;
    - the span must lie inside the session (checked before any compute);
    - `zfast_session` is recorded in pieces.json and summary.json;
    - the full env is recorded in drive.jsonl (ZFAST_CENTER, ZFAST_THREADS, ZFAST_H/Δ/K/J/STRICT, CSTEP, CND, MINW_BINS, ZS_*,
      V4_LIM_GB, test hooks, BLAS threads, python/flint);
    - legacy mode strips session variables from the child env.
  - `replay_target5.py`: the replay session comes from pieces.json, not from the caller's env, and `zfast_env` is recorded in
    replay_check.json.
  - `run_window.sh` (legacy), `run_wide.sh`, `THEORY_V5Z5.md`.
- **Gate:** `engine/regress_v1/v5z5_gate.py` (`--strict`, `--zx`, `--w1e22`, `--controls RUN`). It registers the v5z5 tree in
  memory only; zfast.py and cli.py are unchanged.
- **Diagnostics:** `tools/scan_turing4.py`, `tools/turing_extra2.py` (M7-A1), `tools/run_m7.sh`.
- **Disk:** about 21 MB for the run plus about 30 MB of scan grid. Nothing was deleted.

## 2. Predictions

| # | prediction | outcome | verdict |
|---|---|---|---|
| G0 | tier 0 = last counted run (only the known F-ART fails) | `tier0_20261101_103006`: 6/7 sections, zfast 51/51, golden 0 differing, artin 2,256. After A5, `tier0_20261101_111452`: **7/7 PASS** | MET |
| G1 | tier 1 30/30 | `tier1_20261101_103152`: PASS (Z1 25/25, Z-X, G1, L1, K1), 535 s | MET |
| G2 | v5z5 regenerates v5z3 x_1e16 | `v5z5_zx_20261101_104057`: identical; pieces diff ⊆ {z_provider, zfast_session} | MET |
| G3 | v5z5 regenerates v5z4 w_1e22 (tier 2) | `v5z5_w1e22_20261101_104111`: certs 2/2 and np 16/16 canonically identical; zs.json and gen_measurements.json **byte**-identical; replay check and records identical; mcl 0.7475326795220493; 2,011 s | MET |
| G4 | strict checks: outside, second, no centre, -O / PYTHONOPTIMIZE all raise | `v5z5_strict_20261101_103000`: 6/6 cases | MET |
| W1 | claim (A) | all_closed; 100/100 plain + hardened; seams 0/0; no d = 0 gaps | MET |
| W2 | claim (B) | 777/777 S-layer, uncovered = [], np min 0.8781 | MET |
| W3 | independent replay | passed, passed_B; session from pieces.json (centre 50.0, H 61, threads 2) | MET |
| W4 | 777 zeros, band [774, 780] | 777 certified sign changes in the target, 0 straddling, disjoint | MET |
| W5 | Turing count = sign changes (as registered) | N(T0) pinned and equal to scan2_1e22; **N(T0+100) not pinned** (U − L = 1.35·10⁷) | **MISS** (S4: inconclusive) |
| W5′ | amended (M7-A1): Δ_T = 39 exact, from the saved grid | N(T0) = …886088, N(T0+100) = …886865, both pinned (U − L 0.476 / 0.477); count **777** = sign changes; crosscheck.json match | MET |
| W6 | pipeline ≤ 3,854 s and independent replay ≤ 1,921 s (predicted 2,400 / 1,200) | **2,373 s** (generator 1,288 + replay 1,085) / **1,083 s** | MET |
| W7 | gain ≥ 25× (predicted 39×) | 777 / 3,456 s = 809 /h vs 16 / 2,887.6 s = 19.9 /h: **40.6×** | MET |
| W8 | peak ≤ 0.5 GB | generator 0.217, replay 0.093, independent 0.092 GB | MET |
| W9 | Lean 0 violations | 877 certificates (100 main, 777 np), 877/877 checks, targets 2/2, claim-B group 1/1, **VIOLATIONS 0** | MET |
| W10 | reported min in [0.58, 0.76]; tight min in [1.05, 1.13]; tight ≥ reported | reported **0.5806** (just inside); tight **1.0651**; median tight 1.1352 (predicted ≈ 1.13); tight ≥ reported on 100/100 | MET |
| W11 | one session per process | strict mode was on in all three processes (pieces.json/replay env) and raised nothing; zs alone took 1,065 s including the one build | MET |
| W12 | ≥ 95 pieces at t1; np = intervals | 100/100 at t1; 777 = 777 | MET |
| NC-W1 | w × 1.10 | 0/200 main records pass | MET |
| NC-W2 | swapped interval | 0/200 main pass | MET |
| NC-W3 | w × (1 + 10⁻³) | 0/200 main pass (every certificate's (R) is tighter than 10⁻³ relative) | MET |
| NC-W4 | one interval deleted from one main certificate | replay passes 200/200 and the union count stays 777: **not detected** | **MISS** |

**Controls report:** `engine/regress_v1/reports/v5z5_controls_20261101_123705.json`, overall FAIL because of NC-W4.

**Post-hoc NC-W4b (not pre-registered)** — `reports/v5z5_controls_posthoc_NCW4b.json`:
- **Why NC-W4 missed.** Windows are piece ± 2, so every zero is listed and credited by about 5 neighbouring main certificates.
  Deleting it from one leaves the union count unchanged.
- **The post-hoc test.** I deleted the same zero (u ≈ 54.0557) from all 5 certificates that list it.
- **Result.** The count drops to 776 ≠ 777 (Turing), so the count check detects it. All 200 replay records still pass, which is
  correct: less credit is still a valid certificate.
- **Lesson.** A dropped zero is caught only by the Turing cross-count, which is not part of the certificate. For the HIK-height run,
  that cross-count should be a required gate.

## 3. Findings

- **F-M7a. Turing tool defect.** It was inherited from scan_turing2/3 but harmless there.
  - Lemma T's U and L divide by arb(Δ_T) while integrating over [v, fl(v + Δ_T)].
  - With integer v and Δ_T, as in every earlier run, these are equal.
  - With the grid clip Δ_T = 39.999999999 at v = 100 they are not. The mismatch, times N ≈ 7.6·10²², moved U by 1.4·10⁷.
  - This affects no certificate and no earlier result: every stored Turing count used Δ_T = 40 at integer v.
  - **Fix for future versions:** divide by the exact w = hx(v + Δ_T) − hx(v), or check exactness, as `turing_extra2.py` does.
- **F-M7b. Margin.**
  - The two lowest pieces use 4–5 rows: p9600_9700 (tight 1.065, reported 0.581) and p7000_7100 (1.083 / 0.608), a different dual
    combination.
  - This is the edge-crowding switch documented in MARGIN_ANATOMY §0.2.
  - The worst-case tight margin at 10²² over 100 pieces (1.065) is lower than the 2-piece estimate (1.12). A wide sample finds the
    tail. Even so, the margin projection to 10²⁸ (true slack ≈ 1.0) should be read as "≈ 0.95–1.0 worst case".
- **F-M7c. The cost model held.**
  - The Z scan (25,655 points at Δ = 0.012, including the session build) took 1,065 s, against 958 s for 1,483 points at
    Δ = 0.15.
  - The 802 rows took 72 s, and the LP plus checks for 877 certificates about 220 s.
  - The remaining cost is the session pass: 3 passes per window (generator, replay, independent replay) regardless of width.
- **Env record.** In wide mode, drive.jsonl's `env.ZFAST_CENTER` is null, because the caller sets none. The centre in use is in
  `zfast_session` (pieces.json, summary.json) and in replay_check.json `zfast_env`.

## 4. What the 10²⁸ run needs (inference unless stated)

1. **Session cost.** About 100× the 10²⁴ pass, ≈ 2·10⁶ s single-thread, so about 3 passes plus 1 Turing scan per window. Wide
   windows make width nearly free, so one 100-unit window (≈ 1,060 zeros) costs the same as a 2-unit one.
   - Thread scaling above 2 is unmeasured. Measure it in a 10²⁵ or 10²⁶ dry run, now that the NN job has finished and up to 4 threads
     are allowed.
2. **A code-independent Z check at ≥ 10²²** (CORE_ROADMAP item 3a): diagnose the 4e91 Arb ball first.
3. **A fixed Turing tool** (scan_turing5, with exact Δ_T built in), and the count-equality as a required gate (NC-W4b lesson).
4. **The w_1e24 tier-2 regeneration under v5z5** (11.5 h, Phil's call), if the 10²⁸ run is to cite a gate at 10²⁴.
5. **A memory check of the session at N ≈ 4·10¹³** (buckets ≈ ln N / Δ ≈ 2,600 at Δ = 0.012, small), plus PREDICTIONS_M8 with a
   worst-case tight margin band of about 0.95–1.05.

Wording: the certification method is Atlas's own and new; only zfast's evaluation core has prior art (FLINT dfloat). Zeros near 10²²
have been computed before by other methods; this is a list-free certificate, not a new zero height.
