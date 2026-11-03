# atlas_v5 — exact heights and a height-robust prime side (written before the v5 code, 2026-10-08)

v5 is atlas_v4 (THEORY_V4.md, copied here unchanged for reference) with two changes:

1. **Exact heights (§1–§4).** Every height is carried as an integer base T0 plus a binary64 offset u. The real number is T0 + u,
   exactly. This removes the binary64 blocker found in BIG_TARGETS §1.7: ulp(10^13) = 0.002 and ulp(10^16) = 2, so v4 could not
   represent its own bins, sign-change intervals or row centres above about 10^12.
2. **A Dirichlet-sum evaluator for the sech rows (§5).** v4's rows call Arb's ζ'/ζ K = 10–17 times per row. Arb evaluates each call by
   Riemann–Siegel, which costs about 1 s at 10^13 and 30 s at 10^16. v5 keeps one Arb call per row (the k = 0 term) and replaces the
   rest by a finite Dirichlet sum with a proved tail bound.

Nothing else changes: the THEORY_ZSIGN Theorem, Lemma 1, Lemma 2, the all-open model, the S-layer (claim B), the assembly, the hardened
replay, the pinned exact-tiling script and the pinned verifier's inequality logic.

Labels: **[T]** proved here; **[I]** inherited from v4 and trusted exactly as v4 trusts it.

---

## 1. Height representation [T]

**Definition.** A run fixes an integer T0 ≥ 0 (stored as a JSON integer in `pieces.json` and in every certificate). Every height in a
run is a pair (T0, u) with u a finite binary64 number. The pair denotes the real number h = T0 + u. Its exact rational value is
`Fraction(T0) + Fraction(u)`, because every binary64 number is a dyadic rational. Files store u only (JSON `repr` round-trips binary64
exactly).

**Where it is used.** Bin edges, windows, model boxes, candidate regions, sign-change endpoints, sech-row centres, the target and the hull
are all offsets u. Displacements d ∈ [0, 1/2] and every dual quantity (y, w, Elo, Ehi, F, Nwin) are not heights and are unchanged.

**Arb conversion.** Every Arb evaluation that needs an absolute height (Z, E, θ in the count bounds) builds it with `hx(T0, u)`.
`hx` forms the exact rational T0 + u = p / 2^e, sets the working precision to at least bitlen(p) + 8 bits and returns arb(p) / arb(2^e).
Division by a power of two at that precision is exact. `hx` asserts that the result has radius 0. So every Arb evaluation sees the exact
height, at any T0.

**Why differences are exact.** The sech kernel and the remainder/candidate conditions depend on heights only through differences
x − t of two heights of the same run. (T0 + u_x) − (T0 + u_t) = u_x − u_t. Every place where v5 forms such a difference does it in
Arb (balls around the offsets) or in exact arithmetic. So T0 cancels exactly and the verifier's inequality code can work on offsets.

**Translation invariance of the geometric checks.** The map u ↦ T0 + u is an exact, order-preserving bijection of the rationals. So
"the regions tile hull × [0, 1/2]", "the interval lies in the window", "t1 < t2", "intervals are disjoint" hold for the offsets iff they
hold for the absolute heights. The pinned tiling script `exact_tiling_check.check` (sha `0868990e…`, unchanged) is therefore run on the
offsets. The Lean exporter writes the absolute rationals T0 + u (§7).

## 2. Grids [T]

v5 has two bin grids. The grid is a field of `pieces.json` and of every certificate, and it is part of the model definition the replay
rebuilds.

- **grid "v5" (production):** e(k) = T0 + u_k with u_k = fl(k · 0.01), the binary64 product of the integer k and the double 0.01.
  Sech-row centres for bin m: u = fl((m + 0.5) · 0.01). Every u_k is exact data. Bins [u_k, u_{k+1}] are contiguous. Their width
  is about 0.01 and need not be exactly 1/100, which nothing requires.
- **grid "v4" (compatibility only, used to reproduce the v4 acceptance runs):** u_k = fl(T0 + k · 0.01) − T0, computed exactly
  (`Fraction(fl(T0 + k*0.01)) − T0`; it is a binary64 number because both terms are binary64 numbers of nearby size). This is the v4
  edge expression e(k) = T0 + k·0.01 evaluated in binary64. So a v4 run and its v5 "v4-grid" re-run have **identical bins, windows and
  regions as real numbers**. Centres likewise: u = fl(T0 + (m + 0.5)·0.01) − T0.

