# M5d: the 10²³ replay failure (root cause and fix), and the 10²³ certificates (2026-10-20)

Pre-registration: PREDICTIONS_M5d.md (sha 74cb57a5…), written after the diagnosis and before any v5z4 measurement. Every
prediction was MET.

## 1. Root cause (plain statement)

**The failure was a determinism bug in the model, not a soundness bug, and the generator was not wrong.**

- **What the replay checks.** The replay rebuilds each certificate's model and requires N_win to equal the certificate's value
  exactly. This check is correct and was not changed.
- **How N_win is computed.** N_win = up(count_upper5(window).upper()) encloses (θ(y) − θ(x))/π + 2S_max(y) in Arb. In v5 through
  v5z3 it did so **at whatever ctx.prec was active**.
- **Where the precision changes.** The frozen sech engine `certify_sech_interferometer._init` runs on the first row measurement of a
  process. It sets ctx.prec = 256 globally and never restores it. Before that call, ctx.prec is 128, set at import time by
  integer_mechanism.
- **The generator** measures its rows before building models, so its N_win was computed at 256 bits.
- **The replay** built cert p0's model first, at 128 bits, and so mismatched. It then measured rows, so cert p100's model was built
  at 256 bits and matched. The independent replay behaves the same way.
- **Why only 10²³.** θ(10²³) ≈ 2.5·10²⁴ ≈ 2⁸¹, so the 128-bit enclosure is about 2·10⁻¹⁴ wider. Its binary64 upper bound is
  59.77123605871552 rather than 59.7712360587155. **Both are valid upper bounds.** At 10¹⁶, 10²⁰ and 10²² both precisions give the
  same double (`runs/m5/nwin_prec_leak.json`), which is why no earlier run was affected.
- **Other suspects ruled out:**
  - zero placement: no zero near a piece edge played any role;
  - zfast (the Z values are unchanged);
  - the v13b guards;
  - N ≈ 4·10¹¹ terms.

  The v5z3 failure is exactly the predicted pattern in all four replays (h_1e23 pipeline and independent; hp_1e23 pipeline and
  independent): the first main certificate fails on N_win in plain and hardened, the second passes, and every S-layer certificate
  passes (**Y1 MET**).

## 2. Fix (atlas_v5z4: one trusted change; THEORY_V5Z4.md; frozen in V5Z4_FREEZE.sha256)

- `model5.count_upper5` evaluates at the fixed precision 256 + bitlen(T0) and restores ctx.prec afterwards. It encloses the same real
  number, so it is valid for the same reason.
- N_win is now a deterministic function of (T0, window).
- Everything else is a byte copy of atlas_v5z3, still using libzfast.v13b. The frozen engine is untouched; its leak is now harmless.
- Generator: `tools/make_v5z4.py`.

**Validation:**

| # | result | verdict |
|---|---|---|
| Y2 | N_win recomputed under the v5z4 rule for **all 92 main certificates** in every tree (v5 originals, record_heights, v5z, v5z2, v5z3; heights 7000 to 10²³), both before and after the engine's 256-bit side effect: **92/92 equal to the stored value**, 92/92 independent of the ambient precision (`runs/m5/Y2_nwin_all.json`) | **MET**: the fix changes no existing certificate |
| Y3 | v5z4 reproduces [10²², +2] (w_1e22): identical intervals, identical min_candidate_lower (0.7475326795220493); independent replay passes | **MET** |

## 3. The 10²³ certificates (atlas_v5z4, zfast v13b; 2 threads)

| window | result | sign changes | Turing count (separate method; `runs/m5/scan2_1e23`) | min margin | certified closest pair δ | pipeline + independent replay | Lean |
|---|---|---|---|---|---|---|---|
| **[10²³, 10²³ + 2]** (w_1e23) | **CLOSED (A) and (B)**; both main certificates replay-passed plain + hardened + independent; S-layer 16/16; 0 seams | 16 | **16**: N(10²³) = 797709722410724475904516, N(10²³ + 2) = …532 (pinned, U − L = 0.51, 0.52) | 0.729 | [0.3502, 0.3515] | 6072 s + 3035 s | 18 certificates, 0 violations |
| **[10²³ + 2, 10²³ + 4]** (wp_1e23; closest pair of the scan) | **CLOSED (A) and (B)**; same checks all pass | 16 | **16**: N(10²³ + 4) = …548 (pinned, U − L = 0.48) | 0.726 | **[0.1081, 0.1093]** | 6073 s + 3032 s | 18 certificates, 0 violations |

**Y4 MET.**

**The 10²³ close pair.**
- γ₁ ∈ 10²³ + [2.669609375, 2.6696875] and γ₂ ∈ 10²³ + [2.68296875, 2.683046875];
- gap ∈ [0.013281, 0.013437], δ ≈ 0.108;
- both zeros on the critical line and simple.
- The scan covered 122 units, 993 zeros located.

**Zeros of [10²³, +2]** (midpoints, widths ≤ 7.8e-5): 0.04809, 0.09387, 0.36121, 0.42090, 0.58863, 0.71840, 0.76152, 0.84691,
1.03184, 1.10410, 1.22824, 1.39066, 1.50660, 1.57645, 1.77957, 1.94074.

**This is Odlyzko's region.** The 10²³rd zero lies at t ≈ 1.3·10²²; these windows sit at 10²³, around zero n ≈ 7.98·10²³.

**Margins:** 0.794 (10²⁰) → 0.769 (10²¹) → 0.748 (10²²) → 0.729 (10²³), about 0.02 per decade.

## 4. Status of runs

- **Claim:** `atlas_v5z4/runs/w100000000000000000000000/{w_1e23, wp_1e23}`, each with a `provenance.json` (zfast v13b, tree
  atlas_v5z4). The theory list in `provenance.json` predates THEORY_V5Z4.md; see V5Z4_FREEZE.
- **The 10²⁰–10²² claims remain the v5z3 runs.** Y2 shows their N_win values are identical under v5z4, and Y3 reproduces 10²²
  exactly.
- **Failed, kept as evidence:** v5z3 h_1e23 and hp_1e23. These are not claims.

**Rules followed:**
- no in-place edits (new tree, new generator and tool scripts);
- no deletions;
- ≤ 2 threads: my diagnosis job that would have added two more threads was stopped, and all other work waited for the
  coordinator's hp_1e23 to finish;
- footprint ≤ 0.1 GB.
