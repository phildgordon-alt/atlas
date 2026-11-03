"""Independent rigorous verifier for zsign certificates (THEORY_ZSIGN.md, Theorem).
atlas_v5 verify_zs5.py = the pinned verify_zs.py (sha ed5bc621...) with exactly the changes of THEORY_V5.md section 3: heights are
offsets relative to an integer T0 (new keyword check(..., T0=0)); Zg(t) -> Zg(T0, t) at the exact height T0 + t, precision
160 + bitlen(T0), memoised.  Every other line (structure, _ball, _parse, _phi, K, zsub, bisection, inequalities) is unchanged.  Own kernel enclosures and bisection
(does not import verify.py / lslab*).  Pure function of its inputs:
  ids, Elo, Ehi, Fa (row data), Nwin, vars (model boxes), window, region, y (2J+1), w (m), intervals (m pairs).
Checks: (0) structural: w_i >= 0 finite, t1 < t2, wlo <= t1, t2 <= whi;  (Z) strict opposite signs of Z at t1, t2
(gamma-form Z, 160 bits);  (R) Phi - f*SUM_{i: box meets d=0 and [t1_i,t2_i]} w_i >= 0 on every var box;
(C) Phi(.,.,2) - K - 2yc + sum w > 0 on the region box."""
import math
from fractions import Fraction
from flint import arb,acb,ctx
import zfast_provider as _zfp
def _hx(T0,t):
    """exact Arb ball of T0 + t (T0 int, t binary64); asserts radius 0 (THEORY_V5 section 1)"""
    f=Fraction(T0)+Fraction(t);p,q=f.numerator,f.denominator;old=ctx.prec;ctx.prec=max(old,abs(p).bit_length()+q.bit_length()+8)
    try:v=arb(p)/arb(q)
    finally:ctx.prec=old
    assert v.rad()==0
    return v
_ZG={}
def Zg(T0,t):
    """v5z: Z(T0+t) as a rigorous ball from zfast (lib/zfast_provider.py, THEORY_V5Z section 1); memoised."""
    key=(T0,t)
    if key in _ZG:return _ZG[key]
    v=_zfp.Zball(T0,t)
    _ZG[key]=v
    return v
def _ball(lo,hi):a,b=arb(lo),arb(hi);return (a+b)/2+arb(0,((b-a)/2).upper())
def _parse(ids):return [(k.startswith('L'),float(k.split('|')[0].lstrip('L')),float(k.split('|')[1])) for k in ids]
def _phi(terms,yc,x0,x1,d0,d1,f):
    x=_ball(x0,x1);d=_ball(d0,d1);s=arb(yc)
    for c,isL,a,t in terms:
        r=x-arb(t);A=arb(a)
        if isL:em=A-d;ep=A+d;s+=c*(em/(em*em+r*r)+ep/(ep*ep+r*r))/2
        else:cc=(A*d).cos();sh=(A*r).sinh();s+=c*(A*r).cosh()*cc/(sh*sh+cc*cc)
    return arb(f)*s
def check(ids,Elo,Ehi,Fa,Nwin,vars_,window,region,y,w,intervals,maxdepth=48,budget=8_000_000,check_z=True,sub='sum',T0=0):
    assert isinstance(T0,int) and not isinstance(T0,bool) and T0>=0
    J=len(ids);P=_parse(ids);y=[float(v) for v in y];w=[float(v) for v in w];wlo,whi=window
    if len(y)!=2*J+1 or len(w)!=len(intervals):return dict(status='BAD_SHAPE')
    if any(not(math.isfinite(v)) or v<0 for v in y):return dict(status='BAD_Y')
    if any(not math.isfinite(v) or v<0 for v in w):return dict(status='BAD_W')
    for t1,t2 in intervals:
        if not(wlo<=t1<t2<=whi):return dict(status='BAD_INTERVAL',interval=[t1,t2])
    if check_z:
        for t1,t2 in intervals:
            z1,z2=Zg(T0,t1),Zg(T0,t2)
            if not((z1.lower()>0 and z2.upper()<0) or (z1.upper()<0 and z2.lower()>0)):return dict(status='NO_SIGN_CHANGE',interval=[t1,t2],z=[z1.str(5),z2.str(5)])
    terms=[(arb(y[j])-arb(y[J+j]),*P[j]) for j in range(J) if y[j]!=y[J+j]];yc=y[2*J]
    K=arb(0)
    for j in range(J):
        isL=P[j][0];K+=arb(y[j])*(arb(Ehi[j])+(arb(Fa[j]) if isL else 0))-arb(y[J+j])*(arb(Elo[j])-arb(Fa[j]))
    K+=arb(yc)*(arb(Nwin)-2);W=arb(0)
    for v in w:W+=arb(v)
    def zsub(b0,b1,e0):
        if e0>0:return arb(0)
        hit=[arb(v) for (t1,t2),v in zip(intervals,w) if b0<=t2 and b1>=t1]
        if not hit:return arb(0)
        if sub=='max':return max(hit,key=lambda q:float(q.mid()))   # UNSOUND variant, negative control only
        s=arb(0)
        for h in hit:s+=h
        return s
    roots=[('rem',lo,hi,0.,0.,1.) if k=='on' else ('rem',lo,hi,0.,cap,2.) for k,lo,hi,_,cap in vars_]+[('cand',*region,2.)]
    n=0;minc=None
    for kind,x0,x1,d0,d1,f in roots:
        st=[(x0,x1,d0,d1,0)]
        while st:
            b0,b1,e0,e1,dep=st.pop();n+=1
            if n>budget:return dict(status='BUDGET',boxes=n)
            v=_phi(terms,yc,b0,b1,e0,e1,f)
            if kind=='cand':
                v=v-K-2*arb(yc)+W
                if v.lower()>0:minc=float(v.lower()) if minc is None else min(minc,float(v.lower()));continue
            else:
                v=v-arb(f)*zsub(b0,b1,e0)
                if v.lower()>=0:continue
            if dep>=maxdepth:return dict(status='FAIL',kind=kind,box=[b0,b1,e0,e1],value=v.str(6),boxes=n)
            if (b1-b0)>=4*(e1-e0) or e0==e1:m=(b0+b1)/2;st+=[(b0,m,e0,e1,dep+1),(m,b1,e0,e1,dep+1)]
            else:m=(e0+e1)/2;st+=[(b0,b1,e0,m,dep+1),(b0,b1,m,e1,dep+1)]
    return dict(status='CERTIFIED',boxes=n,min_candidate_lower=minc,K=float(K.mid()),sum_w=float(W.mid()))
