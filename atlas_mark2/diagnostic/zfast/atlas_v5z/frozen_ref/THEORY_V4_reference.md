# atlas_v4 — what is proved and how it is assembled (written before the production code, 2026-10-07)

v4 keeps the certificate theory of `zsign/THEORY_ZSIGN.md` (Theorem, Lemma 1) and atlas_v3 Lemma 2 (parity ⇒ simplicity), and the
unchanged, sha-pinned verifier `verify_zs.py` (`ed5bc621…`). Every change below is to the *inputs* of that theorem (the model, the rows,
which regions a certificate claims) or to the *assembly*. Each section states the change, why it is sound, and what checks it.

Notation as in THEORY_ZSIGN.md: atoms a = (x, d, f); var boxes (H_model); rows with bounds (H_rows); count Nwin (H_count); sign-change
intervals I_i with weights w_i ≥ 0; Φ, Φ_w, K; conditions (R) on every var box and (C) on the candidate region.

## 1. The all-open model (replaces base ledgers, off-centre unions and propagation)

**Change.** For a window W = [e(k0), e(k1)], e(k) = T0 + k·0.01 (the v3 float expression), the model has, for every bin
[e(k), e(k+1)] ⊂ W, one box `on` [lo,hi] × {0} (f = 1) and one box `off` [lo,hi] × [0, 1/2] (f = 2). Nothing else is assumed.

**Why (H_model) holds.** Every nontrivial zero ρ = β + iγ has 0 < β < 1 (ζ(1+it) ≠ 0 and the functional equation), so
d = |β − 1/2| < 1/2. A zero with γ ∈ W lies in at least one bin (closed bins cover W). An on-line zero of multiplicity k is k atoms in that
bin's `on` box. An off-line zero ρ (d > 0) of multiplicity m has the partner 1 − ρ̄ (same γ, same d, same multiplicity), and the m pairs are
m atoms (γ, d, 2) in the `off` box [lo,hi] × [0, 1/2]. So every atom lies in a var box. No ledger, union or propagation certificate is used:
these three stages and their trust items (sech ledgers, off-centre Arb unions, propagation replays, the ledger-based c_in of farL) leave the
trust base.

**Consequence for the assembly.** A certificate's hypotheses are now (H_model) for the all-open model, (H_rows), (H_count) and Lemma 1.
None of them refers to another certificate, so **there are no dependencies between pieces** (no phases, no induction over d, no derived
cases). Each certificate stands alone.

## 2. Rows: sech rows only, measured afresh

**Change.** v4 certificates use only sech rows `a|t` (0 < a < π; v4 uses a ∈ {1.6, 2.2, 2.8}), with
Elo/Ehi = outward-rounded ends of the Arb enclosure `E_comp(t)` of `certify_sech_interferometer.py` (`--evaluator zeta`, series target
1e-6; called exactly as v3 `make_cases.ensure_meas` / `propagation.py` do, including the `str(30)` round trip), and F = `im.far_bound(a, t,
wlo, whi)` (Trudgian count per unit interval, 60 units each side), Nwin = `im.count_upper(wlo, whi)` rounded up — the same functions v3
used in `propagation.build`. (H_rows) for these rows is the inherited fact: the window sum of f·Re sech(a(x − t − i d)) is ≤ E(t) (every
zero's contribution, mirror terms included, is ≥ 0 because a·d < π/2) and ≥ E(t) − F.

**Lorentzian rows are not used in v4.** Reason (a soundness finding, see §9): `farL.far_L` computes the open-column correction with the
distance from t to the *ends* of each OPEN run, which under-estimates the distance to zeros of a run that straddles the window. In the
all-open model the whole band is OPEN, so this would bite. v4's replay **rejects** any row whose id starts with `L` (no Lorentzian code is
loaded), so this cannot enter a v4 result.

**Rows with zero multiplier are omitted.** The generator emits only rows with y_up,j > 0 or y_low,j > 0. The Theorem with the reduced row
set is literally the same inequality (a row with y_up = y_low = 0 contributes 0 to Φ and to K).

## 3. One certificate, several candidate regions

**Change.** A certificate (y, w) may list regions R_1, …, R_n. It certifies every R_k.

**Why.** In the Theorem and in Lemma 2, (R) and the hypotheses do not depend on the region; the region enters only through (C). If (R)
holds and (C) holds on R_k, the Theorem (d > 0) and Lemma 2 (d = 0) give the claim on R_k.

**Check.** `replay4.py` calls the unchanged `verify_zs.check` once with the full var list and R_1 (this checks the Z signs, (R) and (C) on
R_1), and once per further region with `vars = []` (only (C) on R_k) and `check_z = False` (the same interval list, already checked).
All calls must return CERTIFIED. (The production driver uses one region per certificate, [x0, x1] × [0, 1/2]; the multi-region path is
kept for tests and is checked the same way.)

## 4. Sign-change intervals: computed once per target, adaptively; verified per certificate

