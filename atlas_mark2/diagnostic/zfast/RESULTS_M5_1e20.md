# M5 results, part 1: validation of the M5 code and the 10²⁰ certificates (2026-10-19)

**Status.** Contingent on the independent review (`zfast/review/`, now `zfast/review2/`). Pre-registration: PREDICTIONS_M5.md (sha
f104fab0…) and PREDICTIONS_M5b.md (sha d71d42c6…), both written before the measurements.

## 0. Exact code that produced the 10²⁰ certificates (for review2)

| item | path | sha256 |
|---|---|---|
| frozen tree | `zfast/atlas_v5z2/` (V5Z2_FREEZE.sha256, 30 files) | — |
| trusted verifier and rows | `atlas_v5z2/lib/verify_zs5.py` (identical to atlas_v5z), `lib/sech5.py`, `lib/zfast_provider.py` | provider ca405c1c… |
| zfast library | `zfast/bin/libzfast.v12a.dylib` | 70e1c317… |
| zfast sources | `zfast/bin/src_v12a/` (`zfast.c` includes `zfast_m3b.inc` and `zfast_m3c.inc`; `zfast_api3.c`, `zfast_api4.c`) | `bin/SHA256.v12a` |
| theory | THEORY_ZFAST.md, THEORY_M3.md, THEORY_M5.md (§1, §2), THEORY_M5b.md (rows by complex shift), atlas_v5z/THEORY_V5Z.md, atlas_v5z2/THEORY_V5Z2.md | `*.sha256` |
| per-run record | `atlas_v5z2/runs/w100000000000000000000/{h,hp}_1e20/provenance.json` | — |
| Turing count / scan (separate method) | `zfast/tools/scan_turing2.py` (uses libzfast.v12a) | in provenance.json |

**What review2 must check.** The code path used by these certificates is:
- **Z:** M3 sessions (kind 0; `zfm_new`, `zfm_Z`) with zfast_m3b's moment pass;
- **rows:** `zfm_row3`/`zfm_sum_c` (complex shift, THEORY_M5b);
- **RS correction:** `zf_rs_corr`;
- `Hjet`/`Hfun`.

The kind-2 combined path (v11) is not used by any certificate.

## 1. Validation of the M5 code (V1–V4)

| # | result | verdict |
|---|---|---|
| V1 v11 combined sessions | 240/240 overlap; build cost 2.4–3.6 × a Z session (predicted ≤ 1.6) | overlap MET; cost **MISSED** → replaced by v12 |
| V1b v12 rows from the Z moments (complex shift) | 60/60 against single-point v9 rows; 38/38 inside the stored Arb jets (10¹⁰–10¹⁵); P radius 0.86 × the v10b row-session radius | **MET** |
| V1c v12 Z values | bit-identical to v11 at equal K (20/20); K = 18 against K = 16 overlap 20/20. The first comparison mixed K = 18 with K = 16, so it was not "identical" (13–18/20); the prediction was mis-specified, not a failure | **MET** at equal K |
| V1d cost | v12 session = Z-only session; row point ≤ 8 ms | **MET** |
| V2 v5z2 acceptance | the six original windows (10¹²–10¹⁶, 10¹⁵ + 286) re-certified with **identical** intervals (margins Δ ≤ 2e-14); v5z's 10¹⁷/10¹⁸ reproduced with identical intervals and identical margins | **MET** |
| V3 Turing count (separate method) at 10¹⁶ | N(10¹⁶) = 54118226280292478 and N(10¹⁶ + 2) = 54118226280292488 pinned (U − L ≈ 0.40), equal to Arb's counts | **MET** (after a harness fix: the first run, `runs/m5/scan_1e16`, converted through double and printed wrong last digits; superseded by `scan2_1e16`) |
| V4 Arb at 10²¹ (`powsum_smooth`, 4525 s, 4.4 MB) | zfast single point (70 s): diff 1.4e-15, radius 1.1e-9, contained; v12 session: diff 1.0e-15, radius 2.2e-9, contained | **MET**. Precision at 10²¹ is confirmed without triple-double (THEORY_M5 §2) |

## 2. [10²⁰, 10²⁰ + 2] and a close pair at 10²⁰ + 4.72

Both runs: v5z2, zs-step 0.005, 1 zfast thread (an Arb reference job ran in parallel), nice 19.

