# review_v14c: independent review of libzfast v14c + atlas_v5z9 (2026-11-02)

**Verdict: PASS WITH CONDITIONS.**

**May a multi-day resumable 10^28 run proceed on v14c?** **Not yet.** First fix one new defect (MJ-C1 below; a few lines) and
re-run the differential tests. A 10^28 run on the current v14c build would compute correct Z values: nothing I found can make a
session, fresh or resumed, accept a wrong value. But its checkpoint could become permanently unresumable exactly when it is needed.
With MJ-C1 fixed and the operational conditions in §3 met, v14c/v5z9 is fit for the window.

Summary of what I checked:

- **The compute path is unchanged.** My rebuild of both dylibs from `bin/src_v14c` with the build_v6 flags reproduces 59883f5e…
  and 9c0d4a9b… byte for byte. All compute-relevant functions are textually v14b's, which are v14's: `merge_bucket`,
  `cmp_len_desc`, `vq_worker`, `verify_sample`, `items_free`, `prefast_digest`, the item construction in `zfm_fast14b`, and
  `wq_worker` except for the new x argument.
- **The differential is bit-identical to v14 in every case**: 29 cases × 6 sessions = 174 sessions, comparing
  state, grid, rows and Z. The sessions were fresh with no checkpoint, fresh with a checkpoint, a full resume, a partial resume
  from a torn file, and a resume of that resume, all with verify = all items and W ∈ {1, 2, 3, 8}, D ∈ {1, 2, 3, 5, 7}, up to
  10^20.
- **Kill/resume.** 9 trials (six at 10^18 D2, three at 10^20 D3), 18 real SIGKILLs at random times (others landed after completion), including during header
  load, the verify phase and the head part. Every final resume, and every verify-all resume, was bit-identical to v14, and none
  produced a duplicate.
- **MJ1 is closed.** Lines from another session, another file with the same parameters, another hnonce or another index are never
  loaded under one key (72-case attack suite with my own v3 sealer).
- **mn1–mn7 are closed in code, with one exception: the mn1 rewrite introduced MJ-C1.**

No production run was active (I checked `ps` at the start and during the work). Everything ran at nice 19 under
`review_v14c/scratch/`, with W ≤ 2 except for short W3/W8 differential cases, and an RSS watchdog of 2.5 GB on every probe. No
session exceeded 10^20. Nothing outside `review_v14c/` was written or modified, and nothing was deleted. I only *read* the v14
production checkpoints in `atlas_v5z7/runs/…/wide7_1e2{2,5,6}/`.

---

## 1. Findings

### Critical
None. No path was found that yields a wrong Z or an underestimated radius from an uninterrupted session, or from a resumed session
whose checkpoint was not forged by a key holder.

### Major

**MJ-C1 (new in v14c, from the mn1 fix): the parser refuses honest balls with a nonzero radius whose mantissa has 30 bits. Such a
line is authenticated, so the refusal is fatal and the whole resume is refused.**

- **Where.** `zfast_sched14c.inc:393`, `parse_arb_strict`:
  `mag_set_fmpz_2exp_fmpz(arb_radref(x), f[2], f[3])` followed by the canonical re-dump check (`:397`).
- **The cause.** `mag_set_fmpz_2exp_fmpz` returns an *upper bound*, not the exact value. When the radius mantissa has exactly
  `MAG_BITS` = 30 significant bits (which a mag can hold exactly), FLINT 3.6.0 rounds it up by one ulp. The re-dump then differs
  from the tokens, so `load_line` returns 0 and `zfm_fast14b` refuses the session with `fatal = 3`. These lines are *not* merely
  rejected and recomputed.
