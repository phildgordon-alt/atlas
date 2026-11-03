# RESULTS_M13: libzfast v14c + atlas_v5z9 (fixes for review_v14b), 2026-11-02

**Pre-registration.** `PREDICTIONS_M13.md`, sha f4f70ca7… (`PREDICTIONS_M13.sha256`), hashed 20:22, before any v14c code. Phil
approved the path on 2026-11-02 ("fixes → review → 1e28"). Machine idle at start (`ps`); every heavy step ran alone, nice 19, under
`runs/m13/gates/watchdog.sh` (footprint ≤ 3 GB, disk ≥ 2 GB): no kills, no disk events. Manifest: `MANIFEST_M13.sha256`.

## 0. Answer first

- **Every review_v14b finding is fixed in new trees:** MJ1 (a, b, c) and mn1–mn7. The new trees are `src/v14c`, `bin/src_v14c`,
  `bin/libzfast.v14c.dylib` (59883f5e…), `bin/libzfast.v14c_testhooks.dylib` (9c0d4a9b…), `src/build_v8.sh` (calls the unchanged
  build_v7 → build_v6, same flags), `atlas_v5z9/` (V5Z9_FREEZE, 37 entries) and `engine/regress_v1/v5z9_gate.py`. Nothing in
  v14/v14b/v5z7/v5z8, any frozen tree, `ckpt_keys/` or an existing gate was modified, and no file was deleted.
- **The reviewer's splice is now rejected.** On v14b it was accepted 6/6 with a wrong Z ball. On v14c the foreign lines fail
  authentication 6/6 (2 rejected per trial) and the state is bit-identical to honest B. Duplicates are refused. A new header under
  an existing key is reported and cannot be spliced.
- **The mn1 abort is gone, and so is a second abort class the M13 fuzz found** (see §3, D1). 600 re-sealed fuzz cases on a UBSan +
  libgmalloc build gave 0 crashes and 0 sanitizer reports. The reviewer's build had 7/150 aborts.
- **Identity.** Kill/resume is identical at 10^20 (I3a, I3b) and through the pipeline (G2). wide_1e22 regenerates under v5z9 (G1).
  The I1 matrix is 77/77 bit-identical to v14.
- **Gates.** tier 0 PASS; tier 1 PASS; turing_gate all PASS (52 windows); v5z9_gate ckpt / n13 / w1e22 PASS.
- **Cost.** The checkpointed build at 10^20 D2 W8 took 17.107 s on v14c against 16.497 s on v14 (ratio 1.037 ≤ 1.05). The measured
  maximum write-to-fsync age was 1.017 s.
- **Status.** v14c/v5z9 are **not yet production** until the independent re-review (`review_v14c/BRIEF.md`) passes. Self-review
  does not count. Until then the review_v14b interim rule stands: never move, rename or recreate a run's checkpoint; a different
  session gets a fresh run name.

## 1. What was built

The compute path is v14's, byte for byte. `zfast.c`, `zfast_m3c.inc`, `zfast_api3.c`, `zfast_api4.c`, `zfast_api14.c`,
`zfast_hash14.inc` and the CLIs are identical to `bin/src_v14b` (= v14). The remaining changes:

- `zfast_m3b.inc`: the include, 5 info fields and comments.
- `zfast_api14b.c`: the bad-T0 error, `"lib": "v14c"` and the buffer size.
- `zfast.h`: one declaration.
- `zfast_sched14c.inc` replaces `zfast_sched14b.inc`.

The ctypes API names and signatures are unchanged, so v14c is a drop-in. Diffs are in `review_v14c/`.

| finding | fix (as pre-registered unless noted) |
|---|---|
| MJ1 a | Format `ZFAST14C CKPT v3`. A new header carries a random 16-byte `hnonce`. Header seal = HMAC(K, "ZF14C-HDR\0" ‖ body). Item line `I x b i lo hi …`, seal = HMAC(K, "ZF14C-ITEM\0" ‖ SHA-256(header body) ‖ u64be(x) ‖ body). After authentication, x = first[b] + i is required. |
| MJ1 b | Any second authenticated line for a loaded item is fatal: "conflicting duplicate" or "identical duplicate". The per-item SHA-256 of the loaded body classifies which. Identical duplicates are refused because an honest writer never emits one. |
| MJ1 c | A new header under an existing key is allowed (crash recovery), with a stderr note and `key_reused_new_header` 1. A fresh hnonce gives it its own sealing domain. |
| mn1 | The parser pre-validates canonical hex tokens (zero mantissa ⇒ exactly `0 0`; the radius is unsigned) and **no longer calls `arb_load_str`**. Each ball is built with `arf_set_fmpz_2exp` / `mag_set_fmpz_2exp_fmpz`, then the canonical re-dump check runs. The second half of this is the D1 amendment. |
| mn2 | A flusher thread F_FULLFSYNCs every 1.0 s while lines are unsynced (`pthread_cond_timedwait_relative_np`, so a wall-clock step cannot stall it), plus after the header and at the end. Bound: a line is durable by its write time + 1 s + one F_FULLFSYNC. `max_unsynced_s` is measured. |
| mn3 | Header adds `bin_uuid`, `bin_text_sha` (in-memory `__TEXT`), `flint/gmp/mpfr_uuid`, `libm_uuid`, `dyld_cache_uuid`, `hw_model`. Any unavailable field refuses; no placeholder exists. |
| mn4 | Keys are created through a temp file (O_EXCL\|O_NOFOLLOW, 0600), F_FULLFSYNC, `renamex_np(RENAME_EXCL)` and a directory fsync. An existing key must be regular, not a symlink, owned by the euid, mode & 077 = 0, and 32 bytes. A 0-byte key has its own refusal. |
| mn5 | The first worker write/fsync error reaches `zfa14b_last_error`. `lines_written` can no longer go negative. A bad T0 sets an error. |
| mn6 | A bounded line reader: lines over max(64 KiB, 2 × estimate + 4096) are skipped unstored, counted in `lines_overlong` and as rejected. |
| mn7 | The v5z9 generator verify default is 64 (replay 8). Per resume, the detection probability for k forged-but-authentic items among N loaded is 1 − C(N−k, 64)/C(N, 64); for k = 1 this is 64/N (≈ 0.96% at the 10^26 scale, N = 6,696). The key holder is still trusted. |

