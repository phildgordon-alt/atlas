# HIARY_SCOPE: a rigorous sub-√T evaluator (Hiary T^{1/3}) as a new module of the Atlas engine (scoping study, 2026-11-02)

Phil approved this study on 2026-11-02. It is a study only: no heavy compute was run. The only measurement was one
python-flint micro-timing (about 1 s at nice 19). Nothing frozen or running was touched (runs/m11, src/v14b, atlas_v5z8,
review_v14b).

Labels:
- **[S]** sourced: the paper, code or page is cited and was read today.
- **[M]** measured here.
- **[I]** inference or estimate, with the model stated.

## 0. Answer first

**Verdict: feasible, but not the lever for 10^28. Go with conditions: build only the kernel and its cost gate (stage 1),
then decide.**

1. **Session structure.** A Hiary-type main sum **keeps Atlas's session structure.** One pass still serves a 100-unit
   window, so the cost does not become per-point (§2.4). This is the good news.
2. **The gain grows slowly.** Under the √T engine the session cost is about N·c_term. A T^{1/3} session costs about
   (t^{1/3}/0.9)·c_q·(1 + ln x), where c_q is the cost of one quadratic-sum block. The speedup is
   **S = x/(1 + ln x)**, where x = 0.36·t^{1/6}/r and r = c_q/c_term (§3).
   - So the gain grows only like t^{1/6}: a factor of 2.15 per two decades.
   - Bober–Hiary's own numbers calibrate r ≈ 3,400 for non-rigorous double-precision code. At 8.1·10^34 they report 22.5
     core-years against 300 for direct summation, which is S ≈ 13.3.
   - A rigorous double-double version is plausibly r ≈ 3,000–30,000 [I].
3. **At 10^28 (the HIK target) the gain is 1.0–2.7×** (central 1.1–1.9×). The window takes 3.8 days now and about
   1.4–3.8 days with Hiary. The √T engine on v14b already makes 10^28 feasible, so **do not wait for Hiary for 10^28.**
4. **The real payoffs:**
   - **(a) A second, algorithmically independent evaluator at about zfast's cost at 10^25–10^28.** This closes the
     "code-independent Z at ≥ 10^24" gap. Today zref_m8 takes about 12 h per point at 10^24.
   - **(b) 10^30 windows in about 1–3.5 weeks instead of 38 days.** 10^32 windows take 1.5–5 months instead of about a
     year. The top of that range is near zfast's N < 2^52 ceiling (t < 1.3·10^32).
5. **Hardest rigour step.** Hiary's theta algorithm has no numerical constants. He writes "We do not try to obtain
   numerical values for the constants" [S, arXiv:0711.5002]. Two things must be built from scratch and proved:
   - explicit truncation bounds for the saddle-point remainder integrals, which use
     h(z,w) = ∫₀¹ t^z e^{wt} dt (incomplete-gamma type);
   - a rounding and error-propagation bound through about log₂K reduction levels. Hiary bounds the coefficients only as
     O(8^j K²), and that growth must be beaten in double-double.

   This must also be fast. Arb in the loop is not viable: acb gamma_lower at 128 bits costs **15.4 µs per call [M]**, and
   a block needs on the order of 10³ such integrals, so r would be about 10^5–10^6.

## 1. The algorithms

### 1.1 Hiary, "Fast methods to compute the Riemann zeta function", Ann. of Math. 174 (2011) 891–946 (arXiv:0711.5005) [S]

**T^{1/3+o(1)} method.**
- The Riemann–Siegel main sum Σ_{n≤N} n^{−1/2−it}, N = ⌊√(t/2π)⌋, is split into blocks [v, v+K).
- For each block:

  t log(v+k) = t log v + (t/v)k − (t/2v²)k² + (t/3v³)k³ − …

- With K ≈ v/t^{1/3}, the cubic and higher terms are O(1). Their exponential is Taylor-expanded into a polynomial in k/K
  of degree about J (J = 18 in practice).