- **Measured.**
  - `scratch/radtest/bits.c`: for odd radius mantissas of 1–29 bits, 0/20000 are inexact at each width. At 30 bits,
    **20000/20000** are inexact.
  - `scratch/radtest/radtest.c`: 35,417 of 138,238 random nonzero-radius `arb_randtest` balls (25.6 %) fail to round-trip through
    v14c's construction.
  - End to end on the production dylib (`scratch/t3/`): an honest 10^14 line whose first moment ball is given the radius
    0x3fffffff·2^-500 and resealed (`105fecff98dc35197 -45 3fffffff -1f4`, exactly what `arb_dump_str` emits for that ball):
    - **v14c refuses**: rc 3, "authenticated but invalid: arb value not canonical / not finite / radius not a valid mag".
    - **v14b accepts the same line**: rc 0, 480 loaded.
  - This is a regression against v14b.
- **Do honest lines carry nonzero radii?** Not in any test: 771,320 moment balls in my 10^14–10^20 checkpoints all have radius
  `0 0`, so no identity or resume test by the builder or by me ever exercised this path. But the production v14 checkpoints of the
  same compute path do (read-only scan, `scratch/radtest/rad_*.txt`):

  | run | wp | widest midpoint mantissa | balls with nonzero radius |
  |---|---|---|---|
  | wide7_1e22 | 408 | 377 bits | 0 |
  | wide7_1e25 | 418 | 418 bits (= wp) | 348 |
  | wide7_1e26 | 421 | 421 bits (= wp) | 1,098 |

  - The moments are sums of hi/lo doubles accumulated with `arb_add(…, wp)` (`zfast_m3b.inc:244-247`). Their exact width grows
    much faster with T than wp does: 153 / 275 / 322 / 377 bits at 10^14 / 18 / 20 / 22, against wp 381 → 408. From 10^25 on,
    the width saturates wp, `arb_add` rounds, and radii appear.
  - At 10^25 and 10^26 every radius mantissa is still 1, 3 or 5. These are a few roundings within one or two binades, and all of
    them round-trip (`radtest/reload.c`: 0/1,446 refused).
  - A 30-bit mantissa appears as soon as `mag_add` combines two rounding errors more than 29 binades apart, which then needs
    rounding up. A synthetic accumulation of the same kind at wp 427 produced such radii in 313 of 2000 trials (`radtest/accum.c`).
  - At 10^28 the excess of width over wp is larger, and there are more items. I could not run 10^28 (the 10^20 cap), so whether
    the 10^28 session produces such a radius is **unproven but plausible**, and the trend points towards it.
  - The consequence of a single such ball anywhere in the file: *every* resume of that checkpoint is refused, and the run needs a
    fresh name (new nonce and key), which means a full recomputation.
- **Not a soundness issue.** It fails closed. But it defeats the checkpoint for exactly the target use. It also falsifies two
  claims:
  - RESULTS_M13 / the code comment "a loaded honest ball equals the dumped one bit for bit": what actually happens is that it is
    *refused*.
  - The brief's assumption that "an honest line rejected would only cost recomputation": an authenticated line that fails to parse
    is fatal.
- **Fix** (tested): `scratch/radtest/fix2.c`, 300,000/300,000 random finite balls round-trip bit for bit. Build the mag exactly:
  - (a) refuse if `fmpz_sgn(f[2]) < 0 || fmpz_bits(f[2]) > MAG_BITS`;
  - (b) `MAG_MAN(r) = fmpz_get_ui(f[2]) << (MAG_BITS - b)`, where `b = fmpz_bits(f[2])`;
  - (c) `fmpz_add_ui(MAG_EXPREF(r), f[3], b)`;
  - keep `mag_valid` and the canonical re-dump check.

  This is the construction that `parse_mag_strict` already uses for the err and V mags, which is why those 30-bit mags round-trip.
  `arf_get_mag` is *not* a fix: it also rounds up (207,419 of 300,000 failed; `radtest/fix.c`).
- **Regression test to add.** An `arb_randtest` round-trip of `parse_arb_strict` (nonzero radii, all mantissa widths 1–30), plus
  a resume test on lines that contain nonzero radii, e.g. the t3 case above sealed honestly by the test-hooks build.

