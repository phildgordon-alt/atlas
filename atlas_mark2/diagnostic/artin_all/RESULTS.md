# artin_all: Artin's conjecture for the 186 S5 quintic fields of calegari3 (2026-10-19)

Files:
* `THEORY.md`: the theorem applied, with verbatim quotations, and why dropping Frob_5 needs nothing else.
* `PREDICTIONS.md` (+ `PREDICTIONS.sha256`, which still verifies). Written before V1 and before any certificate ran.
* Code:
  * `algebra_flint_all.py`, `algebra_pari_all_v2.py`, `gt_tame_check_v2.py`, `verify_all.py`, `run_all.sh`, `run_negctl.sh`.
  * Copied unchanged from artin_literal (sha256 identical): `cert_FE.py`, `zFE.py`, `grouptheory.py`, `validate_coeffs.py`.
  * Superseded, kept: `algebra_pari_all.py` (v1, never run) and `gt_tame_check.py` (v1, matched nothing because of a list/tuple
    comparison; its output `runs/gt_tame_check.json` is empty).
* Outputs: `runs/`. Per-field table: `runs/summary.md`. Logs: `logs/`.

Rules followed:
* Nothing was contacted or posted, and nothing outside this directory was modified, except one appended row in
  `../new_territory/TARGETS_LEDGER.md`.
* One heavy process at a time, nice 19, watchdog FP_MB = 2000.

## 0. Bottom line

For **every one of the 186 fields** in `../general_eval/calegari3/runs/list_all.txt`, every hypothesis of **Theorem C** (THEORY.md §3)
holds:
* **(G)** Gal(K̃/Q) ≅ S5;
* **(C)** complex conjugation is in (12)(34), i.e. signature (1,2);
* **(A)** **ζ_H(σ) < 0 for all σ ∈ (0,1)**, where H is the degree-12 field K̃^{D5} = F·E.

These are all S5 quintic fields of signature (1,2) with d ≤ 2·10⁴ in LMFDB (174), plus the 12 literal fields with 2·10⁴ < d ≤ 4·10⁴.

**Statement obtained, split by route (modulo §5):**

> **(a) 15 literal fields** (8249, 17744.3, 19876, 25624, 27029, 27364, 27881, 29081, 30301, 32069, 33616, 34189, 37156, 38069, 38189):
> by Calegari, Math. Ann. 356 (2013), Thm 1.1 and Thm 1.2 **as published** (`../artin_literal/`), every irreducible representation of
> Gal(K̃/Q) is modular.
>
> **(b) the other 171 fields:** by Calegari's Thm 1.1/1.2 **with Lemma 3.2 supplied by Pilloni–Stroh, Astérisque 382 (2016), Thm 0.3**,
> every irreducible ρ of Gal(K̃/Q) ≅ S5 is modular. This is the substitution of Khare–La Rosa–Wiese, Expo. Math. 2023, Thm 1.2 and
> remark, also remarked by Dwyer 2014. It removes hypothesis (2), "unramified at 5, Frob_5 ∈ (12)(34)".
> * 153 of these fields have 5 unramified with Frob_5 ∈ 3A (11), 4A (44), 5A (60) or 6A (38).
> * 18 have 5 ramified: d = 2665, 5025, 7265, 8105, 8705, 8945, 9065, 10825, 12205, 12440, 12785, 15705, 16085, 17145, 17245, 17725,
>   18485, 19280.
>
> In both cases: for every irreducible ρ there is an automorphic π on GL(dim ρ)/Q with L(π,s) = L(ρ,s), cuspidal if ρ ≠ 1. In particular
> **the Artin conjecture holds for every representation of Gal(K̃/Q)**, and ζ_M/ζ is entire for every subfield M ⊆ K̃.

Notable fields:
* **5.1.2869.1 = Q(x⁵ − x − 1)** (PARI nfisisom). This is the Khare–La Rosa–Wiese field. They prove ρ4 weakly modular there; Frob_5 is a
  5-cycle. Under (b), the full Artin conjecture follows for its S5 closure.
* **5.1.1609.1** is already Calegari's Thm 5.1, via Booker and Sasaki Thm 2. Here it is re-derived via (b).

## 1. Algebra (exact; two routes; `runs/algebra_flint.json`, `runs/algebra_pari.json`, `runs/pari/`)

