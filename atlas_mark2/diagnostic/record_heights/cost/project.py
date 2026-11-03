"""Cost projection for one certified 2-unit window (COST.md).  Inputs: measured single-point costs (probe.log) and the measured
per-window evaluation counts of the v5 runs.  Model: window_seconds = (nZ_gen + nZ_rep) * cZ(T) + (n_jet_gen + n_jet_rep) * cJ(T)."""
import json, math
# measured Arb (pinned Zg / row jet), this Mac, seconds (cost/probe.log)
Z = {13: 0.25, 14: 0.76, 15: 2.42, 16: 8.0}
J = {13: 1.19, 14: 3.67, 15: 11.48, 16: 37.6}
RSS = {13: 0.074, 14: 0.17, 15: 0.48, 16: 1.30}   # GB, single Z


def fit(d):
    xs = list(d); ys = [math.log10(d[x]) for x in xs]; n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); return b, my - b * mx


bz, az = fit(Z); bj, aj = fit(J); br, ar = fit(RSS)
print(f"fit: Z ~ T^{bz:.3f}, jet ~ T^{bj:.3f}, RSS ~ T^{br:.3f}")
cZ = lambda e: 10 ** (az + bz * e); cJ = lambda e: 10 ** (aj + bj * e); rss = lambda e: 10 ** (ar + br * e)
# evaluation counts per window: 'v5' = as run (grid search; counts from the 1e14/1e15 runs), 'gram' = Gram-guided search estimate
dens = lambda e: math.log(10 ** e / (2 * math.pi)) / (2 * math.pi)
def counts(e, mode):
    zeros_span = 6 * dens(e)                      # hull +- 2 units
    if mode == 'v5': nz = 1375                    # measured at 1e14 (step 0.005); larger steps are pre-registered above 1e14
    else: nz = zeros_span * (2 + 8)               # ~2 bracketing evals + ~8 Illinois/secant evals to width 1e-4 per zero
    return nz + 2 * 2 * 25, 36                    # + replay endpoints (~100 distinct Z), 18 jets generator + 18 replay
rows = []
for e in (15, 16, 17, 18, 20, 22, 23):
    for mode in ('v5', 'gram'):
        nz, nj = counts(e, mode)
        arb = nz * cZ(e) + nj * cJ(e)
        rows.append(dict(exp=e, mode=mode, zeros_per_unit=round(dens(e), 2), nZ=round(nz), cZ_arb_s=round(cZ(e), 1),
                         arb_window_h=round(arb / 3600, 2), arb_rss_gb=round(rss(e), 2)))
print(json.dumps(rows, indent=0))
