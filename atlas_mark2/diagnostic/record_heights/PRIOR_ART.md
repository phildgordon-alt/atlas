# Prior art: verifying RH far above 3·10¹² (record_heights, 2026-10-18)

This builds on `new_territory/BIG_TARGETS.md` §1 (2026-10-08), which already read Gourdon, Bober–Hiary, HIK and the FLINT docs. Here I
re-checked those sources and added the cost and algorithm literature.

How I searched: WebSearch was used up. The arXiv API returned HTTP 429 and then timed out, so I fetched sources directly:
- arXiv PDFs 2004.09765, 2408.00187, 1607.00709, 0711.5005 and 1002.2443, with text pulled out by pypdf;
- the FLINT acb_dirichlet docs;
- Johansson's 2016 Riemann–Siegel post;
- Gourdon's page, fetched with `curl -4`;
- Hiary's home page;
- the arXiv author listing for Platt.

Odlyzko's PDFs use Type-3 fonts and yield no text, so I have no direct quote from him on rigour. Tags: **[S]** I read it in the
source today. **[P]** taken from BIG_TARGETS.md, which read the source. **[I]** my inference.

## 1. The rigorous frontier

- **Platt–Trudgian, Bull. LMS 53 (2021), arXiv:2004.09765 [S].** Their Theorem 1: "The Riemann hypothesis is true up to height
  3 000 175 332 800." The method is Arb interval arithmetic plus "a variation of Turing's method". It used 7.5 million core hours.
  - On the earlier records: Gourdon 2004 (H = 2.44·10¹²) and Wedeniwski (2.41·10¹¹) "have the disadvantage that neither has been
    published in a peer reviewed journal. Furthermore, it is not clear how the computations were set up to avoid problematic
    accumulation of rounding and truncation errors."
- **Platt, Math. Comp. 86 (2017) [P].** Zeros isolated rigorously to 3.06·10¹⁰.

## 2. Above 3·10¹²: what exists, and how rigorous it is

| work | height | what | rigorous? |
|---|---|---|---|
| Odlyzko 1989/1992, 1998, 2001, 2002 | zeros n ≈ 10²⁰ (70 M, then 175 M zeros), 10²¹, 10²² (10¹⁰ zeros), 10²³ (2·10¹⁰, unpublished) | Odlyzko–Schönhage in floating point; spacing statistics | **No** [P]. No source cites it as a rigorous verification. Gourdon quotes the 1987 accuracy as "10⁻⁸". |
| Gourdon (with Demichel) 2004, unrefereed | first 10¹³ zeros (t ≈ 2.446·10¹²); **2·10⁹ zeros at each n = 10¹³, 10¹⁴, …, 10²⁴** [S] | Odlyzko–Schönhage, "classic double floating point", checked by recomputing a fraction of the zeros | **No.** In his own words it is difficult "to consider such results as 'proved' in a strong sense" [P]. The 10¹³ part now lies inside Platt–Trudgian's range. |
| Bober–Hiary, Exp. Math. 27 (2018), arXiv:1607.00709 | t from 10²⁴ to 8·10³⁴ (up to zero n ≈ 10³⁶) | Hiary's t^{1/3} quadratic-sum algorithm in C++ doubles plus MPFR; Turing's method | **No.** [S] "we have checked the Riemann Hypothesis for more than 50000 zeros in over 200 separate small intervals with values of t ranging from 10²⁴ to 8×10³⁴". [S] "we expect to be able to compute up to an absolute precision of around 10⁻¹⁰". Of the true truncation error: "we cannot prove this". |
| **Hiary–Ireland–Kyi 2024**, arXiv:2408.00187 (preprint) | y = 10²⁸ + 501675.8, η = 70 216 (**1 399 910 zeros**) | explicit-formula positivity evaluated in mpmath interval arithmetic, minus intervals around known zeros | **Conditional.** [S] "Our working assumption is that the zeros ordinates from [LMFDB] and [Zet] are accurate within ±10⁻¹⁰". [Zet] is Hiary's floating-point amortized code. The on-line zero mass is assumed, not proved. This is the closest prior art to Atlas, with the same architecture (prime side + zero intervals). |
| **FLINT/Arb** `acb_dirichlet_platt_*`, `zeta_zeros`, `zeta_nzeros` | n from 10⁴ to 10²³ | Platt's grid method / RS, plus Turing's method, in ball arithmetic | **Rigorous as a library** (as rigorous as the code) [S]. The docs say the Platt routines "expect 10⁴ ≤ n ≤ 10²³" and the large-height method works for "10¹¹ ≤ n < 10²³". I found **no paper that publishes a window** proved this way. |
| atlas_v5 (this project, Oct 2026, unpublished) | [10¹³, +2], [10¹⁴, +2] | explicit-formula LP + Arb sign changes, no zero list, no Turing count | yes (claims A and B), independently replayed, Lean file audit |

Other records (Wedeniwski/ZetaGrid, Franke et al. 10¹¹, van de Lune) all lie below 3·10¹². I found no rigorous, unconditional,
published verification of RH in any window above 3·10¹² other than Atlas's own unpublished v5 windows. Two caveats:
- The search was limited (§0). A recent arXiv preprint could have been missed.
- Polymath 15 (de Bruijn–Newman) used large-height barrier computations for a different function, H_t. I did not check them, and
  they are not a claim about ζ's zeros.

