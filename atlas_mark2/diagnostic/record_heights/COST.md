# Cost of rigorous Z(t) and of one certified window: measured, fitted, projected (record_heights, 2026-10-18)

Machine: Apple M1 Mac mini, 8 GB. python-flint 0.9.0, which bundles FLINT 3.6.0 (Arb). Every run used `nice -n 19` under a
footprint watchdog. During the 10¹⁶ run a second user's process (`cert_FE.py`, about 1 core) ran at the same time, so the 10¹⁶ times
are 10–30 % pessimistic. Raw data:
- `cost/probe.log`;
- `v5run/pilot.log`;
- the run summaries `v5run/runs/w*/big_1e*/summary.json`;
- the projection script `cost/project.py`;
- the C kernel benchmark `cost/c_bench/`;
- the Arb Platt probe `cost/platt_probe.log`.

## 1. One rigorous Z(T + u): the pinned verifier's `Zg`

`Zg` is Arb ζ(1/2 + it) times the Γ-phase, at the exact height, with precision 160 + bitlen(T) bits. Arb picks Riemann–Siegel and
takes its error bound from Arias de Reyna's Thm 4.2. The row jet is the length-2 ζ series at 1/2 + π/5.6 + it, at 128 + bitlen bits.

| T | Z (s) | row jet (s) | RSS of one Z |
|---|---|---|---|
| 10¹³ | 0.25 | 1.19 | 0.07 GB |
| 10¹⁴ | 0.76 | 3.67 | 0.17 GB |
| 10¹⁵ | 2.42 (2.75 inside the run) | 11.5 | 0.48 GB |
| 10¹⁶ | 8.0 (10.4 inside the run, under contention) | 37.6 | **1.30 GB** |

Fits:
- Z ∝ T^0.502 and jet ∝ T^0.499, i.e. √T exactly (the RS main sum has N = √(T/2π) terms);
- jet/Z ≈ 4.7;
- **memory ∝ T^0.42–0.45**, from Arb's sieved power sum. Extrapolated to 10¹⁷ that is about 3.5 GB, over this machine's 2.5 GB cap.

Johansson's 2016 post (PRIOR_ART §3) says Arb caps itself at 4 GB and then switches to partial sieving, which is about ×1.5–2
slower. That cap does not help on this machine. The 2016 times were 18.5 / 58 / 279 / 896 / 2884 s at 10¹⁶ … 10²⁰. This Mac is
about 2.3× faster at 10¹⁶. **Arb single-point cost on this Mac: about 25 s at 10¹⁷, 120 s at 10¹⁸, 1250 s at 10²⁰ and 3.5 h at
10²², at about 4 GB.**

## 2. One certified window [T, T + 2] with the frozen v5 pipeline (same claim, same checks)

| T | generator: Z search (evals, s) | rows (18 jets) | in-pipeline replay | **pipeline wall** | independent replay | peak footprint |
|---|---|---|---|---|---|---|
| 10¹³ (v5, 2026-10-08) | 1363, 283 s (step 0.005) | 20 s | 39 s | 344 s | 39 s | 0.24 GB |
| 10¹⁴ (v5) | 1375, 890 s (0.005) | 58 s | 127 s | 1078 s | 127 s | 0.31 GB |
| **10¹⁵ (this run)** | 811, 2233 s (0.01) | 248 s | 659 s | **3143 s** | 577 s | 0.66 GB (replay 0.54 GB) |
| **10¹⁶ (this run)** | 565, 5859 s (0.02) | 915 s | 2097 s | **8874 s** | 2057 s | 1.51 GB (replay 1.46 GB) |

- The pipeline wall time grows by ×3.1, ×2.9 and ×2.8 per decade, close to √10. **W(T) ≈ 8900 s · (T/10¹⁶)^½** with the
  pre-registered grid steps, plus about 25 % for the independent replay.
- In the generator, the Z search is 66–90 % of the time, and the bisection to width 1e-4 is about 2/3 of the Z evaluations.
  Replay is about 135 Z evaluations at interval endpoints plus 18 jets.
- **Minimum count per window** with today's verifier and claim:
  - (a) about 200 Z for the search, using Gram-point bracketing plus Illinois refinement to 1e-4 (not implemented);
  - (b) about 135 Z for replay endpoints;
  - (c) 36 jets, i.e. 18 rows, generated and replayed.

  That is **about 500 Z-equivalents**, against about 1300 Z-equivalents as run. At 10¹⁶, optimising the search alone would cut the
  wall time to about 1.4 h.

## 3. Projection per 2-unit window (one P-core unless stated)

Zeros per unit: log(T/2π)/2π = 5.6 at 10¹⁶, 7.0 at 10²⁰, 7.8 at 10²². "Z-eq" means Z-equivalents per window.

| route | 10¹⁶ | 10¹⁸ | 10²⁰ | 10²² | memory |
|---|---|---|---|---|---|
| (a) Arb as is, v5 as run (about 1300 Z-eq) | **3.0 h measured (2.5 h pipeline + 0.6 h independent replay)** | about 37 h | about 15 days | about 150 days | 1.5 GB at 10¹⁶; **≥ 4 GB from about 10¹⁷: blocked by the 2.5 GB cap** |
| (a′) Arb with an optimised search (about 500 Z-eq) | 1.4 h | about 14 h | about 6 days | about 60 days | same block |
| (b) C Riemann–Siegel, double-double, rigorous error accumulation (about 500 Z-eq) | about 0.3 h | about 3–4 h | about 35 h (about 10 h on 4 P-cores) | about 30 days (needs triple-double; about 8 days on 4 cores) | about 10 MB |
| (b′) (b) plus a multi-evaluation per window (Odlyzko–Schönhage / Platt band-limited grid; the whole window from one √T pass, about 10–20 Z-eq) | minutes | about 10–20 min | about 1–2 h | about 15–30 h (about 5–8 h on 4 cores) | about 0.1–0.5 GB (FFT grid) |
| (c) Hiary t^{1/3}, rigorous | — | — | not competitive with (b′) below about 10²³ | crossover about 10²³–10²⁴ | small |

