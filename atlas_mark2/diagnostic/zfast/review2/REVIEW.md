# zfast: independent adversarial review (review2, 2026-10-19)

**Scope.** The trusted evaluator zfast, exactly as used in the RH window certificates:
- **v10b** (`bin/libzfast.v10b.dylib`, sha 3daa33d5…; `bin/src_v10b/`) via atlas_v5z: the [10¹⁷, +2] and [10¹⁸, +2] certificates. Z comes from kind-0 M3 sessions; rows come from kind-1 sessions with polynomial weights.
- **v12a** (`bin/libzfast.v12a.dylib`, sha 70e1c317…; `bin/src_v12a/`) via atlas_v5z2: the two 10²⁰ windows (h_1e20 and hp_1e20), plus identical re-runs of the 10¹⁷ and 10¹⁸ windows. Z comes from kind-0 sessions; rows come from the same Z moments by the complex shift of THEORY_M5b.

**Method.** I read the source versions recorded in the freeze files, the theory files (THEORY_ZFAST, M3, M5, M5b, V5Z, V5Z2), the results files (RESULTS_M2/M3/M4) and FLINT 3.6's RS sources (`diagnostic/perf/ref_src/`).
- Both freeze files verify: every sha is OK.
- `src/v10b` and `src/v12` are byte-identical to `bin/src_v10b` and `bin/src_v12a`.
- The previous reviewer's directory `review/` was read only. Its references were reused only after I reviewed their source (`rv_ref.c`, which links only stock FLINT and shares no code with zfast).
- Everything new is in `review2/`. No production file was modified, and nothing was deleted or posted.
- Every compute job ran at nice 19 on one thread, one job at a time. Peak footprint was 393 MB (stock Arb at 10¹⁵).

## Verdict

**The 10¹⁷, 10¹⁸ and 10²⁰ certificates stand as far as zfast is concerned.**
- I found no soundness defect in either production version.
- Every rigorous bound in THEORY_ZFAST §§5–7 and §10, THEORY_M3 and THEORY_M5b was re-derived and matches the C code.
- Every independent comparison is contained, from 10¹⁰ to 10²⁰. The tests include N jumps, p = ±1/2, near-zeros down to |Z| = 4e-12, session edges and stress parameters.
- Every certified sign change at 10²⁰ is reproduced by the production library: h_1e20 42/42, hp_1e20 43/43.
- Mutation testing detects every error term that real data can expose. The terms it cannot expose are listed in section 4, with why each is still believed correct.

**Residual trust is unchanged from v5:** Arb/FLINT 3.6.0 [A] (θ, lgamma/digamma, the RS F/d coefficients, ball arithmetic) and the Arias de Reyna Thm 4.2 constants as implemented by FLINT (see m6).

## 1. Findings

**Critical: none.**

**Minor.** None of these affects a certificate.

- **m1. `ok = 0` row results are finite but wrong.**
  - Where: `zfm_row`, `zfm_row2`, `zfm_row3` and `zf_row` (`Hjet`).
  - Trigger: within about 1e-6 of an N jump, no box with ρ ≥ 2⁻²⁰ avoids the jump. `Hjet` then fails, H′ gets no Cauchy term, and the `&&` short-circuit skips the mirrored jet G entirely, so G₀ = G₁ = 0.
  - Observed: at T0 = 999998594275, u = u_jump ± 1e-9, `ok = 0` and P is off by 1.2e-6 against a radius of 1e-13. That is 20/200 battery quantities.
  - Why no certificate is affected: both production APIs return −3 and both providers raise RuntimeError on any rc ≠ 0. A wrong row can therefore never reach a certificate. Near-jump rows are refused, never certified.
  - Fix: set the outputs to indeterminate when `!ok`. Optionally split the box at the jump: H is analytic across jumps, so only the evaluation needs this.
- **m2. Session code lacks some single-point guards.** `zfm_new2` does not assert 2 ≤ J ≤ 32 (stack arrays have JMAX = 32), t > 1000 or N < 2⁵², which `zf_Z` does assert.
  - Production uses J = 12 and N ≤ 1.3·10¹¹, so nothing is affected.
  - Add the asserts before 10²¹+ use. N < 2⁵² holds up to about 10³².
