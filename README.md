# Atlas: zero-list-free certificates for the Riemann Hypothesis in windows at large height

Atlas is a computer-assisted proof engine. It certifies that **every zero of the Riemann zeta function in a given height window
lies on the critical line and is simple**. Every certificate is checked in rigorous ball arithmetic, replayed by separate code
in a fresh process, and audited by a checker written in Lean 4.

The certification method is Atlas's own and new: **zero-list-free, Turing-free explicit-formula certificates**. Each certificate
is a linear program over explicit-formula test functions, and its dual is verified in Arb ball arithmetic. It also uses
sign-change credit from a rigorous evaluation of Z(t), a local-count closure, and Lemma 2 (parity of sign changes ⇒ simplicity),
whose logic is checked in Lean. No list of zeros is ever an input to a certificate, and Turing's method is not used to make one.
Only the fast evaluator of ζ underneath the method, zfast (a rigorous Riemann–Siegel main sum in double-double arithmetic), has
prior art: the unreleased FLINT development work "dfloat" (2026).

This repository holds the certificates, the run records, the frozen code that produced and replayed them, the Lean
formalisation, the independent review reports and the pre-registrations. A verification script re-checks everything here in
about 5 minutes (results below).

> Status: research code and results by one independent researcher, **not yet reviewed by outside experts**. The new
> mathematical step (Lemma 2 and THEORY_V4 §10, the no-parity S-layer) has had no external review. Expert review is pending.

## Story

Atlas started as a moonshot: a launch pad for me to practise on. My role is the conductor. I don't understand all of the mathematics myself, so I push the limits, form the theories and decide where to aim next. The steps, simply:

1. Map the primes from the zeros. I wanted to see if I could recover the primes from the locations of the zeta zeros. It is known mathematics; I just wanted to do it. It worked: 33 of 33 prime powers recovered, and 200 scrambled control runs found nothing.
2. Look for hidden patterns. I tested whether the maps repeat across scales. The pattern held, but it wasn't strong enough to use as a detector.
3. Try to catch a zero off the line. We built a sensor to hunt for a counterexample to the Riemann hypothesis. Every real search came up empty, which is what you'd expect if it's true.
4. Turn it around. That evolved into a method that proves where the zeros are without needing a list of known zeros.
5. Build a tool and aim it at known problems. It has rigorously verified the Riemann hypothesis in windows up to 10^26, to my knowledge the highest rigorously and unconditionally verified in published or publicly documented work, and shown a published 2024 conjecture false for every quadratic and cubic field. Along the way the engine became about 550 times faster, and it all runs on an 8 GB Mac. Over 30 certified results in all, from Artin's conjecture to prime races, are listed below.

The biggest lesson came early: AI builders kept reporting "pass" and the independent checker kept overturning it. So I set the rules, carried over from my manufacturing work: predictions are locked in before any code is written, no agent checks its own work, independent reviewers try to break every result, and the proof logic is machine-checked in Lean. All code in Atlas's current engine was written by Claude Code; Codex and Gemini served as independent checkers of the mathematics, and Codex also wrote some early exploratory code in the first version.

(The precise statements, with their context and caveats, are in sections 1, 2 and 6; the detailed AI disclosure is in section 7.)

---

## 1. Main result: RH certified in windows from 10^15 to 10^26

RH is certified in windows at heights 10^15 … 10^26. The latest window is [10^26, 10^26 + 100], with 924 zeros, equal to the
Turing count. To our knowledge (literature check, 2 November 2026), [10^26, 10^26 + 100] is the highest window in which RH has
been rigorously and unconditionally verified in published or publicly documented work.

Context that goes with that statement:

- **Bober and Hiary** (Exp. Math. 27, 2018) computed zeros from 10^24 to 8·10^34 and checked RH for more than 50,000 of them. In
  their own words this was **not rigorous**. Zeros at these heights have therefore been computed before. What is new here is a
  rigorous, unconditional certificate.
- **Hiary, Ireland and Kyi** (Math. Comp. 2026) treat a window near 10^28 that is **conditional**. It assumes that zero ordinates
  taken from tables are accurate to ±10^-10.
- **The global verification height is unchanged.** RH is known for all zeros up to H = 3·10^12 (Platt and Trudgian, 2021).
  The windows here are isolated windows. They say nothing about the gaps between them.
- **Standard tools could in principle do this.** FLINT/Arb's rigorous Riemann–Siegel evaluation with Turing's method could in
  principle certify such windows, at a much greater cost, and Arb's documented zero-counting range reaches about t ≈ 10^22.
  What is claimed is a new certification method that is fast enough to reach these heights. No claim is made that only this
  method could reach them.

