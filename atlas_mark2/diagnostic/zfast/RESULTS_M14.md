# RESULTS_M14: libzfast v14d + atlas_v5za (closing review_v14c), 2026-11-02

**Pre-registration.** `PREDICTIONS_M14.md`, sha e276dbe7… (`PREDICTIONS_M14.sha256`). It was hashed at 22:07, before any v14d code, and
made read-only. The machine was idle at the start (`ps`). Every heavy step ran alone at nice 19 under `runs/m14/gates/watchdog.sh`
(footprint ≤ 3 GB, disk ≥ 2 GB): there were no kills and no disk events, and free disk stayed ≥ 7 GB. No session went above 10^20 (the
gates stop at 10^20; G1 regenerates the frozen 10^22 window as in M13). No brew command was run. HOMEBREW_NO_AUTO_UPDATE=1 and
HOMEBREW_NO_INSTALL_UPGRADE=1 were set in every script. Manifest: `MANIFEST_M14.sha256`.

## 0. Answer first

- **Every review_v14c finding is fixed in new trees.** That covers MJ-C1, mn-C1, mn-C3, mn-C4 and all six nits. The new trees are:
  - `src/v14d` and `bin/src_v14d`;
  - `bin/libzfast.v14d.dylib` **e0ed15f3cd4d62f887ab62cf6f6af0be5f378d356e35663ef9bafd432c425b81**;
  - `bin/libzfast.v14d_testhooks.dylib` **e6c011ce0840d8b89988f624d9bc8ebe2185a380c16dc15c60f6a39703a06e07**, built by the unchanged
    `src/build_v8.sh`;
  - `atlas_v5za/` (V5ZA_FREEZE, 38 entries; built by `tools/make_v5za.py`);
  - `engine/regress_v1/v5za_gate.py`;
  - the permanent MJ-C1 test `tools/m14_rt/`.
- **Nothing old was modified.** Nothing in v14, v14b, v14c, v5z7, v5z8, v5z9, any frozen tree or any existing key was modified, and no
  file was deleted.
- **MJ-C1 is closed.** Honest balls with 30-bit radius mantissas now load bit for bit:
  - 300,000 width-swept balls with 0 failures, 10,000 of them at exactly 30 bits;
  - all 1,240,720 moment balls of the v5z7 10^22, 10^25 and 10^26 production checkpoints, 2,892 of them with a nonzero radius: 0
    failures;
  - honest library-written lines carrying radii of every width from 1 to 30 bits, through a kill, a verify-all resume and a full
    resume: identical;
  - the v14c control fails on exactly the 30-bit balls (10,000/10,000) and nowhere below 30 bits.
- **The compute path is untouched.** The I1 matrix against v14 is **77/77 bit-identical**, the reviewer's differential is **29/29**,
  and the reviewer's SIGKILL suite is **9/9**. Kill/resume (I3a, I3b, G2, G3, G4) is identical too.
- **The checkpoint cost ratio is unchanged.** At 10^20 D2 W8 it is v14d/v14 = **1.0385** (v14c: 1.037).
- **Gates.** tier 0, tier 1, `turing_gate all` and v5za_gate in all seven modes: **PASS**.
- **Status.** v14d/v5za are **not production until the focused independent re-review (`review_v14d/BRIEF.md`) passes.** Self-review
  does not count. Until then the v14c/v5z9 rules stand, and v5z7/v14 remains production.

## 1. What was built

The compute files are byte copies of v14c (= v14): `zfast.c`, `m3c`, `api3`, `api4`, `api14`, `hash14`, `zfast.h` and the CLIs
(`review_v14d/identical_files.txt`). `zfast_sched14d.inc` replaces `zfast_sched14c.inc`. `zfast_m3b.inc` changes only the include, two
info fields and comments. `zfast_api14b.c` changes only `"lib": "v14d"`. The edits were made by counted replacements
(`runs/m14/dev/edit_sched14d.py`). The diffs are in `review_v14d/`.

