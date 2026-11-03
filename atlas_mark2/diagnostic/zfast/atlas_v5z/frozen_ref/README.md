# atlas_v5 — atlas_v4 with exact heights (2026-10-08)

atlas_v5 certifies the same claim as atlas_v4: every zero of ζ with ordinate in the hull lies on the critical line and is simple.
Claim (A) gets simplicity via Lemma 2; claim (B) gets it without Lemma 2. v5 can do this at any height. Two changes make that possible
(theory, written before the code: `THEORY_V5.md`):

1. **Exact heights.** Every height is an integer T0 plus a binary64 offset u, and the real number T0 + u is exact. This covers bins,
   windows, model boxes, regions, sign-change endpoints and sech-row centres. All Arb evaluations use the exact height (`lib/heights.hx`).
   The verifier, `lib/verify_zs5.py`, is the pinned v4 verifier with 4 documented changes and identical inequality logic
   (`dev/verify_zs5_diff.txt`).
2. **Dirichlet-sum prime side** (`lib/sech5.py`). Each sech row needs one Arb ζ'/ζ jet instead of 10–16. The k ≥ 1 terms are summed in
   closed form over n ≤ 10^6, with a proved tail (Lemma D).

Results: `RESULTS.md`. Pre-registration: `PREDICTIONS.md` (sha in `PREDICTIONS.sha256`). Code freeze: `V5_FREEZE.sha256`.
`atlas_v4/` is untouched.

**Certified (claims A and B):**
- [10^12, 10^12 + 2] (control, inside Platt–Trudgian);
- [10^13, 10^13 + 2] and [10^14, 10^14 + 2] (above 3·10^12). To our knowledge these are the first published certifications above
  3·10^12 by a method independent of Turing's method. Arb's Turing tools can certify such windows too, so this is not a new fact
  about ζ in a strong sense.

Arb's rigorous N(T + 2) − N(T) agrees in every window: 8, 9 and 9.

## Layout

| file | role | trusted? |
|---|---|---|
| `atlas_v5.py` | driver: pieces, generator (fresh process, watchdog), replay | no (orchestration) |
| `replay_target5.py` | independent re-check: hull, structure, replay5 plain + hardened, exact tiling (pinned script, on offsets), claim (B), `exact_heights.json` | yes (assembly) |
| `lib/verify_zs5.py` | pinned verifier at exact heights (sha in `VERIFY_ZS5.sha256`) | **yes** |
| `lib/replay5.py` | rebuilds model and rows from definitions, calls verify_zs5; the no-parity verifier is built in memory | yes |
| `lib/model5.py` | all-open model, Nwin, far bound, row measurement at exact heights | yes |
| `lib/sech5.py` | "dirichlet" evaluator of E_a(x) | **yes (new)** |
| `lib/heights.py` | exact heights, grids v5 and v4 (compatibility) | yes |
| `lib/gen_target5.py`, `gen4.py`, `zs5.py`, `zfun5.py`, `verify.py`, `lp.py` | generator: LP, cutting planes, Z search | no |
| `lib/verify_zs.py` | pinned v4 verifier, kept only as the diff base | — |
| `compare_v4.py`, `run_acceptance5.sh` | step 1: v4 targets re-run and compared field by field as exact rationals | diagnostic |
| `validate_prime_side.py` | step 2: dirichlet vs zeta enclosures | diagnostic |
| `nzeros/arb_nzeros.py`, `crosscheck.py` | Arb `acb_dirichlet_zeta_nzeros` via ctypes; sign-change count vs Arb | diagnostic only |
| `run_big.sh` | steps 3–4 runner | — |

## How to run

```
P=/Users/kiosk/projects/atlas-rerun/.venv/bin/python; cd diagnostic/atlas_v5
nice -n 19 $P -u -B atlas_v5.py 10000000000000 10000000000000 10000000000002 --name big_1e13      # grid v5, evaluator dirichlet (defaults)
nice -n 19 $P -B replay_target5.py runs/w10000000000000/big_1e13 replay_check_independent           # exit 0 iff closed
python3 crosscheck.py runs/w10000000000000/big_1e13 43124192297102 43124192297111                   # vs Arb N(T), N(T+2)
nice -n 19 $P -u -B atlas_v5.py 9000 9000 9010 --name v1_9000 --grid v4 --evaluator zeta            # v4 compatibility mode
# Lean audit of v5 outputs (exact rationals T0 + u):
cd ../../formal && python3 export/export_certs.py --v5 v5_big audit/data_v5 <RUN_DIR ...> && .lake/build/bin/atlas_audit audit/data_v5/v5_big.txt
```

Usage: `atlas_v5.py T0 tlo thi --name N [--grid v5|v4] [--evaluator dirichlet|zeta] [--zs-step 0.005] [--zs-refine 1e-4]
[--pw 1] [--wm 2] [--gen-timeout s]`.
- T0 is a decimal integer; tlo and thi are absolute decimal strings.
- Output goes to `runs/w{T0}/{name}/` (`runs/w{T0:.2f}/` for grid v4), with the same files as v4. The certificates carry
  `format: atlas_v5`, `T0`, `grid` and `evaluator`, and every height is an offset.

## Limits

- Lemma 2 (claim A) and THEORY_V4 §10 (claim B) are still unreviewed. They are inherited from v4.
- The cost is dominated by the Z sign-change search (0.005 grid; 90–94 % of generator time). Measured:
  - 10^14 takes 18 min plus 2 min for the independent replay;
  - 10^15 and 10^16 were pre-registered but not run;
  - single-point Riemann–Siegel Z (6 s at 10^16) and one ζ'/ζ jet per row (31 s at 10^16) set the scale above that.
- The v4 negative controls were not ported. The v4.2 local-count finalizer was not ported; nothing needed it.
