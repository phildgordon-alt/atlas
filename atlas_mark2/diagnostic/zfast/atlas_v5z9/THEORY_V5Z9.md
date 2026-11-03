# atlas_v5z9 = atlas_v5z8 on libzfast.v14c (checkpoint format v3; PREDICTIONS_M13, review_v14b)

**What changed.** Every file is a byte copy of atlas_v5z8 except `lib/zfast_provider.py`, `atlas_v5.py` and `replay_target5.py`
(counted replacements in `tools/make_v5z9.py`), plus `run_wide9.sh`. THEORY_V5Z6, THEORY_V5Z7 and THEORY_V5Z8 still apply.

**The engine.** libzfast.v14c's compute path is v14's (= v13b at equal D), byte for byte; only the checkpoint layer
(`zfast_sched14c.inc`) and its wiring changed, so an uninterrupted v5z9 window equals a v5z8/v5z7 window bit for bit
(PREDICTIONS_M13 I1, G1). The ctypes API (`zfa14b_new`, `zfa14b_info`, `zfa14b_last_error`) is unchanged.

**Checkpoint v3 (review_v14b).**
- **MJ1.** Every item line is sealed as HMAC(K, "ZF14C-ITEM\0" || SHA-256(header body) || u64be(item index) || line body), and every
  new header carries a fresh random `hnonce`. A line therefore authenticates only in the file (header) and at the index it was written
  for: a line from another session, run, recreated file or position is ignored (never loaded) even under the same key. A second
  authenticated line for a loaded item refuses the session (identical or conflicting duplicate). A new header under an existing key
  is allowed (crash recovery), reported (`key_reused_new_header`) and cannot be spliced.
- **mn1.** The arb parser builds each ball from its tokens with exact FLINT setters (no `arb_load_str`, which aborts the process on
  some malformed inputs) and accepts only canonical values: malformed authenticated input refuses with a reason.
- **mn2.** A flusher thread F_FULLFSYNCs every 1.0 s while lines are unsynced: a line is durable within 1 s + one F_FULLFSYNC of its
  write (measured: `max_unsynced_s`).
- **mn3.** The header pins the dyld shared-cache UUID, hw.model, LC_UUIDs of all loaded images and the in-memory `__TEXT` hash of
  libzfast; an unavailable field refuses (no placeholders). Consequence: a resume after ANY OS update (including a background security
  update that changes the shared cache) or on another Mac is refused; keep automatic OS updates off during a multi-day run.
- **mn4.** Keys are created atomically (temp, F_FULLFSYNC, renamex_np(RENAME_EXCL), directory fsync); an existing key must be a
  regular, non-symlink, user-owned, 0600-or-stricter, 32-byte file. A 0-byte key (from a pre-v14c crash) refuses.
- **mn5/mn6.** Worker write errors reach `zfa14b_last_error`; overlong lines are skipped without being stored.
- **mn7 (this tree).** The generator session recomputes 64 random loaded items on every resume (replay: 8). For k forged-but-authentic
  items among N loaded the detection probability per resume is 1 - C(N-k, 64)/C(N, 64) (= 64/N for k = 1). The key holder is
  trusted, as before.

Do not delete `ckpt_keys/`. Keys are not certificate inputs; losing them costs only recomputation.
