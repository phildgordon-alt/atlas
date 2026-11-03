# PREDICTIONS_M9: libzfast.v14 + atlas_v5z6 (faster, leaner RH windows) — pre-registration (2026-11-01)

Hashed (`PREDICTIONS_M9.sha256`) **before** any of the measurements below. Plan: `OPTIMIZE_M9.md`. Rules: nice 19, one heavy job at a time,
footprint watchdog (regress `guarded`, ≤ 3 GB everywhere; v5z6 driver V4_LIM_GB 1.0), disk floor 2 GB, explicit raises, -O refused,
ZFAST_THREADS (= D) / ZFAST_WORKERS / ZFAST_CENTER recorded. Two non-Atlas `colab drivemount` processes (~1 core each) are running and
are left alone; every timing is taken with them present. **No 10²⁵ run. No w_1e24 regeneration.**

## 0. Facts known before hashing (disclosed; development measurements, not predictions)

- Profile (v13b, 10²⁰, 1 thread): kernel 96.7% of samples; 50 ns/term; head 0.2 s; build 199.8 s (`runs/m9/profile/`).
- Kernel bench (`src/v14_bench/kbench.c`, dev build): 0 mismatches; 50.1 → 19.7–20.9 ns/term (2.39–2.55×); -O3 ≈ 3% (not used).
- Dev library (scratch build of the same source), 10¹⁶: state hash of v14 at W = 1, 3, 8 equal to ref13h's; grid/rows/Z equal to the frozen
  v13b dylib's; checkpoint exit/resume, foreign-checkpoint refusal and corrupted-line rejection behaved as designed.
- Dev library, 10²⁰ (H 61, Δ 0.012): D 2: W 1 79.5 s, W 4 26.7 s, W 8 20.6 s (hash equal for all W); D 8 W 8 20.7 s; D 4 W 4 26.8 s.
- Official build `bin/libzfast.v14.dylib` sha 7abaaa8a…; ref13h sha d0438135…; atlas_v5z6 built and frozen (V5Z6_FREEZE.sha256, 34 entries).
- Smoke run v5z6 `smoke_1e12` (target [0, 10], H 91, Δ 0.008, D 2, W 4): closed, 41 sign changes, Turing recount 41, gate PASS, 42 s.
- Finding F-M9a: `python -m engine.regress_v1 --tier 0` stops in `lean.v5_datasets` (StopIteration) since M7's Lean dataset
  `v5z5_wide_1e22` exists; the last green tier 0 (11:14) predates it. Tiers are therefore run through `engine/regress_v1/tier_m9.py`, which
  registers atlas_v5z5 (tree + Lean prefix) in memory only, as v5z5_gate/turing_gate already do. A tier-0 run under that wrapper was started
  before hashing; its result is reported, not predicted (it is the "tier 0 green" check, criterion T0 below is fixed here regardless).

## 1. Identity criteria (bit-identity is the acceptance rule; any miss = v14/v5z6 not used for claims)

| # | prediction | pass rule |
|---|---|---|
| I1 | `v5z6_gate --identity`: for every case (10¹² H 91 Δ 0.008 D 1/2/4; 10¹⁶ H 61 Δ 0.012 D 1/2/4; 10¹⁶ legacy H 4 Δ 0.15 D 2; 10²⁰ H 61 D 2 and D 4) and every W ∈ {1, 3, 8}: v14 state SHA-256, Z-grid bytes (mid, rad, u), row strings and Z strings equal to ref13h's (frozen v13b source) | all equal |
| I2 | the frozen `libzfast.v13b.dylib` gives the same grid bytes, rows and Z strings as ref13h (so ref13h = v13b) | all equal |
| I3 | v14 with `ZFAST14_GENERIC_KERNEL=1` (scheduler only) equals ref13h | equal |
| NC-I1 | control: D 1 vs D 2 at 10¹⁶ give different state hashes (the hash sees the decomposition) | differ |
| I4 | historical: v14 at 10²¹ (H 61, Δ 0.012, centre 50, D 4) reproduces M8's 4-thread calibration max_rad over the same grid (3000 points from u = 0, step 0.004) **exactly**: 2.8794749640237427e-09 (any W) | exact equality |
| G1 | `v5z6_gate --w1e22` (frozen session params H 61, Δ 0.012, D 2; W 8): certs 100/100 and certs_np 777/777 canonically identical; zs.json and gen_measurements.json canonically identical; pieces.json differs only in {z_provider, zfast_session} and zfast_session's v5z5 keys are equal; replay result and replay records identical to the frozen run's replay_check | all |
| G1b | zs.json and gen_measurements.json are also **byte**-identical | both |
| C1–C4 | `v5z6_gate --ckpt`: C1 test-hook exit (rc 77) + resume → identical state; C2 real SIGKILL after ≥ 300 checkpoint lines + resume with W 3 → identical; C3 foreign checkpoint refused; C4 pipeline killed inside its generator session + `--resume` → window identical to an uninterrupted run (certs, certs_np, zs, measurements, replay records, Turing grid bytes) | all |
| T0 | regress tier 0 (via tier_m9): every section PASS | PASS |
| T1 | regress tier 1 (via tier_m9): PASS (Z1, Z-X, G1, L1, K1) | PASS |
| TG | `turing_gate all`: every gated window with a record passes (43 at M8 + the new v5z6 production run if picked up); `turing_gate controls` on the new production run: baseline PASS, NC-T1..NC-T4 all FAIL | all |