### Minor

- **mn-C1. One copied line, with no key, makes a checkpoint permanently unresumable.**
  - Appending (or inserting) a byte-identical copy of any authentic line is refused as "identical duplicate", which is fatal. Tests:
    `attack_rv.py` `nokey_identical_duplicate_*`. In v14b such a copy was ignored.
  - I found **no honest path** that writes an item twice under one header. I checked by code reading: the worker writes once per
    computed item, loaded items are never recomputed, `verify_sample` never writes, a torn line is never authenticated, and the
    newline repair is a single `\n`. I also checked by test: 29 partial resumes, each followed by a resume of the resume, in the differential, the
    kill/resume trials, 16 truncation offsets and NUL-padded tails. None produced a duplicate.
  - So the decision is fail-safe, but it is not free. Under the v3 binding, a byte-identical authenticated duplicate is provably
    harmless: same header hash, same index, same body, hence the same value. Refusing it turns any accidental `cat >>` or
    sync-tool replay into the loss of a multi-day checkpoint. Anyone with write access to RUN can already destroy a checkpoint
    (truncate the header), so the gain is only "evidence".
  - Recommendation: count identical duplicates (`lines_duplicate`, which is now always 0) and warn, and refuse only *conflicting*
    duplicates, which require the key. At minimum, document the recovery: deleting the extra line restores the file to an honest
    state.
- **mn-C2. Environment pins: benign changes that refuse a resume (operational, for the 4-day window).**
  - Correct by design, but each of the following forces a fresh run name:
    - a Homebrew upgrade of flint, gmp or mpfr, including the implicit dependent upgrades of any `brew install` or `brew upgrade`;
    - a macOS update, including Rapid Security Responses or Background Security Improvements, which replace the Cryptex shared
      cache;
    - moving to another Mac.
  - Verified here:
    - `dyld_cache_uuid` (ea2c265e…) equals the UUID in the header of the signed on-disk cache
      `/System/Volumes/Preboot/Cryptexes/OS/…/dyld_shared_cache_arm64e` (mtime Sep 2026, before the Oct 30 boot). It is therefore
      stable across reboots and changes only with an OS or cryptex update.
    - Automatic macOS, config-data and critical updates are currently **off** (`com.apple.SoftwareUpdate`).
  - I could not reboot, so a *resume across a reboot*, the very path the checkpoint exists for, is untested by me. Conditions §3.2
    and §3.3.
- **mn-C3. Driver: a crash after the session build makes the complete checkpoint unusable** (pre-existing since v5z7, not v14c
  code, but an operational risk for the window).
  - `atlas_v5.py:214-216` allows `--resume` only while `zs.json`, `turing_grid/` and `certs/*` are absent.
  - `zs.json` is written right after the session is built (`gen_target5.py:65-67`). A generator death after that loses the whole
    session. Examples: power loss; the `guarded` memory limit (`V4_LIM_GB`, 1.0 GB by default in `run_wide9.sh`) killing the
    certificate stage; a crash during the Turing grid after `gen_done`.
  - The fresh name the driver demands creates a new nonce and key, so the old checkpoint cannot be reused.
  - At 10^26 this post-build phase was about 300 s against 16,345 s of build (`atlas_v5z7/…/wide7_1e26/gen.jsonl`), so the window
    is small but not empty.
  - Recommendation: document (or implement) a recovery path that reuses a complete checkpoint, or at least set `V4_LIM_GB` with
    margin for the 10^28 certificate stage.
- **mn-C4. A checkpoint write or fsync error stops checkpointing for the rest of the run, and the only signal is stderr.**
  - `ck_write` / `ck_sync` close the fd (`:446`, `:459`). The session continues, correctly, but for a 4-day run a transient error,
    such as a full disk, means that the remaining days are unprotected.
  - The provider warns only after the build returns (`zfast_provider.py:127`).
  - Recommendation: a watchdog check on the checkpoint's mtime and growth during the window, beside the existing disk floor.

