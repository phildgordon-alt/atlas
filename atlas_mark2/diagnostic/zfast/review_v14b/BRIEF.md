# review_v14b: brief for an independent re-review of libzfast v14b + atlas_v5z8 (requested 2026-11-02)

**Request.** Review libzfast v14b and the atlas_v5z8 pipeline. They were built to close review_m10's conditions (`../review_m10/REVIEW.md`:
MAJOR M1, M2; minors m1–m8).

The builder did **not** review this code. `../RESULTS_M12.md` contains the builder's own test results and claims; treat it as
claims to check, not as evidence. The pre-registration is `../PREDICTIONS_M12.md` (sha in `../PREDICTIONS_M12.sha256`).

**Rules.**
- nice 19; at most 2 threads unless a short test needs more; footprint ≤ 3 GB; disk floor 2 GB; never `python -O`.
- Write only inside `review_v14b/`. Never modify `bin/`, `src/`, `atlas_v5z7/`, `atlas_v5z8/`, `ckpt_keys/` or any run.
- Do not run a session above 10^20. Check `ps` first and do not compete with a running production window (run_m1x / run_wide*).
- No outreach.

## What changed (diffs in this directory)

| file | what |
|---|---|
| `lib_v14_to_v14b.diff` | `bin/src_v14` → `bin/src_v14b` (the sched file is renamed; see the next row) |
| `sched14_to_sched14b.diff` | `zfast_sched14.inc` → `zfast_sched14b.inc`: the checkpoint layer rewritten; items, merge and workers intended unchanged |
| `pipeline_v5z7_to_v5z8.diff` | `atlas_v5.py`, `replay_target5.py`, `lib/zfast_provider.py`, `run_wide8.sh` (built by `../tools/make_v5z8.py`, counted replacements) |

**Artefacts.**
- `bin/libzfast.v14b.dylib` sha d77bf28f…, and the test-only `bin/libzfast.v14b_testhooks.dylib` (built with -DZF_TEST_HOOKS). Both
  are listed in `bin/SHA256.v14b`.
- Build script: `src/build_v7.sh` (calls the unchanged `build_v6.sh`).
- `atlas_v5z8/V5Z8_FREEZE.sha256`.

**Claimed unchanged.** These are byte-identical to v14: `zfast.c`, `zfast_m3c.inc`, `zfast_api3.c`, `zfast_api4.c`,
`zfast_hash14.inc` and the CLIs. In `zfast_m3b.inc`, only these change:
- session struct fields;
- `#ifdef ZF_TEST_HOOKS` around the generic-kernel getenv, plus a new LBSHIFT hook;
- the `zfm_build` checkpoint argument type;
- `zfm_new14` / `zfm_new14b` guards;
- `zfm_info14b_ck`.

## What a reviewer must check

1. **The compute path is unchanged.**
   - Confirm that items, the merge, worker scheduling, the head and Z/rows are v14's.
   - Verify that nothing new runs on the compute path of an uninterrupted session, other than header hashing before the fast part
     and line I/O after each item.
   - Confirm that the session is not perturbed. For example, check whether `prefast_digest` / `ckpt_env_fields` (dladdr, file
     hashing, `arb_dump_str(tau0)`) could change FLINT thread-cache state relevant to m6.
   - Re-run your own differential: v14b vs v14 and/or v13b/ref13h, state hash + grid + rows + Z, uneven D, W ∈ {1, 2, 3, 8}.
2. **M1.**
   - Is `prefast` complete? Does every environment-derived value that a loaded item depends on enter the header, directly or through
     the digest? Consider `log2tau` in `mom_range` (from tau0), `choose_B`, `ZF_EC`/`RDEG` constants (covered only through `bin_sha`),
     and libm calls inside `mom_range`/`block_setup` (covered only through `os`).
   - Re-run `../review_m10/lbshift_test.py`'s idea against v14b (the test-hooks LBSHIFT hook, or your own build).
   - Check that the header comparison cannot be bypassed by token reordering, duplication or extra fields (`header_diff`).