## 2. Production run at 10²² under v5z6 (the M8 plan's gate run; not a new height)

`run_wide6.sh wide6_1e22 10²² [T0, T0 + 100] H 91 Δ 0.008` (centre = span midpoint 50), D 2, W 8.

| # | prediction | band |
|---|---|---|
| W1 | claim (A) 100/100 and claim (B) 777/777, replay of record passed and passed_B | exact |
| W2 | 777 certified sign changes in the target, 0 straddling | exact |
| W3 | Turing recount from the generator's own grid: N(T0) = 76106294246675308886088, N(T0 + 100) = 76106294246675308886865, both pinned; count 777; turing_gate PASS | exact |
| W4 | grid: 45,001 points, 0 undecided, 1,399 zeros in [−40, 140] (= scan4_1e22) | exact |
| W5 | peak footprint ≤ 0.5 GB per process | ≤ 0.5 |
| W6 | certificates differ from wide_1e22 only through Z/row radii (session H/Δ changed): not predicted identical; recorded | — |

## 3. Speed (predictions; measured with the two spinners present)

| # | quantity | predicted | MET band |
|---|---|---|---|
| S1 | 10²¹ session (H 61, Δ 0.012, D 4): v14 W 1 vs M8 v13b 1 thread (624.4 s) | 2.5× (≈ 250 s) | ≥ 2.2× |
| S2 | 10²¹: v14 W 8 vs M8 v13b 4 threads (197.6 s) | 3.0× (≈ 65 s) | ≥ 2.4× |
| S3 | 10²¹: v14 W 4 vs W 8 | W 8 faster by 1.2–1.4× | W 8 ≥ 1.1× faster |
| S4 | production window wall at 10²² (pipeline + recount + gate), v5z6 | ≈ 950 s | ≤ 1,500 s |
| S5 | the same window under v5z5 cost 2,373 + 1,083 (+ the separate scan, 1,167 s at H 91) = 4,623 s: gain | ≈ 4.9× | ≥ 3.0× |
| S6 | sessions per window | 2 | exact |

## 4. Projections (inference; recomputed from the measured S2 ratio in RESULTS_M9)

Session at 10²⁵ = 19,763 s (M8, v13b 4 threads) ÷ S2-ratio; window = 2 sessions + ≈ 15 min (points, rows, LP, grid, recount).
With the predicted 3.0×: 10²⁵ ≈ 6,590 s/session → **window ≈ 3.9 h** (v5z5: 22.2 h); 10²⁶ (×√10) ≈ **12 h** (v5z5 ≈ 70 h);
10²⁸ (×10 from 10²⁶) ≈ 58 h/session → **window ≈ 5 days** (v5z5 ≈ 29 days; M8's v5z6 plan without the faster engine ≈ 14.5 days).

## 5. Stops

- Any identity miss (I1–I4, G1, C1–C4): v14/v5z6 are not used for any claim; report and stop.
- Any watchdog kill, or disk < 2 GB: stop that step.
