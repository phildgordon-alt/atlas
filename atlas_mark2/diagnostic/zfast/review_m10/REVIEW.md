# review_m10: independent review of libzfast v14 (kernel z20, work-queue scheduler, checkpoint/resume, parallel Z grid)

Reviewer: independent agent, 2026-11-02. Scope: `src/v14/` (= `bin/src_v14/`, SHA256.v14 verified OK) against the frozen `src/v13b/`.
OPTIMIZE_M9.md was read for orientation only; every claim below is from the code, the disassembly, or tests I ran myself.
Nothing outside `review_m10/` was modified. All runs used nice 19 and at most 2 threads, except four W=3/W=8 sessions at 10^15 and 10^16 that each lasted under 0.2 s.

## Verdict: PASS WITH CONDITIONS

- **Kernel (z20) and scheduler: PASS.** The two kernels perform the same IEEE operations in the same order. The decomposition and merge are v13b's, and the output does not depend on W. I found no route to a silently partial sum.
- **Checkpoint/resume: conditional.** Resume is exact: an interrupted and resumed session is bit-identical to an uninterrupted one in every test, including partial writes. However, the header does not pin the environment-derived state that every loaded item depends on: `Lb[]` (from libm `log`), `nbeg[]` (libm `exp`), `Xb[]`, the library build, and the FLINT version.
  - A checkpoint written under a different libm or library build is therefore accepted silently. In that case the loaded moments are expansions about a centre other than the one `zfm_sum` uses, and no error term accounts for the difference. The ball is then no longer proven to enclose Z (finding M1).
  - Demonstrated here with a test build that shifts Lb by one ulp: all items were loaded and no warning was given.
- **Conditions before any resumed session feeds a certificate or the Turing grid:**
  1. Fix M1, or adopt an interim operating rule: never resume across an OS, Homebrew/FLINT, or library change; otherwise delete the checkpoint and recompute.
  2. Fix M2: tag the checkpoint role, so the replay of record cannot load the generator's numbers.

No critical findings. Nothing I found can underestimate a radius in an uninterrupted (non-resumed) v14 session.

## Findings

### Critical
None.

### Major

**M1. The checkpoint header does not pin the environment-derived session state that loaded items depend on.**
`zfast_sched14.inc:59-67` (header), `:181-196` (validation).

- **What the header contains:** T0, u0, H, Delta, K, J, D, kind, bmax, interp, Nw, nb, nhead, nitems, wp. Each item line also checks (b, i, lo, hi).
- **What each item depends on but the header omits:**
  - `S->Lb[b]`, a binary64 from libm `log` (`zfast_m3b.inc:315`). It is the expansion centre used by `logL_poly` inside `mom_range`.
  - `S->Xb[b]`, which enters the item's error bound through `Xp = Xb + e_x`.
  - The bucket edges `nbeg[]`, from libm `exp`. These are only indirectly guarded by the lo/hi check.
  - The library itself: kernel, bound constants, `ZF_EC`, `RDEG`. A different library build with the same format tag `ZFAST14CKPT v1` would be accepted.
- **Why a mismatch breaks the proof:** if the resuming process computes a different `Lb[b]`, the loaded moments M_k = Σ w (log n − Lb')^k are about Lb'. `zfm_sum` combines them with e^{−ihLb} and Taylor coefficients about Lb. This silently multiplies the bucket's contribution by about e^{ih(Lb−Lb')}, and nothing bounds that error.
- **Demonstration** (`lbshift_test.py`, `lbshift.log`): a test-only copy of v14 (`scratch/src_lbshift`, one added line under an env var) writes a checkpoint with every Lb moved up one ulp. The genuine `libzfast.v14.dylib` then resumes from it.
  - Result: `items_loaded 480/480` (10^14) and `751/751` (10^16), with no warning.
  - Z midpoints moved by 1e-14 to 4.5e-13. Radii are 3e-11 to 1.7e-10, so all 24 balls still overlapped the honest ones; the shift is about 0.3% of the radius.
  - This drift is therefore not empirically dangerous at these heights, but the enclosure is no longer proven.
- **Why this matters for the pipeline:**
  - The replay of record recomputes Z and rows, so a generator resumed across a drift is caught for certificates, unless the replay itself was resumed across the same drift.
  - The Turing grid (v5z6 lever a) comes only from the generator's session and is not recomputed by the replay. A generator resume across a drift therefore reaches `scan_turing5.py recount` with unproven balls.
  - Multi-day sessions at 10^25–10^28, run unattended for weeks, make "interrupted, OS/Homebrew updated, resumed" a realistic sequence.
