# PREDICTIONS_M12: libzfast v14b + atlas_v5z8 (checkpoint hardening after review_m10), pre-registration (2026-11-02)

Hashed (`PREDICTIONS_M12.sha256`) **before** v14b is written, built or run. Phil approved the build on 2026-11-02. The input is
`review_m10/REVIEW.md` (verdict PASS WITH CONDITIONS; MAJOR M1, M2; minors m1–m8).

**Rules.**
- nice 19; one heavy job at a time; footprint watchdog ≤ 3 GB; disk floor 2 GB; explicit raises; -O / PYTHONOPTIMIZE refused.
- New dirs only: `src/v14b`, `bin/src_v14b`, `bin/libzfast.v14b.dylib`, `atlas_v5z8`, `runs/m12`. Nothing in v14 / v5z7 or any
  frozen tree is modified.
- Compiler flags are as v13b/v14: `-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math`.

**Scheduling.** M11 (10^26, run_m11.sh, pid 20988, started 09:46) uses 8 cores for about 9–10 h.
- Until RESULTS_M11.md exists and no M11 process remains, only light work runs: code, plus unit and negative tests at ≤ 10^14 on
  1 thread.
- The heavy gates come after M11. These are the identity matrix to 10^20, kill-and-resume, wide_1e22 regeneration under v5z8,
  regress tier 0/1, and turing_gate.

## 0. Design (fixed here; the details are in RESULTS_M12 and `atlas_v5z8/THEORY_V5Z8.md`)

**Compute path.** v14b's compute path is v14's, unchanged: kernel, items, merge, head, Z/rows. Only the checkpoint layer, the API
guards and the build-time test hooks change.

| finding | v14b fix |
|---|---|
| M1 | The header (format `ZFAST14B CKPT v2`) adds the following, and resume refuses on any mismatch, naming every mismatching field. (1) `prefast` = SHA-256 of nbeg[], Lb[] (raw bits), Xb[] (raw mag fields), arb_dump_str(tau0), nb/Nw/nhead/wp/K2, computed by the resuming process before its fast part. (2) `lib` = compile-time identity string plus compiler version. (3) `bin` = SHA-256 of the loaded zfast image (dladdr). (4) FLINT/GMP/MPFR version strings and SHA-256 of their loaded dylib files. (5) `os` = kern.osversion, a conservative pin: a resume across an OS update is refused. |
| M2 | `zfa14b_new` takes `role` (gen \| replay), a per-run `nonce` (32 hex) and a key file. Header role and nonce must equal the caller's. The v5z8 driver creates the nonce once per run (RUN/zfast_ckpt_nonce.txt), passes role-specific key paths, and records each session in `<ckpt>.sessions.jsonl` (provider). `replay_target` (v5z8) fails unless every session record of its replay process is role replay with the run's nonce, and it records items_loaded in replay_check.json. |
| m1 | **Decision: both layers.** (a) Every line, header included, is sealed with HMAC-SHA256 under a per-run, per-role 32-byte random key. The key is created by the library (O_EXCL, 0600) in a directory outside RUN (`diagnostic/zfast/ckpt_keys/`, 0700). This gives authenticity against anything without the key: resealed SHA lines, copies and misrouting. It gives none against a key holder, who has the same trust as the code. (b) On resume, a random sample of `verify_n` loaded items (provider default 8, recorded) is recomputed and must be bit-identical, or the session is refused. This is a probabilistic, key-independent content check. (c) Every parsed field is validated: hex-only tokens; mags normalised (2^29 ≤ man < 2^30, or zero) with a bounded exponent; arbs finite; every token canonical (re-serialisation equals the token). A line that fails its HMAC is ignored and counted (a torn write is possible after SIGKILL). A line that passes its HMAC but fails validation, matching or range checks is fatal (refuse). |
| m2 | Bounds are checked on `i` (0 ≤ i < T of the bucket) before the item index is formed. No signed overflow is possible. |
| m3 | Each line is one checked `write(2)` on an O_APPEND fd, followed by `F_FULLFSYNC` (falling back to `fsync`), both checked. On error: a stderr message, `ckpt_write_errors` +1, checkpointing stops (the computation continues, so the result is unaffected), and `zfa14b_info` reports it. The provider records it and warns. Checkpoint I/O moves off the queue mutex (separate I/O mutex). |
| m4 | `flock(LOCK_EX \| LOCK_NB)` on the checkpoint for the whole session build. A lock already held means refuse. |
| m5 | `zfa14_Zgrid` / `zfa14b_Zgrid` join every started thread before returning −1 on a `pthread_create` failure. |
| m6 | Not changed by design (documented). The cross-process Z/grid identity checks stay in the gate, and the resume sample recompute (m1 b) also exercises it. |
| m7 | D ∉ [1, 16] → `zfa14_new` / `zfa14b_new` return NULL with an explicit error. The provider also checks it. |
| m8 | The test hooks (EXIT_AFTER, GENERIC_KERNEL, plus new LBSHIFT and ZGRID_FAIL_AT for the negative tests) are compiled only with `-DZF_TEST_HOOKS`, into a separate `libzfast.v14b_testhooks.dylib`. The production dylib has none. Because its `bin` SHA differs, the production lib refuses its checkpoints. The v5z8 provider refuses to import, and the driver to start, when any `ZFAST14*_TEST*` / `ZFAST14_GENERIC_KERNEL` variable is set. The driver strips them from every child env. |

