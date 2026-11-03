# geval_stream: independent adversarial review (2026-10-21)

Scope: `THEORY_STREAM.md`, `INTEGRATION.md`, `RESULTS.md`, `geval_s1.py`, `gs_sieve_v1.c` (+ `libgs_v1.dylib`), `gs_stream_v1.py`, the
drivers `cert_k10_s1.py`, `negctl_k10_s1.py`, `cert_FE_s1.py`, `ecnf_cert_s1.py`, `ecnf_cert_bc_v1.py`, `cert_newfield_v1.py`, against the
frozen `general_eval/geval.py` (sha256 5e201f6f…, equal to `general_eval/SHA256SUMS`) and `general_eval/audit2/AUDIT.md`.

Rules: nobody was contacted, nothing was posted, nothing was deleted. All runs were sequential at nice 19 under `wd_r.sh`, an 800 MB
copy of `wd_v1.sh`. The peak footprint of any run was 559 MB, in the sanitizer driver; every other run stayed ≤ 245 MB.

**Incident.** One write landed outside `review/`. Running the production `compare_v1.py` once on the M5 mutant appended one line, tagged
`"x"`, to `geval_stream/runs/compare_v1.jsonl`. That script always appends to that file. The first 21 lines are unchanged: their sha256 is
cb0266cc…, the value in `SHA256SUMS`. So `shasum -c SHA256SUMS` now fails on that one file only. The line was left in place, because
removing it would be a second edit. Whoever owns the file should drop line 22 or keep it with this note.

## Verdict

**No critical finding.** The streamed evaluator computes the same integers and the same balls as the frozen one:
* every certificate reproduced character-identical;
* streamed coefficients agree with independent PARI computations at the largest X2 actually used.

**Streamed runs may carry the new claims (Artin sweep to d ≈ 10⁵, cubic sweep, LMFDB curves) under three conditions:**

1. **Standing coefficient check.** Each claim-carrying run, or at least each new family/field, runs a coefficient check that crosses
   several block boundaries (m1, m2). The per-run check `INTEGRATION.md` proposes ([1, 10⁶] vs the frozen sieve) contains **no** interior
   block boundary, and is not implemented in any driver.
2. **No unreviewed code change.** The code does not change. Lifting the 2³² − 1 limit, or any edit to `gs_sieve_v1.c`, needs a re-review.
   At d ≈ 10⁵ the K10 X2 is about 2.4·10⁹, inside the limit; the limit is reached near d ≈ 1.3·10⁵. Exceeding it aborts; it is not silent.
3. **Overflow guard before larger families.** Before families with larger |a_n| or degree (cubic sweep, higher-degree curves), add the
   cheap int64 headroom assert (m5).

The minor items below are hygiene. None affects any existing result.

## 1. geval_s1.py vs frozen geval.py (task 1)

`diff general_eval/geval.py geval_stream/geval_s1.py` has 12 hunks. Each one is accounted for:

| hunk | content | class |
|---|---|---|
| docstring, `[geval_s1]` print tag | text | cosmetic |
| `amax_up` (new), `strip_M` G, f1, f2 | `max(up(x), up(y))` → max of the exact `x.upper()` arbs | **m1** |
| `Evaluator.__init__` signature + docstring | `stream`, `tail`, `nonneg` | streaming |
| `assert self.c >= 1` | Lemma D q-bound needs \|z\| ≥ 1; \|z\| ≥ Re z = c | **m4** |
| cell geometry | identical formulae (m, lo, hi, dmax, deltaC); `idx`/`vals` no longer stored | streaming |
| singletons, Σ\|a_n\|, moments | same chunked exact Python-integer code (CH = 2¹⁸), accumulated per block | streaming |
| added asserts | contiguity, `nseen == X`, `ci == len(cells)`, `S >= 0`, cell ∈ supplied grid | streaming (safety only) |
| `nonneg` asserts | a_n ≥ 0 on [1, X]; nneg = 0 on [1, X2] | **m3** |
| tail cells | frozen formula; S from `tail` (exact Σ\|a_n\|) | streaming |
| `tail_X` middle range | `assert cp > need` | **m2** |

