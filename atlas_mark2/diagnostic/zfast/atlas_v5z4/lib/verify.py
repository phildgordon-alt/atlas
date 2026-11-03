"""Rigorous continuous check of the sampled Lorentzian+sech witness, with exchange (cutting-plane) rounds.
Remainder: every var box (on: [lo,hi]x{0}, f=1; off: [lo,hi]x[0,cap], f=2) must have Phi >= 0.
Candidate: region box must have f*Phi - K - 2*y_count > 0 (f=2).
Enclosures: Arb balls over boxes, closed-form kernels only (no zeta on boxes); recursive bisection.
Lorentzian far allowance F is a provisional constant (rigorous count-based bound still to be derived) - flagged in output."""
import json,sys,time,numpy as np
from farL import far_L
from flint import arb,acb,ctx
ctx.prec=128
exec(open('lp.py').read().split("for name in ('g00_left'")[0].replace("def run(","def run_unused("))
def build(name,eps_list=(0.002,0.005,0.01,0.02,0.05),step=0.005):
    c=json.load(open(R+f'feedback_closure_1000200_v1/round_001/cases/{name}.json'))['case'];m=c['model']
    ids=list(m['ids']);Elo=list(m['Elo']);Ehi=list(m['Ehi']);Fa=list(m['F']);x0,x1,d0,d1=c['region'];xc=(x0+x1)/2
    openc=[(lo,hi) for k,lo,hi,_,cap in m['vars'] if k=='off' and cap>0]
    for e in eps_list:
        for t in np.arange(xc-0.15,xc+0.15+1e-9,step):
            if any(lo-GAP<=t<=hi+GAP for lo,hi in openc):continue
            lo_,hi_=Phi(e,t);ids.append(f'L{e}|{float(t)!r}');Elo.append(lo_);Ehi.append(hi_);Fa.append(far_L(e,float(t),m['window'][0],m['window'][1],m['Nwin']))
    return c,m,ids,np.array(Elo),np.array(Ehi),np.array(Fa)
def kern_np(ids):
    A=np.array([float(k.split('|')[0].lstrip('L')) for k in ids]);T=np.array([float(k.split('|')[1]) for k in ids]);isL=np.array([k.startswith('L') for k in ids])
    return A,T,isL
def U_np(A,T,isL,x,d):return np.where(isL,uL(A,x-T,d),usech(A,x-T,d))
def solve(ids,Elo,Ehi,Fa,m,rem,cand):
    A,T,isL=kern_np(ids);J=len(ids);n=2*J+2;rows=[];b=[]
    for x,d,f in rem:
        u=f*U_np(A,T,isL,x,d);r=np.zeros(n);r[:J]=-u;r[J:2*J]=u;r[2*J]=-f;rows.append(r);b.append(-TAU*f)
    for x,d in cand:
        u=2*U_np(A,T,isL,x,d);r=np.zeros(n);EhiF=np.where(isL,Ehi+Fa,Ehi);r[:J]=-(u-EhiF);r[J:2*J]=-(-u+(Elo-Fa));r[2*J]=-(2-(m['Nwin']-2)-2);r[-1]=1;rows.append(r);b.append(0.)
    Aeq=np.zeros((1,n));Aeq[0,:2*J+1]=1
    res=linprog(np.r_[np.zeros(2*J+1),-1],A_ub=np.array(rows),b_ub=b,A_eq=Aeq,b_eq=[1],bounds=[(0,None)]*(2*J+1)+[(None,None)],method='highs')
    return res.x[:2*J+1],-res.fun
def ball(lo,hi):a,b=arb(lo),arb(hi);return (a+b)/2+arb(0,((b-a)/2).upper())
def phi_box(terms,yc,x0,x1,d0,d1,f):
    x=ball(x0,x1);d=ball(d0,d1);v=arb(yc)*f
    for c,a,t,L in terms:
        r=x-arb(t)
        if L:
            e=arb(a);em=e-d;ep=e+d;v+=c*f*(em/(em*em+r*r)+ep/(ep*ep+r*r))/2
        else:
            A=arb(a);cc=(A*d).cos();s=(A*r).sinh();v+=c*f*(A*r).cosh()*cc/(s*s+cc*cc)
    return v
