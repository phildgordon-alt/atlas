# Novelty check: GRH for ζ_K, K = Q(x³ − x − 1) (d_K = −23), to height 10⁴

Compiled 2026-10-10. This is literature diligence only: nobody was contacted.

**Claim tested.** Every zero of ζ_K with |Im s| ≤ 10⁴ lies on the critical line and is simple. Equivalently, the same holds for
L(s, ρ) = ζ_K/ζ = L(s, 23.1.b.a), plus RH for ζ. The draft also says: "to our knowledge this is the highest published
rigorous/verified height for this field."

**Prior art already logged, not redone here.**
- `../new_territory/PRIOR_VERIFICATION.md`: Tollis 1997 (93.81 in Table 6.2, 92 in the abstract); the LMFDB API; the code-implied
  CMF height b = 32; Das–Gaba–Lee–Savalia–Wong 2025 and Das–Kadiri–Ng 2025 still cite Tollis as the state of the art.
- `../new_territory/CITATION_USERS.md`: a forward-citation census of Tollis, Omar (×2), Booker 2006, Platt 2016, Best et al. (CMF),
  Büthe, Hiary–Ireland–Kyi and Platt–Trudgian, via Semantic Scholar and OpenAlex.
- `../new_territory/WAITING_DEMAND_2.md` and `../CORRECTIONS_2026-10-06.md`: Ng's 2000 thesis.

This pass extends those searches. It does not repeat them.

---

## 1. Searches performed (this pass)

WebSearch was unavailable: the session's 200-call cap was already used. Every source below was queried directly.

| Source | Queries / objects |
|---|---|
| **arXiv API** | `ti:"Dedekind zeta" AND abs:zeros` (27 hits, all read by title; none is a numerical verification) · `abs:Dedekind AND abs:"Riemann hypothesis" AND (verif* OR height)` · `abs:Artin AND abs:zeros AND abs:Turing` · `abs:"weight one" AND abs:zeros AND abs:L-function` · `abs:"Riemann hypothesis" AND abs:verification AND abs:L-functions` · `abs:"generalized Riemann hypothesis" AND abs:(verify\|verification)` · `abs:"Hecke L-function(s)" AND (zeros\|"Riemann hypothesis") AND (computation\|numerical)` · `abs:"Dedekind zeta" AND abs:Turing` · `abs:"Artin L-functions" AND "Riemann hypothesis" AND numerical` (0 hits) · `abs:"motivic L-functions"` with Bober/Booker/Platt (0 hits, so "Computing motivic L-functions" is still not on arXiv) · author lists in math.NT for **Platt** (25), **Booker** (39), **Bober** (17), **Hiary** (27), **Molin**, **Bucur** (incl. Bucur–Florea), **Lowry-Duda** (36), all read by title |
| **OpenAlex search** | "Riemann hypothesis Dedekind zeta verification" · "zeros Dedekind zeta functions critical line computation" · "Artin L-function zeros computation" · "weight one modular form L-function zeros" · "generalized Riemann hypothesis verified height number field" · "Turing method Dedekind zeta" · "Artin L-functions dihedral zeros numerical" · "zeros Hecke L-functions imaginary quadratic field numerical verification Riemann hypothesis" · "class group character L-function zeros computation imaginary quadratic" · "Isolating some non-trivial zeros of zeta" (top 25 per query, read by title) |
| **Google Scholar** (HTML) | `"Riemann hypothesis" "Dedekind zeta" "discriminant -23" zeros` (13 hits, snippets read) · `"Dedekind zeta" "GRH" "verified" "height" "Tollis"` · `"Artin L-function" "Riemann hypothesis" "interval arithmetic" zeros verified` · `"generalized Riemann hypothesis" "cubic field" "verified" "up to height"` · a conductor-23 / weight-one query (0 hits) · **all 47 Scholar citers of Ng's thesis** (cites=18399948250388898957, read by title) |
| **LMFDB** | API record `2-23-23.22-c0-0-0`; the HTML page `/L/2/23/23.22/c0/0/0` and its `/Reliability`, `/Source` and `/Completeness` subpages; knowl `lfunction.zeros`; `/L/NumberField/3.1.23.1/` (404) |
| **Full text read or grepped** | Ng thesis §4.3.4–4.3.5 (re-read, quotes below); Booker 2006 (math/0507502); Büthe 2015 (1308.6704); Hiary–Ireland–Kyi (2408.00187); Palojärvi–Zhao (2508.03023); **Amberger 2025 (2510.27444)**; **Bellotti–Wong 2026 (2606.31441)**; **Rubinstein 2004 survey (math/0412181)**; **Dokchitser 2002 (math/0207280)**; **Hayani 2024 (2404.06804)**; **Bradshaw PhD thesis 2010** (U. Washington, "Provable computation of motivic L-functions"); Platt–Trudgian 2020 (2004.09765); **Lagarias–Odlyzko 1979** (abstract via Crossref) |
| **Code / data** | GitHub `djplatt/code`: full tree of 4,226 paths, searched for artin / dedekind / cubic / hecke / 23. Found an `artin/` directory (Dirichlet-coefficient parser for LMFDB Artin reps) and nothing for d = −23 at height. Repo list for `djplatt` (arb_zeta, glfunc, glfunc_stripdown, code, lmfdb) |

