"""Rigorous error bound for zfast's cos2pi/sin2pi kernel (THEORY_ZFAST.md section 5).  Arb (python-flint), no floating trust.
Kernel: input v (uint64, x = v/2^64 turns).  q = (v + 2^61) >> 62 (mod 4), r = (int64)(v - q*2^62) in [-2^61, 2^61).
y = fl(fl((double)r) * K), K = fl(2*pi/2^64);  z = fl(y*y);
C(z) = 1 + z*(c1 + z*(c2 + ... + z*c8))   (fma Horner, coefficients = binary64 roundings of (-1)^j/(2j)!)
S(y) = y + y*z*(s1 + z*(s2 + ... + z*s8)) (fma Horner; s_j = binary64 of (-1)^j/(2j+1)!)
Output: E_c with |cos_comp - cos(2*pi*x)| <= E_c and |sin_comp - sin(2*pi*x)| <= E_c for every uint64 v."""
from flint import arb, ctx, fmpq
import math, json, sys
ctx.prec = 200
u = arb(2) ** -53
DEG = 8
cc = [float(fmpq((-1) ** j, math.factorial(2 * j))) for j in range(DEG + 1)]        # cc[0] = 1
sc = [float(fmpq((-1) ** j, math.factorial(2 * j + 1))) for j in range(DEG + 1)]    # sc[0] = 1
K = float(arb.pi() * 2 / arb(2) ** 64)
# |r| <= 2^61 ; (double) r : rel err <= u ; K rel err <= u ; product rel err <= u
Kerr = abs(arb(K) - arb.pi() * 2 / arb(2) ** 64) / (arb.pi() * 2 / arb(2) ** 64)
assert Kerr < u
Ystar = arb.pi() / 4                       # exact |y*| max  (y* = 2 pi r / 2^64)
dely = (1 + u) ** 3 - 1                   # |y - y*| <= dely |y*|
Y = Ystar * (1 + dely)                    # bound on computed |y|
Z = Y * Y * (1 + u)                       # bound on computed z
def horner_bound(coef, Zb):
    """computed p_hat = Horner(coef[DEG..1]) at computed z (fma each step).  returns (P, err): |p_hat - p(z)| <= err (z = the computed z,
    p exact polynomial with the binary64 coefficients), |p_hat| <= P"""
    P = abs(arb(coef[DEG])); err = arb(0)
    for j in range(DEG - 1, 0, -1):
        exact_mag = P * Zb + abs(arb(coef[j]))        # bound on |p_{j+1}^ * z + c_j|
        err = Zb * err + u * (exact_mag)             # propagated + one rounding of the fma result
        P = exact_mag * (1 + u)
    return P, err
# cos: Q(z) = c1 + z(c2 + ...) ; cos_comp = fma(Q_hat, z, 1)
Pq, eq = horner_bound(cc, Z)
# result fl(Q_hat*z + 1): |Q_hat*z + 1| <= 1 ; rounding <= u * 1 (result magnitude <= 1 + small)
cos_eval = Z * eq + u * (1 + Pq * Z)
# exact polynomial at computed z vs at y^2 exactly: |C(z) - C(y^2)| <= max|C'| * |z - y^2|, |C'| <= sum j|c_j| Z^(j-1)
Cp = sum(j * abs(arb(cc[j])) * Z ** (j - 1) for j in range(1, DEG + 1))
cos_z = Cp * (Y * Y * u)
# polynomial (rounded coeffs) vs cos(y): Taylor remainder + coefficient rounding
cos_tay = Y ** (2 * DEG + 2) / math.factorial(2 * DEG + 2) + sum(abs(arb(cc[j]) - arb(fmpq((-1) ** j, math.factorial(2 * j)))) * Y ** (2 * j) for j in range(DEG + 1))
# argument: |cos(y) - cos(y*)| <= |y - y*| <= dely * Ystar
arg = dely * Ystar
E_cos = cos_eval + cos_z + cos_tay + arg
# sin: Q(z) = s1 + z(s2 + ...) ; t = fl(y*z) ; sin_comp = fma(t, Q_hat, y)   [ = y + y z Q ]
Ps, es = horner_bound(sc, Z)
tbound = Y * Z * (1 + u)
sin_eval = tbound * es + u * Y * Z * Ps + u * (Y + tbound * Ps * (1 + u))   # error of Q_hat times |t|, rounding of t, final rounding
Sp = 1 + sum((2 * j + 1) * abs(arb(sc[j])) * Z ** j for j in range(1, DEG + 1))
sin_z = Y * sum(j * abs(arb(sc[j])) * Z ** (j - 1) for j in range(1, DEG + 1)) * (Y * Y * u)
sin_tay = Y ** (2 * DEG + 3) / math.factorial(2 * DEG + 3) + sum(abs(arb(sc[j]) - arb(fmpq((-1) ** j, math.factorial(2 * j + 1)))) * Y ** (2 * j + 1) for j in range(DEG + 1))
E_sin = sin_eval + sin_z + sin_tay + arg
E = max(E_cos.upper(), E_sin.upper())
out = dict(cos_coeffs=[c.hex() for c in cc], sin_coeffs=[s.hex() for s in sc], K=K.hex(),
           E_cos=E_cos.upper().str(5, radius=False), E_sin=E_sin.upper().str(5, radius=False),
           parts=dict(cos_eval=cos_eval.upper().str(3, radius=False), cos_z=cos_z.upper().str(3, radius=False), cos_taylor=cos_tay.upper().str(3, radius=False),
                      arg=arg.upper().str(3, radius=False), sin_eval=sin_eval.upper().str(3, radius=False), sin_taylor=sin_tay.upper().str(3, radius=False)),
           E_c_over_u=(E / u).upper().str(5, radius=False))
print(json.dumps(out, indent=1))