**Error bounds.** Every bound function is textually identical to the frozen one, except the m1 lines in `strip_M` and the m2 assert:
rad_D (Lemma D), Q, trap_err, stirling_C, node_err, taylor_rem, the Rankin range, jet, value, value_A, plan, plan_tail_params and
choose_X. The m1 change can only raise the upper bound, by at most the last bit.

**Equivalence of the moments.** The frozen moments are exact integer sums. The streamed ones are the same sums split at block
boundaries, so the result is the same integer, then the same `arb(mom)/arb(m)^j`. This is confirmed empirically (§4).

The drivers' diffs match the hunks listed in INTEGRATION.md:
* the frozen `Ev3` (calegari3) is replaced by `geval_s1` with `tail=`, equivalent because Ev3 only replaces X2/tcells;
* the frozen tail sums Σ a_n become Σ|a_n|, equal under nneg = 0, which is now asserted on [1, X2].

## 2. gs_sieve_v1.c review (task 2)

**Algorithm, read line by line.**

*Small-prime pass.*
* Every multiple m of p in [s0, e0) gets b_p[v_p(m)].
* t = m/p and c = t mod p are recomputed at each block start, so no state crosses a block.
* When c = 0, v ≥ 2 is found by division; `v > kmax` aborts.

*Large-prime pass.* n = kq with q > r prime and k ≤ (e0−1)/(r+1) < q.
* a_n = a_k·b1(q), and a_k is already in `out[n]`.
* The q-range is [max(r+1, ⌈s0/k⌉), ⌊(e0−1)/k⌋].

*Lemma C* (cursor contiguity) was re-derived and holds:
* the first active block starts at r+1;
* a block with no multiple of k leaves the expected value unchanged.

*The two table paths* index the same table consistently:
* For k < 16, cursor = number of primes > r seen; T[idx] is the idx-th prime > r.
* For k ≥ 16, PV is exactly the prefix of the T-primes that are ≤ X2/16, so PV[idx] and T[idx] refer to the same prime.
* For k ≥ 2, idx < nT always (q ≤ X2/2), and this is asserted.
* q > X2/2 occurs only for k = 1 and is computed fresh.

*range_primes* is correct: it sieves [lo, hi] with all p ≤ r, starting at max(p², ⌈lo/p⌉p), and lo > r.

**Frobenius cycle type.** This is distinct-degree factorisation:
* g = x^{q^d} mod h by left-to-right powering (Montgomery for p < 2³¹, plain 64-bit for p < 2³²);
* u = gcd(h, g − x), then h /= u and g mod= h;
* stop at 2d > deg h.

The Montgomery parameters are correct for odd p < 2³¹: Newton inverse with 5 steps gives 32 bits; t + mp < 2⁶⁴; u < 2p. There are two
edge cases, both minor (m3, m4):
* p = 2 is wrong;
* for p | disc the routine is not a squarefreeness test.

**The b1 table is an exact code identity, not only a theorem.** At p ∤ disc f and outside the override lists:
* frozen `coeffs.perm_local` (E2 and calegari2 fields) and `zFE.local_fn` compute F_p from the factorisation degrees of f mod p only;
* zFE ζ_E uses (D_E/p), and D_E | disc f.

So F_p is a function of the cycle type. The overrides are complete:
* every prime of disc f;
* every calegari2 `local` key (cert_k10_s1), or every algebra_pari `local` key plus the `override` keys (cert_FE_s1);
* a missing override for p | disc aborts (exact |disc| mod p).

Note on the cubic sweep: the identity holds for the Dedekind zeta of the field cut out by f itself, in any degree ≤ 15. For resolvent
fields of a non-S_n Galois group it needs the class-function argument again, and `expect_types` must be set to that group's class count.