---

## 2. Findings

| # | Source | Object | Height | Rigorous? | What it says (quote or paraphrase) |
|---|---|---|---|---|---|
| 1 | **Tollis**, Math. Comp. 66 (1997) 1295–1321, DOI 10.1090/S0025-5718-97-00871-5 | ζ_K, d = −23 (Table 6.2) | **93.81** (abstract: 92) | Yes, by the standards of 1997: Turing-type theorem plus Friedman's evaluation, with error analysis. Not interval arithmetic. | "a computation which established the GRH to height 92 … for cubic … fields". Table 6.2 row: `x3 + x2 − 1  −23  93.81  121  5.11568`. Already logged. |
| 2 | **N. Ng**, PhD thesis, UBC 2000, "Limiting distributions and zeros of Artin L-functions", §4.3.4–4.3.5 (pp. 66–68) | L(s, f₂₃) = ζ_K/ζ, d = −23; also −31, −59, −83 and f₁₄₄ | **972.2** (N(T) = 1736) | **No.** Maple and C floating point. Zeros "only good to 10 decimal digits" (§5, line ~5806 of the text). The completeness step uses Tollis's Thm 4.3.1 on floating-point Gram-block data. | "This example shows how RH was verified for f23, f31, f59, and f83." Table: "23  972.2  1736  5.1156833287". "N(T) is the number of zeros to height T. This has been verified by Tollis' theorem in the preceding section." The worked example is f₃₁ to T = 1000. f₂₃ is asserted, with no worked detail. |
| 3 | **LMFDB**, L-function 2-23-23.22-c0-0-0 (= 23.1.b.a = Artin 2.23.3t2.b.a); Reliability page | L(s, ρ) | 10 positive zeros, max **18.0807**. Plot to t ≈ 28–33. | Interval arithmetic for zero **locations and completeness of the list**, but **explicitly not RH** | Reliability page, verbatim: "precomputed using rigorous precision bounds and interval arithmetic … and that the list of zeros is complete (within the region covered by the list, including the lowest zero). Each zero is known to lie within a disc whose radius is determined by the displayed precision, **but note that this is not sufficient to prove that the [zeros] lie on the critical line**." Source: "computed by Edgar Costa using source code provided by David Platt." The API has no field for rigor or height. |
| 4 | **LMFDB**, Completeness page | Dedekind zetas of cubic fields with \|D\| ≤ 368 | Dynamic | **No** | "51 dynamically computed Dedekind zeta functions of the cubic fields … The pages for dynamically computed L-functions … may be less accurate than the displayed precision suggests." `/L/NumberField/3.1.23.1/` returns 404. |
| 5 | **Best et al.**, "Computing classical modular forms" §10.3 (arXiv:2002.04717) | All CMF L-functions incl. 23.1.b.a | Unstated "b". Code implies 64/degree = 32. | Büthe-method completeness check | Already logged (PRIOR_VERIFICATION.md). Taken together with row 3, it does not reach 93.8. |
| 6 | **Booker**, Exp. Math. 15 (2006), math/0507502 | ζ_K of a few **S5 and A5** fields | \|Im s\| ≤ 100 | Yes (rigorous FFT algorithm) | "numerical results of tests of the Riemann hypothesis for a few S5 and A5 extensions in the region \|ℑ(s)\| ≤ 100." No cubic or dihedral field. |
| 7 | **Lagarias–Odlyzko**, Math. Comp. 33 (1979) | L = ζ_L/ζ for the pure cubic fields Q(a^{1/3}), a = 2, 3, 6, 12 | \|t\| ≤ 15 | Classical | "all of the zeroes … with \|t\| ⩽ 15 are simple and lie on the critical line". Not d = −23. This is the historical first S3 case. |
| 8 | **Büthe**, Math. Comp. 84 (2015), 1308.6704 | Method for Hecke and Artin L-series and EC | — | Method only | Specifies the method "for Hecke L-series and L-functions of elliptic curves". No d = −23 computation. |
| 9 | **Hiary–Ireland–Kyi**, arXiv:2408.00187 (Math. Comp.) | Dirichlet; EC 37.a1 | Low heights | Yes | No Artin, Dedekind or weight-1 example in the text. |
| 10 | Platt, Math. Comp. 85 (2016) (1305.3087); Platt–Trudgian BLMS 2021 (2004.09765); **Platt, Math. Comp. 86 (2017) "Isolating some non-trivial zeros of zeta"** | Dirichlet L; ζ | ζ: 3·10¹² (RH); isolation of every zero ≤ 3.06·10¹⁰ | Yes (interval) | Degree 1 only. Platt 2017 is the citable source for **simplicity** of ζ's zeros at height ≤ 10⁴: "isolate the non-trivial zeros of zeta with imaginary part ≤ 30,610,046,000 to an absolute precision of ±2⁻¹⁰²". Platt–Trudgian alone states only β = 1/2, not simplicity. |
| 11 | Amberger, arXiv:2510.27444 (2025); Bellotti–Wong, arXiv:2606.31441 (2026); Palojärvi–Zhao, arXiv:2508.03023; Hasanalizade–Shen–Wong 2021; Trudgian 0903.1885 / 1206.1844 | N(T) bounds and Turing-method inputs for Dedekind and Artin | — | Theory | No zero verification anywhere in these papers. They are inputs a verifier would use. |
| 12 | Rubinstein survey (math/0412181); Dokchitser 2002; Bradshaw thesis 2010; Cohen 2019 "Computational Number Theory in Relation with L-Functions" (Scholar snippet only) | Algorithms and examples | — | Mostly non-rigorous (Bradshaw: rigorous special values) | No RH-to-height claim for d = −23. Cohen's notes use the d = −23 cubic as an example (snippet), very likely via PARI lfun. The full text was not read (Springer, paywalled). |
| 13 | Citers of Ng's thesis (47, Google Scholar) | Chebyshev-bias and race papers (Bailleul, Fiorilli–Jouve, Devin, Hayani, HKMS, Das–Kadiri–Ng, …) | — | — | None re-verifies or extends Ng's zero lists rigorously. Hayani 2404.06804 is theoretical. Comparative-PNT papers take zeros from Sage, lcalc or LMFDB (WAITING_DEMAND_2 §1, item 6). |
| 14 | `djplatt/code`, `djplatt/glfunc`, `edgarcosta/lfunctions` | Rigorous degree-2 code | Hard-wired height of 64/degree (already logged) | — | No d = −23 or Artin high-height run was found in the public trees. |
| 15 | Marshak, "A Survey of Results Regarding a Computational Approach to the Zeros of Dedekind Zeta Functions", Cornell 2007 (Scholar snippet) | Survey | — | — | The snippet cites Tollis as the reference for zero computations. Not read in full. |

