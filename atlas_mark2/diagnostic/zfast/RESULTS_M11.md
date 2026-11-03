# RESULTS_M11: the rigorous window [10²⁶, 10²⁶ + 100] on atlas_v5z7 / libzfast.v14 (2026-11-02)

**Pre-registration.** `PREDICTIONS_M11.md`, sha 57d9729e… (`PREDICTIONS_M11.sha256`), hashed 09:46 before any 10²⁶ computation;
the run script re-checked the hash at start (OK). It carries PREDICTIONS_M10 X1–X13 and NC-X1/NC-X2 to 10²⁶ with the same code,
parameters and sequence, adds X5b (U − L band) and S5 (environment snapshots). **No amendments after hashing.**

**Machine.** M1, 4P + 4E cores, 8 GB, uncontended (no other heavy process seen; the v14b agent did light work only). nice 19, one
heavy job. Watchdogs: driver per-child 1.0 GB, `tools/m10_monitor.py` on the whole tree (3 GB, disk floor 2 GB, projection STOP 16 h).

## 0. Answer first

- **10²⁶ window: CERTIFIED** on the reviewed v14 code under the review's interim operating rules (same standing as M10's 10²⁵).
  - Target [10²⁶, 10²⁶ + 100], run `atlas_v5z7/runs/w100000000000000000000000000/wide7_1e26`.
  - Claim (A): 100/100 pieces closed, 100/100 main certificates replay-passed (plain + hardened), 0 seams, no d = 0 gaps.
  - Claim (B): every sign-change interval covered by passed S-layer certificates (924/924 passed, uncovered []).
  - **924 certified sign changes** (predicted 924, band 920–928; smooth term 923.566), 0 straddling, disjoint.
- **Turing count equal.** scan_turing5 recount of the generator session's grid:
  - N(10²⁶) = 907650062242638637035433072, N(10²⁶ + 100) = 907650062242638637035433996;
  - both pinned, U − L **0.512 / 0.519**; difference **924** = certified sign changes;
  - `turing_gate check` PASS (`reports/turing_check_20261102_185658`). crosscheck.py: match.
- **Lean audit:** 1,024 certificates (100 main + 924 S-layer), 1,024 replay-passed, targets covered 2/2, claim (B) group 1/1,
  **VIOLATIONS 0**.
- **Margins.** Reported min_candidate_lower **0.5629** (p7100_7200). Tight min **1.0481** (same piece), median 1.078,
  tight ≥ reported on 100/100. Trend 10²² → 10²⁵ → 10²⁶: reported 0.5806 → 0.5659 → 0.5629, tight 1.065 → 1.051 → 1.048
  (about −0.004 per decade).
- **Wall time: 33,072 s ≈ 9.19 h** (script start 09:46:33 → done 18:57:45; predicted ≈ 9.3 h). Pipeline 33,025 s:
  generator 16,640 s, replay of record 16,385 s; recount, gate, crosscheck, Lean and tight together ≈ 47 s. Controls afterwards ≈ 105 s.
  - Session builds: generator 16,225 s (zfa14_info sec_build), replay ≈ 16,272 s (checkpoint first → last write).
  - Measured 10²⁵ → 10²⁶ session ratio 16,225 / 5,180 = 3.13 (√10 = 3.16): √T scaling holds.
- **Peak memory.** Generator 0.258 GB, replay 0.033 GB (driver); whole tree 0.288 GB (monitor). Disk never below 10.4 GB free.
- **No session was resumed.** drive.jsonl `"resume": false`, one generator and one replay_target stage, no resume stage.
  - Generator session record (`turing_grid/scan_turing.json` session): **items_loaded 0**, items 6,696, D 4, workers 8.
  - The generator writes `zfast_ckpt_gen.txt` (created 09:46:34, last write 14:16:59). The replay writes `zfast_ckpt_replay.txt`
    (created 14:23:54 by the replay process itself, after the generator had exited; last write 18:55:06). These are distinct paths.
    Each file holds exactly 6,696 item lines and has no duplicate (bucket, item) pairs.
  - The replay's own items_loaded is not written to any record (this is review finding M2; v14b will add it). Its checkpoint file did not
    exist before the replay process created it, so there was nothing for it to load.
  - **Environment snapshots identical** at start and end: macOS 27.0 (26A428); libzfast.v14 7abaaa8a…; FLINT 3.6.0, GMP 6.3.0,
    MPFR 4.2.2 dylib hashes; python-flint 0.9.0 (`runs/m11/env_start.txt`, `env_end.txt`). No library, OS or Homebrew change.
  - The Turing grid comes from an uninterrupted generator session: **no flag on the Turing count.**