**Change.** The generator computes the sign changes of Z once for [hull − WM, hull + WM] (grid of step ZS_STEP, extra samples where |Z| has
a same-sign local minimum, bisection of every bracket to width ≤ 1e-4) and gives each piece the intervals inside its window. v3's replay
also re-ran the generator's own search and required an identical interval list; v4 does not.

**Why.** Lemma 1 needs only: t1 < t2 inside the window and Z(t1), Z(t2) of strictly opposite signs (Arb). How the intervals were found is
irrelevant. A missed sign change only removes credit (the certificate may fail; it cannot be wrong). Overlapping or duplicate intervals
are harmless because the verifier subtracts the SUM of the w_i (THEORY_ZSIGN §3).

**Check.** `verify_zs.check` (check_z = True on the first call) evaluates Z at both ends of every interval with its own Γ-form at 160 bits
and checks the window containment and t1 < t2; w ≥ 0, y ≥ 0 are checked there too.

## 5. The replay rebuilds everything except the dual certificate

For each certificate, `replay4.py` (plain and hardened = 2 ulps outward on Elo, Ehi, F):

1. rebuilds the model from its definition (§1) from (T0, k0, k1) and requires vars, window and Nwin to equal the certificate's exactly,
   and every region to lie inside the window (x0 ≥ wlo, x1 ≤ whi, 0 ≤ d0 ≤ d1 ≤ 1/2) — the Theorem needs the candidate to be a window
   atom, and `verify_zs.check` does not test this itself; `replay_target4.py` checks (T0, k0, k1) and the regions against `pieces.json`
   and the target;
2. recomputes every row from scratch (§2): a fresh `E_comp(t)` per sech id (nothing is read from a measurement cache or from the
   generator), `im.far_bound`, `im.count_upper`; rejects any other row type;
3. runs the sha-pinned `verify_zs.check` as in §3.

So the generator (LP, its check, its sign-change search, its measurements) is untrusted. v3 trusted the measurement cache and the case
file; v4 trusts neither.

## 6. Pieces and tiling

**Pieces.** The hull (smallest run of 0.01 bins e(k) containing the target) is cut into pieces of at most PW (default 1.0) at bin edges.
A piece [e(ka), e(kb)] gets window [e(ka − m), e(kb + m)], m = round(WM/0.01), and region [e(ka), e(kb)] × [0, 1/2]. If a piece fails, the
driver may (i) add sech rows (more centres / kernels), (ii) refine the Z sampling in its window, (iii) split it at a bin edge. All three
only change what the generator tries; the claims are checked as above.

**Claim of a closed target.** Every zero of ζ with height in the hull lies on the critical line and is simple.

**Proof from the certificates.** Let ρ have height γ in the hull, d = |β − 1/2|. By the exact tiling, γ ∈ [x0, x1] for some certificate
whose region is [x0, x1] × [0, 1/2] and which passed replay. If d > 0, then (γ, d) ∈ region with d ∈ (0, 1/2): excluded by the Theorem. So
d = 0. If ρ had multiplicity ≥ 2, Lemma 2 (region contains d = 0) excludes it. ∎ No other certificate, no state and no order is involved.

**Exact tiling.** In exact rationals (`Fraction(float)`), with the unchanged `exact_tiling_check.check` (sha `0868990e…`): hull × [0, 1/2]
and target × [0, 1/2] must be covered by the replay-passed regions with 0 seams. Separately, the d = 0 line: the x-projections of the
replay-passed regions that contain d = 0 must cover the hull — checked by a 1-D exact interval sweep in `replay_target4.py`, because
`exact_tiling_check.check` with a degenerate required rectangle [a, b] × [0, 0] checks nothing (§9).

## 7. What is trusted (v4)

