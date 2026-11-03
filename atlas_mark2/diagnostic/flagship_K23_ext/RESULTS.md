# Flagship extension: RH for L(s, ρ) = ζ_K/ζ, K = Q(x³ − x − 1), d_K = −23, from height 10⁴ to 2·10⁴ (2026-10-23/27)

Pre-registration: `PREDICTIONS.md` (sha256 5c4797bd…418650, `PREDICTIONS.sha256`, re-verified OK against the file on disk). Code:
frozen copies of `../deg2_fast/` (sha256s in `CODE_SHA256_FROZEN.txt`, identical to `../deg2_fast/SHA256SUMS`; nothing in `deg2_fast/`,
`flagship_K23/`, `zfast/`, `new_territory/` was edited). Orchestration only: `run_ext_v1.py` (superseded by `run_ext_v2.py` after v1's
post-chain script names were found wrong), `spot_old_ext.py`, `post_ext.py`, and the post-chain copies in `explicit_H2e4/`,
`bertrand_H2e4/`, `disjoint_H2e4/`.

## 1. Claim

**Every zero of L(s, ρ) with |t| ≤ 2·10⁴ lies on the critical line Re s = 1/2 and is simple.** There are exactly **54 962** of them
with 0 < t ≤ 2·10⁴ (mirror-symmetric, so 109 924 with |t| ≤ 2·10⁴); of these, 25 275 lie in (0, 10⁴], reproducing the flagship run
exactly, and **29 687** are new, in (10⁴, 2·10⁴].

The union of certificates is exact and contiguous over the whole range: 2 000 chunks (20 tollis chunks [0, 200] + 980 flagship windows
[200, 10⁴] + 1 000 new windows [10⁴, 2·10⁴]), 40 000 cells, **0 gaps**, one a_p table sha (c268c8da…ffa7b), one replay_verify sha
(3aceb379…) — the same two shas as the 10⁴ run, so nothing about the certified arithmetic changed between the two runs.

ζ/L(ρ) disjointness to 2·10⁴ (Arb `zeta_zeros`): **0 clashes** between the 54 962 certified L(ρ) intervals and 22 491 ζ zeros,
min gap 7.19e−6. Combined with Platt–Trudgian (RH for ζ to 3·10¹²), this gives **every zero of ζ_K with |t| ≤ 2·10⁴ on the line and
simple, i.e. GRH for ζ_K up to height 2·10⁴.**

Lean-flagged conditions (1)–(4) of `formal/README.md`, checked on a symlink tree of all three groups (tollis + flagship + extension):
**0 / 0 / 0 / 0 violations** over 40 000 certificates and 2 417 440 interval checks, 0 central reductions.

Old-evaluator spot checks (E1 protocol, 10 pre-drawn stratified points in [10⁴, 2·10⁴], code-independent of the generator/replay above
t = 700): **10/10 pass** (`spot/spot_0.json` … `spot_9.json`). At every point the OLD frozen evaluator (radii ≈ 1e−18 to 1e−27) and
the replay/generator models overlap with the same sign.

Trusted base, independence caveat and formal audit scope are unchanged from the 10⁴ run (§4 below).

