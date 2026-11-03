# Flagship results: RH for L(s, ρ) = ζ_K/ζ, K = Q(x³ − x − 1), d_K = −23, to height 10⁴ (2026-10-10)

Pre-registration: `PREDICTIONS.md` (sha256 7539a824…, recorded in `PREDICTIONS.sha256` before the first heavy process; re-verified OK at
launch). Code: frozen copies of `../deg2_fast/` (sha256s in `CODE_SHA256_FROZEN.txt`, identical to `../deg2_fast/SHA256SUMS`; nothing in
`deg2_fast/` or `new_territory/` was edited). Orchestration only: `run_flagship.py` (task queue), `launch.sh`, `post.py`, `spot_old.py`,
`mainterm.py`.

## 1. Claim

**Every zero of L(s, ρ) with |t| ≤ 10⁴ lies on the critical line Re s = 1/2 and is simple.** There are exactly 25 275 of them with
0 < t ≤ 10⁴ (mirror-symmetric, so 50 550 with |t| ≤ 10⁴).

Since ζ_K = ζ · L(s, ρ), and RH holds for ζ to 3·10¹² (Platt–Trudgian 2021), this gives **GRH for ζ_K up to height 10⁴**.
Previous: Tollis 1997, 93.81; Atlas (tollis), 200. To our knowledge this is the first rigorous verification of GRH to this height for
a non-Galois (non-abelian) number field's Dedekind zeta function. It is novel as far as we know, but we did not run an exhaustive search
of the literature.

Trusted: python-flint/Arb, ATAP Thm 8.2 (Chebyshev interpolation error), and the classical inputs listed in
`../new_territory/tollis/RESULTS.md`. The certificate logic is Lean-audited (`formal/`), with the hypotheses listed there. Independence
caveat above t = 700: see §4.

## 2. Pre-registered predictions against outcome

| # | prediction | outcome |
|---|---|---|
| P1 | 980/980 generator windows certify 20/20 cells | **980/980; 19 600/19 600 cells** |
| P2 | replay (fresh process, plain + hardened, zcheck Z1/Z2/Z3) passes everywhere | **19 600/19 600 cells pass both; 980/980 windows closed; 0 zcheck mismatches** |
| P3 | exact union [0, 10⁴] with the 20 tollis chunks [0, 200]: 0 gaps, 1 a_p sha | **0 gaps; 20 000 cells over 1 000 chunks; one a_p sha (c268c8da…ffa7b); one replay_verify sha (3aceb379…)** |
| P4 | Lean-flagged conditions (1)–(4): 0 violations | **0 / 0 / 0 / 0** over 20 000 certificates and 1 111 420 interval checks; 0 central reductions |
| P5 | 25 018 ± 3 sign changes in (200, 10⁴]; 25 275 ± 3 in (0, 10⁴]; every window within ±2 of the main term | **25 018 and 25 275 (exact hits)**. Largest per-window deviation 1.80; histogram of rounded deviations −2:2, −1:183, 0:589, +1:205, +2:1. S(10⁴) = +0.53, max \|S\| = 1.27 (at T = 3270), against a proven bound of ≈ 16.6: no violation |
| P6 | min hardened margin in [1.70, 1.90] | **1.7750** (window [9770, 9780]); max over windows 1.866 |
| P7 | old-evaluator spot checks E1: 20/20 pass | **20/20 pass** (§4) |
| P8 | 40–60 CPU-h, 16–20 h wall, < 0.6 GB per process | **45.8 CPU-h** for the pipeline (+ 4.8 CPU-h for E1); 15.6 h wall with 3 processes; max RSS 0.48 GB |

Every pre-registered prediction held, with one miss in a budget estimate: E1 cost 4.8 CPU-h against the predicted 0.5–1.5. It was still
below the 6 CPU-h ceiling, and all 20 points were run. No window failed, no task was retried, and no code or parameter was changed.

## 3. Run details

* Gate: started 2026-10-10 03:11 (when `doe/DOE_DONE` appeared). Finished 18:48. Three workers at nice 19.
* **Generator models:** 154 segments of length 64 on [194, 10 050] (φ = 30, 80-bit nodes, n = 384 at 10⁴, error 3.9e−21).
  * Cost: 5.94 CPU-h, from 6 s per segment at t = 200 to 266 s at 10⁴.
