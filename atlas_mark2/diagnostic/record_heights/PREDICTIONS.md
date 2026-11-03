# record_heights — pre-registered predictions (2026-10-18, written before any Atlas run at 10^15 or 10^16)

Pipeline: the frozen atlas_v5 code, copied byte-for-byte into `v5run/` (`shasum -a 256 -c V5_FREEZE.sha256`: 21/21 OK, verifier sha
b0184504… OK). Copying was needed only because the driver writes to `runs/` next to itself; `atlas_v5/` is not touched. No code change.
Parameters exactly as pre-registered in `atlas_v5/PREDICTIONS.md` (sha b4ae8036…) for these two heights: grid v5, evaluator dirichlet,
PW = 1, WM = 2, refinement 1e-4, Z step 0.01 at 10^15 and 0.02 at 10^16, generator timeout 21600 s, 2.5 GB footprint/RSS watchdog on
every child, `nice -n 19`, one heavy process at a time. Run order 10^15, then 10^16 only if 10^15 closed.

Claim definition (identical to v5): every zero of ζ with ordinate in [T, T + 2] lies on the critical line and is simple — claim (A) via
Lemma 2, claim (B) without Lemma 2 (S-layer). No zero list, no Turing count is used by the certificate. Arb's Turing count is a diagnostic.

## Seen before writing this (disclosure)

- Arb Turing counts (atlas_v5/nzeros, 2026-10-08): 10 zeros in (10^15, 10^15 + 2], 10 in (10^16, 10^16 + 2].
- Cost probes (`cost/probe.log`, single point u = 0.505): rigorous Z (pinned Zg) 0.25 / 0.76 / 2.42 / 8.0 s at 10^13 / 10^14 / 10^15 /
  10^16; one row jet 1.2 / 3.7 / 11.5 / 37.6 s. **Arb RSS for one Z: 0.17 / 0.48 / 1.30 GB at 10^14 / 10^15 / 10^16** (≈ √T growth).

## Predictions

| | point prediction | bound (MET if inside) |
|---|---|---|
| P1 sign changes in target = Arb count | 10 and 10 | equal |
| P2 10^15 closes (A) | yes, tier t1 | closed, independent replay passes |
| P3 10^16 closes (A) | yes (70 %); main risk: a pair < 0.02 apart missed by the coarse step | reported as is, never re-tuned |
| P4 claim (B) | holds wherever (A) holds | holds |
| P5 min_candidate_lower | ≈ 0.88 (10^15), ≈ 0.86 (10^16) | > 0 |
| P6 wall (pipeline + replay) | 10^15 ≈ 45 min; 10^16 ≈ 1.8 h | 10^15 ≤ 2 h; 10^16 ≤ 5 h |
| P7 peak memory | 10^15 ≈ 0.5 GB; 10^16 ≈ 1.4 GB | < 2.5 GB (watchdog). Note: v5's Q8 bound "≤ 1 GB" is expected to FAIL at 10^16 (Arb RS memory) |
| P8 independent replay (fresh process, second invocation) | passes | passes |

**Closest pair.** The closest certified pair of consecutive zeros in each window is reported with its normalised gap
δ = Δγ · log(γ/2π)/(2π). Prediction: min δ in a 10-zero window ≈ 0.3–0.5 (no Lehmer-type pair, δ < 0.1, expected; probability ~5 %).

**Failure handling.** As v5: NOT CLOSED is reported with open pieces; no code change to force closure.