The old entry point `zfa14_new` in v14b refuses a non-empty checkpoint path, so the only checkpoint path is v14b's.

## 1. Identity (acceptance rule: bit-identity; any miss means v14b/v5z8 are not used for claims)

| # | prediction | pass rule |
|---|---|---|
| I1 | Matrix T ∈ {10^12, 10^14, 10^16, 10^18, 10^20} (u0 50, H 61, Δ 0.012) × D ∈ {1, 2, 3, 5, 7} × W ∈ {1, 3, 8}: v14b (no checkpoint) state SHA-256, Z-grid bytes, rows and Z strings equal v14's at the same (T, D). v14 reference at W 8. Plus 10^16 legacy (H 4, Δ 0.15, D 2, W 1/8). | 0 mismatches |
| I2 | v14b with a fresh checkpoint (uninterrupted; role gen) equals v14 without one, at 10^14 (D 2, W 1) and 10^20 (D 2, W 8) | equal |
| I3 | Kill and resume at 10^20 (D 2): (a) real SIGKILL after ≥ 300 lines at W 8, resume at W 3; (b) test-hooks lib EXIT_AFTER, resume with the same lib. Both are identical to uninterrupted; verify sample 8/8 passes; items_loaded ≥ 300. | identical |
| I4 | Test-hooks lib with ZFAST14_GENERIC_KERNEL=1 equals production v14b (10^16 D 2 W 4) | equal |
| G1 | v5z8 with wide_1e22's frozen session parameters (H 61, Δ 0.012, D 2, W 8) regenerates atlas_v5z5 wide_1e22 under the same rules as M9 G1: certs 100/100 and certs_np 777/777 canonical; zs/measurements canonical; pieces diff ⊆ {z_provider, zfast_session} with equal v5z5 core keys; replay records identical | all |
| G2 | v5z8 pipeline 10^16 [T0, T0+10]: generator killed in its session (real SIGKILL after ≥ 50 checkpoint lines), then `--resume`, gives a window identical to an uninterrupted v5z8 run, Turing grid bytes included. The replay sidecar shows role replay and the run's nonce; replay_check.json has `zfast_ckpt.ok` true. | identical |
| T0 / T1 | regress_v1 tier 0 and tier 1 PASS (trees unchanged; registers v5z8 only in memory where needed) | PASS |
| TG | `turing_gate all` PASS on every gated record (44 expected incl. M10/M11 if present) | PASS |

## 2. Negative tests: each FAILS (accepts / silent) on v14 and is refused or reported on v14b

