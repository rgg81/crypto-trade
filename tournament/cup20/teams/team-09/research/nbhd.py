"""Offline analogue of the declared-neighbourhood sweep: per-metric median, then G from medians."""
import pandas as pd, numpy as np, itertools, json
from sweep import run
PG=("ret","size","liq"); KINDS=("bigp","imbsml"); WTS=(1.0,1.0)

def points(w,nb,h,k,dw,dn,dh,dk=1,corners=0):
    P=[(w,nb,h,k),(w-dw,nb,h,k),(w+dw,nb,h,k),(w,nb-dn,h,k),(w,nb+dn,h,k),
       (w,nb,h-dh,k),(w,nb,h+dh,k),(w,nb,h,k-dk),(w,nb,h,k+dk)]
    if corners:
        P += [(w-dw,nb-dn,h-dh,k-dk),(w+dw,nb+dn,h+dh,k+dk)][:corners]
    return P

def Gm(m):
    C=lambda x: min(1.,max(0.,x))
    cal=m['calmar2'];  cal=0.0 if not np.isfinite(cal) else cal
    return (30*C((m['worst_fold']+.25)/1.)+20*C((m['median_fold']-.25)/.75)
            +20*C((.20-m['dd2'])/.15)+15*C(cal/1.5)+8*C((m['pq2']-.5)/.375))

def evaluate(nom,dw,dn,dh,corners=0,tag=''):
    P=points(*nom,dw,dn,dh,corners=corners)
    cfgs=[dict(kinds=KINDS,weights=WTS,purge=PG,cadence=1,phase=0,w=a,nb=b,hold=c,k=d) for a,b,c,d in P]
    df=run(cfgs,workers=len(cfgs),out=None)
    med={c:float(df[c].median()) for c in ['sharpe1','sharpe2','sharpe3','ann1','ann2','vol','dd1','dd2',
         'turn','edge_bps','cost_share','trades','worst_fold','median_fold','pq2','calmar2','long_gross','short_gross']}
    pf=float(((df.ann1>0)&(df.sharpe2>0)).mean())
    return dict(nom=nom,d=(dw,dn,dh),G_med=Gm(med),pos_frac=pf,npts=len(P),
                **{('m_'+k):round(v,4) for k,v in med.items()})

CANDS=[((81,126,72,4),9,18,12),((81,126,84,4),9,18,12),((90,126,72,4),9,18,12),
       ((81,126,72,3),9,18,12),((72,126,72,4),9,18,12),((90,108,63,4),9,18,9),
       ((81,126,72,4),12,24,18),((90,126,84,4),9,18,12),((81,120,72,4),9,18,12),
       ((90,90,63,4),9,18,9)]
rows=[evaluate(*c) for c in CANDS]
df=pd.DataFrame(rows); pd.set_option('display.width',300)
print(df[['nom','d','G_med','pos_frac','m_sharpe1','m_sharpe2','m_sharpe3','m_ann1','m_vol','m_dd1','m_dd2','m_turn','m_edge_bps','m_worst_fold','m_median_fold','m_pq2','m_calmar2','m_short_gross','m_trades']].sort_values('G_med',ascending=False).to_string(index=False))