- **Fix:**
  - Compute a pre-fast-part digest: SHA-256 of nbeg[] (raw), Lb[] (raw bits), Xb[] (raw mag fields) and `arb_dump_str(tau0)`. This is the first half of `zfm_hash14`, computed before `zfm_fast14`.
  - Add a compile-time library identity string and the runtime FLINT version (`flint_version`), plus the GMP/MPFR versions.
  - Put all of these in the header and refuse on any mismatch. The cost is negligible.

**M2. Generator and replay checkpoints are indistinguishable. Replay independence is enforced only by the driver's file naming.**
`atlas_v5.py:186` (`zfast_ckpt_gen.txt`), `:205` (`zfast_ckpt_replay.txt`); `zfast_sched14.inc:59-67`.

- In the existing smoke run `runs/w1000000000000/smoke_1e12/` the two files have byte-identical header lines, header SHA included.
- If ZFAST_CKPT is misrouted, or the file is copied, the replay of record silently loads every generator item, and the "independent replay" re-uses the generator's numbers.
- `items_loaded` is reported in `zfa14_info`, but nothing gates on it.
- **Fix:** have the caller pass a role (`gen` / `replay`) and a per-run nonce into `zfa14_new`, and include both in the header. The replay should refuse any file not created by a replay-role process of the same run. replay_check.json should record `items_loaded`, and should fail if the replay loaded items from a file it did not create itself.

### Minor

- **m1. The per-line SHA-256 protects integrity only, not authenticity, and loaded values are not validated.**
  - A forged line whose hash is recomputed is accepted. Tests F, F2, F3 in `ckpt_tests.log`:
    - F: perturbed midpoint accepted.
    - F2: all 20 error bounds of one item set to zero accepted, which shrinks the Z radius (2.86e-11 → 2.85e-11). This is a radius underestimate through the file.
    - F3: a non-normalised mag mantissa (`1:5`) is accepted. `parse_mag` (`zfast_sched14.inc:49-57`) writes `MAG_MAN` raw, with no check of 2^(MAG_BITS−1) ≤ man < 2^MAG_BITS (or man = 0 with exponent 0), and `strtoul` accepts a sign.
  - This is acceptable if the checkpoint is documented as trusted input, comparable to the code itself. If an accidental-or-hostile model is wanted, add an HMAC keyed by a secret kept outside RUN.
  - Either way, validate mags and reject non-finite arb values on load.
- **m2. Index arithmetic from the file can overflow.** `long x = Q.first[b] + i` (`zfast_sched14.inc:200`), where `i` comes from the file. For a huge `i` (resealed line) this is signed overflow (undefined behaviour) followed by an out-of-range `it[x]` read. It did not crash in test K. Fix: check `0 <= i < it[Q.first[b]].T` before forming x.
- **m3. Checkpoint write errors are ignored.** The return values of `fprintf`/`fflush`/`fsync` are ignored (`:133, :214, :219`), and `fsync` on macOS is not `F_FULLFSYNC`.
  - This only loses resumability, never correctness: partial or glued lines are rejected by their hash (tests D, N).
  - Still worth logging, and counting written lines so a "checkpoint not actually written" condition is visible.
  - The I/O and fsync also run under the global queue mutex, so the merge, the hand-out of new items, and checkpointing all serialise behind disk latency. This affects timing only.
- **m4. The checkpoint file is not locked.** Two processes on one checkpoint (for example, a resume launched while the original is still alive) interleave appends. Hashes protect content, but use `flock(LOCK_EX|LOCK_NB)` and refuse if the lock is held.
- **m5. `zfa14_Zgrid` can leave threads writing into freed buffers.** If `pthread_create` fails part-way (`zfast_api14.c:60`), it returns −1 while the already-started workers keep writing into the caller's `mid/rad/uout`. Python raises and frees those ctypes buffers, giving a use-after-free. The output is never used, so this is not a soundness problem. Fix: join the started threads before returning.
- **m6. Bit-identity relies on FLINT's thread-local cache behaviour; this is empirical, not by construction.**
  - FLINT 3.6 caches constants per thread at (max requested precision + 32) (`arb.h:618-639`), so an Arb result can depend on that thread's request history.
  - v13b ran T = 1 items on the main thread, warm from the head, and then `flint_cleanup()`'d the main-thread cache. v14 never runs items on the main thread. Z grids run on fresh worker threads instead of the warm main thread.
  - Every comparison I ran is bit-identical, so the current code paths are unaffected. But future changes that alter which thread does what could silently break identity.
  - This is not a soundness issue: each result is a valid ball. Keep the cross-process Z-string identity check in the gate.
