# OPTIMIZE_M9: profile and plan for a faster, leaner RH window pipeline before 10²⁵ → 10²⁸ (2026-11-01)

Phil approved "optimize Atlas first" (2026-11-01). Efficiency is secondary and never trades against rigour. Rule for this milestone:
every change must leave the session output **bit-identical** to libzfast.v13b (pure scheduling, exact-integer restructuring, or the
same IEEE operations in the same order), or it is not built here. Nothing frozen is modified; new versions only (zfast `src/v14`,
`atlas_v5z6`).

Machine: Apple M1, 4 P-cores + 4 E-cores, 8 GB. Two non-Atlas `colab drivemount` Python processes (Codex app) each use ~100% of one
core throughout; they were not touched. All timings below are measured with them present (nice 19 for our jobs), which depresses
multi-thread numbers.

## 1. Where the time goes (measured)

**Session = everything at high T.** A v5z5 window is 4 sessions (generator, inline replay, independent replay, Turing scan) of one
O(√T) moment pass each (RESULTS_M8 §4–5). The non-session part (rows, ~25k Z points, LP, Arb verification, tiling, Lean export) is about
300 s per window at 10²² (RESULTS_M7 F-M7c) and grows only like log T, so at 10²⁵ (session 5.5 h) it is < 2%.

**Inside a session** (`runs/m9/profile/`, 10²⁰, H = 61, Δ = 0.012, K = 18, J = 12, 1 thread, v13b; macOS `sample`, 30 s, 22,500 samples):

| part | share | note |
|---|---|---|
| `mom_range` self (= inlined `block_kernel_mom`, the per-term loop) | **96.7%** | 199.6 s / 3.99·10⁹ terms = **50 ns/term ≈ 160 cycles** |
| per-block Arb work (block_setup logs, logL_poly, error bounds, 4 arb_add per moment) | ~3% | 249,847 blocks, mean B ≈ 16,000 (bmax = 2^14 binds) |
| head (Arb, n < 36,624) | 0.1% | 0.20 s |
| Z/row point evaluation | small | 2.4 ms per Z point at 10²⁰ (2,000 points 4.8 s); ~3.5 ms at 10²⁵ |
| Python orchestration | negligible | |

**Inside the kernel** (disassembly of `libzfast.v13b.dylib` `_mom_range`, plus timing ablations `src/v14_bench/ablate.c`):
- The 20 complex moment accumulators g[2m], g[2m+1] live in a stack array: every term does 20 × (load pair, 2 scalar adds, store pair,
  one 2-lane multiply) plus loop overhead, i.e. store-to-load forwarding through memory on every term. The (re, im) pair is already
  2-lane NEON for the multiply but not for the adds.
- The J = 12 fixed-point phase recurrence (12 exact 256-bit adds, 48 add-with-carry) is a generic loop with loads/stores per word.
- cos/sin (`cs_core`, both polynomials as one 2-lane fma chain) is already good: ~2.3 ns/term.
- After the kernel rewrite below, the remaining 20 ns/term splits roughly: phase recurrence ~8 ns (flag-setting add throughput; a fused
  two-step sweep was tried and is not faster), moment updates ~5 ns, cos/sin + weight + Horner ~5 ns.

**Threading.** v13b splits every bucket into `threads` contiguous ranges and joins after each bucket (a barrier per bucket, ~1,500–2,600
buckets). Measured 1 → 2 → 4 threads = 1.00 / 1.98 / 3.16× (M8). Faster cores wait for the slowest at every barrier; E-cores are unused.

**A fact that constrains every scheduling change:** the output depends on the decomposition. Each range starts its own blocks, so block
boundaries and the per-range sums change with `threads`; M8's calibration shows max_rad 2.8794750e-9 (4 thr) vs 2.8794785e-9 (2) vs
2.8794826e-9 (1) at 10²¹. The certificates of wide_1e22 were made with threads = 2. So bit-identity requires keeping v13b's decomposition
as a **recorded session parameter D** and decoupling it from the number of OS threads.