- **Every registered prediction is MET (13/13 + X5b + NC-X1 + NC-X2). No MISSes.**
  - Disclosure 1: NC-W4 is not detected, as at M10. It is unscored per M8 §2, and its registered form NC-T1 is detected.
  - Disclosure 2: the X9 interval count. The replay record says intervals_to_cover 925 because it counts (main certificate, interval)
    pairs. One interval, [42.999921875, 43.0], ends exactly on the boundary between pieces p4200_4300 and p4300_4400 and is counted
    for both (checked directly: 924 distinct intervals, 925 pairs). 924 distinct intervals = 924 S-layer certificates passed.

## 1. Run record

- **Command.** `tools/run_m11.sh` under nohup → `atlas_v5z7/run_wide7.sh wide7_1e26 10^26 10^26 10^26+100 91 0.008`.
  - Default centre 50; H 91, Δ 0.008, K 18, J 12; zs-step 0.005; Turing grid u0 −40, step 0.004, n 45001; Δ_T 40.
  - **D = ZFAST_THREADS = 4** (pieces.json `zfast_session.threads`), **W = ZFAST_WORKERS = 8** (session record workers 8),
    V4_LIM_GB 1.0. V5Z7_FREEZE checked OK at start (`runs/m11/freeze_check.txt`).
- **Checkpoint header (both sessions identical by design, review M2).** Nw = 3,989,422,804,014; nb 3095; nhead 106000; nitems 6696;
  D 4; wp 421.
- **zs scan.** 26,567 evaluations, 961 intervals in the span [−2, 102].

**Timeline.**

| time | event |
|---|---|
| 09:46:33 | start (load 2.4, 11 GB free) |
| 09:57:24 | first projection: 3.1% of terms after 615 s → session 19,622 s, window 40,143 s (11.2 h), under the 16 h STOP |
| 14:16:59 | generator session complete (sec_build 16,225 s) |
| 14:23:53 | generator done (100 main pieces, all t1; 924 S-layer; Turing grid) |
| 14:23:54–18:55:06 | replay session |
| 18:56:58 | replay done (16,385 s); recount + gate PASS |
| 18:57:45 | crosscheck, Lean export/audit, tight done; env snapshot identical |
| 18:59 | NC-X2, NC-X1 controls (on copies) |

The first projection overestimated, as at M10 (12,444 s projected against 10,870 s actual): early checkpoint items are the long ones.

## 2. Predictions: MET / MISS

| # | outcome | verdict |
|---|---|---|
| X1 | all_closed true; 100/100 passed plain + hardened; seams 0 (hull and target); gaps_d0 [] | **MET** |
| X2 | passed_B true; np 924/924 passed both modes; uncovered []; np min margin 0.8731 | **MET** |
| X3 | replay of record (fresh process, D 4 from pieces.json): passed and passed_B true; failed [] | **MET** |
| X4 | 924 in [920, 928] (central 924); 0 straddling; disjoint (crosscheck) | **MET** |
| X5 | both ends pinned; 924 = 924; `turing_check_20261102_185658` PASS | **MET** |
| X5b | U − L 0.512 / 0.519 in [0.50, 0.60] | **MET** |
| X6 | `lean_audit/audit_v5z7_wide7_1e26.txt`: VIOLATIONS 0; 1,024/1,024 replay-passed; targets 2/2; claim (B) 1/1 | **MET** |
| X7 | reported min 0.5629 in [0.50, 0.63] (central 0.561) | **MET** |
| X8 | tight min 1.0481 in [0.95, 1.08] (central 1.046); median 1.078 (≈ 1.08); tight ≥ reported 100/100 (`runs/m11/tight_v1_wide7_1e26.jsonl`) | **MET** |
| X9 | 100/100 at t1 (≥ 95); np passed 924 = 924 distinct intervals (see disclosure 2) | **MET** |
| X10 | generator 0.258 GB, replay 0.033 GB (≤ 0.5); tree peak 0.288 GB | **MET** |
| X11 | strict provider (a second session raises), one session per process; Nw = 3,989,422,804,014 exactly; D 4, W 8 recorded | **MET** |
| X12 | generator 16,640 / 16,800 = 0.99; replay 16,385 / 16,400 = 1.00; pipeline 33,025 / 33,200 = 0.99 (band 0.75–1.33) | **MET** |
| X13 | generator session 16,225 / 16,380 = 0.99 | **MET** |
| NC-X1 | `reports/v5z5_controls_20261102_185910`: baseline 2,048/2,048 records pass (200/200 main); NC-W1 0/200 main pass; NC-W2 100 main certificates failing; NC-W3 100 failing both modes. NC-W4 not detected (unscored, as M10) | **MET** |
| NC-X2 | `reports/turing_controls_20261102_185901`: baseline PASS; NC-T1..T4 all FAIL the gate | **MET** |

