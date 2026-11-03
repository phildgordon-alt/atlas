# geval_c: independent adversarial review (2026-10-21)

**Scope.** I read the following:
* `THEORY_GEVALC.md`, `INTEGRATION.md` and `RESULTS.md`;
* `gc_core_v3.c` in full, with `libgc_v3.dylib`;
* `gc_lib_v2.py`, `gc_wrap_v3.py`, `gc_eval_v1.py` with its generator `tools/mk_eval_v1.py`, and `gc_plan_v1.py`;
* `cert_field_c3.py`.

I compared them against the frozen `geval_stream/geval_s1.py`, `geval_stream/review/REVIEW.md` and `general_eval/audit2/AUDIT.md`. All
14 files in `CODE_AT_VALIDATION_v3.sha256` verified OK before and after the review, and `SHA256SUMS` is all OK.

**Rules.**
* Nobody was contacted and nothing was posted.
* All runs were sequential at nice 19, one thread, under `geval_stream/wd_v1.sh` with FP_MB = 800. The peak footprint was 709 MB (the
  exact-moment reference in `t_moments.py`); every other run stayed ≤ 230 MB.
* The artin_sweep queue (PID 1901) kept running and was not touched.

**Incidents.** These are all of them. No pre-existing file was modified or deleted.
* **One file was created outside `review/`:** `geval_c/__pycache__/gc_lib_v2.cpython-312.pyc` (10:49). A diagnostic `python -c` (the dyld
  image check, §6) ran without `-B`. The file did not exist before, and it was left in place.
* **I deleted and edited some of my own files inside `review/`.**
  * I deleted the first draft of my N1 mutant (`mut/N1_class_beyond_C5.{c,dylib}`), built minutes earlier. It was an equivalent mutant
    (see §4). The rebuild uses a new name.
  * I edited `t_lemmaF.py`, `t_moments.py` and `PREDICTIONS_REVIEW.md` in place. The two scripts were edited before their scored
    runs. The predictions file got an appended addendum, which is marked as such.
  * `shadow/`, `rcert.py` and `rcert_v2.py` are broken or superseded drafts. They were never used for a scored run.

## Verdict

**No critical finding.**
* The numerical core is correct as far as I can test and prove it: Lemma F, the REDC bound, the multi-limb width, two's complement
  ring arithmetic, Lemma P, the C7 residues and thread determinism.
* I reproduced the certificates myself, with a character-level diff (§5).
* All 9 new faults (8 C, 1 Python) were caught before any certificate file existed.

**geval_c may carry claims in the Artin sweep, under these conditions:**

1. **Fix m1 before the first claim run.** Refuse optimized Python: an explicit `if sys.flags.optimize: raise SystemExit`, not an
   `assert`, and record `sys.flags.optimize` in the code record. Today, `PYTHONOPTIMIZE=1` strips every check C1–C7 and the
   loaded-library assert. A mutant library then produces certificates with status DONE and `mutation_test: false` (E4b). This is
   about ten lines of wrapper code, reviewable by diff. The fixed wrapper needs a new hash record.
2. **Claim runs** are launched through `wd_v1.sh`, with `GEVALC_LIB`, `GEVALC_MUTATION_TEST` and `PYTHONOPTIMIZE` unset.
   `verify_sweep_v2` should reject a run in any of these cases (m2, m3):
   * the code record is missing;
   * `mutation_test` is true;
   * `lib_sha256` differs from the recorded libgc_v3 hash;
   * `lib` is not `geval_c/libgc_v3.dylib`;
   * `optimize` is nonzero (once recorded).

   It should also bind every certificate file to such a summary through `file_sha256`.
3. **C1–C7 stay mandatory.** Together with the author's M1–M5, each of the 14 faults was stopped by a check or a C abort before any
   certificate existed:
   * 6 by C7 (M1, M2, M5, N3, N7, N8);
   * 3 by C6 (N4, N5, N6);
   * 2 by C1 (M4, N1);
   * 1 each by C2 (N1b), C5 (M3) and a class-pass abort (N2).

   No single check covers the others. N5 passes C7 and N8 passes C3. Separately, a foreign library without the test flag is
   stopped by install() (E1, E2).
