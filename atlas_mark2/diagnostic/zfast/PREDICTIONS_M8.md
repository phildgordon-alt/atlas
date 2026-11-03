# PREDICTIONS_M8: the rigorous window [10²⁵, 10²⁵ + 100] on atlas_v5z5, with thread scaling, the Turing gate, and the 10²⁶/10²⁸ plan

Written 2026-11-01 before any 10²⁵ run (sha in `PREDICTIONS_M8.sha256`). Approved by Phil 2026-11-01 (milestone M8).
A criterion changed after hashing is an amendment: dated, appended at the end, and disclosed in RESULTS_M8.md.

## 0. Disclosed before hashing (everything done for M8 so far; no 10²⁵ computation of any kind)

1. **scan_turing5** (`tools/scan_turing5.py`, sha 898bf5c5…). Exact rational Δ_T, v, divisor and interval selection (fixes F-M7a).
   Validation, `runs/m8/turing5_validation.json`, ALL OK:
   - 36/36 stored Turing records (1e16–1e24 and wide_1e22) are reproduced from the saved scans: N_lower, N_upper and the 12-digit
     U and L strings are identical.
   - The F-M7a record (scan4_1e22, v = 100) now pins at Δ_T = 40 and equals the M7-A1 value …886865.
   - Fresh scans at 1e12–1e18 (`runs/m8/fresh/`) reproduce all 13 Arb crosscheck counts (1e12–1e16, including the 1e15 + 286 pair).
     They give this project's first Turing counts for its 1e17/1e18 windows: 11 and 11 (N(1e17) = 577829042746896155, N(1e18) = 6144758226908675409), equal to the certified sign changes.
2. **Required Turing gate.**
   - `engine/regress_v1/turing_gate.py` (sha 25e7972f…), amendment A6 in `engine/regress_v1/PREREG_AMENDMENTS.md`, re-hashed to
     b86ce3b9….
   - `all` mode: 43/43 closed zfast windows pass, 1e12–1e24 plus wide_1e22.
   - Controls NC-T1..NC-T4 all FAIL the gate as required, on wide_1e22 and on w_1e24. NC-T1 deletes one zero from all 5 covering
     main certificates and from its S-layer certificate, giving count 776 ≠ 777.
3. **Code-independent Z (zcheck_m8/).**
   - **Cause of the 4e91 ball.** Stock `acb_dirichlet_powsum_smooth` adds ~0.27·N terms sequentially into one ball. Once the term
     radii fall below one mag ulp, every add rounds the radius up by about 2^-29: the radius grows like e^{c·n} with c ≈ 2.2·10⁻⁹
     (measured, `bin/probe_mag3`). That gives about e^{230} at 1e24, whatever the precision.
   - **The precision was a red herring.** prec 192 vs 208 does not matter; single terms have radius about 1e-38
     (`bin/probe_term`).
   - **Replacement.** `zcheck_m8/src/zref_m8.c` uses stock FLINT only: the powsum_smooth algorithm with blocked accumulation, 4
     threads, and rv_ref's independent Gabcke term.
   - **Agreement so far.** Stock acb_dirichlet_hardy_z agrees at 1e12 and 1e16 to ≤ 1.3e-16, inside zref's ball. zfast's balls
     contain zref at 1e12, 1e16 and 1e20 (|diff| ≤ 9e-16; zref radius = the Gabcke R1 bound, 5.3e-27 at 1e20).
   - **Cost.** 0.26 µs CPU per n per point. The 1e22 point (u = 65.292, a near-zero grid point, Z ≈ 4.19e-5) finished before hashing: 3,588 s at 4 threads, zref radius
     9.7e-29, |diff| to zfast 3.9e-16, inside the zfast ball (3.85e-9), same sign. Details are in RESULTS_M8.
4. **Thread calibration** (§1 below), measured before hashing. **Machine state:** two non-Atlas processes (`colab drivemount`,
   started by the Codex app) each use about 100% of one core at 13 MB. They are not ours to stop. Nothing else heavy runs (`ps`).

## 1. Thread calibration (measured, `runs/m8/calib/calib.jsonl`)

Setup: height 1e21 (Nw = 12,615,662,610). One kind-0 session per fresh process, with the wide parameters (H 61, Δ 0.012, K 18, J 12),
then 3,000 Z points. The tool is `tools/calib_threads_m8.py`. Runs were sequential at nice 19, with the two non-Atlas spinners present
(load average ≈ 6).

| threads | session build (s) | speedup | CPU user (s) | 3,000 Z points (s) | max RSS |
|---|---|---|---|---|---|
| 1 | 624.4 | 1.00 | 630 | 7.6 | 22 MB |
| 2 | 315.0 | 1.98 | 634 | 7.6 | 22 MB |
| 4 | 197.6 | **3.16** | 768 | 7.6 | 23 MB |

