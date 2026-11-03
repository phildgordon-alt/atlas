# PREDICTIONS_M11: the rigorous window [10²⁶, 10²⁶ + 100] on atlas_v5z7 / libzfast.v14 (amendment A2 of PREDICTIONS_M8)

Written 2026-11-02 before any 10²⁶ computation (sha in `PREDICTIONS_M11.sha256`). Approved by Phil 2026-11-02 (milestone M11).
This file carries PREDICTIONS_M10 (sha 5cd7feb1…, itself amendment A1 of PREDICTIONS_M8 sha 5b117db0…) X1–X13 and NC-X1/NC-X2 to
T0 = 10²⁶ with **the same code, the same parameters and the same run sequence** as M10. Neither earlier file is changed.
A criterion changed after hashing is a further amendment: dated, appended at the end, and disclosed in RESULTS_M11.md.

## 0. Disclosed before hashing

1. **Code.** atlas_v5z7, frozen (V5Z7_FREEZE.sha256, checked by the run script before start), unmodified; libzfast.v14 sha 7abaaa8a…
   (in the freeze list). Tools unchanged from M10: scan_turing5.py, turing_gate.py, export_certs.py, atlas_audit, tight_margin_v1.py,
   crosscheck.py. Run tooling: `tools/run_m11.sh` (= run_m10.sh with T0 = 10²⁶, run name wide7_1e26, log dir runs/m11, projection
   STOP 16 h, plus an environment snapshot before and after) and the unchanged `tools/m10_monitor.py` (no certificate input).
2. **v14 review conditions (review_m10/REVIEW.md, PASS WITH CONDITIONS).**
   - Never resume across any library/OS/Homebrew/FLINT change. The run script writes `runs/m11/env_start.txt` and `env_end.txt`
     (sw_vers, sha256 of libzfast.v14 and of the resolved libflint/libgmp/libmpfr dylibs, `brew list --versions flint gmp mpfr`);
     RESULTS_M11 reports whether they are identical.
   - Generator and replay checkpoints are separate files (RUN/zfast_ckpt_gen.txt, RUN/zfast_ckpt_replay.txt), written by separate
     processes, never cross-loaded.
   - RESULTS_M11 records whether any session resumed. If the **generator** session resumed, the Turing count is flagged (its grid
     would then rest on a resumed session) even if the gate passes.
   - A resume is permitted only with byte-identical env snapshots; it is recorded in RESULTS_M11 and is a disclosed deviation.
3. **Machine state at hashing.** Load ≈ 1.8, 11 GB free disk, no other heavy process. A separate agent is building zfast v14b
   (src/v14b, atlas_v5z8, review_v14b; not touched by this run) and has agreed to do only light work until this run finishes; any
   contention it causes is outside this run's control and will be recorded if seen in monitor.jsonl / load averages.
