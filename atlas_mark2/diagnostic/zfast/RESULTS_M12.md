# RESULTS_M12: libzfast v14b + atlas_v5z8 (checkpoint hardening after review_m10), 2026-11-02

**Pre-registration.** `PREDICTIONS_M12.md`, sha 8920c920… (`PREDICTIONS_M12.sha256`, check OK). It was hashed at 09:50, before
any v14b code was written. Phil approved the build on 2026-11-02.

**Scheduling.**
- 09:50–10:08: light work only, while M11 ran (started 09:46). This covered code, the build, the 10^14 single-thread negative tests
  and a 1-thread 10^12 pipeline smoke.
- 18:57: M11 finished (`runs/m11/m11.log`: "M11 done", all processes gone). RESULTS_M11.md had not yet been written; that is the
  caller's.
- 18:58–19:40: heavy gates, one at a time, nice 19, under the footprint ≤ 3 GB / disk ≥ 2 GB watchdog
  (`runs/m12/gates/watchdog.sh`; no kills, no disk events).

Manifest: `MANIFEST_M12.sha256` (38 files).

## 0. Answer first

- **Every review finding is fixed in new trees.**
  - The finding fixes are M1, M2, m1, m2, m3, m4, m5, m7 and m8. m6 is documented and mitigated, as pre-registered.
  - The new trees are `src/v14b`, `bin/src_v14b`, `bin/libzfast.v14b.dylib` (sha d77bf28f…), the separate
    `bin/libzfast.v14b_testhooks.dylib` (cb05f4ff…) and `atlas_v5z8/` (V5Z8_FREEZE, 36 entries).
  - v14, v5z7 and every frozen tree are untouched.
  - Flags are unchanged: `-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math`, via `src/build_v7.sh`, which is `build_v6.sh` plus the
    test-hooks lib.
- **Identity: MET.**
  - v14b equals v14 bit for bit (state SHA-256, Z-grid bytes, rows, Z strings) on 77/77 comparisons. The matrix was 10^12–10^20 ×
    D {1,2,3,5,7} × W {1,3,8}, plus the 10^16 legacy session.
  - v5z8 regenerates wide_1e22 exactly (G1).
  - A SIGKILLed and resumed session is identical at 10^20 (I3a) and through the pipeline at 10^16 (G2).
- **Negative tests: MET.** All 24 negative and control checks behave as predicted. Each check that a finding fix was meant to change
  fails on v14 (accepted / silent / UB) and is refused or reported on v14b.
- **Gates.** regress tier 0 PASS, tier 1 PASS, turing_gate all PASS (43/43), and all four v5z8_gate reports PASS.
- **Deviations (§4).** One amendment, A1: group-commit fsync, decided before the official build. Three wording misses: the N2 field
  names, the N7 index value, and the TG count (43, not 44). One limitation is disclosed: a key-holder forgery passes a verify-8
  resume with probability about 1 − 8/N.
- **Status.** v14b/v5z8 are **not yet the production engine.** They await the independent re-review (`review_v14b/BRIEF.md`). Until
  it passes, v5z7/v14 remain production under the review_m10 interim rule (never resume across an environment or library change;
  never cross-load role files).

## 1. What was built (diff vs v14: `review_v14b/lib_v14_to_v14b.diff`, `sched14_to_sched14b.diff`, `pipeline_v5z7_to_v5z8.diff`)

**Unchanged files.** The compute path is byte-unchanged: `zfast.c`, `zfast_m3c.inc`, `zfast_api3.c`, `zfast_api4.c`, `zfast_hash14.inc`
and the CLIs keep identical SHAs. In `zfast_m3b.inc`, only the session struct fields, the hook guards, the constructor wiring and the
info output change. The scheduler and merge in `zfast_sched14b.inc` are v14's code.

