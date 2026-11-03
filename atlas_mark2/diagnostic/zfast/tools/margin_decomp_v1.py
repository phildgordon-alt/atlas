# margin_decomp_v1.py (CORE_ROADMAP 2026-11-01). DIAGNOSTIC ONLY, not in any trust path. Float decomposition of each main
# certificate margin: Phi_cand_min - K + sum_w = Phi_cand_min - far - interval_resid (far := K - sum over credited zeros of Phi).
import json, glob, os, sys, math, cmath
base='/Users/kiosk/atlas_mark2/diagnostic/zfast'
runs=sorted(glob.glob(base+'/atlas_v5z*/runs/w*/*/certs/cert_p*.json'))
def U(a,r,d):  # Re sech(a(r - i d))
    return (1/cmath.cosh(a*complex(r,-d))).real
out=[]
for cp in runs:
    rd=os.path.dirname(os.path.dirname(cp))
    c=json.load(open(cp))
    T0=c['T0']; L=math.log(T0/(2*math.pi))
    meas=json.load(open(rd+'/gen_measurements.json'))
    ids=c['ids']; n=len(ids); y=c['y']; yup=y[:n]; ylow=y[n:2*n]; yc=y[2*n]
    rows=[(float(i.split('|')[0]),float(i.split('|')[1])) for i in ids]
    Ehi=[meas[i][1] for i in ids]; Elo=[meas[i][0] for i in ids]
    K=sum(yup[j]*Ehi[j] for j in range(n)) + yc*(c['Nwin']-2)
    if any(ylow): K=None
    cvec=[yup[j]-ylow[j] for j in range(n)]
    phi=lambda x,d,f=1: f*(yc+sum(cvec[j]*U(rows[j][0],x-rows[j][1],d) for j in range(n)))
    x0,x1,d0,d1=c['regions'][0]
    pm=min((phi(x0+(x1-x0)*i/200,d1*k/50,2),x0+(x1-x0)*i/200,d1*k/50) for i in range(201) for k in range(51))
    ivs=c['zs_intervals']; w=c['w']
    gam=[(a+b)/2 for a,b in ivs]
    sphi=sum(phi(g,0) for g in gam)
    resid=sum(phi(g,0)-wi for g,wi in zip(gam,w))
    far=K-sphi
    ecount=(c['window'][1]-c['window'][0])*L/(2*math.pi)
    out.append(dict(run=os.path.relpath(rd,base),piece=c['piece'],tier=c['tier'],L=round(L,3),rows=ids,yup=[round(v,4) for v in yup],
        yc=yc,ylow=sum(ylow),Nwin=round(c['Nwin'],2),window=c['window'],nint=len(ivs),exp_zeros=round(ecount,1),
        K=round(K,4),sum_w=round(sum(w),4),phi_cand_min=round(pm[0],4),cand_at=(round(pm[1],3),round(pm[2],3)),
        sum_phi_zeros=round(sphi,4),far_plus_slack=round(far,4),interval_resid=round(resid,4),
        margin_cert=round(c['min_candidate_lower'],4),margin_recon=round(pm[0]-K+sum(w),4),
        ballrad=max(meas[i][1]-meas[i][0] for i in ids)))
for o in out: print(json.dumps(o))