- `certify_sech_interferometer.E_comp` (explicit formula for the sech kernel, Arb; zeta-series evaluator with certified remainder) and the
  inherited (H_rows) argument for sech rows; `im.far_bound`, `im.count_upper` (Trudgian's S(T) bound).
- The classical fact 0 < β < 1.
- Lemma 1 (proved), the Theorem (proved in THEORY_ZSIGN), **Lemma 2 (parity; new in v3, still needs independent review)** — in v4 every
  certificate's simplicity claim rests on it.
- Arb / python-flint, Python `fractions`, the exact-tiling script, the sha-pinned `verify_zs.py`.
- Not trusted: the generator (LP, its internal check, its sign-change search, its measurements).

Removed from the v3 trust base: the base sech ledgers, the off-centre unions, the propagation certificates, the measurement cache
`joint_primal_dual/measurements.json` + extra caches, the case files, `lp.Phi`, `farL`.

## 8. Not changed

verify_zs.py (byte-identical, sha-pinned); the kernel formulas; the Theorem; Lemma 2; hardened replay; the exact tiling script.

## 9. Findings about v3 made while writing v4 (reported, not used)

1. **The d = 0 tiling check in v3 is vacuous.** `exact_tiling_check.check(name, [(a, b, 0, 0)], …)` builds the list of d-breakpoints
   {0}; with one breakpoint there is no strip, so it always returns 0 seams. v3's claim is not affected: hull × [0, 0.5] was covered
   with 0 seams, level-0 unions were excluded and propagation rectangles start at d ≥ 0.001, so the bottom strip [0, d_min] could only be
   covered by ladder slabs with d_lo = 0 — which is the d = 0 statement. v4 checks the d = 0 line with its own 1-D sweep.
2. **farL open-run distance (potential gap in v3 certificates that use Lorentzian rows next to long open runs).** In
   `far_L`, for each OPEN run (a, b) not inside the window, the extra (c_out − c_in) term uses r = min(|a − t|, |b − t|). If the run
   straddles a window edge, the run's zeros just outside the window are closer to t than r, so the bound can be too small. In v3, OPEN is
   the list of *merged* open runs of the band; at 6.8e6 most of the band is open, so runs straddle the ±3 windows.
   **Audit (dev/farL_audit.py, all 352 v3 certificates in atlas_v3/runs):** 19 certificates have straddling runs, but in every one of
   them the run has an end *inside* the window, which makes r small and the term larger (conservative). Recomputing F with the runs
   split at the window edges never increased any F used with a nonzero multiplier (ΔK = 0 for all 352). So no v3 result is affected;
   the flaw is latent (it bites only when one open run contains a whole window, which an all-open model would cause). v4 does not use
   farL.

## 10. Simplicity without Lemma 2 (the S-layer; added before coding it, before any acceptance run)

The controls show that the d = 0 claim of almost every main certificate needs Lemma 2 (the no-parity verifier rejects it). Lemma 2 is
unreviewed. v4 therefore adds a second, parity-free route to simplicity and reports it as a separate claim (B). Claim (A) — on the line
and simple, simplicity via Lemma 2 — is unchanged.

**(i) Main certificates are parity-free away from their intervals.** Let C pass the pinned verifier with region [x0, x1] × [0, 1/2] and
interval list ZIV(C). Suppose ζ has a zero of multiplicity k ≥ 2 at height x* ∈ [x0, x1] on the line, with x* in no closed interval of
ZIV(C). Take a* = (x*, 0, 2) and k − 2 further f = 1 atoms at x*. All atoms but a* lie in var boxes, so Φ_w ≥ 0 there by (R).
Σ_A Φ ≤ K + 2y_c by (H_rows), (H_count); Σ_i w_i n_i ≥ Σ_i w_i by Lemma 1 (n_i ≥ 1); Φ_w(a*) = Φ(a*) since x* is in no interval.
Hence Φ(x*, 0, 2) ≤ K + 2y_c − Σw, contradicting (C) at d = 0. No parity is used.

**(ii) Per-zero certificates, checked by the no-parity verifier, are parity-free.** The no-parity verifier is the pinned
`verify_zs.py` with exactly one line changed (built in memory by `replay4.py` from the pinned file, the original line asserted):
the candidate value of a box becomes Φ − K − 2y_c + Σw − f·Σ_{i: box reaches d = 0 and meets cl I_i} w_i. Suppose it certifies a region
[s0, s1] × {0} and ζ has a multiple zero at x* ∈ [s0, s1] (on the line). With a* as above, every other atom has Φ_w ≥ 0, Σ_i w_i n_i ≥ Σ_i w_i
(n_i counts a* too; Lemma 1 only), and Φ_w(a*) = Φ(x*, 0, 2) − 2 Σ_{i ∋ x*} w_i. So Φ(x*, 0, 2) − 2 Σ_{i ∋ x*} w_i ≤ K + 2y_c − Σw. Every
box containing x* meets cl I_i for each i ∋ x*, and w ≥ 0, so the verified inequality is at least as strong: contradiction.

(A no-parity certificate cannot cover two true zeros at once: at each true zero x_a the condition says 2Φ_w(a) > K + 2y_c − Σw, while
Σ_A Φ_w ≤ K + 2y_c − Σw. Hence one small certificate per zero.)

**(iii) Assembly of claim (B).** For every replay-passed main certificate C and every I ∈ ZIV(C) whose closure meets [x0, x1], the set
cl(I) ∩ [x0, x1] must lie in the union of the regions of per-zero certificates that passed the no-parity verifier (plain and hardened).
Checked exactly (Fractions). Then every x in the hull: x lies in some main region; if x is in no interval of that certificate, (i);
otherwise (ii). So no zero in the hull is multiple — by the Theorem's argument and Lemma 1 alone.

**Generator side.** Per interval: region [t1 − 0.001, t2 + 0.001] × {0}, window ± WM around it, LP with the parity-free candidate rows
(the w-columns of d = 0 candidate rows inside an interval get +2) and samples inside the interval; the rows are the main run's
measured rows first, then more sech centres, then finer Z. Untrusted as always.