Basis for (b):
- The C kernel benchmark (`cost/c_bench/rs_kernel_bench.c`: double-double phase t·log n mod 2π, then sincos and the n^{−1/2}
  weight) runs at **31.5 ns/term** on one core.
- A proper double-double log plus the bookkeeping for proved rounding bounds adds an estimated ×1.5–2, giving **50–60 ns/term**.
  Arb is at about 200 ns/term (8 s for 4·10⁷ terms at 10¹⁶).
- At 10²², t·log n ≈ 2⁷⁷, so double-double's 106 bits leave about 2⁻²⁹ of phase error per term. Summed over 4·10¹⁰ terms that is
  too much for sign certificates near zeros, so 10²² needs triple-double or 192-bit fixed-point phases (×2–3).
- (b′) assumes one band-limited pass costs about 10–20 single-point sums. This is the standard Odlyzko–Schönhage/Platt trade-off,
  not measured here. §4 measures Arb's own rigorous Platt implementation.

## 4. Arb's rigorous Platt route (the Turing-method comparator), measured

`acb_dirichlet_platt_local_hardy_z_zeros` via ctypes (`cost/arb_platt_probe.py`, logs in `cost/platt_probe.log` and
`cost/platt_scan_1e15.log`). It isolates `len` consecutive zeros from zero n onwards, using Platt's multi-evaluation and Turing's
method. At n = 10¹⁰ it was validated against `acb.zeta_zero`.

| start | len | span covered | wall | peak footprint |
|---|---|---|---|---|
| n = 10¹⁰ | 3 | — | 41 s | 0.46 GB |
| first zero above 10¹⁵ | 50 | 9.4 units | 104 s | 0.37 GB |
| zero 50 above 10¹⁵ | **1500** | **288 units** | **112 s** | 0.37 GB |
| first zero above 10¹⁶ | 50 | 8.9 units | 221 s | 0.35 GB |
| zero n = 10¹⁸ (t ≈ 1.5·10¹⁷) | 50 | — | **killed at 2.5 GB footprint after 1565 s** | > 2.5 GB |

- The first zeros agree with Atlas: 10¹⁵ + 0.09205 (Atlas's interval midpoint 0.09207) and 10¹⁶ + 0.03184 (Atlas 0.03184).
- **Per unit height, Arb's Turing route is about 4000× cheaper than Atlas at 10¹⁵**: 288 units in 112 s against 2 units in
  62 min. The cost is a fixed multi-evaluation block, roughly ×2 per decade.
- It is also **memory-blocked on this Mac at about 10¹⁷**, like Arb's single-point RS. So with stock Arb and a 2.5 GB cap,
  **nothing rigorous runs above about 10¹⁷ on this machine.** Platt's method (Arb docs: n ≤ 10²³) needs a bigger machine or a
  memory-lean implementation.
- (b′) would re-implement this multi-evaluation inside Atlas's verifier, with streamed memory.

## 5. Effort estimates

- **(a) Arb as is.** No work. Usable to 10¹⁶ on this Mac (done). 10¹⁷ is out under the 2.5 GB cap: Arb is about 3.5 GB there.
  Rebuilding FLINT with a lower partial-sieving memory cap would need about 300 MB of disk for source plus build, at the edge of the
  budget. It would buy at most 10¹⁷–10¹⁸ at days per window.
- **(b) C RS with proved remainder.** About 2–4 weeks for one careful implementer, plus an independent review.
  - Remainder: Gabcke's R₁ bound on the critical line suffices for Z (|R₁| < 0.053 t^{−5/4}). The rows at σ = 1.06–1.48 need
    Arias de Reyna's general-σ bound, and the derivative needs a Cauchy-circle bound.
  - Arithmetic: double-double, or triple-double above about 10²¹, with a running rigorous rounding bound (the Joldes–Muller–Popescu
    error bounds for DD operations) and the phase reduced from the exact height T0 + u.
  - Validation: enclosures must overlap Arb's at 10¹⁰–10¹⁶.
  - Integration: a new Z provider for verify_zs5, which means a trust-base change, a re-freeze, re-running the v4/v5 acceptance
    comparison and a new theory note.
- **(b′) Multi-evaluation.** A further 2–4 weeks. The rigorous interpolation error bound is the delicate part. Platt's 2017
  constants and Arb's `platt_*` code (MIT/LGPL) are templates. Alternatively, call Arb's `acb_dirichlet_platt_multieval` on a grid
  covering the window and add a rigorous interpolation lemma to the verifier.
- **(c) Rigorous Hiary t^{1/3}.** Research-level: months. Hiary's constants are effective but not explicit, and Bober–Hiary's
  implementation is floating-point with unproved working bounds. It is only worth it for 10²⁴–10²⁸, i.e. Gourdon's 10²⁴ or HIK's
  10²⁸ windows made unconditional.

**Memory per approach:**
- (a) Arb: about 0.5 GB at 10¹⁵, 1.3–1.5 GB at 10¹⁶, then its own 4 GB cap;
- (b): O(1), a few MB per thread;
- (b′): one FFT grid, 0.1–0.5 GB;
- (c): small.
