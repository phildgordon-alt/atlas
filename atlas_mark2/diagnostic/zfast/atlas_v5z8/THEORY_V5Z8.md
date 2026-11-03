# atlas_v5z8 = atlas_v5z7 on libzfast.v14b (hardened checkpoints; PREDICTIONS_M12, review_m10)

**What changed.** Every file is a byte copy of atlas_v5z7 except `lib/zfast_provider.py`, `atlas_v5.py` and `replay_target5.py`
(counted replacements in `tools/make_v5z8.py`), plus `run_wide8.sh`. THEORY_V5Z6 and THEORY_V5Z7 still apply: provider, generator +
Turing grid stage, replay, verifiers.

**The engine.** libzfast.v14b's compute path is v14's (= v13b at equal D). Only the checkpoint layer and the API guards changed, so an
uninterrupted v5z8 window equals a v5z7 window bit for bit (PREDICTIONS_M12 I1, G1). In detail:

- **M1.** The checkpoint header pins the pre-fast session state (`prefast`: nbeg, Lb, Xb, tau0), the library image, the
  FLINT/GMP/MPFR versions and dylib hashes, and the OS build. A resume across any change refuses, naming the field.
- **M2.** Headers carry role (gen | replay) and the run's nonce, and must match the caller's.
  - The driver creates the nonce once per run (`RUN/zfast_ckpt_nonce.txt`).
  - It gives the generator role gen and the replay of record role replay, with per-role key files.
  - `replay_target5.py` fails (`passed` false) unless every zfast session of the replay process is recorded with role replay and the
    run's nonce. It records items_loaded / verified / lines_rejected in `replay_check.json` (`zfast_ckpt`).
- **m1. Every checkpoint line is HMAC-SHA256 sealed.**
  - The per-run, per-role 32-byte key is created by libzfast (O_EXCL, 0600) in `diagnostic/zfast/ckpt_keys/` (0700), outside every
    run directory.
  - Authenticated lines are strictly validated. A resume recomputes `ZFAST_CKPT_VERIFY` (default 8) random loaded items, which must
    be bit-identical.
  - **Trust model.** The key gives authenticity against everything that lacks it: copies, misrouting, plain-SHA reseals and other
    tools. It gives none against a key holder, who is trusted like the code.
  - The sample recompute is an independent, probabilistic content check. For a single forged item among N loaded items, the detection
    probability per resume is 8/N.
- **m3.** Write and fsync errors are checked and reported (provider warning + sidecar). The session continues, unaffected but not
  resumable.
- **m4.** flock.
- **m7.** D in [1, 16].
- **m8.** The production dylib has no env test hooks. The provider refuses to import, and the driver refuses to start, with any
  test-hook variable set. The driver strips them from every child env.

**Operating rule.** The interim rule from review_m10 ("never resume across an OS/Homebrew/library change") is now enforced by the
library: such a resume is refused. The remedy is to start a fresh run name.

Do not delete `ckpt_keys/`: a run's checkpoints cannot be resumed without its keys. Keys are not certificate inputs; losing them
costs only recomputation.
