# M5 results, part 2: 10²¹ (2026-10-19)

**Status.** Contingent on the independent review (`zfast/review2/`).
- Code: exactly as for 10²⁰ (RESULTS_M5_1e20.md §0): atlas_v5z2, libzfast.v12a. Per-run record in `provenance.json`.
- Runs: 2 zfast threads, nice 19.

| window | result | sign changes (v5z2) | Turing count (separate method) | min margin | pipeline + independent replay | Lean audit |
|---|---|---|---|---|---|---|
| **[10²¹, 10²¹ + 2]** | **CLOSED (A) and (B)** | 15 | **15**: N(10²¹) = 7244161625227817018173, N(10²¹ + 2) = …188, pinned (U − L = 0.46, 0.43) | 0.769; S-layer 15/15 | 644 s + 319 s | 17 certificates, 0 violations |
| **[10²¹ − 6, 10²¹ − 4]** (closest pair of the scan) | **CLOSED (A) and (B)** | 15 | **15**: N(10²¹ − 6) = …129, N(10²¹ − 4) = …144, pinned | 0.794; S-layer 15/15 | about 644 s + 319 s | 17 certificates, 0 violations |

**Scan.** [10²¹ − 60, 10²¹ + 62]: 903 zeros located, 0 undecided grid points, 0 dips. Session 317 s plus grid 74 s (2 threads).

**Certified closest pair.**
- γ₁ ∈ 10²¹ − [5.137109375, 5.13703125] and γ₂ ∈ 10²¹ − [5.115390625, 5.1153125];
- gap ∈ [0.021641, 0.021797], **δ ∈ [0.1602, 0.1614]**;
- both zeros on the line and simple.
- This scan was less lucky than 10²⁰'s: P predicted δ_min ∈ [0.07, 0.25]; 10²⁰ gave 0.042 (below the range), 10²¹ gives 0.160.
- The main window's closest pair has δ ∈ [0.563, 0.565].

**Zeros of [10²¹, +2]** (midpoints, widths ≤ 7.8e-5): 0.07012, 0.17137, 0.28301, 0.40004, 0.64090, 0.75066, 0.82684, 1.03535, 1.14285,
1.24988, 1.36160, 1.47246, 1.64488, 1.77160, 1.92168.

**Precision at 10²¹.**
- V4 (RESULTS_M5_1e20 §1): Arb `powsum_smooth` at 10²¹ + 0.40625 agrees with zfast to 1.4e-15 and is contained.
- No triple-double was needed (THEORY_M5 §2).