**Novelty wording (kept from `../flagship_K23/NOVELTY_CHECK.md`, height and factor updated).** To our knowledge this remains the first
interval-arithmetic-certified verification of GRH for this field beyond Tollis's 93.81 (Math. Comp. 1997), and it now exceeds the
highest previously published verification claim for this field — Ng's floating-point check to height 972.2 (PhD thesis, UBC 2000,
§4.3.5) — by a factor of about **21** (2·10⁴ / 972.2), against a factor of about 10 for the 10⁴ run. The same avoid-list applies
("highest height ever computed"; "first verification above Tollis"; "every zero of ζ_K is simple" without the disjointness check above;
citing Platt–Trudgian for simplicity of ζ's zeros).

## 2. Pre-registered predictions against outcome

| # | prediction | outcome |
|---|---|---|
| P1 | 1 000/1 000 generator windows certify 20/20 cells (20 000 certs) | **1 000/1 000; 20 000/20 000 cells** |
| P2 | every replay passes: 20 000/20 000 cells, closed, 0 zcheck mismatches | **20 000/20 000 cells pass both; 1 000/1 000 windows closed; 0 zcheck mismatches** (110 302 Z1 endpoints, 17 692 Z3) |
| P3 | exact union [0, 2·10⁴], 0 gaps, 2 000 chunks, 40 000 cells, one a_p sha, one replay_verify sha | **met exactly** (see §1) |
| P4 | Lean-flagged conditions: 0 violations over 40 000 certs | **met exactly** (0/0/0/0, 2 417 440 interval checks) |
| P5 | 29 687 ± 3 new sign changes in (10⁴, 2·10⁴]; 54 962 ± 3 total; every window within ±2 of main term | **29 687 exact hit; 54 962 total exact hit.** Largest per-window deviation 1.94; histogram −2:8, −1:212, 0:571, +1:202, +2:7. S(2·10⁴) = +0.34, max \|S\| = 1.40 (at T = 19 650), against a proven bound ≈ 17.0: no violation |
| P6 | min hardened margin in [1.70, 1.80] | **1.773** (window a = 18 680); max over windows 1.788 |
| P7 | regression on window [10 000, 10 010] vs the flagship run's own grid | **exact match**: 62/62 intervals, endpoint shift 0.0, margins identical (1.7832104259042796 both sides), 20/20 cells |
| P8 | old-evaluator spot checks (E1, 10 points): 10/10 pass | **10/10 pass** |
| P9 | disjointness to 2·10⁴: 0 overlaps, min gap > 1e−8; N_ζ(2·10⁴) = 22 537 ± 2 | **Disjointness held: 0 overlaps, min gap 7.19e−6** (slightly below the 1e−8 floor stated as a prediction, not a requirement — still > 0, so no clash). **The N_ζ sub-prediction missed**: Arb's `zeta_zeros` count is **22 491**, 46 below the predicted 22 537 ± 2 and outside that band. The Riemann–von Mangoldt main term N(T) ≈ (T/2π)ln(T/2πe) + 7/8 gives 22 494.4 at T = 2·10⁴ — essentially the observed count — so the *prediction's* N_ζ estimate was in error, not the certification; the disjointness claim itself (which only needs the two sets to not overlap) is unaffected. |
| P10 | cost: pipeline 70–100 CPU-h, wall 3–4.5 days, spot 25–45 CPU-h, peak RSS < 0.6 GB, new disk < 0.4 GB | **Pipeline 85.3 CPU-h** (gseg 18.17 + rseg 33.47 + gen 16.09 + rep 17.48 + scan 0.10), **spot 24.0 CPU-h** (below the predicted band — cheaper than expected), **total 109.5 CPU-h**; **wall ≈ 108.6 h (4.53 days)**, first task 2026-10-23 01:52:38 to last 2026-10-27 14:35:32; **peak RSS 449.8 MB**; **new disk ≈ 234 MB** (runs/ 207 MB + models 5 MB), matching the ≈ 0.21 GB/1 000-window estimate almost exactly. |

Every prediction held except the N_ζ(2·10⁴) count in P9 (a diagnostic estimate, not part of the certified claim), which missed by 46
against a stated ±2 band. No window failed, no task was retried for a certification reason (see §3 for the two operational retries),
and no code or parameter was changed mid-run.

## 3. Run details and deviations from plan

* Started 2026-10-23 01:52 (v1 runner; v1 built only `models_gen/seg_10050...json`, then was stopped because its post-chain script
  names were wrong — see `RESUME.md`). Resumed under `run_ext_v2.py` (single worker, nice 19, every subprocess under
  `wd_fp.sh` FP_MB = 700), which produced everything reported here. Finished (`post` task) 2026-10-27 14:35.
* **Deviation from plan (operational, not a result): the coordinating agent died partway through the run.** The worker
  (`run_ext_v2.py`, launched via `launch_ext.sh`, resumable by design — a task is "done" once its output file exists) continued
  running unattended; nothing in the pre-registered pipeline or its parameters was touched while unsupervised, and `run_ext_v2.py
  status` now reports the full contiguous replayed prefix [10 000, 20 000] with every stage (gseg/rseg/scan/gen/rep/spot/post/
  extract/disjoint/table/pi/cor/bertrand) at "done N/N, failed-attempts 0". This is consistent with the resumability design in
  `RESUME.md` and introduces no uncontrolled change to the certified pipeline.
* Order of work followed `RESUME.md`: 16 blocks of 640 units each (generator segments → block scan → replay segments → generator
  windows → replays), old-evaluator spot checks interleaved as each window closed, then the deterministic post-chain
  (post → extract → disjoint, table → pi → cor, table → bertrand).
* `logs/tasks.jsonl`: 2 346 task records, 0 non-zero return codes recorded. Per-stage CPU: gseg (156 segments) 18.17 CPU-h, rseg
  (157) 33.47 CPU-h, scan (16) 0.10 CPU-h, gen (1 000 windows) 16.09 CPU-h, rep (1 000) 17.48 CPU-h, spot (10) 24.01 CPU-h, post-chain
  (post/extract/disjoint/table/pi/cor/bertrand) < 0.1 CPU-h combined. Peak RSS over all 2 346 tasks: 449.8 MB (below the 700 MB
  watchdog ceiling and the 0.6 GB prediction).
* Free disk at the end of the run: 1.3 GB (per `run_ext_v2.py status`); the run added ≈ 234 MB on disk.

## 4. Independence (unchanged from the 10⁴ run)

Above t = 700 the replay's Z1 (own models) and Z3 (direct φ = 12 series) share code with the generator (`lfun_rot.py`, `chebz.py`,
Arb `gamma_upper`); they differ in parameters, not in code. Code independence above 700 rests on the regression argument of
`../deg2_fast/THEORY_FAST.md` §6, the flagship run's E1 (20 points) and Tier-2 (100 intervals) checks, and the 10 new E1 points
reported here. A fully code-independent proof of the whole [0, 2·10⁴] range is not claimed. The non-rigorous full-list FFT
independence check (`../flagship_K23/independence/zfft.py`) was **not attempted** for the extension: its footprint was expected to
exceed the 700 MB watchdog ceiling at 2·10⁴ (≈ 1.1 GB, against 0.58 GB at 10⁴), as flagged in `PREDICTIONS.md` §4, and this is
reported as a known gap, not run around.

