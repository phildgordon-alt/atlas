# PREDICTIONS_M7: atlas_v5z5 (wide-session windows) — gate and the window [10²², 10²² + 100]

Written 2026-11-01 before any atlas_v5z5 run (sha in `PREDICTIONS_M7.sha256`). Approved by Phil 2026-11-01 (CORE_ROADMAP §4 item 1).
A changed criterion after hashing is an amendment: dated, appended at the end, disclosed in RESULTS_M7.md.

**Disclosed before hashing.** One uncounted micro-benchmark of the pinned libzfast.v13b (scratch script, 10¹⁶, 2 threads, ~10 s):
per-point cost at (H, Δ) = (4, 0.15) was Z 0.22 ms / row 2.5 ms (107 buckets); at (61, 0.012) Z 1.6 ms / row 15.6 ms
(1,138 buckets); session build 1.2 s vs 1.5 s. No certificate code was run. This shaped the cost prediction in W6.

## 0. What v5z5 is

A new tree `atlas_v5z5/`, built by `tools/make_v5z5.py` from atlas_v5z4 (frozen, untouched). Byte copies of every v5z4 file except:
- `lib/zfast_provider.py` (same module name: the sha-pinned verify_zs5.py imports it by that name):
  - session parameters H, Δ, K, J and the centre are configurable (env ZFAST_H, ZFAST_DELTA, ZFAST_K, ZFAST_J, ZFAST_CENTER);
    defaults are exactly v5z4's (4, 0.15, 18, 12; centre rule unchanged);
  - strict mode (ZFAST_STRICT=1, used by every wide run): a centre is required, a point outside [c − H, c + H] raises, and a
    second session in one process raises (one O(√T) pass per process, by construction);
  - explicit raises instead of asserts; refuses to import under python -O / PYTHONOPTIMIZE (every pipeline process imports it).
- `atlas_v5.py` (driver): records the full zfast/pipeline env (ZFAST_CENTER, ZFAST_THREADS, ZFAST_H/DELTA/K/J/STRICT, CSTEP, CND,
  MINW_BINS, ZS_*, V4_LIM_GB, test hooks, BLAS threads, python/flint versions) in drive.jsonl and the session record
  `zfast_session` in pieces.json; `--wide` mode (centre = midpoint of the Z span, H/Δ explicit, span ⊂ session checked before
  any compute); explicit raises; refuses -O.
