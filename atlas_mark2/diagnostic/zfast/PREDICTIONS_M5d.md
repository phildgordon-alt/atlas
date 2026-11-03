# M5d: the 10²³ N_win replay mismatch and its fix (2026-10-20; written after the diagnosis and before any v5z4 measurement; sha in PREDICTIONS_M5d.sha256)

**Diagnosis** (THEORY_V5Z4.md; evidence in `runs/m5/nwin_prec_leak.json`). N_win depended on the ambient ctx.prec (128 before the
sech engine's first `_init`, 256 after). At 10²³ the two give different, both valid, binary64 upper bounds. The replay's exact model
check rejected the certificate whose model was built first. No soundness defect.

| # | prediction | criterion |
|---|---|---|
| Y1 | The running h_1e23 independent replay (v5z3) shows the same pattern: cert_p0_100 Nwin mismatch (plain + hardened), cert_p100_200 passes | otherwise the diagnosis is incomplete: stop |
| Y2 | v5z4 rule, recomputed for **every** existing main certificate (v5 originals 10¹²–10¹⁶, v5z, v5z2, v5z3 runs incl. 10²⁰–10²³): N_win equals the stored value in all of them, including both h_1e23 certificates (stored 59.7712360587155) | any difference at ≤ 10²² = FAIL |
| Y3 | v5z4 reproduces [10²², +2] (x_1e22) with identical intervals, identical min_candidate_lower, and a passing independent replay | FAIL otherwise |
| Y4 | Fresh v5z4 runs [10²³, +2] and the scan's closest-pair window close (A)+(B), with both certificates replay-passing plain + hardened + independent, 0 seams, Lean 0 violations; the counts equal the Turing counts of `scan2_1e23` | reported; any replay failure = stop |