**Not found anywhere:** a rigorous verification for d = −23, for 23.1.b.a, for the Hecke L-function of the cubic class-group
character of Q(√−23), or for the Artin representation of conductor 23, above **93.81**. No source at all, rigorous or not, claims a
height above **972.2**. No general theorem verifying GRH for all small-discriminant cubic fields beyond Tollis's 92 was found. No
"Computing motivic L-functions" (Bober–Booker–Costa–Lee–Platt–Sutherland) preprint exists on arXiv.

---

## 3. Verdict

1. **Rigorous height.** Supported. The highest published rigorous verification for this ζ_K is Tollis 1997 at **93.81** (92 in the
   abstract). LMFDB/CMF covers only completeness of the zero list to ~18–32, and LMFDB explicitly disclaims RH. 10⁴ is about 100×
   the previous rigorous height.
2. **"Highest published verified height", rigorous or not.** Supported for every claim we could find. Ng 2000 claimed RH to 972.2
   using floating point. 10⁴ exceeds that by about 10×. Unpublished non-rigorous zero lists (lcalc, PARI `lfunzeros`, LMFDB plots)
   to larger heights may exist. They are not *verifications*, but the wording should not imply that nobody has ever *computed*
   zeros this high.
3. **"Every zero of ζ_K … is simple": the wording outruns what was proved.** `RESULTS.md` proves on-line **and simple** for
   L(s, ρ), and **on-line only** for ζ_K (via Platt–Trudgian). Simplicity of ζ_K's zeros needs two more inputs:
   - (a) ζ's zeros at height ≤ 10⁴ are simple. This is citable: Platt 2017, Math. Comp. 86, isolates every zero to 3.06·10¹⁰.
     Platt–Trudgian alone does not state it.
   - (b) ζ and L(ρ) share **no** zero with |t| ≤ 10⁴. I found no record that Atlas checked (b) for the flagship.
     - `races/RESULTS.md` checks only L(χ_d) against L(ρ), and only to 200.
     - (b) is cheap: compare the 25,275 certified L(ρ) isolating intervals with rigorously isolated ζ zeros (Platt / arb_zeta).
       Until it is done, claim simplicity only for L(ρ).