4. **Computed inputs to the predictions (Arb, python-flint 0.9.0, prec 300).**
   - Smooth term (θ(T0+100) − θ(T0))/π = **923.5656** (± 5e-8). (At 10²⁵ the same computation gives 886.9188, matching M8.)
   - Nw = ⌊√((T0 + c)/(2π))⌋ = **3,989,422,804,014** for every c in [−2, 102] (the same formula gives M10's 1,261,566,261,010).
   - Trudgian |S(t)| ≤ 0.112 log t + 0.278 log log t + 2.510 = 10.353 at 10²⁶.
   - scan_turing5's bound B(x) = 0.128 log x + 2.30 = 9.963 at 10²⁶, so the deterministic part of U − L is 2B/Δ_T = 0.498
     (10²⁵: 0.483, observed 0.548/0.529; 10²² : 0.439, observed 0.474/0.469).

## 1. The run (`tools/run_m11.sh`, nohup, nice 19)

- **Window.** T0 = 10²⁶, target [10²⁶, 10²⁶ + 100], run name `wide7_1e26`,
  run dir `atlas_v5z7/runs/w100000000000000000000000000/wide7_1e26`.
- **Command.** `atlas_v5z7/run_wide7.sh wide7_1e26 T0 T0 T0+100 91 0.008` (default centre 50). H = 91, Δ = 0.008, K = 18, J = 12,
  z span [−2, 102], `--zs-step 0.005`, `--gen-timeout 1209600`, `--turing-grid` (u0 −40, step 0.004, n 45001; Δ_T = 40).
- **Settings.** D = ZFAST_THREADS = **4** (recorded in pieces.json `zfast_session.threads`, inherited by the replay);
  W = ZFAST_WORKERS = **8** (recorded in drive.jsonl); V4_LIM_GB = 1.0; checkpointing on (separate gen/replay files).
- **Watchdog.** m10_monitor.py on the run script's tree: phys_footprint ≤ **3 GB**, disk floor **2 GB**, projection STOP **16 h**.
- **Order.** Pipeline (generator session + Turing grid; replay of record in a fresh process) → scan_turing5 recount of the
  generator's grid → `turing_gate check` (REQUIRED) → crosscheck.py → Lean export `v5z7_wide7_1e26` + atlas_audit →
  tight_margin_v1. Then the controls NC-X1, NC-X2 on copies.

## 2. Predictions (M10 X1–X13 carried to 10²⁶)

| # | prediction | MET iff |
|---|---|---|
| X1 | Claim (A): every piece closes; replay plain + hardened passes all certificates; 0 seams; no d = 0 gaps | all_closed = true |
| X2 | Claim (B): all sign-change intervals covered by passed S-layer certificates | passed_B = true, uncovered = [] |
| X3 | Replay of record in a fresh process, session parameters (incl. D) from pieces.json | replay_check passed and passed_B true |
| X4 | Zero count: smooth term 923.566; central **924**; band **[920, 928]**; rigorous envelope [902, 945] (±2·10.353) | certified sign changes in target in band, 0 straddling, disjoint |
| X5 | REQUIRED Turing gate: both ends pinned by scan_turing5 (recount of the generator's grid), N(T0+100) − N(T0) = certified sign changes | `turing_gate check` PASS |
| X5b | U − L at both ends in **[0.50, 0.60]** (central ≈ 0.55; deterministic part 0.498) | both in band (diagnostic; X5 does not depend on it — pinning needs U − L < 1) |
| X6 | Lean audit (`export_certs.py --v5 v5z7_wide7_1e26` + atlas_audit) | VIOLATIONS 0; all certificates replay-passed; target covered; claim (B) group covered |
| X7 | Reported min_candidate_lower over main pieces: central **0.561** (1e22 0.5806 → 1e25 0.5659, −0.005/decade); band **[0.50, 0.63]** | in band |
| X8 | Tight margin (diagnostic): min central **1.046** (1e22 1.065 → 1e25 1.051); band **[0.95, 1.08]**; median ≈ 1.08; tight ≥ reported on every piece | min in band and tight ≥ reported on 100% |
| X9 | 100 main certificates, ≥ 95 at tier t1; S-layer certificates = intervals (≈ 920–928) | ≥ 95 t1 and np passed = np intervals |
| X10 | Driver-recorded peak_gb of generator and replay ≤ 0.5 GB; monitor tree peak recorded (watchdog 3 GB) | ≤ 0.5 GB |
| X11 | One zfast session per process (strict); Nw = **3,989,422,804,014** (checkpoint header); D = 4, W = 8 recorded | 1 per process and Nw exact |
| X12 | Wall time (D 4, W 8, nice 19), from M10's measured uncontended run scaled by √10 (Nw ratio 3.1623): generator ≈ 16,800 s, replay ≈ 16,400 s → pipeline ≈ **33,200 s**; recount + gate + crosscheck + Lean + tight ≈ 60–300 s; **total ≈ 9.3 h** | generator, replay and pipeline each within ×[0.75, 1.33] of prediction |
| X13 | Generator session (checkpoint file first seen → complete) ≈ 5,180 × 3.1623 = **16,380 s** | within ×[0.75, 1.33] |

### Negative controls (stored data, COPIES under engine/regress_v1/work/; nothing in the run directory touched)

| id | control | MET iff |
|---|---|---|
| NC-X1 | `python -m engine.regress_v1.v5z5_gate --controls RUN`: NC-W1 (w × 1.10), NC-W2 (swapped interval), NC-W3 (w × (1 + 10⁻³)). NC-W4 is reported but not scored (M8 §2; its registered form is NC-T1) | NC-W1: 0 main records pass; NC-W2: ≥ 1 failing main certificate; NC-W3: ≥ 1 main failing both modes; baseline all pass |
| NC-X2 | `python -m engine.regress_v1.turing_gate controls RUN RUN/turing_recount.json` (NC-T1..NC-T4) | every NC-T FAILS and the baseline copy PASSES |

## 3. STOP conditions

- **S1.** From the first checkpoint projection (generator fraction ≥ 2% and ≥ 600 s into the session): projected window =
  2 × projected session + 900 s. If > **16 h**, m10_monitor kills the run tree and writes `runs/m11/STOP`; report, nothing rerun
  under the same name.
- **S2.** A strict-mode raise, the driver's 1.0 GB per-child kill, the 3 GB tree watchdog, or disk < 2 GB → stop and report.
- **S3.** Tight min margin < **0.45**, or any replay failure (plain, hardened) → STOP; no 1e28 preparation; report the failing piece.
- **S4.** Turing gate FAIL → the window is NOT CERTIFIED-COMPLETE. No retry with a changed Δ_T without an amendment.
- **S5.** Env snapshots differ between start and end → the window is reported, but flagged; if a resume happened across the change,
  the resumed session's output is NOT used for any claim (review condition 1).

## 4. Claim status

A pass of X1–X6 with no resume (or a resume with identical env snapshots, disclosed) makes the window **CERTIFIED** on the reviewed
v14 code under the review's interim operating rules, with the same standing as M10's 10²⁵ window.

## 5. To be derived from the measured run (inference, not scored)

Projected 10²⁸ (HIK y = 10²⁸ + 501675.8) window time from the measured 10²⁶ session by √T scaling plus measured non-session work
(M10's projection: ≈ 91 h ≈ 3.8 days), and the margin trend 10²² → 10²⁵ → 10²⁶.

## 6. Wording

The certification method is Atlas's own and new: zero-list-free, Turing-free explicit-formula LP certificates with sign-change
credit, local-count closure, the S-layer, Lean-audited and independently replayed. Only zfast's evaluation core has prior art (FLINT
dfloat). Zeros near 10²⁶ may have been computed before by other methods; this window is a list-free certificate, not a claim of a new
zero height. No "first"/"highest" claim without the separate novelty check.