**STOP conditions.** None triggered: first projection 11.2 h < 16 h (S1); no strict raise, kill, or disk floor (S2); tight min
1.048 > 0.45 and no replay failure (S3); Turing gate PASS (S4); env snapshots identical (S5).

## 3. Projections from the measured run (inference)

| quantity | basis |
|---|---|
| session | 16,225 s at 10²⁶ (D 4, W 8, uncontended); ∝ √T (measured 10²⁵ → 10²⁶ ratio 3.13) |
| non-session work | generator 415 s, replay ≈ 113 s, post ≈ 47 s; slowly growing; take 700 s |

| height | one session | window (2 sessions + ≈ 700 s) |
|---|---|---|
| 10²⁸ (HIK y = 10²⁸ + 501675.8) | 162,250 s = 45.1 h | **≈ 325,200 s ≈ 90.3 h ≈ 3.8 days** |

- Margins at 10²⁸, by linear extrapolation of the three measured points (−0.004/decade): reported ≈ 0.55, tight ≈ 1.04. STOP stays
  at tight < 0.45. Turing at 10²⁸: deterministic U − L part 2B/Δ_T = 0.528, so pinning (needs < 1) has ample room at Δ_T = 40.
- **Conditions for 10²⁸.** A 3.8-day session will plausibly need a resume, so land v14b (review M1/M2: environment digest plus
  role/nonce in the checkpoint header, replay records items_loaded) before 10²⁸, or keep the interim rule: never resume across a
  library/OS change. Consider D = 8–16 for finer checkpoints (M9). If background load returns, add about 25%.

## 4. Files

- **Docs:** `PREDICTIONS_M11.md`/`.sha256`, this file, `MANIFEST_M11.sha256`.
- **Run tools:** `tools/run_m11.sh` (new; `tools/m10_monitor.py` reused unchanged).
- **Run:** `atlas_v5z7/runs/w100000000000000000000000000/wide7_1e26/` and `atlas_v5z7/runs/wide7_1e26.out`.
- **Lean:** `atlas_v5z7/lean_audit/{v5z7_wide7_1e26.txt, audit_v5z7_wide7_1e26.txt, export_v5z7_wide7_1e26.log}`.
- **Logs:** `runs/m11/` (m11.log, monitor.jsonl, env_start.txt, env_end.txt, freeze_check.txt, tight_v1_wide7_1e26.jsonl, nc_x1.log,
  nc_x2.log).
- **Reports:** `engine/regress_v1/reports/{turing_check_20261102_185658, turing_controls_20261102_185901, v5z5_controls_20261102_185910}`.
- **Untouched:** every frozen tree (v5z4–v5z7 code, v13b, v14), review_m10, the v14b agent's directories (src/v14b, atlas_v5z8,
  review_v14b), w_1e24 (not regenerated). No library or Homebrew change. Nothing deleted.

## 5. Wording

- **The method is Atlas's own and new:** zero-list-free explicit-formula LP certificates with sign-change credit, local-count closure
  and the S-layer, Lean-audited and replayed in a fresh process. The Turing count is a separate required gate.
- **Prior art.** Only zfast's evaluation core has prior art (FLINT dfloat). Lemma 2 and THEORY_V4 §10 have no external review.
- **What this window is.** It is a list-free certificate, not a claim of a new zero height. No "first"/"highest" claim is made; a
  novelty check is being done separately.