* **Route 1 (python-flint; artin_literal helpers imported read-only):** 186/186 pass:
  * f irreducible, with a transposition Frobenius, so Gal = S5;
  * exact Sturm count gives 1 real root, so c ∈ 2B; d > 0, so E is real;
  * sextic g and degree-12 h = g(x²) from certified Arb roots: irreducible, signatures (2,2) and (4,4);
  * a K10 polynomial is irreducible (stored by calegari2 for 161 fields, built from certified roots for the 25 E2 fields);
  * Frobenius consistency f/g/h/K10 and parity against (D_E/p) at 421–427 good p < 3000 per field: 0 failures.
* **Route 2 (PARI 2.17.2):** 186/186 pass:
  * polgalois(f) = S5, polgalois(g) = PGL(2,5), polsturm(f) = 1, nfdisc(f) = d;
  * F ⊂ H, E ⊂ H, K ⊄ H;
  * |d_H|·d_K = D_E·|d_F|·|d_K10|;
  * the local identity Z_H Z_Q Z_K = Z_F Z_E Z_K10 at every p | 5·disc f;
  * ζ_H ζ ζ_K = ζ_F ζ_E ζ_K10 coefficientwise for n ≤ 2·10⁴;
  * dirzetak(F), dirzetak(H) = the local-factor rule for n ≤ 2·10⁴.
* **Group-theoretic check of the ramified F, H data:** at every ramified prime, including p = 5 in the 18 fields where 5 ramifies, the
  F and H patterns are derived from PARI's K, K10, E data and compared with PARI's own F and H data.
  * 185 fields: the derivation is unique and agrees with PARI.
  * 17145 at p = 3 (e = 4): three (D, I) pairs fit. Adding the tame relation φσφ⁻¹ ≡ σ³ (mod P) (`gt_tame_check_v2.py`) leaves one,
    and it agrees with PARI.
* Frob_5 (recorded only): 2B 15, 3A 11, 4A 44, 5A 60, 6A 38, ramified 18. **No field has Frob_5 ∈ {1, 2A}.** We have not checked why;
  presumably small discriminant discourages 5 from splitting into ≥ 3 degree-1 primes.

## 2. Hypothesis A: ζ_H(σ) < 0 on (0,1)

* **Identity (exact):** ζ_H = ζ_F ζ_E ζ_K10 / (ζ ζ_K) (THEORY §5).
* **Inputs per field:**
  * ζ_K10 < 0 and ζ_K < 0: calegari3, 186 fields, sets A and B, sha256 matched against calegari3/SHA256SUMS;
  * ζ_F < 0 and ζ_E < 0: artin_literal for its 15 fields (sha256 matched) and **here for the other 171**.
* **New certificates:**
  * 342/342 runs CERTIFIED: 171 fields × sets A and B, i.e. 684 objects (ζ_F degree 6 with N = |d_F| from 2.3·10⁸ to 7.95·10¹²;
    ζ_E degree 2).
  * Same `cert_FE.py` as artin_literal (calegari3 method: σ(1−σ)I_1(σ) < R on a cover of [1/2,1], R solved and checked at 3 points).
* **`verify_all.py`** re-reads all 186 × 2 × 4 certificate JSONs and checks:
  * the exact cover, every piece positive, R > 0, residue checks overlapping, and the verdict;
  * N = the independently computed |d_F|, D_E, |d_K10|, d_K, and Γ-shifts = the signatures;
  * sha256 of the inherited files, and A/B overlap.
  * Result: **186/186 fields have ζ_H < 0 on (0,1); Theorem C applies to 186/186. Calegari as published applies to 15.**
* **Two near-misses, still certified:**
  * **13116.1:** ζ_F(1/2) = −0.05386124190(±6e−12). Set A min margin is 0.78 (out of R ≈ 4.7·10⁴), on a bisected piece near
    σ ≈ 0.52 (79 pieces). Set B margin is 27.9.
  * **18485.1:** ζ_F(1/2) = −0.0210715966(±3e−12). Margins A/B are 2.10 / 2.03.
  * These ζ_F are the closest to having a real zero in (0,1) among the 186. The enclosures are rigorous, and both sets agree.

## 3. Prediction outcomes (PREDICTIONS.md)

