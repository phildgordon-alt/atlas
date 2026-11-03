# PREDICTIONS_M14: libzfast v14d + atlas_v5za (closing review_v14c), pre-registration (2026-11-02)

Hashed (`PREDICTIONS_M14.sha256`) **before** any v14d code is written, built or run. Input: `review_v14c/REVIEW.md` (PASS WITH
CONDITIONS; major MJ-C1; minors mn-C1..mn-C4; nits). Goal: a checkpoint layer fit for the multi-day resumable 10^28 window.

**Rules.** nice 19; one heavy job at a time; footprint watchdog <= 3 GB (8 GB Mac; brief cap 4 GB); disk floor 2 GB; never `python -O`
/ PYTHONOPTIMIZE; no session above 10^20; `ps` checked first, no competing production run; HOMEBREW_NO_AUTO_UPDATE=1
HOMEBREW_NO_INSTALL_UPGRADE=1 in every shell, no brew command. New dirs/files only: `src/v14d`, `bin/src_v14d`,
`bin/libzfast.v14d.dylib`, `bin/libzfast.v14d_testhooks.dylib`, `bin/SHA256.v14d`, `bin/BUILD_ENV.v14d.txt` (built by the unchanged
`src/build_v8.sh`, i.e. build_v7 -> build_v6, flags `-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math`), `atlas_v5za/`,
`tools/make_v5za.py`, `tools/m14_rt/`, `tools/reboot_rehearsal_m14/`, `runs/m14/`, `engine/regress_v1/v5za_gate.py`, `review_v14d/`,
`RESULTS_M14.md`, `MANIFEST_M14.sha256`. Nothing in v14 / v14b / v14c / v5z7 / v5z8 / v5z9, any frozen tree or `ckpt_keys/` is
modified; nothing is deleted (superseded items are moved aside with a README).

## 0. Design (fixed here)

The compute path stays v14's byte for byte: `zfast.c`, `zfast_m3c.inc`, `zfast_api3.c`, `zfast_api4.c`, `zfast_api14.c`,
`zfast_hash14.inc`, the CLIs are byte copies of `bin/src_v14c`. `zfast_sched14d.inc` replaces `zfast_sched14c.inc`; `zfast_m3b.inc`
changes only the include, info fields and comments; `zfast_api14b.c` only `"lib": "v14d"`. In `zfast_sched14d.inc` the items,
`split_ranges`, `merge_bucket`, `cmp_len_desc`, `verify_sample` and `mom_range` calls are unchanged; `wq_worker` adds only an abort check
before taking the next item (F3); test hooks are compiled only with `-DZF_TEST_HOOKS`. ctypes API names and signatures unchanged
(`zfa14b_new`, `zfa14b_info`, `zfa14b_last_error`), so v14d is a drop-in; lib id `zfast-v14d(PREDICTIONS_M14)`; the file format string
`ZFAST14C CKPT v3`, the line format and the HMAC domains are unchanged (a v14c checkpoint is refused by v14d through the lib / bin_sha /
bin_uuid / bin_text_sha pins, as any library change is).

