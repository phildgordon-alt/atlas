# tight_margin_v1.py (CORE_ROADMAP 2026-11-01). DIAGNOSTIC ONLY. Branch-and-bound Arb lower bound of the candidate margin to 1e-3,
# same box formula as verify_zs5._phi; K uses generator measurements (not replayed). Usage: python tight_margin_v1.py CERT.json ...
# Diagnostic only: rigorous branch-and-bound lower bound of the candidate margin min over the region,
# using the same Arb box formula as verify_zs5._phi (copied), K from generator measurements (not replayed).
import json, sys, heapq, os
from flint import arb, ctx
def _ball(lo,hi):a,b=arb(lo),arb(hi);return (a+b)/2+arb(0,((b-a)/2).upper())
def _phi(terms,yc,x0,x1,d0,d1,f):
    x=_ball(x0,x1);d=_ball(d0,d1);s=arb(yc)
    for c,a,t in terms:
        r=x-arb(t);A=arb(a);cc=(A*d).cos();sh=(A*r).sinh();s+=c*(A*r).cosh()*cc/(sh*sh+cc*cc)
    return arb(f)*s
for cp in sys.argv[1:]:
    rd=os.path.dirname(os.path.dirname(cp)); c=json.load(open(cp)); meas=json.load(open(rd+'/gen_measurements.json'))
    ids=c['ids'];J=len(ids);y=c['y'];yc=y[2*J]
    P=[(float(i.split('|')[0]),float(i.split('|')[1])) for i in ids]
    terms=[(arb(y[j])-arb(y[J+j]),*P[j]) for j in range(J) if y[j]!=y[J+j]]
    K=sum((arb(y[j])*arb(meas[ids[j]][1])-arb(y[J+j])*arb(meas[ids[j]][0]) for j in range(J)),arb(0))+arb(yc)*(arb(c['Nwin'])-2)
    W=sum((arb(v) for v in c['w']),arb(0))
    val=lambda b:_phi(terms,yc,*b,2.)-K-2*arb(yc)+W
    x0,x1,d0,d1=c['regions'][0]
    # upper bound from midpoints
    best_up=1e9; h=[]; n=0
    def push(b):
        global best_up,n
        n+=1; v=val(b); m=val(((b[0]+b[1])/2,(b[0]+b[1])/2,(b[2]+b[3])/2,(b[2]+b[3])/2))
        best_up=min(best_up,float(m.upper())); lv=float(v.lower()); lv=-1e300 if lv!=lv else lv; heapq.heappush(h,(lv,b))
    push((x0,x1,d0,d1))
    while h:
        lo,b=h[0]
        if best_up-lo<1e-3 or n>200000: break
        heapq.heappop(h); b0,b1,e0,e1=b
        if (b1-b0)>=4*(e1-e0) or e0==e1: m=(b0+b1)/2; push((b0,m,e0,e1)); push((m,b1,e0,e1))
        else: m=(e0+e1)/2; push((b0,b1,e0,m)); push((b0,b1,m,e1))
    print(json.dumps(dict(cert=cp.split('runs/')[1],reported_min_candidate_lower=round(c['min_candidate_lower'],4),sampled=round(c['sampled_margin'],4),tight_lower=round(h[0][0],4),upper=round(best_up,4),boxes=n)))
