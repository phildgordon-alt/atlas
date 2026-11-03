# review_v14b: independent review of libzfast v14b + atlas_v5z8 (2026-11-02)

**Verdict: PASS WITH CONDITIONS.**

The compute path is v14's. I checked this by diffing the source and by rebuilding the library: the rebuilt production and test-hooks dylibs are byte-identical to the shipped ones. A 36-case differential shows v14b = v14 bit for bit (state hash, Z grid, rows and Z strings), with and without a checkpoint and on full resume. M1, M2 and m2–m8 are closed in code.

One **major** design gap remains (MJ1). A checkpoint line's seal is not bound to the session or header it belongs to, and an existing key is silently reused for a new checkpoint. As a result, authentic lines from a *different session* of the same run and role are accepted. I demonstrated this: a wrong Z ball was accepted in 6 of 6 trials, and building the file did not require reading the key. The driver never produces such a file on its own, so this is not critical. It does falsify RESULTS_M12 §5 ("loads only items written by the same … session"). The fix is cheap.

**Conditions** for replacing v14 in multi-day resumable 10^26–10^28 sessions that feed certificates and the Turing grid:

1. **Fix MJ1 in code.** Bind every line MAC to the header, and refuse conflicting duplicates. Re-run the splice test (`scratch/attack_rv.py` §6). It must refuse.
   - Interim rule until then: never move, rename or recreate a run's checkpoint file. A different session always gets a fresh run name.
2. **Fix mn1** (FLINT abort instead of a refusal) before relying on the "strict parser" claim.

Everything else is minor or a nit.

No production run was active (checked with `ps`). All tests ran at nice 19 with ≤ 4 threads, under `review_v14b/scratch/`. Nothing outside `review_v14b/` was modified. One exception: one scratch session briefly wrote two files under `/tmp` while I smoke-tested the driver, and I deleted them immediately.

---

## Findings

### Critical
None found. No path was found that yields an underestimated radius or a wrong Z from an *uninterrupted* session, or from a resumed session built only by the pipeline.

### Major

**MJ1. Line seals are not bound to the session, existing keys are reused for new checkpoints, and conflicting duplicates are silently ignored. Together these let a mismatched checkpoint be accepted.**

- **What is sealed.** `ck_seal_write` MACs only the line body (`zfast_sched14b.inc:315-320`). `hmac_hex(want, Q.key, line, len-66)` checks only the body (`:517-522`). Neither the header, the prefast digest, the nonce nor the session parameters enter a line's MAC. A line is tied to its session only through the key and through (b, i, lo, hi).
- **Key reuse.** `key_load` opens and uses an existing key file even when the checkpoint is empty, that is, when a *new* header is being created (`:436-447`, `may_create` only matters when the key is missing). Within one run and role (key path `ckpt_keys/{nonce}_{role}.key`), two different sessions can therefore both be sealed under one key. One example: the checkpoint is moved aside, then `--resume` runs with a different `--zfast-center`.
- **Duplicates.** `load_line` returns "duplicate (ignored)" for a second line of an already-loaded item *without comparing contents* (`:280`). The first line wins.
- **Demonstration** (`scratch/attack_rv.py` §5–6, log `scratch/attack_rv.log`). Setup:
  - Session A: 10^14, u0 = 50.
  - Session B: u0 = 50.5, a fresh checkpoint with A's key file at the key path. The library accepted it and wrote a new header.
  - The spliced file is B's header, then 2 of A's lines (same (b, i, lo, hi), different content), then all of B's own lines.
  - Result: resumed with verify_n = 8, it was **accepted 6/6**, and the **state, grid and Z differed from honest B in 6/6**. Z(u0 + 0.123456789) came out as [0.42032058… ± 3.05e-11] against an honest [0.51307264… ± 3.05e-11]. That is a disjoint ball: an unsound value.
  - Building the file needs no key access: only files the library itself wrote, plus `cat`.
  - Detection is the 8/N sample only (8/480 here). In the Turing grid there is no replay behind it.