- **m7. D > 16 is aliased to 16.** `split_ranges` clamps D to 16 (`zfast.c:384`), as v13b did. The header and record keep the raw D, so D = 17 and D = 16 produce identical sessions under different recorded parameters. Reject D > 16 in `zfa14_new` or the provider.
- **m8. The driver passes test hooks through to children.** The replay environment is `dict(os.environ)` (`atlas_v5.py:204`), so `ZFAST14_TEST_EXIT_AFTER` and `ZFAST14_GENERIC_KERNEL` reach the replay if set in the parent. The exit hook fails loudly (`_exit(77)`) and the generic kernel is identical, and both are recorded in env records. So this is harmless, but production runs could refuse to start with either set.

## 1. Kernel equivalence (v14 `block_kernel_mom_z20` vs v13b `block_kernel_mom`)

**Source, line by line** (`src/v14/zfast_m3b.inc:105-157` vs `src/v13b/zfast_m3b.inc:64-102`):

- **Per term:** same `zf_cos2pi(E[0].w[3])`; same `xx = (double)k − xc`; same `x = horner6(cx, xx)`; same `w = 1.0/sqrt((double)(n0+k))`, which equals v13b's `zfirst` branch since kind 0 implies zfirst and nw = 1; same `pr = w*c`, `pi = w*s`.
- **Moment loop:** v13b does `g[2m] += pr; g[2m+1] += pi; pr *= x; pi *= x`. v14 does `G[m] = vaddq_f64(G[m], P); P = vmulq_n_f64(P, x)`. These are two independent IEEE binary64 lanes doing the identical scalar operations in the identical order. The vector form computes `(c, s)·w` where the source computes `w·c, w·s`; IEEE multiplication is commutative, so the results are identical.
- **Phase recurrence:** the 12 `fx_add` calls run in v13b's order (E0 += E1, then E1 += E2, …), on a local copy that is written back, which is equivalent. `fx[13]` fits, since JMAX = 32.
- **Accumulation:** the 16-term TwoSum block is identical. The output layout `acc[4m+{0,1,2,3}] = (hi_re, lo_re, hi_im, lo_im)` matches v13b's `acc[2a], acc[2a+1]` with a = 2m + {re, im}.
- **Dispatch guard:** `nw == 1 && kind == 0 && K2 == 20 && J == 12 && !generic` (`:211-214`). The generic path is unchanged.

**Compiler flags** (`src/build_v6.sh`, used for v13b and v14; `v14_bench/build_ref13h.sh` uses the same): `-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math`. There is no `-ffast-math`, `-Ofast`, `-freciprocal-math` or LTO.

**Disassembly** (`otool -tvV`):

- In v14 both kernels are inlined into `_wq_worker`.
- The FP-instruction histogram reconciles exactly with "v13b's kernel + one z20 kernel":
  - +20 `fmul.2d` (the 20 `P *= x`)
  - +80 `fadd.2d` (20 moment adds + 3×20 TwoSum)
  - +80 `fsub.2d` (4×20 TwoSum)
  - +8 `fmla.2d` and +6 `fmadd`, which are exactly the explicit `fma()` calls of `cs_core` (2-lane) and `horner6`. These are present in v13b too and are covered by its error bound (`ZF_EC`, `horner6` bound).
- No new fused instruction appears in the moment recurrence. The inner loop reads `fadd.2d vG, vG, vP; fmul.2d vP, vP, vx[0]` × 20.
- `1/sqrt` is `fsqrt` + `fdiv`. There is no `frsqrte`/`frecpe`/`frsqrts`/`frecps` anywhere in either dylib, and no `msr`/`mrs` (no FPCR manipulation).
- AArch64 Advanced SIMD binary64 obeys FPCR.FZ/RMode exactly like scalar (unlike ARMv7 NEON), and pthreads start with the default FPCR (RN, FZ = 0). There is no denormal or rounding-mode difference.

**Dynamic comparison:** see §5. All session state hashes are equal to `ref13h` (the frozen v13b source plus the hash function). All Z strings and Z grids are equal to the frozen `libzfast.v13b.dylib`.

## 2. Scheduler (`zfast_sched14.inc`)