**Overflow.**
* All C products of a_n are `__builtin_mul_overflow`-checked.
* Modular arithmetic is bounded as derived above (disc_mod < 2⁴⁸, mulm < 2⁶⁴).
* Indices and primes are uint64/uint32 under nmax < 2³² − 1 (asserted).
* The int8 and int32 table ranges are asserted.
* The unchecked paths are on the Python side (m5).

**Memory safety.** ASan could not be used: its runtime hangs during shadow-memory initialisation on this macOS, even for an empty
`main`. It was replaced by two tools:
* UBSan (`-fsanitize=undefined,bounds`, no recover);
* macOS Guard Malloc (`libgmalloc`), with a guard page after and, separately, before every allocation.

The harness is `harness.c`, which `#include`s the C file verbatim. It replays the setup calls recorded from the production
`CoeffSource`. Results (`logs/t_sanit.json`):
* 21 cases, 142 harness runs, 0 sanitizer reports, 0 crashes;
* the production dylib equals the frozen `coeffs.sieve` (an independent plain per-prime sieve) on every case;
* the harness checksums equal production for every case.

The cases:
* 1609 ζ_K10, 4417 ζ_K (calegari2 bad primes) and 18485 ζ_F (5 ramified) at 2·10⁶;
* ECNF 6.6.300125.1 in sparse mode at 3·10⁶;
* edge sizes nmax ∈ {4, 5, 10, 100, 289, 300, 600, 1000, 1100, 1500, 4096, 5000, 65536, 2²⁰−1, 2²⁰, 2²⁰+1, 3·2²⁰+7};
* each case with block sizes {1, 3, 64, 1000, 2²⁰} and 3 passes (X = nmax, nmax/3, nmax).

**Determinism.**
* Output is independent of block size (1 … 2²⁰) and of the pass sequence (above).
* All reproductions are identical (§4).
* Rebuilding `libgs_v1.dylib` from `gs_sieve_v1.c` with `build_v1.sh` flags gives an identical instruction stream (`otool -tv`,
  addresses normalised) and identical `__cstring` / `__const`. Only the install name / UUID differ, so the shipped binary is this source.

## 3. Independent coefficient check vs PARI (task 3)

The streamed side is `s_sample.py`:
* the production source is built exactly as the driver builds it, at the **largest X2 actually used**;
* the production pass 1 (`grid_sums`) is run and its blocks are tapped.

The independent side is `p_indep.py`, PARI 2.17.2, and imports no geval_stream or frozen code:
* **Dedekind:** a_n = Π_{p^k‖n} #{ideals of norm p^k}, from `idealprimedec` of `nfinit(M)`.
  * K10 is the pairs resolvent, recomputed here from f.
  * F is the artin_all sextic g.
  * The full prefix comes from `dirzetak`.
* **Curve:** `ellinit([1,2,1,−1,−3], K)`; F_p is built from `ellap(E, P)` with bad P ⟺ P | disc E; the full prefix comes from
  `lfunan(lfuncreate(E))`.

| L-function | X2 | random n (≤ X2) | windows 5 × 2·10⁴ (incl. one ending at X2, one across a 2²⁰ boundary) | full prefix vs dirzetak / lfunan | production grid cells checked | result |
|---|---|---|---|---|---|---|
| ζ_K10, 5.1.87529 (P6 field), nfdisc = d³ ✓ | 1 936 494 406 | 113 956, 0 mismatches (20 865 ≠ 0) | 0 mismatches; Σ\|a\| and Σa = production Pabs/P | [1, 2·10⁶]: 0 | 246 / 690, 0 | **OK** |
| ζ_K10, 5.1.38069.1, nfdisc = d³ ✓ | 484 605 840 | 113 481, 0 (20 254 ≠ 0) | 0; sums equal | 0 | 290 / 645, 0 | **OK** |
| ζ_F, 5.1.18485.1 (5 ramified), nfdisc = 6 316 236 234 125 = N ✓, sign (2,2) | 76 422 013 | 112 620, 0 (9 175 ≠ 0) | 0; sums equal | 0 | 349 / 585, 0 | **OK** |
| L(E/K), bc49 over 6.6.300125.1 (P7), cond. norm 2401 ✓ | 1 317 945 551 | 113 850, 0 (656 ≠ 0) | 0; sums equal | [1, 3·10⁵]: 0 (2 488 ≠ 0) | 136 / 678, 0 | **OK** |

