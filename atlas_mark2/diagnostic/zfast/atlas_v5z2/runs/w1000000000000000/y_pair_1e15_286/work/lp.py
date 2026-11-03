"""Sampled feasibility LP (not a certificate): survivor edge models from feedback_closure round_001 (sech long336+3.0/3.1 rows,
domain feedback), optionally plus near-line Lorentzian rows M_eps(t)=Re xi'/xi(1/2+eps+it) = sum_rho Re 1/(s-rho).
Orbit-symmetric kernel uL(r,d)=1/2[(e-d)/((e-d)^2+r^2)+(e+d)/((e+d)^2+r^2)], f=1 on-line, f=2 off-line orbit.
Lorentzian far allowance: conservative 0.5/r^2 per zero beyond the window, density bound 2/unit."""
import json,sys,numpy as np
from scipy.optimize import linprog
from flint import arb,acb,acb_series,ctx
ctx.prec=128
R='/Users/kiosk/atlas/workbench/math_ablation_20260928/'
def Phi(e,t):
    s=acb(arb(0.5)+arb(e),arb(t));z=acb_series([s,1],prec=2).zeta().coeffs()
    v=(1/s+1/(s-1)-arb.pi().log()/2+(s/2).digamma()/2+z[1]/z[0]).real;return float(v.lower()),float(v.upper())
def usech(a,r,d):
    ar=np.clip(a*r,-300,300);c=np.cos(a*d);s=np.sinh(ar);return np.cosh(ar)*c/(s*s+c*c)
def uL(e,r,d):return 0.5*((e-d)/((e-d)**2+r*r)+(e+d)/((e+d)**2+r*r))
GAP=float(sys.argv[1]) if len(sys.argv)>1 else 0.003
def run(name,use_L,eps_list=(0.002,0.005,0.01,0.02,0.05),step=0.005):
    c=json.load(open(R+f'feedback_closure_1000200_v1/round_001/cases/{name}.json'))['case'];m=c['model']
    ids=list(m['ids']);Elo=list(m['Elo']);Ehi=list(m['Ehi']);Fa=list(m['F']);kind=['S']*len(ids)
    x0,x1,d0,d1=c['region'];xc=(x0+x1)/2
    if use_L:
        for e in eps_list:
            openc=[(lo_,hi_) for k_,lo_,hi_,_,cap_ in m['vars'] if k_=='off' and cap_>0.0011]
            for t in np.arange(xc-0.15,xc+0.15+1e-9,step):
                if any(lo_-GAP<=t<=hi_+GAP for lo_,hi_ in openc):continue
                lo,hi=Phi(e,t);ids.append(f'L{e}|{float(t)!r}');Elo.append(lo);Ehi.append(hi);Fa.append(0.5*2*2/3.0+1e-3);kind.append('L')
    J=len(ids);A=np.array([float(k.split('|')[0].lstrip('L')) for k in ids]);T=np.array([float(k.split('|')[1]) for k in ids]);isL=np.array([k=='L' for k in kind])
    def U(x,d):
        out=np.where(isL,uL(A,x-T,d),usech(A,x-T,d))
        return out
    rem=[]
    for k,lo,hi,_,cap in m['vars']:
        for x in np.arange(lo,hi,0.002 if hi-lo>0.05 else 0.0005):
            if k=='on':rem.append((x,0.,1.))
            else:
                for d in [v for v in sorted(set(list(np.geomspace(1e-5,0.5,60)))) if v<=cap]+[cap]:rem.append((x,d,2.))
    cand=[(x,d) for x in np.linspace(x0,x1,11) for d in np.geomspace(max(d0,1e-3),d1,25)]
    n=2*J+2   # y_up, y_low, y_count, m
    Arows=[];b=[]
    for x,d,f in rem:
        u=f*U(x,d);row=np.zeros(n);row[:J]=-u;row[J:2*J]=u;row[2*J]=-f;Arows.append(row);b.append(0.)
    Kup=np.array(Ehi);Klow=-(np.array(Elo)-np.array(Fa))
    for x,d in cand:
        u=2*U(x,d);row=np.zeros(n);row[:J]=-(u-Kup);row[J:2*J]=-(-u-Klow);row[2*J]=-(2-(m['Nwin']-2)-2);row[-1]=1;Arows.append(row);b.append(0.)
    Aeq=np.zeros((1,n));Aeq[0,:2*J+1]=1
    res=linprog(np.r_[np.zeros(2*J+1),-1],A_ub=np.array(Arows),b_ub=b,A_eq=Aeq,b_eq=[1],bounds=[(0,None)]*(2*J+1)+[(None,None)],method='highs')
    y=res.x;wL=(y[:J][isL].sum()+y[J:2*J][isL].sum()) if res.success else None
    return dict(case=name,lorentz=use_L,rows=J,remainder_samples=len(rem),status=res.status,sampled_margin=(-res.fun if res.success else None),lorentz_weight=wL)
for name in ('g00_left','g00_right','g01_left','g01_right'):
    for L in (False,True):print(json.dumps(run(name,L)),flush=True)