Nits fixed as well: the tag compare is now constant-time, and `sprintf` is gone.

## 2. Predictions: MET / MISS

### Identity and gates

| # | outcome | verdict |
|---|---|---|
| I1 | `reports/v5z9_identity_20261102_211108`: 75 matrix + 2 legacy comparisons, 0 mismatches (state SHA-256, Z-grid bytes, rows, Z strings); control D1 ≠ D2 state | **MET** |
| I2 | A fresh checkpoint equals no checkpoint at 10^14 (D2 W1) and 10^20 (D2 W8; 1,460 lines for 1,459 items; 18 syncs in 16.9 s) | **MET** |
| I3a | SIGKILL at 311 lines (W8), resume at W3: 310 loaded, 8/8 verified, 0 rejected, identical; resume took 6.2 s | **MET** |
| I3b | Test-hooks EXIT_AFTER 120 (rc 77), resume: 120 loaded, 8 verified, identical to v14 | **MET** |
| I4 | GENERIC_KERNEL=1 (test-hooks) equals production at 10^16 | **MET** |
| G1 | `reports/v5z9_w1e22_20261102_204849`: PASS. Pieces differ only in {z_provider, zfast_session}, with an identical core. Wall 698 s. | **MET** |
| G2 | `reports/v5z9_ckpt_20261102_204351`: pipeline 10^16, generator SIGKILLed at 261 lines, then `--resume`: window and Turing grid identical. The resumed generator loaded 260 and **verified 64**. The replay sidecar shows role replay with the run's nonce, ok true. | **MET** |
| C | Cost ratio 1.037; `max_unsynced_s` 1.017 (I2 at 10^20) | **MET** |
| T0 | `reports/tier0_20261102_210031`: PASS | **MET** |
| T1 | `reports/tier1_20261102_210219`: PASS (518 s) | **MET** |
| TG | `reports/turing_all_20261102_211057`: PASS, 52 windows gated | **MET** |
| N13 | `reports/v5z9_n13_*`: v5z7 replay silently reuses the misrouted generator checkpoint and passes. The v5z9 replay refuses ("header line is not authenticated"); replay fails and the driver returns rc 1. | **MET** |

### Review attacks (`runs/m13/neg/out_attack/attack_results.json`, 25/25 OK, official libraries)