## 2. Levers: gain, risk, decision

Gain is for the session (≈ the window at ≥ 10²⁴). "Identical" means bitwise-identical session state (all moments, bounds, Nw, buckets)
and therefore identical Z/row balls.

| # | lever | expected gain | identical? | risk | decision |
|---|---|---|---|---|---|
| a | **v5z6 two-session windows**: the generator's session also writes the Turing grid (u ∈ [lo − 40, hi + 40], step 0.004, H = 91); the separate scan_turing5 session is dropped; `scan_turing5.py recount` (unchanged tool of record) runs on the saved grid; one replay of record (fresh process, session from pieces.json) instead of two | 4 → 2 sessions: **2.0×** per window | certificates: yes in legacy params; with H = 91 radii change slightly (not identical, still rigorous) | low: no certificate code changes; the dropped second replay was a byte-identical rerun of the same program | **build** |
| b | **work queue on all 8 cores**: items = v13b's exact (bucket, range) decomposition with D recorded; W worker threads pull items longest-first across buckets; per-bucket merge in v13b's exact order | dev: W = 8 vs v13b 4 thr ≈ 1.3× on top of c (contended machine) | **yes** (merge order per bucket is v13b's; max/sum of integers are order-free) | low; tested W = 1, 3, 4, 8 hash-identical | **build** |
| c | **kernel rewrite** (kind 0, K = 18, J = 12): moments in NEON registers (fully unrolled 20 × (fadd.2d, fmul.2d)), phase recurrence unrolled; same IEEE operations in the same order, `-ffp-contract=off` unchanged | measured **2.46–2.55×** single-thread (50 → 20 ns/term) | **yes** (bench: 0 mismatches over 300 × 16,384, 3,000 × 1,001 and 30,000 × 37 random blocks; full-session hash identical) | low; generic kernel kept, selectable by env for A/B | **build** |
| c′ | compiler flags -O3 / LTO | ~3% (noise level) | yes in principle | none, but no gain | not built (keep v13b's exact flags) |
| c″ | narrow-width phase recurrence (E[i] for large i fits in 64/128 signed bits; per-block rigorous no-overflow check, else 256-bit path) | est. +10–15% | yes (exact integer) | medium: new overflow lemma, needs review | **not built; proposal** |
| c‴ | FMA in the moment recurrence, larger bmax, fewer Taylor terms | 5–30% | **no** (changes rounding / block bound) | needs new written error bound + review | **not built** |
| d | redundant work across sessions: replay reusing the generator's moments | 2× | n/a | **breaks replay independence** | **rejected** |
| d′ | Turing grid evaluated in parallel (each point independent; identical to zfa3_Zgrid) | 45k points: ~160 s → ~30 s at 10²⁵ | **yes** | low | **build** (part of a) |
| d″ | head / Lb / Xb / per-block Arb overhead | ≤ 3% | — | — | not worth it now |
| e | **checkpoint/resume**: each finished item appended (exact `arb_dump_str`, raw mag fields, SHA-256 per line; header pins every parameter that defines the items); resume loads matching valid lines, merge unchanged | none in speed; needed for 2–5-day sessions at 10²⁸ | **yes** (resume = uninterrupted, tested) | medium-low: a new input path into the session; protected by header equality + per-line SHA-256; replay of record keeps its own checkpoint (never the generator's) | **build**, flag for review |
| f | memory | v14 adds per-item buffers only until its bucket completes: maxrss 20 → 30 MB at 10²⁰ | — | — | fine (≤ 3 GB watchdog) |
| — | Hiary T^{1/3} main sum | the only exponent change | — | high; separate project | **out of scope** (noted) |

Ranking by gain × safety: c (2.5×, identical) > a (2×, no certificate change) > b (1.2–1.4×, identical) > e (enabling) > d′ > c″ (proposal).

## 3. Build plan (Phase 2)

1. **zfast `src/v14`** (from v13b; built with the unchanged `build_v6.sh`, same flags):
   - `zfast_m3b.inc`: `block_kernel_mom_z20` (used iff kind 0, nw = 1, K2 = 20, J = 12; `ZFAST14_GENERIC_KERNEL=1` forces v13b's
     kernel); `zfm_build` = v13b's `zfm_new2` with the fast part replaced by the scheduler; `zfm_new2`/`zfa4_new` keep v13b semantics
     (workers = threads, no checkpoint).
   - `zfast_sched14.inc`: items, work queue, per-bucket merge, checkpoint file (`ZFAST14_TEST_EXIT_AFTER=k` test hook: `_exit(77)` after
     k items are checkpointed).
   - `zfast_hash14.inc`: SHA-256 of the complete session state, also compiled into a test-only reference build of the **frozen v13b
     source** (`ref13h.c`), so v14 is compared with v13b's own code, not with itself.
   - `zfast_api14.c`: `zfa14_new(T0, u0, H, Δ, K, J, D, W, ckpt)`, `zfa14_info`, `zfa14_hash`, `zfa14_Zgrid(…, W)`.
2. **atlas_v5z6** (built by `tools/make_v5z6.py` from v5z5; byte copies except):
   - `lib/zfast_provider.py`: libzfast.v14 (sha-pinned); D = the recorded `threads` (ZFAST_THREADS, as in v5z5), W = ZFAST_WORKERS
     (output-free), ZFAST_CKPT (optional); `turing_grid()` writes the scan_turing5 saved-scan format from the process's single session.
   - `atlas_v5.py`: `--turing-grid` (the session must contain [lo − 40, hi + 40]; checked before any compute); `--resume` (only while no
     zs.json/certs exist; earlier logs renamed, never deleted); child envs carry ZFAST_THREADS = pieces.json's `threads` (the replay's D
     comes from the record), ZFAST_WORKERS, and role-specific checkpoints (generator / replay never share one).
   - `lib/gen_target5.py`: one added stage after `gen_done` (untrusted generator): `turing_grid` if requested.
   - `run_wide6.sh`: generator(+grid) → replay of record (driver stage 3) → `scan_turing5.py recount` → `turing_gate check`.
3. **Gate** `engine/regress_v1/v5z6_gate.py`: identity of v14 vs the frozen v13b dylib and the v13b-source reference; v5z6 regenerates
   wide_1e22 identically; checkpoint kill/resume identity.

## 4. Validation (Phase 3)

- regress_v1 tier 0 + tier 1 (frozen code; must stay green).
- Identity: v14 vs frozen libzfast.v13b (grid mids/radii, Z strings, rows) and vs ref13h (state hash) at 10¹², 10¹⁶, 10²⁰, 10²² with
  D ∈ {1, 2, 4}, W ∈ {1, 3, 8}.
- wide_1e22 regenerated by v5z6 with the frozen session parameters (H 61, Δ 0.012, centre 50, D 2), any W: certs, certs_np, zs.json,
  gen_measurements.json, replay records identical to the frozen v5z5 run.
- wide_1e22 under v5z6 production parameters (H 91 + Turing grid): closes, 777 sign changes, recount N values equal M7-A1/M8,
  turing_gate PASS, and its four negative controls FAIL.
- Checkpoint: kill mid-session (test hook and a real SIGKILL), resume, identical state hash.
- Measure per-window cost, re-project 10²⁵ / 10²⁶ / 10²⁸. **No 10²⁵ run; no 11.5 h w_1e24 regeneration.**

## 5. Needs independent review (before claims rest on it)

- The v14 kernel's bit-identity argument (same operations, same order) — mechanically confirmed by hashes, but the code is new trusted code.
- The checkpoint load path (a new way for numbers to enter a session).
- Lever c″ if ever built (new overflow lemma).

Wording: the certification method is Atlas's own and new; only zfast's evaluation core has prior art (FLINT dfloat).