## 5. Explicit theorems: improvement from H = 10⁴ to H = 2·10⁴ (`explicit_H2e4/`)

Same inputs as `../flagship_K23/explicit/` (I2–I10 unchanged), with the ρ-zero input replaced by `zeros_K23_H2e4.json` (54 962
ordinates), HEIGHT_ρ = 2·10⁴, N_ρ(2·10⁴) = 109 924, and the ρ fine grid to 50H = 10⁶.

**Theorem A, certified ε (Arb upper bounds), H = 10⁴ → H = 2·10⁴:**

| x0 | ε_e | ε_σ | ε_τ | ε_K (direct) |
|---|---|---|---|---|
| 10⁸ | 0.01054 → **0.00985** | 0.00855 → **0.00789** | 0.00498 (unchanged) | 0.00513 → **0.00440** |
| 10⁹ | 0.00519 → **0.00429** | 0.00439 → **0.00349** | 0.00181 (unchanged) | 0.00328 → **0.00232** |
| e²⁵ | 0.00287 → **0.00173** | 0.00262 → **0.00155** | 2.78e−4 (unchanged) | 0.00249 → **0.00141** |
| e³⁰ | 0.00258 → **0.00140** | 0.00240 → **0.00131** | 5.49e−5 (unchanged) | 0.00239 → **0.00130** |
| e⁵⁰ | 0.00253 → **0.00136** | 0.00236 → **0.00128** | 3.45e−5 (unchanged) | 0.00236 → **0.00128** |
| e¹⁰⁰ | 0.00249 → **0.00134** | 0.00232 → **0.00126** | 3.34e−5 (unchanged) | 0.00232 → **0.00126** |
| e¹⁰⁰⁰ | 0.00171 → **0.00097** | 0.00155 → **0.00089** | 5.09e−6 (unchanged) | 0.00155 → **0.00089** |
| e⁹⁵⁵³ and beyond | unchanged (zero-free region dominates, not ρ-zeros) | | | |