- **m3. Rare build abort.** `mom_range` aborts ("mom block too short") if the part of a bucket left after the head has fewer than J + 1 = 13 terms. That happens when n_head lands within 12 of a bucket end, about 0.2 % per session. It is a crash, not unsound.
- **m4. Printed balls are coarser than computed.**
  - The APIs print with `arb_get_str(x, 40, 0)`, and the provider parses that string. Only digits inside the radius are printed and the radius is rounded up. Example at 10²⁰: radius 1.26e-9 is printed as 5.38e-9.
  - This is sound, but it wastes margin. The certified min |Z|/radius computed from printed balls is still 6682 (h_1e20) and 1706 (hp_1e20).
  - `ARB_STR_MORE` would keep the full ball. My driver uses it.
- **m5. Thread count changes midpoints.** The block partition depends on the thread count, so midpoints change with it. Each result is a valid ball, and it is reproducible for a fixed count.
  - The provider default is 2 (`ZFAST_THREADS`); the run scripts use 1.
  - Byte-identical replays need the same setting. No certificate depends on this.
  - The code has no shared mutable state: threads write only their own `R[i]`, FLINT caches are thread-local, and `flint_cleanup()` runs per thread. Earlier multi-thread repeat runs (`review/data/determinism.txt`) gave identical hashes per thread count. I did not re-run multi-thread tests because of the one-thread limit.
- **m6. RS remainder with σ < 0.** The rows' mirrored side has 1 − σ = −0.06 and −0.48. There FLINT's `zeta_rs_bound` uses c₁ = 1/2, and that value is not in the [ADR-II] quote cited by THEORY_ZFAST §3.
  - [ADR-II] p. 12 does state c₁/c ≤ 0.5·0.9^⌈−σ⌉/(2^{−σ}/π√2) for σ < 0, which is consistent with c₁ ≤ 1/2.
  - Stock Arb's own jets (v5's old row provider) evaluate R(1 − s̄) in exactly the same way (`zeta_rs.c`), so this is not new trust.
  - [ADR-I] itself is still unobtained. With K chosen so the bound is below 2⁻²⁰⁰, a constant error of 10³⁰ would not matter.

**Cosmetic**
- **c1. Rounding of bound constants.** Several mag bounds are formed from binary64 expressions rounded to nearest before `mag_set_d`, for example `3.03*u + ZF_EC`, the γ₁₅ expression and `(k+1)*u*1.0001*(1+ZF_EC)`. These can round down by a few ulps. The explicit slack absorbs this: 3.03u against the needed 3.01u, the factor 1.0001, and E_c = 4.88e-16 against my proved 3.15e-16.
- **c2. m_w bounds w*, not ŵ.** `m_w = mag_rsqrt(n0)` bounds w* but not ŵ ≤ w*(1 + 2.01u). The second-order deficit (about 2u·trig·m_w·X^k) is covered by the slack in e_w = 2.01u·m_w against the needed 2u/(1 − u). The theory should say this.
- **c3. Implementation-defined cast.** `(int64_t)` of a uint64 ≥ 2⁶³ in `cs_core` is implementation-defined before C23. It is two's complement on clang/arm64, which is what is intended.
- **c4. Pessimistic propagation term.** The rounding-propagation term Σ C(B−1, i)(2⁻²⁵⁷ + rad) is very pessimistic. High-order differences |D_i| < 2⁻²⁵⁷ round to 0, so their actual error is |D_i|. The best observed/bound ratio over 32 adversarial configurations is 0.05.
- **c5. Sessions are never freed.** The provider never frees sessions; the memory involved is negligible.

## 2. Re-derived bounds: all agree with the code

