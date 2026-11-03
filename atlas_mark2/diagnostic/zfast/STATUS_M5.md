# zfast STATUS after M5 (2026-10-19). STATUS.md and STATUS_M4.md are kept unedited.

**Headline.** [10²⁰, +2], [10²¹, +2] and [10²², +2], each with a certified close pair, are closed (A)+(B) with atlas_v5z3 and zfast
v13b (review2 fixes). Each has an independent replay, 0 tiling seams, 0 Lean violations, and a matching Turing cross-count. Details:
RESULTS_M5_FINAL.md; also RESULTS_M5_1e20.md and RESULTS_M5_1e21.md.

## Versions

| tree | zfast | used for | status |
|---|---|---|---|
| atlas_v5z | v10b | 10¹²–10¹⁸ (M4) | reviewed (review2: stands) |
| atlas_v5z2 | v12a | V2 re-runs; 10²⁰ (reviewed); 10²¹/10²² (made before review2's fixes request) | 10²¹/10²² superseded by v5z3 (identical) |
| **atlas_v5z3** | **v13b** | X5 (10¹⁶, 10²⁰ ×2 reproduced identically); **10²⁰ ×2, 10²¹ ×2, 10²² ×2** | **current claim** |

## New code this round (all new files)

- **Sources:** `src/v11`, `src/v12`, `src/v13`, `src/v13b` (v13 was never built; v13b corrects its m3 clause).
- **Build script:** `src/build_v6.sh`.
- **Theory:** THEORY_M5.md, THEORY_M5b.md; atlas_v5z2/THEORY_V5Z2.md, atlas_v5z3/THEORY_V5Z3.md.
- **Generators:** `tools/make_v5z2.py`, `tools/make_v5z3.py`.
- **Tools:**
  - `tools/scan_turing2.py` (scan + Turing count; v1 had an inexact integer conversion and is superseded);
  - `tools/pair_gap2.py` (v1 failed on Fraction → arb);
  - `tools/provenance.py`;
  - `tools/m5_validate_v11.py`, `tools/m5_validate_v12.py`;
  - `tools/m5c_validate2.py` (v1 could not parse NaN).
- **Predictions:**
  - PREDICTIONS_M5 f104fab0…;
  - PREDICTIONS_M5b d71d42c6…;
  - PREDICTIONS_M5c aa6dc3b7….
- **Novelty data:** `novelty/` (OpenAlex JSON; arXiv XML files are empty because of rate limiting).

## Rule log

- **No in-place edits:** every fix went into new files or directories.
- **Deletions:** none.
- **Junk files kept:**
  - two empty `pair_gap.json` (in `atlas_v5z2/runs/w1e20/{h,hp}_1e20/`, from `tee` with the v1 pair-gap tool);
  - the earlier `atlas_v5z/compare_z_.json` and `lean_audit/audit_v5z_.txt`.
- **Threads:** ≤ 2 total. While the Arb 10²¹ reference ran (1 thread), zfast used 1 thread.
- **Footprint:** ≤ 0.1 GB (zfast/v5z) and ≤ 4.6 MB (Arb `powsum_smooth`).
- **Disk:** zfast/ is 77 MB; 5.0 GB free.
- **Other directories:** `formal/` was used only to run the exporter and `atlas_audit`, with output written to my dirs. `review/` and
  `review2/` were read only.

## Next

1. **10²³** (about 6 h, ready: `atlas_v5z3/run_height.sh 23`). Optional Arb point at 10²³ (about 11 h).
2. **Review of v13b's diff from v12a.** The changes are small: asserts, indeterminate on `!ok`, the head extension, and print
   flags.
3. **A write-up for Phil.** Highest rigorous RH windows 10²⁰–10²², with the δ ≈ 0.042 certified pair at 10²⁰, together with the
   novelty caveats.