### Nits / notes
- **Key FIFO hang.** `key_load` opens the key `O_RDONLY` without `O_NONBLOCK` before the `S_ISREG` check (`:613`), so a FIFO at
  the key path blocks the session forever (`attack_rv.py` `key_fifo`: timeout). This needs write access to `ckpt_keys/`. Use
  `O_NONBLOCK`, or `lstat` first.
- **NUL bytes.** A NUL byte inside an *authenticated* line ends parsing early, so junk after it is accepted (`fuzz_rv.py`
  `nul_then_junk`). This needs the key, so it is a nit.
- **Double spaces in the header.** `header_diff` still collapses runs of spaces: a key-resealed header with a double space is
  accepted. Its own lines then cannot load, because the header hash differs.
- **Stale field.** `lines_duplicate` is now always 0.
- **Misleading message.** "this checkpoint is not resumable past it" (`:817`): the file *is* resumable; the lines after the error
  are simply missing.
- **Directory fsync.** The checkpoint file's directory entry is not fsynced after `O_CREAT`. A power loss within about a second of
  creation could lose the new file. The cost is recomputation only.
- **Pins on fresh runs** (pre-existing). The provider pins only libzfast's SHA. FLINT, GMP and MPFR are pinned only for resumes
  (header), not for fresh runs or the replay of record.
- **python-flint.** python-flint bundles a second `libflint.24.0.dylib`. libzfast still binds Homebrew's copy whatever the import
  order. Tested: a checkpoint created in a process that imported `flint` first resumes in one that did not
  (`probe_withflint.py`, `t1/`).

---

## 2. Answers to the brief's items

1. **MJ1 line binding.**
   - My sealer (`scratch/rvlib.py`) is written from the C source and reproduces every honest tag.
   - A line authenticates only under the header body it was written for, hnonce included, and at its own index x:
     - A's lines spliced into B's file under one key: 40/40 rejected in each of 3 trials, state = honest B.
     - All of A's lines under B's header: 480 rejected, 0 loaded.
     - A second checkpoint *with identical session parameters* under the same key: all 480 of the first file's lines rejected.
     - Header transplant: 0 loaded.
     - A changed x token: rejected, state honest.
   - The x token parsed before the MAC is safe:
     - it is at most 21 digits and must be followed by a space;
     - `parse_dec_ul` rejects leading zeros and overflow;
     - it is used only as MAC input;
     - `load_line` re-parses it and requires `xt == xs` and `x == first[b] + i` with matching (b, i, lo, hi). With the key, a
       mismatch is fatal (tested).
   - Domain separation is sufficient. The HMAC inputs `"ZF14C-HDR\0"…` and `"ZF14C-ITEM\0"…` differ at byte 9. A first line is
     checked only as a header, and later lines only as items.
   - The reviewer's v14b splice and the v14b-format file are refused, because the header is not authenticated.
2. **Duplicates.** There is no honest path that writes an item twice (see mn-C1). The fatal decision is fail-safe, but I recommend
   ignoring identical duplicates.
3. **Key reuse.** Binding is enough. A new header under an existing key gets a fresh 128-bit hnonce, so every line is sealed with
   SHA-256(header incl. hnonce), and nothing from an earlier file can load (tested: A2, B). The reuse is reported (stderr note,
   `key_reused_new_header` 1). Refusing would only break the crash recovery between key creation and header write. One
   suggestion: put `key_reused_new_header` and `key_created` into the driver's `ckpt_sessions_gen` summary.
