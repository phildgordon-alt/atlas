# Novelty note, M10 (2026-11-02): the [10²⁵, 10²⁵+100] window (888 zeros)

Update to NOVELTY_M6.md (2026-10-23), RESULTS_M5_1e20.md §3 and record_heights/PRIOR_ART.md (2026-10-18). Literature only, no
compute. No one was contacted.

## 0. Sources and how they were checked (2026-11-02)

- **Bober–Hiary**, arXiv:1607.00709 (Exp. Math. 27 (2018)). Full PDF fetched today and the text extracted with pypdf. All quotes
  below are **[S]**, read in the source today.
- **Hiary–Ireland–Kyi (HIK)**, arXiv:2408.00187 (v1 only, 31 Jul 2024; Math. Comp. 2026, doi 10.1090/mcom/4129). Full PDF
  fetched today **[S]**.
- **OpenAlex** (works published since 2024-06 / 2025-01). Queries:
  - "riemann zeta zeros computation";
  - "riemann hypothesis verified height";
  - "zeros zeta critical line large height computation";
  - "turing method zeta zeros rigorous";
  - author filters Hiary / Platt / Bober.

  Abstracts of the relevant hits were read.
- **arXiv**:
  - the arXiv API still returns empty bodies (same as on 10-18 and 10-19);
  - the arXiv web search ("Riemann zeta zeros verification", newest first) worked;
  - two WebSearch queries were also run.
- **FLINT**: GitHub releases API.
- **Not re-read**:
  - Odlyzko's PDFs (Type-3 fonts, no extractable text);
  - Gourdon's site (unreachable on 10-23);
  - the FLINT per-function docs pages (moved; 404). The height range of FLINT's zero routines is taken from PRIOR_ART.md
    (10-18) **[P]**.

Tags: **[S]** read in the source today. **[P]** from an earlier project note that read the source. **[I]** my inference.

**Height bookkeeping.** At t = 10²⁵, N(t) ≈ 8.71·10²⁵. The window is therefore at zero index about 8.7·10²⁵. Bober–Hiary's
zero number 10²⁶ lies at t ≈ 1.145·10²⁵, essentially the same height.

## 1. Prior works

| work | height (t) | rigorous? | what exactly is verified | citation |
|---|---|---|---|---|
| Platt–Trudgian | initial segment to 3.0002·10¹² | **Yes** (Arb interval arithmetic + Turing variant) | RH for all zeros with 0 < γ ≤ 3 000 175 332 800 | Bull. LMS 53 (2021), arXiv:2004.09765 [P] |
| Platt | initial segment to 3.06·10¹⁰ | **Yes** | zeros isolated rigorously | Math. Comp. 86 (2017) [P] |
| FLINT/Arb `acb_dirichlet_platt_*`, `zeta_zeros`, `zeta_nzeros` | documented for n up to ≈10²³ (t ≈ 1.3·10²²) | rigorous as a library | a tool, not a result: **no paper publishes a window proved this way** | FLINT docs [P]. dfloat is still unreleased: the latest release is v3.6.0 (2026-06-29) [S] |
| Odlyzko 1989–2001 (and later) | zeros near n = 10²⁰, 10²¹, 10²², 10²³ (t up to ≈1.3·10²²); secondary reports of zeros near n ≈ 10³² | **No** (Odlyzko–Schönhage in floating point) | zero lists and statistics | [P]; secondary sources only |
| Gourdon (with Demichel) 2004, unrefereed | first 10¹³ zeros; 2·10⁹ zeros near n = 10¹³ … 10²⁴ (t ≤ ≈1.25·10²³) | **No** ("classic double floating point"; by his own account not "proved" in a strong sense) | zero lists | manuscript, 2004 [P] |
| **Bober–Hiary** | **t from 10²⁴ to 8·10³⁴**; Table 3 lists zeros n = 10²⁵, **10²⁶ (t ≈ 1.145·10²⁵)**, 10²⁷ … 10³⁶ | **No** (see §2) | "checked the Riemann Hypothesis for more than 50000 zeros in over 200 separate small intervals" | Exp. Math. 27 (2018), arXiv:1607.00709 [S] |
| **HIK** | window y = 10²⁸ + 501675.8, about 1.4·10⁶ zeros (also 989 881 zeros for η = 49650) | **Conditional** | explicit-formula positivity in mpmath interval arithmetic, but the zero intervals come from floating-point data: "Our working assumption is that the zeros ordinates from [LMFDB] and [Zet] are accurate within ±10⁻¹⁰" [S] | Math. Comp. (2026), doi 10.1090/mcom/4129; arXiv:2408.00187 |
| Hasanalizade–Shen–Wong; Trudgian; others | — | rigorous | explicit bounds on N(T) and S(T): inputs to Turing-type methods, not window verifications | [P] |
| 2025–26 Zenodo/preprints (e.g. Rafiq, zenodo 23447265; zenodo 22183395) | just above 3·10¹² | **No** (mpmath, residual checks). Rafiq states that rigorous exclusion "would require ... Turing method or Arb interval arithmetic" [S] | a few zeros | Zenodo 2026 |
| Farmer, Bull. AMS (2026), doi 10.1090/bull/1890 | — | survey | about computational evidence; no new verification | [S, abstract] |
| Atlas (this project, unpublished) | windows at 10¹³–10¹⁸, 10²⁰–10²⁴ (100 units at 10²²), now **[10²⁵, 10²⁵+100]** | yes (Arb/ball arithmetic, replayed, Lean-audited) | all zeros in the window on the line and simple; 888 zeros | RESULTS_M10.md |

No 2025–2026 arXiv, OpenAlex or Zenodo item found reports a rigorous, unconditional zero verification above 3·10¹², at 10²⁵ or
anywhere else. The only hits were non-rigorous computations just above 3·10¹², proof claims, and surveys.