- **RS remainder.** `zf_rs_corr` is the FLINT 3.6 `zeta_rs_r` correction loop, line for line.
  - Differences: the main sum is omitted; the `wp` loop limit is 64·prec instead of 4·prec; and there is a `!acb_is_exact(s)` break for box inputs. These affect accuracy only.
  - The box-input use is rigorous: N must be unique over the box, the bound uses sup σ and inf t, and the f-coefficients are pure ball arithmetic.
  - The sign is (−1)^{N−1}, and p = 1 − 2(a − N), as in FLINT.
  - Z = 2Re(e^{iθ}(S + corr)) holds because χ = e^{−2iθ} on the critical line.
- **θ.** Computed by `acb_dirichlet_hardy_theta` at wp = 330 + bits(T0) + 4. In single-point Z, the radius of Θ enters ε₀. In sessions, θ enters only through e^{iθ} (Arb).
- **Phase.**
  - `fx_from_arb`: round-to-nearest gives an error ≤ 2⁻²⁵⁷ + rad, and the residue is ≥ 0 by `fdiv_r_2exp`.
  - Lemma 2: the loop runs in increasing i and reads E_{i+1} before it is updated. E_J is constant. The term for k is read before the update.
  - Theorem 1: C(k, i) ≤ C(B−1, i); Π|k − i| ≤ (B−1)^{J+1}; |f^{(J+1)}| ≤ τJ!/n0^{J+1}; truncation to the top limb loses less than 2⁻⁶⁴.
  - `block_setup` evaluates exactly this bound with upward mag operations: `mag_bin_uiui`, then the denominator via `mag_set_ui_lower`/`mag_pow_ui_lower`/`mag_mul_ui_lower`.
  - 2π: phases are carried in turns, so 2π enters only as Arb balls in τ = t/2π and Θ = θ/2π, plus K_TURN = fl(2π/2⁶⁴) inside the kernel. Its error is 0.351u, which my kernel bound uses.
- **Integer code.**
  - `fx_add`: each 128-bit partial sum is ≤ 2⁶⁵, and the top limb wraps mod 2⁶⁴ as intended.
  - `cs_core`: q ∈ {0..3}, and r ∈ [−2⁶¹, 2⁶¹) including the wrap case, so x ≡ q/4 + r/2⁶⁴ exactly.
  - The quadrant tables for cos and sin are correct.
  - No overflow is possible for N < 2⁵².
- **cos/sin kernel: my own interval proof** (`py/kernel_bound.py`).
  - Method: 65536 subintervals of |ŷ| ≤ 2⁶¹·K_TURN. The bound sums five parts: the running fma-Horner error, the binary64 coefficients against the exact Taylor coefficients (parsed from the C literals), T(ẑ) − T(ŷ²), the Taylor remainder, and the argument error with the actual K_TURN error.
  - Result: **E_cos = 3.146e-16 and E_sin = 3.153e-16, against ZF_EC = 4.88e-16. OK.**
  - Empirical check on the production `zf_cos2pi` and on the inlined `cos2pi_only`: 5.5·10⁵ inputs (random, quadrant edges, structured). The maximum error is 1.69e-16 (cos) and 1.72e-16 (sin).
- **No float contraction (disassembly of the production v12a dylib).**
  - Fused operations appear exactly where the source calls `fma`: 16 in `zf_cos2pi`; 32 in `z_range` (two inlined kernels); 34 in `row_range`; and in `mom_range`, 12 scalar fmadd for the two Horner6 evaluations plus 8 `fmla.2d`, which is the cos and sin Horner chains vectorised lane-wise with the same single rounding.
  - There is no other fmadd or fmla, so the compiler contracted nothing.
  - The build flags are `-ffp-contract=off -fno-fast-math`.
