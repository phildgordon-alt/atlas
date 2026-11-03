# review_v14c: brief for an independent re-review of libzfast v14c + atlas_v5z9 (requested 2026-11-02)

**Request.** Review libzfast v14c and atlas_v5z9. They were built to close `../review_v14b/REVIEW.md` (PASS WITH CONDITIONS:
major MJ1; minors mn1-mn7) before the multi-day, resumable 10^28 window. The builder did **not** review this code.
`../RESULTS_M13.md` holds the builder's results; treat them as claims to check. Pre-registration: `../PREDICTIONS_M13.md`
(sha in `../PREDICTIONS_M13.sha256`, hashed before any v14c code was written).

**Rules.** nice 19; ≤ 2 threads unless a short test needs more; footprint ≤ 3 GB; disk floor 2 GB; never `python -O`. Write only
inside `review_v14c/`. Never modify `bin/`, `src/`, `atlas_v5z*/`, `ckpt_keys/`, `engine/` or any run. No session above 10^20. Check
`ps` first; do not compete with a production window. No outreach.

## What changed (diffs in this directory)

| file | what |
|---|---|
| `lib_v14b_to_v14c.diff` | `bin/src_v14b` → `bin/src_v14c`: `zfast_m3b.inc` (include sched14c; 5 info fields; comments), `zfast_api14b.c` (bad-T0 error; `"lib": "v14c"`; ck buffer 2048), `zfast.h` (one declaration). Every other file byte-identical. |
| `sched14b_to_sched14c.diff` | the checkpoint layer (the file is renamed). Items, `split_ranges`, `merge_bucket`, `wq_worker` (except `item_line(…, x)` and the item seal call), `cmp_len_desc`, `verify_sample` are intended unchanged. |
| `pipeline_v5z8_to_v5z9.diff` | provider (lib path/sha, `lib='v14c'`, hook prefix), driver (generator verify default 64, hook prefix, names), replay_target5 (name), run_wide9.sh. Built by `../tools/make_v5z9.py` (counted replacements). |
| `gate_v5z8_to_v5z9.diff` | `engine/regress_v1/v5z9_gate.py` (new file) vs v5z8_gate.py. |

**Artefacts.** `bin/libzfast.v14c.dylib` 59883f5e…, `bin/libzfast.v14c_testhooks.dylib` 9c0d4a9b… (`bin/SHA256.v14c`); build script
`src/build_v8.sh` = unchanged `build_v7.sh` (→ `build_v6.sh`, same flags) plus `bin/BUILD_ENV.v14c.txt`. `atlas_v5z9/V5Z9_FREEZE.sha256`
(37 entries). A first official v14c build was superseded before any use (the M13 fuzz found a second FLINT abort class) and is kept in
`bin/superseded_v14c_build1/` (README there); never use it.

**API.** Names and signatures are v14b's (`zfa14b_new`, `zfa14b_info`, `zfa14b_last_error`): v14c is a drop-in; the library is
identified by its pinned SHA, the `lib` header id `zfast-v14c(PREDICTIONS_M13)` and the format `ZFAST14C CKPT v3`.

## The fixes, and what to re-check

1. **MJ1, line binding.** New header = expected body + ` hnonce=<32 hex>` (arc4random). Header seal HMAC(K, "ZF14C-HDR\0" ‖ body).
   Item line `I x b i lo hi …` with seal HMAC(K, "ZF14C-ITEM\0" ‖ SHA-256(stored header body incl. hnonce) ‖ u64be(x) ‖ body).
   - Check: can any line authenticate under a header other than the one it was written for, or at an index other than its own? Is the
     x token parsed before the MAC (for the MAC input) safe (it is only used for the MAC until `load_line` re-parses and requires
     x == first[b] + i)? Is the domain separation between header and item seals sufficient?
   - Re-run the reviewer's splice (`../review_v14b/scratch/attack_rv.py` §5-6 idea) against v14c with your own v3 sealer.
2. **MJ1, duplicates.** Any second authenticated line for a loaded item is fatal; identical and conflicting duplicates are both
   refused (decision: an honest writer never emits one). Check that claim: is there any honest path (EINTR, short write, newline
   repair, kill during write, resume of a resume, verify_sample) that writes an item twice under one header? If yes, the decision
   would make an honest checkpoint unresumable (fail-safe, but costly at 10^28).
