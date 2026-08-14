import numpy as np, pandas as pd
import sweep as SW; SW.init()
from book import tranche_book, score_book, G
from sim import normalise_unit_gross, apply_caps, daily, sharpe, maxdd
E=SW._S['E']; sim=SW._S['sim']; fe=SW._S['fe']; p=SW._S['p']
PG=("ret","size","liq")
def build(w,hold,k,kinds=("bigp","imbsml"),wts=(1.0,1.0),purge=PG):
    S=SW.score(kinds,wts,w,purge); return tranche_book(S,E,k=k,hold=hold)
W=build(90,63,4)
out=sim.run(W); r=score_book(sim,W,fe); r['G']=G(r)
print('CANDIDATE bigp+imbsml w=90 hold=63 k=4')
for kk in ['sharpe1','sharpe2','sharpe3','ann1','ann2','vol','dd1','dd2','turn','edge_bps','cost_share','trades','long_gross','short_gross','f1','f2','f3','f4','worst_fold','median_fold','pq2','calmar2','G','req_min_scale']:
    print('  %-14s %s'%(kk, round(r[kk],4) if isinstance(r[kk],float) else r[kk]))
# fold share of positive PnL (base cost) and top-5 day share
d1=daily(out[1]['net'],sim.days)[1]
idx=pd.DatetimeIndex(np.unique(sim.days)*86400000000000).tz_localize('UTC')
pos=np.clip(d1,0,None); tot=pos.sum()
print('  fold positive-PnL shares:', [round(float(pos[(idx>=a)&(idx<b)].sum()/tot),3) for _,a,b in fe], '(floor <= 0.60)')
ad=np.abs(d1); print('  top5-day share: %.3f (floor <= 0.35)'%(np.sort(ad)[-5:].sum()/ad.sum()))
# rolling 1y sharpe
s=pd.Series(d1,index=idx); roll=s.rolling(365).apply(lambda x: sharpe(x.values),raw=False)
print('  rolling-365d Sharpe: min %.2f p10 %.2f med %.2f max %.2f ; frac>0 %.2f'%(roll.min(),roll.quantile(.1),roll.median(),roll.max(),(roll.dropna()>0).mean()))
# yearly
print('  by year:'); yr=s.groupby(s.index.year)
for y,g in yr: print('    %d  ret %+.3f  sharpe %+.2f'%(y,(1+g).prod()-1,sharpe(g.values)))
# symbol concentration of gross PnL
Wn=apply_caps(normalise_unit_gross(W)); sc=out['scalars']
Wx=apply_caps(Wn*sc[:,None])
ret=sim.o_next/sim.o_now-1.0; ret=np.where(np.isfinite(ret),ret,0.0)
contrib=(Wx*ret)
tot_by_sym=contrib.sum(axis=0)
o=np.argsort(-np.abs(tot_by_sym))[:10]
print('  top-10 symbols by |gross contribution| (sum=%.3f):'%tot_by_sym.sum())
for j in o: print('    %-12s %+.4f  (share of total %.2f)'%(p.symbols[j],tot_by_sym[j],tot_by_sym[j]/tot_by_sym.sum()))
print('  n symbols ever held:',int((np.abs(Wx)>1e-9).any(axis=0).sum()))
