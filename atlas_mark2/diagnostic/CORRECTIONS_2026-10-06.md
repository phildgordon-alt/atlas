# Corrections and amendments (2026-10-06)

Trigger: the pole-guard bug (found 2026-10-05; crowded_ladder/RESULTS.md addendum) affected more runs than first stated.
Bug: the Lorentzian slab ladder allowed a Lorentzian row (eps = d) within 0.003 of the region it was testing, in bins the model
had already excluded; the row has a pole on the tested point, the Arb enclosure diverges (seen: +-1.24e9), and the rigorous check
can never pass. Effect: SPURIOUS STALLS ONLY. A pole can only prevent certification, never produce one — no certificate is affected.

## Which runs had the guard
| run | pole guard | t0 stalls |
|---|---|---|
| crowded_ladder (7000–7500, first crowded run) | NO | 3 / 9 (g6866, g6910, g7251) |
| hardness_study (exploratory, 18 targets) | mostly NO (the 9 from crowded_ladder) | 4 / 18 |
| crowded_v2_7500 (out-of-sample) | yes | 0 / 9 |
| crowded_v2_narrow (control) | yes | 1 / 9 |
| hardness_test_8000 | yes | 0 / 31 |
| hybrid_v1 re-run of crowded_ladder's hard targets | yes | g6910: 0, g6866: 0 so far (g7251 pending) |

## Amendments
1. **crowded_v2_narrow/RESULTS.md** — its conclusion "the jump from 6/9 (first run) to 9/9 is mostly target difficulty" is
   CONFOUNDED: the first run lacked the pole guard. The comparison narrow-vs-wide (both with the guard) stands: the wide band
   removed one t0 stall. The cause of the 6/9 → 9/9 jump is most likely the pole-guard fix; to be tested (ablation).
2. **crowded_ladder/RESULTS.md** — escalation tiers t1–t4 (incl. "tier 4 closed g6866 and g7251") were at least partly
   compensating for the bug: with the guard, g6910 and g6866 close at t0. Statements about mid-depth hardness and the need
   for narrow sech kernels must be re-evaluated after the ablation.
3. **hardness_study / hardness_test_8000** — the exploratory hypothesis was built partly on artifact stalls (>= 2 of the 4
   "hard" targets). The pre-registered falsification stands; the artifact is a likely reason the pattern did not replicate.
4. **Unchanged:** every certificate (all replayed hardened); the 10^6 band (46/46); Lehmer (8/8, slabs made before escalation —
   check whether its ladder could hit the pole case: its column was fully open at every level, so the guard condition did not
   arise); the out-of-sample prediction (met, with the guard); direct-evaluation results.

## Planned tests
- Pre-registered ablation: crowded_ladder's 9 targets with vs without the pole guard, all else identical.
- Pre-registered fresh test of the canonical pipeline on [9000, 9500].

## Ablation outcome (later 2026-10-06) — see hybrid_v1/ABLATION_RESULTS.md
The guard fixed 3 artifact stalls but created 1 (g7142, close zero pair): it is too blunt (drops pole-free rows with
eps in (d_hi, 2 d_hi]). Pre-registered follow-up: guard_v2/PREDICTIONS.md (GUARD_FACTOR 1.1). No certificate affected.

## Formal gap: 1-ulp slivers in older column certificates (found by atlas_v3 build)
In 10 older column cases (hybrid_v1 g6866 x2, g6895, g7000 x2, g7142, g7251 x2, g7255; zsign case_7393.01_7393.03) the model's
in-column bin edge differs from the rounded certificate region by 1 ulp (~1e-12); the ladder capped those slivers without certificate
coverage and the old tiling check used rounded edges. Measure ~1e-12 per column; formal, not practical. atlas_v3 uses exact float
edges and asserts membership; its g7142/g6866 re-runs close those columns without the gap. TO CHECK: whether the 10^6 audit bundle
(lorentz_feasibility_v1 / audit_20261004) has the same rounding pattern.
## Simplicity in atlas_v3 rests on Lemma 2 (parity of sign changes): reviewed by me 2026-10-06 — holds (an interval with a Z sign
change has odd on-line multiplicity, so a double zero inside forces another on-line zero that carries the credit). d > 0 claims
do not depend on it. Independent expert review still advisable before citing "simple".
CHECKED (2026-10-06): the 10^6 audit bundle and Lehmer certificates are NOT affected — 0 slivers (exact Fraction comparison over
54 bundle certificates + 8 cases; audit_20261004/SLIVER_CHECK.md). Column ends coincide with bin-edge floats there.

## Lean formalization (2026-10-07, atlas_mark2/formal/): certificate logic L1-L6 machine-checked (no sorry/axiom; only propext,
Classical.choice, Quot.sound — rebuilt and re-checked by me). Gaps it surfaced in the informal docs (none makes a result wrong):
(1) Lemma 2 needs (C) at d = 0, which holds only because the verifier checks the closed box with d0 = 0; (2) the Theorem needs the
candidate region inside the window — v4 checks it, v3 not verified; (3) intervals inside the window is load-bearing; (4) v4_1 Lemma A
needs the closed-box count, i.e. the counter certifying no boundary zeros. TO CHECK: deg2 (11.a/23.1.b.a) verifier against (1)-(3).