- **Term and summation.**
  - Weight: |ŵ/w* − 1| ≤ 2u/(1 − u).
  - Term: |t̂ − w*c*| ≤ w*(3.01u + E_c + 2πE_ph + O(u²)); the code uses 3.03u and the factor 7.
  - Groups of at most 16 terms from 0.0 need γ₁₅ (Higham recursive summation).
  - TwoSum is exact in RN for any operand order. The lo accumulation error is ≤ n_g²u²Σ|t̂|; the code uses the factor 2.
  - Σ|t̂| ≤ (1 + E_c)(1 + 3.1u)B/√n0.
  - Every accumulation is upward: mag_add/mul/mul_ui/pow_ui/div/rsqrt with lower-bounded denominators, `mag_sub_lower` in the 1/(1 − x) factors, and `arb_add_error_mag` into the Arb sums.
  - Block hi and lo are exact binary64 values entered by `arb_set_d`.
  - No underflow: z ≥ 2⁻¹²³ and the products are far above 2⁻¹⁰²².
- **Block-length cap.** `choose_B` is a heuristic only. Every bound uses the actual B, B ≥ J + 1 is asserted, and the tail absorption is covered by the same bound.
- **Rows, single point (THEORY_ZFAST §10).**
  - The analytic split is correct: H(z) = R(z) − Σ_{n≤N} n^{−z} with fixed N, and H̃(z) = conj H(1 − z̄).
  - The N(z) ≠ N correction sums in `Hfun` are correct.
  - The central-difference remainder is (M/ρ)(h/ρ)²/(1 − (h/ρ)²). The supremum M is taken over a box that contains the disc of radius ρ.
  - log χ = (s − 1/2)log π + lgamma((1 − s)/2) − lgamma(s/2), and χ′/χ = log π − (ψ((1 − s)/2) + ψ(s/2))/2.
  - ζ′ = S₁ + H′ + χ′(S₂ + G) + χ(S₃ + G′).
- **Weight and log polynomials (`weight_poly`, `logL_poly`).**
  - Coefficient recurrences are correct.
  - The Cauchy bounds hold on |z − c| ≤ c/2: |z^{−σ}| ≤ (c/2)^{−σ_lo}; |z^{σ−1}| ≤ (3c/2)^{σ_hi−1} for σ ≥ 1; |log z − L_b| ≤ max(|log(c/2) − L_b|, |log(3c/2) − L_b|) + π/6.
  - Horner rounding with fma is ≤ γ_D Σ|co_j|X^j; the code uses γ_{D+1}.
  - The argument x = k − (B − 1)/2 is exact.
- **M3 Lemmas M1 and M2.**
  - Lemma M1: |e^z − T_K(z)| ≤ |z|^{K+1}/(K+1)!·e^{|z|} for complex z.
  - G uses L_b·M_k + M_{k+1}, with the remainder multiplied by (|L_b| + X_b).
  - Lemma M2's four parts match `mom_range`: (k + 1) roundings ≤ (k + 1)u·1.0001; X = X_b + e_x; summation (1 + u)^{k+2} ≤ 1 + (k + 3)u.
  - The error is added to both Re and Im. V_b ≥ Σ|w|, from the head plus B·m_w per block.
  - The moment index layout is correct (q[0..3] = hi/lo of Re/Im). Blocks never cross a bucket edge.
  - The point-wise subtraction for n ∈ (N(t), N_w] is in Arb. Lemma M1 holds for every h, so the |h| ≤ H check concerns cost only.
- **M5b (complex shift).** These statements are correct:
  - h′ = h − ib for n^{−σ}, h″ = h + ib for n^{σ−1};
  - e^{−ih′ log n} = e^{−ih′L_b}·e^{−ih′(log n − L_b)};
  - the remainder is multiplied by an Arb upper bound of |e^{−ih′L_b}|;
  - the subtraction weights are n^{−1/2∓b};
  - S₂ and S₃ are conjugated.
- **Conversion and provider.**
  - `arb_get_str` → `arb(str)` contains the ball in 80000/80000 random round trips.
  - ctypes signatures match the C prototypes, `restype` is `c_void_p` for sessions, rc ≠ 0 raises, and the 4096-byte buffer overflow is detected (rc −2).
  - The verifier's offsets are binary64 values from JSON, so `float(u)` is the identity.
  - sech5's σ = 1/2 + π/(2·fl(a)) is the same real number on the kernel side (`arb(a)` of the same float) and in zfast.

## 3. Adversarial tests against independent references