- Each block therefore becomes Σ_j c_j F(K, j; a, b), where F(K, j; a, b) = Σ_{0≤k<K} (k/K)^j e(ak + bk²),
  a = t/(2πv) mod 1 and b = −t/(4πv²) mod 1. These are quadratic exponential sums.
- Each sum is computed in polylog(K) time (§1.2).
- The number of blocks is about (t^{1/3}/0.9)·ln(N/v₀). The range n < v₀ ≍ t^{1/3} is summed directly.

**T^{4/13+o(1)} method** (same paper).
- Longer blocks, K ≈ v/t^{1/4}, are reduced to *cubic* exponential sums.
- These are computed by a cubic-sum algorithm that works only when the cubic coefficient is small, so the reduction is
  more intricate.
- It has never been implemented: Bober–Hiary: "the fastest method … t^{4/13+o(1)}"; they implemented the 1/3 method.
- Constants are unknown, and the rigour burden is strictly larger. **Not proposed** [I].

### 1.2 Hiary, "A nearly-optimal method to compute the truncated theta function, its derivatives, and integrals", Ann. of Math. 174 (2011) 859–889 (arXiv:0711.5002) [S]

**The theta algorithm.**
1. **Normalise.** Periodicity and conjugation reduce to a ∈ [0,1) and b ∈ [0,1/4] (Lemma 4.1).
2. **Transform.** Poisson summation (a van der Corput step) turns F(K, j; a, b) into a sum of length about 2bK ≤ K/2
   with arguments a/(2b) and −1/(4b), using the self-similarity of the Gaussian.
3. **Remainders.** The non-saddle remainders R₁, R₂ are integrals. After contour shifts they decay exponentially and are
   truncated after about log(K/ε) terms. They are built from h(z,w) = ∫₀¹ t^z e^{wt} dt.
4. **Boundary cases.** Euler–Maclaurin is used when q ≤ p, and direct summation when K is small.
5. **Iterate.** At most about log₂K levels are needed.

**Cost.** At most A₂ν^{κ₂} operations, with ν = (j+1) log(K/ε). Bits needed are at most A₃ν², but "substantially
fewer" in practice.

**Status of the bounds.** The error is ±A₁ν^{κ₁}ε with *absolute constants that are not computed*. The paper calls the
method "rigorous, explicit, and suited for computer implementation" but gives no numerical constants. That gap is the
whole rigour project (§2).

### 1.3 Bober–Hiary, "New computations of the Riemann zeta function on the critical line", Exp. Math. 27 (2018) (arXiv:1607.00709) [S]

**What they implemented.** Hiary's T^{1/3} method:
- **Stage 1** (n ≤ t^{1/4}): direct summation, 50-bit terms.
- **Stage 2** (t^{1/4} to t^{1/3}): term by term, with a Taylor-recurrence exponent.
- **Stage 3** (n ≥ v₀ = ⌈2000·t^{1/3}⌉): blocks with u₀ = α|s|^{1/3}, α = 1/0.9, J = 18, then the theta algorithm.
  K_min = 2000 is the direct-summation cutoff.

**Arithmetic.** C++ double, with MPFR only "where completely unavoidable".

**Multi-evaluation (their §7).** Block sums at t₀ are reused for t₀ + jδ:
- grid δ = 0.04, 0 ≤ j ≤ 1000, about 40 units;
- error ≲ δj·log t₀ / t₀^{1/6} (provable form), so the range of j can be about t₀^{1/6−ε};
- this is the same idea as Atlas's session moments.

**Scale.**
- More than 50,000 zeros in over 200 intervals, 10^24 ≤ t ≤ 8.1·10^34.
- The largest run took 22.5 core-years on 2.8 GHz Xeon E5462, against an estimated 300 core-years for stage 2 alone.
  Stage 3 per block is "around 200" times faster near the top of the range.
- Most other runs took "a few days" on about 12 nodes × 8 cores (2.27 GHz).

**No crossover height or per-evaluation wall time is stated.** Figure 4 gives summands per second only as a plot.

