# record_heights: RH certified in windows at 10¹⁵ and 10¹⁶, costs, and the ladder (2026-10-18)

Pre-registration:
- `PREDICTIONS.md` (sha256 35bc2600…);
- `PREDICTIONS_PAIR.md` (sha256 71eca040…), written after the two main windows and before the pair run.

The code is the frozen atlas_v5, copied byte-for-byte to `v5run/` (V5_FREEZE 21/21 OK, verifier sha b0184504… OK). No code was
changed. Companion files: `PRIOR_ART.md`, `COST.md`.

## 0. What was certified

Claim, per window, identical to atlas_v5: every zero of ζ with ordinate in the window lies on the critical line and is simple.
- (A) is via Lemma 2.
- (B) is without Lemma 2, via the S-layer.
- No zero list and no Turing count are used.
- The count is matched against Arb's rigorous Turing count as an independent diagnostic.

| window | closed (A) / (B) | sign changes / Arb count | min margin (main; S-layer) | tiers | pipeline wall + independent replay | peak footprint | Lean file audit |
|---|---|---|---|---|---|---|---|
| **[10¹⁵, 10¹⁵ + 2]** | **yes / yes** | **10 / 10** | 0.864; 0.912 | t1 ×2; z1 ×10 | 3143 s + 577 s (1.03 h) | 0.66 GB | 12 certs, 0 violations |
| **[10¹⁶, 10¹⁶ + 2]** | **yes / yes** | **10 / 10** | 0.826; 0.894 | t1 ×2; z1 ×10 | 8874 s + 2057 s (3.04 h) | 1.51 GB | 12 certs, 0 violations |
| **[10¹⁵ + 286, 10¹⁵ + 288]** (close pair) | **yes / yes** | **10 / 10** | 0.864; 0.909 | t1 ×2; z1 ×10 | 3371 s + 492 s (1.07 h) | 0.64 GB | 12 certs, 0 violations |