## 2. Bober–Hiary: rigorous or not? Not rigorous, in their own words [S]

**Claim.**
- "we have checked the Riemann Hypothesis for more than 50000 zeros in over 200 separate small intervals with values of t ranging
  from 10²⁴ to 8×10³⁴."
- The highest such zero is n = 10³⁶ + 42420637374017961984 at t ≈ 8.1·10³⁴.
- The counting uses Turing's method on the computed values.

**Truncation error.**
- What they proved: "The bound M_max(t) that we proved is of the form ≪ t^{1/6} log t, which we know is a significant
  overestimate."
- What they use: "In practice, ε_J(t) is bounded by something like c_max(J,t)·√log(N/v₀), **though we cannot prove this**."

**Roundoff.**
- Worst case: "≤ 0.05εt^{1/6}".
- But: "In practice though, this maximal size is never reached. Instead, due to pseudorandom nature of roundoff errors, one observes
  square-root cancellation … So the cumulative error is **typically** ≤ 0.0011ε."

**Multi-evaluation.** "Almost surely the cumulative error will be significantly below the maximal size (29)."

**Precision.**
- "we **expect** to be able to compute up to an absolute precision of around 10⁻¹⁰ with our implementation".
- On doubles: "We **hope**, at least, that our implementation will return NaN in such a case, rather than returning a wrong answer."

**Summary.** "In summary, we **expect** the values of Z(t) that we computed to be accurate to within ±10⁻⁷ typically, and accurate
to within ±10⁻⁵ in the worst cases. The bulk of the error comes from the practical truncation error."

**Verdict.**
- These are careful floating-point computations with heuristic ("practical") error control. They are not certified: there is no
  interval arithmetic and no proven error bound on the values actually used.
- Their "checked RH" at 10²⁴–8·10³⁴ is therefore non-rigorous. This includes zero n = 10²⁶ at t ≈ 1.145·10²⁵, the same height as
  the M10 window.
- The full error budget is not stated as rigorous anywhere in the paper.
- **Consequence for Atlas.** Zeros at height 10²⁵ (and far above) have been computed before, and RH has been "checked" there in
  the non-rigorous sense. M10 is **not** a new height for zero computation.

## 3. Verdict

**Status of the claim.** To our knowledge (searches of 2026-11-02, with the limits in §0), no published or publicly documented
work contains a rigorous, unconditional verification of RH in any window at height ≥ 10²⁵. Nor, as recorded in the earlier notes,
does any such work exist above 3·10¹² apart from Atlas's own windows.

Everything at or above this height is one of two kinds:
- floating-point/heuristic: Bober–Hiary 10²⁴–8·10³⁴, Odlyzko's reported samples;
- conditional on floating-point zero intervals: HIK, 10²⁸.

**A small change from M6.** FLINT's documented zero-isolation routines target n ≲ 10²³. The window at n ≈ 8.7·10²⁵ is outside
their documented range [P/I]. So the old caveat "Arb can certify such windows by a library call" no longer applies literally at
10²⁵. It should become: "general-purpose rigorous tools (Arb's Riemann–Siegel evaluation plus a Turing-type count) could in
principle certify such windows at much greater cost." This does not support any claim that Atlas is the only rigorous route.

**Recommended wording (safest accurate).**

> "All 888 zeros of ζ(s) with imaginary part in [10²⁵, 10²⁵+100] lie on the critical line and are simple. This is certified
> unconditionally with ball arithmetic, independently replayed and Lean-audited, using Atlas's zero-list-free, Turing-free
> explicit-formula certificates. To our knowledge (literature check of 2 Nov 2026), this is the highest window in which RH has been
> **rigorously and unconditionally** verified in published or publicly documented work. Zeros at this height and far above have
> previously been computed **non-rigorously** (Bober–Hiary 2018, heights 10²⁴–8·10³⁴). Hiary–Ireland–Kyi (Math. Comp. 2026)
> treat a window near 10²⁸ **conditionally** on floating-point zero data. The rigorous initial segment H = 3·10¹² (Platt–Trudgian
> 2021) is unchanged."

**Shorter variant.** "the highest rigorous, unconditional RH window we are aware of (as of Nov 2026)", followed in the same
paragraph by the Bober–Hiary and HIK caveats.

**Also allowed.** "the first rigorous, unconditional RH window at height 10²⁵ by a zero-list-free, Turing-free method." This is
narrower and is true as far as we know.

**Forbidden phrasings.**
- "first at 10¹⁵", or "first verification at 10²⁵" without "rigorous, unconditional" and "to our knowledge". The unqualified forms
  are false: Bober–Hiary checked RH, non-rigorously, at 1.1·10²⁵.
- "first zeros computed at 10²⁵", or "new height for zeta zeros". Both are false: Bober–Hiary reached 8·10³⁴.
- "beyond Odlyzko", "beyond Bober–Hiary", "beyond HIK", or "highest RH verification" without "rigorous unconditional".
- "extends H", "RH verified to 10²⁵", or "RH true up to 10²⁵". A window is not an initial segment; H stays 3·10¹².
- "the only rigorous method", or "cannot be done with Arb/FLINT".
- "Bober–Hiary's results are wrong/unreliable". Say only "not rigorous (heuristic error control, as they state)".
- "HIK is non-rigorous". Say "conditional on floating-point zero ordinates".
- Any novelty claim for the ζ-evaluation core (fast rigorous RS). Prior art: FLINT dfloat, dev branch, still unreleased as of
  v3.6.0.

**Caveats to keep attached.**
- zfast is in the trust base.
- The arXiv API was unavailable (web search and arXiv site search only), so a missed preprint is possible.
- Odlyzko's and Gourdon's texts were not re-read today.
