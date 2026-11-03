# zfast M1 + M2 results (2026-10-19)

Scored against PREDICTIONS_M2.md (sha256 830221e2…, written before the measurements). The theory is in THEORY_ZFAST.md (M1 sha
6748271…). Raw data are in `runs/m2/`. The binaries and the exact sources of each build are in `bin/` (`SHA256.<ver>`,
`src_<ver>/`).
- Validation used dev4 (Z), dev7 (Z stress and variants) and dev8 (rows, high heights).
- The Z code path is identical in dev4–dev8. Later builds only added the row code, a ball-input branch in `zf_rs_corr` that exact
  inputs never reach, and printing.

Machine: M1 Mac mini, one core, `nice -n 19`. Three other users' heavy processes ran the whole time, so the times below are
pessimistic.

## 1. Correctness

| test | result |
|---|---|
| Q1 cos/sin kernel, 10⁷ random inputs plus 56 boundary inputs, against Arb | max error 1.75e-16 (cos), 1.73e-16 (sin); proved bound E_c = 4.88e-16. **MET** |
| Q2 phase (fixed-point forward differences), 19 blocks at 10¹⁰, 10¹⁶, 10²⁰, 10²², every k compared with Arb | 19/19 within the bound. Production blocks sit at the 2⁻⁶⁴ truncation floor (5.42e-20 against a bound of 5.42e-20). Control case J = 6, B = 300 at 10¹⁰: the interpolation error is visible, 3.55e-5, against a bound of 3.87e-5, so the bound is sharp and the code follows it. **MET** |
| Q3 Z against Arb, 208 points at 10¹⁰, 10¹¹, …, 10¹⁶ (u random binary64 in [0, 2) and [0, 1000)) | **208/208**: Arb's ball lies inside zfast's ball. Reference to 10¹⁵: v5's own `Zg` formula. At 10¹⁶: Arb `powsum_smooth` plus the Arb-copied correction (validated against `Zg` at 10¹³; stock Arb needs 1.3 GB there). **MET** |
| Q4 actual error | max \|zfast − Arb\| = 2.0e-15 at every height; median radius/error 4·10³ (10¹⁰) to 8·10⁴ (10¹⁶). **MET** |
| Q5 radius | 1.2e-12 (10¹⁰), 1.0e-11 (10¹³), 3.4e-11 (10¹⁵), 6.2e-11 (10¹⁶), 2.0e-10 (10¹⁸), 6.3e-10 (10²⁰). **MET** |
| Q6 stress: 28 points at N jumps (a = √(t/2π) within ~1e-15 of an integer) and at p = ±1/2, 0 (removable singularities of F); 6 large or zero offsets (T0 = 0, u = 10¹²; u = 10⁶); J ∈ {6, 8, 16, 24} × bmax ∈ {64, 2¹⁴, 2¹⁶} | 34/34 and 36/36 contained. **MET**. Finding: J = 24 with long blocks makes the 256-bit rounding-propagation term Σ C(B−1, i) 2⁻²⁵⁷ explode (radius up to 2e20). The actual error grows too (to 1e-11) and the bound still covers it. `choose_B` needs a cap on that term (to do; production J = 12 and B ≤ 2¹⁴ give 2⁻¹¹⁸). |
| Q7 sign replay: every certified sign-change interval of [10¹⁵, +2], [10¹⁵ + 286, +288] and [10¹⁶, +2] (94 intervals, 188 endpoints) | 94/94 decided with opposite signs. min \|Z\|/radius = 7.4·10⁴. Smallest \|Z\| = 4.6e-6. All 188 endpoints also lie inside Arb's balls. **MET** |
| Q11 rows: ζ, ζ′, P = Re(−ζ′/ζ) at σ = 1/2 + π/5.6 and 1/2 + π/3.2, 38 points at 10¹⁰–10¹⁵, against Arb's length-2 jet (v5's `mzl`) | **38/38** contained (all five quantities). Radius of P ≤ 4.2e-13 (a = 2.8) and 2.5e-15 (a = 1.6). Actual \|ΔP\| ≤ 3.1e-17. **MET** |
| high heights (not pre-registered as Arb checks) | 10¹⁸: Arb (`powsum_smooth`, 115 s) agrees, diff 2.8e-16 (J = 12) and 9.1e-16 (J = 16), radius 2e-10. 10²⁰: Arb (1245 s) agrees, diff 9.0e-16 and 6.0e-16, radius 6.3e-10 |

