# atlas_v5z2 = atlas_v5z with provider v5z2 (2026-10-19)

The only change from atlas_v5z (THEORY_V5Z.md, whose trust-base description applies) is `lib/zfast_provider.py`:
- one kind-0 zfast session (libzfast.v12a) per process answers both Z (THEORY_M3) and the rows, via the complex shift of the Z moments
  (THEORY_M5b);
- the session centre comes from env ZFAST_CENTER (the run script sets the target centre), and the rule c = 8 round(u/8) is the
  fallback;
- H = 4, Δ = 0.15, K = 18.

The driver changes only its provenance string. Every other file is a byte copy of atlas_v5z. Acceptance (PREDICTIONS_M5 V2): the
six original windows and v5z's 10¹⁷/10¹⁸ windows must be reproduced with identical intervals.