| finding | v14d fix |
|---|---|
| MJ-C1 | `parse_arb_strict` builds the radius exactly, as `parse_mag_strict` does: refuse if the radius mantissa token has more than MAG_BITS = 30 significant bits; `MAG_MAN = m << (30 - bits)`, `MAG_EXP = e + bits` (fmpz); the canonical re-dump check and `mag_valid` stay. No FLINT rounding setter is used for the radius. |
| mn-C1 | An authenticated line byte-identical (body SHA-256) to the already loaded line for its item is **ignored and counted** (`lines_duplicate`); it is neither loaded again nor rejected. A *conflicting* authenticated duplicate (different body) stays fatal. |
| mn-C4 | **Abort policy.** Any checkpoint write or fsync error (worker line write, flusher F_FULLFSYNC, newline repair, header write, final sync, directory fsync of a new file) aborts the session: no further item is dispatched, in-flight items finish, `zfa14b_new` returns NULL and `zfa14b_last_error` starts with `CKPT-IO-ABORT:` and names the error and the lines written. The checkpoint stays valid up to the error (a torn last line is rejected on resume), so `--resume` after fixing the cause reloads it. Reason: a multi-day run continuing without checkpoint protection is exactly the failure the checkpoint exists to prevent; the abort costs at most the in-flight items. A successful session therefore always has `ckpt_write_errors` 0. |
| mn-C4 (pipeline) | v5za provider: a refused session appends `{t, pid, role, nonce, ckpt, error}` to `CKPT + '.refusals.jsonl'` and raises; a session with `ckpt_write_errors` > 0 raises (defence in depth). v5za driver: if the generator's or the replay's refusal sidecar holds a `CKPT-IO-ABORT` record from this attempt, it logs `stage=ckpt_io_abort`, prints a banner to stderr and exits **rc 3** before any later stage; `run_wideA.sh` stops on rc 3 (no recount / gate) and logs it. |
| mn-C3 | v5za driver `--resume` after the session build (zs.json / certs / certs_np / gen_measurements.json / turing_grid exist, no `gen_done`): allowed only with `--resume --wide`, while `replay_check/` and `zfast_ckpt_replay.txt` do not exist, the run's nonce file and generator checkpoint exist, and the generator sidecar `zfast_ckpt_gen.txt.sessions.jsonl` holds >= 1 record with role gen and the run's nonce. Then every generator output (zs.json, certs/, certs_np/, gen_measurements.json, turing_grid/, gen.log, gen.jsonl) is **moved** into `RUN/gen_postbuild.attempt<k>/` (never deleted) and the generator re-runs with the same nonce and key; its session reloads the complete checkpoint (verify 64). Every library refusal (role, nonce, key, header, pins, duplicates, parse) is unchanged; outside this case the driver's "use a fresh --name" refusal is unchanged. |
| nit FIFO | Key file and checkpoint file are opened with `O_NONBLOCK`, `fstat` must show a regular file before any read (else refused, "not a regular file"), then `O_NONBLOCK` is cleared. |
| nit NUL | A line containing a NUL byte is never authenticated: a header with NUL refuses; an item line with NUL is rejected (counted in `lines_rejected` and `lines_nul`). |
| nit header_diff | The stored header body (without hnonce) must equal the expected body byte for byte; a whitespace-only difference refuses (`format (whitespace)`). |
| nit message | The "not resumable past it" message is gone (F3 replaces it). |
| nit dir fsync | After a new checkpoint's header is durable, its directory is fsynced (F_FULLFSYNC, fallback fsync); failure = CKPT-IO-ABORT refusal before any item. |
| suggestion | v5za driver `ckpt_sessions_gen` also records `key_created`, `key_reused_new_header`, `lines_nul`. |

**Test hooks (test-hooks dylib only; the production dylib has none; the v5za provider/driver refuse every `ZFAST14D_TEST*` variable):**
`ZFAST14D_TEST_WFAIL_AT=n` (the n-th item-line write fails with EIO), `ZFAST14D_TEST_SYNCFAIL=n` (the n-th flusher fsync fails with
EIO), `ZFAST14D_TEST_RADIUS=1` (after every `mom_range`, in the worker and in the verify recomputation, every moment ball's radius is set to
m·2^e with m odd of width w = 1 + ((7x + 2a + c) mod 30) bits, so every width 1..30 occurs; honest library-written lines then carry
nonzero radii including 30-bit mantissas).

## 1. MJ-C1 regression (permanent: `tools/m14_rt/`, also `v5za_gate --roundtrip`)

