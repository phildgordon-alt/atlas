# review_v14d: independent re-review of libzfast v14d + atlas_v5za (2026-11-03)

**Verdict: PASS WITH CONDITIONS.**

**May the multi-day resumable 10^28 window proceed on v14d / v5za?** **Yes**, under the conditions in §4. I found no path that
yields a wrong Z, accepts a non-canonical or foreign value, or leaves an unresumable checkpoint after an honest interruption or
I/O error. MJ-C1 is closed. The remaining findings are all in the **driver's classification** of a stop (rc 3 against other
codes) or are operational. None touches the library, the compute path or any certificate.

No production run was active (I checked `ps` at the start and between phases). Everything ran at nice 19 under `review_v14d/scratch/`
with W ≤ 2, except the differential's short W3/W8 cases. No session went above 10^20. Every driver run used a **review copy** of the tree
(`scratch/v5za_copy/`), changed in one line only: KEYDIR points to `scratch/keys_drv/`, so `ckpt_keys/` stayed untouched (40
files before and after). I read the v5z7 production checkpoints and did not write to them. Nothing outside `review_v14d/` was written,
and nothing was deleted.

---

## 1. Findings (ranked)

### Critical
None.

### Major
None. MJ-C1 from review_v14c is closed (§2.1).

### Minor

**mn-D1. The driver's `io_abort()` can attribute an earlier attempt's CKPT-IO-ABORT to the current attempt.**
(`atlas_v5za/atlas_v5.py`, `io_abort` and its two call sites.)

- The sidecar test is `x['t'] >= t_since` with `t_since = t_start - 1`, and the function returns the first match in file order.
- For the replay, the check runs even when the replay succeeded (it is not gated on `rc != 0`).
- So a resume that starts less than about 1 s after an earlier I/O abort sees the old record. I reproduced both consequences:
  - **D6** (`scratch/drv_v14d.py`, `drv_logs/d6_tampered.log`). After a generator I/O abort (rc 3), I tampered with the checkpoint
    header and resumed at once. The generator was correctly refused ("header line is not authenticated"), but the driver printed the
    *old* CKPT-IO-ABORT banner and exited 3. That told the operator to "fix the cause and resume", which can never succeed.
  - **D5b** (`scratch/drv2_v14d.py`, `drv_logs/d5b_resume.log`, run `v5za_copy/runs/w10000000000000000/d5b`). A replay I/O abort was
    followed at once by an unlimited `--resume`. The replay **passed** (`replay_check.json`: passed true, zfast_ckpt ok), yet the driver
    logged `ckpt_io_abort` and exited 3 before writing the summary. `run_wideA.sh` would then skip the Turing recount and gate.
- Both recover on a later resume: run a few seconds later, D6 exits 1 with the true reason, and D5b finishes rc 0, bit-identical to
  the reference.
- No soundness impact: no wrong value or certificate, and every outcome fails closed or is merely misreported. It matters only if
  something resumes automatically and immediately (a retry loop, or an agent over RC).
- **Fix** (driver only; the library is not touched):
  - Pass the child's pid, or this attempt's start time with no −1, and match on it.
  - Return the newest matching record.
  - Call the replay check only when `r['rc'] != 0`, or when replay_check did not pass.

**mn-D2. Under a real full disk, the rc-3 classification itself may be lost.**

- The provider's refusal sidecar and `gen.log` are written to the same volume. On ENOSPC (the most likely real cause of an I/O error)
  both writes can fail, and the provider then prints only "could not record the refusal".
- `io_abort()` then finds nothing and the driver ends with an ordinary failure (rc 1, or a traceback if `drive.jsonl` cannot be
  flushed). `run_wideA.sh` goes on to the recount and the gate, which fail.