References come from `bin/ref`, a compiled byte copy of `review/src/rv_ref.c`, which links only FLINT:
- **AZ:** stock `acb_dirichlet_hardy_z`.
- **AR:** stock `acb_dirichlet_zeta_jet`, giving P = Re(−ζ′/ζ).
- **GZ:** Arb `powsum_smooth` main sum, plus Gabcke's C₀ and C₁ with the R₁ < 0.053 t^{−5/4} bound. This correction is independent of the ADR/FLINT code that zfast copies. GZ agrees with AZ at 10¹⁷ and 10¹⁸ to 1e-23.

**Test** means a zfast ball is checked against an independent reference: it must contain the reference midpoint and overlap the reference ball.

| family (production v12a; v10b in brackets) | points | result | max \|diff\|/radius |
|---|---|---|---|
| session Z, production parameters, 10¹⁰–10¹⁵. Points: random; session edges \|h\| = 4; N jumps at 0, ±1e-12, ±1e-9, ±1e-6; p = ±1/2; bisected near-zeros, \|Z\| down to 4.4e-12 (below the radius) | 186 [130] | all contained | 4.4e-4 |
| single-point Z: production parameters plus J6 / log2i −20 / bmax 2¹⁶, J24 / bmax 2¹⁶, J8 / bmax 64, kcorr = 2 at t = 1500–10⁵ | 16 | all contained | 5.5e-3 |
| Taylor-stressed sessions: K = 2–5, Δ = 0.4–0.6, 1500 ≤ T0 ≤ 10¹² | 104 | all contained | 0.17 |
| rows, complex shift (v12a): 10¹⁰–10¹³ and an N-jump window (P, ζ, ζ′) | 200 | 180 contained, 20 refused (ok = 0; m1) | 2.1e-4 |
| rows, kind-1 polynomial weights (the v10b path) | 140 [140] | 120 contained, 20 refused | 2.0e-4 |
| Taylor-stressed rows (both paths) | 600 | all finite balls contained | 0.19 |
| phase blocks at 10¹⁰–10²² (J = 6–24, B up to 16384) | 6 + 32 scan | all within E_ph | 1.0 (2⁻⁶⁴ floor) |
| weight/log polynomials (4 kinds × 5 blocks) | 30 | all within bound | 0.22 |
| **high heights, both libraries:** Z at 10¹⁶ (7), 10¹⁷ (16), 10¹⁸ (8), 10¹⁹ (2), 10²⁰ (3) against GZ/AZ; rows at 10¹⁷ (2) and 10¹⁸ (1) against AR | 39 + 39 | **78/78 contained** | – |

**At 10²⁰ (Arb `powsum_smooth`, about 19.5 min per point):**
- The two points are the smallest-|Z| certified endpoint (Z = 3.5946e-5) and the smallest-|Z| in-target endpoint. zfast differs from Arb by 1.5e-15 and 3e-16, against a radius of 1.1–1.3e-9.
- Rows at 10²⁰ have no stock-Arb reference that fits the memory and time limits. Three zfast code paths (complex shift S3, kind-1 polynomial weights S1, single-point `zf_row`) give pairwise-overlapping balls for P, ζ and ζ′ at 3 offsets × 2 kernels, with midpoints within 1.4e-17. These paths share only the Arb-side H, H′ and χ code.
- Certified-sign replay with the production v12a library: h_1e20 42/42 intervals with opposite decided signs (min |Z|/radius 6682), and hp_1e20 43/43 (1706). At 10¹⁷ and 10¹⁸, the v5z (v10b) and v5z2 (v12a) certificates have byte-identical interval lists and min_candidate_lower values.

## 4. Mutation testing (copies in `mut/`, drivers `bin/rd4.<name>`; production sources only read)

Each mutant shrinks one bound by 10×, except the five logic-bug controls. The battery is the light version, without 10¹⁴ and 10¹⁵. With the corrected scoring, the production build passes every family.

**Detected (13 of 23):**