| finding | fix |
|---|---|
| M1 | The `ZFAST14B CKPT v2` header adds `prefast` (SHA-256 of nbeg/Lb/Xb/tau0 and nb/Nw/nhead/wp/K2, recomputed by the resuming process). It also adds `lib` (an identity string plus the compiler version), `bin_sha` (the loaded zfast image, via dladdr), the flint/gmp/mpfr versions plus `*_sha` of their dylibs, `os` (kern.osversion) and `hooks`. Any mismatch refuses, and the message names each field. |
| M2 | `zfa14b_new(…, role, nonce, keyfile, verify_n)`. The header's role and nonce must match the caller's. The v5z8 driver creates one nonce per run (`RUN/zfast_ckpt_nonce.txt`, O_EXCL) and per-role key paths. The provider writes `CKPT.sessions.jsonl`. `replay_target5` (v5z8) makes `passed` depend on every replay session record being role replay with the run's nonce, and stores `zfast_ckpt` (items_loaded etc.) in replay_check.json. |
| m1 | **Decision: both layers.** (a) Every line is sealed with HMAC-SHA256 under a per-run, per-role 32-byte key, created by libzfast (O_EXCL, 0600) in `diagnostic/zfast/ckpt_keys/` (0700, outside every RUN). A line that fails its HMAC is ignored (torn write) and counted. (b) An authenticated line is strictly validated: hex-only tokens, canonical re-serialisation, normalised finite mags with exponent < 2^40, finite arbs; a failure is fatal. (c) On resume, `verify_n` random loaded items (provider default 8) are recomputed and must be bit-identical. **Trust model:** the key gives authenticity against anything without it; a key holder is trusted like the code. The sample recompute is an independent, probabilistic content check. |
| m2 | `i` is range-checked against the bucket's T before any index arithmetic; integers are parsed with overflow checks. |
| m3 | Every write(2) is checked. F_FULLFSYNC (fallback fsync) is checked after the header, at most once per second, and at the end (amendment A1). Any error gives a stderr message and `ckpt_write_errors`, and checkpointing stops while the session continues unaffected. The provider warns. I/O runs under its own mutex. |
| m4 | flock(LOCK_EX \| LOCK_NB) for the whole session build. |
| m5 | Zgrid joins every started thread before returning −1. |
| m6 | Unchanged by design. Mitigated by the gate's cross-process Z/grid identity checks and by the resume sample recompute. |
| m7 | D ∉ [1, 16] gives NULL with an explicit error, from both zfa14_new and zfa14b_new; the provider checks too. |
| m8 | Test hooks are compiled only with `-DZF_TEST_HOOKS` (the testhooks dylib). The production dylib ignores the env vars. The v5z8 provider refuses to import and the driver refuses to start when any `ZFAST14*_TEST*` / `ZFAST14_GENERIC_KERNEL` variable is set, and children never inherit them. |

`zfa14_new` in v14b refuses any checkpoint path, so v14-format checkpoints cannot be used.

## 2. Predictions: MET / MISS

### Identity

| # | outcome | verdict |
|---|---|---|
| I1 | `reports/v5z8_identity_20261102_185804`: 75 matrix + 2 legacy comparisons, 0 mismatches; control D1 ≠ D2 state | **MET** |
| I2 | a fresh checkpoint equals no checkpoint at 10^14 (D2 W1) and 10^20 (D2 W8; 1,460 lines for 1,459 items) | **MET** |
| I3a | SIGKILL at 307 lines (W 8), resume at W 3: 306 loaded, 8/8 verified, 0 rejected, identical; resume 6.5 s | **MET** |
| I3b | test-hooks EXIT_AFTER 120 (rc 77), resume: 120 loaded, 8 verified, identical to production v14 | **MET** |
| I4 | GENERIC_KERNEL=1 (test-hooks lib) equals production at 10^16 | **MET** |
| G1 | `reports/v5z8_w1e22_20261102_191817`: certs 100/100 and certs_np 777/777 canonical; zs.json and gen_measurements.json **byte**-identical; pieces diff = {z_provider, zfast_session} with equal core; replay summary and records identical. Wall 699 s, peak 0.033 GB (driver). | **MET** |
| G2 | `reports/v5z8_ckpt_20261102_191305`: pipeline 10^16, generator SIGKILLed at 280 checkpoint lines, then `--resume` (W 4 → 8). The window is identical to an uninterrupted v5z8 run, Turing grid bytes included. The resumed generator session loaded 279 items and verified 8/8. The replay sidecar shows role replay with the run's nonce, ok true. | **MET** |
| T0 / T1 | `reports/tier0_20261102_193011` PASS (lean out-of-scope now also lists v5z7_wide7_1e26); `reports/tier1_20261102_193200` PASS | **MET** |
| TG | `reports/turing_all_20261102_194041` PASS, 43/43. I had predicted 44; `gate_all` does not pick up v5z7 windows, and M10/M11 each have their own turing_check PASS. | **MET** (count wording MISS) |

