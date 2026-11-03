# PREDICTIONS_M13: libzfast v14c + atlas_v5z9 (fixes for review_v14b), pre-registration (2026-11-02)

Hashed (`PREDICTIONS_M13.sha256`) **before** any v14c code is written, built or run. Phil approved the path on 2026-11-02 ("fixes ->
review -> 1e28"). Input: `review_v14b/REVIEW.md` (PASS WITH CONDITIONS; major MJ1; minors mn1-mn7).

**Rules.** nice 19; one heavy job at a time; footprint watchdog <= 3 GB; disk floor 2 GB; explicit raises; -O / PYTHONOPTIMIZE refused.
New dirs/files only: `src/v14c`, `bin/src_v14c`, `bin/libzfast.v14c.dylib`, `bin/libzfast.v14c_testhooks.dylib`, `src/build_v8.sh`
(calls the unchanged `build_v7.sh`, hence `build_v6.sh`: same flags `-O2 -mcpu=apple-m1 -ffp-contract=off -fno-fast-math`),
`atlas_v5z9/`, `tools/make_v5z9.py`, `tools/m13_probe.py`, `runs/m13/`, `engine/regress_v1/v5z9_gate.py`, `review_v14c/`.
Nothing in v14 / v14b / v5z7 / v5z8 or any frozen tree is modified. No key file is deleted or overwritten.

## 0. Design (fixed here)

The compute path stays v14's byte for byte (`zfast.c`, `m3c`, `api3`, `api4`, `hash14`, CLIs unchanged; items, merge, workers,
`split_ranges` unchanged). Only the checkpoint layer (`zfast_sched14c.inc`, replacing `zfast_sched14b.inc`) and the small wiring in
`zfast_m3b.inc` / `zfast_api14b.c` change. The ctypes API keeps its names and signatures (`zfa14b_new`, `zfa14b_info`,
`zfa14b_last_error`), so v14c is a drop-in for the v5z8 provider; the library is identified by its pinned SHA, `lib` id
`zfast-v14c(PREDICTIONS_M13)`, info `"lib": "v14c"` and the file format `ZFAST14C CKPT v3`.

