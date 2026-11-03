# zfast STATUS (2026-10-19, after M2; handed back)

**zfast:** a rigorous, O(1)-memory C evaluator of Hardy's Z(t), and of ζ and ζ′ at atlas_v5's row abscissae, at exact heights
T0 + u. The task brief is in the main session; Phil approved the performance program on 2026-10-19 (ATLAS_STATUS.md).

## Milestones

| | state | files |
|---|---|---|
| M1 theory | done | `THEORY_ZFAST.md` (sha in `THEORY_ZFAST.M1.sha256`); `tools/sincos_bound.py` (kernel constant E_c) |
| M2 implementation + validation | done; all 11 predictions met (two high-height point estimates were beaten) | `src/` (working copy), `bin/<prog>.<ver>` + `bin/src_<ver>/` (exact sources per build), `RESULTS_M2.md`, `PREDICTIONS_M2.md` (+ .sha256), `runs/m2/` |
| M2b rows (ζ, ζ′, −ζ′/ζ at σ = 1/2 + π/(2a)) | done and validated (38/38 against Arb's v5 jet) | `zf_row` in `src/zfast.c`, `bin/zfast_row_cli.dev8` |
| M3 multi-evaluation | not started | plan below |
| M4 v5 integration | not started | plan below |

**Current binaries:** `bin/zfast_cli.dev8` (Z) and `bin/zfast_row_cli.dev8` (rows). Defaults: J = 12, bmax = 2¹⁴, interpolation
target 2⁻⁷². Input lines are "T0 u" (or "T0 u a"); the output is JSON with the ball, the bound breakdown, timing and RSS.

## Design in one paragraph

Z = 2 Σ_{n≤N} n^{−1/2} cos 2π(Θ − τ log n) + 2 Re(e^{iθ} corr).
- **Arb (FLINT 3.6.0, trusted as v5 already trusts it)** provides: θ, τ = t/2π, the RS correction and the Arias de Reyna Thm 4.2
  remainder (a line-for-line copy of FLINT's `zeta_rs_r` correction loop), the first ~10⁴ "head" terms, and J + 1 = 13 phase
  nodes per block of up to 16384 terms.
- **Inside a block** the phase is advanced by exact 256-bit integer forward differences in Z/2²⁵⁶, so reduction mod 1 is free and
  exact. The error is the interpolation bound plus rounding propagation plus 2⁻⁶⁴ (Theorem 1). No floating-point log or range
  reduction is used anywhere.
- cos and sin use an own polynomial kernel with a proved bound E_c = 4.88e-16. Weights are IEEE 1/√n. Summation is in groups
  plus TwoSum.
- Every bound is accumulated in upward mag_t arithmetic.
- Rows share the same phase pass, with 8 accumulators and per-block weight polynomials whose remainders are bounded by Cauchy
  estimates. H′ comes from an analytic split H = R − Σ_{n≤N} n^{−s}, a central difference with step 2⁻⁴⁰ and a Cauchy remainder.

## Key numbers (details in RESULTS_M2.md)

- **Correctness:** 208/208 Z points at 10¹⁰–10¹⁶ inside Arb.
  - Plus 34 stress points, 36 J/bmax variants, 188 certified sign endpoints of the 10¹⁵/10¹⁶ record windows (94/94 sign changes
    reproduced), 38/38 rows, and Arb agreement at 10¹⁸ and 10²⁰.
  - Actual error ≤ 2e-15; radius 6e-11 at 10¹⁶ and 6e-10 at 10²⁰. The bound is about 10⁴ times the actual error.
- **Speed:** 12 ns/term. Z costs 0.20 s at 10¹⁵, 0.53 s at 10¹⁶, 4.9 s at 10¹⁸ and 47 s at 10²⁰, which is 15–26× stock Arb.
  Memory is **4 MB at every height** (Arb's default path: 1.3 GB at 10¹⁶).
- **Rows:** 1.5 Z-equivalents (58× Arb's jet at 10¹⁵).

## Prior art and framing (read before claiming anything)

- **FLINT's development branch** (commit "dfloat", F. Johansson, 2026-10-02) adds rigorous double/double-double/triple-double balls
  and `dfloat_powsum_sieved`, which are now inside `acb_dirichlet_zeta_rs_r`, plus a dfloat Platt multi-evaluation. This is the
  same idea class as zfast's M2 and M3. It is not in FLINT 3.6.0 (installed here); copies are in `ref/`.
  - Once released, stock Arb will likely be in zfast's speed class.
  - zfast's distinct points:
    - an independent implementation and error analysis, which is useful as an independent check of a trust-base change;
    - exact integer phases;
    - no sieve tables, so O(1) memory;
    - it works today on 3.6.0.
  - **Do not claim the method is new.**
- Arb's own `acb_dirichlet_powsum_smooth` is already low-memory (4 MB at 10²⁰, about 1.4× slower than its sieve). COST.md's
  "memory wall at 10¹⁷" holds only for Arb's default path. A pure-Arb Z costs about 115 s at 10¹⁸.
- [ADR-I] (the Thm 4.2 paper) was not obtained (AMS 403). The constants are cross-confirmed from [ADR-II] and the FLINT source;
  this is the same bound v5 already relies on through Arb.

## Rule incidents (honest log)

1. **Footprint cap breached once.** In the Q6 stress run, a grep that routed 10¹⁶ points to the low-memory reference missed the
   17-digit T0s. 7 points went to stock Arb at 10¹⁶: **peak RSS 1.39 GB for about 105 s**, against my 1 GB cap. The machine was
   unaffected and the results are valid. Afterwards I used an RSS watchdog (`tools/wd_run2.sh`, 950 MB) for every Arb run that
   could approach the cap.
2. **Source files edited in place.** `src/` was edited during development; these are my own files created this session. Every
   built binary has an exact snapshot of its sources in `bin/src_<ver>/`, except dev1, which was used only for the three
   pre-registration dev checks. From now on, new versions should go to new files.
3. In `src/`, an empty temp file (`zfast.h.tmp`) that I had created was removed by the same command, within the same second. No
   other file was deleted or overwritten. Superseded or buggy outputs are all kept and marked in RESULTS_M2.md §1.
4. `ref/ArdR2011_I.pdf` and `ref/ArdR2011_I_ams.pdf` are AMS 403 HTML pages, not the paper.

## Remaining plan

**M2 follow-ups (small, before M4):**
- (a) In `choose_B`, cap B so that the rounding-propagation term is ≤ 2⁻⁸⁰ for any J. This is the J = 24 finding.
- (b) Optional: make the per-block summation bound tighter (pairwise sums), about 10× smaller radius. Not needed for signs.
- (c) Threads: blocks are independent, so about 3.5× on 4 P-cores when the machine is free.
- (d) Independent review of THEORY §5–7 and §10. Lemma 1/Theorem 1 are short; the kernel bound script is self-contained.
- (e) Build zfast as a shared library and give it a Python ctypes wrapper for M4.

**M3 (multi-evaluation).** Odlyzko–Schönhage / Platt band-limited interpolation:
- Bucket the main sum by log n; take K moments per bucket in one pass (the fixed-point phases carry over); FFT over buckets to a
  t-grid; then rigorous band-limited interpolation (Platt 2017 constants, Arb's `platt_*` as template).
- The dfloat version in FLINT main is prior art to read first.
- Goal: about 10–20 Z-equivalents per window instead of about 500.
- Measure at 10¹⁶ and project to 10¹⁸–10²².
- Without M3, zfast single points already give (one core, about 500 Z-eq): 10¹⁸ in about 41 min per window and 10²⁰ in about
  6.5 h (RESULTS_M2 §3).

**M4 (integration).**
1. Copy frozen atlas_v5 to a new `atlas_v5z/`; frozen code is never touched.
2. Replace `Zg` (verifier) and the generator's Z search with zfast, and `mzl` (rows) with `zf_row`.
3. Write THEORY_V5Z (a trust-base change: zfast's §§5–8 and §10 join Arb).
4. Re-freeze.
5. Re-certify [10¹³, +2], [10¹⁴, +2], [10¹⁵, +2], [10¹⁵ + 286, +288] and [10¹⁶, +2]: the same closure (A/B), the same sign-change
   intervals or, when the search differs, the same count, plus the Lean audit.
6. Then the first windows at 10¹⁷ and 10¹⁸, pre-registered.

Coordination: the perf agent's "zpass" (`diagnostic/perf/zpass`, an Arb shared pass, predicted about 2.5× on rows) overlaps M4.
One Z/row provider should be chosen for v5z. zfast rows are about 58× faster than Arb jets at 10¹⁵.

## Disk

`diagnostic/zfast/` is 2.7 MB. No other directory was written.