### Negative tests

Sources: `runs/m12/neg/out_official/negtests.json` (production v14b and testhooks libs, 10^14, W 1), `out_extra_official/neg_extra.json`,
`n12_pipeline.json` and `reports/v5z8_n13_20261102_191648`.

| # | v14 (observed) | v14b (observed) | verdict |
|---|---|---|---|
| P1/P2 controls | – | a full checkpoint resumes (480/480 loaded, 8 verified, identical); a torn checkpoint (200 lines + half a line) loads 200, rejects 1, identical | **MET** |
| N1 M1 Lb +1 ulp | reviewer's lbshift build → genuine v14 loads 480/480; the state differs from honest | refused, `field(s) [prefast]` only | **MET** |
| N1c control | – | the test-hooks lib writes without the shift and resumes: 480 loaded, identical | **MET** |
| N2 M1 other build | (v14 has no pin; see N1) | production refuses the test-hooks checkpoint, `[bin_sha,hooks]` | **MET** (predicted field names `bin, lib`; `lib` is equal because both builds share the source and compiler) |
| N2b | – | `flint=` altered and key-resealed → refused, `[flint]` | **MET** |
| N3 M2 cross-role | gen file loaded by another session: 480/480 | same key → `[role]`; driver-style per-role key → header not authenticated | **MET** |
| N4 M2 foreign nonce | accepted 480/480 | same key → `[nonce]`; own key → key missing, refused | **MET** |
| N5 m1 zeroed bounds, SHA reseal (review F2) | loaded 480, state ≠ honest, max radius 4.97e-11 < 5.00e-11 (underestimate) | HMAC rejects the line (1 rejected), item recomputed, state = honest | **MET** |
| N5k key-holder reseal | – | verify_n ≥ items → refused ("resume verification FAILED"). **Disclosed:** with verify_n = 8 the forgery was accepted (state ≠ honest); detection is 8/480 here. | **MET** (limitation disclosed) |
| N6 m1 invalid values | `1:5`, `-20000000:5` and a non-canonical arb token all accepted (480 loaded) | all 3 refused ("authenticated but invalid") | **MET** |
| N7 m2 huge index | UBSan build: i = 2^63−1 → "signed integer overflow: 470 + 9223372036854775807" at sched14.inc:200 and a pointer overflow at :201. i = 2^62 → no UB (no overflow; the existing `x >= nit` guard drops it). | UBSan build: no report at either value; key-sealed → refused ("item index out of range"); unsealed → ignored, state = honest | **MET** (registered value 2^62 does not trigger UB in v14; 2^63−1 does; disclosed) |
| N8 m3 failed write | RLIMIT_FSIZE: rc 0, no info field, file silently truncated at 77 lines | `ckpt_write_errors` 1, 77 written, stderr message, state = honest | **MET** |
| N9 m4 lock | wrote 481 lines while another process held the lock | refused ("locked"); accepted after unlock (480 loaded) | **MET** |
| N10 m5 | (scratch v14 + injected failure) returned −1 after 0.1 ms; the buffer was still changing after return (805/797 points written) | returned −1 after join; buffer stable; threads 0, 1 complete (5000/5000), threads 2, 3 none | **MET** |
| N11 m7 D = 17 | accepted, state = D 16 | zfa14b_new and zfa14_new refuse; D 16 = v14 | **MET** |
| N12 m8 | production v14 honours EXIT_AFTER (rc 77); v5z7's replay env is `dict(os.environ)` | the production v14b ignores it (rc 0, generic 0, identical); the test-hooks lib honours it (rc 77); the v5z8 driver and provider refuse for 3 hook vars; no run dir created | **MET** |
| N13 M2 pipeline | v5z7: the generator checkpoint copied to the replay path → the replay loads it all (file unchanged), passes, window "closed" | v5z8: replay session refused (header not authenticated), replay fails, `zfast_ckpt.ok` false, driver rc 1, not closed (fail-safe) | **MET** |
| N14 | – | key missing → refused | **MET** |
| N15 | – | v14-format file → refused (key missing / not authenticated / zfa14_new refuses checkpoints) | **MET** |