| finding | v14c fix |
|---|---|
| MJ1 (a) | A new checkpoint's header carries a fresh random `hnonce` (16 bytes, arc4random). Header seal = HMAC(K, "ZF14C-HDR\0" ‖ header_body). Item lines carry the global item index x as their 2nd token (`I x b i lo hi ...`); line seal = HMAC(K, "ZF14C-ITEM\0" ‖ SHA-256(header_body) ‖ u64be(x) ‖ line_body). A line sealed under any other header (other session, other run, recreated file, same key) or at another index fails authentication and is ignored (never loaded). After authentication x must equal first[b] + i. |
| MJ1 (b) | Any second authenticated line for an already-loaded item is FATAL (refuse), whether its contents differ ("conflicting duplicate") or not ("identical duplicate"). Decision for identical duplicates: refuse, because an honest writer never emits one (loaded items are never recomputed; torn lines are not authenticated), so a duplicate is evidence of file manipulation. |
| MJ1 (c) | Key reuse is no longer silent and no longer exploitable: when a new header is created under an existing key, the header's fresh hnonce gives the new file its own line-sealing domain (so the crash-between-key-and-header case recovers), a stderr note is printed and info reports `key_reused_new_header` 1 (`key_created` 1 for a fresh key). |
| mn1 | Before `arb_load_str`, the four arb tokens are pre-validated: a zero midpoint or radius mantissa must be exactly `0` with exponent exactly `0`; the radius mantissa has no sign; mantissa tokens have no leading zero. Malformed authenticated input refuses with a reason, never SIGABRT. |
| mn2 | A flusher thread issues F_FULLFSYNC (fallback fsync) every 1.0 s while unsynced lines exist, independent of item completion; plus after the header and at session end. True bound: a line whose write(2) returned at time t is on stable storage by t + 1 s + one F_FULLFSYNC duration, unless a write/fsync error is reported. The library measures and reports `max_unsynced_s` (largest observed write-to-sync age). |
| mn3 | The header adds `dyld_cache_uuid` (`_dyld_get_shared_cache_uuid`), `hw_model`, the LC_UUID of each loaded image (`bin`, `flint`, `gmp`, `mpfr`, `libm`) and `bin_text_sha` (SHA-256 of the zfast image's in-memory `__TEXT` segment). Any unavailable field (dladdr, read, sysctl, uuid) REFUSES the checkpoint ("environment identity unavailable"); no placeholder string exists. |
| mn4 | Key creation: temp file (O_EXCL, O_NOFOLLOW, 0600) → 32 bytes → F_FULLFSYNC → `renamex_np(RENAME_EXCL)` → fsync of the key directory. An existing key must be a regular non-symlink file owned by the euid with mode & 077 = 0 and exactly 32 bytes; a 0-byte key is refused with a specific reason and is never overwritten. |
| mn5 | Worker write/fsync errors are stored in the session (first message) and surfaced in `zfa14b_last_error` on the creating thread after a successful build; `lines_written` never goes negative; `zfa14b_new` sets an error for a bad T0. |
| mn6 | A bounded line reader replaces getline: a line longer than cap = 2 × (estimated maximal item line) + 4096 bytes (and at least 64 KiB) is skipped without being stored and counted (`lines_overlong`, also in `lines_rejected`). |
| mn7 | atlas_v5z9 gives the generator session `ZFAST_CKPT_VERIFY` default 64 (replay stays 8; both overridable). Detection probability per resume for k forged-but-authentic items among N loaded: 1 − C(N−k, 64)/C(N, 64) ≥ 1 − (1 − k/N)^64; for k = 1 it is 64/N (≈ 0.9% at N ≈ 7,000 items, the 10^26 scale); cost ≈ 64 item recomputations per resume. The key holder remains trusted (unchanged trust model). |

atlas_v5z9 = atlas_v5z8 with counted replacements (`tools/make_v5z9.py`): provider pinned to libzfast.v14c; `lib='v14c'`; hook
prefixes add `ZFAST14C_TEST`; generator verify default 64. Nothing in certificate content changes.

## 1. Identity (acceptance rule: bit-identity; any miss means v14c/v5z9 are not used for claims)

| # | prediction | pass rule |
|---|---|---|
| I1 | Matrix as M12: T ∈ {10^12, …, 10^20} (u0 50, H 61, Δ 0.012) × D ∈ {1, 2, 3, 5, 7} × W ∈ {1, 3, 8} plus 10^16 legacy (H 4, Δ 0.15, D 2, W 1/8): v14c (no checkpoint) state SHA-256, Z-grid bytes, rows and Z strings equal v14's | 0 mismatches (77) |
| I2 | v14c with a fresh checkpoint equals v14 without one (10^14 D2 W1; 10^20 D2 W8) | equal |
| I3 | (a) real SIGKILL after ≥ 300 lines at 10^20 W8, resume W3, verify 8; (b) test-hooks EXIT_AFTER 120 + resume | identical |
| I4 | test-hooks GENERIC_KERNEL=1 equals production v14c (10^16 D2 W4) | equal |
| G1 | v5z9 regenerates atlas_v5z5 wide_1e22 under the M9/M12 G1 rules | all |
| G2 | v5z9 pipeline 10^16: generator SIGKILLed after ≥ 50 lines, `--resume`: window identical incl. Turing grid; generator session verified = min(64, loaded) | identical |
| T0/T1/TG | regress_v1 tier 0, tier 1, `turing_gate all` | PASS |
| C | checkpointed build at 10^20 D2 W8: v14c / v14 (both checkpointed) ≤ 1.05; I2 `max_unsynced_s` ≤ 1.5 | met |

## 2. Review attacks: each is REFUSED on v14c

"REFUSED" means the foreign or malformed data is not used: either the session is refused with a reason (rc 3, no signal), or every
foreign line is rejected (counted) and the result is bit-identical to honest. Light (10^14, D2, W1), `runs/m13/neg/`.

| # | finding | test | v14b (observed in review / predicted) | v14c (predicted) |
|---|---|---|---|---|
| A1 | MJ1 | reviewer §6 splice: session B (u0 50.5, A's key copied to B's key path, fresh file), then B header + 2 of A's lines + all of B's, 6 trials | accepted 6/6, state ≠ honest B | 6/6: A's lines rejected (2 each), state = honest B |
| A1b | MJ1 | A's lines resealed by the key holder for B's header and index (conflicting duplicates of B's items) | first wins, accepted | refused "conflicting duplicate" |
| A1c | MJ1 | one of B's own lines appended a second time (identical duplicate) | ignored as duplicate | refused "identical duplicate" |
| A1d | MJ1 | an authentic line with its index token x changed (resealing not possible without the header binding) | n/a | rejected (ignored), state honest |
| A1e | MJ1 | the v14b splice files from `review_v14b/scratch/out_attack` and a v14b-format checkpoint given to v14c | n/a | refused (header format / not authenticated) |
| A2 | mn1 | key-resealed arb with zero mantissa and exponent ≠ 0 (radius and midpoint), as `flint_abort.py` | SIGABRT (rc −6) | rc 3, reason names the zero-mantissa rule |
| A2f | mn1 | 300-case re-sealed random mutation fuzz (reviewer's class) on a UBSan + libgmalloc build of v14c | 7/150 aborts | 0 crashes, 0 sanitizer reports |
| A3 | mn4 | (a) existing 0-byte key + empty checkpoint; (b) test-hooks crash after the temp key write, then rerun; (c) key mode 0644; (d) key is a symlink | (a) refused forever | (a) refused, specific reason, key untouched; (b) no final key left by the crash, rerun creates a fresh key and succeeds, identical; (c), (d) refused |
| A4 | mn3 | (a) test-hooks forced env-identity failure (each of bin / flint / os / dyld uuid); (b) production dylib strings contain no `no-image` / `unreadable`; (c) `dyld_cache_uuid` and `bin_text_sha` altered and resealed | placeholders compared equal | (a) refused "environment identity unavailable"; (b) none; (c) refused naming the field |
| A5 | mn6 | 64 MiB unauthenticated line (and a 64 MiB tail with no newline) inside a valid checkpoint | getline allocates ≥ 64 MiB | resume succeeds, identical, `lines_overlong` ≥ 1, maxrss increase < 16 MiB vs a plain resume |
| A6 | mn5 | N8 failed write (RLIMIT_FSIZE) | message only on stderr of the worker | `zfa14b_last_error` contains "checkpoint write failed"; `lines_written` ≥ 0; state honest |
| A7 | mn2 | 10^18 D2 W1 checkpointed session (several seconds) | sync only on item completion | `ckpt_syncs` ≥ ⌊sec_fast⌋ − 1 and `max_unsynced_s` ≤ 1.5 |
| A8 | MJ1 (c) | empty checkpoint with an existing key | silent reuse | created, `key_reused_new_header` 1, stderr note; with A1 the reuse cannot splice |

**M12 negative tests, re-run on v14c** (adapted to the v3 line format: one extra token; v3 sealing): P1, P2, N1, N1c, N2, N2b, N3, N4,
N5, N5k, N6, N7, N8, N9, N11, N12, N14, N15 behave as in M12 (refuse / report), plus N13 (pipeline misrouting) under v5z9 via the
gate. Each must still refuse.

## 3. Stops

Any identity miss: v14c/v5z9 not used; report. Any attack accepted: that fix reported MISS, not claimed. Watchdog kill or disk < 2 GB:
stop that step. After RESULTS_M13, an independent re-review is requested via `review_v14c/BRIEF.md`; self-review does not count.
