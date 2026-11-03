# PREDICTIONS_M10: the rigorous window [10²⁵, 10²⁵ + 100] on atlas_v5z7 / libzfast.v14 (amendment A1 of PREDICTIONS_M8)

Written 2026-11-02 before any 10²⁵ computation (sha in `PREDICTIONS_M10.sha256`). Approved by Phil 2026-11-02 (milestone M10).
This file re-registers PREDICTIONS_M8 (sha 5b117db0…) X1–X13 and NC-X1/NC-X2 for a new code version, as M8 §3 requires ("if a later
amendment changes the code version, it must state which X-criteria carry over"). PREDICTIONS_M8.md itself is unchanged.
A criterion changed after hashing is a further amendment: dated, appended at the end, and disclosed in RESULTS_M10.md.

## 0. Disclosed before hashing

1. **Harness fix (regress_v1 amendment A7, F-M9a).** `lean.TREE_OF_PREFIX` names v5z5/v5z6/v5z7; Lean datasets of trees outside the
   GOLDEN_v1 scope are skipped and reported (`lean_out_of_scope`), and an unknown prefix raises RegressError. Plain
   `python -m engine.regress_v1 --tier 0` → `reports/tier0_20261102_061427.json`: **PASS 7/7** (golden identical to GOLDEN_v1).
   `turing_gate all` → `reports/turing_all_20261102_061616.json`: 43/43 PASS. PREREG_AMENDMENTS.md re-hashed to f3bacbc4….
2. **Code.** atlas_v5z7, frozen (V5Z7_FREEZE.sha256: 35/35 OK at 06:17), unmodified; libzfast.v14 sha 7abaaa8a…. Tools:
   scan_turing5.py 898bf5c5…, turing_gate.py 25e7972f…, export_certs.py 5ceaaeb1…, atlas_audit b77863fc…, tight_margin_v1.py 09c31584….
   The v5z7 verifiers (lib/replay5.py, verify_zs5.py, verify.py, sech5.py, heights.py, replay_target5.py, crosscheck.py) are byte-identical
   to atlas_v5z5's, so the M8 controls apply unchanged.
3. **Machine state at hashing.** The two non-Atlas `colab drivemount` processes present during M8/M9 are **not running** (ps, 06:13 and
   06:18; not touched by this agent). Load average 1.8. A separate review agent (diagnostic/zfast/review_m10/, not touched) may run
   work in parallel; its load is outside this run's control and will be recorded if seen.
4. **New run tooling (no certificate input).** `tools/run_m10.sh` (sequence below) and `tools/m10_monitor.py` (tree phys_footprint
   watchdog ≤ 3 GB, disk floor 2 GB, checkpoint-based progress and the projection STOP). Monitor smoke test on a dummy process and the
   finished wide7_1e22 checkpoints: progress fraction 1.000 for both sessions (the arithmetic Σ(n_hi − n_lo + 1) = Nw − nhead holds).

## 1. The run (`tools/run_m10.sh`, nohup, nice 19)

- **Window.** T0 = 10²⁵, target [10²⁵, 10²⁵ + 100], run name `wide7_1e25`,
  run dir `atlas_v5z7/runs/w10000000000000000000000000/wide7_1e25`.
- **Command.** `atlas_v5z7/run_wide7.sh wide7_1e25 T0 T0 T0+100 91 0.008` (no centre argument: the provider's default, 50, as for
  wide7_1e22). Wide session H = 91, Δ = 0.008, K = 18, J = 12, z span [−2, 102], `--zs-step 0.005`, `--gen-timeout 1209600`,
  `--turing-grid` (u0 −40, step 0.004, n 45001; Δ_T = 40).
- **Settings.** D = ZFAST_THREADS = **4** (work decomposition; recorded as `zfast_session.threads`, inherited by the replay);
  W = ZFAST_WORKERS = **8** (output-free; recorded in drive.jsonl); V4_LIM_GB = 1.0 (driver per-child kill); checkpointing on
  (wide mode: RUN/zfast_ckpt_gen.txt, RUN/zfast_ckpt_replay.txt).
- **Order.** Pipeline (generator session + Turing grid; replay of record in a fresh process) → `scan_turing5.py recount` on the
  generator's grid → `turing_gate check` (REQUIRED, A6) → crosscheck.py → Lean export `v5z7_wide7_1e25` + atlas_audit →
  tight_margin_v1. Then the controls NC-X1, NC-X2 on copies.

## 2. Predictions carried over (M8 X1–X13 → v5z7)

| # | prediction | MET iff | change vs M8 |
|---|---|---|---|
| X1 | Claim (A): every piece closes; replay plain + hardened passes all certificates; 0 seams; no d = 0 gaps | summary all_closed = true | none |
| X2 | Claim (B): all sign-change intervals covered by passed S-layer certificates | passed_B = true, uncovered = [] | none |
| X3 | Replay of record in a fresh process, session parameters (incl. D) from pieces.json | replay_check passed and passed_B both true | v5z7 has one replay (THEORY_V5Z6 (b)): the fresh-process replay of record *is* the independent replay; no third session |
| X4 | Zero count: smooth term 886.919; central **887**; band [883, 891]; rigorous envelope [866, 908] | certified sign changes in target in band, 0 straddling, disjoint | none |
| X5 | REQUIRED Turing gate: both ends pinned by scan_turing5 (recount of the generator's grid) with U − L ≤ 0.6; N(T0+100) − N(T0) = certified sign changes. Predicted U − L ≈ 0.48–0.55 | `turing_gate check` PASS | the count comes from the generator session's grid (v5z6 (a)), not a separate scan session; the counting tool is the unchanged scan_turing5 |
| X6 | Lean audit (`export_certs.py --v5 v5z7_wide7_1e25` + atlas_audit) | VIOLATIONS 0; all certificates replay-passed; target covered; claim (B) group covered | dataset name |
| X7 | Reported min_candidate_lower over main pieces: central **0.56**; band [0.50, 0.66] | in band | none |
| X8 | Tight margin (diagnostic): min over main pieces central 1.02, band **[0.95, 1.08]**; median ≈ 1.09; tight ≥ reported on every piece | min in band and tight ≥ reported on 100% | none |
| X9 | 100 main certificates, ≥ 95 at tier t1; S-layer certificates = intervals (≈ 887–892) | ≥ 95 t1 and np passed = np intervals | none |
| X10 | Memory: driver-recorded peak_gb of generator and replay ≤ 0.5 GB; monitor tree peak recorded (watchdog 3 GB) | ≤ 0.5 GB | the Turing scan is now inside the generator |
| X11 | One zfast session per process (strict); Nw = 1,261,566,261,010 (checkpoint header) | 1 per process and Nw exact | D = 4 recorded in pieces.json; W = 8 in drive.jsonl |
| X12 | Wall time (D 4, W 8, nice 19). M9 projection (3.06× of M8's v13b 4-thread calibration; contended machine): session 6,459 s. Generator ≈ 6,900 s (session + grid + 25k points + LPs), replay ≈ 6,600 s → pipeline ≈ **13,500 s ≈ 3.75 h**; recount + gate + crosscheck + Lean + tight ≈ 300–900 s | generator, replay and pipeline each within ×[0.75, 1.33] of prediction | v5z5's 4 sessions (22.2 h) → 2 sessions. Note: the spinners are absent, so M9 expects 10–25% less; a low-side MISS is possible and will be reported as such |
| X13 | Session build at 1e25 matches the M9 scaling: generator session (checkpoint file first seen → last checkpoint line) within ×[0.75, 1.33] of 6,459 s | in range | base is v14 W 8 (M9 S2) instead of v13b 4 threads |

### Negative controls (stored data, COPIES under engine/regress_v1/work/; nothing in the run directory touched)

| id | control | MET iff |
|---|---|---|
| NC-X1 | `python -m engine.regress_v1.v5z5_gate --controls RUN` (v5z5 verifiers = v5z7 verifiers, byte-identical): NC-W1 (w × 1.10), NC-W2 (swapped interval), NC-W3 (w × (1 + 10⁻³)) | NC-W1: 0 main records pass; NC-W2: ≥ 1 failing main certificate; NC-W3: ≥ 1 main certificate failing both modes; baseline all pass |
| NC-X2 | `python -m engine.regress_v1.turing_gate controls RUN RUN/turing_recount.json` (NC-T1..NC-T4) | every NC-T FAILS and the baseline copy PASSES |

## 3. STOP conditions

- **S1′ (replaces M8 S1/S2's session-time stop; Phil's M10 instruction).** From the first checkpoint projection (generator fraction
  ≥ 2% and ≥ 600 s into the session): projected window = 2 × projected session + 900 s. If > **10 h**, m10_monitor kills the run tree
  and writes `runs/m10/STOP`; report, nothing rerun under the same name.
- **S2.** A strict-mode raise, the driver's 1.0 GB per-child kill, the 3 GB tree watchdog, or disk < 2 GB → stop and report.
- **S3.** Tight min margin < 0.45, or any replay failure (plain, hardened) → STOP; no 1e26 preparation; report the failing piece.
- **S4.** Turing gate FAIL → the window is NOT CERTIFIED-COMPLETE. No retry with a changed Δ_T without an amendment.

## 4. Claim status

A pass of X1–X6 makes the window **"CERTIFIED, pending v14 review"**: the v14 kernel/scheduler and the checkpoint load path are new
trusted code, bit-identity to v13b is mechanically checked (M9) but their independent review is running in parallel. No headline
claim until that review passes.

## 5. To be derived from the measured run (inference, not scored)

Projected 1e26 and 1e28 (HIK y = 10²⁸ + 501675.8) window times, from the measured 1e25 session by √T scaling plus the measured
non-session work. M9's projections for reference: 1e26 ≈ 11.5 h, 1e28 ≈ 4.7 days (contended machine).

## 6. Wording

The certification method is Atlas's own and new: zero-list-free, Turing-free explicit-formula LP certificates with sign-change
credit, local-count closure, the S-layer, Lean-audited and independently replayed. Only zfast's evaluation core has prior art (FLINT
dfloat). Zeros near 10²⁵ have been computed before by other, non-rigorous methods (Odlyzko/Gourdon-type zero lists, Bober–Hiary).
This window is a list-free certificate, not a new zero height; nothing here "extends H" or goes "beyond Odlyzko". Novelty check before
any "first" claim.