### Cost (§3)

- Checkpointed build at 10^20 D2 W8: v14 16.42 s, v14b 17.03 s, ratio **1.037**. **MET** (band ±5%).
- Resume verify of 8 items: the I3a resume took 6.5 s wall for the whole session tail. **MET**.
- At 10^14: 0.74 s vs 0.65 s.

## 3. Light-phase facts (development; disclosed)

- **Dev builds.** `runs/m12/dev/` (libdev, libdev_th): the first full negative run gave 20/20 OK.
- **Measurement that led to A1.** An honest v14b checkpointed 10^14 session took 3.58 s, against 0.66 s for v14. The cause was
  F_FULLFSYNC per line.
- **v5z8 smoke.** Run at 10^12 [0, 10], D 1 W 1, in a scratch copy of the tree: closed 10/10, replay sidecar ok, 115 s.
- **Keys.** The smoke and gate runs created key files in `ckpt_keys/`; they are test keys. Do not delete them: no deletes, per the
  rules.

## 4. Deviations and amendments

- **A1 (10:00, before the official build and before any claim-bearing test).** The pre-registration said "F_FULLFSYNC per item".
  It became group commit: a checked write per line, plus a checked F_FULLFSYNC after the header, at most once per second, and at
  session end.
  - Reason: the measured 5× overhead at 10^14 (§3) would have broken the §3 cost prediction at 10^20.
  - Effect: a power loss can lose at most about one second of items. Those lines are torn or missing, are detected (HMAC), and are
    recomputed.
- **Wording misses.** N2 field names, the N7 index value, and the TG count. Each is detailed in the tables above; none changes a
  verdict.
- **Not done.** v5z8 is not inside regress tier 0 (FROZEN.json v2 is still the pending amendment noted in RESULTS_M10). It is gated by
  `engine/regress_v1/v5z8_gate.py`, a new file: no existing gate or tier file was changed.

## 5. What this does and does not establish

- **What it establishes.** A resumed v14b/v5z8 session either loads only items written by the same library build, session, run and
  role under the same environment, or it refuses. The ball computations are v14's, unchanged. So the review's M1 and M2 conditions
  are met in code rather than by operating rule.
- **The residual trust assumption.** It is the key directory (`ckpt_keys/`, 0700). A process holding a key can forge lines that
  pass the HMAC. Such a forgery is caught only by the sample recompute, with probability 8/N per resume, or by the replay of record
  (for certificate rows). The Turing grid is generator-only (review M1 note) and has no such second check. Raising
  ZFAST_CKPT_VERIFY trades resume time for coverage.
- **Self-review does not count.** v14b/v5z8 are **not** used for any claim until the independent re-review (`review_v14b/BRIEF.md`)
  passes.