**The windows.** Every row is a closed claim (A) and claim (B): every zero with ordinate in the window lies on the critical
line and is simple. Claim (A) uses Lemma 2. Claim (B) proves simplicity without Lemma 2, through the S-layer, whose theory
(THEORY_V4 §10) has no external review yet. "Zeros" counts the certified sign changes. Where a count is listed, it equals an
independent Turing count, which is run as a separate required check.

| height | window(s) | zeros | pipeline (frozen) | run directory under `atlas_mark2/diagnostic/` |
|---|---|---|---|---|
| 10^15 | [10^15, 10^15+2]; close pair [10^15+286, +288] | 10; 10 | atlas_v5 / atlas_v5z | `record_heights/v5run/runs/`, `zfast/atlas_v5z/runs/w1000000000000000/` |
| 10^16 | [10^16, 10^16+2] | 10 | atlas_v5 / atlas_v5z | `record_heights/v5run/runs/`, `zfast/atlas_v5z/runs/w10000000000000000/` |
| 10^17 | [10^17, 10^17+2] | 11 | atlas_v5z | `zfast/atlas_v5z/runs/w100000000000000000/z_1e17` |
| 10^18 | [10^18, 10^18+2] | 11 | atlas_v5z | `zfast/atlas_v5z/runs/w1000000000000000000/z_1e18` |
| 10^20 | [10^20, +2]; [10^20+4, +6] | 13; 14 | atlas_v5z2 (+ v5z3 repeat) | `zfast/atlas_v5z2/runs/w100000000000000000000/` |
| 10^21 | [10^21, +2]; [10^21−6, −4] | 15; 15 | atlas_v5z2 (+ v5z3) | `zfast/atlas_v5z2/runs/w1000000000000000000000/` |
| 10^22 | [10^22, +2]; **[10^22, 10^22+100]** | 16; **777** | atlas_v5z2/v5z4; **atlas_v5z5, re-run on v5z7** | `zfast/atlas_v5z5/runs/…/wide_1e22`, `zfast/atlas_v5z7/runs/…/wide7_1e22` |
| 10^23 | [10^23, +2], [10^23+2, +4], two close-pair windows | 16, 16, 17, 17 | atlas_v5z4 | `zfast/atlas_v5z4/runs/w100000000000000000000000/` |
| 10^24 | [10^24, +2]; close pair [10^24−3, 10^24−1] | 17; 16 | atlas_v5z4 | `zfast/atlas_v5z4/runs/w1000000000000000000000000/` |
| 10^25 | **[10^25, 10^25+100]** | **888** | atlas_v5z7 / libzfast v14 | `zfast/atlas_v5z7/runs/w10000000000000000000000000/wide7_1e25` |
| 10^26 | **[10^26, 10^26+100]** | **924** | atlas_v5z7 / libzfast v14 | `zfast/atlas_v5z7/runs/w100000000000000000000000000/wide7_1e26` |

There is no 10^19 window. The runs at 10^12–10^14 are controls inside the range Platt and Trudgian already verified.

**The 10^26 window in numbers** (`atlas_mark2/diagnostic/zfast/RESULTS_M11.md`):

| item | value |
|---|---|
| certificates | 100/100 main and 924/924 S-layer, replay of record passed (plain and hardened), 0 seams |
| Turing count | N(10^26) = 907650062242638637035433072 and N(10^26+100) = 907650062242638637035433996, both pinned; difference 924 = certified sign changes |
| Lean audit | 1,024 certificates, VIOLATIONS 0 |
| margin | reported 0.5629; diagnostic tight bound 1.048 |
| cost | 9.19 h wall on one Apple M1 laptop (8 GB), peak memory 0.29 GB |
| prediction | predicted 924 zeros (band 920–928), pre-registered before the run (`PREDICTIONS_M11.md`, sha256 57d9729e…) |

The 10^25 window: 888 zeros (predicted 887), 3.02 h, Lean 988 certificates with 0 violations (`RESULTS_M10.md`). The novelty
check is `zfast/novelty/NOVELTY_M10.md`. It found no rigorous, unconditional RH verification at or above 10^25 elsewhere;
because 10^26 lies above 10^25, the same search covers it.

## 2. All certified results (the project's results table)

Below is every row of the project's internal results table (`ATLAS_STATUS.md`, rows 1–31, as of 3 November 2026), with that
table's status and caveat wording. Later updates from the same status log are folded into the rows they change. Internal to-do
notes and drafts of letters to named researchers have been left out. Six rows (19, 22, 24, 25, 26, 31) are RH windows, which
section 1 covers in full. Rows 12, 28 and 30 are evaluator milestones, each with the certificates it produced.

