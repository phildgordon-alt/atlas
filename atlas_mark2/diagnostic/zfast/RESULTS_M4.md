# M4 results: atlas_v5z (zfast as the Z/row provider): re-certification of 10¹²–10¹⁶ and first windows at 10¹⁷ and 10¹⁸ (2026-10-19)

- Pre-registration: `PREDICTIONS_M4.md` (sha 462cf4a3…).
- Theory: `atlas_v5z/THEORY_V5Z.md`.
- Freeze: `atlas_v5z/V5Z_FREEZE.sha256` (28 files, including `bin/libzfast.v10b.dylib` and `bin/src_v10b/`).
- Generator of the code changes: `tools/make_v5z.py`, applied to byte copies of frozen atlas_v5 (V5_FREEZE 21/21 OK before
  copying).
- Runs: `atlas_v5z/runs/`; log `atlas_v5z/runs/v5z.log`; comparisons `atlas_v5z/compare_z_*.json`; Lean audit
  `atlas_v5z/lean_audit/`.

## 1. Re-certification: identical results (S1–S3: MET)

| window | original (v5 + Arb) | v5z | sign changes (orig / v5z / Arb Turing) | intervals | min_candidate_lower (orig / v5z) | Lean audit |
|---|---|---|---|---|---|---|
| [10¹², +2] control | closed A+B, 112 s | closed A+B, **8 s** | 8 / 8 / 8 | **identical** | 0.94354441043769 (Δ 1.8e-15) | 0 violations |
| [10¹³, +2] | 344 s | **8 s** | 9 / 9 / 9 | identical | Δ 2.1e-15 | 0 |
| [10¹⁴, +2] | 1078 s | **9 s** | 9 / 9 / 9 | identical | Δ 1.4e-14 | 0 |
| [10¹⁵, +2] | 3143 s | **11 s** | 10 / 10 / 10 | identical | Δ 2.2e-16 | 0 |
| [10¹⁵ + 286, +288] (close pair) | 3371 s | **11 s** | 10 / 10 / 10 | identical | Δ 2.0e-14 | 0 |
| [10¹⁶, +2] | 8874 s | **16 s** | 10 / 10 / 10 | identical | Δ 1.2e-14 | 0 |

- "Identical" means the certified sign-change intervals are the same binary64 pairs. zfast decides every sign that Arb decided
  during the search, so the generator follows the same path.
- Every window passed:
  - plain + hardened replay;
  - an independent replay (fresh process);
  - claim (B) (S-layer n/n);
  - 0 tiling seams.
- S4 (pipeline ≤ 4–6 min): MET by a factor of about 20. Independent replays take 3–7 s.
- S5 (peak footprint ≤ 0.6 GB): MET, 0.21 GB.

## 2. New windows: first rigorous unconditional RH certificates at 10¹⁷ and 10¹⁸ in this project (S6, S7: MET)

zs-step 0.005 (finer than v5's 0.02 at 10¹⁶). The parameters are otherwise identical.

| window | result | sign changes in target | min margin (main; S-layer) | pipeline + independent replay | peak | Lean audit |
|---|---|---|---|---|---|---|
| **[10¹⁷, 10¹⁷ + 2]** | **CLOSED (A) and (B)** | 11 | 0.836; S-layer 11/11 | 33 s + 15 s | 0.2 GB | 13 certificates, 0 violations |
| **[10¹⁸, 10¹⁸ + 2]** | **CLOSED (A) and (B)** | 11 | 0.809; S-layer 11/11 | 90 s + 41 s | 0.2 GB | 13 certificates, 0 violations |

**Zeros** (interval midpoints, offsets from T; every interval has width ≤ 7.8e-5; exact endpoints are in
`intervals_summary.json`):
- 10¹⁷: 0.03918, 0.16652, 0.54059, 0.72160, 0.78098, 1.02129, 1.15426, 1.33012, 1.48535, 1.69730, 1.83980. Closest pair
  δ ∈ [0.352, 0.353].
- 10¹⁸: 0.19309, 0.34879, 0.47316, 0.69285, 0.90801, 1.11324, 1.21012, 1.44207, 1.60379, 1.74949, 1.79684. Closest pair
  δ ∈ [0.298, 0.299].

The margins (0.836, 0.809) continue the trend of the v5 windows (0.94 → 0.83 from 10¹² to 10¹⁶), about 0.03 per decade.

**Diagnostics (not part of the trust base):**
- **S8:** Arb's Turing count (`acb_dirichlet_zeta_nzeros`) at 10¹⁷ exceeded the 950 MB watchdog (killed at 983 MB). No
  independent zero count is available at 10¹⁷ or 10¹⁸ on this machine under the cap. The count is therefore *not* cross-checked.
  The claim does not depend on it, because v5's certificate is Turing-free and count-free. A rigorous count from zfast (Turing's
  method on zfast Z values) is a natural next diagnostic.
- **Independent sign confirmation.** Every certified interval at both heights (35 and 38, including those outside the target) was
  re-evaluated by the *single-point* zfast path (no moments, no sessions): all sign changes were confirmed, with
  min |Z|/radius ≥ 1.0·10⁵.
- **Pure-Arb check.** Six endpoints, including the one with the smallest |Z| (1.3e-4 at 10¹⁷ − 0.5225), were re-evaluated with
  Arb's own main sum (`powsum_smooth`; RS correction from zfast's copy of Arb's correction loop): the same signs, |diff| ≤ 1.5e-15.
  - Cost: 34 s per point at 10¹⁷ and 114 s at 10¹⁸, 4.6 MB.

## 3. Framing

**Claim:**
- [10¹⁷, 10¹⁷ + 2] and [10¹⁸, 10¹⁸ + 2] are the first windows at these heights certified by Atlas's zero-list-free, Turing-free
  method, with independent replay and a Lean file audit.
- To our knowledge they are the highest rigorous unconditional RH windows in published or publicly documented work. This needs a
  novelty re-check before any statement.

**Mandatory caveats (as for the 10¹⁵/10¹⁶ windows):**
- Arb's (and FLINT-dev's) Turing-method tools can certify such windows given enough memory. This is not a new fact about ζ.
- Odlyzko, Gourdon and Bober–Hiary computed far higher non-rigorously.
- The trust base now includes zfast. zfast is an independent implementation, not a new method: FLINT's dfloat branch does the same
  class of computation. Its validation is RESULTS_M2/M3.
- Lemma 2 and THEORY_V4 §10 remain unreviewed. An independent review of THEORY_ZFAST §§5–7 and §10 and of THEORY_M3 is
  recommended before publication.

## 4. Cost summary

v5z costs about 10–90 s per 2-unit window at 10¹²–10¹⁸, against 2 min to 2.5 h for v5 with Arb at 10¹²–10¹⁶. At 10¹⁶ that is a
**550× speed-up** at 0.2 GB. From the M3 session costs, 10²⁰ should take about 10 min and 10²² about 1–2 h per window. Above
10¹⁸ the non-ζ parts and the session builds dominate, so this is not yet measured.