**Why the error control is heuristic (their words).**
- For the practical truncation bound: "we cannot prove this". The provable bound is "a significant overestimate".
- For roundoff: they rely on "square-root cancellation" in the sum.
- Accuracy: "±10^-7 typically", ±10^-5 worst case. In a test of 29,952 sums near 10^36 at ε = 10^-5, the worst error was
  5.4·10^-6.
- The code hard-codes ε = e^{-20} ≈ 2·10^-9 per block (zetacalc README).

**This rests on unproved but believed bounds plus empirical testing. It is not wrong.** (NOVELTY_M10 wording: "not
rigorous (heuristic error control, as they state)".)

**Code.**
- github.com/jwbober/zetacalc (C++, last push 2016-07-05).
- **The GitHub API reports license: None**, so no reuse rights are granted. Read it for understanding only. Never copy,
  vendor or adapt it into Atlas.
- It could at most serve as an untrusted numerical oracle in scratch, and only with Phil's OK.
- Its structure shows the real engineering: G_functions, H_and_J_integrals, ICn (several integral pieces), precomputed
  tables, Euler–Maclaurin, and w_coefficient. Its README lists "possible sources of nan" from out-of-range tables. This
  is a sign of how much must be bounded rigorously.

### 1.4 Odlyzko–Schönhage / Platt multi-evaluation: why it is not the lever [I, consistent with ADDITIONS_SCOPE §2.3 and CORE_ROADMAP "Demoted"]

- O–S and Platt amortise one √T-cost precomputation over about √T grid points (FFT plus band-limited interpolation).
- Atlas already amortises its single √T pass over a whole 100-unit window: bucket moments (THEORY_M3, THEORY_V5Z5),
  about 26,000 Z/row evaluations plus a 45,000-point Turing grid per session (RESULTS_M10).
- After the pass, points cost milliseconds. The pass is 97% of the runtime (OPTIMIZE_M9 §1).
- O–S therefore leaves the dominant cost exactly where it is. **Only a change in how the pass itself scales (Hiary)
  attacks the √T cost.** Hiary's "amortized algorithm" also needs about T^{1/2} precomputation, so it is irrelevant too
  [S, Hiary's fastmethods page].

## 2. Rigour: what a fully rigorous version requires

The certificate needs a ball that provably contains each session moment, and so each Z/row value. Concretely, the Z
radius must be at most about 1e-9 (THEORY_ZFAST §0).

### 2.1 Error budget [I]

- Main-sum blocks contribute about v^{−1/2}·K·ε_rel each. Σ over blocks ≈ Σ_{n≥v₀} n^{−1/2} ≈ 2√N.
- A Z budget of 10^-10 therefore needs per-block relative accuracy **ε_rel ≲ 10^-10/(2√N)**:
  - 8·10^-18 ≈ 2^-57 at 10^28;
  - 2.5·10^-18 at 10^32.
- That is beyond binary64 for a worst-case (not square-root) bound. **Double-double throughout the theta recursion is
  required**, as in zfast.
- Bober–Hiary's e^{-20} per block is about 2^-29, roughly 28 bits short, and heuristic.

### 2.2 The pieces and their difficulty

| # | piece | what must be proved | difficulty |
|---|---|---|---|
| R1 | Block reduction | Taylor remainder of t·log(1+k/v) past the quadratic term. Truncation of exp(cubic+) into degree-J polynomials in k/K, with explicit remainder (Lemma-M1 style). Weights n^{−σ} for Z and rows expanded in k/v. Shift of block moments to zfast bucket centres L_b (binomial in log(1+k/v), 3–4 terms) | **easy**: zfast-style lemmas |
| R2 | Exact a, b mod 1 | a = t/(2πv), b = −t/(4πv²) mod 1 to about 2^-110 absolute | **easy, and an Atlas asset**: zfast already has exact fixed-point phase residues mod 2^256 (THEORY_ZFAST §5, THEORY_M5 §2) |
| R3 | Theta step algebra | Poisson / van der Corput identity per level, exact, with the a, b normalisation and the conjugation and periodicity bookkeeping | medium: exact identities, but easy to get subtly wrong (signs, boundary k = 0, K) |
| R4 | **Remainder integrals R₁, R₂ and h(z,w)** | Explicit contour-shift truncation bounds (Hiary gives only "absolute constants"). Rigorous dd evaluation of h(z,w) = ∫₀¹ t^z e^{wt} dt over the parameter ranges reached, with a proven error, via series, asymptotics or precomputed tables with certified interpolation | **hardest (analysis)**: new explicit analysis, in effect a paper's worth |
| R5 | **Error propagation through about log₂K levels** | A priori bound on how per-level errors amplify. Hiary bounds the coefficients only as O(8^j K²). At j ≈ 22 and K ≈ 10^4–10^5 a naive bound gives 10^28–10^30, which would swamp dd's 10^-32. Needs a sharper per-level analysis, a better-conditioned basis, or triple-double in part | **hardest (numerical)**: may force more precision, and so a larger r |
| R6 | Euler–Maclaurin and direct boundary cases | Explicit EM remainder with derivatives of the theta-type summand | medium |
| R7 | Rounding analysis of the dd code | Same style as THEORY_ZFAST §6–7 and review2 kernel_bound.py: proven per-operation bounds, -ffp-contract=off, mutation tests | medium (known method) |
| R8 | Session merge | Block moments into bucket moments, plus the extra h-dependence. hK/v ≤ H·0.9·t^{−1/3} ≈ 4·10^-8 at 10^28 with H = 91, so 4–5 Taylor terms suffice | easy |

**The two hardest steps are R4 and R5, and they interact.**
- A rigorous bound that is too loose forces a larger J or precision. That raises r, and S falls fast (§3).
- Arb cannot carry the inner loop: acb gamma_lower at 128 bits costs 15.4 µs per call, against 0.64 µs for acb_exp [M].
  A block needs on the order of 10³ integral evaluations, which is about 15 ms per block (r ≈ 7·10^5, never a gain).
- Arb's role is to validate and precompute certified tables, not to run per block.

### 2.3 Lean / formal status [I]

- R1–R8 would be [T] lemmas in a THEORY doc, at the same trust level as zfast's analysis. They would not be in Lean.
- They add a large new analytic trust surface. **Without an external specialist review, the result would carry the same
  caveat as Lemma 2 and THEORY_V4 §10.**

### 2.4 Fit with the session/moment structure: one session still serves a 100-unit window [I, a structural argument]

- Inside a block, e^{−i(t₀+h)log(v+k)} = e^{−ih log v}·e^{−it₀ log(v+k)}·e^{−ih log(1+k/v)}, and |h·log(1+k/v)| ≤ hK/v
  is tiny (R8).
- Every zfast bucket moment M_{j,b,m} = Σ w_j(n) e^{−it₀ log n}(log n − L_b)^m (m ≤ K+1 = 19) is therefore a fixed
  linear combination of that block's F(K, j′; a, b), with j′ ≤ J + 4.
- The Hiary pass outputs **exactly the same session object** as zfast: bucket moments plus bounds. All downstream code is
  unchanged: point evaluation, rows, the Turing grid and the verifier.
- Multiple weight families (Z and both row σ's) reuse the same F_j, so they are nearly free.
- Bober–Hiary §7 does essentially this over 40 units. Atlas's H = 91 is well within their t^{1/6} range.
- **Cost stays per-session, not per-point.**

## 3. Expected speed on this Mac (M1, 8 cores, 8 GB)

### Model [I]

- c_term is zfast v14's per-term cost, with moments included: 20 ns on one P-core.
- c_q is one rigorous quadratic-sum block with J ≈ 22 weights, and r = c_q/c_term.
- Blocks are used where they win (K > r). K = 0.9v/t^{1/3}, so K_max = 0.36·t^{1/6} at v = N.
- The direct part (n < r·t^{1/3}/0.9) runs on zfast's own kernel.
- The session cost ratio is then S = x/(1 + ln x), with x = 0.36·t^{1/6}/r (S = 1 if x ≤ 1).
- **Calibration:** Bober–Hiary's 300/22.5 = 13.3 at t = 8.1·10^34 gives r ≈ 3,400 for their non-rigorous double code
  (relative to their cheaper stage-2 term).
- The baseline is measured: 1e25 session 5,180 s (D4, W8; RESULTS_M10), scaling as √T. Window = 2 sessions + 600 s.

| height | √T engine (v14) window | r = 2,000 (optimistic) | r = 3,400 (B–H-calibrated, non-rigorous level) | r = 10,000 (central rigorous guess) | r = 30,000 (pessimistic) |
|---|---|---|---|---|---|
| 10^26 | 0.39 d (9.3 h) | S 1.64 → 0.24 d | 1.25 → 0.31 d | 1.00 (no gain) | 1.00 |
| 10^28 | 3.8 d | 2.67 → 1.4 d | 1.89 → 2.0 d | 1.10 → 3.4 d | 1.00 |
| 10^30 | 38 d | 4.6 → 8.2 d | 3.2 → 12 d | 1.6 → 24 d | 1.01 → 37 d |
| 10^32 | 379 d (zfast ceiling at 1.3·10^32) | 8.3 → 46 d | 5.5 → 69 d | 2.5 → 149 d | 1.3 → 286 d |

### Reading the table

- Rigorous dd plus interval bounds should make c_q at least a few times Bober–Hiary's double code. That is why the
  central guess is r ≈ 10^4. This is an estimate, not a measurement; stage 1 measures it.
- **Kill line:** with r > 20,000 there is no useful gain below 10^32.
- For S ≥ 2 at 10^28, c_q must be at most about 50 µs.

**Further assumptions [I]:**
- Blocks are independent, so v14's work queue parallelises them as well as zfast's items. 8-core scaling is assumed equal
  for both engines.
- Margin: MARGIN_ANATOMY's fit (true slack ≈ 1.481 − 0.0070·ln t) extrapolates to about 1.00 at 10^30 and 0.97 at
  10^32. Margin needs a fresh study before any ≥ 10^30 claim.

**Memory [I].**
- Per-block workspace is O(J²·log K) doubles, much less than 1 MB.
- Certified h(z,w) tables are estimated at tens of MB.
- Bucket accumulators are the same as zfast (nb ≈ 3,000 × 20 moments × weights).
- Blocks are streamed and checkpointable per item (the v14b format).
- Expected peak is under 0.5 GB, which fits easily within the 4 GB watchdog.

## 4. Build plan (new versioned modules; nothing frozen modified)

**Module names.**
- `diagnostic/zfast/src/h1/` (libzfast_h1): the theta kernel `hq1.c`, block reduction `hblock1.inc`, session pass
  `hsess1.inc`, and an API that produces the zfast session object.
- `THEORY_H1.md`.
- Provider hook: a new `atlas_v5z9/lib/zfast_provider.py` variant selected by `Z_PROVIDER=h1`. It records the provider in
  pieces.json (ADDITIONS_SCOPE module rule).
- Gate: `engine/regress_v1/h1_gate.py`.
- Code is own code from the papers. No zetacalc code is used (it has no licence).

| stage | deliverable | pre-registrable success criterion | negative controls | effort | risk |
|---|---|---|---|---|---|
| **S0** theory | THEORY_H1 §R1–R8 with explicit constants (R4/R5 first). An untrusted reference: Arb/mpmath direct sums of F(K, j; a, b), K ≤ 10^6 | Fresh-context adversarial review (review_h1/) finds no unresolved gap in R4/R5. Every constant is numerically sanity-checked against direct sums on 10^4 random (a, b, K, j) | Inject a known-wrong constant (×0.5): the sanity check must flag it | 3–5 wk | **high**: R4/R5 may not close at dd |
| **S1** kernel + **cost gate** | `hq1.c`: ball F_j(K; a, b), j ≤ 24, in dd with proven bounds | (a) 100% containment of Arb direct-sum balls on 10^4 random inputs, K ∈ [2·10^3, 10^6], a, b ∈ [0,1) including near-edge b ≈ 0, 1/4. (b) Radius ≤ 2^-57·K. (c) **Measured r reported; STOP if r > 20,000 at K = 10^4–10^5** | Mutation tests (review2/mut style), perturbed-a ball must not contain the true value, and `-ffp-contract=on` build must fail the bound audit | 4–6 wk | high: r is the unknown deciding everything |
| **S2** session | `hsess1`: block reduction plus merge into zfast buckets; same session object | Moment, Z and row balls overlap zfast v14's at 10^16, 10^20 and 10^22 (H 91, 2,000 points each). Radius ≤ 2× zfast's. Replay-of-record verdicts on frozen w_1e22 and w_1e25 certificate sets identical (the certificates themselves are untouched) | Perturb one block's a by 2^-50: overlap must fail. Drop one block: Turing gate must fail | 2–3 wk | medium |
| **S3** crossover | Timed sampled sessions (random 1% of blocks plus a direct-part sample), extrapolated at 10^24, 10^26, 10^28, 10^30 | Measured S within the band pre-registered from S1's r (formula §3). Compute ≤ 1 h per height, run only when cores are free | — | 1 wk | low |
| **S4** independent replay | h1 as the **replay provider of record** for a new window at 10^25–10^26 (generator zfast, replay h1) | Window closes; Turing count equal; Lean 0 violations. First *algorithm-independent* replay at these heights | Standard NC-W/NC-T controls | 1 wk + run | medium |
| **S5** height | Only if S3 shows S ≥ 1.5 at the target: a window at 10^30 (or at 10^28 if not already done on v14b) | Pre-registration with margin re-study, novelty check | as M10 | 2–4 wk + run | medium |

- **Total:** about 3–5 months of build to S4. Stop points are at S0 (theory does not close) and S1 (r too large).
- **Independent review gates:** after S0 (theory), after S1 (kernel plus rounding), and before S4's claim. External
  specialist review remains an open caveat, as for Lemma 2.
- **Validation chain:**
  - regress_v1 tier 0/1 stays green: frozen code is untouched.
  - h1 is compared with zfast at low heights, where both are cheap.
  - The Turing gate and count equality stay required.

## 5. Recommendation

**Go with conditions.**
- Approve S0 and S1 only, about 2–3 months, with the hard kill criterion at S1 (r > 20,000 means STOP).
- Run HIK 10^28 on the √T engine (v14b) as already planned. Hiary would save at most about 1–2.4 days there, and
  plausibly about 0.4 day.

**What a passing S1 would let Atlas reach:**
- an algorithm-independent replay of record at 10^25–10^28, at about zfast's cost;
- rigorous windows at 10^30 in about 1–3.5 weeks;
- 10^32 within months.

**Wording, consistent with NOVELTY_M10:**
- Bober–Hiary computed zeros up to 8·10^34 non-rigorously. Never say "beyond Bober–Hiary" or "new height for zeros".
- A future claim would be "a rigorous (explicit-error) implementation of Hiary's T^{1/3} method serving Atlas's list-free
  certificates". A "first rigorous implementation" claim needs a novelty check: today's searches found none, but that is
  preliminary.
- Gate 0 holds: this is a new evaluator module of the one engine, feeding the same sessions and certificates, not a
  separate tool.

## Sources

- Hiary, Fast methods to compute the Riemann zeta function, Ann. Math. 174 (2011): https://annals.math.princeton.edu/2011/174-2/p04, arXiv:0711.5005.
- Hiary, A nearly-optimal method to compute the truncated theta function…: https://ar5iv.labs.arxiv.org/html/0711.5002.
- Bober–Hiary, arXiv:1607.00709: https://ar5iv.labs.arxiv.org/html/1607.00709.
- Hiary's fastmethods page: https://people.math.osu.edu/hiary.1/fastmethods.html.
- zetacalc: https://github.com/jwbober/zetacalc (API: license null; README read in scratch only).
- Measured [M]: python-flint 0.9.0 (~/projects/atlas-rerun/.venv), 128-bit acb gamma_lower 15.4 µs per call, acb exp
  0.64 µs, single thread, nice 19.
