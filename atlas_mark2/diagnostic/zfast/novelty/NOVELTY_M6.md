# Novelty note, M6 (2026-10-23): windows at height 10²⁴ and the "Gourdon height"

Update to RESULTS_M5_1e20.md §3 (2026-10-19). New files only.

**Sources (read-only; no one contacted).**
- Web search (US index), 2026-10-23: Gourdon's 2004 manuscript is widely cited as "The 10¹³ first zeros of the Riemann zeta function,
  and zeros computation at very large height" (Oct. 24, 2004; numbers.computation.free.fr; the site refused the connection today, so
  the PDF itself was not re-read). Secondary sources (Wolf, arXiv:0910.1534; the survey arXiv:1810.05244; MathWorld news 2004-11-08):
  Gourdon and Demichel computed the first 10¹³ zeros and "two billion zeros from the 10²⁴-th zero", with the Odlyzko–Schönhage
  method, plus "tens of billions of zeros around the 10²³-th and 10²⁴-th", and Odlyzko's "hundreds of zeros near zero number 10³²".
- Platt–Trudgian, arXiv:2004.09765 (Bull. LMS 2021): rigorous to height 3·10¹² remains the rigorous initial segment.
- No search result reports a rigorous (interval-arithmetic, unconditional) verification at heights 10²³–10²⁴ (as of 2026-10-23).
  The arXiv API and the Gourdon site were not reachable; this is the same limitation as in the M5 note.

**Two facts that matter for the framing.**
1. **Gourdon's "10²⁴" is a zero index, not a height.** The 10²⁴-th zero lies at t ≈ 1.248·10²³ (Riemann–von Mangoldt, solved
   today); the 10²³-th at t ≈ 1.307·10²²; the 10²²-th at t ≈ 1.37·10²¹. Atlas's certified 10²³ windows (height 10²³, zero index
   ≈ 7.98·10²³) are therefore slightly **below** Gourdon's highest sampled region in height, and the M6 windows at height 10²⁴
   (zero index ≈ 8.34·10²⁴) are about **8× above** it in height (8.3× in index). Odlyzko's and Bober–Hiary's regions are higher still
   (Bober–Hiary 2018: heights up to ≈ 8·10³⁴, non-rigorous as they state).
2. **Those computations were not rigorous** in the sense used here: floating-point Odlyzko–Schönhage evaluations with heuristic
   error control (Gourdon's manuscript is unrefereed; Bober–Hiary write that they "cannot prove" their truncation error). They are
   evidence of the same kind as Atlas's own non-rigorous scan (THEORY_M5 §3); the certified windows are a different kind of statement:
   every zero in the window is on the critical line and simple, with Arb balls, independent replay, Turing cross-count and a Lean
   audit of the combinatorics.

**Statement (to our knowledge, as of 2026-10-23, with the caveats below).** The M6 windows at height 10²⁴ would be the highest
rigorous, unconditional RH windows in published or publicly documented work, above Gourdon's highest (non-rigorous) region in height
and index, and the 10²³ close pairs lie inside Gourdon's "tens of billions of zeros around the 10²⁴-th" region at a height he did not
treat rigorously.

**Caveats that must accompany any statement (unchanged from M5, plus one).**
- Arb's Turing-method routines, and FLINT-dev's dfloat versions once released, can certify such windows given memory and time; the
  method class (Platt; FLINT dfloat) is not new.
- Non-rigorous computations go far higher (Odlyzko 10²⁰–10²², Gourdon 10²³–10²⁴ by index, Bober–Hiary 8·10³⁴ by height).
- HIK's 10²⁸ window (Math. Comp. 2026) is conditional.
- zfast is in the trust base (review2: no critical findings for v12a; v13b adds the m1–m4 fixes; the 10²⁴ error budget is in
  PREDICTIONS_M6 §0 and RESULTS_M6).
- The literature check was limited (arXiv API and Gourdon's site unreachable; web search only).
- **New:** "Gourdon's height 10²⁴" is a misnomer; comparisons must say "the 10²⁴-th zero (t ≈ 1.25·10²³)".