## 3. Algorithms and rigorous error bounds

- **Riemann–Siegel remainder bounds.**
  - Gabcke (Göttingen dissertation, 1979), quoted by Bober–Hiary §2 and by Hiary 2011 (1.4) [S, secondary]: explicit bounds for
    the remainder R_m(t) on the critical line for m ≤ 10, e.g. "if t ≥ 200, then |R₁(t)| < .053t^{−5/4}, |R₄(t)| < 0.017t^{−11/4}".
    At t ≥ 10¹⁵, one correction term already leaves |R₁| < 10⁻²⁰. The thesis itself was not read (403).
  - Arias de Reyna, "High precision computation of Riemann's zeta function by the Riemann–Siegel formula, I", Math. Comp. 80 (2011)
    995–1009: rigorous bounds for any number of terms, at σ + it. [S, FLINT docs] Arb's `acb_dirichlet_zeta_rs` takes its error
    bound from "Theorem 4.2" of that paper.
- **Arb's RS cost** (Johansson, "The Riemann–Siegel formula in Arb", 2016) [S]. Times for one ζ on 2016 hardware:
  - 18.5 s at 10¹⁶, 58.1 s at 10¹⁷, 279 s at 10¹⁸, 896 s at 10¹⁹, **2884 s at 10²⁰**;
  - the step from 10¹⁷ to 10¹⁸ jumps ×5 because of "switching to the less memory-intensive algorithm";
  - "In Arb, I have currently set the code to use at most 4 GB, switching to a slower algorithm that only performs partial sieving."

  Measured here (COST.md): Arb's footprint for one Z grows like √t, reaching **1.3 GB at 10¹⁶**. Arb as configured therefore exceeds
  this Mac's 2.5 GB cap at about 10¹⁷.
- **Odlyzko–Schönhage**: T^{1/2+ε} work to precompute, then many points almost for free. Platt's rigorous variant is in Arb as
  `platt_multieval`.
- **Hiary, "Fast methods to compute the Riemann zeta function", Ann. Math. 174 (2011), arXiv:0711.5005 [S].**
  - Theorem 1.1 computes ζ(1/2 + it) "to within ± t^{−λ} using ≤ A₁(log t)^{κ₁} t^{4/13} operations" (with precomputation). The
    second method has exponent 1/3.
  - The constants are "effectively computable" but **not explicit**. The paper aims at "provably efficient" techniques, not
    practical ones.
- **Hiary, "An amortized-complexity method…", Math. Comp. 80 (2011), arXiv:1002.2443 [S].** After T^{1/2+o(1)} work and T^{α+o(1)}
  storage, Z(t) on [T, T + T^α] costs T^{α+o(1)} per point. Constants are again not explicit. This is the [Zet] code behind HIK's
  10²⁸ data (about 600 M zeros near 10²⁸).
- **Bober–Hiary**:
  - Proposition 5.1 bounds the Taylor truncation error rigorously, but through an overestimate (M_max ≪ t^{1/6} log t). The working
    bound is heuristic ("cannot prove this"), and roundoff is controlled only heuristically.
  - Cost at 8·10³⁴: about 22.5 core-years for that range.
  - **No rigorous t^{1/3} implementation of ζ exists that I know of.**

## 4. What "first" can be claimed (decision)

The candidate claims are the 10¹⁵ and 10¹⁶ windows, if they close (RESULTS.md):

1. **Allowed, to our knowledge:**
   - "The highest-lying windows in which RH (all zeros on the line, simple, count matched) has been rigorously and unconditionally
     certified in published or publicly documented work."
   - "The first above 3·10¹² by a zero-list-free, Turing-free method."

   Every computation at greater height is either floating-point (Odlyzko, Gourdon, Bober–Hiary) or conditional on floating-point
   zero data (HIK, 10²⁸).
2. **Mandatory caveats, in the same sentence or paragraph:**
   - Arb/FLINT can certify such windows (Turing's method) by a library call, up to n ≈ 10²³. Atlas uses that as its independent
     cross-check (the count is matched).
   - RH at these heights is not a new fact about ζ in any strong sense. Non-rigorous checks reach 8·10³⁴.
   - The method's Lemma 2 / THEORY_V4 §10 are unreviewed.
3. **Not allowed:**
   - "first verification at height 10¹⁵/10¹⁶" (Gourdon's 2·10⁹ zeros near n = 10¹⁶ and 10¹⁷, i.e. t ≈ 1.9·10¹⁵ and 1.8·10¹⁶, are
     non-rigorous but exist);
   - "beyond Odlyzko";
   - "extends the RH verification height" (H stays 3·10¹²: a window is not an initial segment);
   - any statement implying Atlas is the only rigorous route.
4. **What would be a genuinely new record:** a rigorous unconditional window at n ≈ 10²⁰–10²³, Odlyzko's territory, or a rigorous
   version of HIK's 10²⁸ window, i.e. proving the sign changes it assumed. Both need a faster rigorous Z than Arb's single-point RS
   on this machine (COST.md).