Shared caveats:
- Novelty statements are "to our knowledge", from literature checks that are not exhaustive.
- No result has had expert review.
- "Independently verified" means a separate reviewer agent recomputed the result; it does not mean a human expert.
- Only the RH windows have their full certificates in this repository. For the other rows, the documents named in the last
  column (all under `atlas_mark2/diagnostic/`) are included only where a directory is listed. The data are kept in the project
  tree.

| # | result | status / wording | documents |
|---|---|---|---|
| 1 | **GRH for ζ_K, K = Q(x³−x−1), d = −23, to \|t\| ≤ 10⁴**: 25,275 zeros, all on the line and simple. **Extended to 2·10⁴** (27 Oct 2026): 54,962 zeros of L(s,ρ) in (0, 2·10⁴], all on the line and simple | "First interval-certified beyond Tollis 93.81; exceeds Ng's floating-point 972 by ~10×." Independence: full-list FFT match 25,275/25,275; rigorous sample 100/100 above 700. Lean audit 0 violations. Residual: above height 700 the formal proof rests on the deg2_fast code | `flagship_K23/`, `flagship_K23_ext/`; Lean data `formal/audit/data_flagship/` |
| 2 | **Ng's 16 S3 race densities certified (GRH + LI)**; 25-field table; −108 is the most biased in this family | "First rigorous enclosures with interval-certified inputs"; "63 of 75 densities new" | — |
| 3 | **D4 races (31 fields), the first S4 race densities, and elliptic-curve δ(E)** for 11a, 37a, 389a, 5077a | Not yet novelty-checked separately | — |
| 4 | **Serre's quaternion field: ord ζ_K(1/2) = 2** (interval certificate); first δ(P_{205²;2,1}) = 0.71679886746; 2304-field δ = 0.75743538743 | Omar (2001) had the order numerically. The claim is the certificate and the density, not "first proof" | — |
| 5 | **The CMM Euler–Kronecker constants γ_S, unconditionally, to 32–33 digits** (previously under GRH, 2–4 digits) | Holds; "to our knowledge, as of Oct 2026" | — |
| 6 | **Koyama–Sheth Conjecture 3.2 for k ≤ 600; super-positivity and Murty's Conjecture 2 for k ≤ 200** | LMFDB has proved ranks for k ≤ 200; the new range is 202–598 | — |
| 7 | **APKK Mertens constants (15 classes) and prime-form constants, to 34–36 digits; Bateman–Horn constants** | The numbers are new; the formula is a rearrangement | — |
| 8 | **The naive Mertens-type conjecture (Hasan–Kim–Mazur–Sahota, HKMS) is false for Q(√5) and Q(√−3), hence false for every quadratic field** | Independently verified (CONFIRMED, with wording corrections). HKMS's Q(i) value at 72.85 is an error in their paper | `corollaries/RESULTS.md`, `corollaries/verify_hkms/VERIFY.md` |
| 9 | **Super-positivity for 655 L-functions; ζ_K(1/2) < 0 for 652 cubic fields; Watkins's ξ0** | Low novelty | — |
| 10 | **LMFDB issue #5308: for Cremona's sextic curve 6.6.300125.1-1.1-a1, L(E/K,1) = 0.52188070959783711143 ± 3·10⁻²¹ and Sha = 37⁴**; also 5 quadratic and cubic curves | Unconditional (modularity is known). Typical sextics need streamed coefficients | — |
| 11 | **Cohen's MathOverflow question 513303**: a general method; certified S5 prime zeta values for all 7 classes | All classes unconditional after a citation fix (KLW Thm 1.2(b)) | — |
| 12 | **General L-function evaluator; low-lying GRH for 382 totally real cubic fields** | — | — |
| 13 | **Calegari's S5 criterion input, L(ρ5, σ) ≠ 0 on (0,1), unconditional**: all 186 fields, 372/372 runs | Corrected 13 Oct 2026 (the earlier certificates assumed that ζ_K10/ζ is entire); redone via ζ_K10(σ) < 0 and verified. 15 fields satisfy Calegari's literal hypothesis. No automorphy claim from this row alone (see rows 21, 23, 29) | — |
| 14 | **PIMS problem #22 (λχ race): the first numerical densities over Q**: δ(χ−4) ≈ 0.99995, δ(χ−8) ≈ 0.9088; bounds for χ−3 and χ5 | Conditional on GRH + LI **plus a tail hypothesis TH** (Σ_{γ>T} A² ≤ κ/T; κ = ½…4 reported), so not closed in the problem's own terms. Inputs certified | — |
| 15 | **Wei–Zhai non-vanishing conjecture (arXiv 2605.09251)**: all 18,434 Taylor coefficients c_m (r_n ≤ m ≤ 30) of L(E_n, s) at s = 1 certified nonzero, for all squarefree n ≤ 1000 (and n = 1254) | An unconditional finite check, replacing their RH-conditional sign rule for small \|d\|; super-positivity to k ≤ 30 for 608 curves; found a conductor error in their paper for gcd(d, 32) > 1. The sharper threshold is a remark (RH-conditional) | — |
| 16 | **Non-abelian Chebotarev races**: (a) infinitely many sign changes, unconditionally, for 14 S3/D4 races (Landau–Ingham + certified absence of real zeros + Arb witnesses); (c) exact first crossings (e.g. −23 1v2 at 1,954,553; x⁴−12 1vC[−4] at 1,456,919,293); for two D4 leaders, no crossing ≤ 10¹¹–10¹² | The method is classical (Staś et al.; Gallego in degree 1). The non-abelian application and the crossings appear new; Shanks–Lal 1972 (−108) not checked | — |
| 17 | **First Skewes-type regions for non-abelian races (no GRH, no LI)**: the D4 race 189, 1 vs C[21], flips somewhere in x ∈ [5.698·10⁷⁵, 1.549·10⁷⁶]; Ng's x⁴−12, 1 vs C[12], in [1.740·10⁷³, 4.732·10⁷³] | Ford–Hudson re-derived for Artin L-functions; zeros to height 450/500 certified (Booker–Turing). Independently verified (18 Oct 2026). For x⁴−12, 1 vs C[12]: no crossing ≤ 10¹³ (346,065,536,839 primes) | — |
| 18 | **Flagship field K = Q(x³−x−1), no GRH or LI (PIMS #17)**: for ψ_K(x) − x, limsup ≥ 3.126√x and liminf ≤ −3.606√x; at least 846,605 + 1,374 sign changes in [1, e⁴⁰⁰]; Littlewood's theorem for π_K; **the first x with π_K(x) > li(x) is 15,773**; certified regions where π_K > li near 6·10²⁰ and 10⁴⁷ | The method is classical (Staś, Kaczorowski–Staś, Lehman/Ford–Hudson); the hypotheses and numbers are new (provisional novelty). Lehman's 1966 ζ region reproduced | — |
| 19 | **RH certified in [10¹⁵, +2], [10¹⁶, +2], and a close pair (δ ≈ 0.098) at 10¹⁵ + 286.9** | See section 1. At these heights Arb's Turing isolation does the same about 4000× more cheaply; Odlyzko, Gourdon and Bober–Hiary went higher, non-rigorously. No priority claim is made for these heights | section 1 |
| 20 | **Bertrand's postulate for prime forms, unconditional, for all x**: for x ≥ 29.5, (x, 2x] contains a prime p = a² + ab + 6b²; primes inert in K from x ≥ 14.5; full Nagura table; for x ≥ 69,024, (x, 1.00584x] contains such a prime | Classical method plus certified GRH (10⁴) for the flagship field; enumeration to 10¹¹ with three-way classification checks. To our knowledge the first for a non-abelian class / non-congruence form; specialist check advised. Sharpened about 1.7–1.8× after the 2·10⁴ extension | — |
| 21 | **Artin's conjecture for 15 new S5 fields (d = 8249 … 38189)**: all hypotheses of Calegari (Math. Ann. 356, 2013, Thm 1.1/1.2) hold (Sasaki 2013 / Pilloni–Stroh supply the 2-dimensional input); ζ_H < 0 on (0,1) via the exact identity ζ_H·ζ·ζ_K = ζ_F·ζ_E·ζ_K10 plus certificates ⇒ every irreducible representation of Gal ≅ S5 is automorphic | Independently verified (19 Oct 2026); evaluator audited (no critical findings). Open: overlap with Dwyer 2014 unknown (paywalled). **Needs confirmation by an expert (Calegari)** | `artin_literal/` |
| 22 | **zfast / atlas_v5z**: window certificates in 8–16 s at 10¹²–10¹⁶ (previously up to 2.5 h), 0.2 GB; reproduces all earlier windows exactly; new RH windows [10¹⁷, +2] and [10¹⁸, +2] | zfast is an independent implementation (FLINT dfloat is prior art); independently reviewed 19 Oct 2026 (no critical findings). Turing counts for 10¹⁷/10¹⁸ added later (M8) | section 1, `zfast/review2/` |
| 23 | **Artin's conjecture extended to all 186 S5 (1,2) fields**: ζ_H < 0 on (0,1) for 186/186 (342/342 new runs); 15 via Calegari as published, 171 via Calegari + Pilloni–Stroh Thm 0.3 (as quoted by KLW; Pilloni–Stroh not read) | Needs expert confirmation for the 171-field route; evaluator audit passed; Dwyer overlap unknown. Includes Q(x⁵−x−1) (d = 2869) | `artin_all/RESULTS.md`, `general_eval/audit2/AUDIT.md` |
| 24 | **RH certified in [10²⁰, 10²⁰+2]** and a close-pair window at 10²⁰ | Reviewed; independent replay, 0 seams; later Lean audit and Turing cross-count | section 1 |
| 25 | **RH certified in [10²¹, +2] and [10²², +2]**, plus close-pair windows at 10²⁰ (δ ≈ 0.042, gap ≈ 0.006), 10²¹ and 10²² | Turing cross-count matches every window | section 1 |
| 26 | **RH certified in [10²³, 10²³+2] and [10²³+2, +4]**, 16 zeros each; close pair with gap 0.0133 | The first attempt failed closed (a determinism bug, not a soundness bug); fixed in v5z4, and all 92 earlier certificates recomputed equal. Turing count matches; Lean 0 violations | section 1 |
| 27 | **The naive Mertens-type conjecture is false for every cubic field** (HKMS Thm 1.2 made explicit: D_{1,2} ≤ 5177, D_{3,0} ≤ 5229; 1,144 fields below; the last six, −31, −59, 49, 81, 148, 229, certified in both directions) | Independently verified (21 Oct 2026): all 1,144 fields recomputed, all 117 integer-point fields, all 7 Ingham fields; the real-threshold margin is actually 0.40 | `mertens_cubic/RESULTS.md`, `mertens_cubic2/` |
| 28 | **Streaming evaluator (geval_stream)**: 418/418 enclosures character-identical to the frozen certificates; 55× faster and 10× less memory on the slowest Calegari field. New: S5 field d = 87,529, L(ρ5) ≠ 0 on (0,1); a sextic-field CM base-change curve (conductor norm 2401), L(E/K,1) = 2.335211822358 ± 5·10⁻¹³, Sha_an = 49 | Reviewed (21 Oct 2026, no critical findings); streamed runs may carry claims under the review's three conditions | `geval_stream/review/REVIEW.md` |
| 29 | **Artin's conjecture for S5 field d = 87,529** (5.1.87529.1), and the **sweep over all LMFDB S5 (1,2) fields with 2·10⁴ < d ≤ 132,536** | All Calegari hypotheses as published for d = 87,529. Sweep (final, corrected 1 Nov 2026): **2,256** fields certified in both parameter sets (130 via Calegari as published, 2,126 via Calegari + Pilloni–Stroh), 2 gaps that are not counterexamples; with rows 21/23 the total is **2,442** distinct fields (174 + 12 + 2,256). The Pilloni–Stroh route needs expert confirmation; Dwyer overlap unknown | `artin_sweep/RESULTS_FINAL.md`, `artin_sweep/review_gate_v2/REVIEW.md` |
| 30 | **geval_c (C core of the L-function evaluator)**: 28 certificate files reproduced character-identical; 5.7× faster at d = 87,529 (8.1× with 4 threads) | Reviewed (21 Oct 2026, no critical findings) | `geval_c/review/REVIEW.md` |
| 31 | **RH certified in [10²⁴, 10²⁴+2]** (17 zeros) and a close-pair window [10²⁴−3, 10²⁴−1] (16 zeros; certified closest pair δ ∈ [0.1196, 0.1209]) | Independent replay, Lean 0 violations; recorded miss: margin 0.616, below the predicted [0.67, 0.75] | section 1 |
| — | Later RH windows: [10²², 10²²+100] (777 zeros), [10²⁵, 10²⁵+100] (888), [10²⁶, 10²⁶+100] (924) | See section 1 | section 1 |

The October 2026 bundle in `data_release/` covers the earlier atlas_v4 work: ζ windows including Lehmer's pair and Rosser's
region; L(s, 11.a), 37.a1 and 389.a1 to height 200–300; and ζ_K/ζ for Tollis's 25 cubic fields. It has its own
certificates, Lean audit and `quick_verify.sh`.

## 3. How the work is checked

The work was built so that no step relies on trusting the code that produced it, or on trusting the AI that wrote that code.
Concrete practices, with examples:

- **Pre-registration before code.** Each claim-bearing milestone starts with a predictions file that is hashed before any
  source code or run exists. It records the expected zero count with a band, margins, cost, STOP conditions and negative
  controls. Results are scored MET or MISS against it, and misses are published.
  - Example: `zfast/PREDICTIONS_M11.md` (sha in `PREDICTIONS_M11.sha256`) predicted 924 zeros at 10^26 and 9.3 h. The result was
    924 zeros and 9.19 h.
  - Example of a recorded miss: at 10^24 the margin was 0.616, below the predicted [0.67, 0.75] (`zfast/RESULTS_M6.md`).
- **Builders never review their own work.** Every new evaluator version goes to a separate reviewer agent with fresh context. The
  reviewer gets a brief that treats the builder's results as claims to test, not as evidence. Reviewers rebuild the libraries
  and check that the binaries are byte-identical, run differential tests, and write their own attacks.
  - `zfast/review_v14b/REVIEW.md`, **MJ1**: the reviewer found that checkpoint-line MACs were not bound to their session. Lines
    spliced in from another session were accepted, and a wrong Z ball was demonstrated (6 of 6 trials). The production driver
    could not produce such a file. It was fixed in v14c and closed by the next review (72-case attack suite).
  - `zfast/review_v14c/REVIEW.md`, **MJ-C1**: the strict parser refused some honest Arb balls (radius mantissa of 30 bits), which
    would have made a long run impossible to resume. It was fixed in v14d and confirmed in `zfast/review_v14d/REVIEW.md` by a
    1.32-million-case oracle fuzz.
  - `zfast/review_m10/REVIEW.md`: the review of the libzfast v14 kernel and scheduler that produced the 10^25 and 10^26
    windows. It passed with conditions (no resume across library changes; separate checkpoints), and both runs met them.
  - Earlier reviews: `zfast/review2/REVIEW.md` (no critical findings), `geval_c/review/REVIEW.md`,
    `geval_stream/review/REVIEW.md`, `general_eval/audit2/AUDIT.md`.
  - The reviewers are separate AI agents (Claude Code sessions that did not write the code under review), not human experts.
- **Independent replay.** Every certificate is re-checked in a fresh process by replay code that shares no generator code. The
  replay rebuilds every model and row and recomputes Z, runs the sha-pinned verifier in plain and outward-hardened modes, checks
  the exact rational tiling of the window, and checks the claim (B) coverage.
- **Lean audit.** An exact exporter turns every certificate file into rationals, with no rounding. A Lean 4 checker, whose checks
  are proved correct in Lean against the certificate theorem, audits the files: `atlas_mark2/formal/` and
  `atlas_mark2/formal/audit/RESULTS.md`. The Lean project declares no axioms and uses no `sorry`. The analytic inputs appear as
  explicit hypotheses.
- **A separate count as a required gate.** A Turing count of the window comes from the generator's own Z grid
  (`zfast/tools/scan_turing5.py`, exact rational arithmetic) and must equal the number of certified sign changes. This gate was
  made mandatory after a negative control showed that a replay cannot detect a deleted zero: less credit still gives a valid
  certificate, so only the count catches it (`zfast/RESULTS_M7.md`, NC-W4; `engine/regress_v1/turing_gate.py`).
- **Fail-closed gates.** The first 10^23 attempt failed closed: a precision setting depended on run order, a determinism bug and
  not a soundness bug. It stays in the record as NOT CLOSED (`zfast/atlas_v5z3/runs/…/h_1e23`). After the fix (atlas_v5z4), all
  92 earlier certificates were recomputed and came out equal. The verifier here checks that this run is still found not closed.
- **Frozen pipelines and a regression harness.** Code is never edited once it has produced a result; each change is a new version
  (atlas_v5z → v5z2 → … → v5za; libzfast v9 … v14d). `engine/regress_v1/` re-runs the frozen replay logic on every stored window.
  It regenerates cheap windows bit for bit, runs pre-registered negative controls, and checks 68,153 frozen files against their
  manifests (`engine/regress_v1/RESULTS.md`).
- **Corrections are recorded, not erased.**
  - `atlas_mark2/diagnostic/CORRECTIONS_2026-10-06.md` is the project errata.
  - Example: the regression harness found that the Artin sweep headline of 2,259 fields did not reproduce. The stored data give
    2,256, and the correction is appended to `artin_sweep/RESULTS_FINAL.md`.
  - Example: a bug in the Turing-count tool (a non-integer Δ_T) was found in M7 and fixed in scan_turing5, and every stored count
    was recomputed (`zfast/RESULTS_M8.md`).
- **Safety rules in code.** Claim-carrying code refuses to start under `python -O` / PYTHONOPTIMIZE (which would strip its
  assertions). The verifier libraries are sha-pinned, and a library or OS change refuses a resume.

## 4. Verify it yourself

Requirements: Python 3.12 with `python-flint==0.9.0`, `numpy`, `scipy` and `mpmath` (`requirements.txt`), and about 0.5 GB of
free disk for outputs. The tested setup is macOS on Apple M1. The quick check does not call the compiled zfast library to
evaluate Z, but it does load it once, through the sha-pinned provider. That library (`libzfast.v*.dylib`, macOS arm64, linked
against Homebrew FLINT 3.6.0) is needed for the full replay below.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PY=.venv/bin/python ./verify/quick_verify.sh                 # about 5 minutes (measured 279 s on an M1), under 0.1 GB of memory
```

`quick_verify.sh` does the following:

1. Checks every file against `SHA256SUMS`.
2. For each of the 45 stored window runs, runs the frozen replay logic of that run's own code tree on every main and S-layer
   certificate, in plain and hardened modes, from the stored row measurements. The results (pass/fail and margin) must be
   bit-identical to the stored replay records.
3. Recomputes the exact tiling and the claim (B) coverage.
4. Recomputes the Turing count from the stored Z grid with the unchanged tool of record. The count must equal the number of
   certified sign changes (777, 888 and 924 for the wide windows).
5. Runs two negative controls (a tampered certificate and a wrong dual vector), which must be rejected.
6. Re-exports all 34 Lean datasets from the certificate files and requires byte identity with the stored datasets. If an
   `atlas_audit` executable is available, it re-runs the Lean audit and requires identical reports with 0 violations: set
   `ATLAS_AUDIT_BIN`, or build it with `cd atlas_mark2/formal && lake build atlas_audit`, using Lean v4.34.1. The executable
   uses core Lean only, though `lake` still resolves the Mathlib dependency.

What the quick check does not repeat is the evaluation of Z(t) and of the explicit-formula rows at height T0. Those values
come from the stored measurements. A **full replay** recomputes them with fresh zfast sessions on a scratch copy of a run:

```sh
PY=.venv/bin/python ./verify/full_replay.sh atlas_v5z  w100000000000000000/z_1e17               # about 15 s
PY=.venv/bin/python ./verify/full_replay.sh atlas_v5z7 w10000000000000000000000/wide7_1e22      # about 4.5 min (measured 262 s, 8 cores)
PY=.venv/bin/python ./verify/full_replay.sh atlas_v5z7 w100000000000000000000000000/wide7_1e26  # about 4.5 h on 8 cores
```

The frozen code contains a few absolute host paths. These files are sha-pinned and have not been edited. Instead,
`verify/boot/sitecustomize.py` rewrites only those path literals in memory as modules load, and it logs every loaded project
module so that the verifier can check that all of them came from this repository.

**Recorded result (3 November 2026, run from this repository copy on an Apple M1, 8 GB):** see `verify/RESULT_2026-11-03.txt`.
- quick_verify: every check passed (summary in that file).
- Full replay of [10^22, 10^22+100] from the repository copy: claims (A) and (B) passed, 100/100 main and 777/777 S-layer
  certificates, and 1,754/1,754 replay records identical to the stored replay of record. It took 262 s with peak memory
  0.11 GB, and no module was loaded from outside the repository.

## 5. Repository layout

```
README.md  LICENSE (MIT, code)  LICENSE-DATA (CC BY 4.0, data/certificates/docs)  requirements.txt  SHA256SUMS  PROVENANCE.tsv
verify/        quick_verify.sh, verify_windows.py, verify_lean.py, full_replay.sh, run_rewritten.py, boot/ (path bootstrap), recorded result
external/      exact_tiling_check.py (pinned, sha 0868990e…) + SLIVER_CHECK.md
data_release/  atlas_bundle_2026-10-08.tar.gz: the October 2026 bundle (atlas_v4 / degree-2 results; 25 MB)
docs/disclosure/  the AI-contribution questions and the answers received from OpenAI Codex and Google Gemini (October 2026)
atlas_mark2/   byte copies of the project tree at their original relative paths (PROVENANCE.tsv maps each file to its source and sha256)
  diagnostic/zfast/                       zfast evaluator (src/, bin/ = libzfast builds + their sources + SHA256 files), THEORY_*.md,
                                          PREDICTIONS_M*.md + .sha256, RESULTS_M*.md, MANIFEST_M*.sha256, novelty/, review*/,
                                          atlas_v5z … atlas_v5za (frozen pipelines, each with its runs/ and lean_audit/), tools/
  diagnostic/record_heights/              the first 10^15 / 10^16 windows (atlas_v5)
  diagnostic/certify_sech_interferometer.py, integer_mechanism.py   the explicit-formula row engine and the count bound (trusted)
  engine/regress_v1/                      regression harness, pre-registration, gates, reports
  formal/                                 Lean 4 + Mathlib project (without .lake/), exporter, audit data
  diagnostic/{flagship_K23,…,artin_sweep}/  result documents for section 2 (documents only)
```

Large Lean datasets are stored xz-compressed (`*.txt.xz`; the verifier decompresses them). No file is larger than 50 MB.

## 6. Trust base and caveats

- **Trusted, not proved here:**
  - Arb/FLINT via python-flint 0.9.0, for every ball enclosure;
  - libzfast, for the values of Z and of the rows (reviewed, not formally verified);
  - the explicit-formula row engine `certify_sech_interferometer.py` and the count bound in `integer_mechanism.py` (Trudgian's
    S(T) bound);
  - the Lean checker's parser.
- **Classical inputs:** Lemma 1 (a sign change ⇒ an odd-multiplicity zero on the line).
- **Atlas's own steps:** Lemma 2 and the S-layer theory (THEORY_V4 §10). Their logic is machine-checked in Lean, with the analytic
  facts as explicit hypotheses, but they have **no external review**.
- **Untrusted:** the generators, the LP solver (HiGHS), the sign-change search, and every measurement cache. None of these is a
  certificate input; the replay checks everything they produce.
- **Endpoints:** certified endpoints are the binary64 values stored. All windows above have integer endpoints, so this does not
  affect them.
- The reported certificate margin declines slowly with height (0.5806 at 10^22, then 0.5659 and 0.5629 at 10^25 and 10^26).
  The tight diagnostic bound stays near 1.05. Neither margin is near the failure level.

## 7. Authorship and AI disclosure

- **Philip Gordon** designed and directed the program. He set the hypotheses, the verification standards and the rules
  (pre-registration, independent review, no claim without replay and audit), and takes responsibility for the content.
- **All code in this repository was written and run by Claude Code (Anthropic).** This covers the pipelines, the zfast evaluator,
  the verifiers, the regression harness, the Lean formalisation and the reviews; the reviewers were separate Claude Code agents.
  Claude also derived the specific technical results within Phil's directions and drafted the documents.
- **OpenAI Codex and Google Gemini** were used as independent checkers of the mathematics and methodology.
- **Earlier involvement.** In the exploratory phase before 4 October 2026, which produced the earlier "Mark II workbench", Codex
  also wrote exploratory code and ran experiments. That code is not part of this repository's pipelines. Codex's and Gemini's own
  accounts of their contributions are reproduced unedited in `docs/disclosure/`, and the October bundle's README carries the same
  disclosure.
- **One inherited helper.** `external/exact_tiling_check.py` dates from the 4 October 2026 audit.
- The new mathematical arguments have not been reviewed by independent human experts. Everything needed to re-check the results
  without trusting the author or the AI is in this repository.

## 8. Licence

- **Code** (`*.py`, `*.sh`, `*.c`, `*.h`, `*.inc`, `*.lean`, build files): MIT License (`LICENSE`), Copyright (c) 2026 Philip
  Gordon. The exception is noted below.
- **Data, certificates and documentation** (certificate JSON, run records, logs, Lean datasets, Turing grids, the data-release
  archive, Markdown): CC BY 4.0 (`LICENSE-DATA`), same holder.
- **Third-party components keep their own licences:**
  - **FLINT/Arb** (LGPL-3.0-or-later). Section 3 of every `zfast.c` (`atlas_mark2/diagnostic/zfast/src/*/zfast.c`,
    `bin/src_*/zfast.c`, and the reviewers' mutant copies under `review*/mut/`) is adapted from FLINT's
    `acb_dirichlet_zeta_rs_r` (F. Johansson). Those files, and the `libzfast` / CLI binaries built from them, are therefore
    distributed under **LGPL-3.0-or-later**, not MIT. The binaries link dynamically to FLINT, GMP (LGPL-3.0+/GPL-2.0+) and MPFR
    (LGPL-3.0+), which are not bundled.
  - **python-flint** (MIT), **NumPy, SciPy** (BSD-3-Clause) and **mpmath** (BSD-3-Clause): dependencies, not bundled.
  - **Lean 4 and Mathlib** (Apache-2.0): dependencies named in `formal/lake-manifest.json`, not vendored.
  - **PARI/GP** (GPL-2.0+): used by the Artin and field pipelines, which are not in this repository; not bundled.
  - Reference papers and FLINT source files consulted during the work are **not** included, for copyright reasons.
    Citations: Bober–Hiary, arXiv:1607.00709; Hiary–Ireland–Kyi, arXiv:2408.00187; Platt–Trudgian, arXiv:2004.09765;
    Arias de Reyna, arXiv:2201.00342.

## Contact

Philip Gordon, phildgordon@me.com. Corrections, questions and expert review are very welcome.