Every certificate passed the following:
- replay, plain and hardened, inside the pipeline, and again in a second, independent fresh process (`replay_target5.py`);
- the exact tiling of target × [0, 1/2] with 0 seams on the hull, the target and the d = 0 line (pinned tiling script, sha 0868990e…);
- claim (B) coverage, 10/10 per window;
- the Lean audit (`formal/.lake/build/bin/atlas_audit` on the exporter's `--v5` output; files in `lean_audit/`). As a control, the
  audit also re-ran the old 10¹⁴ window: 0 violations.

**Zeros (offsets from T; each lies in a certified sign-change interval of width ≤ 7.9·10⁻⁵).** Exact rational endpoints are in
`v5run/runs/w*/big_1e*/crosscheck.json`.
- 10¹⁵: 0.09207, 0.26215, 0.55551, 0.73004, 0.88809, 1.00441, 1.34629, 1.62285, 1.74785, 1.97668
- 10¹⁶: 0.03184, 0.32027, 0.53918, 0.81340, 0.84965, 1.09699, 1.40762, 1.54051, 1.73535, 1.87871

**Arb cross-check (diagnostic):**
- Turing counts: N(10¹⁵ + 2) − N(10¹⁵) = 10 and N(10¹⁶ + 2) − N(10¹⁶) = 10, from atlas_v5/nzeros, exact integers.
- Both windows have 10 disjoint certified intervals and none straddles an edge: match.
- Arb's own Platt/Turing isolation (COST.md §4; logs in `cost/`) matches Atlas zero by zero in all three windows: each Arb zero lies
  in exactly one Atlas interval, 10/10 for each window.

**Closest pairs.** In the 10¹⁶ window the closest certified pair is at 10¹⁶ + 0.8134 and 10¹⁶ + 0.8497. The certified gap lies in
[0.03617, 0.03633], so δ = gap · log(T/2π)/2π = **0.20**. At 10¹⁵ the minimum is δ = 0.605. See §2 for a δ < 0.1 pair.

## 1. Scoring against PREDICTIONS.md (sha 35bc2600…)

| | prediction | result | verdict |
|---|---|---|---|
| P1 counts = Arb | 10, 10 | 10, 10 | MET |
| P2 10¹⁵ closes | yes, t1 | yes, t1 | MET |
| P3 10¹⁶ closes | yes (70 %) | yes, t1. The step 0.02 still resolved the δ = 0.20 pair (gap 0.036) | MET |
| P4 claim (B) | holds | 10/10, 10/10 | MET |
| P5 margin | 0.88 / 0.86 | 0.864 / 0.826 | MET (> 0). The points were slightly optimistic |
| P6 wall | 45 min / 1.8 h (bounds 2 h / 5 h) | 62 min / 3.04 h | MET on the bounds; both points missed (too optimistic). Part of the 10¹⁶ time came from contention with another user's process |
| P7 peak | 0.5 / 1.4 GB, < 2.5 GB | 0.66 / 1.51 GB | MET. As predicted, atlas_v5's Q8 "≤ 1 GB" fails at 10¹⁶ |
| P8 independent replay | passes | passes, both | MET |
| closest pair | δ ≈ 0.3–0.5 | 0.605 / 0.202 | missed (outside the range both ways) |

This also resolves atlas_v5's own pre-registration (PREDICTIONS sha b4ae8036…), whose 10¹⁵/10¹⁶ rows were "not run":
- Q1: 10/10 MET.
- Q4: "10¹⁵ likely, 10¹⁶ ≈ 50 %": both closed.
- Q6: ≥ 0.6 at 10¹⁶ MET.
- Q7: ≤ 2 h / ≤ 5 h MET.
- Q8: ≤ 1 GB MET at 10¹⁵, **FAILED at 10¹⁶** (1.51 GB).

**Margin against height** (min_candidate_lower, 2-unit windows):

| T | 10¹² | 10¹³ | 10¹⁴ | 10¹⁵ | 10¹⁶ |
|---|---|---|---|---|---|
| margin | 0.944 | 0.939 | 0.902 | 0.864 | 0.826 |

- The margin falls about 0.04 per decade above 10¹³, while tier t1 still closes with 3–4 rows.
- The LP is not the limit in this range; the cost of evaluating ζ is.
- A naive linear extrapolation reaches 0 only near 10³⁶, but that is not evidence for any particular height.

## 2. Close (Lehmer-type) pair near 10¹⁵ (PREDICTIONS_PAIR.md, sha 71eca040…)

**Finding the pair (diagnostic).** Arb's Platt/Turing routine isolated 1500 consecutive zeros above 10¹⁵ (288 units) in 112 s,
at 0.37 GB. The closest of the 1499 gaps is the only one with δ < 0.1: 10¹⁵ + 286.8885 and 10¹⁵ + 286.9073.

**Certificate (frozen v5, same parameters as the 10¹⁵ window):** [10¹⁵ + 286, 10¹⁵ + 288] is **CLOSED, claims (A) and (B)**.
- Two pieces at tier t1 (margins 0.883 and 0.864); S-layer 10/10 (min 0.909).
- Independent replay passed. Tiling 0 seams. Lean audit 0 violations.
- Arb's count N(10¹⁵ + 288) − N(10¹⁵ + 286) = 5 045 354 828 591 033 − 5 045 354 828 591 023 = **10**, equal to Atlas's 10 disjoint
  certified intervals.
- **The pair**, both zeros on the line and simple:
  - γ₁ ∈ 10¹⁵ + [286.8884375, 286.8885156];
  - γ₂ ∈ 10¹⁵ + [286.9072656, 286.9073437];
  - certified gap ∈ [0.018750, 0.018906], i.e. **normalised gap δ ∈ [0.0976, 0.0984]**, about 1/10 of the mean spacing (0.192).
  - These are zeros n = 5 045 354 828 591 028 and …029: Arb's N(10¹⁵ + 286) = …023, and 4 zeros of the window precede the pair.
- Scoring (PREDICTIONS_PAIR):
  - Q1 10 = 10 MET; Q2 closed MET; Q6 the pair is resolved MET.
  - Q3: margin 0.864 against the predicted 0.75. MET (> 0). The near-double zero did not lower the margin, so the point
    prediction was pessimistic.
  - Q4: 64 min (bound ≤ 2 h) MET.
  - Q5: 0.64 GB MET.
- What it is: to our knowledge the highest-lying close (Lehmer-type) pair of ζ zeros whose simplicity and on-line position are
  certified by a Turing-free, list-free method. Arb's Turing route proves the same two zeros (that is how they were found).

  It is a modest close pair (about 1 gap in 1000 is this close), not an extreme Lehmer pair. Odlyzko's and Gourdon's billions of
  non-rigorous zeros at large heights contain much closer pairs; I did not extract their minima here.

## 3. Costs (details in COST.md)

- **Rigorous Z** with Arb, as pinned: 0.25 / 0.76 / 2.4 / 8.0 s at 10¹³–10¹⁶, scaling exactly as √T.
- **Row jet:** 4.7× the Z cost.
- **Arb's memory per Z:** 0.17 / 0.48 / 1.30 GB at 10¹⁴ / 10¹⁵ / 10¹⁶ (∝ T^0.42).
- **Window cost:** about √10 per decade, i.e. W ≈ 2.5 h · (T/10¹⁶)^½ for the pipeline, plus 25 % for the independent replay.
- **The Turing comparator** (Arb's `platt_local_hardy_z_zeros`): 1500 zeros (288 units) above 10¹⁵ in 112 s at 0.37 GB, and 50 zeros
  at 10¹⁶ in 221 s. Per unit height that is **about 4000× cheaper than Atlas** at 10¹⁵. At zero n = 10¹⁸ (t ≈ 1.5·10¹⁷) it was
  killed at the 2.5 GB footprint cap after 26 min.
- **The CPU spent here:** about 6.1 h in total:
  - 4.1 h on the two record windows, including independent replays;
  - 0.8 h on probes and the Arb scan (0.43 h of it the killed 10¹⁸-zero probe);
  - 1.2 h on the pair window and its Arb counts.

## 4. The realistic ladder on this Mac (8 GB, 2.5 GB per process)

| height | route | per 2-unit window | status |
|---|---|---|---|
| 10¹⁵ | frozen v5 + Arb | about 1 h | **done** |
| 10¹⁶ | frozen v5 + Arb | about 3 h | **done** |
| 10¹⁷ | v5 + Arb | about 8–10 h | **blocked by memory**: Arb is about 3.5 GB per Z at 10¹⁷. It would run only with the cap raised to about 4 GB and nothing else running |
| 10¹⁸ | v5 + Arb (Arb's ≤ 4 GB partial sieving) | about 1.5–2 days | over the cap. Not recommended |
| 10¹⁸ | (b) C Riemann–Siegel, double-double, proved rounding | about 3–4 h (1 h on 4 cores) | needs the build: about 2–4 weeks plus review |
| 10²⁰ (Odlyzko's 10²⁰-th-zero region is t ≈ 1.5·10¹⁹) | (b) | about 35 h (about 10 h on 4 cores) | needs the build |
| 10²⁰ | (b′) = (b) + one multi-evaluation per window (Platt/Odlyzko–Schönhage, streamed) | about 1–2 h | needs (b) plus 2–4 weeks more |
| 10²²–10²³ (Odlyzko's 10²²/10²³ zeros: t ≈ 1.4·10²¹ / 1.3·10²²) | (b′) with triple-double phases | about 15–30 h (5–8 h on 4 cores) | needs the build |
| 10²⁴ (Gourdon) and 10²⁸ (HIK) | (b′), or rigorous Hiary t^{1/3} | days per window with (b′); (c) is months of research | (c) only pays above about 10²³ |

**What the build for 10²⁰+ is:**
1. A C Riemann–Siegel evaluator of Z, and of ζ, ζ′ at σ = 1/2 + π/(2a), with:
   - phases from the exact height (T0 + u) in double- or triple-double, with proved per-operation error bounds accumulated into a
     rigorous radius;
   - the Gabcke / Arias de Reyna remainder;
   - O(1) memory.
2. Validation: overlapping enclosures with Arb at 10¹⁰–10¹⁶.
3. A band-limited multi-evaluation with a rigorous interpolation lemma, so one √T pass per window replaces about 500 single points.
4. Wiring it into verify_zs5 as a new Z provider: a trust-base change, a re-freeze and a THEORY note, plus a re-run of the v5
   acceptance comparison and these windows as controls.

## 5. Novelty verdict

See PRIOR_ART.md §4.
- **Defensible (to our knowledge, as of Oct 2026):** [10¹⁶, 10¹⁶ + 2] is the highest-lying window in which RH has been certified
  rigorously and unconditionally in published or publicly documented work. It is also the first such window above 3·10¹² by a
  zero-list-free, Turing-free method, now at 10¹⁵ and 10¹⁶ as well as v5's 10¹³ and 10¹⁴.
- **Mandatory caveats:**
  - Arb's Turing-method routines certify such windows by a library call, ~4000× cheaper per unit height at 10¹⁵. We used them as
    the cross-check, and they agree.
  - Non-rigorous checks reach 8·10³⁴ (Bober–Hiary), and Gourdon computed 2·10⁹ zeros near zero n = 10¹⁶ and 10¹⁷.
  - HIK verified a 1.4-million-zero window at 10²⁸, conditional on floating-point zero intervals.
  - This is not a new fact about ζ in any strong sense, and the initial-segment height H stays at 3·10¹².
  - Lemma 2 and THEORY_V4 §10 (claims A/B) are still unreviewed.
- **Not claimable:** "first verification at 10¹⁵/10¹⁶", "beyond Odlyzko", "extends the RH verification height", or any wording that
  makes Atlas the only rigorous route.
- **Where a genuine record would be:**
  - a rigorous window near Odlyzko's 10²⁰–10²³ zeros. Its value is as a rigorous counterpart to Odlyzko's floating-point statistics
    region, especially a certified close pair there.
  - making HIK's 10²⁸ window unconditional.

  Neither is reachable with stock Arb on this machine. Both need the §4 build. Whether to build is Phil's call. Given Arb's cheap
  Turing route, the honest selling point is the independent (Turing-free, list-free) certificate type, not speed.
