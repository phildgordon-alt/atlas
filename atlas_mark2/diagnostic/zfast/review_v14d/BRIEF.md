# review_v14d: brief for a focused independent re-review of libzfast v14d + atlas_v5za (requested 2026-11-02)

**Request.** This is a focused re-review of the changes that close `../review_v14c/REVIEW.md` (PASS WITH CONDITIONS; major MJ-C1; minors
mn-C1 to mn-C4; nits). The goal is to clear v14d/v5za for the multi-day resumable 10^28 window. The builder did **not** review this
code. Treat `../RESULTS_M14.md` as claims to check. Pre-registration: `../PREDICTIONS_M14.md` (sha in `../PREDICTIONS_M14.sha256`,
hashed at 22:07, before any v14d code).

**Rules** (as before). nice 19; at most 2 threads unless a short test needs more; footprint ≤ 3 GB; disk floor 2 GB; never `python -O`;
`HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1` and no `brew` command. Write only inside `review_v14d/`. Never modify `bin/`,
`src/`, `atlas_v5z*/`, `ckpt_keys/`, `engine/` or any run. No session above 10^20. Check `ps` first and do not compete with a production
window. No outreach.

## What changed (diffs in this directory)

| file | what |
|---|---|
| `sched14c_to_sched14d.diff` | the checkpoint layer: `bin/src_v14c/zfast_sched14c.inc` to `bin/src_v14d/zfast_sched14d.inc` |
| `lib_v14c_to_v14d.diff` | `zfast_m3b.inc` (the include, 2 info fields, comments) and `zfast_api14b.c` (`"lib": "v14d"`) |
| `identical_files.txt` | `zfast.c`, `zfast_m3c.inc`, `zfast_api3/4/14.c`, `zfast_hash14.inc`, `zfast.h` and the CLIs, byte-identical to v14c (= v14) |
| `pipeline_v5z9_to_v5za.diff` | provider, driver, replay_target5 (name only), `run_wideA.sh`, THEORY. Built by `../tools/make_v5za.py` (counted replacements) |
| `gate_v5z9_to_v5za.diff` | `engine/regress_v1/v5za_gate.py` (new file) against v5z9_gate.py, with the new modes `--roundtrip`, `--postbuild` and `--ioabort` |

**Artefacts.**

- `bin/libzfast.v14d.dylib` e0ed15f3…
- `bin/libzfast.v14d_testhooks.dylib` e6c011ce…
- the SHA list `bin/SHA256.v14d` and the build record `bin/BUILD_ENV.v14d.txt`
- the build used the unchanged `src/build_v8.sh` (→ build_v7 → build_v6, same flags)
- `atlas_v5za/V5ZA_FREEZE.sha256` (38 entries)
- the permanent MJ-C1 test `../tools/m14_rt/`
- the reboot rehearsal (prepared, not run) `../tools/reboot_rehearsal_m14/`

## The fixes, and what to re-check

1. **MJ-C1 (`parse_arb_strict`).** The radius is now built exactly:
   - a radius mantissa token wider than MAG_BITS (30) bits is refused;
   - otherwise `MAG_MAN = m << (30 − bits)` and `MAG_EXP = e + bits`;
   - `mag_valid` and the canonical re-dump check are kept.

   Questions:
   - Is the construction exact and total for every token that passes the canonical-hex pre-checks (including huge exponent tokens:
     `fmpz_add_ui` on an arbitrary fmpz, followed by `mag_valid`'s 40-bit bound)?
   - Can any FLINT call reachable from authenticated input still abort?
   - Re-run your own `radtest`/`fix2`-style round trip against **`bin/src_v14d`** (not a copy of the function).
   - Note: arb_randtest balls whose radius exponent exceeds 2^40 are refused by the pre-existing `mag_valid` bound. That was 10,105 of
     300,000 in M14 R1, reported as a literal MISS of R1's wording. Judge whether the bound can ever bite an honest moment at 10^28.
2. **mn-C1 (duplicates).**
   - A byte-identical authenticated duplicate (same body SHA-256 for the same item) is ignored and counted in `lines_duplicate`.
   - A conflicting one is still fatal.
   - Check: under the v3 binding (header hash, index x, key), can "identical body" ever mean a different value? Is the classification
     made only after authentication and after the index/(b, i, lo, hi) checks?
3. **mn-C4 (abort policy).**
   - Every checkpoint write or fsync error goes through `ck_fail`: the record, closing the fd, and an atomic `ioabort`. This covers the
     worker line, the flusher, the newline repair, the header, the final sync and the directory fsync.
   - Workers check `ioabort` before taking the next item.
   - After the join, the session is refused with `CKPT-IO-ABORT: …`. The final-sync failure refuses too.
   - Check:
     - (a) no path continues computing for long after an I/O error;
     - (b) no path returns a session after one (`ckpt_write_errors` is always 0 in a returned session);
     - (c) the checkpoint left behind always resumes: torn last line, partial write, a closed fd while another worker holds a built line;
     - (d) no use-after-close of the fd: every fd access is under `Q.io` or single-threaded;
     - (e) the skipped unfinished-bucket `abort()` cannot hide a real scheduler bug.
   - The policy choice (abort instead of continuing unprotected) is the orchestrator's requirement. Judge whether it is safe for a
     multi-day unattended run: after an abort the window simply stops until someone resumes it.
4. **mn-C4 (pipeline).**
   - The provider writes `<ckpt>.refusals.jsonl` and raises.
   - The driver's `io_abort()` (sidecar since the attempt's start time, with the gen.log tail as fallback) leads to `stage=ckpt_io_abort`,
     a banner and exit 3. `run_wideA.sh` stops on rc 3.
   - Check that an I/O abort of the replay of record is also caught, and that a non-I/O refusal never exits 3.