| # | prediction | pass rule |
|---|---|---|
| R1 | `rt_arb` compiled from `bin/src_v14d` itself (static functions via one translation unit): >= 300,000 random finite `arb_randtest` balls (prec 1-400, mag bits 1-60) + >= 300,000 balls with radius mantissa width drawn uniformly from 1..30 (>= 10,000 exactly 30 bits, odd and even exponents, mid zero and nonzero) round-trip through `parse_arb_strict` bit for bit (`arb_equal` and dump string) | 0 failures |
| R1c | control: the same generator through the v14c construction (compiled from `bin/src_v14c`) | >= 1 failure, every 30-bit-radius ball fails, 0 failures below 30 bits |
| R1n | non-canonical radius tokens (31+ bits, even mantissa, negative, leading zero) are refused by v14d without abort | all refused, no signal |
| R2 | every moment ball of the v5z7 production checkpoints wide7_1e22 / 1e25 / 1e26 (gen and replay; read-only) through v14d `parse_arb_strict` | 0 failures; >= 1,446 nonzero radii seen |
| R3 | test-hooks RADIUS=1, 10^14 D2 W1: fresh no-ckpt state S_R; checkpoint with EXIT_AFTER 120 (rc 77), resume verify-all: rc 0, loaded 120, rejected 0, state = S_R; the file contains >= 1 radius token of 30 bits; second resume of the complete file, verify-all, W3: loaded = items, state = S_R | all |
| R3c | control: the same RADIUS file is never fed to v14c (other pins); instead, the reviewer's t3 case: an honest production 10^14 checkpoint with the first moment radius key-resealed to `3fffffff -1f4`: v14c production refuses (rc 3, "not canonical"); v14d production accepts (rc 0, all loaded; verify 0, the value is a key-holder forgery and the state differs from honest, as designed) | both |

## 2. Fixes F2-F5 (light, 10^14 D2 W1, `runs/m14/neg/`)

| # | test | v14c (observed in review) | v14d (predicted) |
|---|---|---|---|
| D1 | identical copy of an authentic line appended / inserted before the original (no key) | refused "identical duplicate" | rc 0, state honest, `lines_duplicate` 1, loaded N, rejected 0 |
| D2 | key-holder conflicting duplicate (either order) | refused | refused "conflicting duplicate" (unchanged) |
| E1 | RLIMIT_FSIZE 150000 (SIGXFSZ ignored) | rc 0, last_error, unprotected rest | rc 3, reason starts `CKPT-IO-ABORT`, names "File too large"; resume without limit: rc 0, loaded >= 1, rejected <= 1, state honest |
| E2 | hook WFAIL_AT=50 | n/a | rc 3 `CKPT-IO-ABORT` (write, EIO), file has 49 item lines (+ header); resume: loaded 49, identical |
| E3 | hook SYNCFAIL=1 on a 10^18 D2 W1 session (several seconds) | n/a | rc 3 `CKPT-IO-ABORT` (fsync); resume: rc 0, identical |
| N1 | key path is a FIFO | hang (timeout) | rc 3 within 20 s, "not a regular file" |
| N1b | checkpoint path is a FIFO / a directory | (FIFO not tested) | rc 3 within 20 s, refused |
| N2 | authenticated line with a NUL byte then junk (key-resealed), and NUL mid-line | accepted | line rejected (`lines_nul` 1), rc 0, state honest |
| N2b | header line with a NUL byte | n/a | rc 3 |
| N3 | key-resealed header with a double space | accepted (lines then unloadable) | rc 3, "whitespace" |
| N4 | new checkpoint: directory fsync performed (`ckpt_dir_synced` 1 in info) | not done | 1 |

## 3. Identity (acceptance rule: bit-identity; any miss means v14d/v5za are not used for claims)