The proof in THEORY_V4 §1/§6 uses only that the closed bins of a window are contiguous and cover it. Both grids satisfy this.

## 3. The verifier: verify_zs5.py, derived from the pinned verify_zs.py [T]

`lib/verify_zs5.py` is the pinned `verify_zs.py` (sha `ed5bc621…`) with **exactly these changes**. `dev/verify_zs5_diff.txt` holds the
unified diff, and the replay asserts the sha of the new file (re-frozen in `V5_FREEZE.sha256`).

1. `check(..., T0=0)` takes a new keyword argument T0 (a Python int). Every height argument (row ids `a|u`, window, region, model
   boxes, interval endpoints) is an offset relative to T0.
2. `Zg(t)` becomes `Zg(T0, t)`. It builds the exact height `hx(T0, t)` and evaluates the same Γ-form of Z at precision
   160 + bitlen(T0) instead of 160. With T0 = 0 it is v4's Zg: same formula, same precision, and arb(t) is exact in both. The extra
   bits keep the phase accurate at large T. Ball enclosures are valid at any precision, so the change cannot make an invalid sign
   check pass.
3. `Zg` is memoised on (T0, t). It is a pure function of exact inputs, so a cache changes cost only. In v4 a long replay re-evaluated
   the same endpoint up to ~10 times (plain and hardened, overlapping windows, S-layer). At 10^16 one Z costs ~6 s.
4. The structural checks, `_ball`, `_parse`, `_phi`, K, `zsub`, the bisection and every inequality are **byte-identical lines**. They
   see offsets. This is sound by §1: `_phi` uses only `x − arb(t)` (x a ball around the offsets of a box, t an offset), i.e. exactly
   x_abs − t_abs. The comparisons `wlo <= t1 < t2 <= whi` and the interval–box tests compare offsets of the same run, which is exact
   (§1).

With T0 = 0 and absolute heights, verify_zs5.check is the v4 verifier (items 2–3 give identical values and add a cache).

**The no-parity verifier** (THEORY_V4 §10) is built in memory from verify_zs5.py by the same one-line replacement as in v4. The replay
asserts the sha of verify_zs5.py and that the replaced line occurs exactly once.

## 4. Rows, counts and the model at exact heights [T]

`lib/model5.py` rebuilds the model and rows with offsets. The real numbers it encloses are exactly those of v4, at the absolute
heights T0 + u.

- **Model.** All-open, as in THEORY_V4 §1. For window bins k0..k1 of the run's grid: vars `['on', u_k, u_{k+1}, 0, 0]`,
  `['off', u_k, u_{k+1}, 0, 0.5]`.
- **Nwin** = up(count_upper5(T0, u_wlo, u_whi).upper()). It encloses the same real expression as v4:
  (θ(T0 + u_whi) − θ(T0 + u_wlo))/π + 2 S_max(T0 + u_whi), with θ from Arb log-gamma at the exact heights. [I] Trudgian's
  |S(T)| ≤ 0.112 log T + 0.278 log log T + 2.510 (T ≥ e).
- **F** = far_bound5(a, T0, u_t, u_wlo, u_whi): im.far_bound's formula. There are 60 unit shells per side, with shell edges
  u_edge ± k as offsets (any contiguous shelling is valid; the first shell starts exactly at the window edge). Each shell's count
  is count_upper5, plus 1e-20 for everything beyond 60 units [I]. **One change:** the shell distance r = |x0 − t| is computed in
  Arb from the two offsets (exact), not in binary64. In v4 the binary64 subtraction of two nearby absolute values was exact
  (Sterbenz). With offsets of different magnitude it may round, and rounding up would make F too small. Arb removes the
  question.
- **E** (row enclosure) at the exact height x = hx(T0, u):
  - evaluator **"zeta"** = v4's `certify_sech_interferometer.E_comp`, unchanged and called exactly as v4's `model4.measure` does
    (prec 256, configure/_init, `str(30)` round trip, im.dn/im.up). With T0 = 0 this is v4's measurement, bit for bit.
  - evaluator **"dirichlet"** = §5.

  The evaluator is a field of `pieces.json` and of every certificate, and the replay uses the same one. Either gives a valid
  enclosure of E_a(T0 + u).

**Hardened replay**, the region-in-window check, the rebuilt-model equality and the rejection of non-sech rows are as in v4.