| # | v14c observed | verdict |
|---|---|---|
| A1 | Reviewer splice, 6 trials: rc 0, 2 rejected each, 480 loaded, state = honest B | **MET** |
| A1b | Key-holder reseal of A's content for B's header and index: refused "conflicting duplicate", in either order | **MET** |
| A1c | B's line appended twice: refused "identical duplicate" | **MET** |
| A1d | Index token changed: rejected (1), honest. Reversed line order: 480 loaded, identical (control) | **MET** |
| A1e | The reviewer's v14b splice file and a v14b checkpoint: refused (header not authenticated). A's header with B's lines: refused [u0, prefast]; at u0 50, all 480 of B's lines are rejected and the state is honest | **MET** |
| A2 | 6 key-resealed malformed-arb cases (incl. the exact `flint_abort.py` case `0 4`): all rc 3 with a reason, no signal | **MET** |
| A2f | UBSan + libgmalloc build of the final source: 300 cases at seed 2026 and 300 at seed 7, **0 crashes / 0 sanitizer reports** (`asan/fuzz_m13.log`, `fuzz_m13_s7.log`). Of the 82 + 90 rc-0 cases, 4 + 1 leave the state honest (the line was ignored as unauthenticated, or the mutation was a no-op after canonicalisation). The other 78 + 89 are canonical values re-sealed by a key holder with verify 0, accepted by design (the trust model; the reviewer's fuzz also accepted such cases). The canonical re-dump check makes acceptance of a non-canonical value impossible. | **MET** (final build; the first build MISSED, see D1) |
| A3 | (a) 0-byte key refused with its own reason and left untouched. (b) KEYCRASH: rc 78, no final key, one 32-byte temp left; the rerun creates a fresh key (0600) and is identical. (c) mode 0644 and (d) symlink both refused | **MET** |
| A4 | (a) 9 forced env failures (bin, bin_text, flint, gmp, mpfr, libm, dyld_cache_uuid, os, hw_model) all refused "environment identity unavailable". (b) The production dylib has no placeholder strings and no hook names. (c) Altering dyld_cache_uuid, bin_text_sha, hw_model, libm_uuid or bin_uuid and resealing refuses, naming exactly that field | **MET** |
| A5 | 64 MiB line in the middle, and a 64 MiB tail with no newline: rc 0, identical, `lines_overlong` 1, maxrss 25.8 MiB vs 25.3 MiB plain | **MET** |
| A6 | RLIMIT_FSIZE: session identical; `last_error` = "checkpoint write error … File too large"; 77 written | **MET** |
| A7 | 10^18 D2 W1: sec_fast 7.95 s, 9 syncs, `max_unsynced_s` 1.015 | **MET** |
| A8 | Empty checkpoint + existing key: created, `key_reused_new_header` 1, `key_created` 0, stderr note, identical | **MET** |

The reviewer's attack_rv.py checks were also adapted and run:

- role/nonce;
- 16 torn offsets: each refuses (torn header) or is bit-identical, and a second resume is identical;
- glued line;
- 30 key-resealed parser mutations: none accepted except the canonical wider radius `0 0 → 1 0`, which the reviewer also recorded
  as canonical;
- 7 re-sealed header tampers, including a dropped or short hnonce: all refused;
- a header re-sealed with another hnonce: all 480 lines rejected, state honest;
- LBSHIFT [prefast];
- a test-hooks checkpoint loaded by production: refused [bin_sha, bin_uuid, bin_text_sha, hooks];
- flock.

All OK.

### M12 negative tests on v14c (`runs/m13/neg/out_neg/negtests.json`, 20/20 OK)

P1, P2, N1, N1c, N2, N2b, N3, N4, N5, N5k, N6, N7 (2^62, 2^63−1), N8, N9, N11, N12, N14 and N15 all behave as in M12. N13 is
covered by the gate (above). The test was adapted in three ways: m13_probe; v3 seals; and the token offset +1. **Key copies are
made 0600.** The first adapted run used 0644 copies, and v14c refused them all with "group/other permissions". That is the new
mn4 rule working, not a regression.

## 3. Deviations and amendments

- **D1 (20:36, before any gate or claim-bearing run).** The first official build (59883f5e is the second; the first was 2e648e10…)
  failed A2f with 3/300 SIGABRTs.
  - Cause: a second FLINT abort class, `mag_set_arf_dump`, triggered by a radius mantissa that a mag cannot hold, e.g. `7fffffff`.
    The pre-registered pre-validation covered only zero mantissas.
  - Fix: `parse_arb_strict` no longer calls `arb_load_str` (the reviewer's suggested alternative).
  - At the same time, the flusher's absolute wall-clock timeout was replaced by a relative monotonic one. Reason: robustness to a
    clock step.
  - The first build was **moved** (not deleted) to `bin/superseded_v14c_build1/` with a README. Its light-suite outputs are kept
    (`runs/m13/neg/*_build1*`).
  - Every claim above is from the final build.
- **Test-harness fixes during development, all before the official runs.** None changes a library verdict.
  - The attack script truncated reason strings before matching.
  - The canonical wider-radius mutation is now classified as canonical, as in the review.
  - The negtests format detection matched the `ZFAST14CKPT` prefix too loosely.
  - Key copies are made 0600.
- **Gate bookkeeping.** In the first chain the identity gate crashed after 2 s on a key-rename slip in my copy of v5z8_gate (a
  KeyError; no comparison had run). Fixed and re-run alone after the chain (21:11–21:26, PASS).
- **Partial tree.** The first `make_v5z9.py` run stopped on a wrong replacement count after copying files. The partial tree was
  moved to `runs/m13/dev/atlas_v5z9_partial1/`, and the tree was rebuilt cleanly and frozen.

## 4. What this does and does not establish

- **What it establishes.** A resumed v14c session loads only lines sealed for its own checkpoint header (fresh hnonce) and index,
  under its run/role key. Foreign or spliced lines are ignored; duplicates and malformed authenticated input refuse with a reason.
  The parser has no known abort path, and the ball computations are v14's.
- **Residual trust.** This is unchanged: whoever holds `ckpt_keys/` (the same trust as the code) can forge canonical lines. The only
  checks on such lines are the per-resume sample (generator 64/N) and, for certificate rows only, the replay of record.
- **Operational consequence of mn3.** Any OS update (including a background security response that changes the dyld shared cache)
  or a move to another Mac between sessions refuses a resume, which forces a fresh run name. Keep automatic macOS updates off for the
  1e28 window. This is a recommendation for Phil; I changed no settings.
- **Self-review does not count.** v14c/v5z9 are not used for any claim until `review_v14c/BRIEF.md`'s review passes.
