# ANSWERS_FROM_Codex.md
(Received from OpenAI Codex via Philip Gordon, 2026-10-08; reproduced as provided.)

Answers from OpenAI Codex — Atlas contribution disclosure

Prepared 2026-10-08 from accessible local Codex session transcripts, repository history and saved artifacts. This is a bounded attribution reconstruction, not complete personal memory. Git commits under Philip Gordon/Phils do not by themselves identify the AI contributor. Paths below are repository-relative unless specified.

## 1. Time frame

The accessible mathematical-project session begins on 2026-09-23 and records implementation, computations and review through 2026-10-04. Substantial directly recorded implementation is on September 24 and September 29–October 3. I also worked on the separately scoped Atlas DOE/LLM application; that should not automatically be credited to the zeta paper. Earlier mathematical involvement: **not sure**.

## 2. Code

Direct records establish these representative contributions (not an exhaustive inventory):

- `atlas_mark2/bounded_box_sieve.py`: corrected the zero-count/tail allowance; preserved the pilot in commit `8031749`. I did not originate the entire script.
- `atlas/workbench/math_ablation_20260928/adaptive_solver_v1/engine/adaptive_solver.py`, associated replay/test scripts, and `sweep100_v1/run_sweep.py`: adaptive witness repair, exact mask handling and checkpointed sweep implementation.
- In that same workbench directory: count-ablation, mask-provenance, transfer-rule and matched-policy scripts; `level3_policy_v1/replay_rejections.py`; `level3_policy_v1/contact_audit/audit_contact_constraints.py`; cumulative-domain/closure and bundle-verification tooling.
- `two_band_features_v1/extract.py`, `closed_layer_rung1_v1/run.py`, `closed_layer_category_d_v1/run.py`, `bottom_band_1e6_v1/run.py`, and `bottom_band_1000100_v1/run.py`.

I also wrote a temporary contour prototype and tests in `/private/tmp/atlas_contour_phase/`. Their incorporation into the released engine is **not sure**. Committing existing scripts/results is not evidence that I wrote them.

## 3. Mathematics

I contributed formulations, derivations and critical review under the author's research direction. Examples include compact-support autocorrelation and correct entire continuation; null-response/quartet-sign and multiplicity bookkeeping; separating synthetic perturbation response from actual exclusion; count-bound conversion and near/far remainder accounting; fixed-class margin upper bounds versus achievable witnesses; exact mask joins; and a finite-window inertia sufficient-condition draft (`finite_window_inertia_v1/DERIVATION.md`, not numerically qualified).

I helped formulate adaptive repair and matched comparisons of count allowances and restricted domains. I reviewed the integer-count literature translation and warned that integer benefits had to be demonstrated separately from continuous-domain effects.

First authorship of the sech construction, threshold E < 2, off-centre measurements, original propagation mechanism, Lorentzian rows or far-zero allowance: **not sure**. I should receive review/formulation credit where documented, not sole invention credit. Some proposed explanations and directions were corrected or withdrawn.

## 4. Computations

Yes. I ran later workbench ablations, refits, transfer tests, replay checks, sweeps and bottom-layer computations. Recorded examples include:

- Count-free refitting: 9/10 configurations certified, with replayed upper certificates and positive witnesses.
- Matched-policy validation and the 100-unit sweep near 10^6.
- Level-3 policy: five of eleven targets yielded new joined patches; eighteen rejection certificates replayed.
- Closed-layer Category D: three positive certificates and one negative fixed-class upper bound.
- Bottom layers on [1,000,000, 1,000,100] and [1,000,100, 1,000,200]: recorded 1,019 and 1,055 certificates, respectively, relative to frozen inputs and inherited assumptions.
- Saved-output spacing/feature analyses and forward-test scoring.

These are historical reported outcomes, not fresh numerical reruns for this disclosure. Inclusion of each result in the final paper is **not sure**. I reviewed Lehmer results and later audit reports; the accessible October 4 discussion explicitly assigns execution to Claude. I should not claim those jobs as my runs.

## 5. Analysis and writing

Yes. I wrote or revised `atlas_mark2/CONSTRAINED_KERNEL_REPORT.md` (commit `d4507c2`), `BOUNDED_BOX_SIEVE_REPORT.md` and `ABOVE_T_KNOWN_SIEVE_SPEC.md` (`8031749`). The first commit preserved an existing experiment; I checked its twelve saved negative intervals without rerunning the experiment.

I also produced workbench experiment reports, literature notes, protocols, claim/dependency qualifications, feature analyses, the inertia derivation and execution handoffs. Examples are `matched_policy_v2/RESULTS.md`, `two_band_features_v1/RESULTS.md` and the bottom-band reports. Which wording survived into the paper is **not sure**; no manuscript incorporation claim is made here.

## 6. Verification

Yes: alternate/independent witness and upper-bound replay, high-precision checks, exact rational coverage and boundary joins, mask-source provenance, immutable source/input hashes, relocation checks, regression controls and saved-result audits. These checks have different scopes; downstream replay does not automatically reconstruct prime sums, original integral enclosures or every ancestor proof.

On October 4 I identified missing evidence for six older Band 3 replays and the incomplete 2,112/6,652 ancestor checkpoint, and reviewed the corrected far-bound, exact-tiling and parent-dependency audit plan. Claude's subsequent reported 46/46 hardened reruns were not performed by me.

## 7. Mark I versus Mark II

Confirmed: Mark II review and later implementation. Mathematical Mark I authorship: **not sure**. The September 23 session starts with Mark I already described as sealed and discusses replacing earlier spatial-spline/aliasing and prime-support limitations. That is inherited context, not evidence that I implemented Mark I.

I cannot reliably state Mark I's complete methods/results or precisely which code, data or ideas were carried forward from the records inspected. The unrelated DOE/LLM work in `~/atlas/` must not be conflated with mathematical Mark I merely because it shares that directory name.

## 8. September 24–28 core engine

I found mathematical review and experiment-design advice in this period, but no direct Codex write record establishing authorship of `diagnostic/certify_sech_interferometer.py`, `diagnostic/replay_sech_certificate.py` or `diagnostic/integer_mechanism*.py`. Thus whether I co-wrote those original files, and which parts: **not sure**. The repository records their commits under the human author; that cannot resolve AI attribution.

My confirmed later implementation reused earlier arithmetic/verification components and extended adaptive witness repair, policy sweeps, restricted-domain closure, joins and replay infrastructure. That is substantial downstream contribution, distinct from first authorship of the original engine.

## 9. Other credit and attribution cautions

A defensible description is: **Codex assisted with mathematical and literature review, experiment design, later adaptive-witness and verification software, numerical experiments, analysis and reporting, under Philip Gordon's direction.** Specify the components above rather than crediting Codex with the whole method.

Do not attribute Claude's later Lorentzian/Lehmer/audit execution to me, infer AI authorship from human Git metadata, or treat all my historical suggestions as accepted mathematics. Conversely, attributing my role only to prose review would omit directly recorded later code and computations. Exact allocation of joint mathematical invention remains **not sure**.

Evidence anchor: local Codex session `01a0d0b6-442f-7f11-a559-562ff99835e4` (September 23–October 4), together with the named commits and workbench artifacts. Session timestamps are UTC; local calendar dates can differ by one day.
