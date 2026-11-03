"""atlas_v5 all-open case model and row data at exact heights (THEORY_V5.md section 4; THEORY_V4.md sections 1-2).
Used by the generator driver AND by the replay.  Coordinates: every height argument here is a WORK coordinate w with absolute height
base + w (base = 0 for absolute binary64 numbers, base = T0 for offsets).  The replay always calls with base = T0 (offsets).

Model for window bins k0..k1 of a grid (heights.Grid):  vars per bin ['on', lo, hi, 0, 0], ['off', lo, hi, 0, 0.5];
  Nwin = up(count_upper5(wlo, whi))  (Trudgian S(T), Arb theta at the exact heights; = integer_mechanism.count_upper's expression)
Rows: sech 'a|w' (0 < a < pi): (Elo, Ehi) from evaluator 'zeta' (v4 E_comp, unchanged call) or 'dirichlet' (sech5.E5), outward
  rounded exactly as v4 (str(30) round trip, im.dn / im.up); F = far_bound5 (= im.far_bound's formula; shell distance in Arb).
No zero data is used anywhere."""
import sys, math
from pathlib import Path
DIAG = Path('/Users/kiosk/atlas_mark2/diagnostic')
sys.path.insert(0, str(DIAG))
import integer_mechanism as im                      # noqa: E402  (sets ctx.prec = 128, as in v4)
from flint import arb, acb, ctx                      # noqa: E402
from heights import hx, Grid, H                      # noqa: E402
CAP = 0.5


def model(G, base, k0, k1, sech_rows=(), work=True):
    """all-open model on bins k0..k1-1 of grid G.  work=True: edges in G's work coordinates (generator); work=False: offsets (replay).
    base must match (G.base for work, G.T0 for offsets).  sech_rows = [(id, Elo, Ehi)] (F computed here)."""
    edge = G.w_edge if work else G.edge
    assert base == (G.base if work else G.T0)
    wlo, whi = edge(k0), edge(k1)
    vars_ = []
    for k in range(k0, k1):
        lo, hi = edge(k), edge(k + 1)
        vars_.append(['on', lo, hi, 0.0, 0.0]); vars_.append(['off', lo, hi, 0.0, CAP])
    Nwin = im.up(count_upper5(base, wlo, whi).upper())
    ids, Elo, Ehi, F = [], [], [], []
    for key, lo, hi in sech_rows:
        a, t = float(key.split('|')[0]), float(key.split('|')[1])
        ids.append(key); Elo.append(lo); Ehi.append(hi); F.append(far_bound5(a, base, t, wlo, whi))
    return dict(window=[wlo, whi], vars=vars_, Nwin=Nwin, ids=ids, Elo=Elo, Ehi=Ehi, F=F)


# ---- counts (integer_mechanism.theta_arb / Smax / count_upper / far_bound at exact heights) ----
def theta5(base, w):
    T = hx(base, w)
    return acb(arb(1) / 4, T / 2).lgamma().imag - T / 2 * arb.pi().log()


_CU = {}


NWIN_PREC = 256          # v5z4: count_upper5 runs at NWIN_PREC + bitlen(base) bits, independent of the ambient ctx.prec


def count_upper5(base, x, y):
    """v5z4: same real expression as v5; evaluated at the fixed precision NWIN_PREC + bitlen(base), so the returned upper bound
    (an exact Arb number) is a deterministic function of (base, x, y).  (v5/v5z/v5z2/v5z3 used the ambient ctx.prec, which the
    sech engine raises from 128 to 256 on first use: harmless below 1e23, a replay mismatch at 1e23; THEORY_V5Z4.md.)"""
    k = (base, x, y)
    if k not in _CU:
        old = ctx.prec; ctx.prec = NWIN_PREC + int(base).bit_length()
        try: v = arb(((theta5(base, y) - theta5(base, x)) / arb.pi() + 2 * im.Smax(hx(base, y))).upper())
        finally: ctx.prec = old
        _CU[k] = v
    return _CU[k]


def far_bound5(a, base, t, wlo, whi):
    tot = arb(0); A = arb(a)
    for side in (+1, -1):
        edge = whi if side > 0 else wlo
        for k in range(0, 60):
            x0 = edge + side * k; x1 = edge + side * (k + 1); lo_, hi_ = min(x0, x1), max(x0, x1)
            r = abs(arb(x0) - arb(t))                         # v5: exact distance in Arb (THEORY_V5 section 4); v4 used float abs(x0 - t)
            assert r.rad() == 0
            tot += count_upper5(base, lo_, hi_) * ((A * r).cosh() / (A * r).sinh() ** 2)
    return im.up(tot.upper()) + 1e-20


# ---- row measurement ----
_ENG = {}


def measure(key, base, evaluator):
    """(Elo, Ehi) for sech id 'a|w' at the absolute height base + w.  evaluator 'zeta': v4 E_comp (unchanged, called as model4.measure);
    'dirichlet': sech5.E5.  Same outward rounding as v4 (str(30) round trip -> im.dn / im.up)."""
    import certify_sech_interferometer as eng
    a, t = float(key.split('|')[0]), float(key.split('|')[1])
    assert 0 < a < math.pi and evaluator in ('zeta', 'dirichlet')
    if _ENG.get('a') != a:
        band = (0.0, 10.0)                                  # band is not used by E_comp / E5 (only by the v3 tiler)
        eng.configure(a=a, x=1e7, band=band, evaluator='zeta', target='1e-6')
        eng._init((a, 1e7, band, str(eng.TABLE), eng.BB, 'zeta', '1e-6')); _ENG['a'] = a
    old = ctx.prec; ctx.prec = 256
    try:
        x = hx(base, t)
        if evaluator == 'zeta': E = eng.E_comp(x)
        else:
            import sech5
            E = sech5.E5(a, x, base)
    finally: ctx.prec = old
    E = arb(E.str(30))
    return im.dn(E.lower()), im.up(E.upper())