4. **mn1.**
   - (a) In 362 key-resealed targeted and random cases on the production dylib, with verify 0 so that forged values reach the
     merge and the Z / row evaluation, I saw **0 crashes, 0 hangs and 0 watchdog kills**. The cases included 30,000-hex-digit
     midpoint mantissas and exponents, 5000-digit radius mantissas, mag exponents at ±(2^40 − 1), 2^40, 80-digit exponents, inf,
     nan, signed zero, 2^64, tabs, double spaces and NUL. Every non-canonical token was refused with a reason. The 25 cases with
     "rc1" are accepted key-holder forgeries whose Z output is not valid JSON; the driver would fail closed on those. This is
     consistent with the trust model.
   - **(b) is false for nonzero radii with 30-bit mantissas (MJ-C1).** For zero radii, which is all honest data ≤ 10^22, and for
     the err/V mags, honest lines load bit-identically. Midpoints are exact via `arf_set_fmpz_2exp`, and mags are set directly
     from MAG_MAN / exponent.
5. **mn2 flusher.**
   - The code is correct:
     - the wait is relative (`pthread_cond_timedwait_relative_np`, 1 s);
     - `ck_sync` runs under `Q.io`, and the only threads that touch the fd hold `Q.io`;
     - `fstop` is set and signalled under the same mutex and the thread is joined before the final sync and the close, so there is
       no lost wakeup and no closed fd;
     - every refusal path happens before the flusher starts;
     - there are no FLINT calls (`now()` is `clock_gettime(CLOCK_MONOTONIC)`).
   - Measured `max_unsynced_s` ≤ 1.017 s over all differential sessions (≈1.00–1.01 s on the multi-second ones), which
     matches the claimed bound of "write time + 1 s + one F_FULLFSYNC".
   - F_FULLFSYNC runs while holding `Q.io`, which briefly blocks workers that want to write a line. This is negligible at 10^28
     item lengths.
6. **mn3.**
   - `image_text_sha` hashes [mach header, header + `__TEXT.filesize`) in memory. For this dylib `__TEXT` has fileoff 0 and
     filesize = vmsize = 98304. Its in-memory hash (adc231e7…) equals the SHA-256 of the file's first 98304 bytes, so it is stable
     across processes and ASLR slides; arm64 `__TEXT` carries no fixups.
   - Remaining gaps, both small: `__DATA_CONST` of libzfast is not hashed in memory (only through `bin_sha` of the file), and
     FLINT, GMP and MPFR are pinned by file SHA plus LC_UUID, not by their mapped text (a TOCTOU only against an in-place
     replacement).
   - The operational consequence: mn-C2.
7. **mn4.** I tested:
   - symlink, 0644, 33-byte, directory and 0-byte keys: all refused with a specific reason;
   - a 0400 key: accepted;
   - a hard link: accepted (same user);
   - KEYCRASH (test hooks, rc 78): no final key, one 32-byte temp file, an empty checkpoint; the rerun creates a fresh key and is
     identical;
   - a FIFO: hangs (nit).

   `renamex_np(RENAME_EXCL)` cannot replace an existing key. A concurrent creator loses with EEXIST and refuses.
8. **mn5 / mn6.**
   - `ck_err` keeps the first message.
   - Line cap at 10^28: na = 20 and nw = 1 (K = 18, J = 12, independent of T). At wp 427 the formula gives 32,864, so the cap
     stays 64 KiB. Honest lines are about 2.0 KB at 10^14 and at most 3.7 KB at 10^26 (the v14 production checkpoint), so there is a margin of
     about 17×. An honest line cannot be rejected as overlong.
   - The overlong test: a 64 MiB line gave maxrss 25.4 MB against 25.3 MB for a plain resume, and the result was identical.
9. **mn7.**
   - Adequate. After MJ1 only a key holder can forge, and the key holder has the same trust as the code. The sample is then defence
     in depth against bugs, and against systematic corruption it is near-certain to catch (all-item forgery refused). Against a
     single forged item the detection rate is 64/N (I saw 0/10 at 8/480, as expected).
   - Cost: about 64/N of the session per resume. At 10^28 (N in the low 10^4) that is about 0.5 % of the window, tens of minutes,
     per resume.
