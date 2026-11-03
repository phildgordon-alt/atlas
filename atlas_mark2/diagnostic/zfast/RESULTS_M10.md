# RESULTS_M10: the rigorous window [10²⁵, 10²⁵ + 100] on atlas_v5z7 / libzfast.v14, and the regress_v1 tier-0 fix (2026-11-02)

**Pre-registration.** `PREDICTIONS_M10.md`, sha 5cd7feb1… (`PREDICTIONS_M10.sha256`), hashed 06:21 before any 10²⁵ computation. It
re-registers PREDICTIONS_M8 (sha 5b117db0…) X1–X13 and NC-X1/NC-X2 for v5z7/v14. There were no amendments after hashing.

**Machine.** M1, 4P + 4E cores, 8 GB. The two non-Atlas `colab drivemount` processes were stopped earlier on 2026-11-02 with Phil's
approval (ATLAS_STATUS), so this run's timings are **uncontended**, unlike M8/M9. nice 19, one heavy job at a time (the parallel v14
review used ≤ 2 threads). Footprint watchdog: driver per-child 1.0 GB, plus `tools/m10_monitor.py` on the whole process tree (3 GB).

## 0. Answer first

- **10²⁵ window: CERTIFIED, pending v14 review.**
  - Target [10²⁵, 10²⁵ + 100] (run `atlas_v5z7/runs/w10000000000000000000000000/wide7_1e25`).
  - Claim (A): all 100 pieces closed, 100/100 main certificates replay-passed (plain + hardened), 0 seams, no d = 0 gaps.
  - Claim (B): 888/888 sign-change intervals covered by passed S-layer certificates.
  - **888 certified sign changes** (predicted 887, band 883–891), 0 straddling, disjoint.
- **Turing count equal.** scan_turing5 recount of the generator session's grid:
  - N(10²⁵) = 87100328229866724999179370, N(10²⁵ + 100) = 87100328229866724999180258;
  - both pinned (U − L 0.548 / 0.529); difference **888** = certified sign changes;
  - `turing_gate check` PASS. crosscheck.py: match.
- **Lean audit:** 988 certificates (100 main + 888 S-layer), 988/988 per-certificate checks, targets covered 2/2, claim (B) group
  1/1, **VIOLATIONS 0**.
- **Margins.**
  - Reported min_candidate_lower **0.5659** (p3900_4000; predicted 0.56, band 0.50–0.66).
  - Tight min **1.051** (same piece; band 0.95–1.08); median 1.086; tight ≥ reported on 100/100.
  - Against wide_1e22 (0.5806 / 1.065), both fall by about 0.005 per decade.
- **Wall time: 10,870 s ≈ 3.02 h** for everything (pipeline 10,831 s: generator 5,588 s, replay of record 5,243 s; recount,
  gate, crosscheck, Lean and tight together about 40 s).
  - Session builds: generator ≈ 5,180 s, replay ≈ 5,138 s (M9 projection 6,459 s, so 0.80×).
  - M8 needed a projected 22.2 h for this window on v5z5.
- **Peak memory.** Generator 0.248 GB and replay 0.033 GB (driver); replay verifier 0.105 GB. Whole process tree peak 0.29 GB.
- **No session was resumed.** drive.jsonl has `"resume": false` and no resume_generator/resume_replay stage. Each checkpoint file
  was written once, from item 0 to 6,142/6,142, by its own process: generator → `zfast_ckpt_gen.txt`, replay →
  `zfast_ckpt_replay.txt`, distinct paths. **The review's M1/M2 checkpoint gaps therefore did not arise in this run.**
  - No library, OS, Homebrew or FLINT change was made during the run.
  - The Turing grid comes from an uninterrupted generator session.
- **Every registered prediction is MET (13/13 + NC-X1 + NC-X2).** There are no MISSes. One disclosure: the generic v5z5_gate
  `--controls` report says FAIL, because its NC-W4 is not detected. M8 removed NC-W4 from the pass/fail controls (§3).
- **Harness fixed.** Plain `python -m engine.regress_v1 --tier 0` is green again: **7/7 PASS** (amendment A7, F-M9a).
- **Projections from this measured run** (uncontended; inference):
  - 10²⁶ ≈ **9.3 h**;
  - 10²⁸ (HIK height) ≈ **3.8 days**.

## 1. Harness fix (regress_v1 amendment A7)

- **Cause.** `lean.v5_datasets` raised a bare StopIteration on Lean dataset names with no `TREE_OF_PREFIX` entry. The first was
  'v5z5_wide_1e22', written by M7; M10's 'v5z7_wide7_1e25' would have hit the same crash.
