# atlas_v5za = atlas_v5z9 on libzfast.v14d (PREDICTIONS_M14, review_v14c)

**What changed.** Every file is a byte copy of atlas_v5z9 except `lib/zfast_provider.py`, `atlas_v5.py` and `replay_target5.py`
(counted replacements in `tools/make_v5za.py`), plus `run_wideA.sh`. THEORY_V5Z6 to THEORY_V5Z9 still apply. Certificate content is
unchanged.

**The engine.** libzfast.v14d's compute path is v14's (= v13b at equal D) byte for byte; only the checkpoint layer
(`zfast_sched14d.inc`) changed. Checkpoint format v3 as in v14c, with:
- **MJ-C1.** Honest balls whose radius mantissa has 30 bits now load (exact radius construction); v14c refused them, which would have
  made a 10^28 checkpoint unresumable.
- **mn-C1.** A byte-identical copy of an authentic line is ignored and counted (`lines_duplicate`); a conflicting duplicate refuses.
- **mn-C4 (abort policy).** Any checkpoint write or fsync error aborts the zfast session (`CKPT-IO-ABORT`). The checkpoint stays valid up
  to the error. The provider records the reason in `<ckpt>.refusals.jsonl`; the driver logs `stage=ckpt_io_abort`, prints a banner and
  exits 3; `run_wideA.sh` stops. Recovery: fix the cause (e.g. free disk), then `RESUME=1 run_wideA.sh <same args>`. Chosen over
  "continue unprotected" because days of unprotected compute are the failure the checkpoint exists to prevent; the abort costs at most
  the items in flight.
- **mn-C3 (post-build resume).** `--resume` also works after the generator's session build (zs.json, certs, Turing grid ...): while the
  replay has not started, the generator checkpoint and the run nonce exist and the generator sidecar holds a gen-role record of this
  nonce, the interrupted attempt's outputs are MOVED to `RUN/gen_postbuild.attempt<k>/` (never deleted) and the generator re-runs on the
  complete checkpoint with the same nonce and key (generator verify 64). The generator counts as finished only with `gen_done` and, if
  requested, its `turing_grid` stage (gen_done is logged before the grid). All library refusals are unchanged.
- **Nits.** FIFO/non-regular key or checkpoint path refused (no hang); NUL bytes never authenticated; the header must match byte for
  byte; the directory of a new checkpoint is fsynced.

**Operational (review_v14c section 3).** Keep macOS automatic and security updates off and run no `brew` command during a multi-day
window (any OS or library change refuses a resume by design); run on this Mac only. `V4_LIM_GB` (default 1.0 in run_wideA.sh) kills a
stage that exceeds it; after mn-C3 such a kill is resumable, but set it with margin for the 10^28 certificate stage.

Do not delete `ckpt_keys/`. Keys are not certificate inputs; losing them costs only recomputation.
