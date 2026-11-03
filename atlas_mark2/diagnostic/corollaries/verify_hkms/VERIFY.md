# Adversarial verification: RESULTS.md item 3 (HKMS naive Mertens-type conjecture, Q(√5), Q(√−3))

Date 2026-10-11. All code in this directory is new and independent. It does not import `lzeros.py`, `hstar.py` or any other Atlas
module, and it reads no Atlas output except in `compare_lists.py`, which reads Atlas's zero lists only to compare them with mine.
Everything ran at `nice -n 19` under a 2 GB RSS watchdog (`memcap.sh`). Peak RSS was under 100 MB. Nobody was contacted.

## Overall verdict: **CONFIRMED**, with wording corrections

The disproof is correct. The quantity Atlas computes is exactly HKMS's h* (eq. 3.6). I re-derived the implication from Ingham's
theorem: it holds with exactly this normalisation. My own zeros and weights reproduce every certified value to all 12 printed digits.
The Q(i) discrepancy lies in HKMS's paper, not in Atlas's normalisation. A smoothed version of the actual Mertens function matches
h* to about 1e−5.

## Check 1: the implication and every constant. **CONFIRMED**

**Source.** I fetched arXiv 2109.06665 (`hkms_fetched.pdf`). It is byte-identical to `refs/2109.06665.pdf` (v2), with sha256
`472f5569…b93b`. I also checked the **published version**, Math. Proc. Camb. Phil. Soc. 177 (2024) 481–523
(doi 10.1017/S0305004124000306; HTML text in `hkms_published_text.txt`). It is unchanged on every point relevant here:
* Theorem 1.1 still excepts Q(√−3) and Q(√5).
* Eq. (3·6) is the same.
* It still says "h*_{Q(i),600}(72.85) ≤ −1.008 and h*_{Q(i),600}(−85.15) ≥ 1.029".

So the exceptions are still open in print, and the Q(i) number was never corrected.

**Definitions, from the paper.**
* M_K(x) = Σ_{N(a)≤x} μ_K(a), with a half weight at jumps. This has no effect on lim sup or lim inf.
* 1/ζ_K(s) = s∫₁^∞ M_K(x)x^{−s−1}dx.
* M^±_K = lim sup / lim inf of M_K(x)/x^{1/2}.
* Conjecture: −1 ≤ M⁻_K ≤ M⁺_K ≤ 1.
* (3.6): h*_{K,T} = Σ_{|γ|<T} f(|γ|/T) e^{iγy}/(ρζ_K′(ρ)), with f(u) = (1−u)cos πu + sin(πu)/π.

The paper writes h*(t) but puts e^{iγy} inside the sum. This t/y slip is harmless, because any real argument works.

The sum runs over |γ| < T, so it includes both signs of γ. ζ_K has real coefficients, so w(ρ̄) = conj w(ρ). The sum therefore equals
Σ_{0<γ<T} 2 Re[f(γ/T) e^{iγy} w(ρ)], which is what Atlas computes. There is no other normalisation: no log factor, and no factor 1/2.

For quadratic K, ζ_K = ζ·L(χ_D) with χ_D primitive real. If ζ and L have no common zero, then:
* at a zero of ζ, ζ_K′(ρ) = ζ′(ρ)L(ρ);
* at a zero of L, ζ_K′(ρ) = ζ(ρ)L′(ρ).

Atlas uses exactly this. The characters I use are χ₅ = (5/·), χ₋₃ and χ₋₄ (Conrey labels 5.4, 3.2, 4.3). As checks, my M_K reproduces HKMS's
M_{Q(√−3)}(7) = −3 and M_{Q(√5)}(11) = −4.

**Re-derivation of M⁻_K ≤ h*_{K,T}(y) ≤ M⁺_K (all y ∈ ℝ, any T).** HKMS assert this display without proof. Here is the argument.

1. *Kernel.* f = 2·(g∗g) with g(s) = cos(πs)·1_{|s|≤1/2}. Hence the kernel
   K_T(u) = (1/2π)∫f(|t|/T)e^{itu}dt = (T/π)·4π²cos²(Tu/2)/(π²−T²u²)²
   is ≥ 0, and ∫K_T = f(0) = 1.
   Checked numerically to 15 digits (`kernel_check.py` / `.log`).

