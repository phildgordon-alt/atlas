# Correction to record_heights/COST.md §1 and §4: there is no memory wall in Arb (2026-10-19)

This is an appended note. COST.md itself is not edited.

**What COST.md says:**
- §1: Arb's memory per Z grows ∝ T^0.42–0.45, about 3.5 GB at 10¹⁷, "over this machine's 2.5 GB cap".
- §4: "with stock Arb and a 2.5 GB cap, nothing rigorous runs above about 10¹⁷ on this machine."

**Correction.** That memory growth belongs to Arb's *default* main-sum path, `acb_dirichlet_powsum_sieved`. Arb's
`acb_dirichlet_zeta_rs_r` uses it whenever its table fits in 4 GB. FLINT 3.6.0 also exports `acb_dirichlet_powsum_smooth`, Arb's own
fallback, as public API, and that path is memory-lean.

Measured (zfast/runs/m2, `bin/arbref_smooth.dev4`/`.dev8`): Z(T0 + u) = 2 Re(e^{iθ}(powsum_smooth(1/2 + it, N) + RS correction)),
one core, nice 19, machine shared.

| T0 | N | time | peak RSS | check |
|---|---|---|---|---|
| 10¹³ | 1.26e6 | 0.36 s | 3.8 MB | equals stock Arb `Zg` to all 30 printed digits |
| 10¹⁶ | 3.99e7 | 11.1 s | 4.5 MB | stock Arb: 8.0 s, 1.30 GB |
| 10¹⁸ | 3.99e8 | 115 s | 4.0 MB | agrees with zfast (diff 2.8e-16) |
| 10²⁰ | 3.99e9 | 1245 s | 4.4 MB | agrees with zfast (diff 9.0e-16) |

**Consequences:**
- A rigorous, pure-Arb Z works on this Mac at any height, at about 1.4× the cost of the sieved path. That is about 2 min per Z at
  10¹⁸ and 21 min at 10²⁰.
- The "blocked by memory at 10¹⁷" rows of COST.md §3 and §4 and of RESULTS.md §4 should read "blocked by time". The ladder's
  conclusion is unchanged: practical windows above 10¹⁷ still need zfast (15–26× faster than Arb, 4 MB) and multi-evaluation.
- The Arb Platt/Turing routine (`platt_local_hardy_z_zeros`) killed at 2.5 GB near 1.5·10¹⁷ (COST.md §4) is a different code path.
  Its memory is not addressed by this note.
- Caveat: the RS correction in `arbref_smooth` is zfast's line-for-line copy of Arb's correction loop (`zf_rs_corr`), validated
  against stock Arb ≤ 10¹⁵. The main sum is Arb's own.