## Lean certificate-file audit (2026-10-08, formal/audit/): 0 violations over ~3,600 real certificate files (deg2, ec37a, ec389a,
tollis, v4); re-run by me. Findings: (1) 26 targets with non-binary64 decimal endpoints are covered for their STORED binary64
endpoints; the decimal interval can miss a sliver of 1e-15..4.5e-10 at an end — all contiguous headline claims have integer
endpoints and are unaffected; read decimal-endpoint claims as binary64. (2) CORRECTION: the "Lehmer column" target
[7005.06, 7005.10] used in v3/v4 acceptance contains only the FIRST zero of Lehmer's pair (7005.0629); the second (7005.1006) lies
just outside. Fixed: v4 run lehmer_full_pair on [7005.0, 7005.2] — closed, independent replay passed, claims A and B (both zeros on
line + simple). (3) The 389.a central-mass reduction is now Lean-proved (Atlas/Central.lean).

## Prior art found by citation census (2026-10-10, new_territory/CITATION_USERS.md)
N. Ng, PhD thesis (UBC, 2000), computed zeros of dihedral Artin L-functions of levels 23, 31, 59, 83, 144 up to heights 972, 1072,
794, 737, 667 (10-digit floating point; not interval-rigorous), i.e. covering the cubic fields d = −23, −31, −59, −83 well above
Tollis and above our 110/200. Our claims must read: "first RIGOROUS (interval-certified) verification" for these fields at these
heights; Ng 2000 must be cited. The flagship (−23 to 10^4) exceeds Ng's 972. LMFDB/CMF (Best et al. §10.3) checked RH to an unstated
height b for all newforms with Nk² ≤ 4000 (all elliptic curves of conductor ≤ 1000) — find b before claiming novelty for any EC table.
Addendum (2026-10-10, WAITING_DEMAND_2.md): Ng's thesis §4.3.4–4.3.5 CLAIMS RH (Maple floating point + Tollis's method, not
interval-certified) for L(ρ) of d = −23 (972), −31 (1072), −59 (794), −83 (737) and f_144 (667). All Atlas claims for these must read
"first interval-certified", never "highest height"; the flagship (−23 to 10^4) exceeds 972.

## Correction 2026-10-13 (holomorphy): "Λ(ρ4⊕ρ5) = Λ_{K10}/Λ_ζ entire by Aramata–Brauer" is a wrong citation
Found by general_eval/calegari2/HOLOMORPHY_AUDIT.md (raised first in cohen_mo/RESULTS.md §9). Aramata–Brauer covers ζ_L/ζ_K for Galois
L/K only; for K10 (closure S5) it is Dedekind's conjecture, not known, and it follows from Calegari's conclusion (circular).
Consequences: (1) general_eval E2 (25 fields) and calegari2 (174 fields d ≤ 2·10⁴ + literal-hypothesis fields beyond) certified
Λ_comp > 0, which equals Λ(ρ4⊕ρ5) only under hypothesis H ("no poles"): every "analytic input of Calegari Thm 1.2 verified" claim
reads "conditionally on H"; for d = 1609 H holds a posteriori (Calegari Thm 5.1 via Booker). No automorphy claim from those runs.
(2) The A-split check cannot detect such poles (residue terms ~1e−35, ~20 orders below tolerance). (3) L(ρ4) and L(ρ4⊗sgn) entire:
true for all signature-(1,2) S5 quintics, citation is KLW (arXiv:2206.08116) Thm 1.2(b), not Aramata–Brauer; so cohen_mo's 7 classes
are all unconditional (d = 1609 and 2869). Appended correction blocks (no edits above them): general_eval/RESULTS.md,
general_eval/THEORY_GENERAL.md, general_eval/calegari2/RESULTS.md, new_territory/ARTIN_ROUTE.md, cohen_mo/RESULTS.md.
Repair: certify ζ_{K10}(σ) < 0 on (0,1) directly (degree 10, residue solved from theta splits), in general_eval/calegari3/.

### Closing note 2026-10-17 (holomorphy correction resolved by calegari3)
The repair is done: general_eval/calegari3/RESULTS.md. ζ_{K10}(σ) < 0 on (0,1) is certified (Hecke + Arb, residue solved from theta splits,
no hypothesis H) for all 186 fields in both parameter sets (372/372 runs; 4 set-B runs needed TL 18000 s instead of 7200 s, disclosed).
Hence L(ρ5,σ) ≠ 0 on (0,1) **unconditionally** for every field the E2/calegari2 claims covered, plus 38069 and 38189; ζ_K(σ) < 0 too, so
L(ρ5), L(ρ4) are finite and positive there. The Booker zero brackets for 1609 and 2869 now hold unconditionally. The new values agree with
the old Λ_comp at all 1835 comparison points (a consistency check only). The "conditionally on H" wording in the earlier correction blocks
may now be read as superseded for the real-segment statement; it still applies to anything stated about Λ_comp itself. Automorphy is
still NOT claimed: Calegari's hypotheses/remark need expert confirmation (and Pilloni–Stroh for non-literal fields).

### Correction 2026-11-01 (artin_sweep count)
artin_sweep/RESULTS_FINAL.md §0 and ATLAS_STATUS.md (2026-10-27 line) said 2 259 fields d > 2·10⁴ certified in both sets (130 + 2 128),
2 445 in total. The stored field summaries give **2 256** (130 `calegari_published` + 2 126 `calegari_plus_PS`), total **2 442**.
Source: engine/regress_v1 tier 0 (frozen verifier) + independent recount. Tally error only; no certificate or verdict changes.
Correction block appended to artin_sweep/RESULTS_FINAL.md. (patterns/PATTERNS.md "n=2259" is a margin-sample size, not this claim — left as is.)