| window | result | sign changes (v5z2) | Turing count (separate method) | min margin | pipeline + independent replay | Lean audit |
|---|---|---|---|---|---|---|
| **[10²⁰, 10²⁰ + 2]** | **CLOSED (A) and (B)** | 13 | **13**: N(10²⁰) = 687769382578810314775, N(10²⁰ + 2) = …788, both pinned (U − L = 0.44, 0.47) | 0.794; S-layer 13/13 | 537 s + 265 s | 15 certificates, 0 violations |
| **[10²⁰ + 4, 10²⁰ + 6]** (closest pair) | **CLOSED (A) and (B)** | 14 | **14**: N(10²⁰ + 4) = …803, N(10²⁰ + 6) = …817, pinned | 0.773; S-layer 14/14 | 535 s + 266 s | 16 certificates, 0 violations |

**The close pair.**
- The scan covered [10²⁰ − 60, 10²⁰ + 62], 860 zeros located, 0 undecided grid points. The closest pair in [−20, 22] lies at offset
  4.72 (scan δ ≈ 0.056).
- **Certified:**
  - γ₁ ∈ 10²⁰ + [4.719375, 4.719453125];
  - γ₂ ∈ 10²⁰ + [4.725390625, 4.72546875];
  - both on the critical line and simple (claims A and B);
  - gap ∈ [0.0059375, 0.0060938], i.e. **normalized gap δ ∈ [0.0418, 0.0429]**: about 1/24 of the mean spacing (0.142).
- Exact rationals are in `hp_1e20/pair_gap2.json`.
- For comparison: the 10¹⁵ pair had δ ≈ 0.098, and the main 10²⁰ window's closest pair has δ ∈ [0.103, 0.104].

**Zeros of [10²⁰, +2]** (midpoints; widths ≤ 7.8e-5): 0.08160, 0.12223, 0.38902, 0.51590, 0.75215, 0.80043, 0.97848, 1.03059,
1.19613, 1.42957, 1.60910, 1.94434, 1.95910.

**Costs** (1 thread):
- scan session (H = 61) 279 s, plus the grid of 30 501 points in 104 s;
- window pipeline about 9 min;
- independent replay about 4.4 min.
- Prediction T was ≈ 8 min per window: MET.
- Footprint ≤ 0.1 GB per replay.

## 3. Novelty re-check (2026-10-19; `zfast/novelty/`)

**Sources.**
- arXiv API: empty responses (rate-limited, as on 2026-10-18).
- OpenAlex works searches (4 + 4 queries, from 2018), citing-works of Platt–Trudgian 2021 and of Bober–Hiary 2018, author/title
  checks.
- GitHub FLINT releases.

**Findings:**
- **Platt–Trudgian 2021** (Bull. LMS): RH to 3·10¹². Still the rigorous initial-segment record. OpenAlex lists no later rigorous
  extension (citation coverage is thin).
- **Hiary–Ireland–Kyi** is now published: "A method for verifying the generalized Riemann hypothesis", Math. Comp. (2026),
  doi 10.1090/mcom/4129 (the arXiv 2408.00187 work, with the 10²⁸ window conditional on floating-point zero intervals; see
  record_heights/PRIOR_ART.md). Their abstract describes Riemann-style verification generalized to L-functions; the conditional
  nature of the 10²⁸ window is as recorded earlier.
- **Bober–Hiary 2018** (Exp. Math.): non-rigorous to 8·10³⁴, "we cannot prove this" for the truncation error, as previously quoted.
- **Gourdon 2004:** non-rigorous, unrefereed (unchanged).
- **Platt 2017** (Math. Comp. 86): rigorous to 3.06·10¹⁰ (unchanged).
- **FLINT dfloat** (rigorous low-precision balls; RS main sum and Platt multi-evaluation): only on the development branch (commit
  "dfloat", 2026-10-02). No FLINT release contains it; the latest is v3.6.0, 2026-06-29. Once released, Arb's Turing-method
  windows at 10²⁰+ become cheap for anyone.
- **2026 Zenodo deposits** found (e.g. zenodo 23447265, 22183395) are non-rigorous mpmath computations just above 3·10¹².

**Verdict (to our knowledge, as of 2026-10-19, with the usual caveats).**
- No published or publicly documented rigorous, unconditional verification of RH in any window above 3·10¹² other than Atlas's own.
- Atlas's 10²⁰ windows (and 10¹⁷, 10¹⁸) are the highest such windows.

**Caveats that must accompany any statement:**
- Arb's Turing-method routines (and FLINT-dev's dfloat versions) can certify such windows given enough memory and time. This is not
  a new fact about ζ.
- Odlyzko, Gourdon and Bober–Hiary computed far higher, non-rigorously.
- HIK's 10²⁸ window is conditional.
- zfast is in the trust base and is under independent review.
- The method class is not new (FLINT dfloat; Platt).
- The search was limited (arXiv API unavailable).