| finding | v14d fix |
|---|---|
| MJ-C1 | `parse_arb_strict` builds the radius exactly: a mantissa token of more than 30 bits is refused; otherwise `MAG_MAN = m << (30 − bits)` and `MAG_EXP = e + bits`. `mag_valid` and the canonical re-dump check are kept. |
| mn-C1 | An identical authenticated duplicate (same body SHA-256 for that item) is ignored and counted in `lines_duplicate`, which now counts. A conflicting duplicate stays fatal. |
| mn-C4 | **The abort policy.** Every checkpoint write or fsync error goes through `ck_fail`, which records it, closes the file and sets an atomic `ioabort`. This covers worker lines, the flusher, the newline repair, the header, the final sync and the directory fsync. Workers then take no new item. `zfa14b_new` returns NULL with `CKPT-IO-ABORT: …`, which names the error, the items done and the lines written. The checkpoint stays valid and resumes. **Why abort:** days of unprotected compute are the failure the checkpoint exists to prevent, and the abort costs at most the items in flight. The trade-off: an aborted unattended window waits for someone to resume it. |
| mn-C4 (pipeline) | The v5za provider writes `<ckpt>.refusals.jsonl` and raises. A returned session with write errors also raises. The driver detects CKPT-IO-ABORT for the generator or the replay, logs `stage=ckpt_io_abort`, prints a banner and **exits 3**. `run_wideA.sh` stops on rc 3. |
| mn-C3 | `--resume` after the session build. It needs all of: `--resume --wide`; no `replay_check/` and no `zfast_ckpt_replay.txt`; the generator checkpoint and nonce present; a gen-role sidecar record of the nonce. The interrupted outputs are **moved** to `RUN/gen_postbuild.attempt<k>/` (with a README), and the generator re-runs on the complete checkpoint with the same nonce and key. "Finished" now also requires the `turing_grid` stage when one was requested: `gen_done` is logged before the grid, so v5z9 would have treated a crash during the grid as finished. |
| nits | The key and the checkpoint are opened O_NONBLOCK and must be regular files (no FIFO hang). A line with a NUL byte is never authenticated (`lines_nul`). The header must match byte for byte. The message is fixed. The directory of a new checkpoint is fsynced (`ckpt_dir_synced`). The driver records `key_created`, `key_reused_new_header`, `lines_nul` and `ckpt_dir_synced`. |

Test hooks exist only in the test-hooks dylib: `ZFAST14D_TEST_WFAIL_AT`, `_SYNCFAIL` and `_RADIUS`. The production dylib contains no hook
strings, and the provider and driver refuse `ZFAST14D_TEST*`.

## 2. Predictions: MET / MISS

### Section 1: MJ-C1 (`reports/v5za_roundtrip_20261102_222142.json`, PASS)