- `replay_target5.py`: takes the session parameters from pieces.json (not from the caller's env) and records the replay env.
- New run scripts (`run_window.sh` legacy-compatible, `run_wide.sh`); `THEORY_V5Z5.md`; `V5Z5_FREEZE.sha256`.

The verifier (verify_zs5.py, sha 79ca5b16…), model, LP generator, replay logic, tiling and S-layer are byte copies. The certificate
inequality and the claim are unchanged. **Soundness argument:** THEORY_M5 §1 — every value is a ball from a session whose validity
range contains the point (now a raise, not an assert); which session answers is a matter of cost only. THEORY_M5b Lemma M1c holds
for any H, Δ (the Taylor remainder (|h′|X_b)^{K+1}/(K+1)!·e^{|h′|X_b} is evaluated in Arb per block).

**Wide session parameters (pre-registered):** H = 61, Δ = 0.012, K = 18, J = 12 — the parameters of the 10²²–10²⁴ scans
(scan_turing2/3), so |h′|X_b ≤ √(61² + 0.98²)·0.006(1+ε) ≤ 0.37 and the remainder ≤ 0.37¹⁹/19! ≈ 5e-26. Centre 50.0 for the
target [0, 100] (Z span [−2, 102] ⊂ [−11, 111]). ZFAST_THREADS = 2 throughout (the w_1e22 reference also used 2), nice 19.

## 1. Gate (must pass before the wide window runs)

| # | check | MET iff |
|---|---|---|
| G0 | regress_v1 tier 0 | identical outcome to the last counted run (reports/tier0_20261101_095813): every section PASS except the known, pre-existing artin_sweep count F-ART (2,256 vs 2,259; unrelated to zfast); zfast windows 51/51; golden: 0 differing |
| G1 | regress_v1 tier 1 | PASS 30/30 (Z1 25/25, Z-X, G1, L1, K1) |
| G2 | new `engine/regress_v1/v5z5_gate.py --zx`: v5z5 code (legacy session mode, recorded env centre 1.0, threads 2) regenerates v5z3 x_1e16 | every certs/ and certs_np/ file canonically identical (volatile: gen_seconds), zs.json and gen_measurements.json canonically identical, pieces.json differing ONLY in keys ⊆ {z_provider, zfast_session}, replay_check results and replay records identical |
| G3 | `v5z5_gate.py --w1e22` (tier 2): v5z5 code regenerates v5z4 w_1e22 (centre 1.0 as run_y34.sh, threads 2) | same criteria as G2, against the frozen v5z4 w_1e22 files; expected 2/2 main + 16/16 S-layer certificates identical; min_candidate_lower 0.7475326795220493 |
| G4 | strict-mode unit checks (in v5z5_gate.py, at 10¹² only): a point outside the session raises; a second session raises; a missing centre raises; import under PYTHONOPTIMIZE=1 refuses | all four raise |

The 11.5 h w_1e24 regeneration is NOT run (Phil's call). v5z5 changes no generator path at H = 4 (only how the session is
configured), which is why G2 + G3 are the registered gate.

## 2. The wide window W = [10²², 10²² + 100] (run name `wide_1e22`, `run_wide.sh`)

Reference: v5z4 w_1e22 (2 units, 2 threads): pipeline wall 1,927.12 s (generator 963.9 + replay 963.2), independent replay
960.5 s, total 2,887.6 s; 16 zeros; 2 main + 16 S-layer certificates; min_candidate_lower 0.74753.

| # | prediction | MET iff |
|---|---|---|
| W1 | Claim (A): every piece closes; replay plain + hardened passes all certificates; tiling of hull and target × [0, ½] with 0 seams and no d = 0 gaps | summary all_closed = true |
| W2 | Claim (B): every sign-change interval met by a main region is covered by passed S-layer certificates | passed_B = true, uncovered = [] |
| W3 | Independent replay (fresh process, own copy of lib, session parameters from pieces.json) | passed and passed_B both true |
| W4 | Zero count. Smooth term (θ(T+100) − θ(T))/π = 776.978 (Arb). Prediction: sign changes in the target = **777**, MET band [774, 780]; rigorous envelope from Trudgian's \|S\| ≤ 9.27: [758, 796]. (Non-rigorous scan2_1e22 hint: 481 zeros in [0, 62] vs smooth 481.73.) | count in band |
| W5 | Sign-change count = Turing count, separate method: new `tools/scan_turing4.py` (= scan_turing3 with centre/H/Δ/grid as arguments): one kind-0 session centred T0 + 50, H = 91, Δ = 0.008, K = 18, grid u ∈ [−40, 140] step 0.004; Turing (Lemma T, Bober–Hiary, Δ_T = 40) at v = 0 and v = 100, both pinned; crosscheck.py on the run | N(T0+100) − N(T0) = certified sign changes inside [0, 100], both ends pinned, no straddling interval; N(T0) also equals scan2_1e22's 76106294246675308886088 |
| W6 | Cost (2 threads, nice 19, one other single-core job may be running). Predicted pipeline wall ≈ 2,400 s (one session build ≈ 950 s per process + ≈ 26,000 Z points and ≈ 1,000 rows at Δ = 0.012 + ≈ 880 certificates replayed twice); independent replay ≈ 1,200 s | pipeline wall ≤ 2 × 1,927.12 = 3,854 s AND independent replay ≤ 2 × 960.5 = 1,921 s |
| W7 | Zeros per wall-hour (pipeline + independent replay): reference 16 / 2,887.6 s = 19.9 /h; predicted ≈ 777 / 3,600 s ≈ 780 /h, a gain ≈ 39× | gain ≥ 25× |
| W8 | Memory: peak phys_footprint of every stage ≤ 0.5 GB (driver kill limit V4_LIM_GB = 1.0) | ≤ 0.5 GB |
| W9 | Lean audit: `export_certs.py --v5 v5z5_wide_1e22` + `atlas_audit` | VIOLATIONS 0, all certificates replay-passed, target covered, claim (B) group covered |
| W10 | Margins. Reported min_candidate_lower (frozen verifier's first-positive-leaf number) over all main pieces: central 0.62 (a combination-B piece, MARGIN_ANATOMY), MET band [0.58, 0.76]. **Tight margin** (tools/tight_margin_v1.py, Arb branch-and-bound to 1e-3, diagnostic): min over main pieces central 1.09, MET band [1.05, 1.13]; tight ≥ reported on every piece; median tight ≈ 1.13 | both minima in band and tight ≥ reported on 100% of pieces |
| W11 | Sessions: exactly one zfast session per process (generator, replay, independent replay), recorded in the session stats/strict mode | 1 per process |
| W12 | Main certificates: 100 pieces, ≥ 95 at tier t1 (no split); S-layer certificates = number of intervals met (≈ 777–781) | ≥ 95 t1 and np passed = np intervals |

Negative controls on the finished wide run (stored-data re-verification with the frozen v5z5 replay logic via
engine/regress_v1/zfast_t0_worker.py on a COPY under engine/regress_v1/work/; nothing in the run directory is touched):

| id | control | MET iff |
|---|---|---|
| NC-W1 | `--tamper-cert` (every w × 1.10) | 0 main records pass |
| NC-W2 | `--swap-interval` (one interval replaced by the gap to the next) | at least one record fails in every main certificate with ≥ 2 intervals, or geometry not closed |
| NC-W3 | every w × (1 + 10⁻³) in every main certificate (copy) | at least 1 main certificate fails both modes (prediction: most fail; (R) is near-tight) |
| NC-W4 | one sign-change interval (and its w) deleted from one main certificate (copy) | detected by the replay OR by the count check (sign changes ≠ Turing count); prediction: the replay may still pass (less credit is still sound), the count check detects it |

## 3. STOP conditions

- S1: any of G0–G4 not MET → no wide run; report the difference.
- S2: during the wide run: a strict-mode raise (second session / point outside), the watchdog kill (> 1.0 GB), disk < 2 GB, or a
  projected wall time > 6 h → stop and report; nothing is rerun under the same name.
- S3: a piece that does not close is reported as NOT CLOSED. No parameter change and rerun without an amendment here.
- S4: a Turing end not pinned → W5 reported as inconclusive (not MET), no retry with changed Δ_T without an amendment.

## 4. Wording

The certification method (zero-list-free explicit-formula LP certificates with sign-change credit, local count closure, S-layer,
Lean-audited, independently replayed) is Atlas's own and new; only zfast's evaluation core has prior art (FLINT dfloat). Nothing
here "extends H" or goes "beyond Odlyzko"; zeros near 10²² have been computed before by other methods (zero lists). Novelty check
before any "first" claim.

## Amendment M7-A1 (2026-11-01 ~12:45, after the scan; disclosed in RESULTS_M7.md)

**Finding.** scan_turing4 (W5) pinned N(T0) = 76106294246675308886088 (equal to scan2_1e22) but did NOT pin N(T0 + 100): U − L =
1.35·10⁷. Cause, located from the saved grid (no new zfast call): the Lemma-T formulas inherited from scan_turing2/3 integrate θ/π + 1
over [v, fl(v + Δ_T)] but divide by arb(Δ_T). With v, Δ_T small integers (every earlier use) fl(v + Δ_T) − v = Δ_T exactly; my grid
clip gave Δ_T = 39.999999999 at v = 100, where fl(100 + Δ_T) − 100 ≠ Δ_T by ~10⁻¹⁴ relative to 40, times N ≈ 7.6·10²² ⇒ ~10⁷.
At Δ_T = 39 (exact) U and L pin (U − L ≈ 0.48). A tool defect of the diagnostic count, not of any certificate. As registered, W5 is
reported NOT MET (inconclusive, S4).

**Change (amended W5).** New `tools/turing_extra2.py` = turing_extra.py with (a) Δ_T as an argument, required to make v ± Δ_T exact
in binary64 (checked), and (b) the sign of Z(T0 + v) taken from the zfast ball at exactly v recorded in scan_turing.json when v is not
a grid point. Run on the SAVED runs/m7/scan4_1e22 with Δ_T = 39 at v = 0 and v = 100. Amended W5 MET iff both pinned and
N(T0+100) − N(T0) = the certified sign changes in [0, 100].