- **Why not critical.** The v5z8 driver never creates a second session under one key: the checkpoint path is fixed, a header mismatch refuses, and nothing renames checkpoint files. Two deliberate manual file operations are needed.
- **Fix** (a few lines; keep the format version bump honest):
  - (a) MAC each item line as `HMAC(key, SHA256(header_body) ‖ line_body)`. Alternatively, derive a per-header subkey `k_h = HMAC(key, header_body)` and seal lines with `k_h`.
  - (b) On a duplicate of a loaded item, compare it byte for byte with the first line and refuse if they differ.
  - (c) Optionally, refuse to create a header when the key file already exists and the checkpoint is empty, unless the key is newer than the checkpoint file. This is the crash-between-key-and-header case. Simplest: write the header first, then create the key. Note that (a) alone already closes the splice.

### Minor

- **mn1. The strict parser can abort the process instead of refusing.**
  - Trigger: an authenticated line in which an arb radius (or midpoint) has mantissa 0 and exponent ≠ 0 (e.g. `… 0 4 …`).
  - Effect: FLINT throws inside `arb_load_str` ("FLINT exception (General error): (arf_set_fmpz_2exp_dump)"), and the process gets SIGABRT with no refusal reason (`zfast_sched14b.inc:259`).
  - Found by a 150-case re-sealed fuzz under UBSan + libgmalloc (7/150 aborts, all of this class; no UBSan report, no heap overrun). Confirmed on the production dylib (`scratch/flint_abort.py`, rc −6).
  - Not unsound, since the process dies, and it needs the key. But the "every field validated, invalid ⇒ refuse" claim is incomplete.
  - Fix: before calling `arb_load_str`, check that a zero mantissa implies a zero exponent for both pairs, or parse the four tokens with `fmpz_set_str` and use `arf_set_fmpz_2exp` / `mag` setters directly.
  - ASan could not be used: it hangs in shadow-memory init on this macOS. I used UBSan plus `libgmalloc` instead.
- **mn2. The group-commit loss bound is misstated (amendment A1).**
  - Actual behaviour: `ck_sync` runs only when a later write happens ≥ 1 s after the last sync (`:292-300`). A line written < 1 s after a sync stays unsynced until the *next item completes*, which at 10^26+ can be minutes to hours later.
  - What A1 claims: "≤ ~1 s of items".
  - The actual bound: the lines written within 1 s before the last sync-triggering write, which can be several items of compute.
  - Correctness is unaffected (torn or missing lines are recomputed; tested), but the claim should be fixed. Options: a 1 s flusher thread that syncs a dirty fd, or sync immediately whenever the previous line is older than 1 s.
- **mn3. Gaps at the edges of the environment pin.** These are not soundness issues: items are self-contained rigorous enclosures, and the merge-relevant state (nbeg, Lb, Xb, tau0, nhead) is in `prefast`.
  - (a) libm and the rest of libSystem are pinned only through `kern.osversion` (`:140`), since they live in the dyld shared cache. Also pin the shared-cache UUID (`_dyld_get_shared_cache_uuid`). Optionally pin `hw.model`.
  - (b) `sb_image` writes the constant placeholders `no-image` / `unreadable` (`:128-129`). Two environments that both fail would then compare equal. Refuse instead.
  - (c) `bin_sha` hashes the file at the `dladdr` path at header time, not the loaded image. This is a TOCTOU against an in-place replacement, which the build scripts prevent. The LC_UUID of the loaded image would be stronger.
- **mn4. Key lifecycle.**
  - A crash between `open(O_EXCL)` and `write` of the key leaves a 0-byte key. The checkpoint is then empty and refuses forever (tested: "not a 32-byte key file"); under the no-delete rule that means a fresh run name.
  - The key directory entry is not fsynced. After a power loss, the header could persist while the key does not, which also means refusal.
  - The mode and owner of an existing key are not checked.
  - None of this is unsound.
- **mn5. Error reporting.**
  - Write and fsync failures in workers set the *worker's* `__thread zf14b_err` (`:42`, `:298`, `:309`), so `zfa14b_last_error` on the creating thread does not show them. The `ckpt_write_errors` counter does, and the provider warns on it.
  - `Q.written--` after a failed newline repair makes the count −1 (`:540`).
  - `zfa14b_new` returns NULL on a bad T0 without setting the error, so the message can be stale or empty (`zfast_api14b.c:16`).
