import numpy as np, pandas as pd
import sweep as SW; SW.init()
from book import tranche_book, score_book, G
from flow import prev_mean, prev_sum, rank_rows, cs_residual
E=SW._S['E']; sim=SW._S['sim']; fe=SW._S['fe']; f=SW._S['f']; p=SW._S['p']
PG=("ret","size","liq"); W_,H_,K_=90,63,4
def show(tag,W):
    r=score_book(sim,W,fe); r['G']=G(r)
    print('%-34s S1 %+6.2f S2 %+6.2f edge %+7.1f dd2 %.3f wf %+6.2f G %5.1f LG %+9.0f SG %+9.0f turn %5.1f'%(
      tag,r['sharpe1'],r['sharpe2'],r['edge_bps'],r['dd2'],r['worst_fold'],r['G'],r['long_gross'],r['short_gross'],r['turn']))
    return r
S=SW.score(("bigp","imbsml"),(1.0,1.0),W_,PG)
base=tranche_book(S,E,k=K_,hold=H_); show('NOMINEE',base)
show('EXACT SIGN INVERSION',-base)
# lag/lead sensitivity: does one bar of timing carry the result?
for sh in (-1,1,3):
    Ss=np.full_like(S,np.nan)
    if sh>0: Ss[sh:]=S[:-sh]
    else: Ss[:sh]=S[-sh:]
    show('signal shifted %+d bar(s)'%(-sh), tranche_book(Ss,E,k=K_,hold=H_))
# mechanism-off: print-size shock replaced by a constant -> plain imbalance level
show('MECH OFF (plain imbalance level)', tranche_book(SW.score(("lvl",),(1.0,),W_,PG),E,k=K_,hold=H_))
# mechanism-scrambled: print-size shock replaced by a symbol-shuffled copy of itself
rng=np.random.default_rng(7)
big=f.log_ats-prev_mean(f.log_ats,90)
perm=rng.permutation(p.n_sym); bigp_sh=big[:,perm]
z=np.where(np.isfinite(bigp_sh)&np.isfinite(f.imb),np.clip(bigp_sh,-3,3),np.nan)
num=prev_sum(np.where(np.isfinite(z),f.imb*z*f.qv,0.0),W_); den=prev_sum(np.where(np.isfinite(z),f.qv,0.0),W_)
cov_sh=np.where(den>0,num/den,np.nan)[p.d0:p.dn]
sel=np.isfinite(f.imb)&np.isfinite(bigp_sh)&(bigp_sh<=0)
n2=prev_sum(np.where(sel,f.net_quote,0.0),W_); d2=prev_sum(np.where(sel,f.qv,0.0),W_); c2=prev_sum(sel.astype(float),W_)
ims_sh=np.where((c2>=15)&(d2>0),n2/np.where(d2>0,d2,np.nan),np.nan)[p.d0:p.dn]
ctrl=[rank_rows(SW.raw_measure('ret',W_),E),SW._S['size'],SW._S['liq']]
Ssh=cs_residual(rank_rows(cov_sh,E)+rank_rows(ims_sh,E),ctrl,E)
show('MECH SCRAMBLED (print size shuffled)', tranche_book(Ssh,E,k=K_,hold=H_))
# random gate at identical selectivity
for seed in (1,2,3):
    rr=np.where(E, rng.standard_normal(S.shape), np.nan)
    show('RANDOM gate seed=%d'%seed, tranche_book(rr,E,k=K_,hold=H_))
# weight-multiset placebo: keep the book, permute which eligible symbol gets which weight
for seed in (11,12,13):
    g=np.random.default_rng(seed); P=np.zeros_like(base)
    for i in range(base.shape[0]):
        nz=np.flatnonzero(np.abs(base[i])>1e-12)
        if nz.size==0: continue
        pool=np.flatnonzero(E[i])
        pick=g.choice(pool,size=min(nz.size,pool.size),replace=False)
        P[i,pick]=base[i,nz][:pick.size]
    show('PLACEBO permuted symbols seed=%d'%seed, P)
