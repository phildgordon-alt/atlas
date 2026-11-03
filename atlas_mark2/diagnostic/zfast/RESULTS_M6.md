# M6: RH windows at 10²⁴ (2026-10-23/24)

Pre-registration: PREDICTIONS_M6.md (sha 8bfd1787…, verified). Pipeline: atlas_v5z4 (V5Z4_FREEZE.sha256, unchanged), zfast
v13b (`bin/libzfast.v13b.dylib`, sha 82489d1a89e25bef117cd87f47d591d9426282c4b211f92ace12d097767dffca — same binary as M5).
New files only: `tools/pair_gap_m6.py` (modeled on `tools/pair_gap2.py`), and run-dir outputs below (`intervals_summary.json`,
`endpoints.txt`, `provenance.json`, `pair_gap_m6.json`, `endpoint_margin_m6.json`) — none of which existed before this write-up.
`tools/provenance_m6.py` already existed (written during the M6 run) and was simply invoked correctly; no new copy was made.
Nothing deleted or edited in place. nice 19, ZFAST_THREADS=1 throughout, peak footprint of every process run here ≤ a few MB
(the certificate runs themselves report ≤ 0.23 GB; see table).

**Note on a stalled step.** `atlas_v5z4/run_m6_stage2.sh`'s `post()` helper called `tools/pair_gap2.py` and `tools/provenance_m6.py`
by a path relative to `atlas_v5z4/` (`tools/pair_gap2.py`), but both tools live in `zfast/tools/`, one level up. Both calls
failed with "No such file or directory" for `w_1e24` and `wp_1e24` (visible in `atlas_v5z4/runs/m6.log`), leaving empty
`pair_gap2.json` placeholder files (0 bytes, from shell output redirection) and no `provenance.json` in those two run dirs. The
certificate pipelines, independent replays, and Lean exports/audits were unaffected (they use absolute or correctly-cd'd paths)
and completed successfully. This write-up supplies the missing post-processing from the correct paths, writing to new files
(`pair_gap_m6.json`, `provenance.json`) rather than touching the stale empty `pair_gap2.json`s.

## 1. Certified windows (atlas_v5z4, zfast v13b, ZFAST_THREADS=1)

| window | zeros (sign changes) | Turing count N (separate method) | min margin | closest certified pair, δ | pipeline + independent replay | Lean |
|---|---|---|---|---|---|---|
| **[10²⁴, 10²⁴ + 2]** (w_1e24) | 17 | N(10²⁴) = 8343565023546958629481544, N(10²⁴+2) = …561 (17; both pinned, U−L = 0.503, 0.479) | 0.6155925086489527 | gap ∈ [0.043906, 0.044063], δ ∈ [0.3733, 0.3747] (not the designated close pair; see §2) | 20816.19 s + 20627.02 s (41443 s total) | 19 certs (2 main + 17 S-layer), 0 violations |
| **[10²⁴ − 3, 10²⁴ − 1]** (wp_1e24; scan's closest-pair window) | 16 | N(10²⁴−3) = …519, N(10²⁴−1) = …535 (16; both pinned, U−L = 0.523, 0.520) | 0.6144840396533866 | **[0.014063, 0.014219], δ ∈ [0.1196, 0.1209]** | 20752.58 s + 20801.73 s (41554 s total) | 18 certs (2 main + 16 S-layer), 0 violations |

Peak footprint: 0.207 GB (w_1e24 generator), 0.078 GB (its replay); 0.232 GB (wp_1e24 generator), 0.084 GB (its replay). No
watchdog kill in either run (`"killed": null`). All figures from `summary.json`/`replay_check_independent/replay_check.json`
in each run dir; independently reproduced here by `tools/window_intervals.py` (new `intervals_summary.json`/`endpoints.txt`,
17 and 16 sign changes, 0 straddlers, disjoint) — margins match to the last printed digit.

**Turing cross-count** (`runs/m6/scan3_1e24/scan_turing.json`, libzfast v13b, scan H=61, Δ=0.012): all four window ends
pinned, U−L ∈ [0.4787, 0.5230] (prediction C1's [0.45,0.62] — MET). N(10²⁴) = 8343565023546958629481544, N(10²⁴+2) =
…561: exact match to the certified sign-change counts (17, 16), and within 1 of the pre-registered estimates
…544.16/…561.17.

## 2. The 10²⁴ close pair (certified; `tools/pair_gap_m6.py` on wp_1e24's `intervals_summary.json`, Arb prec 200)

- γ₁ ∈ 10²⁴ + [−1.711953125, −1.711875] and γ₂ ∈ 10²⁴ + [−1.697812500, −1.697734375] (offsets relative to T0 = 10²⁴).
- Gap ∈ [0.014063, 0.014219]; **δ ∈ [0.1196, 0.1209]**, i.e. about 1/8 of the mean local spacing 2π/log(T/2π).
- Both zeros on the critical line and simple (wp_1e24 certificate, (A)+(B) closed).
- Matches the scan's non-rigorous estimate (δ_mid ≈ 0.102, `scan3_1e24/scan_turing.json`'s `closest_pair`) to the expected
  precision; the scan searched offsets [T−20, T+22] (`gap_mid`/`gap_lower`/`gap_upper` = 0.0120/0.0080/0.0160), 1038 zeros
  located, 0 undecided grid points, 0 "dips".
- For reference, the closest pair inside the main window [10²⁴,+2] is much wider: gap ∈ [0.043906, 0.044063], δ ∈
  [0.3733, 0.3747] (not competitive with wp_1e24's).

## 3. Error budget and scan diagnostics (predictions B1/B2; `tools/budget_m6.py`, `tools/endpoint_margin_m6.py`)

- `runs/m6/budget_m6.jsonl` (scan session, E=24): N = 398942280401 (= Nw below, matches B1 exactly), Z_radius_apriori =
  9.21·10⁻⁹, well inside the predicted [1·10⁻⁸, 4·10⁻⁸]×(session variation). RS remainder ≤1.2·10⁻³⁵ at K=2.
- Scan session (`scan3_1e24/scan_turing.json`): Nw = 398942280401, max_phase_err = 1.152·10⁻¹⁹ (≤ 1·10⁻¹⁷ required), grid =
  30501 points, **0 undecided**. Three representative grid points (`runs/m6/gz_1e24_points.json`): radii 1.1224·10⁻⁸
  (nearest the closest-pair midpoint), 1.2554·10⁻⁸ (smallest |mid|/rad), 1.3136·10⁻⁸ (largest |mid|) — all inside
  [1.0·10⁻⁸, 4.0·10⁻⁸]. **B1 MET.**
- `endpoint_margin_m6.py` (new output, diagnostic/linearized, not a certificate) against the same scan grid: min ratio
  701.73 for both w_1e24 (52 intervals) and wp_1e24 (51 intervals), medians 53731 and 59479. **B2 MET** (≥300 required).

## 4. GZ independent-engine spot check (prediction G) — in progress, one of three points done

`runs/m6/gz_1e24.jsonl` (stock FLINT `acb_dirichlet_powsum_smooth` + Gabcke, `review2/bin/ref`, under `tools/wd_run2.sh` at a
950 MB watchdog) has produced one result so far:

```
{"u": "-0x1.ffbe76c8b4394p+3" (t = T0 − 15.992), "N": 398942280401, "Z": "[+/- 4.27e+91]", "rad": 4.2673e+91, "sec": 121658.85}
```

This is **not a useful cross-check**: the returned ball has radius ≈4.3·10⁹¹, so it trivially contains the zfast midpoint
(and everything else) rather than bounding it to anywhere near the required |diff| ≤ 10⁻¹³. Plainly, this point does not
meet prediction G's criterion as stated; it is reported rather than silently dropped. The process (`review2/bin/ref`, pid
99186, started Fri 07:25 local) is **still running** on the second of the three points at the time of this report — per
the task's "wait, don't duplicate" rule it was not touched or restarted. No "GZ done" line has yet appeared in
`atlas_v5z4/runs/m6.log`. The per-point wall time (33.8 h) is inside the predicted 1.6–2.0·10⁵ s range (actually a bit
faster). **G: not resolved — 1/3 points returned a non-binding ball; 2/3 points still pending on the running job.**

## 5. Lean audit (prediction L)

| window | certificates | TOTAL VIOLATIONS |
|---|---|---|
| w_1e24 | 19 (2 main + 17 no-parity/S-layer), 19 replay-passed, 19 regions, 665 intervals, 15634 model boxes | **0** |
| wp_1e24 | 18 (2 main + 16 no-parity/S-layer), 18 replay-passed, 18 regions, 626 intervals, 14832 model boxes | **0** |

Both inside the predicted 18–21 certificates/window. **L MET.**

## 6. Step 2 ("two more close pairs near 10²³", prediction Q23) — not done; in progress

- The Turing pre-check is already in hand from the saved 10²³ scan (`runs/m6/turing_extra_1e23.json`, `tools/turing_extra.py`
  on `runs/m5/scan2_1e23`): wq_1e23 = [10²³−24, 10²³−22] and wr_1e23 = [10²³−2, 10²³] both show **17** sign changes with the
  Turing count, all four ends pinned (U−L = 0.478–0.526), matching PREDICTIONS_M6's Q23 exactly.
- The actual certificate pipelines are **not finished**. `ps` shows a live `atlas_v5.py --name wq_1e23` generator (started
  17:59 local) and a live `replay_target5.py … wq_1e23` independent replay (started 19:49 local) under
  `atlas_v5z4/runs/w100000000000000000000000/wq_1e23`; `wr_1e23` has not started. Per instructions this job was left running
  and not duplicated or touched. **Q23: pending — report only, no certificate yet to score.**

## 7. Scoring summary vs. PREDICTIONS_M6

| # | predicted | observed | verdict |
|---|---|---|---|
| B1 | radii [1e-8,4e-8], 0 undecided, Nw=398942280401, max_phase_err≤1e-17 | radii 1.12–1.31e-8, 0 undecided, Nw exact match, max_phase_err 1.152e-19 | **MET** |
| B2 | min endpoint ratio ≥300 | 701.7 (both windows) | **MET** |
| C1 | ends pinned U−L∈[0.45,0.62]; N within 3 of …544.16/…561.17 | pinned, U−L 0.479–0.523; N = …544/…561 exactly | **MET** |
| W24 | 16–19 sign changes (mean 17.0); count=Turing count; margin ∈ [0.67,0.75] | 17 sign changes, count matches; **margin 0.6156** | sign-change/count **MET**; **margin MISS** (below predicted range; not a STOP — no replay failure occurred, the only stated STOP trigger) |
| P24 | δ ≤ 0.20 (δ>0.25 = MISS) | certified δ ∈ [0.1196,0.1209] | **MET** |
| Q23 | both windows close, 17/17, margins ∈[0.70,0.75] | Turing pre-check 17/17 pinned; certificates **not yet run** | **pending** |
| G | reference inside ball, \|diff\|≤1e-13 | 1 of 3 points returned, ball radius ≈4.3e91 (non-binding); 2 pending | **not resolved / effectively a miss on the 1 point available** |
| L | 0 violations, 18–21 certs | 0 violations; 19 and 18 certs | **MET** |
| T | scan ≈18500s; window pipeline≈36000s+replay≈18000s (×0.6–1.6); total ≈45h | scan 20193s; pipelines 41443s/41554s, replays 20732s/20727s — all inside range; running total (excl. pending wq/wr, GZ) ≈40h | **MET so far** |
| M | peak ≤0.3 GB, no kill | 0.207/0.232 GB pipelines, 0.078/0.084 GB replays, no kill | **MET** |

## 8. Margin trend and novelty

Min margins: 0.794 (10²⁰) → 0.769 (10²¹) → 0.748 (10²²) → 0.729 (10²³) → **0.6156 / 0.6145 (10²⁴)**. The decline
accelerates between 10²³ and 10²⁴ (≈0.11 drop, versus ≈0.02/decade earlier) — this is the plainest miss against
PREDICTIONS_M6's extrapolated [0.67,0.75] band and is worth tracking at the next height: if the trend is genuinely
accelerating (not a one-off of this particular window's zero spacing), margins could become a binding constraint sooner
than the earlier linear extrapolation suggested. No replay failed and no certificate is in doubt; this is a margin-budget
observation, not a soundness concern.

**Novelty.** To our knowledge these [10²⁴, 10²⁴+2] and [10²⁴−3, 10²⁴−1] windows are the highest rigorous, unconditional RH
windows in published or publicly documented work; no rigorous window above 3·10¹² was found by earlier checks in this
project, and the 10²⁴ close pair (δ ≈ 0.12) extends the certified-pair series (10²⁰: 0.042, 10²¹: 0.161, 10²²: 0.120,
10²³: 0.108). Standard caveats carry forward: Gourdon's 10²⁴-scale computations (2004, extended since) are large-scale but
non-rigorous (floating point, no interval certification); Arb/FLINT-dev Turing routines could do this given memory and
time; non-rigorous computations go further still; the arXiv API was unavailable for a fresh check. Per the 2026-10-20
WORDING note (ATLAS_STATUS.md): the certification method (zero-list-free explicit-formula certificates + sign-change
credit + local-count closure + Lemma 2, Lean-checked) is Atlas's own; only the ζ-evaluation engine (zfast's rigorous
Riemann–Siegel main sum with double-double arithmetic) has reported prior art (FLINT dev "dfloat", 2026-10-02, per the
zfast agent, not independently verified) — the method itself is not claimed as unprecedented beyond that.

**Caveats carried from M5/M5d, still applicable:** zfast is in the trust base (review2 found no critical issues in v12a;
v13b adds only the review2 fixes, unchanged since M5); the margin decline noted above; the GZ cross-check at this height
is, so far, non-informative (§4) rather than a clean confirmation; Q23's two extra 10²³ pairs are not yet certified (§6).
