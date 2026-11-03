# 1-ulp sliver check — 10^6 band and Lehmer certificates (2026-10-06)

**Result: NOT AFFECTED. 0 slivers.** No capped region of any column certificate lies outside the union of certificate rectangles, at any d.
The pattern behind the older-run gap (atlas_v3 RESULTS item 3; CORRECTIONS_2026-10-06, last section) does not occur here.

## What was checked
The question: when a certificate's model lowers an off-line cap (claiming "no zeros in bin [lo,hi] above d = cap_cert"), is every point of
[lo,hi] x (cap_cert, cap_case] covered by some certificate rectangle? A 1-ulp sliver would appear as an in-column bin whose edge lies
outside the certificate region [a,b].

All comparisons use `Fraction(float)` (exact dyadic values), no tolerances. Inputs: the bundle `atlas_standalone_audit/` (54 certificates,
8 case files). The bundle certificates and case files are byte-identical to the workbench copies (lorentz_feasibility_v1/, the three
round_018/round_001 case directories, lehmer_7000/ladder). `model()` in lslab.py, lslab.py.bak_densemem (used by replay) and the Lehmer
lslab_prepatch.py (workbench and bundle) are identical.

1. **Every lowered cap in every certificate.** For each of the 52 certificates that store `vars` (lslab slabs + lclose certs), I compared the
   stored vars with the source case model bin by bin. Wherever the stored cap is lower than the case cap, I subtracted the union of all 54
   certificate rectangles (closed, exact) from [lo,hi] x [cap_cert, cap_case]. The 4 verify.py witnesses use their case model unchanged, so they lower nothing.
2. **In-column bin edges vs column endpoints.** For each run (m052, m056, m193, g240s, b240, b203, lclose g240, Lehmer), I computed the in-column
   off bins with the model's own float criterion (`lo<b-1e-12 and hi>a+1e-12`; lclose: its own criterion). Then I compared the extreme
   edges exactly with the column [a,b] that the run was given, and listed every bin edge within 1e-6 of a or b.
3. **Upstream link.** For every open bin (cap > binary64(0.001)) in every source case model, I checked that [lo,hi] x [0.001, cap] is covered
   exactly by the certificate union. I also checked that the bins of every case model tile x with no gaps and no overlaps.

## Findings
| run | column [a,b] | in-column bins | extreme in-column edges − [a,b] | lowered bins outside column | uncovered |
|---|---|---|---|---|---|
| m052 | 1000052.05–.11 | 7 | 0, 0 | none | 0 |
| m056 | 1000056.41–.43 | 3 | 0, 0 | none | 0 |
| m193 | 1000193.38–.39 | 1 | 0, 0 | none | 0 |
| g240s | 1000240.19–.49 | 30 | 0, 0 | 4 neighbour bins (whole bins, see below) | 0 |
| b240 | 1000240.15–.55 | 41 | 0, −1 ulp (inside) | none | 0 |
| b203 | 1000203.55–.58 | 3 | 0, 0 | none | 0 |
| g240 (lclose) | 1000240.17–.49 | 32 | 0, 0 | none | 0 |
| Lehmer 7005 | 7005.06–7005.1 | 14 | 0, 0 | none | 0 |
| Lehmer c7002 (workbench only) | 7002.48–.49 | 2 | 0, 0 | none | 0 |

- **No in-column bin crosses its column endpoint, even by 1 ulp.** The bin edges at the column ends are the same binary64 values as the
  argv column endpoints (for example 1000052.05 and 1000052.11). The float-arithmetic edges that do occur (1000052.1099999999,
  1000056.4299999999, 1000240.5499999999, 1000240.4999999999, 1000203.5599999999) all lie inside a column or at the edge of a ledger-closed
  region, never outside a certificate region:
  - m052 [1000052.1099999999, .11] and m056 [1000056.4299999999, .43]: these bins are in-column, but their case cap is already 0.001, so the
    ladder never lowers them. The bottom-level certificate ([a,b] x [0, 0.001]) covers them anyway. TARGETS.json uses the 1-ulp-smaller right
    edge (…1099999999 / …4299999999), so the certificates over-cover the target.
  - b240: the off bins of fb001_g01_left stop at 1000240.5499999999. Only an on-line bin covers [.5499999999, .55]. This matches the bottom-band
    uncertified interval exactly (same float), and the b240 certificates reach .55. No sliver.
- **The 1e-12 tolerance in `model()` is a no-op at 10^6.** There ulp = 1.16e-10, so `b-1e-12 == b`. At 7005 it equals 1 ulp (9.1e-13). No bin edge lies
  within 1 ulp of a column endpoint in either regime, so the tolerance never changes membership.
- **The only lowered bins outside a column** come from lslab's "already-certified neighbours" branch in the 10 g240s certificates: whole bins
  [.16,.17], [.17,.18], [.18,.19] and [.49,.4999999999], each 0.35 → 0.001 (40 instances). They are covered exactly by witness_g01_left
  [.16,.17], cert_g240 [.17,.18] and [.18,.1900000001], and witness_g01_right [.4899999999,.4999999999], all at d ∈ [0.001, 0.35].
  The lclose certificates lower only [.17,.18] (covered by cert .17).
- **Upstream link holds.** Every open bin of the five 10^6 case models is fully covered: 2 + 34 + 1 + 6 + 2 bins, 0 uncovered. All case models
  tile their windows with no gaps or overlaps. The Lehmer 7005 case also has open bin 7002.48–.49 (cap 0.01). The model only allows zeros
  there and never lowers its cap, so it creates no gap for the 7005 claim. The c7002 workbench slabs close it ([7002.48,7002.49] x [0, 0.01]); they are not in the bundle.

## Why the old-run gap does not reproduce here
In the older runs, the column was given as rounded decimals while the bins were built as `T0 + k*0.01` (for example 7393.009999999999 vs 7393.01).
In these case models, the bins at the column ends carry the same float as the column endpoint passed to the run. Where an arithmetic-artefact edge exists, it sits
either strictly inside a certificate region or on a bin whose cap is already 0.001, which no certificate lowers. So the bundle's exact tiling
check (`run_audit.py` step 3 / `exact_tiling_check.py`) has no hidden sliver behind it. Only geometry was checked here; certificate validity still rests
on the hardened replays.

Method scripts (read-only, not part of the bundle) are in the session scratchpad: sliver.py, sliver2.py, sliver3.py, sliver4.py.