At ≤ 10^14, 1 thread, unless marked (H). Scripts and logs go in `runs/m12/neg/`.

| # | finding | test | v14 (predicted) | v14b (predicted) |
|---|---|---|---|---|
| N1 | M1 | Lb shifted by 1 ulp at write time. v14: the reviewer's lbshift build writes, genuine v14 resumes (review_m10/lbshift_test.py). v14b: the test-hooks lib with ZFAST14B_TEST_LBSHIFT=1 writes, the same lib without it resumes. | accepted, all items loaded | refused; the error names `prefast` only |
| N1c | control | test-hooks lib writes without the shift and resumes | n/a | accepted; state = uninterrupted |
| N2 | M1 | a different library build: the production v14b resumes a test-hooks-lib checkpoint (same session) | (v14 analogue: N1, a different build accepted) | refused (`bin`, `lib`) |
| N2b | M1 | header field `flint=` altered and resealed with the key | n/a (no field) | refused, names `flint` |
| N3 | M2 | cross-role: a gen-role checkpoint opened with role replay (same nonce) | accepted (no role) | refused (`role`) |
| N4 | M2 | foreign nonce: a checkpoint of nonce A opened with nonce B, same session | accepted | refused (`nonce` / HMAC key) |
| N5 | m1 | the reviewer's F2: one item's 20 error bounds zeroed, line resealed with plain SHA-256 | accepted; Z radius smaller | line rejected by HMAC, item recomputed, state = honest |
| N5k | m1 | the same forgery resealed WITH the key, verify_n ≥ items | n/a | refused (sample recompute mismatch) |
| N6 | m1 | key-sealed invalid values: mag `1:5`; signed mantissa `-1…`; arb token not canonical | accepted (F3) | refused (validation) |
| N7 | m2 | index i = 2^62 in a line; UBSan scratch builds of the v14 and v14b sources | UBSan reports signed overflow at sched14.inc:200 | no UB report; refused (key-sealed) or ignored (unsealed) |
| N8 | m3 | failed write (RLIMIT_FSIZE, SIGXFSZ ignored) | silent: info shows nothing, file truncated | `ckpt_write_errors` ≥ 1 reported; state = honest |
| N9 | m4 | checkpoint flock-held by another open file description | accepted (two writers) | refused (`locked`) |
| N10 | m5 | simulated pthread_create failure at thread 2 of 4 in Zgrid (scratch v14 + same injection; v14b test-hooks lib) | returns −1 while workers still write to the buffers | returns −1 only after join; buffers stable after return |
| N11 | m7 | D = 17 | accepted, state = D 16 | NULL, explicit error |
| N12 | m8 | ZFAST14_TEST_EXIT_AFTER set: production lib; v5z8 provider import; v5z8 driver start | v14 honours it (rc 77); v5z7 passes it to the replay env | production v14b ignores it (compiled out); provider and driver refuse to start |
| N13 | M2 (H) | pipeline: the generator checkpoint copied over the replay checkpoint path before stage 3 (10^12 smoke, [0, 10]) | v5z7: the replay loads all generator items silently and passes | v5z8: the replay's session is refused, so the replay fails (not closed); fail-safe |
| N14 | m1 | the checkpoint exists but the key file is missing | n/a | refused |
| N15 | format | a v14-format checkpoint given to v14b | n/a | refused (header) |

## 3. Cost (prediction)

- Uninterrupted v14b with a checkpoint, at 10^20 D 2 W 8: build time within ±5% of v14 with a checkpoint (HMAC plus F_FULLFSYNC
  per item).
- Resume verify of 8 items: ≤ 2 item-times of wall time.

## 4. Stops

- Any identity miss (I1–I4, G1, G2): v14b/v5z8 are not used; report.
- Any negative test that v14b accepts: that fix is reported as MISS and is not claimed.
- Watchdog kill or disk < 2 GB: stop that step.

After RESULTS_M12, an independent re-review is requested via `review_v14b/BRIEF.md`. No self-review counts as the review.