| mutant | detected by |
|---|---|
| E_c / 10 | kernel test |
| 2⁻⁶⁴ floor / 10 | phase test (5/6) |
| interpolation / 10 | phase test (2/6) |
| weight_poly e / 10 | WP (12/30) |
| logL_poly e / 10 | WP (3/30) |
| M3 Taylor remainder / 10 | stressed Z sessions and kind-1 rows |
| M5b complex-shift remainder / 10 | stressed rows |
| V_b / 10 | stressed Z and rows |
| controls: quadrant sign, tail start Nt + 2, ws sign in subtraction, h′ sign, missing conj of S₂ | all detected |

**Not empirically testable at 10× (10 of 23).** Their correctness rests on the derivations in section 2.

| mutant | why it cannot be detected |
|---|---|
| 2⁻²⁵⁷ + rad propagation | best observed/bound is 0.05 (c4) |
| 3.03u per term | a-priori worst-case bound against random-walk rounding |
| γ₁₅ + n_g² summation | same reason |
| 7·E_ph in Z | E_ph ≈ 5e-20 is negligible |
| RS Thm 4.2 remainder | below 2⁻¹⁰⁰ at the chosen K, and loose even at kcorr = 2 |
| Hjet Cauchy term | (h/ρ)² = 2⁻⁷⁰, so the true truncation is about 1e-36 |
| whole moment-block bound, its trig part, its summation part | about 10³–10⁴ slack, as the earlier reviewer's /10³ vs /10⁵ slack runs found |
| the \|e^{−ih″L_b}\| factor for the W sum | its error is multiplied by \|χ\| ~ N^{1−2σ} and never dominates the final ball |

The measured overall slack (radius / actual error) is about 2·10³ to 5·10³ for Z and rows at production parameters.

## 5. Notes for 10²¹ and above

- Nothing in the analysis depends on height except τ in the interpolation term, which is controlled by the actual-B bound, and wp = 330 + bits(T0). N < 2⁵² holds to about 10³².
- Before relying on 10²¹+, add the m2 asserts and make `ok = 0` outputs indeterminate (m1).
- Keep a few Arb `powsum_smooth` references: about 1.1 h per point at 10²¹, 4 MB. `run_ref.sh` here is not needed; `bin/ref` with GZ lines does it.

## Files (all in `review2/`)

- **Scripts:**
  - `py/kernel_bound.py`, `data/kernel_bound_*.json` (kernel proof);
  - `py/kernel_emp2.py`, `data/kernel_emp.jsonl`;
  - `data/v12a_disasm.txt` (disassembly);
  - `src/rd4.c` (driver: one translation unit with the production or a mutant `zfast.c`);
  - `py/bat2_prep3.py`, `py/bat2_extra.py` (points), `py/bat2_ref.py` (references), `py/bat3_run.py` (battery);
  - `py/make_mut.py`, `mut/*/MUTATION.txt`;
  - `py/high_cmp.py`, `py/ep_check.py`, `sess_points.py`.
- **Results:**
  - `data/bat3_prod_v12a.json`, `data/bat3_prod_v10b.json`, `data/bat3_mut_*.json`, `data/bat3_mut_summary.txt`;
  - `data/high_cmp.jsonl`, `data/ref_1e20_GZ.jsonl`, `data/v12a_h1e20_endpoints.jsonl`, `data/v12a_hp1e20_endpoints.jsonl`;
  - `data/rows1e20b.jsonl`, `data/rows1e20_consistency.txt`;
  - `data/ph_scan.jsonl`.
- **Superseded, kept:**
  - `data/bat2_*.json`: scored `ok = 0` and non-finite balls as failures, which made every run "detected".
  - `bin/rd2*`, `bin/rd3.*`, `src/rd2.c`, `src/rd3.c`: rd3 printed balls without `ARB_STR_MORE`, so its radii were inflated up to about 5× (m4); its containment results remain valid.
  - `zlib.py`: a misnamed copy of `zfl.py` that shadows the standard-library zlib module when scripts run from `review2/`. The scripts in `py/` avoid it.
  - `data/bat2_prep.log`: from a stopped run.