ε_τ does not involve ρ-zeros and is unchanged at every x0, as predicted. The ρ-dependent constants improve by a factor of
**1.6–1.8** at moderate x, matching the 1.7–1.8 predicted in `PREDICTIONS.md` §5 (and short of the naive c/H factor of 2, for the
reasons given there: the ζ/χ terms and the smoothing defect now take a larger share).

**Theorem B (π form, x ≥ 10⁹), H = 10⁴ → 2·10⁴:**
* |π_e − Li/6| ≤ 0.00605 → **0.00511** · (x/6)/log x;
* |π_σ − Li/3| ≤ 0.00492 → **0.00397** · (x/3)/log x;
* |π_τ − Li/2| ≤ 0.00204 (unchanged) · (x/2)/log x;
* |π_K − Li| ≤ 0.00413 → **0.00366** · x/log x.

**Corollary C (short intervals, x ≥ e²⁵), H = 10⁴ → 2·10⁴:**
* (x, 1.00584x] → **(x, 1.00353x]** contains a prime a² + ab + 6b² (splits completely in L), for every x ≥ **≈ 137 863**
  (controlling pair 137 633 → 138 349, ratio 1.0052022; `bertrand_H2e4/thresholds_H2e4.json`, class e, last staircase entry);
* (x, 1.0053x] → **(x, 1.00315x]** contains a prime inert in K, for every x ≥ **≈ 68 229**
  (controlling pair 68 227 → 68 443, ratio 1.0031659; class σ).

All four numbers (h_e, h_σ and both controlling pairs) were obtained from the certified table, not the `whatif_H_v2.py` float
estimate; they match that pre-registered estimate to 3 significant figures (predicted h_e ≈ 0.00353, h_σ ≈ 0.00314; certified
0.0035283 and 0.0031485).

Files: `explicit_H2e4/table_K23.json`, `pi_table_K23.json`, `corollaries_K23.json`; Bertrand: `bertrand_H2e4/analytic_h_H2e4.json`,
`thresholds_H2e4.json`. No new enumeration of a² + ab + 6b² / inert-prime pairs was needed: the existing exact pair list to 10¹¹
(`../bertrand_forms/runs/pairs_1e11.txt`) already covers both controlling pairs.

## 6. 5·10⁴ and beyond: not attempted (unchanged decision)

As pre-registered, 5·10⁴ would cost ≈ 600–700 CPU-h with this pipeline (outside the ~30 CPU-h-per-step guideline by a wide margin)
and was not attempted. 2·10⁴ itself, at ≈ 109.5 CPU-h total, ran somewhat over the 83 CPU-h pipeline estimate but under the combined
118–123 CPU-h pipeline+spot estimate, mainly because the spot checks (24.0 CPU-h) came in cheaper than predicted (35–40 CPU-h).

## 7. Files

* `runs/w_<a>/`: certificates, intervals, gen/replay summaries for the 1 000 new windows [10⁴, 2·10⁴).
* `models_gen/`, `models_rep/`: the shared segment models for the extension (the two boundary segments are copied from the flagship
  run, shas recorded in `CODE_SHA256_FROZEN.txt`).
* `logs/tasks.jsonl`: per-task CPU, wall and RSS (2 346 records). `logs/post_ext.json`: union, Lean-gap check, counts, regression.
* `spot/spot_0.json` … `spot_9.json`: the 10 E1 old-evaluator checks.
* `leancheck/runs/{flagship,flagship_ext,tollis_K23_contig}/`: the symlink tree for the frozen `lean_gap_check.py`.
* `explicit_H2e4/`, `bertrand_H2e4/`, `disjoint_H2e4/`: the post-chain outputs described in §§1, 5.

## 8. Caveats (carried over from the 10⁴ run)

* Independence above t = 700 is parameter-independence only, not code-independence (§4); the FFT full-list check was not run at this
  height (footprint).
* Trusted base: python-flint/Arb, ATAP Thm 8.2, the classical inputs of `../new_territory/tollis/RESULTS.md`; certificate logic
  Lean-audited in `formal/`; numerical inequalities trusted to Arb.
* Novelty is "to our knowledge", per the search scope recorded in `../flagship_K23/NOVELTY_CHECK.md`; no exhaustive literature search
  was redone for this extension.