4. **No unreviewed code change.** This includes lifting the 2³² − 1 limit and the degree ≠ 5 path. That path is the verbatim
   gs_sieve_v1 DDF, so it is covered by the earlier review, not by my Lemma F tests.

## 1. Evaluator text and bounds (task 1)

**The evaluator text is geval_s1 except one block.**
* `tools/mk_eval_v1.py` regenerated from the frozen `geval_s1.py` gives a file **byte-identical** to `gc_eval_v1.py`
  (`review/gc_eval_regen.py`). The geval_s1 sha256 is 8910cd18…, matching `geval_stream/CODE_AT_VALIDATION.sha256`.
* `diff` of `Evaluator.__init__` against `GCEvaluator.__init__` has exactly one hunk: the stream loop, which becomes the
  `isinstance(stream, GCStream)` branch. The old loop is kept verbatim, re-indented, as the else branch.
* In the new branch, `C['absum'] = …` / `C['mom'] = …` replace the frozen `+=` on zero-initialised values, which is equivalent.
* The nonneg assert uses the pass-2 count of a_n < 0 on [1, X], the same set as the frozen per-block `blk.min() >= 0`.
* `ns ≤ 100 < 128`, so every singleton is in the pass-1 target set (C6 singletons).

**All bounds are inherited unchanged.**
* `GCEvaluator` defines only `__init__`. Q, strip_M, trap_err, stirling_C, node_err, taylor_rem, tail_X, jet, value and value_A are
  geval_s1's.
* `gc_plan_v1` replaces only float planning helpers: `plan_tail_params`, and `lgamma_r` memoised. Rigour does not depend on them.
  tail_X asserts `cp > need` and `1 < β < cp − w/2` on the chosen values, and all bound arithmetic is in Arb.
* I re-checked bit-identity on 60 fresh random cases per module (N up to 10¹⁶, X up to 2³² − 2, A < 1 and A > 1): **0 mismatches**,
  including types (`logs/t_plan_review.json`). I also re-read the operand order of the vectorised expression against `_tail_log`,
  and np.argmin's first occurrence against the strict `<` rule.

## 2. Lemma F and `cycle_code5b` (task 2)

**Proof.** The proof holds.
* Frobenius gives g2 = g(g(x)) ≡ x^{q²} (mod f).
* For f squarefree, gcd(f, x^{q^k} − x) is the product of the irreducible factors whose degree divides k. Hence d1 = c₁ and
  d2 = c₁ + 2c₂.
* The rest has degree 5 − d2 and consists of factors of degree ≥ 3, so it is either empty or a single factor of degree 3, 4 or 5.

**Enumeration of all 17 factorisation patterns of degree 5, including repeated factors** (`logs/t_lemmaF.json`). The routine sees
d1 = the number of *distinct* linear factors and d2 = d1 + 2·(the number of distinct quadratics).
* On the 7 squarefree partitions, (d1, d2) is injective: (5,5), (3,5), (1,5), (2,2), (0,2), (1,1), (0,0). The code equals the DDF
  encoding in every case.
* 9 of the 10 non-squarefree patterns abort (rem = 1 or 2). In the symbolic table, 6 of them do.
* **Four repeated-factor patterns silently return a valid but wrong code:**

  | pattern | routine returns |
  |---|---|
  | (x−a)(x−b)⁴ | 0x102 |
  | (x−a)²(x−b)³ | 0x102 |
  | (x−a)²·cubic | 0x1001 |
  | (x−a)⁵ | 0x1001 |

  As in the earlier review's m4, squarefreeness is **not** tested by the routine. It rests on the two exact disc checks:
  * the class pass marks q | disc f as 255;
  * gc_prepare applies the source's own disc test, and a missing override aborts.
* Empirically, 168 constructed polynomials covering every pattern ran through the production `gc_cycle_code5b`. The primes were
  3, 5, 7, 11, 101, 65537, 10⁶+3, 2³¹−1, 2³¹+11 and 2³²−5. The result agreed with the prediction in every case: correct code,
  predicted wrong code, or abort.

**Production class pass vs flint `nmod_poly.factor`**: 1 236 021 primes, **0 mismatches**, every class code present.
* The production pass is `gcc_new_mt` with 1 thread.
* Every prime dividing disc f in range was class 255.