* The streamed max|a_n| equals the value recorded in the original certificates: 12 320 (87529), 1 764 (38069), 203 860 800 (bc49).
* Caveat for bc49: the curve is CM and a base change, so most a_n are 0. Only 656 of the random n and 501 of the window n are nonzero.
  The nonzero evidence is mainly the 2 488 nonzero terms of the lfunan prefix and the window sums (Σ|a| ≈ 3–5·10⁷ per window).
* The large cells near X2 (length ≈ X2/64) were not summed independently. The window sums test the same `grid_sums` prefix-sum code
  on arbitrary boundaries near X2.

## 4. Certificate reproduction (task 4)

The production drivers were rerun unchanged, with only the output path redirected (`repro.py`). They were compared with
`compare_r.py`, which:
* drops only timings, memory and provenance strings;
* compares every leaf and the canonical text;
* reports keys present in only one file.

| run | vs frozen original | vs streamed original |
|---|---|---|
| V2 calegari3 5.1.1609.1 set A (+ Booker) | 823 common leaves, **0 differ**; 33 extra leaves are new diagnostics only (amax_X2, nneg_X2, cycle_table, overrides) | canonical text **identical** |
| V3 artin_all 5.1.13116.1 set A (ζ_F, ζ_E) | 866 common, **0 differ**; 30 extra diagnostic leaves | **identical** |
| V5 lmfdb_ecnf 2.2.5.1-31.1-a1 set A, 128 bits (sparse cache regenerated from the frozen rows inside review/: byte-identical) | 76 common, **0 differ**; extra `omega_prec` (the frozen JSON predates the final frozen ecnf_cert.py revision by 28 min; cosmetic) | **identical** |
| P7 bc49 set A (claimed new result) | n/a | **identical** (76 leaves) |
| P6 new.5.1.87529 set A (claimed new result; 671 s, 245 MB) | n/a | **identical** (821 leaves) |

## 5. Mutation tests (task 5)

Mutants are copies in `review/mut/`, with one-line changes. Each was run in a fresh process (`mut_one.py`, `run_mut.sh`) with the checks of
`test_coeffs_v1.check_family`:
* a_n against the frozen sieve;
* all grid-cell sums;
* b1 at 400 sampled large primes.

A C abort counts as caught. Results are in `logs/mut_results.jsonl`.

| mutant | 1609 K10, 3·10⁵ ("quick") | 1609 K10, 2·10⁶ | 1609 K10, 2·10⁶, BLOCK 2¹⁰ | 18485 F, 2·10⁶ |
|---|---|---|---|---|
| production (control) | clean | clean | clean | clean |
| M1a small-prime block start off-by-one (`(st+p)/p`) | **missed** | caught: **1** a_n (n = 2²⁰), 1 cell | caught: 1 920 a_n | caught: 1 a_n |
| M1b large-prime qlo off-by-one | **missed** | abort (contiguity) | abort | abort |
| M1c large-prime qhi off-by-one | **missed** | abort | abort | abort |
| M2 wrong cycle-type map (swap (2,1,1,1) ↔ (2,2,1)) | caught: 10 171 a_n, b1 77/400 | caught: 63 692 | caught | caught: 55 040 |
| M3 dropped prime power (v ≥ 3 treated as 2) | caught: 1 520 | caught: 9 312 | caught | caught: 5 203 |
| M4 last k dropped in large-prime loop | **missed** | abort | abort | abort |
| M5 geval_s1: last n of every block dropped from cells (13116 F set A run) | — | the certificate still says **CERTIFIED**, all residue checks overlap; compare_v1: ok = False (1 disjoint ball, 18/48 balls differ); compare_r: 104 leaves differ | — | — |