- **Fix.**
  - The prefixes v5z7_/v5z6_/v5z5_ are now named.
  - Datasets of trees outside `zfast.TREES` (the GOLDEN_v1/FROZEN.json scope) are skipped and reported as top-level
    `lean_out_of_scope`, outside the golden hash.
  - An unknown prefix now raises RegressError.
  - Files: `engine/regress_v1/lean.py` (2450a629… → 6813d0b6…) and `cli.py` (b359909c… → 5bf9c485…).
  - PREREG_AMENDMENTS.md re-hashed to f3bacbc4…; the A6 hash is kept in `PREREG_AMENDMENTS_upto_A6.sha256`.
- **Runs.**
  - `reports/tier0_20261102_061427`: PASS 7/7 (frozen_integrity, historical_manifests, zfast_tree_freeze, zfast_windows,
    lean_audit, artin_sweep, golden), before the run.
  - `reports/tier0_20261102_092526`: PASS 7/7 after the run, with out-of-scope = [v5z5_wide_1e22, v5z7_wide7_1e25].
  - Turing gate `all`: `reports/turing_all_20261102_061616`, 43/43.
- **Not done (disclosed).** Bringing v5z5/6/7 inside tier 0 itself needs FROZEN.json v2 and GOLDEN_v2 (a larger amendment). Until
  then those trees are gated by v5z5_gate, v5z6_gate and turing_gate.

## 2. Run record

- **Command.** `tools/run_m10.sh` under nohup → `atlas_v5z7/run_wide7.sh wide7_1e25 10^25 10^25 10^25+100 91 0.008`.
  - Default centre 50; K 18, J 12; zs-step 0.005; Turing grid u0 −40, step 0.004, n 45001; Δ_T 40.
  - **D = ZFAST_THREADS = 4** (in pieces.json `zfast_session.threads`), **W = ZFAST_WORKERS = 8**, V4_LIM_GB 1.0.
  - V5Z7_FREEZE checked 35/35 OK at start (`runs/m10/freeze_check.txt`). libzfast.v14 sha 7abaaa8a….
- **Checkpoint header (both sessions identical by design, M2).** Nw = 1,261,566,261,010; nb 2951; nhead 88793; nitems 6142; D 4.

**Timeline.**

| time | event |
|---|---|
| 06:21:19 | start |
| 06:31:59 | first projection: 10.5% of terms after 608 s → session 5,772 s, window 12,444 s, far under the 10 h STOP |
| 07:47:54 | generator session complete |
| 07:49:47 | zs.json written (zs stage 5,307 s incl. session; 26,333 evaluations, 922 intervals in span) |
| 07:54:27 | Turing grid and generator done (100 main pieces, all tier t1; 888 S-layer) |
| 07:54:28–09:20:05 | replay session |
| 09:21:50 | replay done (5,243 s); recount and gate |
| 09:22:29 | Lean + tight done |

## 3. Predictions: MET / MISS

| # | outcome | verdict |
|---|---|---|
| X1 | all_closed true; 100/100 passed plain + hardened; seams 0; gaps_d0 [] | **MET** |
| X2 | passed_B true; np 888/888; uncovered []; np min margin 0.8756 | **MET** |
| X3 | replay of record (fresh process, D 4 from pieces.json): passed and passed_B true; failed [] | **MET** |
| X4 | 888 in [883, 891]; 0 straddling; disjoint (crosscheck) | **MET** |
| X5 | both ends pinned, U − L 0.548 / 0.529 (≤ 0.6; predicted 0.48–0.55); 888 = 888; `reports/turing_check_20261102_092150` PASS | **MET** |
| X6 | `lean_audit/audit_v5z7_wide7_1e25.txt`: VIOLATIONS 0; 988/988 replay-passed and checked; targets 2/2; claim (B) 1/1 | **MET** |
| X7 | reported min 0.5659 in [0.50, 0.66] | **MET** |
| X8 | tight min 1.051 in [0.95, 1.08]; median 1.086 (≈ 1.09); tight ≥ reported 100/100 (`runs/m10/tight_v1_wide7_1e25.jsonl`) | **MET** |
| X9 | 100/100 at t1 (≥ 95); np passed 888 = intervals 888 | **MET** |
| X10 | generator 0.248 GB, replay 0.033 GB (≤ 0.5); tree peak 0.29 GB | **MET** |
| X11 | one strict session per process (generator, replay); Nw = 1,261,566,261,010 exactly | **MET** |
| X12 | generator 5,588 / 6,900 = 0.81; replay 5,243 / 6,600 = 0.79; pipeline 10,831 / 13,500 = 0.80 (band 0.75–1.33) | **MET** (low side; uncontended machine, as disclosed in the prereg) |
| X13 | generator session ≈ 5,180 s / 6,459 = 0.80 (band 0.75–1.33) | **MET** |
| NC-X1 | `reports/v5z5_controls_20261102_092402`: baseline 1,976/1,976 pass; NC-W1 0/200 main pass; NC-W2 100 main certificates failing; NC-W3 100 failing both modes | **MET** |
| NC-X2 | `reports/turing_controls_20261102_092355`: baseline PASS; NC-T1..T4 all FAIL the gate | **MET** |