| # | outcome |
|---|---|
| V1 sieve = PARI dirzetak, n ≤ 10⁵, F and E, 186 fields | **Met** (ALL_MATCH, both block sizes; includes the 18 fields where 5 ramifies and the 6 with index > 1) |
| V2 residue checks; R rel. radius F ≤ 1e−9, E ≤ 1e−8 | Checks overlap in 342/342 runs: **met**. F ≤ 2.4e−12: **met**. E: **missed** in 11/342 runs (max 2.6e−8) |
| V4 A/B overlap at 5 points | **Met**, 171/171 (186/186 with artin_literal) |
| P1 all certified | **Met**: 684/684 objects |
| P2 margin > 1; set A argmin on the σ = 1/2 piece | Margin > 1 **missed** once (13116 A, 0.78 > 0). Argmin **missed** for 2/171 in set A (13116, 18485). Set B: 48/171 on the first piece (as anticipated) |
| P3 cost | Wall 9.0 h (06:32–15:31). The predicted 12–30 h was **missed** (faster): median time ratio vs calegari3 0.48, max 1.03 (≤ 1.3 **met**). Peak footprint 1191 MB (≤ 1.2 GB **met**, barely). No watchdog kill and no wait events. X2(F)/X2(K10) ≤ 0.93. ζ_E ≤ 1.9 s |
| P4 disk < 30 MB | **Met**: 11 MB for the whole directory |
| P5 negative controls (1609, 2665; A, B) | **Met**: 32/32 variants rejected by the residue checks, including ram1 at p = 5 for 2665 (`logs/run_negctl.out`, `runs/negctl/`) |
| Combined: ζ_H < 0 for all 186 | **Met** |

## 4. Costs

* **Certificates:** 8.81 CPU-h summed run time, 9.0 h wall, sequential, nice 19.
* **Algebra:** < 1 min (flint) and 47 s (PARI). V1: a few minutes.
* **Memory:** peak footprint 1191 MB (5.1.19876-size fields are not in this set; the largest here is 19961, at 1004 MB in set B).
* **Disk:** 11 MB. Free disk never below 4.7 GB.

## 5. Caveats (read before any claim)

1. **Route (b) is a reading, not a published statement.**
   * KLW's *theorem* covers only ρ4, at almost all p. That Calegari's Thm 1.1/1.2, including dims 5 and 6 and the ζ_H step, holds without
     (2) rests on three things:
     * KLW's and Dwyer's remark that the Frob_5 condition is "superfluous";
     * our line-by-line check that (2) is used only in Lemma 3.2 (THEORY §4), including the 5-ramified case;
     * Pilloni–Stroh Thm 0.3 as quoted by KLW. **PS16 itself was not read.**
   * **Expert confirmation (ideally Calegari) is needed** before (b) is stated as a theorem. Route (a), for the 15 fields, needs no PS.
2. **Evaluator audit pending.** The certificates rest on the calegari3 evaluator lemmas and code (THEORY_GENERAL; Arb). They are not
   formally verified and not independently audited. The verifiers re-read JSON only. The negative controls and residue checks are
   numerical safeguards, not proofs.
3. **Field data come from PARI** (maximal orders at p | 5·disc f, |d_M|, ramified (e,f)). They are cross-checked by the discriminant
   identity, local Artin identity, group-theoretic derivation, coefficient identities, V1 and the residue checks. The LMFDB list is taken
   as complete for d ≤ 2·10⁴.
4. **Novelty is unknown.**
   * Dwyer (BLMS 46 (2014)) gives unspecified "concrete examples" (text not obtainable). He may cover some of these fields, plausibly
     small d.
   * Calegari 2013 has d = 1609. KLW have only ρ4 for 2869.
   * Phrase any claim as "to our knowledge".
5. Cited, not re-proved: Hecke, Artin formalism (with ramified factors), ζ(σ) < 0, and calegari3's ζ_K / ζ_K10 certificates (re-verified
   from JSON, not re-run).

## 6. Reproduce

1. `python algebra_flint_all.py`
2. `paripy/bin/python algebra_pari_all_v2.py`
3. `python gt_tame_check_v2.py`
4. `python validate_coeffs.py ours`, then `paripy/bin/python validate_coeffs.py pari`
5. `./run_all.sh`, then `./run_negctl.sh`
6. `python verify_all.py`

Main venv: `/Users/kiosk/projects/atlas-rerun/.venv`. PARI: `/Users/kiosk/atlas_mark2/tools/paripy`. Checksums: `SHA256SUMS`.

## Erratum (appended)

§4 "Memory": the 1191 MB peak is 5.1.19761.1 set B (`logs/cert_5.1.19761.1_B.log`), not 19961; 19961 B peaked at 1004 MB.