5. **mn-C3 (post-build resume).**
   - The driver now resumes after `zs.json`, `certs`, `certs_np`, `gen_measurements.json` or `turing_grid` exist. Conditions: `--resume
     --wide`; no `replay_check/` and no `zfast_ckpt_replay.txt`; the generator checkpoint exists; the generator sidecar has a gen-role
     record of the run's nonce.
   - In that case every generator output is **moved** to `RUN/gen_postbuild.attempt<k>/` (with a README) and the generator re-runs.
   - "Generator finished" now means `gen_done` **and**, when requested, the `turing_grid` stage, because gen_done is logged before the
     grid.
   - Check:
     - can this path ever reuse a stale output (zs.json, certs) from the interrupted attempt in a certificate or the Turing count?
     - can it run with a different nonce or key? With the nonce file replaced, the driver refuses before the library is reached; see G3n
       (iv).
     - does it weaken any earlier refusal (N13 misrouting, foreign replay checkpoint, role/nonce pins)?
     - is `gen_finished`'s stricter definition safe for runs without `--turing-grid`?
6. **Nits.**
   - The key and checkpoint are opened `O_NONBLOCK`, checked `S_ISREG` before any read, and then have `O_NONBLOCK` cleared.
   - A NUL byte means the line is never authenticated (header: refuse; item: rejected, `lines_nul`).
   - The header body must match exactly (`strcmp`, then `header_diff` only names the fields).
   - The directory is fsynced after a new header.
   - Check the races around the `O_CREAT` of a FIFO path (it is not created: an existing FIFO is opened non-blocking and refused) and
     around symlinked checkpoint paths, which are unchanged from v14c and still followed.
7. **Test hooks** (`-DZF_TEST_HOOKS` only): `ZFAST14D_TEST_WFAIL_AT`, `ZFAST14D_TEST_SYNCFAIL`, `ZFAST14D_TEST_RADIUS`.
   - Confirm that the production dylib contains no hook strings and no `getenv`.
   - Confirm that the provider and driver refuse `ZFAST14D_TEST*`.
   - Confirm that `th_radius` is applied identically in the worker and in `verify_sample`, so that R3 tests what it claims.
8. **Compute path and identity.** Confirm that nothing new runs in an uninterrupted session except one atomic load per item dispatch.
   Re-run your own differential of v14d against v14 (`../review_v14c/scratch/diff_rv.py` and `kill_rv.py` with the library path
   changed). The builder's copies are in `../runs/m14/rv/`.

## Builder's tests you may reuse (re-run them; do not trust their verdicts)

- `../runs/m14/neg/fix_m14.py` (R3, R3c, D1/D2, E1 to E3, N1 to N4)
- `negtests_m14.py`, `attack_m14.py`, and the generator `make_suites_m14.py`, which lists every changed expectation
- `asan/` (UBSan + libgmalloc)
- `../runs/m14/rv/` (your v14c suite, adapted)
- `../tools/m14_rt/run_rt.sh`
- `engine/regress_v1/v5za_gate.py`, all modes

## Deliverable

`review_v14d/REVIEW.md` should contain:

- a verdict (PASS / PASS WITH CONDITIONS / FAIL);
- the findings by severity;
- the tests you ran;
- answers to items 1 to 8;
- whether v14d/v5za may be used for the multi-day resumable 10^28 window that feeds the certificates and the Turing grid.

The reboot-resume rehearsal (`../tools/reboot_rehearsal_m14/README_PHIL.md`) is Phil's action. It is not part of this review, but the
scripts may be read.