**Disclosure on NC-X1.** The v5z5_gate tool's overall verdict is FAIL because of NC-W4 (one interval deleted from one main
certificate). That leaves the main records passing and the count at 888, because about 5 overlapping certificates credit each zero.
This is M7's NC-W4b lesson. M8 §2 removed NC-W4 from the pass/fail controls, and its registered form is NC-T1, which is detected
here.

**STOP conditions.** None triggered: first projection 3.5 h < 10 h; tight min 1.051 > 0.45; no replay failure; Turing gate PASS.

## 4. Claim status and the v14 review

- **Review verdict.** The independent review (`review_m10/REVIEW.md`, sha f3ba1b2a…) is **PASS WITH CONDITIONS**.
  - Kernel and scheduler PASS: 20 differential sessions, 0 mismatches.
  - No critical findings.
  - Two MAJOR checkpoint findings:
    - **M1:** the header does not pin Lb/Xb/nbeg/tau0, the library build or the FLINT version;
    - **M2:** generator and replay checkpoint headers are byte-identical.
- **How the conditions were met in this run.**
  1. No OS, Homebrew, FLINT or library change was made during the run.
  2. The generator and replay checkpoints are distinct paths (`zfast_ckpt_gen.txt`, `zfast_ckpt_replay.txt`), each written by its
     own process and never cross-loaded.
  3. **No session was resumed, so the M1/M2 gaps did not arise.** The Turing count rests on an uninterrupted generator session.
- **Status.** This window is **CERTIFIED, pending v14 review closure**. The review found nothing that can underestimate a radius in a
  non-resumed v14 session, but the headline is held until Phil accepts the review. The M1/M2 fixes go into a future new version
  (v14b), not into v14.

## 5. Projections from the measured run (inference)

| quantity | basis |
|---|---|
| session | 5,180 s at 10²⁵ (D 4, W 8, uncontended); sessions scale ∝ √T (M5–M9) |
| non-session work | generator 408 s, replay ≈ 105 s, post ≈ 40 s. It grows like log T. Take 600 s. |

| height | one session | window (2 sessions + ≈ 600 s) | M9 projection (contended) |
|---|---|---|---|
| 10²⁶ | 16,380 s = 4.55 h | **≈ 9.3 h** | 11.5 h |
| 10²⁸ (HIK y = 10²⁸ + 501675.8) | 163,800 s = 45.5 h | **≈ 91 h ≈ 3.8 days** | 4.7 days |

- **Caveats.**
  - If background load like M8/M9's returns, add about 25%.
  - At 10²⁸ use D = 8–16 for finer checkpoints (M9).
  - Because a multi-day session will plausibly be resumed, **the M1/M2 fixes (v14b) should land before 10²⁸**, or the interim
    rule applies: never resume across a library/OS change.
- **Margins.** The 10²⁸ margins are an extrapolation at −0.005/decade (reported 0.566 → ≈ 0.55; tight 1.051 → ≈ 1.03). STOP
  stays at tight < 0.45.

## 6. Files

- **Docs:** `PREDICTIONS_M10.md`/`.sha256`, this file, `MANIFEST_M10.sha256`.
- **Run tools:** `tools/run_m10.sh`, `tools/m10_monitor.py`.
- **Run:** `atlas_v5z7/runs/w10000000000000000000000000/wide7_1e25/` (certs, certs_np, zs.json, gen_measurements.json,
  replay_check/, turing_grid, turing_recount.json, crosscheck.json, both checkpoints) and `atlas_v5z7/runs/wide7_1e25.out`.
- **Lean:** `atlas_v5z7/lean_audit/{v5z7_wide7_1e25.txt, audit_v5z7_wide7_1e25.txt, export_v5z7_wide7_1e25.log}`.
- **Logs:** `runs/m10/` (m10.log, monitor.jsonl, tight_v1_wide7_1e25.jsonl, freeze_check.txt).
- **Reports:** `engine/regress_v1/reports/{tier0_20261102_061427, tier0_20261102_092526, turing_all_20261102_061616,
  turing_check_20261102_092150, turing_controls_20261102_092355, v5z5_controls_20261102_092402}`.
- **Untouched:** every frozen tree (v5z4–v5z7 code, v13b, v14), `review_m10/`, w_1e24 (not regenerated). Nothing was deleted.

## 7. Wording

- **The method is Atlas's own and new.** The certification method is zero-list-free explicit-formula LP certificates with
  sign-change credit, local-count closure and the S-layer, Lean-audited and replayed in a fresh process. It is Atlas's own and new.
- **Prior art.** Only zfast's evaluation core has prior art (FLINT dfloat).
- **What this window is.** Zeros near 10²⁵ have been computed before by other, non-rigorous methods (Odlyzko/Gourdon-type lists,
  Bober–Hiary). This window is a list-free certificate, not a new zero height. It does not "extend H" and is not "beyond Odlyzko".
  No "first" claim is made without a novelty check.