- The checkpoint itself stays valid, and `--resume` after freeing space works: the pre-build resume path is unchanged and tested.
- For the replay there is no log fallback at all; `replay_target.log` could serve as one.
- Not reproduced: I did not fill a real disk. My I/O tests used RLIMIT_FSIZE, which is a per-file limit, so the sidecar stayed writable.
- Mitigation: condition §4.3.

**mn-D3. A failed header write leaves a checkpoint that no resume accepts.**

- Test `IO_rlimit_inside_header`. The session is refused with `CKPT-IO-ABORT: cannot write the checkpoint header…`. The file now holds a
  torn header, so every rerun is refused with "header line is not authenticated", and a fresh run name is needed.
- The loss is zero items, but the rc-3 banner says "resume".
- In the same area: if the new directory fsync fails, the session is refused, and a later resume of that file never fsyncs the
  directory again.
- Both happen only at second zero of a run. Document them, or truncate a header-only torn file on retry.

**mn-D4. The reboot rehearsal (`tools/reboot_rehearsal_m14/`) is correct, but it tests less than its README says.**

- `step1` SIGKILLs the pipeline. That is not a power cut: the page cache survives a SIGKILL, and Apple-menu Restart flushes it. What the
  rehearsal does test is the condition that matters most here: that the environment pins (dyld cache UUID, library SHAs and so on)
  survive a reboot, so a resume is not refused. It does not test crash durability. That is covered by the 1 s F_FULLFSYNC design,
  which I checked by code reading (max_unsynced ≤ 1.017 s measured), not by a power cut.
- It exercises only the pre-build resume path. It does not exercise the post-build path or the replay.
- Script logic I checked:
  - the kill targets the right pids (`exec` makes `$!` the driver);
  - `no_production` and the 10^20 cap work;
  - the PASS criterion (`items_loaded ≥ lines_at_kill − 2`, `verified == min(64, loaded)`, byte compare of the grid) is sound.
- At 10^20 D4 W8 with 300 lines, the kill lands mid-build, as RESULTS_M14 I3a shows.
- Suggested README wording: "kills the pipeline abruptly (as a crash would; a power cut can additionally lose the last ≈1 s of
  checkpoint lines, which are recomputed)".

### Nits
- **Nonce file removed.** When `zfast_ckpt_nonce.txt` is missing on a post-build `--resume`, the driver first *creates a new nonce file*,
  then refuses (D8, `new_nonce_file_created: true`). Recovery means putting the original back by hand, and the message does not say so.
- **Turing-grid exceptions.** If the Turing grid raises a deterministic exception (not a crash), each `--resume` moves all outputs and
  re-runs the whole post-build phase, and the exception repeats. This is safe but wasteful; an operator should read `gen.log` before
  resuming twice.
- **Symlinked checkpoint paths** are still followed (unchanged from v14c, as the brief says). A dangling symlink *creates its target*
  (`out_sym/`). Exploiting this needs write access to RUN.
- **F_FULLFSYNC fallback.** If `F_FULLFSYNC` fails and plain `fsync` then succeeds, the sync counts as successful (pre-existing).
- **No O_NOCTTY.** The checkpoint is opened without `O_NOCTTY`, so a checkpoint path symlinked to a tty is opened, but then refused by the
  `S_ISREG` check.
- **ASan.** The runtime hangs during initialisation on this macOS 27 / dyld (`sample`: `__sanitizer::get_dyld_hdr`). I used UBSan instead.
  This is not a code problem, but anyone re-running "asan" suites should know.

---

## 2. Answers to the brief's items 1–8

### 2.1 MJ-C1 (`parse_arb_strict`, `zfast_sched14d.inc:387-433`)

**The construction is exact.**

- A mag's value is `MAN·2^(EXP−30)`. With `MAN = m·2^(30−b)` and `EXP = e + b`, the value is `m·2^e`, and the result is
  normalised (`2^29 ≤ MAN < 2^30`) for every `1 ≤ b ≤ 30`.