* **Global scan of [194, 10 016]:** 25 073 float sign changes, all 25 073 certified, 0 dropped. 333 s.
* **Replay models:** 154 segments (offset 32, φ = 45, target 1e−22, exact nodes). Cost: 10.22 CPU-h, 8 s to 478 s per segment.
* **Generator windows:** 15.40 CPU-h, 56–61 s each, independent of height.
* **Replays:** 14.16 CPU-h. They take 44–55 s each, except below 700, where the old evaluator runs at every endpoint (up to 188 s).
  * Endpoints checked: 110 016 by the replay's own models (Z1).
  * 4 046 by the frozen old evaluator (Z2: every endpoint ≤ 700).
  * 14 546 by the direct φ = 12 series (Z3: every 8th endpoint above 700).
* Memory: max RSS 0.48 GB (generator windows), 0.23 GB for replays, 0.14 GB for model builds. The footprint watchdog never fired.
  Note: its `footprint` readings were implausibly low (MB), so the memory figures quoted here are rusage max RSS.
* cubic_sweep: early in setup I created `cubic_sweep/runs/STOP`. The coordinator told me to leave it alone, and it then resumed stage 1
  itself. During the flagship run STOP was present, set by the main session, and no cubic_sweep process ran.

## 4. Independence, and the extra old-evaluator check (E1)

**Limitation.** Above t = 700 the replay's sign re-verification (Z1, own models) and the direct spot checks (Z3) use the same code
as the generator: `lfun_rot.py`, `chebz.py` and Arb gamma_upper. They differ in parameters (rotation, grid, nodes, degree), not in
code. A bug common to both rotations, such as one in Lemma B(ii) or Lemma S, would not be caught there. Code independence comes from
Z2 below 700, and from E1.

**E1 (pre-registered).** The OLD frozen evaluator `new_territory/deg2/lfun.py` (real-A Lavrik series: no rotation, no Lemma S, no
interpolation) was run with its own coefficient source `new_territory/deg2/forms.py` (the η(z)η(23z) product, not the Tollis type table).
* Points: the first certified endpoint after each of the 20 pre-drawn stratified points in [700, 10⁴].
* Precision: 96 + 2.3t + 32 bits for A = 1, +40 bits for A = 1.2.
* Result: **20/20 pass.**
  * At each point the A = 1 and A = 1.2 balls are strictly signed and overlap each other, the replay model and the generator model.
  * The old radii are about 1e−18 to 1e−27, against model radii of about 1e−13.
* Example, t = 9950.2678: old Z = 1.110950103e−8 ± 3e−18 (23 013 bits, 1 650 s), replay model 1.11095e−8 ± 7e−14.
* Cost per point grows from 2.2 s at t = 1010 to 1 650 s at 9950 (about t^2.8). Total 4.8 CPU-h. `spot/spot_*.json`.

## 5. Zero counts (diagnostic)

The main term is M(T) = (1/π)[T log(√23/2π) + Im log Γ(1/2 + iT)]. M(200) = 256.44 and M(10⁴) = 25 274.47.

The certified intervals in (0, 10⁴] number 25 275, collected over all 1 000 chunks with intervals of the same zero merged
(`explicit/extract_zeros_H1e4.py`). Of these, 257 lie in (0, 200], unchanged from tollis.
* First: γ₁ ∈ [5.1156833285, 5.1156833291].
* Last: γ ∈ [9999.8755977850, 9999.8755977860].
* Maximum width 9.5e−10.

The same count comes from the per-window midpoint rule: 25 018 in (200, 10⁴], which is 0.03 from the main-term difference.

## 6. Explicit theorems with H = 10⁴ (`explicit/`)

Copies of `../explicit_theorems/` (originals untouched). The differences are:
* the ρ zero input is `zeros_K23_H1e4.json` (25 275 ordinates);
* HEIGHT_ρ = 10⁴ and N_ρ(10⁴) = 50 550;
* the ρ fine grid runs to 50H = 5·10⁵ (the original used 10⁴ = 50 × 200).

All other inputs (I2–I10) are unchanged. The original H = 200 tables are kept in `explicit/H200/`.

The count N_ρ(10⁴) = 2 × 25 275 is read from the certificates the same way as I1 (N_ρ(200) = 514) in DERIVATION.md: one zero per
certified interval. That count agrees with the main term to S = 0.53.