| # | outcome | verdict |
|---|---|---|
| R1 | Width sweep: 300,000 (10,000 per width 1–30, 10,000 at 30 bits), 0 failures. Random: of 300,000 `arb_randtest` balls, 0 round-trip failures, **but 10,105 (3.4 %) are refused** by the pre-existing `mag_valid` rule (radius exponent > 40 bits; arb_randtest's mag bits go up to 60). The rule as written ("0 failures") does not hold for them. | **MISS (literal wording)**; MJ-C1 itself MET. The refusals are a documented range bound, not a rounding defect; honest moment radii have exponents of a few hundred. Flagged for the re-review. |
| R1c | v14c control: 10,000/10,000 of the 30-bit balls fail and 0 below 30 bits; 50,442 random balls fail | **MET** |
| R1n | 12 non-canonical tokens (31-bit, even, negative, leading-zero, 5,000-digit) all refused, no signal | **MET** |
| R2 | 1,240,720 production balls (v5z7 1e22/1e25/1e26, gen and replay, read-only), 2,892 with a nonzero radius, 0 failures | **MET** |
| R3 | RADIUS hook: 4,800 nonzero radii in the file, widths 1–30 all present, 160 at 30 bits. Kill (rc 77) then verify-all resume: 120 loaded, 120 verified, identical. Full resume at W3: 480 loaded, identical. The hook state differs from the no-hook state (control). | **MET** |
| R3c | `3fffffff -1f4` key-resealed: v14c refuses ("not canonical"); v14d accepts (480 loaded; a forged value, verify 0) | **MET** |

### Section 2: the other fixes (`runs/m14/neg/out_fix/fix_results.json`, 17/17)

| # | outcome | verdict |
|---|---|---|
| D1 | Appended / inserted before the original / the whole file appended to itself: rc 0, honest, `lines_duplicate` 1 / 1 / 480 | **MET** |
| D2 | Conflicting duplicate refused in either order | **MET** |
| E1 | RLIMIT_FSIZE: rc 3, `CKPT-IO-ABORT: checkpoint write failed (File too large)`, 77 of 480 items done. Resume: 76 loaded, 1 torn line rejected, identical. | **MET** |
| E2 | WFAIL_AT 50: rc 3 (write, EIO), 49 item lines; resume: 49 loaded, identical | **MET** |
| E3 | SYNCFAIL 1 at 10^18: rc 3 (fsync, EIO) after 24 of 1,104 items; resume identical | **MET** |
| N1 / N1b | A FIFO key, a FIFO checkpoint and a directory checkpoint are each refused within 0.1 s | **MET** |
| N2 / N2b | NUL then junk, and NUL mid-line: rejected (`lines_nul` 1), honest. A header with a NUL byte: refused. | **MET** |
| N3 | Header with a double space: refused, `format (whitespace)` | **MET** |
| N4 | `ckpt_dir_synced` 1, `ckpt_io_policy` "abort", fresh checkpoint identical | **MET** |

### Section 3: identity

| # | outcome | verdict |
|---|---|---|
| I1 | `reports/v5za_identity_20261102_230031`: 77/77, 0 mismatches; control D1 ≠ D2 | **MET** |
| I2 | Fresh checkpoint = no checkpoint at 10^14 and 10^20 (1,460 lines for 1,459 items, 18 syncs, `max_unsynced_s` 1.021) | **MET** |
| I3a / I3b / I4 | SIGKILL at 306 lines, resume W3: 305 loaded, 8 verified, identical. EXIT_AFTER 120: identical. Generic kernel: identical. | **MET** |
| I5 | `runs/m14/rv/out_diff`: 29/29 cases × 6 sessions identical; every partial resume rejected exactly 1 torn line; max `max_unsynced_s` 1.015 | **MET** |
| I6 | `runs/m14/rv/out_kill`: 9/9 identical, 18 real SIGKILLs, no refusals | **MET** |
| G1 | `reports/v5za_w1e22_20261102_231508`: PASS | **MET** |
| G2 | Generator SIGKILLed at 271 lines, `--resume`: 270 loaded, 64 verified, window and Turing grid identical | **MET** |
| G3 | Generator SIGKILLed **after gen_done, during the Turing grid**. `--resume` moved zs.json, certs, certs_np, gen_measurements.json, gen.log and gen.jsonl into `gen_postbuild.attempt1/`. The resumed session loaded 1,075/1,075 items and verified 64. Window and Turing grid identical. (G3a, killed right after zs.json: the same, identical.) | **MET** |
| G3n | (i) no `--resume`, (ii) `replay_check/` present, (iii) sidecar moved away, (iv) nonce file replaced: all refused, rc 1, nothing moved | **MET**, with one deviation: (iv) is refused by the **driver** (no sidecar record of the new nonce) before the library is reached. The prediction's parenthesis said the library would refuse. |
| G4 | `reports/v5za_ioabort_20261102_225727`: under RLIMIT_FSIZE the pipeline exits **rc 3**: one `ckpt_io_abort` record (147 of 1,075 items), the banner printed, a refusal sidecar record, no replay. `--resume`: 143 loaded; window and Turing grid identical. | **MET** |
| N13 | v5z7 reuses the misrouted checkpoint silently; v5za's replay refuses (rc 1) | **MET** |
| C | Checkpointed build at 10^20 D2 W8: 17.035 s against 16.404 s, ratio 1.0385 | **MET** |

### Sections 4 and 5: earlier suites and gates

| suite | outcome | verdict |
|---|---|---|
| M12 N-tests (`negtests_m14.py`) | 20/20. N8 now refuses with CKPT-IO-ABORT and resumes identically (the pre-registered change). | **MET** |
| M13 attack suite (`attack_m14.py`) | 25/25 (A1c: duplicate ignored and counted; A6: abort and resume) | **MET** |
| reviewer `attack_rv.py` (adapted) | 73/73: the reviewer's 72 cases plus the provider check for `ZFAST14D_TEST_RADIUS`. The changed expectations held: duplicates ignored, the FIFO key refused, the header double space refused. | **MET** |
| reviewer `fuzz_rv.py` | 362 cases, 0 crash / hang / watchdog. Against the reviewer's v14c run only two cases changed class: `rad_3fffffff` (refused → accepted canonical, rc 1 as in the reviewer's other 25 accepted forgeries) and `nul_mid` (refused → rejected, honest) | **MET** |
| UBSan + libgmalloc | Seed 2026: 300 cases (209 refused, 88 accepted). Seed 7: 300 cases (198 refused, 99 accepted). **0 crashes, 0 sanitizer reports.** The accepted cases are key-holder canonical values with verify 0, as in M13. | **MET** |
| tier 0 / tier 1 / turing_gate all | PASS / PASS (518 s) / PASS | **MET** |
| v5za_gate | roundtrip, identity, ckpt, postbuild, ioabort, n13 and w1e22: all PASS | **MET** |