Every injected fault is caught by the full validation suite: the 2·10⁶ test, the contiguity asserts, and comparison with the frozen JSON.
Two limits matter for new claims:
* Block-boundary faults are caught at 2·10⁶ only because that range contains exactly one interior boundary. M1a was detected by a single
  coefficient. Quick mode and the proposed [1, 10⁶] standing check contain no interior boundary.
* A streaming fault of small measure (M5) leaves every in-run consistency check green. For runs beyond the frozen range, the coefficient
  checks are therefore the only guard.

## 6. Findings

**Critical:** none.

**Minor**

* **m1 — thin block-boundary coverage.** Evidence: §5. The 2·10⁶ test has 1 interior boundary, quick mode and the INTEGRATION standing
  check [1, 10⁶] have 0, and M1a is caught by one coefficient. *Fix, cheap:* in the standing check, stream a prefix with `GS.BLOCK = 2¹⁰`
  (≈ 1 000 boundaries) and compare it with the frozen sieve. Alternatively, compare the cell sums of a full pass at two block sizes:
  the output is provably block-size independent, and the harness confirms it.
* **m2 — standing check not implemented.** INTEGRATION item 3 is described as "recommended", but no driver performs a prefix
  comparison. Only the 7-class table assertion runs in every run. Given m1 and M5, make it mandatory for claim-carrying runs.
* **m3 — p = 2 wrong in `cycle_code`.** Montgomery is used with an even modulus; the C codes are wrong for 2 of 3 test polynomials
  (`logs/t_cycle_edge.json`). This is reachable only if r = ⌊√nmax⌋ = 1, i.e. nmax ∈ {2, 3}. No production X2 is that small; the
  smallest is 461. *Fix:* `usem = (p & 1) && p < 2^31`, or assert nmax ≥ 4.
* **m4 — `cycle_code` does not detect squarefreeness reliably.** For p | disc f it often returns a code silently: 87529 at p = 13 gives
  258, 1609 at p = 1609 gives 258, x⁵−x−1 at p = 151 gives 258. It aborts only sometimes. Correctness rests entirely on the exact
  `disc_mod` check in `b1_fresh`, and on `factor_mod`'s assert in the Python table builder. Both are correct. THEORY's "f is squarefree
  mod q" should name that check as the guard, and `gs_cycle_code` should not be used as a validation primitive for p | disc.
* **m5 — unchecked int64 on the Python side.**
  * ctypes silently wraps Python ints > 2⁶³ (small series b_p[k], overrides, table values).
  * numpy block `cumsum` in `grid_sums` and `np.abs(vals).sum()` in `geval_s1` are unchecked. The frozen geval has the same sum.
  * Current headroom is large: max|a_n| = 2.04·10⁸ (bc49), so block sums are < 2⁴⁸.
  * *Fix before the cubic and LMFDB-curve sweeps:* `assert g['amax'] * BLOCK < 2**62`, and range-check values before the ctypes
    conversion.
* **m6 — ECNF sparse cache keyed only by (label, X2, negap).** A regenerated rows file would silently reuse a stale cache. *Fix:* put
  the rows-file sha256 in the cache name or header. Regenerating from rows in review/ gave a byte-identical cache for 2.2.5.1-31.1-a1.
* **m7 — `compare_v1.py` compares only common keys.** It ignores keys present in one file only. Every reported "identical" result still
  stands: the strict comparer found only additive diagnostic keys. It also always appends to `runs/compare_v1.jsonl`, which caused the
  incident above. *Fix:* report key-set differences, and make the jsonl output optional.