- `fmpz_get_ui` is safe for b ≤ 30.
- `fmpz_add_ui` on an arbitrary fmpz cannot abort, including mpz-sized tokens of hundreds of digits.
- `mag_valid` then applies the 40-bit bound, and the canonical re-dump check makes acceptance equivalent to "tokens == arb_dump_str of
  the value".

**No new acceptance of non-canonical values:**

- even mantissas, leading zeros, upper case, `-0`, a signed radius, 31+-bit mantissas and zero with a nonzero exponent are all refused;
- no FLINT call reachable from authenticated input can abort: the arb parse uses only `fmpz_set_str`, `arf_set_fmpz_2exp`,
  `fmpz_add_ui` and `arb_dump_str`, all total.

**My test against the real source** (`scratch/rt/rt_rv.c`, one translation unit with `#include "zfast.c"` from `bin/src_v14d`, built
with the production flags; `rt_rv.out`, and `rt_rv_ubsan.out` under UBSan):

| part | cases | result |
|---|---|---|
| A: `arb_randtest`, prec 1–600, mag bits 1–62 | 300,000 | 288,300 accepted, every one exact (arb_equal, mag_equal, identical re-dump). 11,700 refused. Acceptance ⇔ `bits(MAG_EXP) ≤ 40` held in every case. |
| B: every width 1–30 × 13 exponents across the ±2^40 boundary of `EXP = e + b` | 19,500 | parser = independent oracle; every accepted value = m·2^e |
| C: grammar fuzz of all four tokens (lengths up to 8000 bits, leading zero, case, sign, `-0`, even values, 31–80-bit radii) | 1,000,000 | **0 discrepancies** between parser and oracle |

End to end on the **production** dylib (`attack_v14d.py` RAD_*):

- 6,400 key-resealed balls with radius widths 1–30 load (rc 0, 480/480);
- `3fffffff -1f4` loads; v14c refused it;
- a 31-bit radius, an even radius and a radius exponent of 2^40 are refused with a reason and no crash.

The test-hooks R3 path is consistent: a fresh session, a 40 % partial resume and a verify-all resume of a checkpoint whose every first
radius is nonzero all agree (`HOOK_radius_*`).

**The 40-bit radius-exponent bound (R1 "MISS"): it cannot bite an honest moment at 10^28.**

Read-only scan of the v5z7 gen checkpoints (`scratch/mag/scan_exp.py`, `scan_exp.out`):

| run | balls | nonzero radii | radius MAG_EXP | err/V MAG_EXP |
|---|---|---|---|---|
| 1e22 | 106,840 | 0 | n/a | [−295, 10] |
| 1e25 | 245,680 | 348 (all 1-bit) | [−603, −584] | [−196, 12] |
| 1e26 | 267,840 | 1,098 (widths 1–3) | [−611, −569] | [−197, 12] |

- Moment midpoints have top exponents in [−265, −2]. The radii sit about wp ≈ 420 bits below them.
- At 10^28, wp is ≈ 427, so honest |EXP| stays below about 700, against a bound of 2^40 ≈ 1.1·10^12. The margin is about nine orders of
  magnitude *in the exponent*, and the trend 1e22 → 1e26 is flat.
- The only honest value the bound would refuse is an infinite mag (MAN 0, EXP +∞). None occurs in any production file
  (`zero_man_nonzero_exp: 0`), and it would make the session's Z useless anyway.
- R1's literal miss is therefore a statement about arb_randtest's range, not about Atlas data. I agree with the builder's
  classification.

### 2.2 mn-C1 (identical duplicates)

- The classification is made only after the seal has been checked for index x (`zfm_fast14b` calls `load_line` only when `auth`). It
  also comes after `xt == xs`, the bucket and index range checks, `x == first[b] + i` and the (b, i, lo, hi) match (`load_line:445-451`).
- Under v3, the line's tag binds K, SHA-256(the stored header incl. hnonce), x and the body. An identical body for the same item therefore
  means an identical value: the first copy was parsed strictly, and the body determines the value. The ignore cannot change state.