### Section 6: reboot rehearsal (prepared, not executed)

`tools/reboot_rehearsal_m14/`:

- `step1_start_and_stop.sh`: 10^20 by default, D4 W8, SIGKILL after 300 lines, fingerprint recorded.
- `step2_resume_after_reboot.sh`: checks `kern.boottime`, diffs the fingerprint, runs `--resume`, runs an uninterrupted reference and
  compares (PASS/FAIL in `runs/m14/reboot/<name>/result.json`).
- `README_PHIL.md`: Phil's exact steps.

**Script smoke test only** (10^12, no reboot, `--no-reboot-smoke`, labelled as such in `result.json`): PASS. At 10^12 the session had
finished building before the kill, so the smoke test exercised the script logic but not a mid-build resume. The 10^20 default and the
300-line trigger do resume mid-build (I3a: 306 of 1,459 lines at 10^20 in about 5 s). The smoke test also caught one script bug: `set -u`
with no third argument, fixed. The failed first attempt is kept in `runs/m14/reboot/rr_20261102_233750/`.

## 3. Deviations

- **R1, literal MISS.** 10,105 of the 300,000 random balls are refused by the pre-existing 40-bit radius-exponent bound of `mag_valid`.
  I did not change that rule; it is v14b's documented range check. The test now reports these refusals in their own field
  (`refused_radius_exponent_over_40_bits`) and fails on any other failure. The classification was added to `tools/m14_rt/rt_arb.c`
  during development, before the official run.
- **G3n (iv).** The refusal came from the driver, not the library (see above).
- **Development builds.** `runs/m14/dev/libdev*.dylib` were scratch builds used for one dev pass of `fix_m14.py`; no claim rests on
  them. After that pass, the abort message was reworded (the repeated tag "CKPT-IO-ABORT" was removed). Every claim above comes from
  the official e0ed15f3 / e6c011ce build.
- **Keys.** The gate pipelines and the smoke test added new key files to `ckpt_keys/` (18 → 40), as the M12/M13 gates did. Their key
  paths are hard-wired in the driver. No existing key was read for writing, changed or removed.

## 4. What this does and does not establish

- **Established, by the builder's tests.**
  - A v14d checkpoint holding honest nonzero radii, including 30-bit ones, resumes bit-identically.
  - A copied line no longer destroys a checkpoint.
  - A checkpoint I/O error stops the session loudly (rc 3 through the pipeline) instead of letting it run on unprotected, and the run
    resumes from the checkpoint.
  - A generator crash after its session build, including during the Turing grid, resumes from the complete checkpoint with the same
    nonce and key.
  - No earlier refusal was weakened.
- **Not established.**
  - An independent review of these changes: `review_v14d/BRIEF.md`.
  - A resume across a real reboot: Phil's rehearsal, `tools/reboot_rehearsal_m14/README_PHIL.md`.
  - The operational conditions for the 10^28 window (review_v14c §3.2): macOS updates off, no brew, this Mac only. These are Phil's.