10. **Compute path.** Confirmed by source diff, a bit-identical rebuild and the differential (§4). In an uninterrupted session the
    only additions are the header (Mach-O walks and one SHA-256), line building and sealing per item, and the flusher.

## 3. Conditions for the 10^28 resumable window

1. **Fix MJ-C1**, using the exact mag construction above. Add the `arb_randtest` round-trip regression test. Rebuild into new
   v14d trees, re-run the differential and the attack and fuzz suites, and re-pin the provider. The diff is a few lines in
   `parse_arb_strict`; a short focused re-review of that function and of the identity results is enough.
2. **Freeze the environment for the window.** Keep macOS automatic and security updates off (they are off now). No `brew`
   install, upgrade or cleanup, and set `HOMEBREW_NO_AUTO_UPDATE=1` and `HOMEBREW_NO_INSTALL_UPGRADE=1` in any shell an agent
   uses. Run on this Mac only.
3. **Rehearse a resume across a reboot** at ≤ 10^20 before the window: build part of a checkpoint, reboot, then `--resume`. This
   is the one checkpoint path that no one has tested.
4. Recommended, not blocking:
   - mn-C1: ignore identical duplicates, or document the recovery;
   - mn-C3: a post-build recovery path, or a `V4_LIM_GB` margin;
   - mn-C4: a checkpoint-growth watchdog.

## 4. Tests run (all under `review_v14c/scratch/`)

| script / log | what | result |
|---|---|---|
| `rb/build_rv.sh` | rebuild of both dylibs from a copy of `bin/src_v14c`, build_v6 flags, same relative paths | 59883f5e…, 9c0d4a9b… identical |
| `diff_rv.py` / `diff_rv.log`, `out_diff/diff_results.json` | v14 vs v14c ×5 modes (no ckpt; fresh ckpt; full resume verify-all; partial (45 % torn) resume verify-all; resume of resume), 10^14 D{1,2,3,5,7}×W{1,3,8}, 10^18 D{1,2,3,5,7}×W{1,3} + D{2,5}×W8, 10^20 D{3,7}×W2 | 29/29 identical (174 sessions); every partial resume rejected exactly 1 torn line; max_unsynced 1.017 s |
| `kill_rv.py` / `kill_rv.log` | random SIGKILLs (fresh, resume, load/verify phase), then a final resume and a verify-all resume | 9/9 identical to v14, 18 real SIGKILLs, 0 duplicates or refusals |
| `attack_rv.py` / `attack_rv.log`, `out_attack/attack_results.json` | 72 cases: splice (cross-session, same-params, transplant), key-holder duplicates and forgeries, index tampering, duplicates, shuffle, removal, 16 torn offsets, NUL tail, CRLF, blank line, 10 header tampers, role/nonce/format/hooks crossover, key-file cases, overlong, provider hook and verify pins | 71 as designed; key FIFO hangs (nit) |
| `fuzz_rv.py` / `fuzz_rv.log`, `out_fuzz/fuzz_results.json` | 62 targeted + 300 random key-resealed numerics mutations, production dylib, verify 0, RSS / time watchdog | 0 crashes / 0 hangs; 241 refused, 96 accepted (canonical key-holder values or ignored), 25 accepted with invalid Z JSON |
| `radtest/{bits,radtest,reload,accum,fix,fix2,mk}.c`, `t3/` | MJ-C1: exactness by mantissa width, random round-trip, real 10^22/25/26 radii, synthetic accumulation, candidate fixes, end-to-end v14c vs v14b | see MJ-C1 |
| `t2/` | flock: a second session on a live checkpoint | refused "locked" |
| `probe_withflint.py`, `t1/` | header identity with python-flint imported first | resumes |
| (shell) | `dyld_cache_uuid` vs the on-disk Cryptex cache header; SoftwareUpdate settings; production dylib imports and strings | equal; auto-install off; no `getenv`, no hook strings |