| f | range | primes |
|---|---|---|
| 5.1.87529.1 | all q in (2, 3.2·10⁶] (incl. 3, 5, 7 and the disc primes) | 230 208 |
| 5.1.22237.1 | 2³¹ ± 2.3·10⁶ | 214 248 |
| 5.1.18485.1 | (2³² − 5·10⁶, 2³² − 2] | 225 259 |
| 5.1.19761.1 (index 3) | (10⁹, 10⁹ + 4.8·10⁶] | 231 554 |
| 5.1.22352.1 | 2²⁴ ± 2·10⁶ | 240 489 |
| cyclic quintic (conductor 11) | (2, 6·10⁵] | 49 097 |
| large coefficients (up to 2⁴⁵, both signs) | (4·10⁹, 4.001·10⁹] | 45 166 |

**Arithmetic, read line by line.**
* m64_init:
  * the Newton iteration from x = q (3 bits) takes 5 steps, giving 96 ≥ 64 bits;
  * `one = (−q) mod q` = 2⁶⁴ mod q, and r2 = 2¹²⁸ mod q.
* REDC: for t < q·2⁶⁴, the sum s = t + m·q < 2q·2⁶⁴, so u < 2q, and one conditional subtraction follows.
* The "≤ 9 products per slot" claim is exact. Per slot in sqrmod5b, counting the products added by the reduction of higher slots, the
  counts are 2, 3, 4, 7, **9**, 7, 5, 3, 1 (slots 0..8, assuming dense inputs). So the maximum is 9q² < q·2⁶⁴ for q < 2³²; mulmod5b
  is the same. Every addend is a product of two values < q, in the same R² scale.
* mulx5b adds a value < q to one < q, then subtracts once.
* Horner g2 = Σ g1ᵢ·g1^i is correct.
* deg_gcd_b computes A ← lc(B)·A − lc(A)·x^k·B. This keeps gcd(A, B), since lc(B) ≠ 0. All values are in the uniform R scale, so
  degrees are unaffected.
* The dt < 0 case (g = x) is handled as d = 5.

## 3. Exact moments, threads, sanitizers (task 3)

**Width.** S = Σ|a_n| < 2⁶³·2³² = 2⁹⁵. With w = ⌈(96 + bJ)/64⌉ + 1, 64w − 1 ≥ 96 + bJ + 63 > 95 + bJ, so |M_j| ≤ S·D^j <
2^{64w−1}. Every operation is a ring operation mod 2^{64w}, so the signed residue is M_j.

**Carries and borrows.**
* `tc_add_mag` / `tc_sub_mag` propagate to w limbs.
* `tc_addmul`: x·s + acc + c ≤ 2¹²⁸ − 1.
* `tc_submul`: br stays ≤ 2⁶⁴ − 1 (see c1).
* The window accumulators carry-check into wi limbs (abort on overflow).
* T is reduced into the w-limb ring with wc = min(wi, w) limbs, which is exact (TP and TN are exact in wi limbs).

**Lemma P** (the binomial shift loop) is proved correctly: the induction on (e + s)^k e^{j−k} holds. The shift uses ring operations
for both signs of s.

**C7.**
* mod61 for t < 2¹²²: r < 2⁶², then ≤ P + 1, then the final subtraction.
* s2m61 is safe for INT64_MIN.
* It shares no code with the limb route. It does share `out` and the cell range [a0, a1], so a range fault is C6's job (N5 below
  confirms this).

**Tests** (`logs/t_moments.json`, `logs/t_limbs.json`):
* **Production dylib vs exact Python big-integer moments from the frozen `coeffs.sieve`:** 0 mismatches in every cell (Σ|a|, every
  M_j, singletons, nneg, C7 residues). The run used:
  * two sources: ζ_K10 of 5.1.18485.1 with overrides above r, and a synthetic **signed** sparse series (455 474 negative a_n,
    |a| up to 1.16·10⁹);
  * four request geometries in one pass-2 call: A (J = 48), B (J = 56), δ = 1/2 with J = 120 (the C maximum; 39 limbs, moments up
    to 2249 bits), and a fine geometry with δ = 1/1000;
  * block sizes 2¹⁶ and 4097, with the window route on (≈ 1.8–2.1 M terms through windows) and off.