| # | prediction | pass rule |
|---|---|---|
| I1 | M13 matrix (T 10^12..10^20 × D {1,2,3,5,7} × W {1,3,8} + 10^16 legacy) v14d no-ckpt vs v14: state, grid, rows, Z | 77/77 identical; control D1 ≠ D2 |
| I2 | fresh checkpoint = no checkpoint (10^14 D2 W1, 10^20 D2 W8) | equal |
| I3a / I3b / I4 | SIGKILL >= 300 lines at 10^20 W8 + resume W3; test-hooks EXIT_AFTER 120 + resume; generic kernel | identical |
| I5 | reviewer's `diff_rv.py` on v14d (29 cases × {no ckpt, fresh, full resume verify-all, 45 % torn resume verify-all, resume of resume}; D {1,2,3,5,7}, W {1,2,3,8}, to 10^20) | 29/29 |
| I6 | reviewer's `kill_rv.py` on v14d (random SIGKILLs incl. load/verify phase, then final + verify-all resume) | 9/9 identical, 0 duplicates or refusals |
| G1 | v5za regenerates atlas_v5z5 wide_1e22 (G1 rules) | PASS |
| G2 | v5za pipeline 10^16: generator SIGKILLed in its session build, `--resume` | identical (window, Turing grid), verified 64 |
| G3 | v5za pipeline 10^16: generator SIGKILLed **after** zs.json exists (during the Turing grid), `--resume` | window + Turing grid identical to an uninterrupted run; resumed session items_loaded = items, verified 64; old outputs in `gen_postbuild.attempt1/`; nothing deleted |
| G3n | refusals kept: (i) post-build state without `--resume`; (ii) with `replay_check/` present and generator not done; (iii) generator sidecar removed (moved); (iv) nonce file replaced (library refuses the header nonce) | each refused, rc != 0, no generator output moved in (i)-(iii) |
| G4 | v5za pipeline 10^16 under RLIMIT_FSIZE (driver process, SIGXFSZ ignored): generator session aborts | driver rc 3, `stage=ckpt_io_abort` logged, banner on stderr, no replay; then `--resume` without the limit: window identical to the uninterrupted run |
| N13 | generator checkpoint misrouted to the replay (as M12/M13) | v5za replay refuses, rc != 0 |
| C | checkpointed build at 10^20 D2 W8: v14d / v14 | <= 1.05 |

## 4. Earlier suites, re-run on v14d (each must still refuse what it refused)

- M12 negative tests (`runs/m13/neg/negtests_m13.py` copied to `runs/m14/neg/negtests_m14.py`), with exactly one changed expectation:
  N8 (RLIMIT_FSIZE) is now rc 3 `CKPT-IO-ABORT` (F3) instead of rc 0 with a warning. All others as M13: 20/20.
- M13 attack suite (`attack_m13.py` -> `attack_m14.py`), changed expectations only: A1c (identical duplicate) -> ignored and counted
  (D1); A6 -> E1. All others as M13: 25/25.
- Reviewer v14c suite (`review_v14c/scratch/attack_rv.py`, `fuzz_rv.py`, adapted copies in `runs/m14/rv/` pointing to v14d / v5za),
  changed expectations only: `nokey_identical_duplicate_*` -> rc 0, duplicate counted, honest; `key_fifo` -> rc 3 (no hang);
  `keyholder_header_double_space` -> rc 3; fuzz `nul_then_junk` / `nul_mid` -> rejected, honest; `rad_3fffffff` -> accepted canonical.
  Everything else as the reviewer recorded (71 + FIFO).
- UBSan + libgmalloc build of `src/v14d` + driver: 300 re-sealed mutations at seed 2026 and 300 at seed 7: 0 crashes, 0 sanitizer
  reports.

## 5. Gates

regress_v1 tier 0 PASS, tier 1 PASS, `turing_gate all` PASS; `engine/regress_v1/v5za_gate.py` in every mode (`--roundtrip`,
`--identity`, `--ckpt`, `--postbuild`, `--ioabort`, `--n13`, `--w1e22`) PASS.

## 6. Reboot-resume rehearsal (prepared, NOT executed)

`tools/reboot_rehearsal_m14/` with a step-1 script (start a checkpointed v5za window at <= 10^20, stop it mid-session after >= 300
checkpoint lines, record an environment fingerprint), a step-2 script (after Phil reboots: compare the fingerprint, `--resume`, compare
against an uninterrupted reference) and README with Phil's exact steps. Only a script smoke test at 10^12 **without** a reboot is run
(labelled as such); the rehearsal itself is Phil's action.

## 7. Stops

Any identity miss: v14d/v5za not used; report. Any earlier refusal now accepted (other than the pre-registered changed expectations):
MISS, reported. Watchdog kill or disk < 2 GB: stop that step. After RESULTS_M14, a focused independent re-review is requested via
`review_v14d/BRIEF.md`; self-review does not count, and v14c/v5z9 rules stay in force until it passes.