- **Items:** built in bucket order with v13b's exact `split_ranges(lo0, hi0, P->threads = D, bmax)` and the same `n` advance (`:157-172` vs v13b `zfast_m3b.inc:308-343`). This holds for uneven D as well, because integer-floor partitions are computed by the same function. Tested D = 3, 5, 7.
- **Merge:** `merge_bucket` (`:93-115`) runs only when a bucket's `left` reaches 0, under the mutex. It merges items i = 0..T−1 in index order, with exactly v13b's `acb_add` / `arb_add_error_mag` ×2 / `mag_add` sequence on that bucket's slots only. Different buckets touch disjoint `S->M`/`S->V` slots, and the head part writes these slots before the fast part starts, so the order across buckets does not matter.
- **Summary statistics:** `maxph` is a max (NaN is ignored identically in either order) and `nblocks` is a sum of integers below 2^53, so both are order-free. They are informational only.
- **Races:** worker threads touch shared state only in `mom_range`, which reads `S` (tau0, Lb, Xb, P, kind) and never `S->M`/`S->V`, and in the locked section (done flag, checkpoint write, counters, merge). There are no mutable statics in zfast.c or the .inc files. The FLINT caches used are thread-local. TSan could not be used (any FLINT program segfaults under TSan with this Homebrew build), so this conclusion rests on reading the code.
- **Failure propagation:** `mom_range` aborts the process on any internal error, and `pthread_create` failure aborts. After the join, every bucket must have `left == 0`, otherwise the process aborts (`:240`). A loaded duplicate cannot double-count (the `done` check, `:201`). I found no path that returns a partial sum.
- **Queue order:** longest first (`qsort_r`, deterministic tie-break). This affects only timing.
- **Wrappers:** `zfm_new2`/`zfa4_new` in v14 keep v13b semantics (workers = D, no checkpoint), and `zfa3_*` are byte-identical files.

## 3. Checkpoint/resume

- **What is right:**
  - Moments are stored with exact `arb_dump_str`/`arb_load_str`, and the error and V mags as raw (mantissa, exponent) fields. `nblocks`/`maxph` use `%a`. All of these round-trip exactly.
  - Ball radii and rounding-error accumulators are therefore restored bit for bit, and the merge is the uninterrupted one.
  - A partial final line, a corrupted byte, glued lines, short or long resealed lines, mismatched (b, i, lo, hi), and duplicate lines are all ignored or recomputed. A foreign or truncated or missing header, or another D, is refused (the session returns NULL and the provider raises).
  - An item that fails part-way through parsing is re-zeroed by `mom_range` before it is recomputed.
  - A missing newline at the end of the file is repaired before appending.
- **What is missing:** M1 (environment pinning), M2 (role tagging), m1–m4.

## 4. Anything that could make a certificate unsound

- In a non-resumed session: nothing found. The kernel's floating-point operations are those of v13b, so v13b's proven bound applies unchanged, and the scheduler cannot drop or duplicate work.
- In a resumed session: M1 (silent cross-environment acceptance, demonstrated), and m1 (radius underestimation via a forged file, demonstrated; a trusted-input question).
- The Turing grid is generator-only, so it is the one consumer not protected by the replay against M1.

## 5. Tests run (all scripts and logs in this directory)

| test | what | result |
|---|---|---|
| `diff_matrix.py` + `diff1.log` | 15 sessions, T ≈ 10^12…10^16 (random T0), (H, Δ) ∈ {(61, 0.012), (4, 0.15)}, D ∈ {1, 2}, W ∈ {1, 2}. Each run is a fresh process. Checks: ref13h state hash; 4–6 random Z strings vs frozen v13b dylib and ref13h; 64-point Z grid (`zfa14_Zgrid` vs v13b `zfa3_Zgrid`, raw hex) | 0 mismatches |
| `diff2.log` | uneven D = 3, 5, 7 at 10^15/10^16, W ∈ {1, 2, 3, 8} | 0 mismatches |
| `diff3.log` | 10^18 (D = 1, 2; W = 1, 2) and 10^20 (D = 2, W = 2) | 0 mismatches (hash, 3–4 Z strings, 8–16-point grid; 10^20 fast part 81 s at W = 2) |
| `ckpt_tests.py` + `ckpt_tests.log` | 22 adversarial checkpoint cases (kill via test hook at W = 1/2, truncation, corruption, forgery, foreign/different-D/missing/truncated header, empty file, short/long/glued/duplicate lines, index overflow, wrong lo/hi, generic kernel) | resume identical in every honest case; forgeries accepted (m1) |
| `lbshift_test.py` + `lbshift.log` | checkpoint written by a 1-ulp-shifted-Lb build (`scratch/src_lbshift`, test only), resumed by the genuine v14 | accepted silently (M1); balls still overlap (shift ≈ 0.3% of radius) |
| disassembly | `_mom_range` (v13b) vs `_wq_worker` (v14) FP-op histogram; search for estimate/FPCR instructions | reconciles exactly; none |
| TSan | `scratch/tsan` | not usable (FLINT segfaults under TSan on this system) |