* **Pass 1** (|a|, a and n·a prefixes, targets, nneg/amax) vs exact cumulative sums: 0 mismatches.
* **Block streams** at block sizes 1000, 4097, 2¹⁶ and 2²⁰ equal the frozen sieve.
* **Extreme limb test** (`t_limbs.c`): 300 windows with dense a_n up to ±(2⁶³ − 1) (149 390 such values) and centres m up to 2³² away
  (|s| up to 2³²), with J ∈ {1, 2, 3, 7, 48, 56, 120}. The direct route equals the window route equals the exact value, and the
  residues equal M_j mod P, in all 300 (moments up to 3898 bits).
* **UBSan** (`-fsanitize=undefined,bounds`, no recover) and **Guard Malloc** (guard page after, before, and with
  MALLOC_STRICT_SIZE=1): 0 reports, 0 crashes, and the outputs equal production. The harness `harness_gc.c` includes gc_core_v3.c
  verbatim.
  * Pitfall: launching through `/usr/bin/nice` silently drops DYLD_INSERT_LIBRARIES (SIP), so Guard Malloc is not loaded. My runs
    launch the harness directly and assert the `GuardMalloc[` banner.
  * ASan was not used. The earlier review found its runtime hangs on this macOS.
* **Thread determinism.**
  * By inspection:
    * `gcc_new_mt` writes classes and checkpoints at global indices from phase-1 counts;
    * the ranges are disjoint;
    * the counters are per job, and the joins come before any read;
    * the class index is fixed (CODES5).
  * By test, honouring the one-thread rule: a `-DSERIAL_THREADS` build runs every worker inline. With T = 2, 3, 7 and 64, the class
    array, checkpoints and counts are byte-identical to T = 1 (FNV hashes), and all downstream outputs are equal. I did not run
    concurrent threads; the author's T = 4 run (`t_classes_mt_v1`) covers that.
* **Build provenance.** Rebuilding `libgc_v3.dylib` from `gc_core_v3.c` with the `build_v3.sh` flags gives the same instruction
  stream (8070 lines; modulo a 16-byte layout shift, one `adrp` page immediate differs) and byte-identical `__cstring` / `__const`.

## 4. Checks C1–C7 and mutations (task 4)

**Is each check fail-closed?**
* **C1, C2, C5 and C6/C7** are Python `assert`s. They raise before the driver writes a file, but **not under `-O`** (m1).
* **C4** is the Python headroom asserts plus `__builtin_*_overflow` in C, which aborts.
* **C3** is partly fail-open (m2):
  * the geval_stream hashes are asserted;
  * the geval_c file hashes are checked only if `CODE_AT_VALIDATION_v3.sha256` exists;
  * the loaded-library hash is skipped under `GEVALC_MUTATION_TEST=1` (recorded);
  * it hashes files on disk, not the loaded objects.
* **C6's nneg comparison** is conditional on X being a recorded point. In the field drivers it always is (X = lo − 1 of a grid cell,
  or X2), but it should be an assert (c4).

**Mutation runs.** The table records nine new faults, pre-registered in `PREDICTIONS_REVIEW.md`, sha256 3ee78b10… before the
addendum. They are different from the author's M1–M5. Each ran `cert_field_c3.main`, unchanged and redirected into
`review/mutruns/<id>`, on 18485 k10 A + FE A in a fresh process. **certificates written = 0 in every case.**

| id | fault | stopped by | predicted |
|---|---|---|---|
| N1 | class (2,1,1,1) → (4,1) for q > 10⁶ (outside the C5 window) | C1 prefix (q ≤ 2·10⁶ lies inside the prefix) | C2: wrong check, caught |
| N1b | the same for q > 4·10⁶ (outside C1 and C5) | **C2** (random n / windows vs factor-n) | yes |
| N2 | REDC leaves u = q unreduced (a non-canonical 0, rare) | C abort in the class pass (inconsistent gcd degrees) | yes |
| N3 | two's complement carry ripples ≤ 1 limb past the magnitude | **C7** | yes |
| N4 | singleton a_ns never copied | **C6 singleton** check | yes |
| N5 | last n of each cell dropped from Σ\|a\|, C7 residues and moments alike | **C6 Σ\|a\|** (C7 silent: shared range) | yes |
| N6 | pass-1 n·a_n prefix uses (n − 1)·a_n beyond 10⁶ | **C6 M_1** | yes |
| N7 | binomial shift s off by one in ≈ 1 % of windows | **C7** | yes |
| N8 | Python: gc_lib_v2 copy reading moments unsigned, shadowing the frozen module | **C7**; **C3 silent** | yes |