2. *Set-up.* Let A(u) = e^{−u/2}M_K(e^u) for u ≥ 0. Then
   ∫₀^∞ A(u)e^{−su}du = 1/((s+½)ζ_K(s+½)) for Re s > ½.

3. *Landau step.* Suppose M⁺_K < ∞ (the M⁻ case is symmetric). Then C − A(u) ≥ 0 for some C and all u ≥ 0. By Landau's theorem, its
   Laplace transform C/s − 1/((s+½)ζ_K(s+½)) converges up to the first real singularity. There is none in (0, ½], because ζ_K(σ) ≠ 0
   on [½, 1):
   * ζ(σ) < 0 there (classical);
   * L(σ, χ_D) > 0 there. I re-certified this for D = 5, −3, −4 with a Lipschitz/Abel bound, |L′(σ)| ≤ 4B/e with B = 1. The
     minimum lower bounds are 0.230, 0.479 and 0.666.

   So the transform is analytic for Re s > 0. Hence RH holds for ζ_K.

4. *Ingham's theorem* (Ingham 1942, Thm 1). It needs a kernel whose Fourier transform is supported in [−T, T] and is non-negative,
   which step 1 gives; this is the JP kernel version used by Odlyzko–te Riele 1985. Its continuation hypothesis requires that, on
   Re s = 0 with |t| ≤ T, the transform has only simple poles. This holds when:
   * the zeros of ζ_K with |γ| < T are simple. This is certified, and the ζ and L zeros are disjoint (check 4);
   * ζ_K(½) ≠ 0, so there is no pole at s = 0. This follows from L(½) > 0 and ζ(½) < 0;
   * no zero lies at |γ| = T. This is certified, since the argument count at T requires L ≠ 0 there.

   The residue at s = iγ is 1/(ρζ_K′(ρ)). Zeros above T need no hypothesis at all.

   The conclusion is lim sup_{u→∞} Σ_{|γ|<T} f(|γ|/T) r_γ e^{iγu} ≤ lim sup A = M⁺_K.

5. *Almost periodicity.* A finite trigonometric sum P satisfies P(y) ≤ lim sup P for every y, by Kronecker/Dirichlet return times.

6. *Conclusion.* h*_{K,T}(y) > 1 at any single real y forces M⁺_K > 1 (or M⁺_K = ∞). Likewise h* < −1 forces M⁻_K < −1.
   Either way the conjecture fails as stated.

The trivial zeros, the pole and s = 0 (the M*_K terms) lie in Re s ≤ −½ of the shifted variable. They play no role. M* enters only the
exact-identity diagnostic below.