- **mn6.** `getline` reads unauthenticated lines of unbounded length before the MAC check (`:512`). Anyone with write access to RUN can make the resume allocate huge memory. That is a DoS, not unsoundness. Cap the line length at about 2× the expected length.
- **mn7. Trust model for the Turing grid.** The model is acceptable: whoever can read `ckpt_keys/` can also edit the library and pipeline. But with MJ1 open, generator-only data has only the 8/N sample against a splice. Even after the fix, consider a larger `ZFAST_CKPT_VERIFY` for generator sessions that feed the Turing grid; 64 costs about 64 items per resume.

### Nits
- Tags are compared with `memcmp` rather than in constant time (`:520`). There is no oracle in this threat model.
- `header_diff` collapses runs of spaces. This is harmless because headers are authenticated.
- `sprintf` deprecation warning (`:64`).
- `zfa14_new` with threads ≤ 0 now refuses rather than taking the default (`zfast_api14.c:14`, `zfast_m3b.inc:406`). This is intentional (m7), but it changes the API for any v13b-era caller.
- The flock is held only during the session build; the fd is closed at the end of `zfm_fast14b`. This is by design: my kill test saw the lock free once a session had finished building. Document it.

---

## Answers to the brief's items

1. **Compute path.**
   - Unchanged files: `zfast.c`, `m3c`, `api3`, `api4`, `hash14`, `cli2` and `zfm4_cli` are byte-identical to `bin/src_v14`.
   - Changes in `m3b`: exactly the listed ones (struct fields; `#ifdef` hooks; the ckpt argument type; guards; `zfm_info14b_ck`).
   - Scheduler: items, `split_ranges`, `merge_bucket` and the longest-first order are textually v14's. The only additions on the hot path are a lock/unlock of the I/O mutex per item, and line I/O when a checkpoint is on.
   - Flags: `build_v7.sh` calls `build_v6.sh` unchanged (the same `-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math`). My rebuild in `scratch/rb/` reproduces both dylib SHAs exactly (d77bf28f…, cb05f4ff…).
   - Differential (`scratch/diff_rv.py`, `diff_rv.log`): **36/36 identical**. Each case compares four runs: v14 reference W1; v14b via `zfa14_new`; v14b with a fresh checkpoint; v14b resumed from the complete checkpoint with a different W and **verify_n = all items**. Coverage: 10^14 D ∈ {1, 2, 3, 5} × W ∈ {1..4}; 10^18 the same; 10^20 D ∈ {3, 5} × W ∈ {1, 4}. At 10^18 and 10^20, D changes the item count (483 / 689 / 874 / 1205; 828 / 1229), so the uneven decomposition is exercised.
   - m6: `prefast_digest`, `dladdr`, file hashing and `arb_dump_str` use no FLINT constant caches. The main-thread cache history is unchanged, and the identity tests confirm this.
2. **M1.**
   - The digest is recomputed by the resuming process from its own session state (`ckpt_header` → `prefast_digest(S)`, `:145-154`). It is never read from the file.
   - It covers nbeg, Lb (raw bits), Xb, tau0, nb, Nw, nhead, wp, K2 and nw. The header separately carries u0, H, Delta, K, J, D, kind, bmax, interp and nitems.
   - `kcorr` and `verbose` are not used by the fast part.
   - Libm calls *inside* items (`log2tau` / `choose_B` / `block_setup`) are covered only by `os` and `bin_sha`. A change there alters only an item's internal block partition. Each item is still a rigorous enclosure, and the sample recompute would catch it with near certainty, because every item changes.
   - `ZF_EC` / `RDEG` are covered through `bin_sha`. The production library reads no environment variables (`nm -u`: no `getenv`; `strings`: no hook names).
   - LBSHIFT (test-hooks build) → refused `[prefast]`. A test-hooks checkpoint loaded by production → refused `[bin_sha, hooks]`.
   - `header_diff`: swapping, duplicating, adding or dropping fields, and a 1-character prefast change, all re-sealed with the key, are refused.
   - Gaps: mn3.
3. **M2.**
   - A gen file copied to the replay path refuses: with a new replay key, "key missing"; with the gen key copied over, `[role]`. Another nonce refuses with `[nonce]`.
   - The driver creates the nonce once (O_EXCL, `secrets.token_hex(16)`) and reuses it on `--resume`. Key paths are per nonce and role.
   - `replay_target5` fails closed when the sidecar is missing or empty (`bool(mine)`). The sidecar is unauthenticated, but it is only a secondary control.
   - Bypass: only MJ1, which needs the same run and role, so it is not gen → replay.