The deleted first draft of N1 swapped (3,1,1) ↔ (3,2). It turned out to be an *equivalent* mutant for ζ_K10 and ζ_F: both cycle
types have b1 = 1 for K10 (one fixed pair) and b1 = 0 for F (no fixed point on 6 letters). So it could not change a certificate.
That is why it was replaced.

## 5. Independent reproduction (task 5)

My runner `review/rcert.py` imports the unchanged `cert_field_c3.main` and changes only its output root. I reproduced **all 8
certificate files of 5.1.22352.1 and of 5.1.18485.1** (`review/repro/`, 19 s and 40 s). The comparer `cmp_certs.py` is my own: raw
line diff plus every non-volatile leaf (`logs/cmp_certs.json`).
* **Against the geval_c scored files** (V8, V1): the only differing raw lines are `time_s`, `t_*` and `maxrss_mb`. Every one of the
  1145 / 716 / 856 / 632 / 836 / 612 / 837 / 613 leaves is identical, so the canonical text is identical.
* **Against the artin_sweep originals** (the frozen streamed provider): every enclosure, verdict, X, X2 and cell value is identical.
  The only differences are inside `*/eval/gs_stats`: nT, table_bytes, b1_override, and the renamed keys fresh/b1_poly/b1_sparse vs
  b1_tab/class_offset. These are engine-internal table statistics, expected because geval_c tabulates b1 up to nmax, not nmax/2
  (c7).

## 6. Environment switches (task 6)

| id | environment | outcome |
|---|---|---|
| E1 | GEVALC_LIB = mutant, GEVALC_MUTATION_TEST unset | install() assert, 0 certificates |
| E2 | GEVALC_LIB = mutant, GEVALC_MUTATION_TEST=true (not "1") | same as E1 (only "1" enables the test mode) |
| E5 | genuine library, GEVALC_MUTATION_TEST=1 | certificates canonically identical to a claim run; only the *summary* says MUTATION_TEST (m3) |
| E3 | DYLD_LIBRARY_PATH = dir with the N3 mutant named libgc_v3.dylib, via wd_v1.sh | **no effect**: `/usr/bin/nice` (SIP) strips DYLD_*; the certificates equal E5 |
| E3b | the same, but DYLD_LIBRARY_PATH set after nice (a direct launch) | dyld **loads the copy** (confirmed with `_dyld_get_image_name`); C3 passes, because it hashes geval_c/libgc_v3.dylib; C7 then caught the fault |
| E4 | PYTHONOPTIMIZE=1, genuine library | `__debug__ = False`: every check is skipped, status DONE, every check record says `ok: True` |
| E4b | PYTHONOPTIMIZE=1 + GEVALC_LIB = N3 mutant | **2 certificates written**, status DONE, `mutation_test: false`; only `lib` / `lib_sha256` in the code record reveal it (m1) |

**Conclusion.** GEVALC_LIB and GEVALC_MUTATION_TEST cannot by themselves silently affect a claim run. A foreign library aborts unless
MUTATION_TEST=1, and that mode is recorded in the summary. They can, together with PYTHONOPTIMIZE (or `python -O`), and that variable
passes through the production launcher. GEVALC_THREADS changes only wall time (§3).

## 7. Findings

**Critical:** none.

**Minor.** m1–m3 are conditions for claims; m4 is documentation.
* **m1 — the checks fail open under optimized Python.**
  * Every mandatory check, and the C3 library assert, is an `assert`. `PYTHONOPTIMIZE=1` or `-O` removes them all (E4, E4b).
  * INTEGRATION's "C6/C7 are asserts, so a completed run implies they passed" is false in that mode.
  * The frozen drivers share the property, so this is pre-existing for geval_stream too.
  * *Fix:* `if sys.flags.optimize: raise SystemExit` in `install()`, and record the flag in the code record.