**Theorem A**: certified ε (upper bounds, Arb), H = 10⁴ / H = 200.

| x0 | ε_e | ε_σ | ε_τ | ε_K (direct) | ε_K (via classes) |
|---|---|---|---|---|---|
| 10⁸ | **0.0105** / 0.0840 | **0.00855** / 0.0745 | 0.00498 / 0.00498 | **0.00513** / 0.0717 | **0.00776** / 0.0445 |
| 10⁹ | **0.00519** / 0.0810 | **0.00439** / 0.0719 | 0.00181 / 0.00181 | **0.00328** / 0.0710 | **0.00350** / 0.0414 |
| e²⁵ | **0.00287** / 0.0795 | **0.00262** / 0.0705 | 2.8e−4 / 2.8e−4 | **0.00249** / 0.0704 | **0.00158** / 0.0399 |
| e⁵⁰ | **0.00253** / 0.0773 | **0.00236** / 0.0686 | 3.5e−5 / 3.5e−5 | **0.00236** / 0.0686 | **0.00128** / 0.0387 |
| e¹⁰⁰ | **0.00249** / 0.0733 | **0.00232** / 0.0651 | 3.3e−5 / 3.3e−5 | **0.00232** / 0.0651 | **0.00126** / 0.0367 |
| e³⁰⁰ | **0.00232** / 0.0591 | **0.00214** / 0.0512 | 3.2e−5 | **0.00214** / 0.0512 | **0.00118** / 0.0295 |
| e⁵⁰⁰ | **0.00214** / 0.0461 | **0.00198** / 0.0388 | 2.0e−5 | **0.00198** / 0.0388 | **0.00108** / 0.0231 |
| e¹⁰⁰⁰ | **0.00171** / 0.0210 | **0.00155** / 0.0166 | 5.1e−6 | **0.00155** / 0.0166 | **0.00086** / 0.0105 |
| e²⁰⁰⁰ | **9.4e−4** / 2.97e−3 | **8.1e−4** / 2.19e−3 | 2.8e−7 | **8.1e−4** / 2.19e−3 | **4.7e−4** / 1.48e−3 |
| e⁵⁰⁰⁰ | 3.03e−5 / 3.08e−5 | 2.21e−5 / 2.24e−5 | 1.3e−9 | 2.21e−5 / 2.24e−5 | 1.51e−5 / 1.54e−5 |
| e⁹⁵⁵³ | 2.37e−7 (same) | 1.71e−7 (same) | 8.2e−12 | 1.71e−7 (same) | 1.18e−7 (same) |
| e⁴²⁹⁹⁰ | 4.53e−16 (same) | 3.25e−16 (same) | 1.15e−18 / 1.03e−20 | 3.25e−16 (same) | 2.27e−16 (same) |

* At moderate x every ρ-dependent constant improves by 25–30× (e.g. ε_K via classes at e²⁵: 0.0399 → 0.00158). This matches the c/H
  what-if of DERIVATION §9: the pre-registered prediction was 0.0031 at log x = 25 for the direct route; the result is 0.00249.
* ε_τ does not involve ρ zeros, so it is unchanged.
  * At e⁴²⁹⁹⁰ the new optimiser run returned a weaker (still valid) ε_τ, 1.15e−18 against 1.03e−20.
  * That is a float-optimiser artifact of `run_table.py`'s search, not an effect of H.
* Beyond log x ≈ 5000 the zero-free region dominates, and H no longer matters, as before.

**Theorem B (π form, x ≥ 10⁹)**, H = 10⁴ / H = 200:
* |π_e − Li/6| ≤ **0.00605** (0.0859) · (x/6)/log x;
* |π_σ − Li/3| ≤ **0.00492** (0.0760) · (x/3)/log x;
* |π_τ − Li/2| ≤ 0.00204 (0.00204) · (x/2)/log x;
* |π_K − Li| ≤ **0.00413** (0.0441) · x/log x.

At x ≥ e²⁵ these are 0.00328, 0.00296, 0.00039 and 0.00184.

**Corollary C (short intervals, x ≥ e²⁵):**
* (x, 1.00584x] contains a prime that splits completely in L (a² + ab + 6b²); before, it was (x, 1.173x].
* (x, 1.0053x] contains a prime inert in K; before, it was (x, 1.152x].