4. **The broader claim in RESULTS.md**, "first rigorous verification of GRH to this height for a non-Galois number field's
   Dedekind zeta", is *plausible but less thoroughly searched*.
   - The rigorous non-abelian results found are Tollis (92–94; cubic and quartic), Booker 2006 (S5/A5, 100) and Lagarias–Odlyzko
     (15).
   - Dihedral Artin L-functions are Hecke L-functions over imaginary quadratic fields. No rigorous high-height verification of those
     was found either.
   - Present it as "to our knowledge", with the search scope stated.

### Recommended wording

> **Theorem.** Let K = Q(α), α³ = α + 1 (d_K = −23), and let ρ be the 2-dimensional irreducible representation of
> Gal(K̃/Q) ≅ S₃, so that L(s, ρ) = ζ_K(s)/ζ(s) = L(s, g) for the weight-1 newform g = η(z)η(23z) (LMFDB 23.1.b.a). Every zero of
> L(s, ρ) with |Im s| ≤ 10⁴ lies on Re s = 1/2 and is simple; there are 25 275 with 0 < Im s ≤ 10⁴. Combined with Platt–Trudgian
> (RH for ζ to 3·10¹²), GRH holds for ζ_K for |Im s| ≤ 10⁴.
>
> **Context.** To our knowledge this is the first interval-arithmetic-certified verification of GRH for this field beyond Tollis's
> 93.81 (Math. Comp. 1997; "height 92" in his abstract), and it exceeds the highest previously published verification claim for this
> field, Ng's floating-point check to height 972.2 (PhD thesis, UBC 2000, §4.3.5), by a factor of about 10. LMFDB lists the first
> 10 zeros of L(s, 23.1.b.a) (to t ≈ 18.08) with interval-certified locations and completeness of the list in that range, but does
> not claim that they lie on the critical line.

Only if check 3(b) is done and passes, add: "… and every zero of ζ_K with |Im s| ≤ 10⁴ is simple (using Platt 2017 for ζ, and
the disjointness of the certified zero sets of ζ and L(s, ρ))."

**Avoid:**
- "highest height ever computed";
- "first verification above Tollis" (Ng was first, non-rigorously);
- "every zero of ζ_K is simple" (until 3(b) is done);
- citing Platt–Trudgian for simplicity of ζ's zeros.

---

## 4. Residual uncertainties (need an expert or a paywalled source)

1. **Unpublished rigorous runs.** Platt, Costa, Booker or Bober could have run glfunc/lfunctions on 23.1.b.a far beyond 32 without
   publishing it. "Computing motivic L-functions" is still unpublished, and its per-form heights are unknown. Only the authors can
   say. (Contacts are listed in PRIOR_VERIFICATION.md; none was contacted.)
2. **MathSciNet / zbMATH.** Neither was accessible. A forward search on Tollis 1997 and on the Ng thesis there might surface
   non-arXiv journal papers, such as small-journal computational notes or Japanese/Chinese-language work. The Semantic Scholar,
   OpenAlex and Google Scholar citer lists were covered (CITATION_USERS.md and row 13 here).
3. **Paywalled texts not read in full:**
   - Cohen 2019 (Springer), which uses d = −23 as an example;
   - Marshak 2007 (survey; snippet only);
   - Omar 2001, Exp. Math. "On Artin L-functions for octic quaternion fields" (quaternion fields; d = −23 not expected);
   - Pohst–Zimmer 1996.
   None is expected to contain a d = −23 verification above 94. That is an inference from titles and snippets, not a reading.
4. **Theses.** Omar's thesis (Bordeaux, about 1998–2000, first zeros of ζ_K) and Molin's thesis (Bordeaux 2010) were not obtained.
   Both are about low zeros or methods, not high-height RH.
5. **Ng's rigor.** Read as non-rigorous: Maple floating point, about 10 digits, no interval arithmetic stated. An expert might count
   it as "verified" in the 2000-era sense. Atlas's wording should therefore credit Ng's claim and stress certification, not
   priority of height.
6. **Atlas-internal (not literature, flagged for completeness):**
   - Above t = 700 the replay shares code with the generator (RESULTS.md §4).
   - Simplicity rests on Lemma 2 (parity), which has been Lean-checked at the logic level; independent expert review is still
     advised (CORRECTIONS_2026-10-06).
   - These do not change novelty, but a referee will ask about them.