def check(ids,Elo,Ehi,Fa,m,region,y,maxdepth=48,budget=8000000):
    J=len(ids);A,T,isL=kern_np(ids);c=y[:J]-y[J:2*J];yc=y[2*J]
    terms=[(arb(float(c[j])),A[j],T[j],bool(isL[j])) for j in range(J) if abs(c[j])>0]
    K=sum(arb(float(y[j]))*(arb(float(Ehi[j]))+(arb(float(Fa[j])) if isL[j] else 0))-arb(float(y[J+j]))*(arb(float(Elo[j]))-arb(float(Fa[j]))) for j in range(J))+arb(yc)*(arb(m['Nwin'])-2)
    viol=[];boxes=0;minc=None
    roots=[('rem',lo,hi,0.,0.,1.) if k=='on' else ('rem',lo,hi,0.,cap,2.) for k,lo,hi,_,cap in m['vars']]+[('cand',*region,2.)]
    for kind,x0,x1,d0,d1,f in roots:
        stack=[(x0,x1,d0,d1,0)]
        while stack:
            b0,b1,e0,e1,dep=stack.pop();boxes+=1
            if boxes>budget:return dict(status='BUDGET',violations=viol,boxes=boxes)
            v=phi_box(terms,yc,b0,b1,e0,e1,f)
            if kind=='cand':v=v-K-2*arb(yc)
            ok=v.lower()>0 if kind=='cand' else v.lower()>=0
            if ok:
                if kind=='cand':minc=v.lower() if minc is None else min(minc,v.lower())
                continue
            pv=phi_box(terms,yc,(b0+b1)/2,(b0+b1)/2,(e0+e1)/2,(e0+e1)/2,f)
            if kind=='cand':pv=pv-K-2*arb(yc)
            if (pv.upper()<0) or (kind=='cand' and pv.upper()<=0):viol.append((kind,(b0+b1)/2,(e0+e1)/2,f));continue
            if kind=='rem' and dep>=24 and pv.upper()<TAU*f*0.5:viol.append((kind,(b0+b1)/2,(e0+e1)/2,f));continue
            if dep>=maxdepth:return dict(status='UNRESOLVED_DEPTH',violations=viol,boxes=boxes,box=[kind,b0,b1,e0,e1,v.str(5)])
            if (b1-b0)>=4*(e1-e0) or e0==e1:mm=(b0+b1)/2;stack+=[(b0,mm,e0,e1,dep+1),(mm,b1,e0,e1,dep+1)]
            else:mm=(e0+e1)/2;stack+=[(b0,b1,e0,mm,dep+1),(b0,b1,mm,e1,dep+1)]
    return dict(status='CERTIFIED' if not viol else 'VIOLATIONS',violations=viol,boxes=boxes,min_candidate_lower=float(minc) if minc is not None else None,normalizer=float(sum(y)))
name=sys.argv[2] if len(sys.argv)>2 else 'g00_left';TAU=float(sys.argv[3]) if len(sys.argv)>3 else 1e-4
c,m,ids,Elo,Ehi,Fa=build(name)
rem=[];[rem.extend([(x,0.,1.)] if k=='on' else [(x,d,2.) for d in [0.]+list(np.geomspace(1e-5,cap,40))]) for k,lo,hi,_,cap in m['vars'] for x in np.arange(lo,hi,0.002 if hi-lo>0.05 else 0.0005)]
x0,x1,d0,d1=c['region'];cand=[(x,d) for x in np.linspace(x0,x1,11) for d in np.geomspace(max(d0,1e-3),d1,25)]
for rnd in range(12):
    t0=time.time();y,mu=solve(ids,Elo,Ehi,Fa,m,rem,cand);r=check(ids,Elo,Ehi,Fa,m,c['region'],y)
    print(json.dumps(dict(viol=[(k,round(x,6),round(d,6)) for k,x,d,f in r['violations']][:3],round=rnd,sampled_margin=mu,status=r['status'],violations=len(r['violations']),boxes=r['boxes'],min_candidate_lower=r.get('min_candidate_lower'),box=r.get('box'),seconds=round(time.time()-t0,1))),flush=True)
    if r['status']=='CERTIFIED':
        json.dump(dict(case=name,ids=ids,y=list(map(float,y)),result=r,caveat='Lorentzian far allowance: farL.py (ledger-aware, Trudgian S bound); Lorentzian rows Arb point enclosures; sech rows, Nwin and domain inherited from feedback_closure round_001 case.'),open(f'witness_{name}.json','w'));break
    if not r['violations']:break
    for kind,x,d,f in r['violations']:(rem if kind=='rem' else cand).append((x,d,f) if kind=='rem' else (x,d))