**Bugs found and fixed during M2.** All were harness or tool bugs. The kept outputs are marked superseded.
- The phase-test harness first reduced mod 1 through a double, which loses the integer part above 2⁵³. It reported false failures
  of 1–65536 turns. Superseded file: `phase_test.jsonl`. The fix reduces exactly with fmpz (`phase_test_dev4.jsonl`).
- `compare_rows.py` parsed balls at 53 bits and reported 19 false failures (`row_compare.json`). `compare_rows2.py` uses 200 bits
  (`row_compare2.json`).
- The row CLI printed only certain digits, so the actual-error statistic was unmeasurable. dev8 prints midpoints.
- `wd_run.sh` lost stdin, giving the empty `row_arb_15.jsonl`. `wd_run2.sh` fixes it.
- `build_v.sh` did not stop on compile errors (dev2 is a dead build). `build_v2.sh` and `build_v3.sh` do.

No bug was found in the zfast evaluator itself.

## 2. Speed and memory (one core)

| height | N | zfast Z | Arb Z (stock `Zg`; ¹ Arb `powsum_smooth`) | speed-up | zfast RSS | Arb RSS |
|---|---|---|---|---|---|---|
| 10¹⁰ | 4.0e4 | 0.013 s | 0.010 s | 0.7× | 4 MB | 28 MB |
| 10¹³ | 1.26e6 | 0.046 s | 0.33 s | 7× | 4 MB | 74 MB |
| 10¹⁴ | 4.0e6 | 0.089 s | 1.12 s | 13× | 4 MB | 165 MB |
| 10¹⁵ | 1.26e7 | 0.198 s | 3.9 s | 20× | 4 MB | 476 MB |
| 10¹⁶ | 4.0e7 | 0.53 s | 8.0 s (COST.md) / 11.1 s¹ | 15–21× | 4 MB | 1.30 GB / 4.5 MB¹ |
| 10¹⁸ | 4.0e8 | 4.9 s | 115 s¹ (stock, projected: ~120 s at ~4 GB) | 23× | 4 MB | 4 MB¹ |
| 10²⁰ | 4.0e9 | 47 s | 1245 s¹ | 26× | 4 MB | 4.4 MB¹ |

- The fast part runs at **12 ns/term** (J = 12); J = 16 gives 16.6 ns/term.
- Rows (ζ, ζ′ and P together) cost 1.5–1.6 Z-equivalents: 0.32 s at 10¹⁵ against Arb's jet at 18.8 s (58×), and 0.80 s at 10¹⁶
  against about 38 s.
- Q8: MET (all four time bounds and both speed-up bounds).
- Q9: MET (4.4 MB).
- Q10: the 10¹⁸ and 10²⁰ times (4.9 s, 47 s) are just *below* the predicted ranges (5–10 s, 1–2 min): faster than predicted.
- **Projection for 10²²:** about 470 s per Z (N = 4e10 at 12 ns), 4 MB.

**Side finding (changes COST.md §1, §4).** Arb's own `acb_dirichlet_powsum_smooth` (FLINT 3.6.0, public API) is memory-lean: 4 MB at
10¹⁶–10²⁰, only about 1.4× slower than the default sieved path. The "memory wall at 10¹⁷" is therefore a property of Arb's default
(`powsum_sieved` when it fits in 4 GB), not of Arb. A pure-Arb low-memory Z exists today, at about 115 s per Z at 10¹⁸.

## 3. Per-window projection (v5 claim, one core; zfast replacing every Arb Z and row jet)

Assumptions:
- v5 as run: about 1300 Z-equivalents per 2-unit window. Rows are cheaper than that (1.5 Z each, not 4.7).
- An optimised search: about 500 Z-equivalents (COST.md §2).

| height | v5 as run with Arb (measured or projected) | zfast, about 1300 Z-eq | zfast, about 500 Z-eq | zfast on 4 cores (500) |
|---|---|---|---|---|
| 10¹⁶ | 3.0 h measured | about 12 min | about 5 min | about 1.5 min |
| 10¹⁸ | about 37 h, memory-blocked | about 1.8 h | about 41 min | about 11 min |
| 10²⁰ | about 15 days | about 17 h | about 6.5 h | about 1.7 h |
| 10²² | about 150 days | about 7 days | about 2.7 days | about 16 h |

M3 (multi-evaluation) is what makes 10²⁰–10²² routine. Without it, zfast alone already brings 10¹⁷–10¹⁹ windows within reach on
this Mac.