**Cosmetic**
* `gs_block` line 537 reads `PV[nPV−1]` before testing `nPV > 0`. The statement is dead and is optimised away; Guard Malloc with an
  underflow guard did not trip at the edge sizes where nPV = 0. It is latent undefined behaviour: remove it.
* `static uint32_t *qb` in `gs_block` is shared by all handles, never freed, and not thread-safe.
* The cycle code's nibble overflows for 16 linear factors (MAXDEG = 16). Use MAXDEG ≤ 15.
* Records in the sparse file with p > nmax are never validated.
* `gs_add_small`'s p^k loop is not overflow-guarded for absurd k.
* Most mallocs are unchecked.
* ζ_F/ζ_E and ECNF random samples are mostly zeros (§3), so mismatch evidence there comes chiefly from the windows and the prefixes.
* The frozen V5 reference JSON predates the final frozen `ecnf_cert.py` revision (missing `omega_prec`); all values are equal.

## 7. INTEGRATION.md re-freeze checklist

| # | item | status |
|---|---|---|
| 1 | sha256 of the C, dylib, gs_stream, geval_s1 and drivers recorded | **Done and verified.** All current files match `CODE_AT_VALIDATION`, `CODE_AT_P6` and `CODE_AT_P7`. `SHA256SUMS`: 107 OK, 1 FAILED (`runs/compare_v1.jsonl`, the appended line above; its first 21 lines match). The dylib corresponds to the source (§2). |
| 2 | Non-author review of THEORY_STREAM (Lemma C, cycle type → b1) and gs_sieve_v1.c | **Done (this review).** Lemma C and the b1 argument hold (the b1 map is a code identity for the frozen local factors). The C code is correct, with minor items m3/m4. |
| 3 | Standing per-run check (frozen sieve on a prefix; ≥ 30 000 table primes, 7 classes) | **Partly met.** The table check runs in every run: ≈ 3.1–3.4·10⁴ primes in (r, r + 4·10⁵], 7 classes asserted. The prefix check is **not implemented**, and as specified it covers no block boundary (m1, m2). It is required for new claims. |
| 4 | Frozen pipelines kept as reference provider | **Met.** Frozen files are unchanged (`general_eval/geval.py` hash = its SHA256SUMS), and reproductions vs frozen are identical (§4). |

## Files (all in review/)

| file | role |
|---|---|
| `rlib.py` | paths; mutant-lib loader (exec of the unmodified gs_stream_v1 source with only the CDLL path replaced); setup recorder |
| `harness.c`, `t_sanit.py`, `logs/t_sanit.json`, `data/sanit_*.txt` | T2 sanitizers (UBSan + Guard Malloc), recorded setups |
| `t_cycle_edge.py`, `logs/t_cycle_edge.json` | T2 cycle_code edge primes |
| `s_sample.py`, `p_indep.py`, `data/samp_*`, `logs/p_indep_*.json` | T3 streamed sampling, independent PARI |
| `repro.py`, `compare_r.py`, `repro/runs/cert/*`, `logs/compare_r.jsonl` | T4 reproductions, strict comparison |
| `mut/*.c`, `mut/lib_*.dylib`, `mut/geval_s1_M5_block_end.py`, `mut_one.py`, `run_mut.sh`, `mut_geval.py`, `repro_mut/`, `logs/mut_*` | T5 mutants and results |
| `wd_r.sh`, `bin/` | watchdog (800 MB), builds (rebuild dylib, harness, ASan test binaries) |

Notes on the files:
* `logs/t_sanit.log` is the first sanitizer attempt, abandoned when ASan hung.
* `logs/*aborted_first_try*` is a mutation run restarted to get unique log names.
* `data/sanit_1609_K10.txt` was written by both sanitizer attempts. The content is deterministic.
