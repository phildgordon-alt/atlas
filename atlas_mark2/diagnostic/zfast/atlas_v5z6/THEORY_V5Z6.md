# atlas_v5z6 = atlas_v5z5 on libzfast.v14, two sessions per wide window (2026-11-01; OPTIMIZE_M9 / RESULTS_M9)

**Why.** At 10²⁵ a v5z5 window costs 4 O(√T) session passes (generator, inline replay, independent replay, Turing scan), ≈ 22 h at 4
threads (RESULTS_M8 §5). v5z6 needs 2, and each pass is faster (libzfast.v14).

**What changed. No inequality, model, verifier, LP, row, replay or tiling code changed** (byte copies; V5Z6_FREEZE.sha256).
- `lib/zfast_provider.py`: libzfast.v14 (sha-pinned). Its sessions are **bit-identical** to libzfast.v13b's at equal decomposition
  D (= ZFAST_THREADS = pieces.json `zfast_session.threads`): same work items (bucket ranges from v13b's split_ranges), same per-item
  arithmetic (a kernel performing the same IEEE operations in the same order; exact integer phase updates), same per-bucket merge
  order. Only who computes an item and when changes (ZFAST_WORKERS threads, longest item first, no per-bucket barrier). Optional
  checkpoint (ZFAST_CKPT, strict mode only): every finished item is stored exactly (arb_dump_str, raw mag fields, SHA-256 per line;
  header = every parameter defining the items); resume loads matching valid lines, merges unchanged, so a resumed session equals an
  uninterrupted one. `turing_grid()` saves scan_turing5's grid format from the process's session (diagnostic only).
- `atlas_v5.py`: `--turing-grid`, `--resume`; the replay's D comes from pieces.json (child env); role-specific checkpoints; one replay
  (the driver's stage 3, a fresh process running the byte-copied replay_target5.py — the same program and isolation as v5z5's
  "independent replay", which v5z5 ran a second time).
- `lib/gen_target5.py`: after `gen_done`, the Turing grid stage (untrusted generator; writes no certificate).
- `run_wide6.sh`: pipeline → `scan_turing5.py recount` (the unchanged tool of record) → `turing_gate check` (required, A6).

**Soundness.** Unchanged from v5z5 (THEORY_V5Z5): every Z value and row is a ball from a session whose validity range contains the point;
THEORY_M5b Lemma M1c holds for every H, Δ (production H = 91, Δ = 0.008: |h′|X_b ≤ 0.364, as scan4_1e22). The certificates never
contain or depend on the Turing count, which is a separate-method diagnostic made a required gate (A6).

**Review flags.** (1) v14's kernel and scheduler are new trusted code; bit-identity is confirmed mechanically (RESULTS_M9) but the code
needs review2-style review. (2) The checkpoint load path is a new input path into a session (protected by header equality and per-line
SHA-256; a resumed replay of record should be disclosed as such).

**Regression.** v5z6 with wide_1e22's frozen session parameters must regenerate it identically (certs, certs_np, zs.json,
gen_measurements.json, replay records): engine/regress_v1/v5z6_gate.py, PREDICTIONS_M9.
