"""Independent rigorous bound for zfast's cos/sin kernel (cs_core in zfast.c v10b/v12a), by subinterval interval analysis.
Model (IEEE binary64, RN, u = 2^-53, no underflow): yhat = fl(fl(r) * KTURN), zhat = fl(yhat^2); Horner by fma; c = fma(p1, zhat, 1);
t = fl(yhat*zhat); s = fma(t, s2, yhat).  True target: cos/sin(y*), y* = 2 pi r / 2^64.
Per subinterval Y = [a,b] of yhat >= 0 (both kernels are odd/even exactly under r -> -r, since RN is sign-symmetric):
  E = (Horner rounding, forward, running bound) + (binary64 coeff vs exact Taylor coeff) + (T(zhat) - T(yhat^2)) + Taylor remainder
      + (cos/sin(yhat) - cos/sin(y*)).
Coefficients are parsed from the C source (hex literals) so the check is tied to the production file."""
import re, sys, json, time
from flint import arb, arf, ctx
ctx.prec = 200
SRC = sys.argv[1] if len(sys.argv) > 1 else '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/src_v12a/zfast.c'
NSUB = int(sys.argv[2]) if len(sys.argv) > 2 else 1 << 14
src = open(SRC).read()
def hexlist(name):
    m = re.search(name + r'\[9\] = \{([^}]*)\}', src); return [float.fromhex(x.strip()) for x in m.group(1).split(',')]
CC, SC = hexlist('CC'), hexlist('SC')
KT = float.fromhex(re.search(r'KTURN = (0x[0-9a-fp.+-]+);', src).group(1))
u = arb(2) ** -53
fact = [arb(1)]
for i in range(1, 40): fact.append(fact[-1] * i)
cc_ex = [(-1) ** j / fact[2 * j] for j in range(9)]
sc_ex = [(-1) ** j / fact[2 * j + 1] for j in range(9)]
pi = arb.pi()
# y* = 2 pi r / 2^64 ; yhat = y* (1+d1)(1+d2)(1+d3) where KT = (2pi/2^64)(1+d2) exactly: compute d2 bound from the literal
d2 = abs(arb(KT) / (2 * pi / arb(2) ** 64) - 1)
assert d2 < u
rel = (1 + u) * (1 + u) * (1 + d2) - 1          # |yhat/y* - 1| <= rel  (fl(r): u, product: u)
YMAX = arb(2) ** 61 * arb(KT)                     # |yhat| <= fl(2^61 KT) = 2^61 KT exactly (power of 2 scaling)

def U(x): return arb(x.abs_upper())
def iv(lo, hi): return arb(lo).union(arb(hi))

def horner_err(coef, Z):
    """computed p_hat = Horner(coef[8..1]) at zhat in Z: returns (range of p_hat, forward error vs exact Horner with same coef, same zhat)"""
    P = arb(coef[8]); e = arb(0)
    for j in range(7, 0, -1):
        q = P * Z + coef[j]
        e = U(e) * U(Z) + u * U(q)
        P = q * iv(1 - u, 1 + u)
    return P, e

def bound(a, b):
    Y = iv(a, b)
    Z = iv(arb(a) ** 2 * (1 - u), arb(b) ** 2 * (1 + u))       # zhat
    # ---- cos
    P1, e1 = horner_err(CC, Z)
    q = P1 * Z + 1
    ec = U(e1) * U(Z) + u * U(q)                                 # computed c vs Hb(zhat) := 1 + zhat*Horner_bin(zhat)
    coefc = sum((abs(arb(CC[j]) - cc_ex[j]) * U(Z) ** j for j in range(1, 9)), arb(0))   # Hb vs T (exact Taylor) at zhat
    dT = sum((j * abs(cc_ex[j]) * U(Z) ** (j - 1) for j in range(1, 9)), arb(0))       # |T'| on [0, max Z]
    zc = dT * u * arb(b) ** 2                                    # T(zhat) - T(yhat^2)
    rem = arb(b) ** 18 / fact[18]
    ystar_up = arb(b) / (1 - rel)
    da = ystar_up * rel                                          # |yhat - y*|
    arg = U(ystar_up) * da                                       # |cos yhat - cos y*| <= max|sin| * da <= y* da
    Ec = ec + coefc + zc + rem + arg
    # ---- sin
    P1s, e1s = horner_err(SC, Z)                                 # s2_hat vs Qb(zhat) = SC1 + SC2 z + ...
    T_ = Y * Z * iv(1 - u, 1 + u)                                # t_hat
    qs = T_ * P1s + Y
    es = u * U(qs) + U(Y) * U(Z) * (U(e1s) + u * U(P1s))         # computed s vs yhat + yhat zhat Qb(zhat)
    coefs = U(Y) * U(Z) * sum((abs(arb(SC[j]) - sc_ex[j]) * U(Z) ** (j - 1) for j in range(1, 9)), arb(0))
    dTs = sum(((j) * abs(sc_ex[j]) * U(Z) ** (j - 1) for j in range(1, 9)), arb(0))  # d/dz [z Q(z)] = sum j sc_j z^{j-1}
    zs = U(Y) * dTs * u * arb(b) ** 2
    rems = arb(b) ** 19 / fact[19]
    args = da                                                    # |sin yhat - sin y*| <= da
    Es = es + coefs + zs + rems + args
    return Ec, Es, dict(ec=ec, coefc=coefc, zc=zc, rem=rem, arg=arg, es=es)

t0 = time.time()
ym = float(YMAX.mid()) * (1 + 1e-15)
best = [arb(0), arb(0)]; worst = [None, None]
edges = [ym * i / NSUB for i in range(NSUB + 1)]
for i in range(NSUB):
    Ec, Es, parts = bound(edges[i], edges[i + 1])
    if U(Ec) > best[0].upper() if False else float(U(Ec).upper()) > float(best[0].upper()): best[0] = U(Ec); worst[0] = (i, {k: float(v.upper()) for k, v in parts.items()})
    if float(U(Es).upper()) > float(best[1].upper()): best[1] = U(Es); worst[1] = i
res = dict(src=SRC, nsub=NSUB, E_cos=float(best[0].upper()), E_sin=float(best[1].upper()), worst_cos=worst[0], worst_sin_piece=worst[1],
           E_cos_over_u=float((best[0] / u).upper()), claimed_ZF_EC=float(re.search(r'#define ZF_EC ([0-9.e+-]+)', src).group(1)),
           sec=time.time() - t0, d2_over_u=float((d2 / u).upper()))
res['OK'] = res['E_cos'] <= res['claimed_ZF_EC'] and res['E_sin'] <= res['claimed_ZF_EC']
print(json.dumps(res, indent=1))