**Linearity in Nw** (checked against stored runs):
- 1e21 at 2 threads × √10 = 996 s, against scan4_1e22's measured 992 s;
- 1e21 at 1 thread × 10^1.5 = 19,745 s, against scan3_1e24's measured 20,098 s (+1.8%).

**Extrapolation to 1e25** (Nw = 1,261,566,261,010, ×100): one session costs 62,439 s on 1 thread, **19,763 s ≈ 5.49 h on 4 threads**.
A v5z5 wide window with the required Turing gate needs **4 sessions**:
- generator,
- in-pipeline replay,
- independent replay,
- the scan_turing5 scan.

Non-session work adds about 900 s (per-point Z and rows, LPs, about 890 certificates replayed twice, export/audit/tight about 300 s).

## 2. The window W = [10²⁵, 10²⁵ + 100] (run name `wide_1e25`, `tools/run_m8.sh`)

**Code.** atlas_v5z5 is frozen and unmodified (V5Z5_FREEZE.sha256). The commands are those of `atlas_v5z5/run_wide.sh`, with one
change: `--gen-timeout 57600` instead of run_wide.sh's hard-coded 21600. The timeout enters no certificate.

**Session.** wide, H = 61, Δ = 0.012, K = 18, J = 12, centre 50 (the midpoint of the Z span [−2, 102]). ZFAST_THREADS = 4,
V4_LIM_GB = 1.0 (the driver's phys_footprint kill), nice 19.

**Order.** Pipeline (generator + replay), then the independent replay, then the Turing scan (scan_turing5: centre 50, H 91,
Δ 0.008, u0 −40, n 45001, Δ_T = 40, points 0 and 100), then crosscheck.py, then `turing_gate check`, then the Lean export and
atlas_audit, then tight_margin_v1.

| # | prediction | MET iff |
|---|---|---|
| X1 | Claim (A): every piece closes; replay plain + hardened passes all certificates; 0 seams; no d = 0 gaps | summary all_closed = true |
| X2 | Claim (B): all sign-change intervals covered by passed S-layer certificates | passed_B = true, uncovered = [] |
| X3 | Independent replay (fresh process, session parameters from pieces.json) | passed and passed_B both true |
| X4 | Zero count. Smooth term (θ(T+100) − θ(T))/π = 886.919 (Arb). Central prediction **887**; MET band [883, 891]. Rigorous envelope from Trudgian's \|S(t)\| ≤ 10.08 at 1e25: [866, 908] | certified sign changes in the target in band, 0 straddling, disjoint |
| X5 | **REQUIRED Turing gate** (A6): N(T0) and N(T0 + 100) both pinned by scan_turing5 with U − L ≤ 0.6, and N(T0+100) − N(T0) = certified sign changes (G-T1..G-T6). Predicted U − L ≈ 0.48–0.55 | `turing_gate check` PASS |
| X6 | Lean audit (`export_certs.py --v5 v5z5_wide_1e25` + atlas_audit) | VIOLATIONS 0; all certificates replay-passed; target covered; claim (B) group covered |
| X7 | Reported min_candidate_lower over the main pieces: central 0.56; MET band [0.50, 0.66]. M7: 0.5806 at 1e22, a combination-B piece; MARGIN_ANATOMY: −0.016/decade real; combination B is present in any 100-unit window | in band |
| X8 | Tight margin (tight_margin_v1, diagnostic): min over the main pieces central 1.02, MET band [0.95, 1.08]; median ≈ 1.09; tight ≥ reported on every piece | min in band and tight ≥ reported on 100% |
| X9 | Main certificates: 100 pieces, ≥ 95 at tier t1; S-layer certificates = the number of intervals met (≈ 887–892) | ≥ 95 t1 and np passed = np intervals |
| X10 | Memory: peak phys_footprint of every stage ≤ 0.5 GB; Turing scan ≤ 0.5 GB | ≤ 0.5 GB |
| X11 | Sessions: exactly one zfast session per process (strict mode); Nw = 1,261,566,261,010 | 1 per process and Nw exact |
| X12 | Wall time (4 threads, nice 19, the two non-Atlas spinners present). Predicted total (pipeline + independent replay + Turing scan + gate + Lean + tight) = 4 × 19,763 + 900 ≈ **80,000 s ≈ 22.2 h**; pipeline ≈ 40,500 s, independent replay ≈ 19,900 s, Turing scan ≈ 20,000 s | each stage within ×[0.75, 1.33] of its prediction |
| X13 | Thread scaling at 1e25 equals the §1 calibration: the generator's session build time at 4 threads within ×[0.75, 1.33] of the §1 extrapolation | in range |

### Negative controls (stored-data re-verification on COPIES under engine/regress_v1/work/; nothing in the run directory touched)

| id | control | MET iff |
|---|---|---|
| NC-X1 | `v5z5_gate --controls` NC-W1 (w × 1.10), NC-W2 (swapped interval), NC-W3 (w × (1 + 10⁻³)) | NC-W1: 0 main records pass; NC-W2: ≥ 1 failing main certificate; NC-W3: ≥ 1 main certificate failing both modes |
| NC-X2 | `turing_gate controls` on wide_1e25 (NC-T1 zero deleted from all covering certificates; NC-T2 N + 1; NC-T3 unpinned end; NC-T4 pre-fix tool) | every NC-T FAILS the gate and the baseline copy PASSES |

(NC-W4 is no longer a pass/fail control of the replay: by M7's lesson, a deleted interval is caught by the Turing gate. NC-X2 is the
registered form.)

## 3. STOP conditions

- S1: projected wall > 16 h from §1, or a projected footprint near 3 GB → no run; report. **Decision at hashing: S1 IS TRIGGERED.**
- The calibrated projection is 22.2 h, above the 16 h limit set for M8.
- Even without the Turing scan, the pipeline plus independent replay is 16.7 h.
- **The 1e25 window is therefore NOT run in M8.**

The predictions X1–X13 and NC-X1/NC-X2 stay registered, unchanged, for the run once it is approved. Either Phil approves a run of
about 22 h, or it runs on a version that drops sessions (§4, v5z6). If a later amendment changes the code version, it must state
which X-criteria carry over.
- S2: during the run: a strict-mode raise, the watchdog kill, disk < 2 GB, or a generator session build at 4 threads > 1.5× the §1
  extrapolation (`runs/m8/STOP` is then written by hand and the remaining stages do not start) → report; nothing is rerun under the
  same name.
- S3: **tight min margin < 0.45, or any replay failure (plain, hardened, or independent)** → STOP. No 1e26 preparation; report the
  failing piece.
- S4: Turing gate FAIL → the window is reported NOT CERTIFIED-COMPLETE (count disagreement or unpinned end). No retry with a changed Δ_T
  without an amendment.

## 4. Extrapolated cost and plan for 10²⁶ and 10²⁸ (predictions to be tested later; not scored in M8)

Calibrated session cost, 4 threads: S(T) = 197.6 s × √(T/10²¹). This assumes the 3.16× scaling holds and the machine state is
unchanged.

| height | Nw | one session (4 thr) | v5z5 as is (4 sessions) | v5z6 (2 sessions) | zeros per 100 units | true slack (tight, MARGIN_ANATOMY) |
|---|---|---|---|---|---|---|
| 1e25 | 1.26e12 | 5.5 h | 22.2 h | 11.2 h | 887 | 1.02 (0.95–1.08) |
| 1e26 | 3.99e12 | 17.4 h | 69.7 h (2.9 d) | 34.9 h (1.5 d) | 924 | ≈ 1.00 |
| 1e28 (HIK's y = 10²⁸ + 501675.8) | 3.99e13 | 7.2 d | 29 d | **14.5 d** | 997 | ≈ 0.95–1.0 |

**v5z6** (to be built and gated; not part of M8) cuts the window from 4 sessions to 2:
- (a) The generator's wide session uses H = 91, which costs the same as H = 61, and also writes the scan_turing5 grid, so the
  Turing count costs no extra session. The count stays a separate method; only the evaluator session is shared, and the evaluator
  is already shared.
- (b) The in-pipeline replay is dropped (`--no-inline-replay`), so the fresh-process independent replay is the replay of record.

Gate: regress_v1 plus v5z5_gate G2/G3 (legacy mode identical), the turing_gate controls, and a wide_1e22 rerun identical in
certificates.

**Code-independent Z (zref_m8)** at 0.34 µs CPU per n, 4 threads at 3.16×:
- one point costs about 1 h at 1e22, about 12 h at 1e24, about 38 h at 1e25 and about 50 d at 1e28;
- memory < 10 MB everywhere.

So a code-independent check at 1e28 needs either a sub-√T reference or a reference sharing the multi-point pass (§4 of RESULTS_M8).
**These rows are predictions to be tested later.** A run at 1e26 or above needs its own pre-registration.

## 5. Wording

The certification method is Atlas's own and new: zero-list-free explicit-formula LP certificates with sign-change credit,
local-count closure, the S-layer, Lean-audited and independently replayed. Only zfast's evaluation core has prior art (FLINT dfloat).
Zeros near 10²⁵ have been computed before by other, non-rigorous methods (Odlyzko/Gourdon-type zero lists, Bober–Hiary). This window
is a list-free certificate, not a new zero height. Nothing here "extends H" or goes "beyond Odlyzko". Novelty check before any
"first" claim.