- A line that differs only in its tag is not authenticated, so it is rejected and not counted as a duplicate (`DUP_bad_tag_copy…`). A
  same-body copy with another x is fatal on the x check (`DUP_keyholder_same_body_other_x_fatal`). A conflicting key-holder copy is
  fatal in either order.
- Tests passed:
  - append one copy;
  - insert one copy before the original;
  - double the whole file (dup 480);
  - triple a line with verify-all;
  - torn prefix followed by a full copy;
  - partial file plus a duplicate, resumed twice.

### 2.3 mn-C4 (abort policy, library)

- **(a)** After `ck_fail`, each worker finishes at most its in-flight item. Dispatch checks `ioabort` under `Q.mu`. Measured abort latency
  at 10^14–10^18 was 0.12–0.28 s. At 10^28 the cost is at most W in-flight items of work.
- **(b)** `werr` is incremented only in `ck_fail`. `ioabort` causes a refusal after the join, and `rc == 0 && werr` refuses at the end,
  which also covers a flusher failure in the window between the join and the flusher stop. No returned session can have
  `ckpt_write_errors > 0`. The provider additionally raises if one ever did.
- **(c)** Real partial writes (RLIMIT_FSIZE with SIGXFSZ ignored, the same EFBIG/short-write semantics as a short write) were tested:
  - the limit mid-line at 30 % and at 70 % (W2);
  - exactly at a line end;
  - exactly at the header end;
  - one byte after the header;
  - the last byte missing (the torn line is complete apart from its newline and is correctly loaded);
  - the limit hit during a *resume*;
  - a failed newline repair (the file is left unchanged).

  In each case the session was refused with `CKPT-IO-ABORT`, the file size equalled the limit, and the resume reloaded exactly the
  complete lines, rejected exactly one torn line, and was identical to v14; a verify-all resume of the resume was also identical.
  The test-hook `WFAIL_AT` 1 and 200 cases, and `SYNCFAIL` 1 and 3 at 10^18, also abort and then resume identically. A torn partial
  line cannot authenticate: the seal is the line's last 64 characters.
- **(d)** Every access to `Q.fd` is under `Q.io` (worker writes, flusher) or happens while single-threaded (load, newline repair, header,
  final sync after both joins). A worker holding a built line after another worker's `ck_fail` finds `fd < 0` in `ck_write` and writes
  nothing. `ck_fail` closes the fd and releases the flock while in-flight items are still finishing; that is harmless because the
  process never writes again.
- **(e)** The `abort()` on an unfinished bucket is skipped only on the `ioabort` path, and that path refuses the session. A scheduler bug
  that coincided with an I/O error would therefore be hidden *in a refused session* only. It cannot produce a result.
- **The policy.** Aborting is safe for an unattended run, and preferable to computing for days without protection. The window stops
  until it is resumed, with the checkpoint intact. Watch mn-D1 if the resume is automated.

### 2.4 mn-C4 (pipeline)

The provider writes the refusal sidecar and raises. A non-I/O refusal does not exit 3 when it is the only record in the window: D7
(the replay checkpoint is a FIFO; the reason "not a regular file" is recorded; rc ≠ 3) and D6's later resume (rc 1). Misclassification
is possible within about 1 s of an earlier abort (mn-D1) and under ENOSPC (mn-D2).

