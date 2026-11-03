# atlas_v5z5 = atlas_v5z4 with configurable, recorded zfast sessions (wide-session windows) (2026-11-01)

**Why.** At height T one zfast session costs an O(√T) moment pass (about 960 s at 10²² and 20,000 s at 10²⁴ on 2/1 threads) and then
milliseconds per point. v5z4 fixed the session half-width at H = 4, so a run covered a 2-unit target. A session of half-width H ≈ 61
costs the same pass (the 10²²–10²⁴ scans use exactly that), so one generator/replay process can serve a 100-unit target.

**What changed (the only trusted change is the provider's configuration; no inequality, model, verifier or tiling code changed).**
- `lib/zfast_provider.py`: H, Δ, K, J from env (defaults are v5z4's: 4, 0.15, 18, 12), centre rule unchanged in legacy mode.
  Strict mode (wide runs): the centre is required, a point outside [c − H, c + H] raises, a second session in one process raises.
  Explicit raises instead of asserts; refuses python -O.
- `atlas_v5.py`: `--wide --zfast-h H --zfast-delta Δ [--zfast-center c]`; the session record `zfast_session` goes into pieces.json,
  the full env (ZFAST_CENTER, ZFAST_THREADS, …) into drive.jsonl (regress_v1 finding F-A4); legacy mode strips ZFAST_H/Δ/K/J/STRICT
  from the child env so it is v5z4 exactly.
- `replay_target5.py`: the replay's session comes from pieces.json, never from the caller's env; recorded in replay_check.json.

**Soundness.** THEORY_M5 §1: every Z value and row is a ball from a session whose validity range contains the point; which session answers
is a matter of cost only. THEORY_M5b Lemma M1c: the Taylor remainder (|h′|X_b)^{K+1}/(K+1)!·e^{|h′|X_b} is a valid bound for complex h′
and any H, Δ, and is evaluated in Arb per block by libzfast.v13b (unchanged, sha 82489d1a…). With H = 61, Δ = 0.012, K = 18:
|h′|X_b ≤ 0.37, remainder ≈ 5·10⁻²⁶. The certificate claim, the verifier (verify_zs5.py sha 79ca5b16…) and the replay are unchanged.

**Regression.** Legacy mode must regenerate v5z4/v5z3 windows canonically identically (pieces.json may differ only in z_provider and the
new zfast_session record): engine/regress_v1/v5z5_gate.py, PREDICTIONS_M7 §1.
