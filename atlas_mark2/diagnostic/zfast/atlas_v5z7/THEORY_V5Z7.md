# atlas_v5z7 = atlas_v5z6 with two fail-safe resume defects of the driver fixed (2026-11-01; RESULTS_M9 F-M9b, F-M9c)

Every file is a byte copy of atlas_v5z6 (THEORY_V5Z6.md applies unchanged: libzfast.v14, provider, generator + Turing grid stage,
replay, verifiers) except `atlas_v5.py`:
- F-M9b: the worker count W (output-free) is no longer written into pieces.json's `zfast_session` (v5z6 refused a `--resume` with a
  different ZFAST_WORKERS); it is recorded in drive.jsonl's env.
- F-M9c: stage 3 (the replay of record) runs only if the generator logged `gen_done`; on `--resume` an existing replay is reused only if
  its replay_check.json has passed = true, otherwise it is renamed `*.attemptN` and rerun (v5z6 reused the failed replay of a run whose
  generator had died, so the resumed window ended "not closed").
Both v5z6 defects failed safe (refusal / "not closed"); neither could produce a false PASS. No certificate-relevant code changed.
