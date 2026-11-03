"""Shared helpers for the independent zfast review (2026-10-19).  Never overwrites: every output is opened with mode 'x'."""
import json, math, subprocess, os, random
from fractions import Fraction
from flint import arb, ctx

R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review'
WD = '/Users/kiosk/atlas_mark2/diagnostic/general_eval/calegari2/wd_fp.sh'
PROD = R + '/bin/rv_drv.prod'
REF = R + '/bin/rv_ref2'


def xopen(path):
    return open(path, 'x')


class Drv:
    """persistent rv_drv process (one zfast build)"""
    def __init__(self, exe=PROD):
        self.p = subprocess.Popen(['nice', '-n', '19', exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def q(self, line):
        self.p.stdin.write(line + '\n'); self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())

    def Z(self, T0, u, J=12, bmax=16384, kcorr=0, l2=-72.0, th=1):
        return self.q(f'Z {T0} {float(u).hex()} {J} {bmax} {kcorr} {l2} {th}')

    def sess(self, T0, u0, kind=0, a=0.0, H=3.0, Delta=0.2, K=16, J=12, th=1):
        return self.q(f'SN {T0} {float(u0).hex()} {H} {kind} {a} {Delta} {K} {J} {th}')['id']

    def SZ(self, sid, u):
        return self.q(f'SZ {sid} {float(u).hex()}')

    def SR(self, sid, u):
        return self.q(f'SR {sid} {float(u).hex()}')

    def ROW(self, T0, u, a, J=12, th=1):
        return self.q(f'ROW {T0} {float(u).hex()} {a} {J} {th}')

    def PH(self, T0, u, n0, B, J):
        return self.q(f'PH {T0} {float(u).hex()} {n0} {B} {J}')

    def close(self):
        self.p.stdin.close(); self.p.wait()


def ball(s, prec=600):
    old = ctx.prec; ctx.prec = prec
    try: return arb(s)
    finally: ctx.prec = old


def compare(zs, refs, prec=600):
    """zs, refs: ball strings.  Returns dict: overlap (necessary for correctness), diff = |mid_z - mid_ref|, rad_z, rad_ref,
    contained = ref ball inside z ball."""
    old = ctx.prec; ctx.prec = prec
    try:
        z = arb(zs); r = arb(refs)
        d = abs(z.mid() - r.mid())
        rz = z.rad(); rr = r.rad()
        overlap = bool(d <= rz + rr)
        contained = bool(d + rr <= rz)
        return dict(overlap=overlap, contained=contained, diff=float(d), rad_z=float(rz), rad_ref=float(rr),
                    ratio=float(d / rz) if rz > 0 else float('inf'))
    finally:
        ctx.prec = old


def exact_u(T0, t_arb):
    """nearest binary64 u with T0 + u close to the real t_arb (high precision)"""
    old = ctx.prec; ctx.prec = 400
    try:
        x = t_arb - arb(T0)
        return float(x.mid())
    finally:
        ctx.prec = old


def centre(u):
    return 6.0 * round(u / 6.0)