**Normalisation diagnostic** (`mertens_diag.py`, `mertens_diag.log`; independent of Atlas's diagnostic). I computed the actual
c(n) = (μ ∗ μχ)(n) up to 3.3·10⁶. I then smoothed F(y) = e^{−y/2}(M_K + M*_K)(e^y) with K_T, T = 600, using:
* M* = w/h for Q(i) and Q(√−3);
* M* = HKMS (3.7) for Q(√5), with 4/(L(1)√5) = 2/log φ = 4.15617 and L′/L(1, χ₅) = 0.82768.

The result equals h* from the zeros to within 3e−5 at y between 9 and 14.5 for all three fields, and 1.4e−4 at Q(i) y = 8. Examples:

| field | y | smoothed M | h* |
|---|---|---|---|
| Q(√5) | 11 | −0.29411 | −0.29411 |
| Q(√−3) | 11 | −0.23278 | −0.23276 |

A factor-2 or one-sided error would show up as a 100% discrepancy. None is present.

**Caveat on the wording only.** RESULTS §3.4 calls the relation "HKMS's stated relation … did not re-derive". It is now re-derived, as
above, and the correct citation is Ingham 1942 Thm 1 (JP kernel as in OtR 1985) plus Landau. Prefer citing that over HKMS's unproved
display. Also, "whenever M^± is finite" in Theorem 3 is unnecessary, since the bounds hold in the extended reals.

## Check 2: the Q(i) discrepancy. **PROBLEM in HKMS, not in Atlas**

With my own zeros and weights (Arb, T = 600, 341 ζ zeros + 473 L(χ₋₄) zeros):

| y | h*_{Q(i),600}(y) | HKMS states |
|---|---|---|
| 72.85 | −0.936723117924 ± 3e−13 | ≤ −1.008 |
| 72.8483 (local min) | −0.944651624 | |
| −85.15 | 1.20021579232 | ≥ 1.029 (true, but not "reproduced": the value is 1.20, not ≈ 1.03) |
| −85.1474 (local max) | 1.22097248997 | |
| 90.6694 | −1.19330058033 | (Atlas's replacement for M⁻ < −1) |

The normalisation is decisively the paper's own: eq. 3.6 as printed, and the smoothed actual Mertens function matches it. I tried
every plausible alternative convention (`qi_variants.py` / `.log`):

| convention | h*(72.85) | h*(−85.15) |
|---|---|---|
| Fejér kernel | −0.952 | 1.190 |
| sharp cutoff | −1.150 | 1.349 |
| one-sided (no 2Re) | −0.468 | 0.600 |
| y → −y | +0.091 | 0.559 |
| conj weights | +0.091 | 0.559 |
| first 600 ζ_K zeros | −0.899 | 1.154 |
| ζ zeros only | +0.474 | 0.777 |
| L zeros only | −1.410 | 0.423 |

None gives both of HKMS's numbers at T = 600.

The required scalings differ between the two points: 1.076 at 72.85 and 0.857 at −85.15. So no global constant explains it. Both
points are genuine local extrema of our h*, which means HKMS were looking at the same function.

Under the standard formula, h*(72.85) ≤ −1.008 first holds at T ≈ 890. For example, T = 900 gives −1.0101 and T = 990 gives −1.0267.
That is consistent with HKMS having computed at a larger T than the "600" they printed, but it remains speculation.

**Consequence.** HKMS Thm 1.1(a) for Q(i) is unaffected. M⁺ ≥ h*(−85.15) = 1.2002 > 1 already suffices, and M⁻ < −1 also holds via
y = 90.6694. Atlas's disproof does not depend on HKMS's numbers at all.

## Check 3: independent recomputation of the certified values. **CONFIRMED** (`certify.py`, `certify.log`, `certify.json`)

**Zeros.**
* ζ: Arb's own `acb_dirichlet_zeta_zero`, a different algorithm from Atlas's Hardy scan. There are 640 zeros below 990 (341 below
  600).
* L(χ): my own Hardy Z, scanned with grid step 0.037 (Atlas used 3/64). Each zero is refined by regula falsi and certified by strict
  opposite signs at γ̃ ± 1e−30, at 224 bits.

**Weights.** Arb jets: ζ′·L and ζ·L′ on the ordinate ball, at 192 bits. The maximum weight radius is 1.7e−26. An mpmath (Hurwitz
route) cross-check on every 25th zero agrees to double precision.

**h\*.** Arb ball sum at the exact rational y. The radii shown are inflated by printing to 12 digits.

| K | T | y | h* (mine) | equals Atlas? |
|---|---|---|---|---|
| Q(√5) | 600 | 720.3427 | 1.05738521285 | yes |
| Q(√5) | 600 | 722.7391 | −1.06722864784 | yes |
| Q(√5) | 990 | 17736.1391 | **1.16984379838** | yes |
| Q(√5) | 990 | 12927.3821 | **−1.14508971708** | yes |
| Q(√−3) | 600 | 84.5099 | 1.46764443125 | yes |
| Q(√−3) | 600 | 800.8885 | −1.59399508786 | yes |
| Q(√−3) | 990 | 9955.0694 | **1.77149932910** | yes |
| Q(√−3) | 990 | 800.8888 | **−1.76750184246** | yes |

Every value is certified > 1 or < −1, with error ≤ 5e−12. Even the T = 600 values on their own disprove the conjecture with margin
> 0.05.

## Check 4: completeness and disjointness. **CONFIRMED**

**Argument-principle count.** My own count N(T) = (θ(T) + Δ_{2→2+iT→½+iT} arg L)/π, derived in `vzeros.py`, uses:
* adaptive Arb boxes on the top edge (a box that excludes 0 bounds the arg change by π);
* Re L > 0 on Re s = 2;
* Λ(σ) > 0 on [0, 1] from check 1.

At T = 990:

| L | N(990) | sign changes | ball |
|---|---|---|---|
| L(χ₅) | 893 | 893 | [893 ± 3e−11] |
| L(χ₋₃) | 813 | 813 | |
| L(χ₋₄) | 858 | 858 | |

There were 0 grid points of unknown sign. So every zero with 0 < γ < 990 is on the line, simple, and isolated.

**Agreement with Atlas.** My lists and Atlas's set-B lists, restricted below 990, agree in count and in float value (max |Δ| = 0)
for q = 1, 5, 3, 4 (`compare_lists.py` / `.log`).

**Disjointness.** The minimum distance between a ζ ordinate and an L ordinate is:

| field | min distance | at γ ≈ |
|---|---|---|
| Q(√5) | 1.7e−3 | 538.429 |
| Q(√−3) | 3.8e−3 | 359.74 |
| Q(i) | 5.2e−4 | 437.58 |

Enclosure widths are 2e−30. So ζ_K has only simple zeros below 990, and the multiplicity hypothesis is verified, not assumed.

## Recommended statement (replaces RESULTS §0 row 3 / Theorem 3 wording)

> **Theorem.** For K = Q(√5): M⁺_K ≥ 1.1698 and M⁻_K ≤ −1.1450. For K = Q(√−3): M⁺_K ≥ 1.7714 and M⁻_K ≤ −1.7675. Here
> M^±_K = lim sup / lim inf of M_K(x)/√x, taken in the extended reals. The proof is unconditional. All zeros of ζ_K with 0 < γ < 990
> are certified on the line and simple, with the lists certified complete. Ingham's theorem (1942, Thm 1) with the Jurkat–Peyerimhoff
> kernel (as in Odlyzko–te Riele) then gives M⁻_K ≤ h*_{K,T}(y) ≤ M⁺_K for every real y; Landau's theorem disposes of the case where
> RH fails. Hence the naive Mertens-type conjecture of Hu–Kaneko–Martin–Schildkraut (arXiv 2109.06665; Math. Proc. Cambridge Philos.
> Soc. 177 (2024)) fails for these two fields. Combined with their Theorem 1.1, it fails for every quadratic field.

Also:
* "reproduced (1.2002)" should read "consistent with (we get 1.2002)".
* For the Q(i) note, say: "h*_{Q(i),600}(72.85) = −0.93672 under eq. (3.6) as printed, and no tested convention gives ≤ −1.008 at
  T = 600. The standard formula gives ≤ −1.008 at 72.85 only for T ≳ 890. Their Theorem 1.1(a) for Q(i) is unaffected, since
  h*(−85.15) = 1.200 > 1."
* Also note that the published version (2024) still lists the two exceptions. That is relevant to novelty, but I did not do a full
  novelty search.

**Residual trust.**
* Arb primitives (`dirichlet_l`, `zeta`, `lgamma`, `zeta_zero`).
* Ingham's theorem in its JP-kernel form.
* HKMS Theorem 1.1 itself, for the "every quadratic field" clause. I did not re-audit their real-quadratic M*_K(1) table or proof.

## Files
* `vzeros.py`: zeros, argument count, real segment.
* `vhstar.py`: weights, h*.
* `certify.py`: certificates.
* `qi_variants.py`: Q(i) conventions.
* `mertens_diag.py`: normalisation diagnostic.
* `kernel_check.py`: kernel identity.
* `compare_lists.py`: list agreement with Atlas.
* `memcap.sh`: memory watchdog.
* Outputs: `vz_q{1,5,3,4}_T990.json` and the logs.
* Hashes: `SHA256SUMS`.
