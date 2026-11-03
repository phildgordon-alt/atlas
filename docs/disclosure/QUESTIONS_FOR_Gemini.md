# Questions for Google Gemini — contribution to the Atlas project

**From:** Philip Gordon (project lead)
**Purpose:** We are preparing a paper and an open-data release on *Atlas*, a method that rigorously certifies that zeros of the
Riemann zeta function and other L-functions lie on the critical line, using the explicit formula and **without taking a list of zeros
as input**. The paper includes a full disclosure of AI assistance. Claude (Anthropic) did most of the work reported in the paper
(from 2026-10-04 on). You (Google Gemini) were also used in the project, and we want to describe your role **accurately — neither more nor
less than what you actually did.**

Please answer from your own records of our sessions (conversation history, files you created or edited, commits). If you are not sure,
say "not sure" rather than guessing. Short, concrete answers are best.

## Background you may recognise
- Repositories/folders: `~/atlas/` (incl. `workbench/`, `workbench/math_ablation_20260928/`, `finetune/`, `doe_benchmark/`),
  `~/atlas_mark2/`.
- Components: sech-kernel explicit-formula "ledgers" (`certify_sech_interferometer.py`, `replay_sech_certificate.py`),
  off-centre unions, propagation (`integer_mechanism*.py`), the Lorentzian slab ladder (`lslab.py`, `verify.py`, `farL.py`),
  the 10^6 band certificates and the audit bundle (`audit_20261004/`), the Lehmer-pair work (`lehmer_7000/`).

## Questions
1. **Time frame.** Roughly when did you work on Atlas (dates or date ranges)?
2. **Code.** Which files, scripts or modules did you write or substantially modify? (List paths if you can.)
3. **Mathematics.** Did you propose or derive any of the mathematical ideas? For example: the explicit formula with sech kernels and the
   threshold E < 2; off-centre measurements; the LP "propagation" mechanism; Lorentzian rows Re ξ'/ξ(1/2+ε+it); the far-zero
   allowance; any lemma or bound. Which ones, and how much was your idea vs. the author's direction?
4. **Computations.** Did you run any computations whose results are used or cited (e.g. the 10^6 band, ledgers at particular heights,
   the Lehmer case, benchmarks)? Which?
5. **Analysis and writing.** Did you contribute analyses, literature reviews, reports or written text that ended up in the project's
   documents? Which?
6. **Verification.** Did you design or run any checks, replays or audits?
7. **Atlas Mark I vs Mark II.** Atlas had a first version ("Mark I", folder `~/atlas/`, sealed 2026-09-23 per the commit
   "Atlas Mark II milestone 1: seal Mark I, prime-cone prototype, exact cone"), then the current "Mark II" (`~/atlas_mark2/`, from
   2026-09-23). Did you work on Mark I, Mark II, or both? What did Mark I do (methods, results), and was any Mark I code, data or idea
   carried into Mark II?
8. **The Mark II core engine (2026-09-24 to 09-28).** Commits in that period created the sech-kernel explicit-formula engine
   (`diagnostic/certify_sech_interferometer.py`, `replay_sech_certificate.py`, e.g. "feat(interferometer): certify 62.37% zero-free
   coverage on [9950, 10050] via sech kernel", "chore(sech): stage catalogue- and count-free sech interferometer engine and replay")
   and the propagation mechanism (`diagnostic/integer_mechanism*.py`). Did you write or co-write any of these? Which parts?
9. **Anything else** we should credit you for — or anything we might wrongly attribute to you?

## How to answer
Reply in a short Markdown file named `ANSWERS_FROM_Gemini.md`, with one section per question (1–9). Thank you.