4. **HMAC.**
   - CCHmac SHA-256 with a 32-byte `arc4random_buf` key, O_EXCL 0600, F_FULLFSYNC, and an exact-32-byte check: sound.
   - The MAC covers the line body only. There is no binding to the header, position or session (MJ1). Positional and order replay within one session is harmless, because the contents are identical.
   - Ignoring unauthenticated lines while refusing authenticated invalid ones is correct. A torn line glued to the next line is rejected (tested).
   - `verify_sample` uses `arc4random_uniform` (a real CSPRNG, partial Fisher–Yates), compares bit for bit (memcmp on doubles, `arb_equal`, `mag_equal`), runs on fresh threads, and is enforced (−1 → refuse).
   - Trust model: see mn7.
5. **Parser and fsync.**
   - Every token is checked. Integers have overflow guards and reject leading zeros; hex doubles and mags must be canonical; `i < T` is checked before index arithmetic.
   - 28 hand mutations were refused for the right reason. One "accepted" mutation was in fact canonical: a radius of 0 → 1, which is wider and still sound.
   - Exception: mn1.
   - Torn writes are never accepted. 16 truncation offsets each gave either a refusal (header torn: offsets 10 and 756) or a bit-identical result, and a second resume was also identical. A missing final newline is repaired before appending.
   - The fsync loss bound is misstated (mn2).
6. **Concurrency.**
   - `item_line` reads `w->R` before the decrement under `mu`, so the merge cannot have freed it. This is correct.
   - A write error closes the fd under the I/O mutex. Waiters re-check `fd < 0` inside `ck_seal_write`. This is safe.
   - flock: the lock lives on the original open file description, and `fclose` of the dup'd read stream does not release it (verified mid-run while the session was live).
   - Zgrid joins the threads it started before returning −1. `pthread_create` failure in the fast or verify path calls `abort()`.
   - Kill/resume at 10^18 D2 (`scratch/kill_rv.py`): 3 trials, 2–3 SIGKILLs each at random times (including during resumes and `verify_sample`), then a final resume with W ∈ {1, 3, 4}. All runs were **identical** to the v14 reference.
7. **Hooks.**
   - `libzfast.v14b.dylib` has no `getenv` import and no hook strings.
   - The test-hooks dylib has all four, and its checkpoints are refused by production.
   - The provider and driver refuse to start if any `ZFAST14_TEST*` / `ZFAST14B_TEST*` / `ZFAST14_GENERIC_KERNEL` variable is set, and `child_env` strips them. `replay_target5` imports the driver (refuses), and replay5 gets `child_env` and imports the provider (refuses).
8. **Soundness.**
   - In an uninterrupted session nothing changes.
   - On resume, a wrong ball can come only from authentic-but-foreign lines (MJ1, demonstrated) or from a key-holder forgery (disclosed in N5k; authenticated zeroed error mags with verify 0 are accepted, as designed).
   - Nothing in v5z8 changes certificate content: the diff adds only the nonce, key paths, the sidecar and the `ck_ok` conjunct to `passed`.

## Tests run (all under `review_v14b/scratch/`)
| script / log | what | result |
|---|---|---|
| `rb/` | rebuild of both dylibs from `bin/src_v14b` with `build_v6` flags | SHAs identical |
| `diff_rv.py` / `diff_rv.log` | 36-case v14 vs v14b (no ckpt / ckpt / full-verify resume) | 36/36 identical |
| `attack_rv.py` / `attack_rv.log`, `out_attack/attack_results.json` | role/nonce, torn offsets, glued line, zero key, key reuse, **splice**, 28 parser mutations, header tamper, LBSHIFT, hooks lib, flock | all as designed except **splice accepted 6/6 (MJ1)** |
| `kill_rv.py` / `kill_rv.log` | random SIGKILL + resume, 10^18, W 2 → {1, 3, 4} | 3/3 identical |
| `asan/drv.c`, `asan/fuzz.py`, `asan/fuzz.log` | 150 re-sealed random mutations, UBSan + libgmalloc | no memory/UB errors; 7 FLINT aborts (mn1) |
| `flint_abort.py` / `.log` | mn1 on the production dylib | SIGABRT, no reason |