3. **MJ1, key reuse.** A new header under an existing key is allowed (so the crash between key creation and header write recovers),
   printed to stderr and reported as `key_reused_new_header`. Judge whether binding (instead of refusing) meets the condition.
4. **mn1.** `parse_arb_strict` no longer calls `arb_load_str`: canonical-hex pre-checks, then `arf_set_fmpz_2exp` /
   `mag_set_fmpz_2exp_fmpz`, then `arb_is_finite`, `mag_valid` and the canonical re-dump check. Check that (a) no FLINT call reachable
   from authenticated input can abort (e.g. huge exponents, huge mantissas, tokens up to the line cap), and (b) an honest line loads
   bit-identically (the verify sample and identity tests suggest so; argue it).
5. **mn2.** Flusher thread (`ck_flusher`): `pthread_cond_timedwait_relative_np` 1 s, `ck_sync` under the I/O mutex. Check the claimed
   bound (a line is durable by write time + 1 s + one F_FULLFSYNC), the shutdown (stop + join before the final sync, also on refusal
   paths), and that the flusher never touches FLINT (m6) or a closed fd.
6. **mn3.** New header fields: `bin_uuid`, `bin_text_sha` (in-memory `__TEXT`, from the Mach-O header via dladdr), `flint/gmp/mpfr_uuid`,
   `libm_uuid`, `dyld_cache_uuid` (`_dyld_get_shared_cache_uuid`, a private-but-exported libdyld symbol), `hw_model`. Any unavailable
   field refuses. Check `image_text_sha` (does `__TEXT` start at the header, is `filesize` the right extent, is it stable across
   processes), and whether hashing a dylib file plus its LC_UUID plus in-memory text leaves a meaningful gap.
   Operational consequence to judge: any OS update (incl. background security responses) between sessions refuses a resume.
7. **mn4.** `key_load`: O_NOFOLLOW, regular file, euid owner, mode & 077 == 0, exactly 32 bytes; creation via temp + F_FULLFSYNC +
   `renamex_np(RENAME_EXCL)` + directory fsync. A crash leaves a stray `*.key.tmp.<pid>.<hex>` file (never read). Check races and
   the 0-byte-key message path.
8. **mn5/mn6.** `ck_err` keeps the first worker error; `zfa14b_last_error` carries it after a successful build. Bounded reader
   `read_line_bounded`: cap = max(64 KiB, 2 × estimate + 4096); overlong lines skipped unstored. Check the estimate cannot reject an
   honest line at 10^28 (wp ≈ 427) — an honest line rejected would only cost recomputation, not soundness.
9. **mn7.** v5z9 generator verify default 64 (replay 8). Detection 1 − C(N−k,64)/C(N,64) per resume. Is this adequate for the Turing
   grid (generator-only data), given that after MJ1 only a key holder can forge?
10. **Compute path and identity.** Confirm nothing new runs on the compute path of an uninterrupted session except header building
    (now including Mach-O walks and one in-memory SHA), line building/sealing per item and the flusher. Re-run your own v14c vs v14
    differential (state hash, grid, rows, Z; uneven D; W ∈ {1, 3, 8}; with and without checkpoint; full-verify resume).

## Builder's tests you may reuse (re-run, do not trust verdicts)

- `../runs/m13/neg/attack_m13.py` (A1-A8 + reviewer §1-§10 adapted), `negtests_m13.py` (M12 N-tests adapted), `ck14c.py` (v3 sealer),
  `asan/build.sh` + `asan/fuzz_m13.py` (UBSan + libgmalloc fuzz; FUZZ_SEED env).
- `engine/regress_v1/v5z9_gate.py` (`--identity`, `--ckpt`, `--n13`, `--w1e22`), `../tools/m13_probe.py`.

## Deliverable

`review_v14c/REVIEW.md`: verdict (PASS / PASS WITH CONDITIONS / FAIL), findings by severity, tests run, explicit answers to items
1-10, and whether v14c/v5z9 may be used for the multi-day resumable 10^28 window feeding certificates and the Turing grid.
