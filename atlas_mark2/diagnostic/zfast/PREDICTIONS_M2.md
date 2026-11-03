# zfast M1/M2 predictions (written 2026-10-19, before the M2 measurements; sha256 in PREDICTIONS_M2.sha256)

Before writing this, development used three checks only: one point each at 10^10, 10^13 and 10^15 (two against Arb). The
observations were:
- the differences were 5e-17 and 4e-16;
- the radii were 1.2e-12, 1.0e-11 and 3.4e-11;
- the fast part ran at 25 ns/term at 10^13 and 14 ns/term at 10^15;
- the full evaluation took 0.05 s at 10^13 and 0.20 s at 10^15;
- RSS was 4 MB.

The binary measured is `bin/zfast_cli.dev1` (sha in `bin/zfast_cli.dev1.sha256`), or a later version recorded in STATUS.md, with
J = 12, bmax = 2^14 and interpolation target 2^-72.

| # | prediction | pass criterion |
|---|---|---|
| Q1 | Kernel test: max observed cos/sin error ≤ E_c = 4.88e-16; observed max ≈ 1–2.5e-16 | any excess = FAIL (bug in bound or code) |
| Q2 | Phase test: observed error ≤ E_ph in every block tested (10^10, 10^16, 10^20, 10^22); observed ≤ 2^-64 + tiny (truncation dominates) | any excess = FAIL |
| Q3 | Z vs Arb, ≥ 200 points at 10^10–10^16: 100 % containment (Arb mid in zfast ball; balls intersect) | any miss = FAIL |
| Q4 | Actual \|zfast mid − Arb mid\| ≤ 1e-13 at every point; bound/actual ratio ≥ 100 (median) | point predictions |
| Q5 | Radius: ≤ 2e-12 at 10^10, ≤ 2e-11 at 10^13, ≤ 2e-10 at 10^16 (∝ √N) | point predictions |
| Q6 | Stress (N jumps, tiny Z, J/bmax variants): 100 % containment; every J/bmax variant gives overlapping balls | any miss = FAIL |
| Q7 | Sign replay: every certified endpoint at 10^15, 10^15+286 and 10^16 is sign-decided by zfast, with the certified sign | any disagreement = FAIL; undecided = FAIL of usefulness |
| Q8 | Time per Z (one core, nice 19, others running): 10^13 ≤ 0.1 s, 10^14 ≤ 0.2 s, 10^15 ≤ 0.4 s, 10^16 ≤ 1.2 s | speed-up vs Arb ≥ 5× at 10^13 and ≥ 10× at 10^15–10^16 |
| Q9 | Memory: max RSS ≤ 20 MB at every height through 10^18 (vs Arb 0.07 / 0.17 / 0.48 / 1.30 GB at 10^13–10^16) | > 50 MB = miss |
| Q10 | Projection from ns/term: 10^18 ≈ 5–10 s per Z, 10^20 ≈ 1–2 min, 10^22 ≈ 10–20 min (single point, one core) | checked at 10^18 by one actual run |
| Q11 | Rows (if M2b is completed in this round): enclosures of Re(−ζ′/ζ)(σ+ix), σ = 1/2 + π/5.6 and 1/2 + π/3.2, overlap Arb's mzl at 10^10–10^15, radius ≤ 1e-8, cost ≤ 3 Z-equivalents | any non-overlap = FAIL |