| test | result |
|---|---|
| Generator I/O abort | rc 3, banner, a single `ckpt_io_abort` (D6 first leg; the builder's G4) |
| Replay of record I/O abort | caught: rc 3, `role: replay`, banner, file size equal to the limit (D5b first leg) |
| `--resume` after the replay abort | replay passed, identical, once outside the 1 s window |
| `run_wideA.sh` | stops on rc 3 (read) |

### 2.5 mn-C3 (post-build resume)

Driver runs at 10^16 [T0, T0+10], H 91, D2 W2, with the Turing grid. Each run's certificates, zs, measurements and Turing grid were
compared with the reference using `engine/regress_v1 compare_regenerated` plus a byte comparison of `grid.npz` and
`zeros_intervals.json`:

| test | outcome |
|---|---|
| D2b: generator killed after `gen_done`, before the grid record | moved 7 outputs; session 1075/1075 loaded, 64 verified; identical; replay passed |
| D3: killed in the certificate stage (1 cert written) | moved; identical; replay passed |
| D9: a bogus `cert_BOGUS_PLANTED.json` planted in `certs/` before the resume | moved into `gen_postbuild.attempt1/certs/`, absent from RUN/certs; identical; replay passed |
| D4: replay killed during its session → `--resume` | the replay resumed its own checkpoint; identical; passed |
| D8: nonce file removed | refused, nothing moved (see the nit about the new nonce file) |

**Can a stale output be reused?** No:

- every generator output (zs.json, certs, certs_np, gen_measurements.json, turing_grid, gen.log, gen.jsonl) is moved before the generator
  re-runs, and the generator recreates all of them;
- the replay, crosscheck and summary read only RUN/certs, RUN/certs_np, RUN/gen.jsonl and replay_check;
- no consumer globs recursively, so `gen_postbuild.attempt*/` is invisible;
- `turing_recount.json` is regenerated on every `run_wideA.sh` pass.

**Can it run with a different nonce or key?** No:

- the nonce is read from RUN;
- the path requires a gen-role sidecar record of that nonce;
- the library binds the role, nonce and key in the authenticated header;
- a replaced or removed nonce file is refused by the driver (G3n (iv), D8).

**Earlier refusals are not weakened:**

- a `replay_check/` or `zfast_ckpt_replay.txt` present refuses (N13 misrouting is still caught);
- `--resume` is required;
- pieces.json pins `turing_grid`, so `want_tg` cannot change between attempts.

**`gen_finished` without `--turing-grid`** reduces exactly to v5z9's `gen_done`.

### 2.6 Nits: FIFO, NUL, header, directory fsync

| check | result (timings in parentheses) |
|---|---|
| FIFO checkpoint | refused (0.1 s) |
| FIFO key | refused (0.1 s; the v14c hang is gone) |
| symlink to `/dev/null` | refused |
| directory | refused |
| NUL in a key-sealed item | rejected (`lines_nul` 1), recomputed, identical |
| NUL in the header | refused |
| 8 KiB NUL tail, resumed twice | identical |
| 4 KiB zero block mid-file | identical |
| header with a double space, a trailing double space or a tab (resealed) | refused (`format (whitespace)` / `fieldcount` / `format`) |
| `ckpt_dir_synced` | 1 |
| `O_CREAT` race | no TOCTOU of concern. An existing FIFO is opened `O_NONBLOCK` and refused by `fstat`; the FIFO is never created. |
| symlinks | still followed (nit) |

### 2.7 Test hooks

- Production `libzfast.v14d.dylib` has no `ZFAST14*TEST` strings and no `_getenv` import. The test-hooks build has both.
- The provider and the driver each refuse `ZFAST14D_TEST_WFAIL_AT`, `_SYNCFAIL`, `_RADIUS`, and any other `ZFAST14D_TEST*`. The driver
  check was run from the review copy.
- `th_radius(S, R, x)` is called identically after `mom_range` in `wq_worker` and in `vq_worker` (same x), so R3 tests what it claims.

### 2.8 Compute path and identity

- **The rebuild is reproducible.** `src/build_v6/v7/v8.sh` were copied into `scratch/rb/src` and run on a copy of `bin/src_v14d`. They
  reproduce `libzfast.v14d.dylib` e0ed15f3…, `libzfast.v14d_testhooks.dylib` e6c011ce… and both CLIs **byte for byte**, and the source
  SHAs match `bin/SHA256.v14d`.
- **Sources.**
  - The following are byte-identical to v14c, and those that were part of v14 also to v14: `zfast.c`, `zfast_m3c.inc`, `zfast_api3.c`,
    `zfast_api4.c`, `zfast_hash14.inc`, `zfast_cli2.c` and `zfm4_cli.c`.
  - `zfast_m3b.inc` changes only the include, two record fields and comments.
  - The sched diff (`sched14c_to_sched14d.diff`) touches no compute function. In an uninterrupted session it adds one atomic load per
    dispatch, plus hook code that exists only under `#ifdef ZF_TEST_HOOKS`.
- **My differential** (`scratch/diff_rv.py`): **29/29** cases × 6 sessions bit-identical to v14 (state, grid, rows, Z). Up to 10^20, W
  ∈ {1, 2, 3, 8}, D ∈ {1, 2, 3, 5, 7}, fresh / checkpointed / full resume / partial resume / resume of resume, verify all. Every partial
  resume rejected exactly 1 torn line. Max `max_unsynced_s` was 1.017.
- **Kill/resume** (`kill_rv.py`): **9/9** identical, 18 real SIGKILLs.

---

## 3. Tests run (all under `review_v14d/scratch/`)

| suite | file | result |
|---|---|---|
| reproducible rebuild | `rb/` | SHAs equal |
| differential v14d against v14 | `diff_rv.py`, `diff_rv.log` | 29/29 |
| kill/resume | `kill_rv.py`, `kill_rv.log` | 9/9 |
| v14c attack suite (+ provider checks for the ZFAST14D_* vars) | `attack_rv.py`, `attack_rv.log` | 73/75 pass. The 2 "fails" are the deliberate mn-C1 change: identical duplicates are now ignored, rc 0, honest. |
| v14c fuzz, new seed 4242 | `fuzz_rv.py`, `fuzz_rv.log` | 362 cases, 0 crash / hang / watchdog. The 26 "rc1" cases are accepted key-holder forgeries, as in v14c. |
| parser oracle fuzz on the real source | `rt/rt_rv.c`, `rt_rv.out`, `rt_rv_ubsan.out` | 0 discrepancies, 1.32 M cases |
| production exponent scan (read-only) | `mag/scan_exp.py`, `scan_exp.out` | see §2.1 |
| new-path attacks | `attack_v14d.py`, `attack_v14d.log`, `out_a14d/` | 47/48. The one fail was my own relative-symlink test bug, redone correctly in `out_sym/` (followed, as documented). |
| driver tests | `drv_v14d.py`, `drv2_v14d.py`, logs in `drv_logs/` | D1, D2b, D3, D4, D7, D8 and D9 OK. D5b and D6 reproduce mn-D1. My first D2 and D5 attempts missed their kill windows (10^16 builds in under 1 s) and were redone as D2b and D5b. |

## 4. Conditions for the 10^28 window

1. **Do not resume automatically within seconds of a stop, or fix mn-D1 first.** The fix is in the driver only; the library is
   unchanged and need not be rebuilt.
   - After any rc 3, read the newest line of `<ckpt>.refusals.jsonl` before acting.
   - If the replay's `replay_check.json` says passed, just `--resume` again.
2. **Keep review_v14c §3.2 in force for the whole window**:
   - no macOS, RSR or BSI update (automatic updates off);
   - no `brew` command;
   - the same Mac;
   - the same `ckpt_keys/` and run directory, not moved.
3. **Disk watchdog with margin** (mn-D2): keep ≥ 5 GB free, not 2. Swap files and local snapshots share the APFS container, and only
   7.0 GB were free during this review. If it fires, stop the window cleanly instead of letting ENOSPC hit.
4. **Run Phil's reboot rehearsal before the window, if possible** (review_v14c §3.3; mn-D4).
   - If it is skipped, the window may still run: a resume refused after a reboot fails closed.
   - The cost of that refusal would be a full restart, not a wrong result.