Files: `explicit/table_K23.json`, `pi_table_K23.json`, `corollaries_K23.json`, and the logs.

## 7. Files

* `runs/w_<a>/`: certificates, intervals, gen/replay summaries for 980 windows.
* `models_gen/`, `models_rep/`, `iv.json`: the shared models and the global scan.
* `logs/tasks.jsonl`: per-task CPU, wall time and RSS.
* `logs/post.json`: union, Lean-gap check and counts.
* `spot/`: E1.
* `leancheck/`: the symlink tree for the frozen `lean_gap_check.py`.

**Lean audit (2026-10-10):** the binary `atlas_audit` (formal/) on an exact export of all 20 000 certificates (980 windows + 20 tollis chunks): 0 violations, 20 000/20 000 per-certificate checks, 1 003/1 003 targets exactly covered including [0, 10⁴] × [0, 1/2]; 14/14 negative controls and 16/16 mutations caught. Numerical inequalities remain trusted Arb. Details: `formal/audit/RESULTS.md` (section "Flagship K23 to height 10⁴").

**Addendum 2026-10-10 (simplicity for ζ_K).** NOVELTY_CHECK.md noted that "simple" was proved for L(ρ) only. disjoint/RESULTS.md
certifies that ζ and L(ρ) share no zero with 0 < t ≤ 10⁴ (0 overlaps, min gap 3.7e-5), so every zero of ζ_K with |t| ≤ 10⁴
is on the line and simple. Use the wording recommended in NOVELTY_CHECK.md, now including simplicity for ζ_K.

## Addendum 2026-10-11: independence check (`independence/`)

Pre-registered in `independence/PREDICTIONS.md` (sha256 db9235ae…2fcf). Details are in `independence/RESULTS.md`. Nothing above this
addendum was changed.

**Suggested replacement for the §4 "Limitation" paragraph:**

> **Independence.** The certificates above t = 700 come from one code base: `deg2_fast`. Its replay (Z1) and spot checks (Z3) differ from
> the generator only in parameters. A bug common to both rotations would not be caught by them. Two code-independent checks now cover this range.
>
> (i) **Full list, non-rigorous.** A new evaluator (`independence/zfft.py`) shares no code with any Atlas evaluator. It uses numpy float64, the
> ray-Fourier/FFT method (Mellin integral of the weight-1 form along a ray), and coefficients counted as lattice points of the forms
> x² + xy + 6y² and 2x² + xy + 3y². It finds exactly 25 275 zeros in (0, 10⁴].
> * They match the 25 275 certified intervals one to one: every zero in exactly one interval, every interval with exactly one zero, and
>   equal counts in all 1 000 windows.
> * 25 271 lie strictly inside their interval, and the other 4 are outside by at most 3.6e−12.
> * PARI/GP 2.17.2 (lfundiv of Dedekind zetas) independently gives the same one-to-one match on all of (0, 3000] (6 433 zeros) and in
>   7 seeded windows above 3000.
>
> (ii) **Rigorous sample.** The old real-A Arb evaluator `new_territory/deg2/lfun.py` uses no rotation, no Lemma S and no Chebyshev
> models. It was run with η(z)η(23z) coefficients, checked equal to the lattice counts, and shares only Arb with deg2_fast. Both
> endpoints of 100 stratified-random certified intervals in [700, 10⁴] (seed fixed in advance) were evaluated with it.
> * 100/100 show strict opposite signs, consistent with the flagship models.
> * Each is an independent rigorous proof of a sign change in that interval. Together with E1 (20 points) this gives 220 independent
>   rigorous evaluations above 700.
>
> **What remains.** The *proof* of the full claim above 700 still rests on the deg2_fast code. An error that leaves every zero's position
> correct to 1e−11 but makes a certificate's error bound invalid is not excluded by (i). (ii) excludes it only at the sampled points.
> Within the limits of a floating-point check, (i) would have exposed any error that adds, drops or moves a zero by more than about
> 1e−11 anywhere in (0, 10⁴]. Examples: a wrong
> coefficient, a wrong rotation or contour lemma, a broken Lemma S step or a broken model. A fully code-independent *proof* of the whole range
> would need a second rigorous evaluator at height. The candidates are PARI-style precision growth (≈ 90 CPU-h just for the non-rigorous
> PARI list on [3000, 10⁴]), or a rigorous version of the ray-Fourier method.