3. **M2.**
   - Can a replay-role process ever load a gen-role file, or another run's file?
   - Check the driver (nonce creation and reuse on `--resume`; per-role key paths), the provider sidecar, and the `replay_target5.py`
     `zfast_ckpt` gate (the time filter `t >= t0`; a missing sidecar; multiple sessions).
   - Is the sidecar itself a weak point? It is unauthenticated JSON. The library refusal is the primary control.
4. **m1 / authenticity.**
   - Review the HMAC construction (CCHmac SHA-256 over the line body, hex tag, `" #"` separator), key creation (O_EXCL, 0600,
     arc4random_buf, F_FULLFSYNC), key-file checks (exactly 32 bytes), and the decision to IGNORE unauthenticated lines but REFUSE on
     authenticated invalid ones.
   - Probe the strict parser (`load_line`, `parse_arb_strict`, `parse_mag_strict`, `parse_hexdouble`, `parse_dec_ul`, `next_tok`) for
     out-of-bounds reads, acceptance of non-canonical input, and duplicate handling.
   - Review the resume sample recompute (`verify_sample`): bitwise comparison (`arb_equal`, `mag_equal`, `memcmp` on doubles),
     randomness, and threads.
   - Is the stated trust model (key holder = trusted; detection 8/N per resume) acceptable for the Turing grid, which has no replay?
5. **m2–m5, m7, m8.**
   - Index checks; checked writes and the group commit (amendment A1: at most about 1 s of items unsynced; are torn tails always
     rejected?).
   - flock semantics with the dup'd read fd; Zgrid join on failure.
   - D range; the absence of hooks from the production dylib. Check this with disassembly or `strings`: no `ZFAST14_TEST_EXIT_AFTER`
     / `ZFAST14_GENERIC_KERNEL` / `ZFAST14B_TEST_*` getenv in `libzfast.v14b.dylib`.
6. **Resume equivalence.**
   - Kill at arbitrary points: SIGKILL mid-line, mid-header (is a torn header an unrecoverable refusal, and is that acceptable?),
     between the key and header creation, and during `verify_sample`.
   - Confirm resume is bit-identical, or refuses, in every case. Look for any path that returns a partial or mis-merged sum.
7. **Concurrency.**
   - The I/O mutex vs the queue mutex. Line building outside locks: `item_line` reads `w->R` before `--left`, so the merge cannot have
     freed it. Confirm this.
   - The `fd` close on write error while other workers wait on the I/O mutex.
   - Error reporting via `__thread` `zf14b_err` (`zfa14b_last_error` must be called on the creating thread; the provider does).
8. **Pipeline.**
   - v5z8 must equal v5z7 for uninterrupted runs (G1 claim).
   - Check that test-hook stripping and refusal cover every child (generator, `replay_target5`, `replay5`).
   - Check that nothing in v5z8 changes certificate content.

## Builder's tests you may reuse (do not trust their verdicts; re-run or re-derive)

- `../runs/m12/neg/negtests.py` (N1–N12, N14, N15, P1/P2) and `neg_extra.py` (N7 UBSan, N10 Zgrid). `build_scratch.sh` makes the
  UBSan and injection builds.
- `../runs/m12/neg/n12_pipeline.py`.
- `engine/regress_v1/v5z8_gate.py` (`--identity`, `--ckpt`, `--n13`, `--w1e22`); reports `engine/regress_v1/reports/v5z8_*_20261102_*`.
- `../tools/m12_probe.py`: a one-session probe with v14/v14b modes.

## Deliverable

`review_v14b/REVIEW.md`: a verdict (PASS / PASS WITH CONDITIONS / FAIL), findings by severity, the tests you ran, and explicit
answers to items 1–8. In particular, state whether v14b may replace v14 for multi-day resumable sessions (10^26–10^28) that feed
certificates and the Turing grid.