## 5. The "dirichlet" evaluator [T, with inputs I]

**Setting** (certify_sech_interferometer docstring, [I]): h(r) = sech(a r), 0 < a < π, f(u) = (1/2a) sech(πu/(2a)). For every real x,

  E_a(x) = pole(x) − f(0) log π + arch(x) + prime(x),
  prime(x) = −2 Σ_{n≥2} Λ(n) n^{−1/2} f(log n) cos(x log n),

and E_a(x) = Σ_ρ h_x(γ_ρ) is the row quantity of every v4 sech row.

**Algebra.** Let b = π/(2a) > 1/2, so 1/2 + b > 1. Then f(log n) = (1/2a) · 2/(n^b + n^{−b}) = (1/a) n^{−b}/(1 + n^{−2b}). The identity

  n^{−b}/(1 + n^{−2b}) = n^{−b} − n^{−3b}/(1 + n^{−2b})

gives, with every series absolutely convergent (exponents 1/2 + b > 1 and 1/2 + 3b > 1):

  prime(x) = −(2/a) [ Re(−ζ'/ζ)(1/2 + b + ix) − Σ_{n≥2} c_n cos(x log n) ],   c_n = Λ(n) n^{−1/2−3b}/(1 + n^{−2b}) ≥ 0,

using Re(−ζ'/ζ)(σ + ix) = Σ Λ(n) n^{−σ} cos(x log n) for σ > 1. This is the same real number as v4's zeta-series expression
−(2/a) Re Σ_k (−1)^k (−ζ'/ζ)(1/2 + (2k+1)b + ix). v4 truncates at k = K with remainder R_K ≤ 1e-6. v5 sums the whole k ≥ 1 part in
closed form, per n.

**Truncation.** Split Σ_{n≥2} c_n cos(x log n) = Σ_{n≤M} + Σ_{n>M}. Then |Σ_{n>M}| ≤ Σ_{n>M} Λ(n) n^{−σ3} with σ3 = 1/2 + 3b > 1,
because 0 < 1/(1 + n^{−2b}) < 1. **Lemma D.** For σ > 1 and M ≥ 1,

  Σ_{n>M} Λ(n) n^{−σ} ≤ 1.03883 · σ/(σ − 1) · M^{1−σ}.

*Proof.* Let ψ(y) = Σ_{n≤y} Λ(n). [I] Rosser–Schoenfeld (1962, Thm 12) gives ψ(y) < 1.03883 y for y > 0. This is the same constant
v4's `tail_bound` uses. By Riemann–Stieltjes partial summation, for Y > M,
Σ_{M<n≤Y} Λ(n) n^{−σ} = ψ(Y) Y^{−σ} − ψ(M) M^{−σ} + σ ∫_M^Y ψ(y) y^{−σ−1} dy. Drop −ψ(M)M^{−σ} ≤ 0, let Y → ∞ (ψ(Y)Y^{−σ} → 0) and
bound ψ(y) ≤ 1.03883 y: the integral is ≤ 1.03883 σ ∫_M^∞ y^{−σ} dy = 1.03883 σ M^{1−σ}/(σ − 1). ∎

**Enclosure.** prime(x) ∈ −(2/a)[P0 − S_M] ± (2/a) R_M, where:
- P0 is Arb's enclosure of Re(−ζ'/ζ)(1/2 + b + ix), from the same length-2 `acb_series.zeta` jet as v4 (`mzl`, precision 128). It is
  one Arb call per row instead of K.
- S_M = Σ_{n≤M} c_n cos(x log n) in Arb ball arithmetic at precision 128 + bitlen(T0). c_n and log n are enclosed in Arb, Λ(p^k) =
  log p comes from an exact sieve, and x is exact.
- R_M is the Arb upper bound of Lemma D at σ3, rounded up.

Production uses M = 10^6, giving (2/a) R_M ≈ 1.1e-7 (a = 2.8), 2e-10 (a = 2.2) and < 1e-14 (a = 1.6). v4's target was 1e-6.

The rest of E (pole, −f(0) log π, arch with its Gauss–Legendre/Trefethen remainder) is v4's code, called unchanged on the exact
ball x: `certify_sech_interferometer.arch`, plus the two pole/constant lines of `E_parts` copied verbatim. The same `str(30)`
round trip and outward binary64 rounding as v4 are applied.

**New trusted code:** the algebra above, Lemma D (with its [I] input), the sieve, and the Arb summation loop (`lib/sech5.py`). It is
validated against the v4 evaluator: the enclosures must overlap at 10^7 and 10^12 (§9 step 2).

## 6. Generator (untrusted; nothing here is in the trust base)

The generator works in **work coordinates** and converts to offsets when it writes a certificate.

- grid "v4": absolute binary64, exactly v4's arithmetic. The v4 LP is then reproduced bit for bit, given the same rows.
- grid "v5": offsets.

Z sign changes use the exact height `hx(T0, u)`, at precision raised by bitlen(T0). The sign-change step and the refinement width
are run parameters, pre-registered per target. Everything else (tiers, S-layer, LP, cutting planes) is v4's code.

## 7. Lean audit: exact-height export [T]

The Lean checks (`formal/AtlasAudit`) work on exact rationals and need no change. `formal/export/export_certs.py` gets a **v5 path**
(`--v5 RUN_DIR … OUTFILE`). It writes every height as the exact rational T0 + Fraction(u), with u read from the JSON as v4's path reads
its floats. Displacements are written as in v4. The default path (no `--v5`) is unchanged. A regression check confirms that it still
writes byte-identical files for the existing datasets.

## 8. Claims, trust and novelty

**Per closed target:** every zero of ζ with ordinate in the hull lies on the critical line and is simple. That is claim (A), via Lemma 2,
and claim (B), without Lemma 2, when the S-layer covers. The trust base is v4's, with these changes:
- `verify_zs5.py` replaces `verify_zs.py` (§3);
- for "dirichlet" runs, §5 (Lemma D, Rosser–Schoenfeld's constant, the sieve and the summation) replaces the k ≥ 1 jets of `E_comp`;
- `hx` (exact height conversion), and model5's offset arithmetic (§4).

**Diagnostic, not trusted:** Arb's `acb_dirichlet_zeta_nzeros` (Turing's method, via ctypes). Atlas's sign-change count in the target
is compared with N(T0 + u_hi) − N(T0 + u_lo). The comparison is pre-registered as a prediction. A disagreement would mean either a
missed sign change (Atlas can then not close) or a bug.

**Novelty statement** (BIG_TARGETS §1.6, used verbatim in RESULTS).
- Platt–Trudgian proved RH up to 3·10^12 (3 000 175 332 800).
- Arb's Turing-method routines can certify a local window at any height up to about 10^23. So "RH holds in a window at height
  10^13" is obtainable by a library call, and no Atlas window is a new fact about ζ in any strong sense.
- The claim is: **to our knowledge, the first published certification in a window above 3·10^12 by a method independent of Turing's
  method** (explicit-formula sech rows, Arb-proved sign changes, an LP dual certificate, independent replay and a Lean-checked file
  audit), cross-checked against Arb's Turing count.
- [10^12, 10^12 + 2] is a control inside the verified range.

## 9. Acceptance plan (each step before the next)

1. **Exact heights, compatibility.** Re-run the v4 targets with grid "v4" and evaluator "zeta":
   - [9000, 9010], Rosser, 663318 and lehmer_full_pair (T0 as in v4);
   - the 10^7 T4 window [10^7, 10^7 + 2].

   Required:
   - identical regions, windows, bins and sign-change intervals as real numbers (checked exactly against the v4 files);
   - identical row ids (as real centres);
   - multipliers y, w equal (bit-identical expected, since the LP is reproduced);
   - min_candidate_lower equal up to rounding (|Δ| ≤ 1e-9 relative);
   - plain + hardened replay passing, 0 seams and claim (B).

   Then run the Lean audit on the v5 export.
2. **Prime side.** At x ∈ 10^7 + {0.005, 0.505, …} and 10^12 + {…}, for a ∈ {1.6, 2.2, 2.8}, the "dirichlet" and "zeta" enclosures must
   overlap, and the dirichlet radius should be smaller. Record the times.
3. **Control** [10^12, 10^12 + 2], grid v5, evaluator dirichlet. Pre-registered.
4. **New windows** [10^13, 10^13 + 2], then 10^14, 10^15 and 10^16 as long as each closes and time allows. Pre-registered with the Arb
   counts. If a piece fails, the v4 escalation tiers run as coded. If the target still does not close, it is reported as
   NOT CLOSED / UNRESOLVED. No code change is made to force closure. The v4.2 local-count finalizer may be tried and reported
   separately, if its exact-height port is done and validated first.