* **m2 — C3 verifies files on disk, not the loaded code.**
  * (a) A shadowed `gc_lib_v2` passes C3 (N8).
  * (b) DYLD_LIBRARY_PATH on a direct launch substitutes the library while C3 hashes the frozen file (E3b). The relative
    `GEVALC_LIB` path has the same split (abspath vs the dlopen search).
  * (c) A missing `CODE_AT_VALIDATION_v3.sha256` silently skips the geval_c hash check.
  * *Fix:* hash the image dyld actually loaded (`dladdr` on `gc_new`) and each loaded geval_c module's `__file__`. Refuse if DYLD_*
    or GEVALC_* are set in claim mode, and make a missing hash file fatal.
  * The production path (wd_v1.sh → /usr/bin/nice) already blocks (b).
* **m3 — certificate files carry no provenance.** The engine, library hash and mutation flag appear only in the field summary.
  verify_sweep_v2 must join each certificate to its summary through `file_sha256` and check `lib_sha256` and `mutation_test` there,
  plus `optimize` after m1.
* **m4 — the Lemma F routine is not a squarefreeness test** (§2: 4 patterns silently give a valid code). It is correctly guarded by
  the two disc checks. THEORY §2 says so; keep it that way for any reuse of `gc_cycle_code5b`.

**Cosmetic**
* **c1** — The `tc_submul` comment says hi ≤ 2⁶⁴ − 2. In fact hi can be 2⁶⁴ − 1, but only with lo = 0, so br ≤ 2⁶⁴ − 1 still holds
  and nothing overflows.
* **c2** — Unary minus on int64 in `mom_direct`, `mom_window` and the pass-2 abs is undefined behaviour for INT64_MIN. pass 1 aborts
  on INT64_MIN and always precedes pass 2 over a superset range, so this is unreachable. Add the guard in pass 2 too.
* **c3** — gc_prepare checks prime-sequence alignment every 1024 primes, plus the total only when the class table ends at nmax. A
  desynchronisation in the last < 1024 primes below nmax is checked only by C2's end window. Compare the final index as well.
* **c4** — The C6 nneg comparison is an `if`, not an assert.
* **c5** — `GEVALC_THREADS` is not recorded in the `classes` check record.
* **c6** — The `lgamma_r` memo key equates Fraction and float mus. This is harmless for the dyadic mus in use.
* **c7** — `gs_stats` key names differ from the streamed originals. Comparers should exclude them explicitly (§5).

**Efficiency.** I found no regression. The m1 fix costs nothing. C7 costs 30–50 % of pass 2 and caught 4 of the 9 new faults, 1 of
them only because C3 had been bypassed (N8), so it should stay.

**Residual risk** (as for the frozen path). The sampling checks C1, C2 and C5 cannot exclude a fault confined to very few large
primes. Correctness there rests on the code and proof review above, which found nothing.

## Files (all in review/)

| file | role |
|---|---|
| `gc_eval_regen.py` | T1 regenerated evaluator (byte-identical) |
| `t_lemmaF.py`, `logs/t_lemmaF.json`, `logs_t_lemmaF.out` | T2 symbolic enumeration, patterns, 1.24 M primes vs flint |
| `t_moments.py`, `harness_gc.c`, `bin/harness_ub{,_serial}`, `data/setup_*`, `data/req_*`, `data/sparse_S.bin`, `logs/t_moments.json`, `logs_t_moments.r2.out` | T3 exact moments, pass 1, blocks, UBSan / Guard Malloc, serial-thread shim (`logs_t_moments.out` is the first run, in which Guard Malloc was stripped by nice) |
| `t_limbs.c`, `t_limbs.py`, `bin/t_limbs_ub`, `logs/t_limbs.json` | T3 extreme multi-limb test |
| `bin/libgc_rebuild.dylib` | T3 build provenance |
| `t_plan_review.py`, `logs/t_plan_review.json` | T1 planner bit-identity |
| `mk_mut.py`, `mk_mut2.py`, `mk_mut3.py`, `mut/`, `shadow_v2/`, `dyld/`, `dyld_exec.py`, `rcert_v3.py`, `run_mut_review{,2}.sh`, `PREDICTIONS_REVIEW.md`, `mutruns/`, `logs/mut_*.log`, `logs/run_mut_review.progress` | T4/T6 mutants and environment runs |
| `rcert.py`, `cmp_certs.py`, `repro/`, `logs_repro_*.log`, `logs/cmp_certs.json` | T5 reproduction and comparison |
